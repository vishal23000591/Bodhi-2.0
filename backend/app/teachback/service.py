import uuid
from datetime import datetime, timezone

from pymongo.database import Database

from app.chat.chat_service import retrieve_context
from app.mastery.service import recalculate_mastery
from app.prompts.language import DEFAULT_LANGUAGE
from app.prompts.teachback_prompt import build_diagnosis_messages, build_question_messages
from app.prompts.tutor_prompt import format_context
from app.services import openrouter_client


async def generate_question(db: Database, topic: dict, language: str = DEFAULT_LANGUAGE) -> dict:
    retrieved = await retrieve_context(topic["document_id"], topic["_id"], topic["title"], n_results=8)
    context = format_context(retrieved)
    messages = build_question_messages(topic["title"], context, language)
    data = await openrouter_client.chat_completion_json(messages)
    question = data["question"]
    db.topics.update_one({"_id": topic["_id"]}, {"$set": {"last_teachback_question": question}})
    return {"question": question}


async def score_answer(
    db: Database, user_id: str, topic: dict, answer: str, language: str = DEFAULT_LANGUAGE
) -> dict:
    retrieved = await retrieve_context(topic["document_id"], topic["_id"], topic["title"], n_results=8)
    context = format_context(retrieved)
    question = topic.get("last_teachback_question") or topic["title"]

    messages = build_diagnosis_messages(topic["title"], context, answer, language)
    data = await openrouter_client.chat_completion_json(messages)

    attempt = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "topic_id": topic["_id"],
        "question": question,
        "answer": answer,
        "score": int(data.get("score", 0)),
        "understood": data.get("understood", []),
        "partial": data.get("partial", []),
        "misconceptions": data.get("misconceptions", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.teachback_attempts.insert_one(attempt)
    recalculate_mastery(db, user_id, topic["_id"], attempt["score"])
    return attempt
