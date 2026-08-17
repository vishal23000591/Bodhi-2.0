from app.services import openrouter_client
from app.topics.service import generate_topics, list_topics


async def test_generate_topics_stores_and_returns(mock_db, monkeypatch):
    async def fake_chat_completion_json(messages, **kwargs):
        assert "p.1" in messages[1]["content"]
        return {
            "topics": [
                {"title": "Photosynthesis", "page_range": [1, 2], "description": "How plants make food"},
                {"title": "Respiration", "page_range": [3, 4], "description": "How cells release energy"},
            ]
        }

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    pages = [
        {"page_number": 1, "text": "Plants use sunlight."},
        {"page_number": 3, "text": "Cells release energy."},
    ]
    topics = await generate_topics(mock_db, "doc1", pages)

    assert len(topics) == 2
    assert topics[0]["title"] == "Photosynthesis"
    assert all(t["document_id"] == "doc1" for t in topics)

    stored = list_topics(mock_db, "doc1")
    assert len(stored) == 2


async def test_generate_topics_skips_llm_call_when_no_text(mock_db, monkeypatch):
    called = False

    async def fake_chat_completion_json(messages, **kwargs):
        nonlocal called
        called = True
        return {"topics": []}

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    topics = await generate_topics(mock_db, "doc1", [{"page_number": 1, "text": ""}])

    assert topics == []
    assert called is False
