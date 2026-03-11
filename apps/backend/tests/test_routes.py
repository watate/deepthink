import pytest

from apps.backend.models import QuestionBlock


pytestmark = pytest.mark.anyio


# --- POST /api/trees ---


async def test_create_tree(client, mock_s3, mock_llm):
    resp = await client.post(
        "/api/trees",
        json={"title": "My Essay", "text": "Block one content.\n\nBlock two content."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "My Essay"
    assert len(data["blocks"]) == 2
    assert len(data["blocks"][0]["questions"]) == 2
    assert len(data["blocks"][1]["questions"]) == 2
    mock_s3["save"].assert_awaited_once()
    mock_llm["split"].assert_called_once()
    mock_llm["gen_for_blocks"].assert_awaited_once()


async def test_create_tree_custom_num_questions(client, mock_s3, mock_llm):
    mock_llm["gen_for_blocks"].return_value = [
        ["Q1?", "Q2?", "Q3?"],
        ["Q4?", "Q5?", "Q6?"],
    ]
    resp = await client.post(
        "/api/trees",
        json={
            "title": "Essay",
            "text": "Block one.\n\nBlock two.",
            "num_questions": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["num_questions"] == 3


# --- GET /api/trees ---


async def test_list_trees(client, mock_s3, sample_tree):
    mock_s3["list"].return_value = [sample_tree.model_dump()]
    resp = await client.get("/api/trees")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == "tree-1"
    assert items[0]["title"] == "Test Essay"
    assert items[0]["num_blocks"] == 2
    assert items[0]["num_questions"] == 3  # 2 + 1


async def test_list_trees_empty(client, mock_s3):
    mock_s3["list"].return_value = []
    resp = await client.get("/api/trees")
    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /api/trees/search ---


async def test_search_trees_match_title(client, mock_s3, sample_tree):
    mock_s3["list"].return_value = [sample_tree.model_dump()]
    resp = await client.get("/api/trees/search", params={"q": "test"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_search_trees_match_text(client, mock_s3, sample_tree):
    mock_s3["list"].return_value = [sample_tree.model_dump()]
    resp = await client.get("/api/trees/search", params={"q": "block one"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_search_trees_no_match(client, mock_s3, sample_tree):
    mock_s3["list"].return_value = [sample_tree.model_dump()]
    resp = await client.get("/api/trees/search", params={"q": "nonexistent"})
    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /api/trees/{tree_id} ---


async def test_get_tree(client, mock_s3, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.get("/api/trees/tree-1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "tree-1"
    assert len(resp.json()["blocks"]) == 2


async def test_get_tree_not_found(client, mock_s3):
    mock_s3["load"].return_value = None
    resp = await client.get("/api/trees/missing")
    assert resp.status_code == 404


# --- DELETE /api/trees/{tree_id} ---


async def test_delete_tree(client, mock_s3):
    resp = await client.delete("/api/trees/tree-1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    mock_s3["delete"].assert_awaited_once_with("tree-1")


# --- POST /api/trees/{tree_id}/blocks/{block_id}/questions ---


async def test_generate_questions_for_title_block(
    client, mock_s3, mock_llm, sample_tree
):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/blocks/tree-1-b0/questions",
        json={"num_questions": 1},
    )
    assert resp.status_code == 200
    # Original 2 questions + 1 new
    block0 = resp.json()["blocks"][0]
    assert len(block0["questions"]) == 3
    assert block0["questions"][2]["content"] == "New question?"
    mock_s3["save"].assert_awaited_once()


async def test_generate_questions_for_answer_block(
    client, mock_s3, mock_llm, answered_tree
):
    mock_s3["load"].return_value = answered_tree.model_dump()
    answer_id = "tree-1-b0-q0-a"
    resp = await client.post(
        f"/api/trees/tree-1/blocks/{answer_id}/questions",
        json={"num_questions": 1},
    )
    assert resp.status_code == 200
    answer = resp.json()["blocks"][0]["questions"][0]["answer"]
    assert len(answer["children_questions"]) == 1
    assert answer["children_questions"][0]["content"] == "New question?"


async def test_generate_questions_block_not_found(
    client, mock_s3, mock_llm, sample_tree
):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/blocks/nonexistent/questions",
        json={"num_questions": 1},
    )
    assert resp.status_code == 404


# --- POST /api/trees/{tree_id}/questions/{question_id}/answer ---


async def test_submit_answer(client, mock_s3, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/questions/tree-1-b0-q0/answer",
        json={"content": "My deep answer."},
    )
    assert resp.status_code == 200
    answer = resp.json()["blocks"][0]["questions"][0]["answer"]
    assert answer["content"] == "My deep answer."
    assert answer["id"] == "tree-1-b0-q0-a"
    mock_s3["save"].assert_awaited_once()


async def test_resubmit_answer_replaces_and_wipes_children(
    client, mock_s3, answered_tree
):
    # Add a child question to the existing answer
    answered_tree.blocks[0].questions[0].answer.children_questions = [
        QuestionBlock(id="child-q", content="Child question?")
    ]
    mock_s3["load"].return_value = answered_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/questions/tree-1-b0-q0/answer",
        json={"content": "Rewritten answer."},
    )
    assert resp.status_code == 200
    answer = resp.json()["blocks"][0]["questions"][0]["answer"]
    assert answer["content"] == "Rewritten answer."
    assert answer["score"] is None
    assert answer["feedback"] is None
    assert answer["children_questions"] == []
    mock_s3["save"].assert_awaited_once()


async def test_submit_answer_question_not_found(client, mock_s3, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/questions/nonexistent/answer",
        json={"content": "Answer."},
    )
    assert resp.status_code == 404


# --- POST /api/trees/{tree_id}/answers/{answer_id}/evaluate ---


async def test_evaluate_answer(client, mock_s3, mock_llm, answered_tree):
    mock_s3["load"].return_value = answered_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/answers/tree-1-b0-q0-a/evaluate",
        json={},
    )
    assert resp.status_code == 200
    answer = resp.json()["blocks"][0]["questions"][0]["answer"]
    assert answer["score"] == 85
    assert answer["feedback"] == "Great answer."
    mock_llm["evaluate"].assert_awaited_once()
    mock_s3["save"].assert_awaited_once()


async def test_evaluate_answer_not_found(client, mock_s3, mock_llm, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post(
        "/api/trees/tree-1/answers/nonexistent/evaluate",
        json={},
    )
    assert resp.status_code == 404


# --- POST /api/trees/{tree_id}/export ---


async def test_export_tree(client, mock_s3, evaluated_tree, tmp_path, monkeypatch):
    mock_s3["load"].return_value = evaluated_tree.model_dump()
    import apps.backend.routes as routes_mod

    monkeypatch.setattr(
        routes_mod,
        "Path",
        lambda p: tmp_path / "exports" if "exports" in str(p) else tmp_path,
    )

    resp = await client.post("/api/trees/tree-1/export")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# --- POST /api/backup/save ---


async def test_backup_save(client, mock_s3, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.post("/api/backup/save", params={"tree_id": "tree-1"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    mock_s3["save"].assert_awaited_once()


# --- GET /api/backup/{tree_id} ---


async def test_backup_load(client, mock_s3, sample_tree):
    mock_s3["load"].return_value = sample_tree.model_dump()
    resp = await client.get("/api/backup/tree-1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "tree-1"


async def test_backup_load_not_found(client, mock_s3):
    mock_s3["load"].return_value = None
    resp = await client.get("/api/backup/missing")
    assert resp.status_code == 404
