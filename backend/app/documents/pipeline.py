"""Orchestrates the full post-upload flow: extract -> store pages ->
generate topics -> chunk -> embed -> store in ChromaDB -> mark ready.

Runs as a FastAPI BackgroundTask so /documents/upload returns immediately
with status "processing" (see architecture doc section 12, P0).
"""
import uuid

from pymongo.database import Database

from app.documents.document_service import extract_text
from app.rag import chroma_store
from app.rag.chunking import assign_topic_ids, chunk_pages
from app.rag.embeddings import embed_chunks
from app.topics.service import generate_topics


async def run_pipeline(db: Database, document_id: str, pdf_path: str, min_chars_per_page: int) -> None:
    try:
        pages, extraction_mode = extract_text(pdf_path, min_chars_per_page=min_chars_per_page)

        db.document_chunks.delete_many({"document_id": document_id})
        if pages:
            db.document_chunks.insert_many(
                [{"_id": str(uuid.uuid4()), "document_id": document_id, **p} for p in pages]
            )

        db.documents.update_one(
            {"_id": document_id},
            {"$set": {"extraction_mode": extraction_mode, "page_count": len(pages)}},
        )

        topics = await generate_topics(db, document_id, pages)

        chunks = chunk_pages(pages)
        chunks = assign_topic_ids(
            chunks, [{"topic_id": t["_id"], "page_range": t["page_range"]} for t in topics]
        )
        chunks = await embed_chunks(chunks)

        if chunks:
            chroma_store.add_chunks(
                document_id,
                ids=[c["chunk_id"] for c in chunks],
                embeddings=[c["embedding"] for c in chunks],
                documents=[c["text"] for c in chunks],
                metadatas=[
                    {"page_number": c["page_number"], "topic_id": c["topic_id"] or ""} for c in chunks
                ],
            )

        db.documents.update_one({"_id": document_id}, {"$set": {"status": "ready"}})
    except Exception as exc:
        db.documents.update_one(
            {"_id": document_id}, {"$set": {"status": "failed", "error": str(exc)}}
        )
        raise
