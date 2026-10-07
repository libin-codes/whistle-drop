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

    async def test_shadcn_design_system_and_iconography(self, client):
        """Ticket 1 acceptance criteria: pure CSS Zinc tokens, button variants,
        toasts, dialog overlays, inline SVG icon helpers, and zero CDN links.
        """
        # 1. GET / verification
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text
        assert "<script src=\"http" not in html
        assert "<link rel=\"stylesheet\" href=\"http" not in html
        assert "🛡️" in html
        assert "WhistleDrop" in html

        # 2. CSS custom properties & components verification
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text

        # Dark Zinc palette tokens in :root
        required_tokens = [
            "--background",
            "--foreground",
            "--card",
            "--border",
            "--input",
            "--ring",
            "--primary",
            "--muted",
            "--destructive",
        ]
        for token in required_tokens:
            assert token in css, f"Missing token {token} in styles.css"

        # Reusable component styling for shadcn button variants
        assert "btn-outline" in css
        assert "btn-ghost" in css
        assert "btn-destructive" in css

        # Dialog overlay and modal container primitives
        assert "dialog-overlay" in css or "modal-overlay" in css
        assert "dialog-content" in css or "modal-card" in css

        # Toast styling
        assert "toast-container" in css
        assert ".toast" in css

        # Icon styling
        assert ".icon" in css or ".lucide" in css

        # 3. JavaScript SVG icon helpers verification
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text

        assert "getIcon" in js
        # Verify Lucide-style SVG icons are defined
        for icon_name in ["shield", "lock", "search", "copy", "fileText", "alertTriangle"]:
            assert icon_name in js, f"Missing icon {icon_name} in dashboard.js"

    async def test_moderator_auth_header_navigation_and_modal(self, client):
        """Ticket 2 acceptance criteria:
        - Moderator Portal removed from public tab bar; outline 'Moderator Login' button in header top-right
        - Accessible login dialog modal with backdrop blur, keyboard support (Escape to dismiss), and error feedback
        - Successful login persists JWT in state, closes modal, renders moderator badge & consistent Logout button
        - Authenticated view strictly enforces role separation (no whistleblower view for moderators)
        - Clicking Logout clears session, resets header to 'Moderator Login', and returns to public view
        - Zero external scripts or styles
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Zero external scripts or styles
        assert "<script src=\"http" not in html
        assert "<link rel=\"stylesheet\" href=\"http" not in html

        # 2. Moderator Login outline button in header
        assert "btn-open-mod-login" in html
        assert "Moderator Login" in html
        assert "openLoginModal" in html

        # 3. Public tab bar has Submit and Track, but NOT Moderator Portal in tabs
        tabs_start = html.find('class="tabs"')
        tabs_end = html.find('</div>', tabs_start)
        tabs_html = html[tabs_start:tabs_end]
        assert "Submit Report" in tabs_html
        assert "Track Report" in tabs_html
        assert "Moderator Portal" not in tabs_html

        # 4. Accessible dialog modal for moderator login
        assert 'id="mod-login-modal"' in html
        assert 'role="dialog"' in html
        assert 'aria-modal="true"' in html
        assert "mod-login-form" in html
        assert "mod-user" in html
        assert "mod-pass" in html
        assert "mod-login-error" in html
        assert "closeLoginModal" in html

        # 5. Authenticated header navigation elements (role separation & consistent button styling)
        assert "mod-badge" in html
        assert "btn-mod-logout" in html
        assert 'class="btn btn-outline" id="btn-open-mod-login"' in html
        assert 'class="btn btn-outline" id="btn-mod-logout"' in html
        assert "Triage Workspace" in html
        assert "workspace-toggle" not in html
        assert "Whistleblower View" not in html

        # 6. CSS styles verification
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "segmented-control" in css
        assert "segmented-btn" in css
        assert "backdrop-filter" in css

        # 7. JS functions verification
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "openLoginModal" in js
        assert "closeLoginModal" in js
        assert "switchWorkspace" in js
        assert "modLogin" in js
        assert "modLogout" in js
        assert "Escape" in js

    async def test_whistleblower_public_interface_submit_and_track(self, client):
        """Ticket 3 acceptance criteria:
        - Public tab navigation styled as a sleek two-segment control ("Submit Report" and "Track Report")
        - Anonymous submission form features polished inputs, category dropdown, and file upload zone highlighting in-memory EXIF scrubbing
        - Successful submission renders a high-visibility zero-knowledge Case Code card with one-click copy and direct "Track This Case Now" action
        - Tracking view presents current status badge, category chip, and public moderator update callout
        - Dead Drop message feed styled with clean message bubbles distinguishing moderator messages from reporter replies
        - Permanent closure notice clearly indicates frozen thread state when report status is PERMANENTLY_CLOSED
        - All automated tests continue to pass
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Zero external scripts or styles
        assert "<script src=\"http" not in html
        assert "<link rel=\"stylesheet\" href=\"http" not in html

        # 2. Public tab navigation styled as a sleek two-segment control
        tabs_start = html.find('id="public-tabs"')
        assert tabs_start != -1, "Missing public-tabs container"
        tabs_tag_end = html.find('>', tabs_start)
        tabs_tag = html[tabs_start:tabs_tag_end]
        assert "segmented-control" in tabs_tag or "tabs" in tabs_tag
        assert 'role="tablist"' in html

        # Two segment buttons: Submit and Track
        assert 'id="tab-btn-submit"' in html
        assert 'id="tab-btn-track"' in html
        assert 'role="tab"' in html
        assert 'aria-selected="true"' in html
        assert 'aria-selected="false"' in html
        assert "Submit Report" in html
        assert "Track Report" in html

        # 3. Anonymous submission form and scrubbed evidence dropzone
        assert 'id="submit-form"' in html
        assert 'id="submit-category"' in html
        assert 'id="submit-desc"' in html
        assert 'id="submit-evidence"' in html
        assert 'id="evidence-dropzone"' in html
        assert "In-Memory EXIF Scrubbing" in html
        assert 'id="btn-submit"' in html
        assert 'id="submit-error"' in html

        # 4. High-visibility zero-knowledge Case Code reveal card
        assert 'id="success-card"' in html
        assert 'id="success-case-code"' in html
        assert 'id="btn-copy-code"' in html
        assert "copyCaseCode" in html
        assert 'id="btn-track-submitted-case"' in html
        assert "trackCaseFromSuccess" in html
        assert "Zero-Knowledge" in html or "zero-knowledge" in html.lower()

        # 5. Tracking view components
        assert 'id="track-search-card"' in html
        assert 'id="track-form"' in html
        assert 'id="track-code"' in html
        assert 'id="btn-track"' in html
        assert 'id="track-result-card"' in html
        assert 'id="track-status"' in html
        assert 'id="track-category"' in html
        assert 'id="track-display-code"' in html
        assert 'id="track-stepper"' in html
        assert 'id="track-note-container"' in html
        assert 'id="track-note"' in html
        assert "Back" in html

        # 6. Dead Drop message thread components (compact sticky chat box, no badge)
        assert 'id="track-thread"' in html
        assert "thread-box" in html
        assert "thread-reply-bar" in html
        assert 'id="track-reply-form"' in html
        assert 'id="track-reply-text"' in html
        assert 'id="btn-track-reply"' in html
        assert 'id="track-reply-error"' in html
        assert "Confidential & Asynchronous" not in html

        # 7. Permanent closure frozen notice
        assert 'id="track-closed-notice"' in html
        assert "permanently closed" in html.lower()
        assert "frozen" in html.lower()

        # 8. CSS styling verification
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "thread-box" in css
        assert "thread-reply-bar" in css
        assert "public-tab-control" in css
        assert "dropzone" in css
        assert "dropzone-scrub-badge" in css or "dropzone-scrub-banner" in css or "dropzone-scrub-notice" in css
        assert "case-code-card" in css or "case-code-box" in css
        assert "msg-reporter" in css
        assert "msg-moderator" in css
        assert "frozen-thread-notice" in css or "warning-box" in css
        assert "moderator-update-callout" in css or "track-note-container" in css
        assert "workflow-stepper" in css

        # 9. JavaScript functions verification
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "handleFileSelection" in js
        assert "clearEvidenceFile" in js
        assert "updateWorkflowStepper" in js
        assert "trackCaseFromSuccess" in js
        assert "copyCaseCode" in js
        assert "submitReport" in js
        assert "trackReport" in js
        assert "renderThread" in js

    async def test_moderator_triage_workspace_master_detail(self, client):
        """Ticket 4 acceptance criteria:
        - Master-detail split layout renders with left queue list and right detail inspector
        - Queue header features status filter, category filter, and manual refresh button
        - Selecting a queue item displays full report metadata, category, status, and scrubbed evidence image link
        - Dynamic Status Workflow action buttons rendered based on current report lifecycle state
        - Public status update note submitted alongside state transition
        - Dead Drop thread displays bi-directional message history with message posting form
        - Irreversible Permanent Case Closure section enforces data minimization (informing user of redaction marker and evidence shredding) with confirmation
        - Thread is permanently frozen against new messages once closed
        - All automated tests continue to pass
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Zero external scripts or styles
        assert "<script src=\"http" not in html
        assert "<link rel=\"stylesheet\" href=\"http" not in html

        # 2. Master-detail split layout structure
        assert 'id="tab-mod"' in html
        assert 'id="mod-dashboard"' in html
        assert 'triage-workspace' in html
        assert 'id="mod-list-view"' in html
        assert 'triage-queue-pane' in html
        assert 'id="mod-detail-view"' in html
        assert 'triage-detail-pane' in html
        assert 'id="mod-detail-empty"' in html
        assert 'id="mod-detail-content"' in html

        # 3. Queue header controls: status filter, category filter, refresh button, queue counter
        assert 'id="mod-filter-status"' in html
        assert 'id="mod-filter-category"' in html
        assert 'id="btn-mod-refresh"' in html
        assert 'fetchModReports' in html
        assert 'id="mod-queue-count"' in html
        assert 'id="mod-report-list"' in html
        assert 'id="mod-list-error"' in html

        # 4. Detail inspector metadata, description, and scrubbed evidence preview link
        assert 'id="mod-detail-heading"' in html
        assert 'id="mod-det-id"' in html
        assert 'id="mod-det-created"' in html
        assert 'id="mod-det-status"' in html
        assert 'id="mod-det-cat"' in html
        assert 'id="mod-det-desc"' in html
        assert 'id="mod-det-evidence-container"' in html
        assert 'id="mod-det-evidence"' in html
        assert "View Scrubbed Image" in html
        assert 'id="btn-mod-close-detail"' in html
        assert "closeModDetail" in html

        # 5. Dynamic Status Workflow transition action bar & public update note
        assert 'id="mod-workflow-section"' in html
        assert 'id="mod-status-note"' in html
        assert 'id="mod-status-actions"' in html
        assert 'id="mod-status-error"' in html

        # 6. Dead Drop thread feed & message posting form
        assert 'id="mod-thread"' in html
        assert 'id="mod-reply-form"' in html
        assert 'id="mod-reply-text"' in html
        assert 'id="btn-mod-reply"' in html
        assert 'id="mod-reply-error"' in html
        assert 'id="mod-thread-frozen-notice"' in html

        # 7. Irreversible Permanent Case Closure section (ADR-0002)
        assert 'id="mod-close-section"' in html
        assert 'id="mod-close-reason"' in html
        assert 'id="btn-mod-close"' in html
        assert 'triggerPermanentClosure' in html
        assert 'id="mod-close-error"' in html
        assert "Permanent Case Closure" in html
        assert "Data Minimization" in html
        assert "ADR-0002" in html

        # 8. Accessible confirmation dialog modal for Permanent Closure (ADR-0002)
        assert 'id="mod-close-confirm-modal"' in html
        assert 'role="dialog"' in html
        assert 'aria-modal="true"' in html
        assert 'id="mod-close-modal-title"' in html
        assert 'id="btn-confirm-permanent-close"' in html
        assert 'executePermanentClosure' in html
        assert 'closeClosureModal' in html
        assert "Redaction Marker" in html
        assert "[REDACTED - CASE PERMANENTLY CLOSED]" in html
        assert "Evidence Shredding" in html

        # 9. CSS styles verification
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "triage-workspace" in css
        assert "triage-queue-pane" in css
        assert "triage-detail-pane" in css
        assert "triage-empty-detail" in css
        assert "triage-mode" in css
        assert "report-item" in css
        assert "report-has-evidence" in css
        assert "mod-close-section" in css
        assert "dialog-destructive-badge" in css
        assert "closure-consequences-list" in css

        # 10. JavaScript functions verification
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "fetchModReports" in js
        assert "viewModReport" in js
        assert "closeModDetail" in js
        assert "advanceStatus" in js
        assert "sendModReply" in js
        assert "triggerPermanentClosure" in js
        assert "openClosureModal" in js
        assert "closeClosureModal" in js
        assert "executePermanentClosure" in js
        assert "formatRelativeTime" in js
        assert "escapeHtml" in js



