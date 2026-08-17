import uuid
from datetime import datetime, timezone

from pymongo.database import Database

from app.chat.chat_service import retrieve_context
from app.mastery.service import recalculate_mastery
from app.prompts.language import DEFAULT_LANGUAGE
from app.prompts.practice_prompt import build_generation_messages, build_short_answer_scoring_messages
from app.prompts.tutor_prompt import format_context
from app.services import openrouter_client


async def generate_practice_set(
    db: Database, topic: dict, user_id: str, language: str = DEFAULT_LANGUAGE
) -> dict:
    retrieved = await retrieve_context(topic["document_id"], topic["_id"], topic["title"], n_results=10)
    context = format_context(retrieved)

    latest_attempt = db.teachback_attempts.find_one(
        {"user_id": user_id, "topic_id": topic["_id"]}, sort=[("created_at", -1)]
    )
    misconceptions = latest_attempt.get("misconceptions", []) if latest_attempt else []

    messages = build_generation_messages(topic["title"], context, misconceptions, language)
    data = await openrouter_client.chat_completion_json(messages)

    practice_set = {
        "_id": str(uuid.uuid4()),
        "topic_id": topic["_id"],
        "user_id": user_id,
        "mcqs": data.get("mcqs", [])[:5],
        "short_answers": data.get("short_answers", [])[:2],
        # remembered so submit_practice scores/explains in the same language
        # the questions were asked in, without needing it passed again
        "language": language,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.practice_sets.insert_one(practice_set)
    return practice_set


async def submit_practice(
    db: Database, practice_set: dict, mcq_answers: list[int], short_answers: list[str]
) -> dict:
    mcqs = practice_set["mcqs"]
    correct = sum(1 for given, mcq in zip(mcq_answers, mcqs) if given == mcq["correct_index"])
    mcq_score_label = f"{correct}/{len(mcqs)}"

    topic = db.topics.find_one({"_id": practice_set["topic_id"]})
    retrieved = await retrieve_context(topic["document_id"], topic["_id"], topic["title"], n_results=8)
    context = format_context(retrieved)
    language = practice_set.get("language", DEFAULT_LANGUAGE)

    short_answer_scores: list[int] = []
    explanations: list[str] = []
    for sa_def, sa_given in zip(practice_set["short_answers"], short_answers):
        messages = build_short_answer_scoring_messages(sa_def["question"], context, sa_given, language)
        data = await openrouter_client.chat_completion_json(messages)
        short_answer_scores.append(int(data.get("score", 0)))
        explanations.append(data.get("explanation", ""))

    mcq_pct = (correct / len(mcqs) * 100) if mcqs else 0
    short_pct = (sum(short_answer_scores) / len(short_answer_scores)) if short_answer_scores else 0
    overall_score = round((mcq_pct * 0.6) + (short_pct * 0.4)) if (mcqs or short_answer_scores) else 0

    attempt = {
        "_id": str(uuid.uuid4()),
        "user_id": practice_set["user_id"],
        "practice_set_id": practice_set["_id"],
        "mcq_answers": mcq_answers,
        "mcq_score": mcq_score_label,
        "mcq_correct_indices": [m["correct_index"] for m in mcqs],
        "short_answers": short_answers,
        "short_answer_scores": short_answer_scores,
        "short_answer_explanations": explanations,
        "overall_score": overall_score,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.practice_attempts.insert_one(attempt)
    recalculate_mastery(db, practice_set["user_id"], practice_set["topic_id"], overall_score)
    return attempt
