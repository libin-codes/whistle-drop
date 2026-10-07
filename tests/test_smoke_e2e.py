"""End-to-end smoke tests verifying the full WhistleDrop lifecycle."""

import pytest


@pytest.mark.asyncio
class TestEndToEndSmoke:
    """Complete lifecycle smoke tests."""

    async def test_full_lifecycle(self, client, auth_headers):
        """Walk through the entire lifecycle:
        1. Submit a report
        2. Track it with the case code
        3. Moderator logs in and lists reports
        4. Moderator transitions status SUBMITTED → UNDER_REVIEW
        5. Moderator posts a Dead Drop message
        6. Whistleblower replies via Dead Drop
        7. Moderator transitions UNDER_REVIEW → RESOLVED
        8. Moderator permanently closes the case
        9. Verify closure immutability
        """
        # Step 1: Submit report
        resp = await client.post("/api/v1/reports", json={
            "category": "CORRUPTION",
            "description": "Observed unusual fund transfers in Q3 treasury reports."
        })
        assert resp.status_code == 201
        case_code = resp.json()["case_code"]
        assert case_code.startswith("WD-")

        # Step 2: Track report
        resp = await client.get(f"/api/v1/reports/track/{case_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUBMITTED"
        assert data["category"] == "CORRUPTION"

        # Step 3: Moderator lists reports
        resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
        assert resp.status_code == 200
        reports = resp.json()
        assert len(reports) >= 1
        report_id = reports[0]["id"]

        # Step 4: Transition to UNDER_REVIEW
        resp = await client.patch(
            f"/api/v1/moderator/reports/{report_id}/status",
            headers=auth_headers,
            json={"status": "UNDER_REVIEW", "status_update": "Assigned to primary investigator."}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "UNDER_REVIEW"

        # Step 5: Moderator Dead Drop message
        resp = await client.post(
            f"/api/v1/moderator/reports/{report_id}/messages",
            headers=auth_headers,
            json={"content": "Can you provide the specific account numbers involved?"}
        )
        assert resp.status_code == 201
        assert resp.json()["sender_role"] == "MODERATOR"

        # Step 6: Whistleblower replies
        resp = await client.post(
            f"/api/v1/reports/track/{case_code}/messages",
            json={"content": "Accounts 4401 and 4402 in the offshore ledger."}
        )
        assert resp.status_code == 201
        assert resp.json()["sender_role"] == "REPORTER"

        # Verify messages appear in tracking
        resp = await client.get(f"/api/v1/reports/track/{case_code}")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["sender_role"] == "MODERATOR"
        assert messages[1]["sender_role"] == "REPORTER"

        # Step 7: Transition to RESOLVED
        resp = await client.patch(
            f"/api/v1/moderator/reports/{report_id}/status",
            headers=auth_headers,
            json={"status": "RESOLVED", "status_update": "Investigation complete. Transfers flagged."}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"

        # Step 8: Permanently close
        resp = await client.post(
            f"/api/v1/moderator/reports/{report_id}/close",
            headers=auth_headers,
            json={"status_note": "Case archived after full resolution."}
        )
        assert resp.status_code == 200
        closed = resp.json()
        assert closed["status"] == "PERMANENTLY_CLOSED"
        assert "REDACTED" in closed["description"]

        # Step 9: Verify closure immutability
        resp = await client.patch(
            f"/api/v1/moderator/reports/{report_id}/status",
            headers=auth_headers,
            json={"status": "UNDER_REVIEW"}
        )
        assert resp.status_code == 400

        resp = await client.post(
            f"/api/v1/moderator/reports/{report_id}/messages",
            headers=auth_headers,
            json={"content": "This should fail."}
        )
        assert resp.status_code == 400

        resp = await client.post(
            f"/api/v1/reports/track/{case_code}/messages",
            json={"content": "This should also fail."}
        )
        assert resp.status_code == 400

    async def test_dashboard_served_at_root(self, client):
        """GET / should return the embedded HTML dashboard with 3 tabs and zero external dependencies."""
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        content = resp.text

        # Core branding & structure
        assert "WhistleDrop" in content
        assert "🛡️" in content

        # Zero external frontend dependencies check
        assert "<script src=\"http" not in content
        assert "<link rel=\"stylesheet\" href=\"http" not in content

        # Tab 1: Whistleblower Submit
        assert "Submit Report" in content
        assert "submit-category" in content
        assert "submit-desc" in content
        assert "submit-evidence" in content
        assert "copyCaseCode" in content

        # Tab 2: Whistleblower Track
        assert "Track Report" in content
        assert "track-code" in content
        assert "track-thread" in content
        assert "track-reply-form" in content

        # Tab 3: Moderator Portal
        assert "Moderator Portal" in content
        assert "mod-login-form" in content
        assert "mod-report-list" in content
        assert "mod-filter-status" in content
        assert "mod-filter-category" in content
        assert "triggerPermanentClosure" in content

        # Static assets
        assert "/static/css/styles.css" in content
        assert "/static/js/dashboard.js" in content
        assert "toast-container" in content

        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        assert "toast-container" in css_resp.text

        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        assert "showToast" in js_resp.text

    async def test_openapi_docs_available(self, client):
        """GET /docs serves interactive OpenAPI documentation."""
        resp = await client.get("/docs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    async def test_openapi_schema_complete(self, client):
        """The OpenAPI schema includes all expected endpoints."""
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = list(schema["paths"].keys())
        expected = [
            "/api/v1/reports",
            "/api/v1/reports/track/{case_code}",
            "/api/v1/reports/track/{case_code}/messages",
            "/api/v1/evidence/upload",
            "/api/v1/auth/login",
            "/api/v1/moderator/reports",
            "/api/v1/moderator/reports/{report_id}",
            "/api/v1/moderator/reports/{report_id}/status",
            "/api/v1/moderator/reports/{report_id}/messages",
            "/api/v1/moderator/reports/{report_id}/close",
        ]
        for ep in expected:
            assert ep in paths, f"Missing endpoint in OpenAPI schema: {ep}"

    async def test_evidence_upload_and_report_with_evidence(self, client, auth_headers, tmp_path):
        """Upload evidence, submit report with evidence URL, verify in moderator view."""
        # Create a minimal valid PNG
        import struct
        import zlib
        def make_png():
            # 1x1 red pixel PNG
            def chunk(chunk_type, data):
                c = chunk_type + data
                crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
                return struct.pack('>I', len(data)) + c + crc
            header = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            raw = b'\x00\xff\x00\x00'  # filter byte + RGB
            idat = chunk(b'IDAT', zlib.compress(raw))
            iend = chunk(b'IEND', b'')
            return header + ihdr + idat + iend

        png_data = make_png()

        # Upload evidence
        resp = await client.post(
            "/api/v1/evidence/upload",
            files={"file": ("evidence.png", png_data, "image/png")}
        )
        assert resp.status_code == 201
        evidence_url = resp.json()["url"]
        assert evidence_url.startswith("/uploads/")

        # Submit report with evidence
        resp = await client.post("/api/v1/reports", json={
            "category": "SECURITY",
            "description": "Leaked credentials in repo.",
            "evidence_url": evidence_url
        })
        assert resp.status_code == 201
        case_code = resp.json()["case_code"]

        # Moderator can see the evidence URL
        resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
        assert resp.status_code == 200
        reports = resp.json()
        matching = [r for r in reports if r["evidence_url"] == evidence_url]
        assert len(matching) == 1
