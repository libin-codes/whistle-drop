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

        # 5. Authenticated header navigation elements (streamlined outline logout button, badge omitted)
        assert "mod-badge" not in html
        assert "mod-identity-badge" not in html
        assert "Moderator: moderator" not in html
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
        assert 'id="btn-submit"' in html
        assert 'id="submit-error"' in html

        # 4. High-visibility zero-knowledge Case Code reveal modal dialog
        assert 'id="submit-success-modal"' in html
        assert 'id="success-case-code"' in html
        assert 'id="btn-copy-code"' in html
        assert "copyCaseCode" in html
        assert 'id="btn-close-success-modal"' in html
        assert "closeSuccessModal" in html
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
        assert "Status Workflow Transition" in html
        assert "Forward-only deterministic lifecycle" not in html
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

    async def test_streamline_authenticated_header_and_remove_workflow_subtitle(self, client):
        """Issue #20 acceptance criteria:
        - The 'Moderator: moderator' identity badge is completely removed from the authenticated top navigation bar.
        - The top navigation bar displays a styled outline Logout button when authenticated.
        - Client-side JavaScript correctly initializes and manages authenticated sessions without referencing the removed badge elements.
        - The 'Forward-only deterministic lifecycle' subtitle is removed from the Status Workflow section header.
        - The Status Workflow section header cleanly displays 'Status Workflow Transition' without subtitles.
        - Automated end-to-end tests verify that the badge and subtitle are not present in rendered responses and that authentication and logout still function properly.
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Moderator badge is completely absent from HTML
        assert "mod-badge" not in html
        assert "mod-identity-badge" not in html
        assert "Moderator: moderator" not in html

        # 2. Top nav contains outline logout button
        assert 'id="btn-mod-logout"' in html
        assert 'class="btn btn-outline" id="btn-mod-logout"' in html
        assert 'id="auth-header-actions"' in html

        # 3. Status Workflow header cleanly displays 'Status Workflow Transition' without subtitle
        assert "Status Workflow Transition" in html
        assert "Forward-only deterministic lifecycle" not in html

        # 4. JavaScript does not reference removed badge elements
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "mod-badge-username" not in js
        assert "mod-badge" not in js
        assert "mod-identity-badge" not in js
        assert "modLogin" in js
        assert "modLogout" in js

        # 5. Moderator login and authentication session functionality
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "moderator", "password": "moderator123"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 6. Status workflow transitions remain fully functional
        create_resp = await client.post(
            "/api/v1/reports",
            json={"category": "SECURITY", "description": "Security report for workflow test"},
        )
        assert create_resp.status_code == 201
        case_code = create_resp.json()["case_code"]

        mod_reports_resp = await client.get("/api/v1/moderator/reports", headers=headers)
        assert mod_reports_resp.status_code == 200
        reports = mod_reports_resp.json()
        assert len(reports) >= 1
        report_id = reports[0]["id"]

        # Moderator advances status to UNDER_REVIEW
        patch_resp = await client.patch(
            f"/api/v1/moderator/reports/{report_id}/status",
            headers=headers,
            json={"status": "UNDER_REVIEW", "status_update": "Reviewing security issue"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "UNDER_REVIEW"
        assert patch_resp.json()["status_update"] == "Reviewing security issue"

        # Whistleblower tracking verifies the transition
        track_resp = await client.get(f"/api/v1/reports/track/{case_code}")
        assert track_resp.status_code == 200
        assert track_resp.json()["status"] == "UNDER_REVIEW"
        assert track_resp.json()["status_update"] == "Reviewing security issue"

    async def test_full_width_triage_reports_table_and_search(self, client, auth_headers):
        """Issue #21 acceptance criteria:
        - The narrow side-panel queue list is replaced by a full-width responsive table of reports.
        - Table columns display Report ID, Category, Description Preview, Evidence indicator, Status, Submitted Timestamp, and Actions.
        - A real-time client-side search input field allows instant filtering of reports by ID or description keywords.
        - Existing Status and Category filter dropdowns and the manual Refresh button continue to filter the table data seamlessly.
        - The queue count badge updates dynamically to reflect the number of reports matching active filters.
        - A clean empty state row appears when no reports match the active filters or search criteria.
        - Automated end-to-end tests verify the table markup, column structure, search input element, and filtering functionality.
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Full-width responsive table markup and column headers
        assert 'id="mod-report-table"' in html
        assert 'reports-table' in html
        assert 'triage-table-wrap' in html
        assert '<th scope="col" class="th-id">Report ID (#)</th>' in html
        assert '<th scope="col" class="th-category">Category</th>' in html
        assert '<th scope="col" class="th-desc">Description Preview</th>' in html
        assert '<th scope="col" class="th-evidence">Evidence Indicator</th>' in html
        assert '<th scope="col" class="th-status">Status</th>' in html
        assert '<th scope="col" class="th-time">Submitted Timestamp</th>' in html
        assert '<th scope="col" class="th-actions"' in html
        assert '<th scope="col" class="th-actions">Actions</th>' not in html
        assert 'id="mod-report-list"' in html

        # 2. Real-time client-side search input field and toolbar
        assert 'id="mod-search-input"' in html
        assert 'triage-search-input' in html
        assert 'oninput="filterModReports()"' in html
        assert 'Search by ID or description...' in html

        # 3. Existing status & category dropdown filters and manual refresh button
        assert 'id="mod-filter-status"' in html
        assert 'id="mod-filter-category"' in html
        assert 'id="btn-mod-refresh"' in html
        assert 'id="mod-queue-count"' in html

        # 4. CSS delivery: table styling, clean description preview truncation, empty state, and responsive wrap
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "reports-table" in css
        assert "triage-table-wrap" in css
        assert "report-desc-preview" in css
        assert "row-chevron" in css or "col-chevron" in css
        assert "triage-table-empty" in css
        assert "triage-search-input" in css

        # 5. Client JavaScript delivery: table rendering, real-time client search, and dynamic counter
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "filterModReports" in js
        assert "renderModReportsTable" in js
        assert "fetchModReports" in js
        assert "viewModReport" in js
        assert "mod-search-input" in js
        assert "row-chevron" in js or "chevronRight" in js
        assert "triage-table-empty" in js

        # 6. Verify backend API integration with query filters for moderator reports
        # Create reports across multiple categories
        r1 = await client.post("/api/v1/reports", json={
            "category": "SECURITY",
            "description": "Vulnerability in auth token validator"
        })
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/reports", json={
            "category": "CORRUPTION",
            "description": "Kickbacks discovered in procurement department"
        })
        assert r2.status_code == 201

        # Query all reports
        list_resp = await client.get("/api/v1/moderator/reports", headers=auth_headers)
        assert list_resp.status_code == 200
        reports = list_resp.json()
        assert len(reports) >= 2

        # Query by category
        sec_resp = await client.get("/api/v1/moderator/reports?category=SECURITY", headers=auth_headers)
        assert sec_resp.status_code == 200
        sec_reports = sec_resp.json()
        assert all(r["category"] == "SECURITY" for r in sec_reports)

    async def test_drill_down_report_details_and_full_lifecycle(self, client, auth_headers, tmp_path):
        """Issue #22 acceptance criteria:
        - Clicking a report row or "View" button in the table switches the view to a dedicated full-width Report Details view.
        - A prominent "← Back to Reports" button in the details view header returns the interface to the reports table view.
        - The full-width details view displays complete report metadata, full description box, and scrubbed evidence preview link when present.
        - Status Workflow transition buttons render based on current lifecycle state and successfully submit forward transitions with public notes.
        - The Dead Drop message thread displays history and allows posting new messages when open.
        - Permanent Case Closure (ADR-0002) executes via an accessible confirmation modal dialog, shreds evidence, and freezes the Dead Drop thread.
        - After closure, the details view displays the frozen thread state, and the moderator can navigate back to the reports table using the back button.
        - Automated end-to-end smoke tests verify the view transition, back button functionality, inspector details, and full lifecycle execution.
        """
        # 1. HTML Markup & Layout Verification for Report Details Drill-Down View
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # Full-width details view and header Back action (ticket #29 removed secondary top nav bar)
        assert 'id="mod-detail-view"' in html
        assert 'triage-detail-pane' in html
        assert 'id="mod-detail-content"' in html
        assert 'mod-detail-nav-bar' not in html
        assert '← Back to Reports' not in html
        assert 'id="btn-mod-close-detail"' in html
        assert 'onclick="closeModDetail()"' in html
        assert 'Back' in html

        # Report Metadata & Description
        assert 'id="mod-detail-heading"' in html
        assert 'id="mod-det-id"' in html
        assert 'id="mod-det-created"' in html
        assert 'id="mod-det-status"' in html
        assert 'id="mod-det-cat"' in html
        assert 'id="mod-det-desc"' in html
        assert 'mod-description-box' in html

        # Scrubbed Evidence Preview
        assert 'id="mod-det-evidence-container"' in html
        assert 'id="mod-det-evidence"' in html
        assert 'btn-evidence-preview' in html
        assert 'View Scrubbed Image' in html

        # Status Workflow Action Bar & Note
        assert 'id="mod-workflow-section"' in html
        assert 'Status Workflow Transition' in html
        assert 'id="mod-status-note"' in html
        assert 'id="mod-status-actions"' in html

        # Dead Drop Message Thread
        assert 'id="mod-thread"' in html
        assert 'id="mod-reply-form"' in html
        assert 'id="mod-reply-text"' in html
        assert 'id="btn-mod-reply"' in html
        assert 'id="mod-thread-frozen-notice"' in html

        # Permanent Case Closure (ADR-0002) & Confirmation Modal
        assert 'id="mod-close-section"' in html
        assert 'id="mod-close-reason"' in html
        assert 'id="btn-mod-close"' in html
        assert 'id="mod-close-confirm-modal"' in html
        assert 'id="btn-confirm-permanent-close"' in html

        # 2. CSS Stylesheet Delivery: Drill-down layout and prominent back button
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "triage-detail-pane" in css
        assert "btn-mod-back" in css
        assert "mod-description-box" in css
        assert "btn-evidence-preview" in css
        assert "frozen-thread-notice" in css
        assert "mod-close-section" in css

        # 3. Client JavaScript Delivery & Syntax Validation
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "viewModReport" in js
        assert "closeModDetail" in js
        assert "advanceStatus" in js
        assert "sendModReply" in js
        assert "executePermanentClosure" in js
        assert "mod-detail-view" in js
        assert "btn-mod-back" in js

        import shutil
        import subprocess

        if shutil.which("node"):
            syntax_check = subprocess.run(
                ["node", "--check", "app/static/js/dashboard.js"],
                capture_output=True,
                text=True,
            )
            assert syntax_check.returncode == 0, f"JS syntax error: {syntax_check.stderr}"

        # Browser favicon request check (prevents 404 console errors)
        fav_resp = await client.get("/favicon.ico")
        assert fav_resp.status_code in (200, 204)

        # 4. Full Lifecycle Execution via APIs
        # Step A: Submit report with scrubbed evidence
        import io
        from PIL import Image

        img = Image.new("RGB", (30, 30), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

        up_resp = await client.post(
            "/api/v1/evidence/upload",
            files={"file": ("leak.jpg", img_bytes, "image/jpeg")},
        )
        assert up_resp.status_code == 201
        evidence_url = up_resp.json()["url"]

        rep_resp = await client.post("/api/v1/reports", json={
            "category": "SECURITY",
            "description": "Critical vulnerability uncovered in backend token signing algorithm.",
            "evidence_url": evidence_url,
        })
        assert rep_resp.status_code == 201
        rep_data = rep_resp.json()
        case_code = rep_data["case_code"]

        # Step B: Moderator inspects report in details drill-down view
        mod_list = await client.get("/api/v1/moderator/reports", headers=auth_headers)
        assert mod_list.status_code == 200
        target = next(r for r in mod_list.json() if r["category"] == "SECURITY" and "token signing" in r["description"])
        report_id = target["id"]

        detail_resp = await client.get(f"/api/v1/moderator/reports/{report_id}", headers=auth_headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["status"] == "SUBMITTED"
        assert detail["category"] == "SECURITY"
        assert "Critical vulnerability" in detail["description"]
        assert detail["evidence_url"] == evidence_url

        # Step C: Status Workflow forward transition with public note
        patch_resp = await client.patch(
            f"/api/v1/moderator/reports/{report_id}/status",
            headers=auth_headers,
            json={
                "status": "UNDER_REVIEW",
                "status_update": "Escalated to core cryptography engineering team for urgent review.",
            },
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "UNDER_REVIEW"

        # Verify whistleblower tracking reflects new status and public update note
        track_resp = await client.get(f"/api/v1/reports/track/{case_code}")
        assert track_resp.status_code == 200
        assert track_resp.json()["status"] == "UNDER_REVIEW"
        assert track_resp.json()["status_update"] == "Escalated to core cryptography engineering team for urgent review."

        # Step D: Bi-directional Dead Drop messaging
        # Moderator sends inquiry
        mod_msg_resp = await client.post(
            f"/api/v1/moderator/reports/{report_id}/messages",
            headers=auth_headers,
            json={"content": "Can you provide the specific commit hash where this was introduced?"},
        )
        assert mod_msg_resp.status_code == 201
        assert mod_msg_resp.json()["sender_role"] == "MODERATOR"

        # Whistleblower replies via Case Code
        rep_msg_resp = await client.post(
            f"/api/v1/reports/track/{case_code}/messages",
            json={"content": "It was introduced in commit 8f9b2a1."},
        )
        assert rep_msg_resp.status_code == 201
        assert rep_msg_resp.json()["sender_role"] == "REPORTER"

        # Moderator inspects thread history
        detail_after_msgs = await client.get(f"/api/v1/moderator/reports/{report_id}", headers=auth_headers)
        assert detail_after_msgs.status_code == 200
        msgs = detail_after_msgs.json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["content"] == "Can you provide the specific commit hash where this was introduced?"
        assert msgs[0]["sender_role"] == "MODERATOR"
        assert msgs[1]["content"] == "It was introduced in commit 8f9b2a1."
        assert msgs[1]["sender_role"] == "REPORTER"

        # Step E: Permanent Case Closure (ADR-0002) with closing resolution note
        close_resp = await client.post(
            f"/api/v1/moderator/reports/{report_id}/close",
            headers=auth_headers,
            json={"status_note": "Cryptographic flaw patched and verified; report permanently closed."},
        )
        assert close_resp.status_code == 200
        closed_data = close_resp.json()
        assert closed_data["status"] == "PERMANENTLY_CLOSED"
        # Verify Redaction Marker
        assert closed_data["description"] == "[REDACTED - CASE PERMANENTLY CLOSED]"
        # Verify evidence unlinked
        assert closed_data["evidence_url"] is None

        # Verify evidence file physically shredded from disk
        saved_filename = evidence_url.split("/")[-1]
        saved_file_path = tmp_path / saved_filename
        assert not saved_file_path.exists()

        # Step F: Verify Dead Drop thread is frozen against all future writes
        mod_fail_msg = await client.post(
            f"/api/v1/moderator/reports/{report_id}/messages",
            headers=auth_headers,
            json={"content": "Trying to message on closed report."},
        )
        assert mod_fail_msg.status_code == 400
        assert "closed" in mod_fail_msg.json()["detail"].lower()

        rep_fail_msg = await client.post(
            f"/api/v1/reports/track/{case_code}/messages",
            json={"content": "Whistleblower trying to reply on closed report."},
        )
        assert rep_fail_msg.status_code == 400
        assert "closed" in rep_fail_msg.json()["detail"].lower()

        # Step G: Whistleblower tracking verifies frozen closed state
        final_track = await client.get(f"/api/v1/reports/track/{case_code}")
        assert final_track.status_code == 200
        assert final_track.json()["status"] == "PERMANENTLY_CLOSED"
        assert final_track.json()["status_update"] == "Cryptographic flaw patched and verified; report permanently closed."

        # Step H: Moderator details drill-down verification of closed state (ADR-0002)
        final_mod_detail = await client.get(f"/api/v1/moderator/reports/{report_id}", headers=auth_headers)
        assert final_mod_detail.status_code == 200
        assert final_mod_detail.json()["status"] == "PERMANENTLY_CLOSED"
        assert final_mod_detail.json()["description"] == "[REDACTED - CASE PERMANENTLY CLOSED]"
        assert final_mod_detail.json()["evidence_url"] is None

    async def test_ticket_28_public_experience_persona_submit_and_whatsapp_dead_drop(self, client):
        """Ticket 28 acceptance criteria verification:
        1. Header shows 'Whistleblower' persona badge to the left of 'Moderator Login' in public mode.
        2. Header transitions to show 'Moderator' badge to the left of 'Logout' when authenticated.
        3. Static 'Logged in as: moderator' is removed from the triage header.
        4. Submit report button is positioned in the top-right header row of the submit card.
        5. Bottom submit action row is removed.
        6. CSS defines WhatsApp-style date chips and bottom-right message timestamp layout.
        7. JS implements centered date separators and 12-hour timestamps without seconds.
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Persona badge in unauthenticated header to the left of Moderator Login button
        assert "persona-badge" in html or "badge-role" in html or "role-badge" in html
        assert "Whistleblower" in html
        assert "Moderator" in html

        # 2. Static 'Logged in as:' removed from triage queue header
        assert "Logged in as:" not in html

        # 3. Submit report button in the card header row
        card_header_start = html.find('id="submit-card"')
        assert card_header_start != -1
        submit_card_html = html[card_header_start:html.find('<!-- TAB 2:', card_header_start)]
        card_header_row_start = submit_card_html.find('class="card-header-row"')
        assert card_header_row_start != -1
        card_header_row_end = submit_card_html.find('</form>', card_header_row_start)
        card_header_row_snippet = submit_card_html[card_header_row_start:card_header_row_end]
        assert "btn-submit" in card_header_row_snippet or 'form="submit-form"' in card_header_row_snippet
        assert "submit-actions-row" not in submit_card_html

        # 4. CSS tokens for WhatsApp-style date separator and message timestamps
        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "msg-date-separator" in css or "thread-date-separator" in css
        assert "msg-date-chip" in css or "thread-date-chip" in css
        assert "msg-time" in css or "msg-timestamp" in css

        # 5. JS implementation of WhatsApp-style messages and 12-hour time format
        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "msg-date-separator" in js or "thread-date-separator" in js
        assert "msg-time" in js or "msg-timestamp" in js

    async def test_ticket_29_moderator_triage_filters_chevron_and_split_inspector(self, client, auth_headers):
        """Ticket 29 acceptance criteria verification:
        1. Queue filter toolbar renders as a single row containing a fixed-width search field on the left
           and status/category filters aligned on the right.
        2. Total results count badge appears directly to the left of the Refresh button in the triage queue header.
        3. Reports queue table displays a subtle trailing column header, and each report row displays a right chevron
           icon in the trailing cell instead of a "View" button.
        4. Clicking any row (or pressing Enter/Space) opens the report inspector.
        5. Secondary top "← Back to Reports" navigation bar in the inspector is removed.
        6. Inspector header action button is labeled "Back" with a back arrow icon, and clicking it closes the inspector
           and returns to the queue.
        7. Report ID, Submitted At, Report Description, and Scrubbed Evidence File link are rendered inside a single
           consolidated overview container.
        8. Status Workflow Transition panel and Dead Drop Message Thread panel are arranged side-by-side in a two-column
           row with a vertical divider on desktop screens.
        9. Side-by-side layout collapses cleanly to stacked columns on smaller viewports.
        10. Permanent Case Closure section spans full-width directly below the two-column split row.
        11. All automated end-to-end smoke and lifecycle tests continue to pass.
        """
        resp = await client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Total results count badge directly to the left of the Refresh button in triage queue header
        pane_header_start = html.find('class="triage-pane-header"')
        assert pane_header_start != -1
        pane_header_end = html.find('id="mod-filters"', pane_header_start)
        header_snippet = html[pane_header_start:pane_header_end]
        assert 'id="mod-queue-count"' in header_snippet
        assert 'id="btn-mod-refresh"' in header_snippet
        assert header_snippet.find('id="mod-queue-count"') < header_snippet.find('id="btn-mod-refresh"')
        # Ensure count badge is removed from the title row beside heading
        title_row_start = header_snippet.find('class="triage-title-row"')
        assert title_row_start != -1
        title_row_end = header_snippet.find('</div>', title_row_start)
        assert 'id="mod-queue-count"' not in header_snippet[title_row_start:title_row_end]

        # 2. Queue filter toolbar markup & fixed-width styling
        assert 'id="mod-filters"' in html
        assert 'class="triage-filters"' in html
        assert 'id="mod-search-input"' in html
        assert 'id="mod-filter-status"' in html
        assert 'id="mod-filter-category"' in html

        css_resp = await client.get("/static/css/styles.css")
        assert css_resp.status_code == 200
        css = css_resp.text
        assert "triage-filters" in css
        assert "triage-search-wrap" in css
        assert "triage-filter-selects" in css
        assert "btn-ghost" in css
        assert "detail-item-desc" in css

        # 3. Queue table subtle trailing column header and chevron icon
        assert '<th scope="col" class="th-actions"' in html
        assert '<th scope="col" class="th-actions">Actions</th>' not in html

        js_resp = await client.get("/static/js/dashboard.js")
        assert js_resp.status_code == 200
        js = js_resp.text
        assert "chevronRight" in js
        assert "row-chevron" in js or "col-chevron" in js
        assert "btn-view-report" not in js

        # 4. Row click & keydown handlers
        assert "viewModReport(r.id)" in js
        assert "Enter" in js and "viewModReport" in js

        # 5. Secondary top "← Back to Reports" bar removed
        assert "mod-detail-nav-bar" not in html
        assert "← Back to Reports" not in html

        # 6. Inspector header Back button on left as ghost button, status badge on right
        assert 'id="btn-mod-close-detail"' in html
        close_btn_id_idx = html.find('id="btn-mod-close-detail"')
        close_btn_start = html.rfind('<button', 0, close_btn_id_idx)
        close_btn_end = html.find('</button>', close_btn_id_idx)
        close_btn_snippet = html[close_btn_start:close_btn_end]
        assert "Back" in close_btn_snippet
        assert "btn-ghost" in close_btn_snippet
        assert "Close Inspector" not in close_btn_snippet
        assert "m12 19-7-7 7-7" in close_btn_snippet or "arrowLeft" in close_btn_snippet

        # Back button is placed on the left before report details heading
        heading_idx = html.find('id="mod-detail-heading"')
        assert close_btn_start < heading_idx, "Back button should be positioned on the left before the heading"

        # Status badge is positioned in mod-detail-header-actions on the right
        header_actions_start = html.find('class="mod-detail-header-actions"')
        assert header_actions_start != -1
        header_actions_end = html.find('</div>', header_actions_start)
        actions_snippet = html[header_actions_start:header_actions_end]
        assert 'id="mod-det-status"' in actions_snippet
        assert 'id="btn-mod-close-detail"' not in actions_snippet
        assert 'id="mod-det-cat"' not in actions_snippet

        # 7. Single consolidated overview container with Report Description inside detail-grid occupying flex: 1
        assert 'id="mod-overview-card"' in html or 'class="inspector-overview-card"' in html
        card_start = html.find('id="mod-overview-card"')
        if card_start == -1:
            card_start = html.find('class="inspector-overview-card"')
        assert card_start != -1
        # Overview card must encompass ID, Category badge, Created, Description, and Evidence
        card_end = html.find('id="mod-split-row"', card_start)
        overview_snippet = html[card_start:card_end]
        assert 'detail-grid' in overview_snippet
        assert 'id="mod-det-id"' in overview_snippet
        assert 'id="mod-det-cat"' in overview_snippet
        assert 'id="mod-det-created"' in overview_snippet
        assert 'id="mod-det-desc"' in overview_snippet
        assert 'id="mod-det-evidence-container"' in overview_snippet

        # Report Description is inside the detail container occupying flex: 1
        grid_start = overview_snippet.find('class="detail-grid"')
        grid_end = overview_snippet.find('id="mod-det-evidence-container"', grid_start)
        grid_snippet = overview_snippet[grid_start:grid_end]
        assert 'id="mod-det-desc"' in grid_snippet
        assert 'flex: 1' in grid_snippet

        # 8 & 9. Responsive two-column split row with divider and responsive collapse
        assert 'id="mod-split-row"' in html or 'class="inspector-split-row"' in html
        assert 'class="inspector-split-divider"' in html or 'inspector-split-divider' in html
        split_row_start = html.find('id="mod-split-row"')
        if split_row_start == -1:
            split_row_start = html.find('class="inspector-split-row"')
        closure_start = html.find('id="mod-close-section"')
        assert split_row_start < closure_start, "Split row must precede permanent closure section"
        split_row_snippet = html[split_row_start:closure_start]
        assert 'id="mod-workflow-section"' in split_row_snippet
        assert 'id="mod-thread"' in split_row_snippet
        assert 'inspector-split-divider' in split_row_snippet

        # CSS verification for split row, divider, and responsive collapse
        assert "inspector-split-row" in css
        assert "inspector-split-col" in css
        assert "inspector-split-divider" in css

        # 10. Permanent Case Closure full-width directly below the two-column split row
        assert 'id="mod-close-section"' in html
        assert "mod-close-section" in css

        # 11. End-to-end API lifecycle validation
        # Create a report and verify moderator access
        create_res = await client.post("/api/v1/reports", json={
            "category": "SECURITY",
            "description": "Inspector split layout triage test report"
        })
        assert create_res.status_code == 201
        report_data = create_res.json()
        case_code = report_data["case_code"]

        mod_res = await client.get("/api/v1/moderator/reports", headers=auth_headers)
        assert mod_res.status_code == 200
        reports = mod_res.json()
        matched = [r for r in reports if r["description"] == "Inspector split layout triage test report"]
        assert len(matched) == 1
        rep_id = matched[0]["id"]

        detail_res = await client.get(f"/api/v1/moderator/reports/{rep_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == rep_id
        assert detail["status"] == "SUBMITTED"








