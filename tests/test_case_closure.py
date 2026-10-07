"""Tests for Permanent Case Closure & Data Minimization (Issue #4 / AC 4-7, 8)."""

import io
import pytest
from PIL import Image


def _make_image_bytes() -> bytes:
    img = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_permanent_case_closure_redacts_description(client, auth_headers):
    """POST .../close sets status to PERMANENTLY_CLOSED and overwrites description with Redaction Marker."""
    create_resp = await client.post(
        "/api/v1/reports",
        json={
            "category": "CORRUPTION",
            "description": "Sensitive investigation details regarding project budgets.",
        },
    )
    case_code = create_resp.json()["case_code"]

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Close case
    close_resp = await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )
    assert close_resp.status_code == 200
    closed_data = close_resp.json()
    assert closed_data["status"] == "PERMANENTLY_CLOSED"
    assert closed_data["description"] == "[REDACTED - CASE PERMANENTLY CLOSED]"

    # Moderator detail endpoint reflects redaction and closure
    detail_resp = await client.get(
        f"/api/v1/moderator/reports/{report_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "PERMANENTLY_CLOSED"
    assert detail_resp.json()["description"] == "[REDACTED - CASE PERMANENTLY CLOSED]"

    # Whistleblower tracking reflects closure
    track_resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert track_resp.status_code == 200
    assert track_resp.json()["status"] == "PERMANENTLY_CLOSED"


@pytest.mark.asyncio
async def test_permanent_case_closure_shreds_evidence(client, auth_headers, tmp_path):
    """Permanent closure deletes associated local evidence file from disk storage."""
    # Upload evidence
    upload_resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("evidence.png", _make_image_bytes(), "image/png")},
    )
    assert upload_resp.status_code == 201
    evidence_url = upload_resp.json()["url"]
    filename = evidence_url.split("/")[-1]
    saved_file = tmp_path / filename
    assert saved_file.exists()

    # Create report with evidence
    await client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Exfiltrated data snapshot.",
            "evidence_url": evidence_url,
        },
    )

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Invoke closure
    close_resp = await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )
    assert close_resp.status_code == 200

    # Evidence file must be shredded from disk
    assert not saved_file.exists()


@pytest.mark.asyncio
async def test_permanent_case_closure_unauthenticated(client):
    """Closing a report without moderator authentication returns 401."""
    resp = await client.post("/api/v1/moderator/reports/1/close")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_permanent_case_closure_nonexistent(client, auth_headers):
    """Closing nonexistent report returns 404."""
    resp = await client.post(
        "/api/v1/moderator/reports/99999/close",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_permanent_case_closure_rejects_subsequent_close(client, auth_headers):
    """Calling close on an already permanently closed report returns 400."""
    await client.post(
        "/api/v1/reports",
        json={"category": "OTHER", "description": "Double closure test."},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # First close succeeds
    r1 = await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )
    assert r1.status_code == 200

    # Second close rejected with 400
    r2 = await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_permanently_closed_report_rejects_status_updates(client, auth_headers):
    """Permanently closed reports reject any further status updates with HTTP 400."""
    await client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Immutability test."},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Close case
    await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )

    # Attempt to reopen or update status
    resp = await client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_permanently_closed_report_rejects_new_messages(client, auth_headers):
    """Permanently closed reports freeze the Dead Drop thread and reject new messages with HTTP 400."""
    create_resp = await client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Message thread freeze test."},
    )
    case_code = create_resp.json()["case_code"]

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Close case
    await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        headers=auth_headers,
    )

    # Moderator attempts message
    mod_msg = await client.post(
        f"/api/v1/moderator/reports/{report_id}/messages",
        json={"content": "Attempted question on closed case."},
        headers=auth_headers,
    )
    assert mod_msg.status_code == 400

    # Whistleblower attempts message
    rep_msg = await client.post(
        f"/api/v1/reports/track/{case_code}/messages",
        json={"content": "Attempted reply on closed case."},
    )
    assert rep_msg.status_code == 400


@pytest.mark.asyncio
async def test_permanent_case_closure_with_optional_note(client, auth_headers):
    """Permanent closure can accept an optional status_note or status_update."""
    await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Case closure note test."},
    )
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/moderator/reports/{report_id}/close",
        json={"status_note": "Case permanently archived after forensic review."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PERMANENTLY_CLOSED"
    assert resp.json()["status_note"] == "Case permanently archived after forensic review."
