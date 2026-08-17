import uuid
from datetime import datetime, timezone

import bcrypt
from pymongo.database import Database

from app.auth.schemas import SignupRequest


class AuthError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_user(db: Database, payload: SignupRequest) -> dict:
    if db.users.find_one({"email": payload.email}):
        raise AuthError("An account with this email already exists")

    user = {
        "_id": str(uuid.uuid4()),
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "grade": payload.grade,
        "preferred_language": payload.preferred_language,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.users.insert_one(user)
    return user


def authenticate_user(db: Database, email: str, password: str) -> dict:
    user = db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        raise AuthError("Invalid email or password")
    return user
