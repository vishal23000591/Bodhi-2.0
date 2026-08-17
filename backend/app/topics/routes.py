from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.services.mongo_client import get_db
from app.topics.schemas import TopicOut
from app.topics.service import generate_topics, list_topics

router = APIRouter(prefix="/documents", tags=["topics"])


def _to_out(t: dict) -> TopicOut:
    return TopicOut(
        id=t["_id"],
        document_id=t["document_id"],
        title=t["title"],
        description=t["description"],
        page_range=t["page_range"],
    )


@router.get("/{document_id}/topics", response_model=list[TopicOut])
def get_topics(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.documents.find_one({"_id": document_id, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return [_to_out(t) for t in list_topics(db, document_id)]


@router.post("/{document_id}/topics/generate", response_model=list[TopicOut], status_code=status.HTTP_201_CREATED)
async def regenerate_topics(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.documents.find_one({"_id": document_id, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = list(db.document_chunks.find({"document_id": document_id}).sort("page_number", 1))
    if not pages:
        raise HTTPException(status_code=409, detail="Document has not finished extraction yet")

    db.topics.delete_many({"document_id": document_id})
    topics = await generate_topics(db, document_id, pages)
    return [_to_out(t) for t in topics]
