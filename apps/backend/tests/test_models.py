from apps.backend.models import (
    AnswerBlock,
    BlockTree,
    EvaluationResponse,
    QuestionBlock,
    QuestionsResponse,
    TitleBlock,
)


def test_block_tree_defaults():
    tree = BlockTree(id="t1", title="T", original_text="text")
    assert tree.blocks == []
    assert tree.num_questions == 2


def test_question_block_no_answer():
    q = QuestionBlock(id="q1", content="Why?")
    assert q.answer is None


def test_answer_block_defaults():
    a = AnswerBlock(id="a1", content="Because.")
    assert a.score is None
    assert a.feedback is None
    assert a.children_questions == []


def test_nested_tree_roundtrip():
    tree = BlockTree(
        id="t1",
        title="Test",
        original_text="text",
        blocks=[
            TitleBlock(
                id="b0",
                content="Content",
                questions=[
                    QuestionBlock(
                        id="q0",
                        content="Q?",
                        answer=AnswerBlock(
                            id="a0",
                            content="A.",
                            score=90,
                            feedback="Good",
                            children_questions=[
                                QuestionBlock(id="q1", content="Follow-up?"),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )
    data = tree.model_dump()
    restored = BlockTree(**data)
    assert restored.blocks[0].questions[0].answer.children_questions[0].id == "q1"


def test_questions_response():
    r = QuestionsResponse(questions=["Q1?", "Q2?"])
    assert len(r.questions) == 2
    schema = QuestionsResponse.model_json_schema()
    assert "questions" in schema["properties"]


def test_evaluation_response():
    r = EvaluationResponse(score=85, feedback="Nice")
    assert r.score == 85
    schema = EvaluationResponse.model_json_schema()
    assert "score" in schema["properties"]
    assert "feedback" in schema["properties"]
