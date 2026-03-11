from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.backend.main import app
from apps.backend.models import AnswerBlock, BlockTree, QuestionBlock, TitleBlock


@pytest.fixture
def sample_tree() -> BlockTree:
    """A fully populated tree for testing."""
    return BlockTree(
        id="tree-1",
        title="Test Essay",
        original_text="Block one content.\n\nBlock two content.",
        num_questions=2,
        blocks=[
            TitleBlock(
                id="tree-1-b0",
                content="Block one content.",
                questions=[
                    QuestionBlock(id="tree-1-b0-q0", content="Question 1?"),
                    QuestionBlock(id="tree-1-b0-q1", content="Question 2?"),
                ],
            ),
            TitleBlock(
                id="tree-1-b1",
                content="Block two content.",
                questions=[
                    QuestionBlock(id="tree-1-b1-q0", content="Question 3?"),
                ],
            ),
        ],
    )


@pytest.fixture
def answered_tree(sample_tree: BlockTree) -> BlockTree:
    """A tree with one answered question."""
    sample_tree.blocks[0].questions[0].answer = AnswerBlock(
        id="tree-1-b0-q0-a",
        content="My answer to question 1.",
    )
    return sample_tree


@pytest.fixture
def evaluated_tree(answered_tree: BlockTree) -> BlockTree:
    """A tree with one evaluated answer."""
    answered_tree.blocks[0].questions[0].answer.score = 75
    answered_tree.blocks[0].questions[0].answer.feedback = "Good depth of thinking."
    return answered_tree


@pytest.fixture
def mock_s3():
    """Mock all S3 service functions."""
    with (
        patch("apps.backend.routes.s3_service.save_tree", new_callable=AsyncMock) as save,
        patch("apps.backend.routes.s3_service.load_tree", new_callable=AsyncMock) as load,
        patch("apps.backend.routes.s3_service.list_trees", new_callable=AsyncMock) as list_t,
        patch("apps.backend.routes.s3_service.delete_tree", new_callable=AsyncMock) as delete,
    ):
        yield {"save": save, "load": load, "list": list_t, "delete": delete}


@pytest.fixture
def mock_llm():
    """Mock all LLM service functions."""
    with (
        patch("apps.backend.routes.llm_service.split_text_into_blocks") as split,
        patch(
            "apps.backend.routes.llm_service.generate_questions_for_blocks",
            new_callable=AsyncMock,
        ) as gen_for_blocks,
        patch(
            "apps.backend.routes.llm_service.generate_questions",
            new_callable=AsyncMock,
        ) as gen,
        patch(
            "apps.backend.routes.llm_service.evaluate_answer",
            new_callable=AsyncMock,
        ) as evaluate,
    ):
        split.return_value = ["Block one content.", "Block two content."]
        gen_for_blocks.return_value = [
            ["Question 1?", "Question 2?"],
            ["Question 3?", "Question 4?"],
        ]
        gen.return_value = ["New question?"]
        evaluate.return_value = {"score": 85, "feedback": "Great answer."}
        yield {
            "split": split,
            "gen_for_blocks": gen_for_blocks,
            "gen": gen,
            "evaluate": evaluate,
        }


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
