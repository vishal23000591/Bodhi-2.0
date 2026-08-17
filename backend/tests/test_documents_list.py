def _signup(app_client, email="vishal@example.com"):
    resp = app_client.post(
        "/auth/signup", json={"name": "Vishal", "email": email, "password": "password123"}
    )
    return resp.json()["access_token"]


def test_list_documents_returns_only_the_current_users_documents_newest_first(app_client, mock_db):
    token_a = _signup(app_client, "a@example.com")
    token_b = _signup(app_client, "b@example.com")

    mock_db.documents.insert_many(
        [
            {
                "_id": "doc1",
                "user_id": mock_db.users.find_one({"email": "a@example.com"})["_id"],
                "filename": "Chapter 3.pdf",
                "status": "ready",
                "extraction_mode": "copy_paste",
                "page_count": 10,
                "created_at": "2026-08-17T10:00:00+00:00",
            },
            {
                "_id": "doc2",
                "user_id": mock_db.users.find_one({"email": "a@example.com"})["_id"],
                "filename": "Chapter 4.pdf",
                "status": "processing",
                "extraction_mode": None,
                "page_count": None,
                "created_at": "2026-08-18T09:00:00+00:00",
            },
            {
                "_id": "doc3",
                "user_id": mock_db.users.find_one({"email": "b@example.com"})["_id"],
                "filename": "Someone Else's Book.pdf",
                "status": "ready",
                "extraction_mode": "copy_paste",
                "page_count": 5,
                "created_at": "2026-08-18T08:00:00+00:00",
            },
        ]
    )

    resp = app_client.get("/documents", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    docs = resp.json()
    assert [d["id"] for d in docs] == ["doc2", "doc1"]
    assert all(d["filename"] != "Someone Else's Book.pdf" for d in docs)

    resp = app_client.get("/documents", headers={"Authorization": f"Bearer {token_b}"})
    assert [d["id"] for d in resp.json()] == ["doc3"]


def test_list_documents_empty_for_new_user(app_client):
    token = _signup(app_client)
    resp = app_client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_upload_stores_created_at_and_status_reflects_it(app_client, sample_pdf_path, monkeypatch):
    from app.services import openrouter_client

    async def fake_embed(texts, **kwargs):
        return [[0.1, 0.2] for _ in texts]

    async def fake_chat_completion_json(messages, **kwargs):
        return {"topics": []}

    monkeypatch.setattr(openrouter_client, "embed_texts", fake_embed)
    monkeypatch.setattr(openrouter_client, "chat_completion_json", fake_chat_completion_json)

    token = _signup(app_client)
    with open(sample_pdf_path, "rb") as f:
        resp = app_client.post(
            "/documents/upload",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    document_id = resp.json()["document_id"]

    resp = app_client.get(f"/documents/{document_id}/status", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["created_at"] is not None
