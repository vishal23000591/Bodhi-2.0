from pydantic import BaseModel


class OpenChatRequest(BaseModel):
    document_id: str
    topic_id: str
    title: str


class ChatOut(BaseModel):
    id: str
    document_id: str
    topic_id: str
    title: str
    last_message_at: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list[dict] = []
    created_at: str


class AskRequest(BaseModel):
    message: str
    language: str = "en"
