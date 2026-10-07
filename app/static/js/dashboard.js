// --- Monochromatic Lucide-Style SVG Icon Utility Foundation ---
const ICONS = {
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    check: '<polyline points="20 6 9 17 4 12"/>',
    fileText: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/>',
    send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    alertTriangle: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>',
    logIn: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" x2="3" y1="12" y2="12"/>',
    logOut: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
    refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    arrowLeft: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    externalLink: '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/>'
};

function getIcon(name, className = 'icon') {
    const path = ICONS[name] || '';
    return `<svg class="${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
}

// Attach globally for accessibility across components
window.getIcon = getIcon;
window.ICONS = ICONS;

// --- Toast Notification System (Shadcn Polished) ---
function showToast(title, body = '', type = 'success', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;

    let iconName = 'info';
    if (type === 'success') iconName = 'check';
    else if (type === 'error' || type === 'destructive') iconName = 'alertTriangle';
    else if (type === 'info') iconName = 'info';

    toast.innerHTML = `
        <div class="toast-icon">${getIcon(iconName, 'icon icon-md')}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${body ? `<div class="toast-body">${body}</div>` : ''}
        </div>
        <button class="toast-close" onclick="dismissToast(this.parentElement)" aria-label="Close notification">${getIcon('x', 'icon icon-sm')}</button>
    `;

    container.appendChild(toast);

    const timer = setTimeout(() => {
        dismissToast(toast);
    }, duration);

    toast._timer = timer;
}

function dismissToast(toast) {
    if (!toast || toast.classList.contains('toast-hiding')) return;
    if (toast._timer) clearTimeout(toast._timer);
    toast.classList.add('toast-hiding');
    setTimeout(() => {
        if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, 250);
}

function trackCaseFromSuccess() {
    const code = document.getElementById('success-case-code').textContent.trim();
    if (!code || code === 'WD-XXXX-XXXX') return;
    switchTab('track');
    const input = document.getElementById('track-code');
    if (input) {
        input.value = code;
        trackReport(new Event('submit'));
    }
}

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
        container.innerHTML = '<div style="color: var(--muted-foreground); text-align: center; padding: 24px; font-size: 0.875rem;">No messages in this Dead Drop thread yet.</div>';
        return;
    }

    messages.forEach(msg => {
        const div = document.createElement('div');
        const isMod = (msg.sender_role || '').toUpperCase() === 'MODERATOR';
        div.className = 'msg ' + (isMod ? 'msg-moderator' : 'msg-reporter');

        const meta = document.createElement('div');
        meta.className = 'msg-meta';
        const dateStr = msg.created_at ? new Date(msg.created_at).toLocaleString() : '';
        const roleIcon = isMod ? getIcon('shield', 'icon icon-xs') : getIcon('lock', 'icon icon-xs');
        const roleLabel = isMod ? 'Moderator' : 'Whistleblower';
        meta.innerHTML = `${roleIcon} <span>${roleLabel}</span>${dateStr ? ' • ' + dateStr : ''}`;

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
        showToast('Report Submitted Securely', 'Your report is registered. Save your Case Code below!', 'success', 6000);

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
    const code = document.getElementById('success-case-code').textContent.trim();
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('btn-copy-code');
        btn.innerHTML = `${getIcon('check', 'icon icon-sm')} Copied!`;
        showToast('Case Code Copied', 'Your confidential Case Code was copied to clipboard.', 'info', 3000);
        setTimeout(() => {
            btn.innerHTML = `${getIcon('copy', 'icon icon-sm')} Copy Case Code`;
        }, 2000);
    }).catch(() => {
        showToast('Case Code', code, 'info', 6000);
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
            list.innerHTML = '<li class="report-item text-center" style="color: var(--muted-foreground); padding: 24px;">No reports found matching criteria.</li>';
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
                        <span style="font-size: 0.75rem; color: var(--muted-foreground);">${dateStr}</span>
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
            const evLink = document.getElementById('mod-det-evidence');
            evLink.href = data.evidence_url;
            evLink.innerHTML = `${getIcon('search', 'icon icon-sm')} View Scrubbed Image`;
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
                    <button class="btn btn-outline" onclick="advanceStatus('DISMISSED')">Dismiss Report</button>
                `;
            } else if (data.status === 'UNDER_REVIEW') {
                actions.innerHTML = `
                    <button class="btn btn-primary" onclick="advanceStatus('RESOLVED')">Mark as Resolved</button>
                    <button class="btn btn-outline" onclick="advanceStatus('DISMISSED')">Dismiss Report</button>
                `;
            } else {
                actions.innerHTML = '<span style="color: var(--muted-foreground); font-size: 0.85rem;">No further forward workflow transitions available. Use Permanent Closure below to archive.</span>';
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
        setBtnLoading('btn-mod-close', false, 'Irreversibly Close Case');
    }
}
