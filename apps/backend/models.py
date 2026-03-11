from __future__ import annotations

from pydantic import BaseModel, Field


class AnswerBlock(BaseModel):
    id: str
    content: str
    score: int | None = None
    feedback: str | None = None
    children_questions: list[QuestionBlock] = Field(default_factory=list)


class QuestionBlock(BaseModel):
    id: str
    content: str
    answer: AnswerBlock | None = None


class TitleBlock(BaseModel):
    id: str
    content: str
    questions: list[QuestionBlock] = Field(default_factory=list)


class BlockTree(BaseModel):
    id: str
    title: str
    original_text: str
    blocks: list[TitleBlock] = Field(default_factory=list)
    num_questions: int = 2


# --- Request / Response models ---


class CreateTreeRequest(BaseModel):
    title: str
    text: str
    num_questions: int = 2


class SubmitAnswerRequest(BaseModel):
    content: str


class GenerateQuestionsRequest(BaseModel):
    num_questions: int = 2


class EvaluateAnswerRequest(BaseModel):
    pass  # no body needed; we already know the answer from the tree


class TreeListItem(BaseModel):
    id: str
    title: str
    num_blocks: int
    num_questions: int
