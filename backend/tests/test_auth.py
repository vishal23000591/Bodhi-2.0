import pytest

from app.auth.jwt_handler import create_access_token, decode_token
from app.auth.schemas import SignupRequest
from app.auth.service import AuthError, authenticate_user, create_user, hash_password, verify_password


def test_hash_password_round_trips():
    hashed = hash_password("super-secret-pw")
    assert hashed != "super-secret-pw"
    assert verify_password("super-secret-pw", hashed)
    assert not verify_password("wrong-password", hashed)


def test_create_user_then_authenticate(mock_db):
    payload = SignupRequest(name="Vishal", email="vishal@example.com", password="password123")
    user = create_user(mock_db, payload)

    assert user["email"] == "vishal@example.com"
    assert "password_hash" in user

    authenticated = authenticate_user(mock_db, "vishal@example.com", "password123")
    assert authenticated["_id"] == user["_id"]


def test_create_user_rejects_duplicate_email(mock_db):
    payload = SignupRequest(name="Vishal", email="vishal@example.com", password="password123")
    create_user(mock_db, payload)

    with pytest.raises(AuthError):
        create_user(mock_db, payload)


def test_authenticate_user_rejects_wrong_password(mock_db):
    payload = SignupRequest(name="Vishal", email="vishal@example.com", password="password123")
    create_user(mock_db, payload)

    with pytest.raises(AuthError):
        authenticate_user(mock_db, "vishal@example.com", "wrong-password")


def test_access_token_round_trips(test_settings):
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_signup_and_login_via_api(app_client):
    resp = app_client.post(
        "/auth/signup",
        json={"name": "Vishal", "email": "vishal@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens

    resp = app_client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "vishal@example.com"

    resp = app_client.post(
        "/auth/login", json={"email": "vishal@example.com", "password": "password123"}
    )
    assert resp.status_code == 200

    resp = app_client.post(
        "/auth/login", json={"email": "vishal@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_protected_route_requires_token(app_client):
    resp = app_client.get("/auth/me")
    assert resp.status_code in (401, 403)
