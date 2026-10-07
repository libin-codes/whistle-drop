"""Tests for Dead Drop Two-Way Messaging (Issue #4 / AC 1-3, 7-8)."""

import pytest


@pytest.mark.asyncio
async def test_moderator_post_message_success(client, auth_headers):
    """Authenticated moderator can post a message (sender_role: MODERATOR) to report thread."""
    # Create a report
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Suspicious login activity."},
    )
    assert resp.status_code == 201

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Post message as moderator
    msg_resp = await client.post(
        f"/api/v1/moderator/reports/{report_id}/messages",
        json={"content": "Can you specify the IP addresses observed?"},
        headers=auth_headers,
    )
    assert msg_resp.status_code == 201
    body = msg_resp.json()
    assert body["sender_role"] == "MODERATOR"
    assert body["content"] == "Can you specify the IP addresses observed?"
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_reporter_post_message_success(client):
    """Whistleblower can post an anonymous reply (sender_role: REPORTER) using Case Code."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "CORRUPTION", "description": "Misallocated department funds."},
    )
    case_code = resp.json()["case_code"]

    msg_resp = await client.post(
        f"/api/v1/reports/track/{case_code}/messages",
        json={"content": "Here is additional context regarding the invoices."},
    )
    assert msg_resp.status_code == 201
    body = msg_resp.json()
    assert body["sender_role"] == "REPORTER"
    assert body["content"] == "Here is additional context regarding the invoices."
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_bidirectional_dead_drop_conversation(client, auth_headers):
    """Chronological conversation history is visible to both whistleblower and moderator."""
    # 1. Submit report
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Leaked credentials on pastebin."},
    )
    case_code = resp.json()["case_code"]

    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # 2. Moderator posts an inquiry
    m1 = await client.post(
        f"/api/v1/moderator/reports/{report_id}/messages",
        json={"content": "Which repository was targeted?"},
        headers=auth_headers,
    )
    assert m1.status_code == 201

    # 3. Reporter replies anonymously
    r1 = await client.post(
        f"/api/v1/reports/track/{case_code}/messages",
        json={"content": "The backend payment gateway repo."},
    )
    assert r1.status_code == 201

    # 4. Moderator acknowledges
    m2 = await client.post(
        f"/api/v1/moderator/reports/{report_id}/messages",
        json={"content": "Understood, revoking tokens now."},
        headers=auth_headers,
    )
    assert m2.status_code == 201

    # 5. Whistleblower tracking verifies chronological order and sender roles
    track_resp = await client.get(f"/api/v1/reports/track/{case_code}")
    assert track_resp.status_code == 200
    track_body = track_resp.json()
    assert "messages" in track_body
    messages = track_body["messages"]
    assert len(messages) == 3
    assert messages[0]["sender_role"] == "MODERATOR"
    assert messages[0]["content"] == "Which repository was targeted?"
    assert messages[1]["sender_role"] == "REPORTER"
    assert messages[1]["content"] == "The backend payment gateway repo."
    assert messages[2]["sender_role"] == "MODERATOR"
    assert messages[2]["content"] == "Understood, revoking tokens now."

    # 6. Moderator report detail also returns the identical thread
    detail_resp = await client.get(
        f"/api/v1/moderator/reports/{report_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200
    detail_body = detail_resp.json()
    assert "messages" in detail_body
    assert len(detail_body["messages"]) == 3
    assert detail_body["messages"] == messages


@pytest.mark.asyncio
async def test_moderator_post_message_unauthenticated(client):
    """Posting message as moderator without authentication returns 401."""
    resp = await client.post(
        "/api/v1/moderator/reports/1/messages",
        json={"content": "Unauthorized note."},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_message_nonexistent_report(client, auth_headers):
    """Posting to nonexistent report returns 404 for both endpoints."""
    # Moderator route
    resp_mod = await client.post(
        "/api/v1/moderator/reports/99999/messages",
        json={"content": "Hello?"},
        headers=auth_headers,
    )
    assert resp_mod.status_code == 404

    # Reporter route
    resp_rep = await client.post(
        "/api/v1/reports/track/WD-NONEXISTENT/messages",
        json={"content": "Hello?"},
    )
    assert resp_rep.status_code == 404


@pytest.mark.asyncio
async def test_post_message_empty_content_validation(client, auth_headers):
    """Empty or whitespace-only message content returns 422."""
    resp = await client.post(
        "/api/v1/reports",
        json={"category": "OTHER", "description": "Test report."},
    )
    case_code = resp.json()["case_code"]
    list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]

    # Moderator empty message
    m_resp = await client.post(
        f"/api/v1/moderator/reports/{report_id}/messages",
        json={"content": "   "},
        headers=auth_headers,
    )
    assert m_resp.status_code == 422

    # Reporter empty message
    r_resp = await client.post(
        f"/api/v1/reports/track/{case_code}/messages",
        json={"content": ""},
    )
    assert r_resp.status_code == 422
