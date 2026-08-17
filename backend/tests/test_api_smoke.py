"""End-to-end smoke test across the P0 flow: signup -> upload -> topics ->
ask a doubt -> teach-back -> practice -> mastery. Mongo is mongomock,
ChromaDB is a real local instance in a temp dir, and OpenRouter is mocked
so the test doesn't need network access or a real API key.
"""
from app.services import openrouter_client


def _fake_embed_texts(dim=3):
    async def _embed(texts, **kwargs):
        return [[0.1, 0.2, 0.3] for _ in texts]

    return _embed


def _fake_chat_completion_json(monkeypatch):
    responses = {
        "topics": {
            "topics": [
                {"title": "Photosynthesis", "page_range": [1, 2], "description": "How plants make food"},
            ]
        },
        "question": {"question": "Explain photosynthesis in your own words."},
        "diagnosis": {
            "score": 70,
            "understood": ["Sunlight is involved"],
            "partial": [],
            "misconceptions": [],
        },
        "practice": {
            "mcqs": [
                {"question": f"Q{i}", "options": ["A", "B", "C", "D"], "correct_index": 0}
                for i in range(5)
            ],
            "short_answers": [{"question": "Why do plants need sunlight?"}, {"question": "What is glucose used for?"}],
        },
        "scoring": {"score": 90, "explanation": "Great answer."},
    }

    async def fake(messages, **kwargs):
        system = messages[0]["content"]
        if "curriculum designer" in system:
            return responses["topics"]
        if "your own words" in system:
            return responses["question"]
        if "diagnostic tutor" in system:
            return responses["diagnosis"]
        if "practice set" in system:
            return responses["practice"]
        if "grading a student" in system:
            return responses["scoring"]
        raise AssertionError(f"Unexpected system prompt: {system[:80]}")

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake)


def test_full_p0_flow(app_client, monkeypatch, sample_pdf_path):
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed_texts())

    async def fake_chat_completion(messages, **kwargs):
        return "Photosynthesis is how plants turn sunlight into food."

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)
    _fake_chat_completion_json(monkeypatch)

    # 1. signup
    resp = app_client.post(
        "/auth/signup",
        json={"name": "Vishal", "email": "vishal@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. upload a real copy-paste PDF; background pipeline runs synchronously
    #    within TestClient's request/response cycle
    with open(sample_pdf_path, "rb") as f:
        resp = app_client.post(
            "/documents/upload", files={"file": ("sample.pdf", f, "application/pdf")}, headers=headers
        )
    assert resp.status_code == 202
    document_id = resp.json()["document_id"]

    # 3. pipeline should have completed and marked the document ready
    resp = app_client.get(f"/documents/{document_id}/status", headers=headers)
    assert resp.status_code == 200
    status_body = resp.json()
    assert status_body["status"] == "ready", status_body
    assert status_body["extraction_mode"] == "copy_paste"
    assert status_body["page_count"] == 2

    # 4. topics were generated
    resp = app_client.get(f"/documents/{document_id}/topics", headers=headers)
    assert resp.status_code == 200
    topics = resp.json()
    assert len(topics) == 1
    topic_id = topics[0]["id"]
    assert topics[0]["title"] == "Photosynthesis"

    # 5. open a chat for the topic and ask a doubt
    resp = app_client.post(
        "/chats", json={"document_id": document_id, "topic_id": topic_id, "title": "Photosynthesis"}, headers=headers
    )
    assert resp.status_code == 201
    chat_id = resp.json()["id"]

    resp = app_client.post(f"/chats/{chat_id}/ask", json={"message": "Why do plants need sunlight?"}, headers=headers)
    assert resp.status_code == 200
    assert "Photosynthesis" in resp.json()["content"]

    resp = app_client.get(f"/chats/{chat_id}/messages", headers=headers)
    assert len(resp.json()) == 2

    resp = app_client.get("/chats", headers=headers)
    assert len(resp.json()) == 1

    # 6. teach the topic
    resp = app_client.post(f"/topics/{topic_id}/teach", headers=headers)
    assert resp.status_code == 200

    # 7. teach-back question + answer -> diagnosis
    resp = app_client.post(f"/topics/{topic_id}/teachback/question", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["question"]

    resp = app_client.post(
        f"/topics/{topic_id}/teachback/answer",
        json={"answer": "Plants use sunlight to make food."},
        headers=headers,
    )
    assert resp.status_code == 200
    diagnosis = resp.json()
    assert diagnosis["score"] == 70

    # 8. practice: generate then submit
    resp = app_client.post(f"/topics/{topic_id}/practice/generate", headers=headers)
    assert resp.status_code == 201
    practice_set = resp.json()
    assert len(practice_set["mcqs"]) == 5
    assert len(practice_set["short_answers"]) == 2
    # correct answers must never be sent to the client before submission
    assert "correct_index" not in practice_set["mcqs"][0]

    resp = app_client.post(
        f"/practice/{practice_set['id']}/submit",
        json={"mcq_answers": [0, 0, 0, 0, 0], "short_answers": ["sunlight", "energy storage"]},
        headers=headers,
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["mcq_score"] == "5/5"
    assert result["overall_score"] > 0

    # 9. mastery reflects the practice result
    resp = app_client.get(f"/topics/{topic_id}/mastery", headers=headers)
    assert resp.status_code == 200
    mastery = resp.json()
    assert mastery["status"] in ("mastered", "in_progress")

    # 10. delete chat
    resp = app_client.delete(f"/chats/{chat_id}", headers=headers)
    assert resp.status_code == 204
