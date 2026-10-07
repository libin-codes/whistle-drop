"""Tests for Status Workflow State Machine (Issue #3 / AC 7-9)."""

import pytest


@pytest.mark.asyncio
async def test_valid_transition_submitted_to_under_review(client, auth_headers):
    """SUBMITTED -> UNDER_REVIEW with status_update note readable by whistleblower."""
    # Whistleblower submits report
    create_resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Compromised API keys in repository"},
    )
    case_code = create_resp.json()["case_code"]

    # Moderator fetches report ID
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Transition to UNDER_REVIEW
    patch_resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={
            "status": "UNDER_REVIEW",
            "status_update": "Assigned to Security Operations Team.",
        },
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["status"] == "UNDER_REVIEW"
    assert patched_data["status_note"] == "Assigned to Security Operations Team."

    # Whistleblower tracks report and sees the update
    track_resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert track_resp.status_code == 200
    track_data = track_resp.json()
    assert track_data["status"] == "UNDER_REVIEW"
    assert track_data["status_note"] == "Assigned to Security Operations Team."
    assert track_data["status_update"] == "Assigned to Security Operations Team."


@pytest.mark.asyncio
async def test_valid_transition_submitted_to_dismissed(client, auth_headers):
    """SUBMITTED -> DISMISSED is allowed."""
    await client.post(
        "/api/v1/reports",
        json={"category": "OTHER", "description": "Spam submission"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    patch_resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "DISMISSED", "status_update": "Duplicate or invalid report."},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "DISMISSED"


@pytest.mark.asyncio
async def test_valid_transition_under_review_to_resolved(client, auth_headers):
    """SUBMITTED -> UNDER_REVIEW -> RESOLVED is allowed."""
    await client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Harassment claim"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # First advance to UNDER_REVIEW
    p1 = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    assert p1.status_code == 200

    # Advance to RESOLVED
    p2 = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "RESOLVED", "status_update": "Investigation complete. Remediation applied."},
        headers=auth_headers,
    )
    assert p2.status_code == 200
    assert p2.json()["status"] == "RESOLVED"
    assert p2.json()["status_note"] == "Investigation complete. Remediation applied."


@pytest.mark.asyncio
async def test_valid_transition_under_review_to_dismissed(client, auth_headers):
    """SUBMITTED -> UNDER_REVIEW -> DISMISSED is allowed."""
    await client.post(
        "/api/v1/reports",
        json={"category": "CORRUPTION", "description": "Unverified rumor"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    p2 = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "DISMISSED"},
        headers=auth_headers,
    )
    assert p2.status_code == 200
    assert p2.json()["status"] == "DISMISSED"


@pytest.mark.asyncio
async def test_illegal_transition_submitted_directly_to_resolved(client, auth_headers):
    """Illegal jump SUBMITTED -> RESOLVED returns HTTP 400 Bad Request."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Direct jump test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "RESOLVED"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Illegal status transition" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_illegal_backwards_transition_under_review_to_submitted(client, auth_headers):
    """Backwards transition UNDER_REVIEW -> SUBMITTED returns HTTP 400 Bad Request."""
    await client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Backwards transition test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Move forward to UNDER_REVIEW
    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )

    # Attempt backwards jump
    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "SUBMITTED"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Illegal status transition" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_illegal_transition_from_resolved_backwards(client, auth_headers):
    """Backwards transition RESOLVED -> UNDER_REVIEW returns HTTP 400."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Resolved backwards test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "RESOLVED"},
        headers=auth_headers,
    )

    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Illegal status transition" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_illegal_same_status_transition(client, auth_headers):
    """Same-status transition SUBMITTED -> SUBMITTED returns HTTP 400."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Same status test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "SUBMITTED"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Illegal status transition" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_status_enum_value(client, auth_headers):
    """Invalid status name returns HTTP 400."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Invalid enum test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "NON_EXISTENT_STATUS"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Invalid target status" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_patch_status_nonexistent_report(client, auth_headers):
    """PATCH status on non-existent report ID returns HTTP 404."""
    resp = await client.patch(
        "/api/v1/moderator/reports/99999/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Report not found."


@pytest.mark.asyncio
async def test_illegal_transition_to_permanently_closed_rejected(client, auth_headers):
    """Transitioning to PERMANENTLY_CLOSED via status patch is rejected with 400 (reserved for closure route)."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Closure boundary test"},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "RESOLVED"},
        headers=auth_headers,
    )

    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "PERMANENTLY_CLOSED"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Illegal status transition" in resp.json()["detail"]
