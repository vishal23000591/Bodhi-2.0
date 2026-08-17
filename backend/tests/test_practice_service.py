from app.practice import service
from app.services import openrouter_client


async def _fake_retrieve_context(document_id, topic_id, query, n_results=5):
    return [{"text": "Photosynthesis makes glucose and oxygen.", "metadata": {"page_number": 12}}]


def _sample_mcqs():
    return [
        {"question": f"Q{i}", "options": ["A", "B", "C", "D"], "correct_index": 0}
        for i in range(5)
    ]


async def test_generate_practice_set_uses_latest_misconception(mock_db, monkeypatch):
    monkeypatch.setattr(service, "retrieve_context", _fake_retrieve_context)

    mock_db.teachback_attempts.insert_one(
        {
            "user_id": "user1",
            "topic_id": "topic1",
            "misconceptions": [{"claim": "oxygen is an input", "correction": "oxygen is a product"}],
            "created_at": "2026-08-18T00:00:00",
        }
    )

    seen_messages = {}

    async def fake_chat_completion_json(messages, **kwargs):
        seen_messages["content"] = messages[1]["content"]
        return {"mcqs": _sample_mcqs(), "short_answers": [{"question": "Why?"}, {"question": "How?"}]}

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    topic = {"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"}
    practice_set = await service.generate_practice_set(mock_db, topic, "user1")

    assert len(practice_set["mcqs"]) == 5
    assert len(practice_set["short_answers"]) == 2
    assert "oxygen is an input" in seen_messages["content"]


async def test_submit_practice_scores_mcqs_and_short_answers(mock_db, monkeypatch):
    monkeypatch.setattr(service, "retrieve_context", _fake_retrieve_context)

    mock_db.topics.insert_one({"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"})

    async def fake_chat_completion_json(messages, **kwargs):
        return {"score": 80, "explanation": "Good answer."}

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    practice_set = {
        "_id": "ps1",
        "user_id": "user1",
        "topic_id": "topic1",
        "mcqs": _sample_mcqs(),
        "short_answers": [{"question": "Why?"}, {"question": "How?"}],
    }

    attempt = await service.submit_practice(
        mock_db,
        practice_set,
        mcq_answers=[0, 0, 1, 1, 0],
        short_answers=["because sunlight", "via chlorophyll"],
    )

    assert attempt["mcq_score"] == "3/5"
    assert attempt["short_answer_scores"] == [80, 80]
    # overall = mcq_pct(60) * 0.6 + short_pct(80) * 0.4 = 36 + 32 = 68
    assert attempt["overall_score"] == 68

    mastery = mock_db.student_concept_mastery.find_one({"user_id": "user1", "topic_id": "topic1"})
    assert mastery["mastery"] == 0.68
