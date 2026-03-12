from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    tool_calls: list[ToolCall]
    is_done: bool
    _raw: Any = field(repr=False)


class AnthropicProvider:
    def __init__(self, api_key: str) -> None:
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._mod = anthropic

    async def create(
        self,
        *,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict],
        tools: list[dict],
        tool_choice: dict | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
        )
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        resp = await self._client.messages.create(**kwargs)

        calls = [
            ToolCall(id=b.id, name=b.name, input=b.input)
            for b in resp.content
            if b.type == "tool_use"
        ]
        return LLMResponse(
            tool_calls=calls,
            is_done=resp.stop_reason == "end_turn" or not calls,
            _raw=resp,
        )

    def build_result_messages(
        self, response: LLMResponse, results: dict[str, str]
    ) -> list[dict]:
        return [
            {"role": "assistant", "content": response._raw.content},
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tid, "content": text}
                    for tid, text in results.items()
                ],
            },
        ]

    def is_rate_limit_error(self, exc: Exception) -> bool:
        return isinstance(exc, self._mod.RateLimitError)


class OpenRouterProvider:
    def __init__(self, api_key: str, providers: list[str] | None = None) -> None:
        import openai as _openai
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._mod = _openai
        self._providers = providers

    async def create(
        self,
        *,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict],
        tools: list[dict],
        tool_choice: dict | None = None,
    ) -> LLMResponse:
        if "/" not in model:
            model = f"anthropic/{model}"

        oai_messages: list[dict] = [
            {"role": "system", "content": system},
            *messages,
        ]

        oai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            messages=oai_messages,
            tools=oai_tools,
        )
        if tool_choice is not None and tool_choice.get("type") == "tool":
            kwargs["tool_choice"] = {
                "type": "function",
                "function": {"name": tool_choice["name"]},
            }
        extra_body: dict[str, Any] = {}
        if self._providers:
            extra_body["provider"] = {"only": self._providers}
        if extra_body:
            kwargs["extra_body"] = extra_body

        resp = await self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments),
                    )
                )

        return LLMResponse(
            tool_calls=calls,
            is_done=resp.choices[0].finish_reason == "stop" or not calls,
            _raw=msg,
        )

    def build_result_messages(
        self, response: LLMResponse, results: dict[str, str]
    ) -> list[dict]:
        raw = response._raw
        assistant: dict[str, Any] = {"role": "assistant", "content": raw.content or ""}
        if raw.tool_calls:
            assistant["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in raw.tool_calls
            ]

        return [assistant] + [
            {"role": "tool", "tool_call_id": tid, "content": text}
            for tid, text in results.items()
        ]

    def is_rate_limit_error(self, exc: Exception) -> bool:
        return isinstance(exc, self._mod.RateLimitError)
