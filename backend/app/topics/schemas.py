from pydantic import BaseModel


class TopicOut(BaseModel):
    id: str
    document_id: str
    title: str
    description: str
    page_range: list[int]
