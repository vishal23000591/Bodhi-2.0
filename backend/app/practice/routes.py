from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.practice import service
from app.practice.schemas import (
    MCQOut,
    PracticeResultOut,
    PracticeSetOut,
    PracticeSubmitRequest,
    ShortAnswerOut,
)
from app.services.mongo_client import get_db

router = APIRouter(tags=["practice"])


@router.post("/topics/{topic_id}/practice/generate", response_model=PracticeSetOut, status_code=status.HTTP_201_CREATED)
async def generate(
    topic_id: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    topic = db.topics.find_one({"_id": topic_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    practice_set = await service.generate_practice_set(db, topic, current_user["_id"], language)
    return PracticeSetOut(
        id=practice_set["_id"],
        mcqs=[MCQOut(question=m["question"], options=m["options"]) for m in practice_set["mcqs"]],
        short_answers=[ShortAnswerOut(question=s["question"]) for s in practice_set["short_answers"]],
    )


@router.post("/practice/{attempt_id}/submit", response_model=PracticeResultOut)
async def submit(
    attempt_id: str,
    payload: PracticeSubmitRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    practice_set = db.practice_sets.find_one({"_id": attempt_id, "user_id": current_user["_id"]})
    if not practice_set:
        raise HTTPException(status_code=404, detail="Practice set not found")
    attempt = await service.submit_practice(db, practice_set, payload.mcq_answers, payload.short_answers)
    return PracticeResultOut(
        mcq_score=attempt["mcq_score"],
        mcq_correct_indices=attempt["mcq_correct_indices"],
        short_answer_scores=attempt["short_answer_scores"],
        short_answer_explanations=attempt["short_answer_explanations"],
        overall_score=attempt["overall_score"],
    )
