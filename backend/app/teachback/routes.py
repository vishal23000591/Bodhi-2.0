from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.chat.chat_service import teach_topic
from app.services.mongo_client import get_db
from app.teachback import service
from app.teachback.schemas import TeachbackAnswerRequest, TeachbackQuestionOut, TeachbackResultOut, TeachOut

router = APIRouter(prefix="/topics", tags=["teachback"])


def _get_topic_or_404(db: Database, topic_id: str) -> dict:
    topic = db.topics.find_one({"_id": topic_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/{topic_id}/teach", response_model=TeachOut)
async def teach(
    topic_id: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    topic = _get_topic_or_404(db, topic_id)
    return await teach_topic(topic["document_id"], topic["_id"], topic["title"], language)


@router.post("/{topic_id}/teachback/question", response_model=TeachbackQuestionOut)
async def teachback_question(
    topic_id: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    topic = _get_topic_or_404(db, topic_id)
    return await service.generate_question(db, topic, language)


@router.post("/{topic_id}/teachback/answer", response_model=TeachbackResultOut)
async def teachback_answer(
    topic_id: str,
    payload: TeachbackAnswerRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    topic = _get_topic_or_404(db, topic_id)
    attempt = await service.score_answer(db, current_user["_id"], topic, payload.answer, payload.language)
    return TeachbackResultOut(
        score=attempt["score"],
        understood=attempt["understood"],
        partial=attempt["partial"],
        misconceptions=attempt["misconceptions"],
    )
