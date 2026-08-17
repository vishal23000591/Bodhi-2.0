import os

from app.documents.pipeline import delete_document
from app.rag import chroma_store


def _signup(app_client, email="vishal@example.com"):
    resp = app_client.post(
        "/auth/signup", json={"name": "Vishal", "email": email, "password": "password123"}
    )
    return resp.json()["access_token"], resp.json()


def _seed_full_document(mock_db, user_id, document_id="doc1", topic_id="topic1"):
    mock_db.documents.insert_one(
        {"_id": document_id, "user_id": user_id, "filename": "book.pdf", "status": "ready", "created_at": "2026-08-18T00:00:00"}
    )
    mock_db.document_chunks.insert_many(
        [{"_id": "chunk1", "document_id": document_id, "page_number": 1, "text": "hello"}]
    )
    mock_db.topics.insert_one(
        {"_id": topic_id, "document_id": document_id, "title": "Photosynthesis", "description": "", "page_range": [1, 2]}
    )
    mock_db.chats.insert_one(
        {
            "_id": "chat1",
            "user_id": user_id,
            "document_id": document_id,
            "topic_id": topic_id,
            "title": "Photosynthesis",
            "last_message_at": "2026-08-18T00:00:00",
            "created_at": "2026-08-18T00:00:00",
        }
    )
    mock_db.messages.insert_one({"_id": "msg1", "chat_id": "chat1", "role": "user", "content": "hi", "sources": [], "created_at": "2026-08-18T00:00:00"})
    mock_db.teachback_attempts.insert_one({"_id": "tb1", "user_id": user_id, "topic_id": topic_id, "score": 70})
    mock_db.practice_sets.insert_one({"_id": "ps1", "user_id": user_id, "topic_id": topic_id, "mcqs": [], "short_answers": []})
    mock_db.practice_attempts.insert_one({"_id": "pa1", "user_id": user_id, "practice_set_id": "ps1"})
    mock_db.student_concept_mastery.insert_one({"user_id": user_id, "topic_id": topic_id, "mastery": 0.7, "status": "in_progress"})


def test_delete_document_cascades_through_every_collection(mock_db, test_settings, tmp_path):
    user_id = "user1"
    document_id = "doc1"
    _seed_full_document(mock_db, user_id, document_id)

    chroma_store.add_chunks(
        document_id,
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["hello"],
        metadatas=[{"page_number": 1, "topic_id": "topic1"}],
    )

    upload_dir = str(tmp_path / "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    pdf_path = os.path.join(upload_dir, f"{document_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 fake")

    delete_document(mock_db, document_id, upload_dir)

    assert mock_db.documents.find_one({"_id": document_id}) is None
    assert mock_db.document_chunks.count_documents({"document_id": document_id}) == 0
    assert mock_db.topics.count_documents({"document_id": document_id}) == 0
    assert mock_db.chats.count_documents({"document_id": document_id}) == 0
    assert mock_db.messages.count_documents({"chat_id": "chat1"}) == 0
    assert mock_db.teachback_attempts.count_documents({"topic_id": "topic1"}) == 0
    assert mock_db.practice_sets.count_documents({"topic_id": "topic1"}) == 0
    assert mock_db.practice_attempts.count_documents({"practice_set_id": "ps1"}) == 0
    assert mock_db.student_concept_mastery.count_documents({"topic_id": "topic1"}) == 0
    assert not os.path.exists(pdf_path)

    # the chroma collection for the deleted document should no longer return
    # matches, since it was deleted entirely
    results = chroma_store.query(document_id, [1.0, 0.0], n_results=5)
    assert results == []


def test_delete_document_is_a_noop_for_missing_files(mock_db, test_settings, tmp_path):
    _seed_full_document(mock_db, "user1", "doc1")
    # no PDF actually written to disk this time
    delete_document(mock_db, "doc1", str(tmp_path / "uploads"))
    assert mock_db.documents.find_one({"_id": "doc1"}) is None


def test_delete_document_api_removes_it_and_requires_ownership(app_client, mock_db):
    token_a, _ = _signup(app_client, "a@example.com")
    token_b, _ = _signup(app_client, "b@example.com")

    user_a_id = mock_db.users.find_one({"email": "a@example.com"})["_id"]
    _seed_full_document(mock_db, user_a_id, "doc1")

    # another user can't delete someone else's document
    resp = app_client.delete("/documents/doc1", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404
    assert mock_db.documents.find_one({"_id": "doc1"}) is not None

    # the owner can
    resp = app_client.delete("/documents/doc1", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 204
    assert mock_db.documents.find_one({"_id": "doc1"}) is None

    resp = app_client.get("/documents", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.json() == []


def test_delete_nonexistent_document_returns_404(app_client):
    token, _ = _signup(app_client)
    resp = app_client.delete("/documents/does-not-exist", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
