"""Authentication, password hashing, JWT operations, and auto-seeding for Moderators."""

from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Moderator

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "whistledrop-jwt-moderator-secret-key-32b"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

DEFAULT_MODERATOR_USERNAME = os.getenv("MODERATOR_USERNAME", "moderator")
DEFAULT_MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD", "moderator123")

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        salt, expected_hex = hashed_password.split("$", 1)
        actual_dk = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return secrets.compare_digest(actual_dk.hex(), expected_hex)
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed HS256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an HS256 JWT access token."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def seed_default_moderator(db: Session) -> Moderator:
    """Auto-seed the default moderator account if it does not exist."""
    moderator = (
        db.query(Moderator)
        .filter(Moderator.username == DEFAULT_MODERATOR_USERNAME)
        .first()
    )
    if not moderator:
        moderator = Moderator(
            username=DEFAULT_MODERATOR_USERNAME,
            hashed_password=hash_password(DEFAULT_MODERATOR_PASSWORD),
        )
        db.add(moderator)
        db.commit()
        db.refresh(moderator)
    return moderator


def get_current_moderator(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Moderator:
    """FastAPI dependency: require and validate a Moderator Bearer JWT token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    moderator = db.query(Moderator).filter(Moderator.username == username).first()
    if not moderator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Moderator not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return moderator
