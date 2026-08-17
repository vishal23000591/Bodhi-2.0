"""Verifies the Tamil/English toggle actually reaches the LLM prompts for
every student-facing tutoring flow (teach, teach-back, practice, ask-a-doubt).
Topic generation is intentionally untouched — see prompts/language.py.
"""
from app.chat import chat_service
from app.practice import service as practice_service
from app.prompts.language import language_instruction
from app.rag import chroma_store
from app.services import openrouter_client
from app.teachback import service as teachback_service


async def _fake_embed(texts, **kwargs):
    return [[1.0, 0.0] for _ in texts]


def _seed_chunk(document_id="doc1", topic_id="topic1"):
    chroma_store.add_chunks(
        document_id,
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["Photosynthesis converts sunlight into chemical energy."],
        metadatas=[{"page_number": 1, "topic_id": topic_id}],
    )


async def test_ask_passes_language_to_the_prompt(mock_db, test_settings, monkeypatch):
    _seed_chunk()
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed)

    seen = {}

    async def fake_chat_completion(messages, **kwargs):
        seen["system"] = messages[0]["content"]
        return "பதில்"

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)

    chat = chat_service.get_or_create_chat(mock_db, "user1", "doc1", "topic1", "Photosynthesis")
    await chat_service.ask(mock_db, chat, "Why do plants need sunlight?", language="ta")

    assert language_instruction("ta") in seen["system"]


async def test_teach_topic_passes_language_to_the_prompt(test_settings, monkeypatch):
    _seed_chunk()
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed)

    seen = {}

    async def fake_chat_completion(messages, **kwargs):
        seen["system"] = messages[0]["content"]
        return "விளக்கம்"

    monkeypatch.setattr(openrouter_client, "chat_completion", fake_chat_completion)

    await chat_service.teach_topic("doc1", "topic1", "Photosynthesis", language="ta")

    assert language_instruction("ta") in seen["system"]


async def test_teachback_question_and_diagnosis_pass_language(mock_db, monkeypatch):
    async def fake_retrieve_context(document_id, topic_id, query, n_results=5):
        return [{"text": "Photosynthesis makes glucose.", "metadata": {"page_number": 1}}]

    monkeypatch.setattr(teachback_service, "retrieve_context", fake_retrieve_context)

    seen = []

    async def fake_chat_completion_json(messages, **kwargs):
        seen.append(messages[0]["content"])
        return {"question": "தமிழில் கேள்வி", "score": 80, "understood": [], "partial": [], "misconceptions": []}

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    topic = {"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"}
    await teachback_service.generate_question(mock_db, topic, language="ta")
    await teachback_service.score_answer(mock_db, "user1", topic, "தாவரங்கள் சூரிய ஒளியைப் பயன்படுத்துகின்றன", language="ta")

    assert all(language_instruction("ta") in s for s in seen)


async def test_practice_generation_and_scoring_pass_language(mock_db, monkeypatch):
    async def fake_retrieve_context(document_id, topic_id, query, n_results=5):
        return [{"text": "Photosynthesis makes glucose.", "metadata": {"page_number": 1}}]

    monkeypatch.setattr(practice_service, "retrieve_context", fake_retrieve_context)
    mock_db.topics.insert_one({"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"})

    seen = []

    async def fake_chat_completion_json(messages, **kwargs):
        seen.append(messages[0]["content"])
        return {
            "mcqs": [{"question": "க1", "options": ["அ", "ஆ", "இ", "ஈ"], "correct_index": 0} for _ in range(5)],
            "short_answers": [{"question": "ஏன்?"}, {"question": "எப்படி?"}],
            "score": 90,
            "explanation": "நல்ல பதில்",
        }

    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    topic = {"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis"}
    practice_set = await practice_service.generate_practice_set(mock_db, topic, "user1", language="ta")
    assert practice_set["language"] == "ta"

    await practice_service.submit_practice(
        mock_db, practice_set, mcq_answers=[0, 0, 0, 0, 0], short_answers=["a", "b"]
    )

    assert all(language_instruction("ta") in s for s in seen)
