import uuid

from pymongo.database import Database

from app.prompts.topic_prompt import build_topic_messages
from app.services import openrouter_client


async def generate_topics(db: Database, document_id: str, pages: list[dict]) -> list[dict]:
    non_empty = [p for p in pages if p["text"]]
    if not non_empty:
        return []

    full_text = "\n\n".join(f"[p.{p['page_number']}] {p['text']}" for p in non_empty)
    messages = build_topic_messages(full_text)
    data = await openrouter_client.chat_completion_json(messages)
    raw_topics = data.get("topics", [])

    topics = []
    for t in raw_topics:
        topics.append(
            {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "title": t["title"],
                "description": t.get("description", ""),
                "page_range": t.get("page_range", [1, 1]),
            }
        )
    if topics:
        db.topics.insert_many(topics)
    return topics


def list_topics(db: Database, document_id: str) -> list[dict]:
    return list(db.topics.find({"document_id": document_id}))
