import uuid
from datetime import datetime, timezone

from pymongo.database import Database

from app.prompts.language import DEFAULT_LANGUAGE
from app.prompts.tutor_prompt import build_ask_messages, build_teach_messages
from app.rag import chroma_store
from app.services import openrouter_client


def get_or_create_chat(db: Database, user_id: str, document_id: str, topic_id: str, title: str) -> dict:
    chat = db.chats.find_one({"user_id": user_id, "document_id": document_id, "topic_id": topic_id})
    if chat:
        return chat
    now = datetime.now(timezone.utc).isoformat()
    chat = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "document_id": document_id,
        "topic_id": topic_id,
        "title": title,
        "last_message_at": now,
        "created_at": now,
    }
    db.chats.insert_one(chat)
    return chat


def list_chats(db: Database, user_id: str) -> list[dict]:
    return list(db.chats.find({"user_id": user_id}).sort("last_message_at", -1))


def list_messages(db: Database, chat_id: str) -> list[dict]:
    return list(db.messages.find({"chat_id": chat_id}).sort("created_at", 1))


def _save_message(db: Database, chat_id: str, role: str, content: str, sources: list[dict] | None = None) -> dict:
    message = {
        "_id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "sources": sources or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.messages.insert_one(message)
    db.chats.update_one({"_id": chat_id}, {"$set": {"last_message_at": message["created_at"]}})
    return message


async def retrieve_context(document_id: str, topic_id: str | None, query: str, n_results: int = 5) -> list[dict]:
    [query_embedding] = await openrouter_client.embed_texts([query])
    results = chroma_store.query(document_id, query_embedding, topic_id=topic_id, n_results=n_results)
    if not results and topic_id:
        # A topic's page range is an LLM estimate matched against word-chunk
        # boundaries, so it doesn't always tag the right chunks. Rather than
        # surface no context at all (which reads as "not in this textbook"),
        # fall back to the whole document.
        results = chroma_store.query(document_id, query_embedding, topic_id=None, n_results=n_results)
    return results


async def ask(db: Database, chat: dict, question: str, language: str = DEFAULT_LANGUAGE) -> dict:
    _save_message(db, chat["_id"], "user", question)

    # A doubt isn't necessarily about the topic the chat happens to be open
    # on, and topic tagging is imprecise (see retrieve_context) — scoping
    # strictly by topic_id caused genuinely-covered questions to come back
    # as "not in this textbook". Search the whole document instead.
    retrieved = await retrieve_context(chat["document_id"], None, question)
    messages = build_ask_messages(question, retrieved, language)
    answer = await openrouter_client.chat_completion(messages)

    sources = [{"page": r["metadata"].get("page_number")} for r in retrieved]
    return _save_message(db, chat["_id"], "assistant", answer, sources)


async def teach_topic(
    document_id: str, topic_id: str, topic_title: str, language: str = DEFAULT_LANGUAGE
) -> dict:
    retrieved = await retrieve_context(document_id, topic_id, topic_title, n_results=8)
    messages = build_teach_messages(topic_title, retrieved, language)
    explanation = await openrouter_client.chat_completion(messages)
    sources = [{"page": r["metadata"].get("page_number")} for r in retrieved]
    return {"explanation": explanation, "sources": sources}
