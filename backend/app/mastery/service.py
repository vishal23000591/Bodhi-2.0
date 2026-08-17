from datetime import datetime, timezone

from pymongo.database import Database

MASTERED_THRESHOLD = 80
IN_PROGRESS_THRESHOLD = 50


def status_for(score: float) -> str:
    if score >= MASTERED_THRESHOLD:
        return "mastered"
    if score >= IN_PROGRESS_THRESHOLD:
        return "in_progress"
    return "needs_reteach"


def recalculate_mastery(db: Database, user_id: str, topic_id: str, latest_score: int) -> dict:
    """Mastery reflects the latest check (teach-back or practice), since each
    is a fresh read of current understanding rather than a rolling average."""
    score = max(0, min(100, latest_score))
    record = {
        "user_id": user_id,
        "topic_id": topic_id,
        "mastery": score / 100,
        "status": status_for(score),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    db.student_concept_mastery.update_one(
        {"user_id": user_id, "topic_id": topic_id},
        {"$set": record},
        upsert=True,
    )
    return record


def get_mastery(db: Database, user_id: str, topic_id: str) -> dict:
    record = db.student_concept_mastery.find_one({"user_id": user_id, "topic_id": topic_id})
    if not record:
        return {
            "user_id": user_id,
            "topic_id": topic_id,
            "mastery": 0.0,
            "status": "not_started",
            "last_updated": None,
        }
    return record
