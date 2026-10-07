"""Tests for Moderator Authentication (Issue #3 / AC 1-3)."""

from datetime import datetime, timezone
import jwt
import pytest

from app.auth import DEFAULT_MODERATOR_PASSWORD, DEFAULT_MODERATOR_USERNAME, JWT_ALGORITHM, JWT_SECRET_KEY
from app.models import Moderator


@pytest.mark.asyncio
async def test_default_moderator_seeded(db_session):
    """Default moderator account is auto-seeded in the database."""
    mod = db_session.query(Moderator).filter(Moderator.username == DEFAULT_MODERATOR_USERNAME).first()
    assert mod is not None
    assert mod.username == "moderator"
    assert mod.hashed_password is not None


@pytest.mark.asyncio
async def test_login_success(client):
    """POST /api/v1/auth/login accepts valid credentials and returns a 24h HS256 JWT."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": DEFAULT_MODERATOR_USERNAME, "password": DEFAULT_MODERATOR_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"

    # Decode and verify the JWT
    token = data["access_token"]
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == DEFAULT_MODERATOR_USERNAME
    assert payload["role"] == "MODERATOR"

    # Verify expiration is ~24 hours from now
    now = datetime.now(timezone.utc).timestamp()
    assert payload["exp"] > now
    assert payload["exp"] - now <= 24 * 3600 + 60
    assert payload["exp"] - now >= 24 * 3600 - 60


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    """POST /api/v1/auth/login rejects wrong password with 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": DEFAULT_MODERATOR_USERNAME, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """POST /api/v1/auth/login rejects unknown user with 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "unknown_moderator", "password": "any-password"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_login_missing_fields_returns_422(client):
    """POST /api/v1/auth/login rejects malformed payload with 422."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "moderator"},
    )
    assert response.status_code == 422
