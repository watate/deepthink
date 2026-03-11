import asyncio
import json
import re
from functools import lru_cache
from pathlib import Path

from openai import AsyncOpenAI

from config import get_settings

PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache
def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


async def generate_questions(content: str, num_questions: int) -> list[str]:
    """Generate questions for a piece of text."""
    client = _get_client()
    settings = get_settings()

    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": _load_prompt("generate_questions_system"),
            },
            {
                "role": "user",
                "content": _load_prompt("generate_questions_user").format(
                    num_questions=num_questions, content=content
                ),
            },
        ],
    )

    raw = resp.choices[0].message.content or "[]"
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    questions: list[str] = json.loads(raw)
    return questions[:num_questions]


async def evaluate_answer(
    question: str, answer: str, context: str
) -> dict[str, float | str]:
    """Evaluate an answer and return score + feedback."""
    client = _get_client()
    settings = get_settings()

    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": _load_prompt("evaluate_answer_system"),
            },
            {
                "role": "user",
                "content": _load_prompt("evaluate_answer_user").format(
                    context=context, question=question, answer=answer
                ),
            },
        ],
    )

    raw = resp.choices[0].message.content or '{}'
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    return json.loads(raw)


def split_text_into_blocks(text: str) -> list[str]:
    """Split markdown text into blocks based on double newlines or headings."""
    # Split on double newlines
    raw_blocks = re.split(r"\n{2,}", text.strip())
    # Filter out empty blocks
    return [b.strip() for b in raw_blocks if b.strip()]


async def generate_questions_for_blocks(
    blocks: list[str], num_questions: int
) -> list[list[str]]:
    """Generate questions for multiple blocks concurrently."""
    tasks = [generate_questions(block, num_questions) for block in blocks]
    return await asyncio.gather(*tasks)
