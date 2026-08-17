from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.chat import chat_service
from app.chat.schemas import AskRequest, ChatOut, MessageOut, OpenChatRequest
from app.services.mongo_client import get_db

router = APIRouter(prefix="/chats", tags=["chat"])


def _to_chat_out(chat: dict) -> ChatOut:
    return ChatOut(
        id=chat["_id"],
        document_id=chat["document_id"],
        topic_id=chat["topic_id"],
        title=chat["title"],
        last_message_at=chat["last_message_at"],
    )


def _to_message_out(message: dict) -> MessageOut:
    return MessageOut(
        id=message["_id"],
        role=message["role"],
        content=message["content"],
        sources=message.get("sources", []),
        created_at=message["created_at"],
    )


@router.post("", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def open_chat(
    payload: OpenChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    chat = chat_service.get_or_create_chat(
        db, current_user["_id"], payload.document_id, payload.topic_id, payload.title
    )
    return _to_chat_out(chat)


@router.get("", response_model=list[ChatOut])
def get_chats(current_user: dict = Depends(get_current_user), db: Database = Depends(get_db)):
    return [_to_chat_out(c) for c in chat_service.list_chats(db, current_user["_id"])]


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    chat = db.chats.find_one({"_id": chat_id, "user_id": current_user["_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return [_to_message_out(m) for m in chat_service.list_messages(db, chat_id)]


@router.post("/{chat_id}/ask", response_model=MessageOut)
async def ask(
    chat_id: str,
    payload: AskRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    chat = db.chats.find_one({"_id": chat_id, "user_id": current_user["_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    message = await chat_service.ask(db, chat, payload.message, payload.language)
    return _to_message_out(message)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = db.chats.delete_one({"_id": chat_id, "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.messages.delete_many({"chat_id": chat_id})
