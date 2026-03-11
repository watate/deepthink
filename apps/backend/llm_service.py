import asyncio
import re
from functools import lru_cache
from pathlib import Path

from openai import AsyncOpenAI

from .config import get_settings
from .models import EvaluationResponse, QuestionsResponse

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _response_format(name: str, model_class):
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": model_class.model_json_schema(),
        },
    }


@lru_cache
def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


async def generate_questions(
    content: str,
    num_questions: int,
    existing_questions: list[str] | None = None,
) -> list[str]:
    """Generate questions for a piece of text."""
    client = _get_client()
    settings = get_settings()

    if existing_questions:
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(existing_questions))
        existing_section = (
            f"The following questions have already been asked. "
            f"Do NOT repeat or rephrase any of them:\n{numbered}"
        )
    else:
        existing_section = ""

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
                    num_questions=num_questions,
                    content=content,
                    existing_questions_section=existing_section,
                ),
            },
        ],
        response_format=_response_format("questions", QuestionsResponse),
    )

    data = QuestionsResponse.model_validate_json(
        resp.choices[0].message.content or '{"questions": []}'
    )
    return data.questions[:num_questions]


async def evaluate_answer(
    question: str, answer: str, context: str
) -> EvaluationResponse:
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
        response_format=_response_format("evaluation", EvaluationResponse),
    )

    return EvaluationResponse.model_validate_json(
        resp.choices[0].message.content or '{"score": 0, "feedback": ""}'
    )


def split_text_into_blocks(text: str) -> list[str]:
    """Split markdown text into blocks based on double newlines or headings."""
    raw_blocks = re.split(r"\n{2,}", text.strip())
    return [b.strip() for b in raw_blocks if b.strip()]


async def generate_questions_for_blocks(
    blocks: list[str], num_questions: int
) -> list[list[str]]:
    """Generate questions for multiple blocks concurrently."""
    tasks = [generate_questions(block, num_questions) for block in blocks]
    return await asyncio.gather(*tasks)
