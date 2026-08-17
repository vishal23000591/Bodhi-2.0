from app.rag.chunking import assign_topic_ids, chunk_pages


def test_chunk_pages_respects_word_window():
    pages = [{"page_number": 1, "text": " ".join(f"word{i}" for i in range(500))}]
    chunks = chunk_pages(pages, chunk_size_words=220, overlap_words=30)

    assert len(chunks) > 1
    assert all(chunk["page_number"] == 1 for chunk in chunks)
    first_words = chunks[0]["text"].split()
    assert len(first_words) == 220


def test_chunk_pages_skips_empty_pages():
    pages = [
        {"page_number": 1, "text": "some real content here"},
        {"page_number": 2, "text": ""},
    ]
    chunks = chunk_pages(pages)
    assert {c["page_number"] for c in chunks} == {1}


def test_chunk_pages_short_page_produces_single_chunk():
    pages = [{"page_number": 1, "text": "just a few words"}]
    chunks = chunk_pages(pages, chunk_size_words=220, overlap_words=30)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "just a few words"


def test_assign_topic_ids_matches_page_range():
    chunks = [
        {"chunk_id": "1_0", "page_number": 1, "text": "a"},
        {"chunk_id": "5_0", "page_number": 5, "text": "b"},
        {"chunk_id": "12_0", "page_number": 12, "text": "c"},
    ]
    topics = [
        {"topic_id": "t1", "page_range": [1, 4]},
        {"topic_id": "t2", "page_range": [5, 10]},
    ]
    tagged = assign_topic_ids(chunks, topics)

    assert tagged[0]["topic_id"] == "t1"
    assert tagged[1]["topic_id"] == "t2"
    assert tagged[2]["topic_id"] is None
