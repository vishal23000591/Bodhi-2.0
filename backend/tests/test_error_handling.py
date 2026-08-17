"""Unhandled exceptions raised inside a route are caught by Starlette's
outermost ServerErrorMiddleware, which sits *outside* CORSMiddleware — so
their response never gets CORS headers, and a browser reports what is
really a server error as a confusing CORS failure. app/main.py registers
explicit exception handlers so these get routed through ExceptionMiddleware
(inside CORSMiddleware) instead. These tests pin that behavior.
"""
from fastapi.testclient import TestClient

from app.auth.jwt_handler import create_access_token
from app.main import app
from app.services import openrouter_client
from app.services.openrouter_client import OpenRouterError


def _auth_headers(mock_db):
    mock_db.users.insert_one({"_id": "user1", "name": "Test", "email": "t@example.com", "password_hash": "x"})
    token = create_access_token("user1")
    return {"Origin": "http://localhost:5173", "Authorization": f"Bearer {token}"}


def _seed_topic(mock_db):
    mock_db.documents.insert_one({"_id": "doc1", "user_id": "user1", "filename": "book.pdf", "status": "ready"})
    mock_db.topics.insert_one({"_id": "topic1", "document_id": "doc1", "title": "Photosynthesis", "description": "", "page_range": [1, 2]})


async def _fake_embed(texts, **kwargs):
    return [[1.0, 0.0] for _ in texts]


def test_openrouter_error_returns_502_with_cors_headers(app_client, mock_db, monkeypatch):
    _seed_topic(mock_db)
    monkeypatch.setattr(openrouter_client, "embed_texts", _fake_embed)

    async def failing_chat_completion(messages, **kwargs):
        raise OpenRouterError("OpenRouter request failed (429): Rate limit exceeded")

    monkeypatch.setattr(openrouter_client, "chat_completion", failing_chat_completion)

    resp = app_client.post("/topics/topic1/teach", headers=_auth_headers(mock_db))

    assert resp.status_code == 502
    assert "Rate limit exceeded" in resp.json()["detail"]
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_unexpected_error_returns_500_with_cors_headers(app_client, mock_db, monkeypatch):
    """A handler registered for the base Exception class is wired into
    Starlette's ServerErrorMiddleware, which always re-raises in Python
    after sending its response (so ASGI servers/tests can still see it for
    logging) — a real browser only ever sees the response that was sent, so
    this uses a client with raise_server_exceptions=False to inspect that,
    same as app_client but without the debug re-raise."""
    _seed_topic(mock_db)

    async def failing_embed(texts, **kwargs):
        raise RuntimeError("something unrelated broke")

    monkeypatch.setattr(openrouter_client, "embed_texts", failing_embed)

    lenient_client = TestClient(app, raise_server_exceptions=False)
    resp = lenient_client.post("/topics/topic1/teach", headers=_auth_headers(mock_db))

    assert resp.status_code == 500
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    # the raw exception message must never leak to the client
    assert "something unrelated broke" not in resp.text
