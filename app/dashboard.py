"""Embedded single-page dashboard served at GET /."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ WhistleDrop — Confidential Reporting</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-color: #c9d1d9;
            --text-muted: #8b949e;
            --accent-green: #238636;
            --accent-green-hover: #2ea043;
            --accent-blue: #1f6feb;
            --accent-blue-hover: #388bfd;
            --danger-red: #da3633;
            --danger-red-hover: #f85149;
            --warning-amber: #d29922;

            --status-submitted: #1f6feb;
            --status-under-review: #d29922;
            --status-resolved: #238636;
            --status-dismissed: #6e7681;
            --status-permanently-closed: #da3633;

            --border-radius: 6px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            padding: 0;
            min-height: 100vh;
        }

        .container {
            max-width: 860px;
            margin: 0 auto;
            padding: var(--spacing-lg) var(--spacing-md);
        }

        .header {
            text-align: center;
            margin-bottom: var(--spacing-lg);
        }

        .header h1 {
            font-size: 2.2rem;
            margin-bottom: var(--spacing-sm);
            color: #f0f6fc;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .header p {
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: var(--spacing-lg);
            gap: 4px;
            overflow-x: auto;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: var(--spacing-md) var(--spacing-lg);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .tab-btn:hover { color: var(--text-color); }

        .tab-btn.active {
            color: #f0f6fc;
            border-bottom-color: var(--accent-green);
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Cards & Forms */
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }

        .card h2 {
            font-size: 1.3rem;
            margin-bottom: var(--spacing-md);
            color: #f0f6fc;
        }

        .card h3 {
            font-size: 1.1rem;
            margin-bottom: var(--spacing-sm);
            color: #f0f6fc;
        }

        .card h4 {
            font-size: 0.95rem;
            margin-bottom: var(--spacing-sm);
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-group { margin-bottom: var(--spacing-md); }

        label {
            display: block;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: var(--spacing-sm);
            color: #c9d1d9;
        }

        input[type="text"], input[type="password"], select, textarea {
            width: 100%;
            padding: 10px var(--spacing-md);
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            color: var(--text-color);
            font-family: inherit;
            font-size: 0.95rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        input[type="file"] {
            width: 100%;
            padding: var(--spacing-sm);
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #58a6ff;
            box-shadow: 0 0 0 3px rgba(56, 139, 253, 0.3);
        }

        textarea { resize: vertical; min-height: 110px; }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background-color: #21262d;
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 9px var(--spacing-md);
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }

        .btn:hover {
            background-color: #30363d;
            border-color: #8b949e;
        }

        .btn-primary {
            background-color: var(--accent-green);
            border-color: rgba(240, 246, 252, 0.1);
            color: #ffffff;
        }

        .btn-primary:hover {
            background-color: var(--accent-green-hover);
            border-color: rgba(240, 246, 252, 0.1);
        }

        .btn-blue {
            background-color: var(--accent-blue);
            border-color: rgba(240, 246, 252, 0.1);
            color: #ffffff;
        }

        .btn-blue:hover {
            background-color: var(--accent-blue-hover);
        }

        .btn-danger {
            background-color: #21262d;
            border-color: var(--danger-red);
            color: #f85149;
        }

        .btn-danger:hover {
            background-color: var(--danger-red);
            color: #ffffff;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Utilities */
        .hidden { display: none !important; }
        .text-center { text-align: center; }
        .mt-2 { margin-top: var(--spacing-sm); }
        .mt-4 { margin-top: var(--spacing-md); }
        .mb-4 { margin-bottom: var(--spacing-md); }

        .error-message {
            color: #f85149;
            margin-top: var(--spacing-sm);
            font-size: 0.85rem;
            padding: 8px;
            background: rgba(248, 81, 73, 0.1);
            border-radius: var(--border-radius);
            border: 1px solid rgba(248, 81, 73, 0.3);
        }

        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Case Code Display Box */
        .case-code-box {
            background-color: var(--bg-color);
            border: 1px dashed #58a6ff;
            padding: var(--spacing-lg);
            text-align: center;
            border-radius: var(--border-radius);
            margin: var(--spacing-md) 0;
        }

        .case-code {
            font-size: 2.2rem;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-weight: 700;
            letter-spacing: 3px;
            color: #58a6ff;
            margin: var(--spacing-md) 0;
            user-select: all;
        }

        .warning-box {
            background: rgba(210, 153, 34, 0.1);
            border: 1px solid rgba(210, 153, 34, 0.4);
            border-radius: var(--border-radius);
            padding: 12px;
            color: #e3b341;
            font-size: 0.85rem;
            margin-top: var(--spacing-md);
            line-height: 1.4;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .badge.SUBMITTED { background-color: var(--status-submitted); color: #fff; }
        .badge.UNDER_REVIEW { background-color: var(--status-under-review); color: #000; }
        .badge.RESOLVED { background-color: var(--status-resolved); color: #fff; }
        .badge.DISMISSED { background-color: var(--status-dismissed); color: #fff; }
        .badge.PERMANENTLY_CLOSED { background-color: var(--status-permanently-closed); color: #fff; }

        .cat-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            background: #21262d;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            font-weight: 600;
        }

        /* Dead Drop Thread */
        .thread-container {
            max-height: 380px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-md);
            background: var(--bg-color);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .msg {
            padding: 10px 14px;
            border-radius: 8px;
            max-width: 85%;
            word-wrap: break-word;
        }

        .msg-reporter {
            background-color: #1f2937;
            border: 1px solid #374151;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .msg-moderator {
            background-color: #1e3a5f;
            border: 1px solid #2b4c7e;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }

        .msg-meta {
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-bottom: 4px;
            font-weight: 600;
        }

        .msg-moderator .msg-meta { color: #79c0ff; }
        .msg-reporter .msg-meta { color: #a5d6ff; }

        /* Moderator Portal */
        .mod-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-md);
            flex-wrap: wrap;
            gap: 10px;
        }

        .filters {
            display: flex;
            gap: var(--spacing-sm);
            flex-wrap: wrap;
        }

        .filters select {
            width: auto;
            padding: 6px 12px;
            font-size: 0.85rem;
        }

        .report-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .report-item {
            padding: 14px var(--spacing-md);
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }

        .report-item:hover {
            border-color: #58a6ff;
            background: rgba(56, 139, 253, 0.05);
        }

        .report-item-title {
            font-weight: 600;
            color: #f0f6fc;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .report-item-desc {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 4px;
            max-width: 520px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .action-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: var(--spacing-sm);
        }

        .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            background: var(--bg-color);
            padding: var(--spacing-md);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            margin-bottom: var(--spacing-md);
        }

        @media (max-width: 600px) {
            .detail-grid { grid-template-columns: 1fr; }
            .tabs { flex-wrap: nowrap; }
            .header h1 { font-size: 1.8rem; }
            .case-code { font-size: 1.7rem; }
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>🛡️ WhistleDrop</h1>
        <p>Confidential, zero-knowledge anonymous reporting & secure dead drop communication.</p>
    </div>

    <div class="tabs">
        <button class="tab-btn active" id="tab-btn-submit" onclick="switchTab('submit')">🔒 Submit Report</button>
        <button class="tab-btn" id="tab-btn-track" onclick="switchTab('track')">🔍 Track Report</button>
        <button class="tab-btn" id="tab-btn-mod" onclick="switchTab('mod')">🛡️ Moderator Portal</button>
    </div>

    <!-- TAB 1: SUBMIT REPORT -->
    <div id="tab-submit" class="tab-content active">
        <div class="card" id="submit-card">
            <h2>Submit an Anonymous Report</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
                Your report is encrypted and protected by zero-knowledge case code hashing. No IP addresses or identifying device metadata are ever recorded.
            </p>
            <form id="submit-form" onsubmit="submitReport(event)">
                <div class="form-group">
                    <label for="submit-category">Issue Category</label>
                    <select id="submit-category" required>
                        <option value="SECURITY">Security — Vulnerability, credential leak, data breach</option>
                        <option value="HARASSMENT">Harassment — Workplace abuse, misconduct, discrimination</option>
                        <option value="CORRUPTION">Corruption — Bribery, embezzlement, fraud, kickbacks</option>
                        <option value="TECHNICAL">Technical — Safety defect, system sabotage, negligence</option>
                        <option value="OTHER">Other — General confidential concern</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="submit-desc">Report Description</label>
                    <textarea id="submit-desc" required placeholder="Provide all relevant details anonymously. Avoid including your own identifying details..."></textarea>
                </div>

                <div class="form-group">
                    <label for="submit-evidence">Image Evidence (Optional, max 5 MB)</label>
                    <input type="file" id="submit-evidence" accept="image/jpeg,image/png,image/webp">
                    <small style="color: var(--text-muted); font-size: 0.8rem; display: block; margin-top: 4px;">
                        All camera EXIF, GPS coordinates, and device timestamps are stripped in-memory before storage.
                    </small>
                </div>

                <button type="submit" class="btn btn-primary" id="btn-submit">
                    Submit Report Securely
                </button>
                <div id="submit-error" class="error-message hidden"></div>
            </form>
        </div>

        <div class="card hidden" id="success-card">
            <h2 style="color: var(--accent-green);">✓ Report Submitted Securely</h2>
            <p style="color: var(--text-color);">
                Your report has been received and assigned a cryptographically random, zero-knowledge Case Code:
            </p>

            <div class="case-code-box">
                <div style="color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Your Secret Case Code</div>
                <div class="case-code" id="success-case-code">WD-XXXX-XXXX</div>
                <button class="btn btn-blue" id="btn-copy-code" onclick="copyCaseCode()">📋 Copy Case Code</button>
            </div>

            <div class="warning-box">
                <strong>CRITICAL:</strong> Save this Case Code immediately. WhistleDrop stores only a one-way SHA-256 hash.
                This plaintext code is <strong>NEVER shown again and cannot be recovered</strong> by anyone, including system administrators.
            </div>

            <button class="btn mt-4" onclick="resetSubmit()">Submit Another Report</button>
        </div>
    </div>

    <!-- TAB 2: TRACK REPORT -->
    <div id="tab-track" class="tab-content">
        <div class="card" id="track-search-card">
            <h2>Track Anonymous Report</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
                Enter your Case Code to check investigation status and access the bidirectional Dead Drop communication thread.
            </p>
            <form id="track-form" onsubmit="trackReport(event)">
                <div class="form-group">
                    <label for="track-code">Case Code</label>
                    <input type="text" id="track-code" required placeholder="e.g. WD-ABCD-1234" autocomplete="off" spellcheck="false">
                </div>
                <button type="submit" class="btn btn-primary" id="btn-track">Track Case</button>
                <div id="track-error" class="error-message hidden"></div>
            </form>
        </div>

        <div class="card hidden" id="track-result-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
                <div>
                    <h2>Case Status: <span id="track-status" class="badge"></span></h2>
                    <span id="track-category" class="cat-badge mt-2"></span>
                </div>
                <button class="btn" onclick="resetTrack()">← Search Another Case</button>
            </div>

            <div id="track-note-container" class="hidden" style="margin-bottom: 16px; padding: 12px; background: rgba(35, 134, 54, 0.1); border-left: 3px solid var(--accent-green); border-radius: 4px;">
                <strong style="color: #3fb950; font-size: 0.85rem; text-transform: uppercase;">Moderator Status Update:</strong>
                <div id="track-note" style="margin-top: 6px; color: var(--text-color); font-size: 0.95rem;"></div>
            </div>

            <div style="margin-top: 20px;">
                <h4>Dead Drop Message Thread</h4>
                <div class="thread-container" id="track-thread">
                    <!-- Populated dynamically -->
                </div>

                <form id="track-reply-form" onsubmit="sendTrackReply(event)">
                    <div class="form-group">
                        <label for="track-reply-text">Post Confidential Reply</label>
                        <textarea id="track-reply-text" required placeholder="Send an anonymous message to the reviewing moderator..." style="min-height: 80px;"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary" id="btn-track-reply">Send Reply</button>
                    <div id="track-reply-error" class="error-message hidden"></div>
                </form>
                <div id="track-closed-notice" class="hidden warning-box" style="margin-top: 12px;">
                    This case is <strong>permanently closed</strong>. The Dead Drop thread has been permanently frozen against new replies (ADR-0002).
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 3: MODERATOR PORTAL -->
    <div id="tab-mod" class="tab-content">
        <!-- Login Card -->
        <div class="card" id="mod-login-card">
            <h2>Moderator Portal Login</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
                Authorized personnel only. Issues 24-hour HS256 JWT access token.
            </p>
            <form id="mod-login-form" onsubmit="modLogin(event)">
                <div class="form-group">
                    <label for="mod-user">Username</label>
                    <input type="text" id="mod-user" required autocomplete="username" value="moderator">
                </div>
                <div class="form-group">
                    <label for="mod-pass">Password</label>
                    <input type="password" id="mod-pass" required autocomplete="current-password" value="moderator123">
                </div>
                <button type="submit" class="btn btn-primary" id="btn-mod-login">Login to Portal</button>
                <div id="mod-login-error" class="error-message hidden"></div>
            </form>
        </div>

        <!-- Authenticated Dashboard -->
        <div id="mod-dashboard" class="hidden">
            <!-- List View -->
            <div class="card" id="mod-list-view">
                <div class="mod-header">
                    <div>
                        <h2>Triage Queue</h2>
                        <span id="mod-current-user" style="font-size: 0.85rem; color: var(--text-muted);"></span>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn" onclick="fetchModReports()">↻ Refresh</button>
                        <button class="btn btn-danger" onclick="modLogout()">Logout</button>
                    </div>
                </div>

                <div class="filters" style="margin-bottom: 16px;">
                    <select id="mod-filter-status" onchange="fetchModReports()">
                        <option value="">All Statuses</option>
                        <option value="SUBMITTED">Submitted</option>
                        <option value="UNDER_REVIEW">Under Review</option>
                        <option value="RESOLVED">Resolved</option>
                        <option value="DISMISSED">Dismissed</option>
                        <option value="PERMANENTLY_CLOSED">Permanently Closed</option>
                    </select>

                    <select id="mod-filter-category" onchange="fetchModReports()">
                        <option value="">All Categories</option>
                        <option value="SECURITY">Security</option>
                        <option value="HARASSMENT">Harassment</option>
                        <option value="CORRUPTION">Corruption</option>
                        <option value="TECHNICAL">Technical</option>
                        <option value="OTHER">Other</option>
                    </select>
                </div>

                <ul class="report-list" id="mod-report-list">
                    <!-- Populated dynamically -->
                </ul>
                <div id="mod-list-error" class="error-message hidden"></div>
            </div>

            <!-- Detail View -->
            <div class="card hidden" id="mod-detail-view">
                <div class="mod-header">
                    <div>
                        <h2 id="mod-detail-heading">Report Details</h2>
                        <span id="mod-det-cat" class="cat-badge"></span>
                        <span id="mod-det-status" class="badge"></span>
                    </div>
                    <button class="btn" onclick="closeModDetail()">← Back to Queue</button>
                </div>

                <div class="detail-grid">
                    <div>
                        <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Report ID</span>
                        <div id="mod-det-id" style="font-weight: 600;"></div>
                    </div>
                    <div>
                        <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Submitted At</span>
                        <div id="mod-det-created" style="font-size: 0.9rem;"></div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Description</label>
                    <div id="mod-det-desc" style="white-space: pre-wrap; background: var(--bg-color); padding: 12px; border-radius: var(--border-radius); border: 1px solid var(--border-color); font-size: 0.95rem;"></div>
                </div>

                <div id="mod-det-evidence-container" class="form-group hidden">
                    <label>Scrubbed Evidence File</label>
                    <a id="mod-det-evidence" href="#" target="_blank" class="btn" style="color: #58a6ff;">🔍 View Scrubbed Image</a>
                </div>

                <!-- Status Workflow Actions -->
                <div id="mod-workflow-section" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-color);">
                    <h4>Status Workflow Transition</h4>
                    <div class="form-group">
                        <label for="mod-status-note">Public Status Update Note (Visible to Whistleblower)</label>
                        <input type="text" id="mod-status-note" placeholder="e.g. Assigned to senior investigator.">
                    </div>
                    <div class="action-buttons" id="mod-status-actions">
                        <!-- Transition buttons dynamically rendered based on allowed state transitions -->
                    </div>
                    <div id="mod-status-error" class="error-message hidden"></div>
                </div>

                <!-- Dead Drop Section -->
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-color);">
                    <h4>Dead Drop Thread</h4>
                    <div class="thread-container" id="mod-thread">
                        <!-- Messages populated dynamically -->
                    </div>

                    <form id="mod-reply-form" onsubmit="sendModReply(event)">
                        <div class="form-group">
                            <label for="mod-reply-text">Post Moderator Message</label>
                            <textarea id="mod-reply-text" required placeholder="Send inquiry or guidance to the whistleblower..." style="min-height: 80px;"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" id="btn-mod-reply">Send Dead Drop Message</button>
                        <div id="mod-reply-error" class="error-message hidden"></div>
                    </form>
                    <div id="mod-thread-frozen-notice" class="hidden warning-box">
                        This report is permanently closed. Message posting is permanently disabled.
                    </div>
                </div>

                <!-- Permanent Closure Section (ADR-0002) -->
                <div id="mod-close-section" style="margin-top: 32px; padding: 16px; border: 1px solid rgba(218, 54, 51, 0.4); border-radius: var(--border-radius); background: rgba(218, 54, 51, 0.05);">
                    <h4 style="color: #f85149;">Permanent Case Closure & Data Minimization (ADR-0002)</h4>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px;">
                        Permanently close this report. This action is irreversible: it immediately overwrites the description with the standardized Redaction Marker, physically shreds all evidence files from disk, and freezes the Dead Drop thread against all future writes.
                    </p>
                    <div class="form-group">
                        <input type="text" id="mod-close-reason" placeholder="Optional closing resolution note...">
                    </div>
                    <button class="btn btn-danger" id="btn-mod-close" onclick="triggerPermanentClosure()">⚠️ Irreversibly Close Case</button>
                    <div id="mod-close-error" class="error-message hidden"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // --- Application State ---
    let modToken = null;
    let currentTrackCode = null;
    let currentModReportId = null;
    let currentModReport = null;

    // --- Tab Navigation ---
    function switchTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        const targetBtn = document.getElementById('tab-btn-' + tabId);
        if (targetBtn) targetBtn.classList.add('active');

        const targetTab = document.getElementById('tab-' + tabId);
        if (targetTab) targetTab.classList.add('active');

        if (tabId === 'mod' && modToken) {
            fetchModReports();
        }
    }

    // --- Helper Functions ---
    function showError(elementId, message) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = message;
            el.classList.remove('hidden');
        }
    }

    function clearError(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = '';
            el.classList.add('hidden');
        }
    }

    function setBtnLoading(btnId, isLoading, originalText) {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        btn.disabled = isLoading;
        if (isLoading) {
            btn.innerHTML = '<span class="spinner"></span> Processing...';
        } else {
            btn.innerHTML = originalText;
        }
    }

    function renderThread(containerId, messages) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';

        if (!messages || messages.length === 0) {
            container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px; font-size: 0.9rem;">No messages in this Dead Drop thread yet.</div>';
            return;
        }

        messages.forEach(msg => {
            const div = document.createElement('div');
            const isMod = (msg.sender_role || '').toUpperCase() === 'MODERATOR';
            div.className = 'msg ' + (isMod ? 'msg-moderator' : 'msg-reporter');

            const meta = document.createElement('div');
            meta.className = 'msg-meta';
            const dateStr = msg.created_at ? new Date(msg.created_at).toLocaleString() : '';
            meta.textContent = (isMod ? '🛡️ Moderator' : '🔒 Whistleblower') + (dateStr ? ' • ' + dateStr : '');

            const content = document.createElement('div');
            content.style.whiteSpace = 'pre-wrap';
            content.textContent = msg.content || msg.message || '';

            div.appendChild(meta);
            div.appendChild(content);
            container.appendChild(div);
        });

        container.scrollTop = container.scrollHeight;
    }

    // --- Tab 1: Submit Logic ---
    async function submitReport(e) {
        e.preventDefault();
        clearError('submit-error');
        setBtnLoading('btn-submit', true, 'Submit Report Securely');

        const category = document.getElementById('submit-category').value;
        const description = document.getElementById('submit-desc').value.trim();
        const fileInput = document.getElementById('submit-evidence');

        if (!description) {
            showError('submit-error', 'Description cannot be blank.');
            setBtnLoading('btn-submit', false, 'Submit Report Securely');
            return;
        }

        try {
            let evidenceUrl = null;

            // 1. Upload evidence if attached
            if (fileInput.files && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                if (file.size > 5 * 1024 * 1024) {
                    throw new Error('File exceeds maximum size of 5 MB.');
                }
                const formData = new FormData();
                formData.append('file', file);

                const upRes = await fetch('/api/v1/evidence/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!upRes.ok) {
                    const upErr = await upRes.json().catch(() => ({}));
                    throw new Error(upErr.detail || 'Evidence upload failed.');
                }
                const upData = await upRes.json();
                evidenceUrl = upData.url;
            }

            // 2. Submit report
            const payload = { category, description };
            if (evidenceUrl) payload.evidence_url = evidenceUrl;

            const repRes = await fetch('/api/v1/reports', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!repRes.ok) {
                const repErr = await repRes.json().catch(() => ({}));
                throw new Error(repErr.detail || 'Report submission failed.');
            }

            const repData = await repRes.json();

            // Display success
            document.getElementById('submit-card').classList.add('hidden');
            document.getElementById('success-card').classList.remove('hidden');
            document.getElementById('success-case-code').textContent = repData.case_code;

        } catch (err) {
            showError('submit-error', err.message || 'An unexpected error occurred.');
        } finally {
            setBtnLoading('btn-submit', false, 'Submit Report Securely');
        }
    }

    function resetSubmit() {
        document.getElementById('submit-form').reset();
        clearError('submit-error');
        document.getElementById('submit-card').classList.remove('hidden');
        document.getElementById('success-card').classList.add('hidden');
    }

    function copyCaseCode() {
        const code = document.getElementById('success-case-code').textContent;
        navigator.clipboard.writeText(code).then(() => {
            const btn = document.getElementById('btn-copy-code');
            btn.textContent = '✓ Copied!';
            setTimeout(() => { btn.textContent = '📋 Copy Case Code'; }, 2000);
        }).catch(() => {
            alert('Case Code: ' + code);
        });
    }

    // --- Tab 2: Track Logic ---
    async function trackReport(e) {
        if (e) e.preventDefault();
        const codeInput = document.getElementById('track-code');
        const code = codeInput.value.trim();
        if (!code) return;

        clearError('track-error');
        setBtnLoading('btn-track', true, 'Track Case');

        try {
            const res = await fetch('/api/v1/reports/track/' + encodeURIComponent(code));
            if (res.status === 404) {
                throw new Error('Report not found. Please verify your Case Code.');
            }
            if (res.status === 429) {
                throw new Error('Too many requests. Please wait a moment before trying again.');
            }
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to track report.');
            }

            const data = await res.json();
            currentTrackCode = code;

            // Render status & metadata
            const statusBadge = document.getElementById('track-status');
            statusBadge.className = 'badge ' + data.status;
            statusBadge.textContent = data.status.replace(/_/g, ' ');

            const catBadge = document.getElementById('track-category');
            catBadge.textContent = 'Category: ' + data.category;

            // Render note
            const noteContainer = document.getElementById('track-note-container');
            const noteText = data.status_update || data.status_note;
            if (noteText) {
                document.getElementById('track-note').textContent = noteText;
                noteContainer.classList.remove('hidden');
            } else {
                noteContainer.classList.add('hidden');
            }

            // Render Dead Drop Thread
            renderThread('track-thread', data.messages);

            // Handle closed status
            const replyForm = document.getElementById('track-reply-form');
            const closedNotice = document.getElementById('track-closed-notice');
            if (data.status === 'PERMANENTLY_CLOSED') {
                replyForm.classList.add('hidden');
                closedNotice.classList.remove('hidden');
            } else {
                replyForm.classList.remove('hidden');
                closedNotice.classList.add('hidden');
            }

            document.getElementById('track-search-card').classList.add('hidden');
            document.getElementById('track-result-card').classList.remove('hidden');

        } catch (err) {
            showError('track-error', err.message);
        } finally {
            setBtnLoading('btn-track', false, 'Track Case');
        }
    }

    function resetTrack() {
        currentTrackCode = null;
        document.getElementById('track-code').value = '';
        clearError('track-error');
        clearError('track-reply-error');
        document.getElementById('track-search-card').classList.remove('hidden');
        document.getElementById('track-result-card').classList.add('hidden');
    }

    async function sendTrackReply(e) {
        e.preventDefault();
        if (!currentTrackCode) return;

        const textInput = document.getElementById('track-reply-text');
        const content = textInput.value.trim();
        if (!content) return;

        clearError('track-reply-error');
        setBtnLoading('btn-track-reply', true, 'Send Reply');

        try {
            const res = await fetch('/api/v1/reports/track/' + encodeURIComponent(currentTrackCode) + '/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to post message.');
            }

            textInput.value = '';
            // Refresh tracking view
            await trackReport(null);

        } catch (err) {
            showError('track-reply-error', err.message);
        } finally {
            setBtnLoading('btn-track-reply', false, 'Send Reply');
        }
    }

    // --- Tab 3: Moderator Portal Logic ---
    async function modLogin(e) {
        e.preventDefault();
        const username = document.getElementById('mod-user').value.trim();
        const password = document.getElementById('mod-pass').value;

        clearError('mod-login-error');
        setBtnLoading('btn-mod-login', true, 'Login to Portal');

        try {
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (res.status === 401) {
                throw new Error('Invalid moderator username or password.');
            }
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Authentication failed.');
            }

            const data = await res.json();
            modToken = data.access_token;

            document.getElementById('mod-current-user').textContent = 'Logged in as: ' + username;
            document.getElementById('mod-login-card').classList.add('hidden');
            document.getElementById('mod-dashboard').classList.remove('hidden');

            fetchModReports();

        } catch (err) {
            showError('mod-login-error', err.message);
        } finally {
            setBtnLoading('btn-mod-login', false, 'Login to Portal');
        }
    }

    function modLogout() {
        modToken = null;
        currentModReportId = null;
        currentModReport = null;
        document.getElementById('mod-dashboard').classList.add('hidden');
        document.getElementById('mod-detail-view').classList.add('hidden');
        document.getElementById('mod-list-view').classList.remove('hidden');
        document.getElementById('mod-login-card').classList.remove('hidden');
        clearError('mod-login-error');
    }

    async function fetchModReports() {
        if (!modToken) return;
        clearError('mod-list-error');

        const status = document.getElementById('mod-filter-status').value;
        const category = document.getElementById('mod-filter-category').value;

        let url = '/api/v1/moderator/reports?limit=100';
        if (status) url += '&status=' + encodeURIComponent(status);
        if (category) url += '&category=' + encodeURIComponent(category);

        try {
            const res = await fetch(url, {
                headers: { 'Authorization': 'Bearer ' + modToken }
            });

            if (res.status === 401) return modLogout();
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to fetch reports.');
            }

            const reports = await res.json();
            const list = document.getElementById('mod-report-list');
            list.innerHTML = '';

            if (reports.length === 0) {
                list.innerHTML = '<li class="report-item text-center" style="color: var(--text-muted); padding: 24px;">No reports found matching criteria.</li>';
                return;
            }

            reports.forEach(r => {
                const li = document.createElement('li');
                li.className = 'report-item';
                li.onclick = () => viewModReport(r.id);

                const dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString() : '';

                li.innerHTML = `
                    <div>
                        <div class="report-item-title">
                            <span>Report #${r.id}</span>
                            <span class="cat-badge">${r.category}</span>
                            <span style="font-size: 0.75rem; color: var(--text-muted);">${dateStr}</span>
                        </div>
                        <div class="report-item-desc">${r.description}</div>
                    </div>
                    <div>
                        <span class="badge ${r.status}">${r.status.replace(/_/g, ' ')}</span>
                    </div>
                `;
                list.appendChild(li);
            });

        } catch (err) {
            showError('mod-list-error', err.message);
        }
    }

    async function viewModReport(reportId) {
        if (!modToken) return;
        clearError('mod-status-error');
        clearError('mod-reply-error');
        clearError('mod-close-error');

        try {
            const res = await fetch('/api/v1/moderator/reports/' + reportId, {
                headers: { 'Authorization': 'Bearer ' + modToken }
            });

            if (res.status === 401) return modLogout();
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to load report.');
            }

            const data = await res.json();
            currentModReportId = reportId;
            currentModReport = data;

            // Populate Details
            document.getElementById('mod-detail-heading').textContent = 'Report #' + data.id;
            document.getElementById('mod-det-id').textContent = '#' + data.id;
            document.getElementById('mod-det-created').textContent = data.created_at ? new Date(data.created_at).toLocaleString() : 'N/A';
            document.getElementById('mod-det-cat').textContent = data.category;

            const badge = document.getElementById('mod-det-status');
            badge.className = 'badge ' + data.status;
            badge.textContent = data.status.replace(/_/g, ' ');

            document.getElementById('mod-det-desc').textContent = data.description;

            // Evidence link
            const evContainer = document.getElementById('mod-det-evidence-container');
            if (data.evidence_url) {
                evContainer.classList.remove('hidden');
                document.getElementById('mod-det-evidence').href = data.evidence_url;
            } else {
                evContainer.classList.add('hidden');
            }

            // Status Workflow Transition Buttons
            const workflowSection = document.getElementById('mod-workflow-section');
            const closeSection = document.getElementById('mod-close-section');
            const replyForm = document.getElementById('mod-reply-form');
            const frozenNotice = document.getElementById('mod-thread-frozen-notice');
            const actions = document.getElementById('mod-status-actions');
            actions.innerHTML = '';

            if (data.status === 'PERMANENTLY_CLOSED') {
                workflowSection.classList.add('hidden');
                closeSection.classList.add('hidden');
                replyForm.classList.add('hidden');
                frozenNotice.classList.remove('hidden');
            } else {
                workflowSection.classList.remove('hidden');
                closeSection.classList.remove('hidden');
                replyForm.classList.remove('hidden');
                frozenNotice.classList.add('hidden');

                // Render forward transitions based on state machine
                if (data.status === 'SUBMITTED') {
                    actions.innerHTML = `
                        <button class="btn btn-blue" onclick="advanceStatus('UNDER_REVIEW')">Move to Under Review</button>
                        <button class="btn" onclick="advanceStatus('DISMISSED')">Dismiss Report</button>
                    `;
                } else if (data.status === 'UNDER_REVIEW') {
                    actions.innerHTML = `
                        <button class="btn btn-primary" onclick="advanceStatus('RESOLVED')">Mark as Resolved</button>
                        <button class="btn" onclick="advanceStatus('DISMISSED')">Dismiss Report</button>
                    `;
                } else {
                    actions.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">No further forward workflow transitions available. Use Permanent Closure below to archive.</span>';
                }
            }

            // Render Thread
            renderThread('mod-thread', data.messages);

            // Switch views
            document.getElementById('mod-list-view').classList.add('hidden');
            document.getElementById('mod-detail-view').classList.remove('hidden');

        } catch (err) {
            alert('Error loading report: ' + err.message);
        }
    }

    function closeModDetail() {
        currentModReportId = null;
        currentModReport = null;
        document.getElementById('mod-detail-view').classList.add('hidden');
        document.getElementById('mod-list-view').classList.remove('hidden');
        fetchModReports();
    }

    async function advanceStatus(targetStatus) {
        if (!modToken || !currentModReportId) return;
        clearError('mod-status-error');

        const noteInput = document.getElementById('mod-status-note');
        const statusUpdate = noteInput.value.trim();

        const payload = { status: targetStatus };
        if (statusUpdate) payload.status_update = statusUpdate;

        try {
            const res = await fetch('/api/v1/moderator/reports/' + currentModReportId + '/status', {
                method: 'PATCH',
                headers: {
                    'Authorization': 'Bearer ' + modToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (res.status === 401) return modLogout();
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Status transition failed.');
            }

            noteInput.value = '';
            await viewModReport(currentModReportId);

        } catch (err) {
            showError('mod-status-error', err.message);
        }
    }

    async function sendModReply(e) {
        e.preventDefault();
        if (!modToken || !currentModReportId) return;

        const textInput = document.getElementById('mod-reply-text');
        const content = textInput.value.trim();
        if (!content) return;

        clearError('mod-reply-error');
        setBtnLoading('btn-mod-reply', true, 'Send Dead Drop Message');

        try {
            const res = await fetch('/api/v1/moderator/reports/' + currentModReportId + '/messages', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + modToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });

            if (res.status === 401) return modLogout();
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to send message.');
            }

            textInput.value = '';
            await viewModReport(currentModReportId);

        } catch (err) {
            showError('mod-reply-error', err.message);
        } finally {
            setBtnLoading('btn-mod-reply', false, 'Send Dead Drop Message');
        }
    }

    async function triggerPermanentClosure() {
        if (!modToken || !currentModReportId) return;
        clearError('mod-close-error');

        const confirmed = confirm(
            '⚠️ PERMANENT CLOSURE WARNING (ADR-0002):\n\n' +
            'This action is IRREVERSIBLE.\n\n' +
            '1. The report description will be overwritten with [REDACTED - CASE PERMANENTLY CLOSED].\n' +
            '2. Any attached evidence files will be permanently shredded from disk.\n' +
            '3. The Dead Drop thread will be permanently frozen against further messages.\n\n' +
            'Are you sure you want to proceed?'
        );

        if (!confirmed) return;

        const reason = document.getElementById('mod-close-reason').value.trim();
        const payload = reason ? { status_note: reason } : {};

        setBtnLoading('btn-mod-close', true, 'Closing...');

        try {
            const res = await fetch('/api/v1/moderator/reports/' + currentModReportId + '/close', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + modToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (res.status === 401) return modLogout();
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Permanent closure failed.');
            }

            document.getElementById('mod-close-reason').value = '';
            await viewModReport(currentModReportId);

        } catch (err) {
            showError('mod-close-error', err.message);
        } finally {
            setBtnLoading('btn-mod-close', false, '⚠️ Irreversibly Close Case');
        }
    }
</script>
</body>
</html>
"""
