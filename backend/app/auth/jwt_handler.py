from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings


def create_access_token(user_id: str) -> str:
    return _create_token(user_id, get_settings().access_token_expire_minutes, "access")


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, get_settings().refresh_token_expire_minutes, "refresh")


def _create_token(user_id: str, expire_minutes: int, token_type: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
