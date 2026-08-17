import shutil
import tempfile

import mongomock
import pytest

from app import config as config_module
from app.rag import chroma_store
from app.services import mongo_client


@pytest.fixture
def test_settings(monkeypatch, tmp_path):
    """A Settings instance pointed at throwaway resources, with the real
    lru_cache cleared so app code picks it up fresh."""
    config_module.get_settings.cache_clear()
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    settings = config_module.get_settings()
    chroma_store.reset_client()
    yield settings
    config_module.get_settings.cache_clear()
    chroma_store.reset_client()


@pytest.fixture
def mock_db(test_settings):
    """An in-memory mongomock database, standing in for MongoDB in tests."""
    client = mongomock.MongoClient()
    return client[test_settings.mongo_db_name]


@pytest.fixture
def app_client(mock_db):
    """A FastAPI TestClient with the Mongo dependency overridden to mongomock."""
    from fastapi.testclient import TestClient

    from app.main import app

    app.dependency_overrides[mongo_client.get_db] = lambda: mock_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_path(tmp_path):
    """A real, copy-paste PDF built with PyMuPDF (has a genuine text layer)."""
    import pymupdf

    doc = pymupdf.open()
    for i in range(2):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Page {i + 1}. Photosynthesis is the process by which plants convert "
            "sunlight into chemical energy, producing glucose and oxygen from "
            "carbon dioxide and water.",
        )
    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def blank_pdf_path(tmp_path):
    """A PDF with no text layer at all — simulates a scanned/image PDF."""
    import pymupdf

    doc = pymupdf.open()
    doc.new_page()
    doc.new_page()
    path = tmp_path / "blank.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)
