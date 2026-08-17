import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.documents.pipeline import delete_document, run_pipeline
from app.documents.schemas import DocumentOut, UploadResponse
from app.services.mongo_client import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_out(doc: dict) -> DocumentOut:
    return DocumentOut(
        id=doc["_id"],
        filename=doc["filename"],
        extraction_mode=doc.get("extraction_mode"),
        status=doc["status"],
        page_count=doc.get("page_count"),
        error=doc.get("error"),
        created_at=doc.get("created_at"),
    )


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)

    document_id = str(uuid.uuid4())
    pdf_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    content = await file.read()
    with open(pdf_path, "wb") as f:
        f.write(content)

    document = {
        "_id": document_id,
        "user_id": current_user["_id"],
        "filename": file.filename,
        "extraction_mode": None,
        "status": "processing",
        "page_count": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.documents.insert_one(document)

    background_tasks.add_task(run_pipeline, db, document_id, pdf_path, settings.min_chars_per_page)

    return UploadResponse(document_id=document_id, status="processing")


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    docs = db.documents.find({"user_id": current_user["_id"]}).sort("created_at", -1)
    return [_to_out(d) for d in docs]


@router.get("/{document_id}/status", response_model=DocumentOut)
def document_status(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.documents.find_one({"_id": document_id, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_out(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_route(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.documents.find_one({"_id": document_id, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    settings = get_settings()
    delete_document(db, document_id, settings.upload_dir)
