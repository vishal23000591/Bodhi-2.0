"""Wrapper around a local persistent ChromaDB client — one collection per
document, so retrieval for a doubt is always scoped to that student's book.
"""
import chromadb

from app.config import get_settings

_client = None


def get_client():
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def reset_client() -> None:
    """Test-only: forces a fresh client on next get_client() call, so tests
    can point at a temp directory via a settings override."""
    global _client
    _client = None


def _collection_name(document_id: str) -> str:
    return f"doc_{document_id}"


def get_or_create_collection(document_id: str):
    return get_client().get_or_create_collection(name=_collection_name(document_id))


def add_chunks(
    document_id: str,
    *,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    collection = get_or_create_collection(document_id)
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(
    document_id: str,
    query_embedding: list[float],
    *,
    topic_id: str | None = None,
    n_results: int = 5,
) -> list[dict]:
    collection = get_or_create_collection(document_id)
    where = {"topic_id": topic_id} if topic_id else None
    result = collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where)

    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances_lists = result.get("distances") or [[]]
    dists = distances_lists[0] if distances_lists and distances_lists[0] else [None] * len(ids)

    return [
        {"chunk_id": cid, "text": text, "metadata": meta, "distance": dist}
        for cid, text, meta, dist in zip(ids, docs, metas, dists)
    ]


def delete_collection(document_id: str) -> None:
    try:
        get_client().delete_collection(name=_collection_name(document_id))
    except Exception:
        pass
