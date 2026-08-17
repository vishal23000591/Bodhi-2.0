from app.services import openrouter_client

BATCH_SIZE = 64


async def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Adds an 'embedding' key to each chunk dict in place, batching calls
    to stay under request size limits."""
    texts = [c["text"] for c in chunks]
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embeddings.extend(await openrouter_client.embed_texts(batch))
    for chunk, vector in zip(chunks, embeddings):
        chunk["embedding"] = vector
    return chunks
