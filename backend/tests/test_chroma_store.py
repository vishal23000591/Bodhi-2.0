from app.rag import chroma_store


def test_add_and_query_scoped_to_document(test_settings):
    chroma_store.add_chunks(
        "doc1",
        ids=["a", "b"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        documents=["chunk about sunlight", "chunk about oxygen"],
        metadatas=[{"page_number": 1, "topic_id": "t1"}, {"page_number": 2, "topic_id": "t2"}],
    )

    results = chroma_store.query("doc1", [1.0, 0.0], n_results=1)
    assert len(results) == 1
    assert results[0]["text"] == "chunk about sunlight"
    assert results[0]["metadata"]["page_number"] == 1


def test_query_filters_by_topic_id(test_settings):
    chroma_store.add_chunks(
        "doc1",
        ids=["a", "b"],
        embeddings=[[1.0, 0.0], [0.9, 0.1]],
        documents=["sunlight chunk", "another sunlight-adjacent chunk"],
        metadatas=[{"page_number": 1, "topic_id": "t1"}, {"page_number": 2, "topic_id": "t2"}],
    )

    results = chroma_store.query("doc1", [1.0, 0.0], topic_id="t2", n_results=5)
    assert len(results) == 1
    assert results[0]["metadata"]["topic_id"] == "t2"


def test_query_is_scoped_per_document(test_settings):
    chroma_store.add_chunks(
        "doc1", ids=["a"], embeddings=[[1.0, 0.0]], documents=["doc1 chunk"],
        metadatas=[{"page_number": 1, "topic_id": ""}],
    )
    chroma_store.add_chunks(
        "doc2", ids=["a"], embeddings=[[1.0, 0.0]], documents=["doc2 chunk"],
        metadatas=[{"page_number": 1, "topic_id": ""}],
    )

    results = chroma_store.query("doc1", [1.0, 0.0], n_results=5)
    assert len(results) == 1
    assert results[0]["text"] == "doc1 chunk"
