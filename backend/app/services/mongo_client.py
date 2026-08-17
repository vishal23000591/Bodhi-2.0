"""Thin wrapper around the Mongo connection so the rest of the app never
imports pymongo directly. Tests override `get_db` with a mongomock database
via FastAPI's dependency-overrides (see tests/conftest.py).
"""
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings


@lru_cache
def _client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongo_uri)


def get_db() -> Database:
    settings = get_settings()
    return _client()[settings.mongo_db_name]
