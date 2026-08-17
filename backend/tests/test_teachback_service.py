from app.services import openrouter_client
from app.teachback import service


async def _fake_retrieve_context(document_id, topic_id, query, n_results=5):
    return [{"text": "Photosynthesis makes glucose and oxygen.", "metadata": {"page_number": 12}}]


async def test_generate_question_stores_on_topic(mock_db, monkeypatch):
    monkeypatch.setattr(service, "retrieve_context", _fake_retrieve_context)

    async def fake_chat_completion_json(messages, **kwargs):
        return {"question": "Explain photosynthesis in your own words."}

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    mock_db.topics.insert_one({"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"})
    topic = mock_db.topics.find_one({"_id": "topic1"})

    result = await service.generate_question(mock_db, topic)

    assert result["question"] == "Explain photosynthesis in your own words."
    stored = mock_db.topics.find_one({"_id": "topic1"})
    assert stored["last_teachback_question"] == "Explain photosynthesis in your own words."


async def test_score_answer_saves_attempt_and_updates_mastery(mock_db, monkeypatch):
    monkeypatch.setattr(service, "retrieve_context", _fake_retrieve_context)

    async def fake_chat_completion_json(messages, **kwargs):
        assert "oxygen to make food" in messages[1]["content"]
        return {
            "score": 62,
            "understood": ["Sunlight is involved"],
            "partial": ["Water"],
            "misconceptions": [{"claim": "oxygen is an input", "correction": "oxygen is a product", "confidence": 0.9}],
        }

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    topic = {"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"}
    attempt = await service.score_answer(mock_db, "user1", topic, "Plants use sunlight and oxygen to make food.")

    assert attempt["score"] == 62
    assert len(attempt["misconceptions"]) == 1
    assert mock_db.teachback_attempts.count_documents({}) == 1

    mastery = mock_db.student_concept_mastery.find_one({"user_id": "user1", "topic_id": "topic1"})
    assert mastery["status"] == "in_progress"
    assert mastery["mastery"] == 0.62
