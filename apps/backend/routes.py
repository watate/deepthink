import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from . import llm_service
from . import s3_service
from .models import (
    AnswerBlock,
    BlockTree,
    CreateTreeRequest,
    EvaluateAnswerRequest,
    GenerateQuestionsRequest,
    QuestionBlock,
    SubmitAnswerRequest,
    TitleBlock,
    TreeListItem,
)

router = APIRouter(prefix="/api")


# --- helpers ---


def _find_question(tree: BlockTree, question_id: str) -> QuestionBlock | None:
    """Recursively find a question by id in the tree."""
    for block in tree.blocks:
        for q in block.questions:
            found = _search_question(q, question_id)
            if found:
                return found
    return None


def _search_question(q: QuestionBlock, question_id: str) -> QuestionBlock | None:
    if q.id == question_id:
        return q
    if q.answer:
        for child_q in q.answer.children_questions:
            found = _search_question(child_q, question_id)
            if found:
                return found
    return None


def _find_answer(tree: BlockTree, answer_id: str) -> AnswerBlock | None:
    """Recursively find an answer by id in the tree."""
    for block in tree.blocks:
        for q in block.questions:
            found = _search_answer(q, answer_id)
            if found:
                return found
    return None


def _search_answer(q: QuestionBlock, answer_id: str) -> AnswerBlock | None:
    if q.answer:
        if q.answer.id == answer_id:
            return q.answer
        for child_q in q.answer.children_questions:
            found = _search_answer(child_q, answer_id)
            if found:
                return found
    return None


def _collect_all_questions(tree: BlockTree) -> list[str]:
    """Collect every question string in the tree, at all depths."""
    result: list[str] = []
    for block in tree.blocks:
        for q in block.questions:
            _collect_questions_recursive(q, result)
    return result


def _collect_questions_recursive(q: QuestionBlock, out: list[str]) -> None:
    out.append(q.content)
    if q.answer:
        for child_q in q.answer.children_questions:
            _collect_questions_recursive(child_q, out)


def _find_block(tree: BlockTree, block_id: str) -> TitleBlock | AnswerBlock | None:
    """Find a TitleBlock or AnswerBlock by id."""
    for block in tree.blocks:
        if block.id == block_id:
            return block
    # Also search answer blocks
    return _find_answer(tree, block_id)


def _get_context_for_question(tree: BlockTree, question_id: str) -> str:
    """Get the parent block content as context for a question."""
    for block in tree.blocks:
        for q in block.questions:
            if _search_question(q, question_id):
                return block.content
    return tree.original_text


async def _load_tree_or_404(tree_id: str) -> BlockTree:
    data = await s3_service.load_tree(tree_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Tree not found")
    return BlockTree(**data)


# --- endpoints ---


@router.post("/trees", response_model=BlockTree)
async def create_tree(req: CreateTreeRequest):
    tree_id = str(uuid.uuid4())

    # Split text into blocks
    raw_blocks = llm_service.split_text_into_blocks(req.text)

    # Generate questions for all blocks concurrently
    all_questions = await llm_service.generate_questions_for_blocks(
        raw_blocks, req.num_questions
    )

    # Build tree structure
    blocks = []
    for i, (content, questions) in enumerate(zip(raw_blocks, all_questions)):
        block_id = f"{tree_id}-b{i}"
        q_blocks = [
            QuestionBlock(id=f"{block_id}-q{j}", content=q)
            for j, q in enumerate(questions)
        ]
        blocks.append(TitleBlock(id=block_id, content=content, questions=q_blocks))

    tree = BlockTree(
        id=tree_id,
        title=req.title,
        original_text=req.text,
        blocks=blocks,
        num_questions=req.num_questions,
    )

    await s3_service.save_tree(tree_id, tree.model_dump())
    return tree


@router.get("/trees", response_model=list[TreeListItem])
async def list_trees():
    all_data = await s3_service.list_trees()
    items = []
    for data in all_data:
        tree = BlockTree(**data)
        total_questions = sum(len(b.questions) for b in tree.blocks)
        items.append(
            TreeListItem(
                id=tree.id,
                title=tree.title,
                num_blocks=len(tree.blocks),
                num_questions=total_questions,
            )
        )
    return items


@router.get("/trees/search", response_model=list[TreeListItem])
async def search_trees(q: str):
    all_data = await s3_service.list_trees()
    query = q.lower()
    items = []
    for data in all_data:
        tree = BlockTree(**data)
        if query in tree.title.lower() or query in tree.original_text.lower():
            total_questions = sum(len(b.questions) for b in tree.blocks)
            items.append(
                TreeListItem(
                    id=tree.id,
                    title=tree.title,
                    num_blocks=len(tree.blocks),
                    num_questions=total_questions,
                )
            )
    return items


@router.get("/trees/{tree_id}", response_model=BlockTree)
async def get_tree(tree_id: str):
    return await _load_tree_or_404(tree_id)


@router.delete("/trees/{tree_id}")
async def delete_tree(tree_id: str):
    await s3_service.delete_tree(tree_id)
    return {"ok": True}


@router.post("/trees/{tree_id}/blocks/{block_id}/questions", response_model=BlockTree)
async def generate_block_questions(
    tree_id: str, block_id: str, req: GenerateQuestionsRequest
):
    tree = await _load_tree_or_404(tree_id)
    block = _find_block(tree, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")

    # Collect ALL questions across the entire tree so the LLM avoids duplicates
    existing = _collect_all_questions(tree)

    new_questions = await llm_service.generate_questions(
        block.content, req.num_questions, existing_questions=existing
    )

    if isinstance(block, TitleBlock):
        existing_count = len(block.questions)
        for j, q_text in enumerate(new_questions):
            block.questions.append(
                QuestionBlock(id=f"{block_id}-q{existing_count + j}", content=q_text)
            )
    elif isinstance(block, AnswerBlock):
        existing_count = len(block.children_questions)
        for j, q_text in enumerate(new_questions):
            block.children_questions.append(
                QuestionBlock(id=f"{block_id}-q{existing_count + j}", content=q_text)
            )

    await s3_service.save_tree(tree_id, tree.model_dump())
    return tree


@router.post(
    "/trees/{tree_id}/questions/{question_id}/answer", response_model=BlockTree
)
async def submit_answer(tree_id: str, question_id: str, req: SubmitAnswerRequest):
    tree = await _load_tree_or_404(tree_id)
    question = _find_question(tree, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    # Resubmitting wipes score, feedback, and all child questions
    answer_id = f"{question_id}-a"
    question.answer = AnswerBlock(id=answer_id, content=req.content)

    await s3_service.save_tree(tree_id, tree.model_dump())
    return tree


@router.post(
    "/trees/{tree_id}/answers/{answer_id}/evaluate", response_model=BlockTree
)
async def evaluate_answer(tree_id: str, answer_id: str, _req: EvaluateAnswerRequest):
    tree = await _load_tree_or_404(tree_id)
    answer = _find_answer(tree, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Find the parent question to get question text
    question_text = ""
    for block in tree.blocks:
        for q in block.questions:
            a = _search_answer(q, answer_id)
            if a is not None:
                # Walk back to find the question that owns this answer
                question_text = _find_question_text_for_answer(q, answer_id) or q.content
                break

    context = tree.original_text
    result = await llm_service.evaluate_answer(question_text, answer.content, context)

    answer.score = result.get("score", 0.0)
    answer.feedback = result.get("feedback", "")

    await s3_service.save_tree(tree_id, tree.model_dump())
    return tree


def _find_question_text_for_answer(q: QuestionBlock, answer_id: str) -> str | None:
    """Find the question text whose direct answer has the given answer_id."""
    if q.answer and q.answer.id == answer_id:
        return q.content
    if q.answer:
        for child_q in q.answer.children_questions:
            result = _find_question_text_for_answer(child_q, answer_id)
            if result:
                return result
    return None


@router.post("/trees/{tree_id}/export")
async def export_tree(tree_id: str):
    tree = await _load_tree_or_404(tree_id)

    lines = [f"# {tree.title}\n"]
    for block in tree.blocks:
        lines.append(f"\n## {block.content[:80]}\n")
        lines.append(f"{block.content}\n")
        for q in block.questions:
            _render_question(lines, q, depth=0)

    md_content = "\n".join(lines)

    export_dir = Path(__file__).resolve().parent.parent.parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in tree.title)
    filepath = export_dir / f"{safe_title}.md"
    filepath.write_text(md_content, encoding="utf-8")

    return {"ok": True, "path": str(filepath.resolve())}


def _render_question(lines: list[str], q: QuestionBlock, depth: int):
    indent = "  " * depth
    lines.append(f"\n{indent}### Q: {q.content}\n")
    if q.answer:
        lines.append(f"{indent}**A:** {q.answer.content}\n")
        if q.answer.score is not None:
            lines.append(f"{indent}*Score: {q.answer.score}/100*\n")
        if q.answer.feedback:
            lines.append(f"{indent}*Feedback: {q.answer.feedback}*\n")
        for child_q in q.answer.children_questions:
            _render_question(lines, child_q, depth + 1)


@router.post("/backup/save")
async def backup_save_tree(tree_id: str):
    """Explicit S3 save — re-saves an already-loaded tree."""
    tree = await _load_tree_or_404(tree_id)
    await s3_service.save_tree(tree_id, tree.model_dump())
    return {"ok": True}


@router.get("/backup/{tree_id}", response_model=BlockTree)
async def backup_load_tree(tree_id: str):
    """Pull JSON from S3."""
    return await _load_tree_or_404(tree_id)
