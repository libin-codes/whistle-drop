"""Shared test fixtures for WhistleDrop API tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import seed_default_moderator
from app.database import Base, get_db
from app.main import app
from app.rate_limit import tracking_limiter


@pytest.fixture()
def db_session():
    """Yield an in-memory SQLite session, rolled back after each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    seed_default_moderator(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
async def client(db_session, tmp_path, monkeypatch):
    """Async HTTPX test client wired to the in-memory DB and a temp upload dir."""

    # Override the DB dependency
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Use a temp directory for uploads
    monkeypatch.setattr("app.routes.UPLOAD_DIR", tmp_path)

    # Reset rate limiter between tests
    tracking_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
async def auth_token(client):
    """Fixture that logs in as default moderator and yields the Bearer token."""
    from app.auth import DEFAULT_MODERATOR_PASSWORD, DEFAULT_MODERATOR_USERNAME

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": DEFAULT_MODERATOR_USERNAME, "password": DEFAULT_MODERATOR_PASSWORD},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    """Fixture providing Authorization header with valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}

