import asyncio
import logging
import random
from functools import lru_cache
from pathlib import Path

from .config import get_settings
from .llm_provider import AnthropicProvider, LLMResponse, OpenRouterProvider
from .models import CreateBlockInput, EvaluationResponse, QuestionsResponse

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"

MAX_RETRIES = 5
MAX_AGENT_TURNS = 20


@lru_cache
def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _get_provider() -> AnthropicProvider | OpenRouterProvider:
    settings = get_settings()
    if settings.anthropic_api_key:
        logger.info("Using Anthropic provider")
        return AnthropicProvider(api_key=settings.anthropic_api_key)
    if settings.openrouter_api_key:
        providers = (
            [p.strip() for p in settings.openrouter_providers.split(",") if p.strip()]
            if settings.openrouter_providers
            else None
        )
        logger.info("Using OpenRouter provider (providers=%s)", providers)
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key, providers=providers
        )
    raise RuntimeError(
        "No LLM API key configured. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY."
    )


CREATE_BLOCK_TOOL = {
    "name": "create_block",
    "description": "Create a block from the writing with its questions. Call this once per block.",
    "input_schema": CreateBlockInput.model_json_schema(),
}

QUESTIONS_TOOL = {
    "name": "return_questions",
    "description": "Return the generated questions.",
    "input_schema": QuestionsResponse.model_json_schema(),
}

EVALUATION_TOOL = {
    "name": "return_evaluation",
    "description": "Return the evaluation score and feedback.",
    "input_schema": EvaluationResponse.model_json_schema(),
}


async def _call_with_retry(
    provider: AnthropicProvider | OpenRouterProvider,
    coro_fn,
    *args,
    **kwargs,  # type: ignore[no-untyped-def]
):
    """Call an async function with exponential backoff on rate limit errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as exc:
            if not provider.is_rate_limit_error(exc):
                raise
            if attempt == MAX_RETRIES - 1:
                raise
            wait = (2**attempt) + random.uniform(0, 1)
            logger.warning(
                "Rate limited — retrying in %.1fs (attempt %d/%d)",
                wait,
                attempt + 1,
                MAX_RETRIES,
            )
            await asyncio.sleep(wait)


async def create_blocks(text: str, num_questions: int) -> list[CreateBlockInput]:
    """Agentic loop: LLM reads full text, creates blocks with questions via tool calls."""
    provider = _get_provider()
    settings = get_settings()

    messages: list[dict] = [
        {
            "role": "user",
            "content": _load_prompt("create_blocks_user").format(
                num_questions=num_questions, text=text
            ),
        },
    ]

    blocks: list[CreateBlockInput] = []

    for turn in range(MAX_AGENT_TURNS):
        logger.info("create_blocks turn %d — calling LLM...", turn + 1)
        resp: LLMResponse = await _call_with_retry(
            provider,
            provider.create,
            model=settings.llm_model,
            max_tokens=4096,
            system=_load_prompt("create_blocks_system"),
            messages=messages,
            tools=[CREATE_BLOCK_TOOL],
        )

        if not resp.tool_calls:
            logger.info(
                "create_blocks — LLM done (no tool calls), total blocks: %d",
                len(blocks),
            )
            break

        for tc in resp.tool_calls:
            if tc.name == "create_block":
                block = CreateBlockInput.model_validate(tc.input)
                blocks.append(block)
                logger.info(
                    "create_blocks — block %d created (%d questions, %d chars)",
                    len(blocks),
                    len(block.questions),
                    len(block.content),
                )

        results = {tc.id: "Block created." for tc in resp.tool_calls}
        messages.extend(provider.build_result_messages(resp, results))

        if resp.is_done:
            logger.info(
                "create_blocks — LLM signalled done, total blocks: %d", len(blocks)
            )
            break

    return blocks


async def generate_questions(
    content: str,
    num_questions: int,
    existing_questions: list[str] | None = None,
) -> list[str]:
    """Generate additional questions for an existing block."""
    logger.info("generate_questions — requesting %d questions", num_questions)
    provider = _get_provider()
    settings = get_settings()

    if existing_questions:
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(existing_questions))
        existing_section = (
            f"The following questions have already been asked. "
            f"Do NOT repeat or rephrase any of them:\n{numbered}"
        )
    else:
        existing_section = ""

    resp = await _call_with_retry(
        provider,
        provider.create,
        model=settings.llm_model,
        max_tokens=1024,
        system=_load_prompt("generate_questions_system"),
        messages=[
            {
                "role": "user",
                "content": _load_prompt("generate_questions_user").format(
                    num_questions=num_questions,
                    content=content,
                    existing_questions_section=existing_section,
                ),
            },
        ],
        tools=[QUESTIONS_TOOL],
        tool_choice={"type": "tool", "name": "return_questions"},
    )

    for tc in resp.tool_calls:
        if tc.name == "return_questions":
            data = QuestionsResponse.model_validate(tc.input)
            return data.questions[:num_questions]

    return []


async def evaluate_answer(
    question: str, answer: str, context: str
) -> EvaluationResponse:
    """Evaluate an answer and return score + feedback."""
    logger.info("evaluate_answer — scoring answer (%d chars)", len(answer))
    provider = _get_provider()
    settings = get_settings()

    resp = await _call_with_retry(
        provider,
        provider.create,
        model=settings.llm_model,
        max_tokens=1024,
        system=_load_prompt("evaluate_answer_system"),
        messages=[
            {
                "role": "user",
                "content": _load_prompt("evaluate_answer_user").format(
                    context=context, question=question, answer=answer
                ),
            },
        ],
        tools=[EVALUATION_TOOL],
        tool_choice={"type": "tool", "name": "return_evaluation"},
    )

    for tc in resp.tool_calls:
        if tc.name == "return_evaluation":
            return EvaluationResponse.model_validate(tc.input)

    return EvaluationResponse(score=0, feedback="")
