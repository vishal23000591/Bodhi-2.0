from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.mastery.service import get_mastery
from app.services.mongo_client import get_db

router = APIRouter(prefix="/topics", tags=["mastery"])


@router.get("/{topic_id}/mastery")
def mastery(
    topic_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    topic = db.topics.find_one({"_id": topic_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    record = get_mastery(db, current_user["_id"], topic_id)
    return {
        "topic_id": topic_id,
        "mastery": record["mastery"],
        "status": record["status"],
        "last_updated": record.get("last_updated"),
    }
