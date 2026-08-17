"""Pure, side-effect-free text chunking and topic-tagging. Kept separate
from embeddings/storage so it's trivially unit-testable.
"""

DEFAULT_CHUNK_SIZE_WORDS = 220
DEFAULT_OVERLAP_WORDS = 30


def chunk_pages(
    pages: list[dict],
    *,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[dict]:
    """Chunks extracted page text into overlapping word-count windows,
    keeping page_number as metadata. ~220 words is roughly 500-800 tokens
    depending on language, matching the architecture doc's target."""
    chunks: list[dict] = []
    chunk_index = 0
    for page in pages:
        words = page["text"].split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(start + chunk_size_words, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(
                {
                    "chunk_id": f"{page['page_number']}_{chunk_index}",
                    "text": chunk_text,
                    "page_number": page["page_number"],
                }
            )
            chunk_index += 1
            if end == len(words):
                break
            start = end - overlap_words
    return chunks


def assign_topic_ids(chunks: list[dict], topics: list[dict]) -> list[dict]:
    """Tags each chunk with the id of the topic whose page_range contains
    it. `topics` items need "topic_id" and "page_range": [lo, hi]."""
    for chunk in chunks:
        chunk["topic_id"] = None
        for topic in topics:
            page_range = topic.get("page_range") or [None, None]
            lo, hi = (page_range + [None, None])[:2]
            if lo is not None and hi is not None and lo <= chunk["page_number"] <= hi:
                chunk["topic_id"] = topic["topic_id"]
                break
    return chunks
