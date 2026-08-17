from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import create_access_token, create_refresh_token
from app.auth.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.auth.service import AuthError, authenticate_user, create_user
from app.services.mongo_client import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Database = Depends(get_db)):
    try:
        user = create_user(db, payload)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(
        access_token=create_access_token(user["_id"]),
        refresh_token=create_refresh_token(user["_id"]),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database = Depends(get_db)):
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(
        access_token=create_access_token(user["_id"]),
        refresh_token=create_refresh_token(user["_id"]),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=current_user["_id"],
        name=current_user["name"],
        email=current_user["email"],
        grade=current_user.get("grade"),
        preferred_language=current_user.get("preferred_language", "en"),
    )
