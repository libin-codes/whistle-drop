"""Authentication routes for moderators."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, verify_password
from app.database import get_db
from app.models import Moderator
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate moderator and return a 24-hour HS256 JWT access token."""
    moderator = (
        db.query(Moderator)
        .filter(Moderator.username == payload.username)
        .first()
    )
    if not moderator or not verify_password(payload.password, moderator.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": moderator.username, "role": "MODERATOR"}
    )
    return TokenResponse(access_token=access_token, token_type="bearer", expires_in=86400)
