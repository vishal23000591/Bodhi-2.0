from app.chat import chat_service
from app.rag import chroma_store
from app.services import openrouter_client


def _fake_embed(vector):
    async def _embed(texts, **kwargs):
        return [vector for _ in texts]

    return _embed


async def test_get_or_create_chat_is_idempotent(mock_db):
    chat1 = chat_service.get_or_create_chat(mock_db, "user1", "doc1", "topic1", "Photosynthesis")
    chat2 = chat_service.get_or_create_chat(mock_db, "user1", "doc1", "topic1", "Photosynthesis")
    assert chat1["_id"] == chat2["_id"]
    assert mock_db.chats.count_documents({}) == 1


async def test_ask_saves_question_and_grounded_answer(mock_db, test_settings, monkeypatch):
    chroma_store.add_chunks(
        "doc1",
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["Photosynthesis converts sunlight into chemical energy."],
        metadatas=[{"page_number": 12, "topic_id": "topic1"}],
    )

    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed([1.0, 0.0]))

    async def fake_chat_completion(messages, **kwargs):
        assert "sunlight into chemical energy" in messages[1]["content"]
        return "Plants use sunlight to make food."

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)

    chat = chat_service.get_or_create_chat(mock_db, "user1", "doc1", "topic1", "Photosynthesis")
    answer_message = await chat_service.ask(mock_db, chat, "How do plants make food?")

    assert answer_message["role"] == "assistant"
    assert answer_message["content"] == "Plants use sunlight to make food."
    assert answer_message["sources"] == [{"page": 12}]

    messages = chat_service.list_messages(mock_db, chat["_id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "How do plants make food?"
    assert messages[1]["role"] == "assistant"


async def test_ask_finds_chunks_regardless_of_their_topic_tag(mock_db, test_settings, monkeypatch):
    """A doubt should be answered from the whole book, not just chunks that
    happen to be tagged with the chat's current topic — topic tagging is an
    imprecise LLM page-range estimate, and scoping to it caused genuinely
    textbook-covered questions to be wrongly answered as 'not covered'."""
    chroma_store.add_chunks(
        "doc1",
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["Photosynthesis converts sunlight into chemical energy."],
        metadatas=[{"page_number": 12, "topic_id": "some-other-topic"}],
    )
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed([1.0, 0.0]))

    async def fake_chat_completion(messages, **kwargs):
        return "Plants use sunlight to make food."

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)

    chat = chat_service.get_or_create_chat(mock_db, "user1", "doc1", "topic1", "Photosynthesis")
    answer_message = await chat_service.ask(mock_db, chat, "How do plants make food?")

    assert answer_message["content"] == "Plants use sunlight to make food."
    assert answer_message["sources"] == [{"page": 12}]


async def test_retrieve_context_falls_back_to_whole_document_when_topic_scope_is_empty(test_settings, monkeypatch):
    chroma_store.add_chunks(
        "doc1",
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["Cellular respiration releases energy from glucose."],
        metadatas=[{"page_number": 3, "topic_id": "respiration-topic"}],
    )
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed([1.0, 0.0]))

    results = await chat_service.retrieve_context("doc1", "photosynthesis-topic", "some query")

    assert len(results) == 1
    assert results[0]["text"] == "Cellular respiration releases energy from glucose."


async def test_teach_topic_returns_explanation_with_sources(test_settings, monkeypatch):
    chroma_store.add_chunks(
        "doc1",
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["Plants absorb sunlight through chlorophyll."],
        metadatas=[{"page_number": 4, "topic_id": "topic1"}],
    )
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed([1.0, 0.0]))

    async def fake_chat_completion(messages, **kwargs):
        return "Here's how photosynthesis works..."

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)

    result = await chat_service.teach_topic("doc1", "topic1", "Photosynthesis")
    assert result["explanation"] == "Here's how photosynthesis works..."
    assert result["sources"] == [{"page": 4}]
