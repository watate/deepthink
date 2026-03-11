import asyncio
import json
import re

from openai import AsyncOpenAI

from config import get_settings


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
                "content": (
                    "You are an expert at generating thought-provoking questions "
                    "that help people think deeply about written text. "
                    "Return ONLY a JSON array of strings, no other text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generate exactly {num_questions} deep, thought-provoking questions "
                    f"about the following text. The questions should challenge the reader "
                    f"to think critically about the ideas presented.\n\n"
                    f"Text:\n{content}\n\n"
                    f"Return a JSON array of {num_questions} question strings."
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
                "content": (
                    "You evaluate answers to questions about written text. "
                    "Score from 0.0 to 1.0 based on depth of thinking, accuracy, "
                    "and insight. Provide constructive feedback. "
                    'Return ONLY JSON: {"score": <float>, "feedback": "<string>"}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original text context:\n{context}\n\n"
                    f"Question:\n{question}\n\n"
                    f"Answer:\n{answer}\n\n"
                    "Evaluate this answer."
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
