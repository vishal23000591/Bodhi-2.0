from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    status: str


class DocumentOut(BaseModel):
    id: str
    filename: str
    extraction_mode: str | None = None
    status: str
    page_count: int | None = None
    error: str | None = None
    created_at: str | None = None
