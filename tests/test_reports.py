"""Tests for POST /api/v1/reports — report creation (acceptance criteria 1-3)."""

import re

import pytest

from app.models import Report


@pytest.mark.asyncio
async def test_create_report_success(client, db_session):
    """Valid submission returns 201 with a WD-XXXX-XXXX case code."""
    resp = await client.post(
        "/api/v1/reports",
        json={
            "category": "CORRUPTION",
            "description": "Suspicious contract awarded without tender.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert re.fullmatch(r"WD-[A-Z0-9]{4}-[A-Z0-9]{4}", body["case_code"])
    assert body["message"] == "Report submitted successfully."


@pytest.mark.asyncio
async def test_create_report_with_evidence_url(client, db_session):
    """Optional evidence_url is accepted and stored."""
    resp = await client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Server credentials leaked on public repo.",
            "evidence_url": "https://example.com/evidence.png",
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_case_code_not_stored_in_db(client, db_session):
    """Plaintext case code must NOT appear in the database (ADR-0001)."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "OTHER", "description": "Test report."},
    )
    case_code = resp.json()["case_code"]

    report = db_session.query(Report).first()
    assert report is not None
    # The stored hash must NOT equal the plaintext code
    assert report.hashed_case_code != case_code
    # And the hash should be 64-char hex (SHA-256)
    assert len(report.hashed_case_code) == 64


@pytest.mark.asyncio
async def test_create_report_invalid_category(client):
    """Invalid category returns 422."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "INVALID", "description": "Something."},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_report_missing_description(client):
    """Missing description returns 422."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_report_empty_description(client):
    """Empty description returns 422."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_report_missing_category(client):
    """Missing category returns 422."""
    resp = await client.post(
        "/api/v1/reports",
        json={"description": "Something happened."},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_report_empty_body(client):
    """Empty body returns 422."""
    resp = await client.post("/api/v1/reports", json={})
    assert resp.status_code == 422
