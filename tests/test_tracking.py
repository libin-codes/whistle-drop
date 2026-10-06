"""Tests for GET /api/v1/reports/track/{case_code} — tracking & rate limiting (AC 6-8)."""

import pytest


@pytest.mark.asyncio
async def test_track_report_success(client):
    """Valid case code returns category, status, and timestamps without internal IDs."""
    # Create a report first
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Workplace bullying incident."},
    )
    case_code = resp.json()["case_code"]

    # Track it
    resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "HARASSMENT"
    assert body["status"] == "SUBMITTED"
    assert "created_at" in body
    assert "updated_at" in body
    # Must NOT expose internal IDs
    assert "id" not in body
    assert "hashed_case_code" not in body


@pytest.mark.asyncio
async def test_track_nonexistent_case_code_returns_404(client):
    """Non-existent case code returns 404."""
    resp = await client.get("/api/v1/reports/track/WD-XXXX-YYYY")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_track_rate_limiting_returns_429(client):
    """Rapid repeated requests from the same client are throttled with 429."""
    from app.rate_limit import tracking_limiter

    # Lower the limit for testing
    tracking_limiter.max_requests = 3
    tracking_limiter.window_seconds = 60

    for _ in range(3):
        await client.get("/api/v1/reports/track/WD-FAKE-CODE")

    # The 4th request should be rate-limited
    resp = await client.get("/api/v1/reports/track/WD-FAKE-CODE")
    assert resp.status_code == 429
    assert "Too many requests" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_track_hashing_verification(client, db_session):
    """The tracking endpoint finds the report via in-memory hashing, not plaintext lookup."""
    from app.case_codes import hash_case_code
    from app.models import Report

    # Create a report
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Server outage detected."},
    )
    case_code = resp.json()["case_code"]

    # Verify the DB stores only the hash
    report = db_session.query(Report).first()
    assert report.hashed_case_code == hash_case_code(case_code)

    # Tracking with the plaintext code works
    resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert resp.status_code == 200
    assert resp.json()["category"] == "TECHNICAL"


@pytest.mark.asyncio
async def test_track_report_with_status_note(client, db_session):
    """Tracking includes status_note if one has been set."""
    from app.case_codes import hash_case_code
    from app.models import Report

    resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Security report with note."},
    )
    case_code = resp.json()["case_code"]

    # Manually attach a status_note to simulate moderator activity
    report = db_session.query(Report).filter(
        Report.hashed_case_code == hash_case_code(case_code)
    ).first()
    report.status_note = "Under active review by IT security."
    db_session.commit()

    resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert resp.status_code == 200
    assert resp.json()["status_note"] == "Under active review by IT security."

