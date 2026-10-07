"""Tests for Moderator Report Review & Authorization (Issue #3 / AC 3-6)."""

import pytest


@pytest.mark.asyncio
async def test_moderator_routes_require_auth(client):
    """Moderator routes return 401 when Authorization header is missing or invalid."""
    # Missing auth header
    resp = await client.get("/api/v1/moderator/reports")
    assert resp.status_code == 401
    assert "detail" in resp.json()

    # Invalid token
    resp = await client.get(
        "/api/v1/moderator/reports",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code == 401

    # Missing on detail route
    resp = await client.get("/api/v1/moderator/reports/1")
    assert resp.status_code == 401

    # Missing on status patch route
    resp = await client.patch(
        "/api/v1/moderator/reports/1/status",
        json={"status": "UNDER_REVIEW"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_reports_empty(client, auth_headers):
    """GET /api/v1/moderator/reports returns empty list when no reports exist."""
    resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_reports_pagination(client, auth_headers):
    """Pagination with limit and offset retrieves correct slices of reports."""
    for i in range(5):
        await client.post(
            "/api/v1/reports",
            json={"category": "SECURITY", "description": f"Security report #{i}"},
        )

    # First page: limit 2, offset 0
    resp = await client.get(
        "/api/v1/moderator/reports?limit=2&offset=0",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    page1 = resp.json()
    assert len(page1) == 2
    assert page1[0]["description"] == "Security report #0"
    assert page1[1]["description"] == "Security report #1"

    # Second page: limit 2, offset 2
    resp = await client.get(
        "/api/v1/moderator/reports?limit=2&offset=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    page2 = resp.json()
    assert len(page2) == 2
    assert page2[0]["description"] == "Security report #2"
    assert page2[1]["description"] == "Security report #3"

    # Third page: limit 2, offset 4
    resp = await client.get(
        "/api/v1/moderator/reports?limit=2&offset=4",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    page3 = resp.json()
    assert len(page3) == 1
    assert page3[0]["description"] == "Security report #4"


@pytest.mark.asyncio
async def test_list_reports_filter_by_category(client, auth_headers):
    """Reports can be filtered by category (case-insensitive)."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Security incident"},
    )
    await client.post(
        "/api/v1/reports",
        json={"category": "CORRUPTION", "description": "Corruption incident"},
    )

    # Filter category=SECURITY
    resp = await client.get(
        "/api/v1/moderator/reports?category=SECURITY",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["category"] == "SECURITY"

    # Filter category=corruption (lowercase)
    resp = await client.get(
        "/api/v1/moderator/reports?category=corruption",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["category"] == "CORRUPTION"


@pytest.mark.asyncio
async def test_list_reports_filter_by_status(client, auth_headers, db_session):
    """Reports can be filtered by status."""
    from app.models import Report, StatusEnum

    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Submitted report"},
    )
    await client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Under review report"},
    )

    # Manually change the second report status in DB to UNDER_REVIEW
    rep2 = db_session.query(Report).filter(Report.description == "Under review report").first()
    rep2.status = StatusEnum.UNDER_REVIEW
    db_session.commit()

    resp = await client.get(
        "/api/v1/moderator/reports?status=UNDER_REVIEW",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["description"] == "Under review report"
    assert items[0]["status"] == "UNDER_REVIEW"


@pytest.mark.asyncio
async def test_moderator_endpoints_expose_no_reporter_identifiers(client, auth_headers):
    """No IP address, client headers, or hashed case codes are exposed to moderators."""
    await client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Confidential harassment report"},
    )

    resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    assert resp.status_code == 200
    report = resp.json()[0]

    forbidden_fields = {"ip", "client_ip", "reporter_ip", "user_agent", "case_code", "hashed_case_code"}
    for field in forbidden_fields:
        assert field not in report


@pytest.mark.asyncio
async def test_get_report_detail_success(client, auth_headers):
    """GET /api/v1/moderator/reports/{report_id} returns full report details."""
    await client.post(
        "/api/v1/reports",
        json={
            "category": "CORRUPTION",
            "description": "Bribery evidence in procurement.",
            "evidence_url": "/uploads/evidence-123.jpg",
        },
    )

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    detail_resp = await client.get(
        f"/api/v1/moderator/reports/{report_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["id"] == report_id
    assert body["category"] == "CORRUPTION"
    assert body["description"] == "Bribery evidence in procurement."
    assert body["evidence_url"] == "/uploads/evidence-123.jpg"
    assert body["status"] == "SUBMITTED"
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_get_report_detail_not_found(client, auth_headers):
    """GET /api/v1/moderator/reports/{report_id} returns 404 for non-existent report."""
    resp = await client.get("/api/v1/moderator/reports/99999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Report not found."
