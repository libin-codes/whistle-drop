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
let currentWorkspace = 'whistleblower'; // 'whistleblower' | 'triage'
let previouslyFocusedElement = null;

// --- Modal Dialog Management ---
function openLoginModal() {
    clearError('mod-login-error');
    previouslyFocusedElement = document.activeElement;
    const modal = document.getElementById('mod-login-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            const userInput = document.getElementById('mod-user');
            if (userInput) {
                userInput.focus();
                userInput.select();
            }
        }, 50);
    }
}

function closeLoginModal() {
    const modal = document.getElementById('mod-login-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    clearError('mod-login-error');
    if (previouslyFocusedElement && typeof previouslyFocusedElement.focus === 'function') {
        previouslyFocusedElement.focus();
    }
}

function handleModalOverlayClick(e) {
    if (e.target && e.target.id === 'mod-login-modal') {
        closeLoginModal();
    }
}

// --- Permanent Case Closure Modal Management (ADR-0002) ---
function openClosureModal() {
    if (!modToken || !currentModReportId) return;
    clearError('mod-close-error');
    clearError('mod-modal-close-error');
    const modal = document.getElementById('mod-close-confirm-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeClosureModal() {
    const modal = document.getElementById('mod-close-confirm-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    clearError('mod-close-error');
    clearError('mod-modal-close-error');
}

function handleClosureModalOverlayClick(e) {
    if (e.target && e.target.id === 'mod-close-confirm-modal') {
        closeClosureModal();
    }
}

// Global Escape key listener for accessible modal dismissal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const loginModal = document.getElementById('mod-login-modal');
        if (loginModal && !loginModal.classList.contains('hidden')) {
            closeLoginModal();
        }
        const closureModal = document.getElementById('mod-close-confirm-modal');
        if (closureModal && !closureModal.classList.contains('hidden')) {
            closeClosureModal();
        }
    }
});

// --- Relative Time & String Escaping Utility Helpers ---
function formatRelativeTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    if (diffMs < 0) return 'just now';
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSec < 45) return 'just now';
    if (diffSec < 90) return '1 min ago';
    if (diffMin < 60) return diffMin + ' mins ago';
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return diffHours + ' hours ago';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 30) return diffDays + ' days ago';
    return date.toLocaleDateString();
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// --- Workspace Navigation & View Switching ---
function switchWorkspace(view) {
    currentWorkspace = view;
    const publicTabs = document.getElementById('public-tabs');
    const tabMod = document.getElementById('tab-mod');
    const modDashboard = document.getElementById('mod-dashboard');
    const container = document.querySelector('.container');

    if (view === 'triage') {
        if (container) container.classList.add('triage-mode');

        // Hide public tabs & public views
        if (publicTabs) publicTabs.style.display = 'none';
        document.querySelectorAll('.tab-content').forEach(c => {
            if (c.id !== 'tab-mod') c.classList.remove('active');
        });

        // Show moderator workspace
        if (tabMod) tabMod.classList.add('active');
        if (modDashboard) modDashboard.classList.remove('hidden');

        // Ensure detail inspector displays empty state if no report is selected
        if (!currentModReportId) {
            const emptyEl = document.getElementById('mod-detail-empty');
            const contentEl = document.getElementById('mod-detail-content');
            if (emptyEl) emptyEl.classList.remove('hidden');
            if (contentEl) contentEl.classList.add('hidden');
        }

        if (modToken) {
            fetchModReports();
        }
    } else {
        // Whistleblower view
        if (container) container.classList.remove('triage-mode');

        // Hide moderator workspace
        if (tabMod) tabMod.classList.remove('active');

        // Show public tabs & ensure an active public tab
        if (publicTabs) publicTabs.style.display = '';
        const activePublic = document.querySelector('.tab-content.active:not(#tab-mod)');
        if (!activePublic) {
            switchTab('submit');
        }
    }
}

// --- Tab Navigation (Public Tabs) ---
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-content').forEach(c => {
        if (c.id !== 'tab-mod') c.classList.remove('active');
    });

    const targetBtn = document.getElementById('tab-btn-' + tabId);
    if (targetBtn) {
        targetBtn.classList.add('active');
        targetBtn.setAttribute('aria-selected', 'true');
    }

    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) targetTab.classList.add('active');

    if (tabId === 'mod') {
        if (modToken) {
            switchWorkspace('triage');
        } else {
            openLoginModal();
        }
    }
}

// --- In-Memory Scrubbed Evidence Dropzone Helpers ---
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function handleFileSelection() {
    const fileInput = document.getElementById('submit-evidence');
    const promptEl = document.getElementById('dropzone-prompt');
    const selectedEl = document.getElementById('dropzone-file-selected');
    const nameEl = document.getElementById('dropzone-filename');
    const sizeEl = document.getElementById('dropzone-filesize');

    if (!fileInput) return;

    if (fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (file.size > 5 * 1024 * 1024) {
            showError('submit-error', 'Evidence file exceeds maximum size of 5 MB.');
            showToast('File Too Large', 'Evidence file must be 5 MB or smaller.', 'error');
            clearEvidenceFile();
            return;
        }
        clearError('submit-error');
        if (nameEl) nameEl.textContent = file.name;
        if (sizeEl) sizeEl.textContent = formatFileSize(file.size);
        if (promptEl) promptEl.classList.add('hidden');
        if (selectedEl) selectedEl.classList.remove('hidden');
    } else {
        if (promptEl) promptEl.classList.remove('hidden');
        if (selectedEl) selectedEl.classList.add('hidden');
    }
}

function clearEvidenceFile(e) {
    if (e) {
        e.stopPropagation();
        e.preventDefault();
    }
    const fileInput = document.getElementById('submit-evidence');
    if (fileInput) fileInput.value = '';
    const promptEl = document.getElementById('dropzone-prompt');
    const selectedEl = document.getElementById('dropzone-file-selected');
    if (promptEl) promptEl.classList.remove('hidden');
    if (selectedEl) selectedEl.classList.add('hidden');
}

function initDropzone() {
    const dropzone = document.getElementById('evidence-dropzone');
    const fileInput = document.getElementById('submit-evidence');
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', (e) => {
        if (e.target.closest('#dropzone-remove-btn')) return;
        fileInput.click();
    });

    dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            if (e.target.closest('#dropzone-remove-btn')) return;
            e.preventDefault();
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', handleFileSelection);

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'dragend'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dropzone-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dropzone-active');
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            fileInput.files = dt.files;
            handleFileSelection();
        }
    }, false);
}

// --- Status Workflow Stepper Helper ---
function updateWorkflowStepper(status) {
    const steps = ['step-submitted', 'step-under-review', 'step-resolved', 'step-closed'];
    steps.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active', 'completed', 'dismissed');
    });

    const stepSub = document.getElementById('step-submitted');
    const stepRev = document.getElementById('step-under-review');
    const stepRes = document.getElementById('step-resolved');
    const stepClo = document.getElementById('step-closed');

    if (!stepSub) return;

    if (status === 'SUBMITTED') {
        stepSub.classList.add('active');
    } else if (status === 'UNDER_REVIEW') {
        stepSub.classList.add('completed');
        if (stepRev) stepRev.classList.add('active');
    } else if (status === 'RESOLVED') {
        stepSub.classList.add('completed');
        if (stepRev) stepRev.classList.add('completed');
        if (stepRes) {
            stepRes.classList.add('active');
            const label = stepRes.querySelector('.step-label');
            if (label) label.textContent = 'Resolved';
        }
    } else if (status === 'DISMISSED') {
        stepSub.classList.add('completed');
        if (stepRev) stepRev.classList.add('completed');
        if (stepRes) {
            stepRes.classList.add('active', 'dismissed');
            const label = stepRes.querySelector('.step-label');
            if (label) label.textContent = 'Dismissed';
        }
    } else if (status === 'PERMANENTLY_CLOSED') {
        stepSub.classList.add('completed');
        if (stepRev) stepRev.classList.add('completed');
        if (stepRes) stepRes.classList.add('completed');
        if (stepClo) stepClo.classList.add('active');
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
        container.innerHTML = `
            <div class="thread-empty-state">
                ${getIcon('lock', 'icon icon-lg')}
                <p>No messages in this Dead Drop thread yet.</p>
                <span>The reviewing moderator will post inquiries here if additional details are needed.</span>
            </div>
        `;
        return;
    }

    messages.forEach(msg => {
        const div = document.createElement('div');
        const isMod = (msg.sender_role || '').toUpperCase() === 'MODERATOR';
        div.className = 'msg ' + (isMod ? 'msg-moderator' : 'msg-reporter');

        const meta = document.createElement('div');
        meta.className = 'msg-meta';
        const dateStr = msg.created_at ? new Date(msg.created_at).toLocaleString() : '';
        const roleIcon = isMod ? getIcon('shield', 'icon icon-xs') : getIcon('user', 'icon icon-xs');
        const roleLabel = isMod ? 'Moderator' : 'Whistleblower (You)';
        meta.innerHTML = `${roleIcon} <span class="msg-author">${roleLabel}</span>${dateStr ? ' • <span class="msg-date">' + dateStr + '</span>' : ''}`;

        const content = document.createElement('div');
        content.className = 'msg-content';
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

        // Clear dropzone file selection
        clearEvidenceFile();

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
    clearEvidenceFile();
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

        // Render tracked code display
        const codeDisplay = document.getElementById('track-display-code');
        if (codeDisplay) {
            codeDisplay.textContent = code;
        }

        // Render status & metadata
        const statusBadge = document.getElementById('track-status');
        statusBadge.className = 'badge ' + data.status;
        statusBadge.textContent = data.status.replace(/_/g, ' ');

        const catBadge = document.getElementById('track-category');
        catBadge.textContent = 'Category: ' + data.category;

        // Update workflow stepper
        updateWorkflowStepper(data.status);

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

// --- Moderator Authentication & Portal Logic ---
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

        // Update badge and username displays
        const badgeUser = document.getElementById('mod-badge-username');
        if (badgeUser) badgeUser.textContent = username;
        const currentUser = document.getElementById('mod-current-user');
        if (currentUser) currentUser.textContent = 'Logged in as: ' + username;

        // Close login dialog modal
        closeLoginModal();

        // Update header state: hide unauth login button, show auth controls
        const unauthActions = document.getElementById('unauth-header-actions');
        const authActions = document.getElementById('auth-header-actions');
        if (unauthActions) unauthActions.classList.add('hidden');
        if (authActions) authActions.classList.remove('hidden');

        showToast('Authenticated', 'Welcome back, ' + username + '. Accessing Triage Workspace.', 'success');

        // Switch to Triage Workspace
        switchWorkspace('triage');

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

    closeClosureModal();

    const container = document.querySelector('.container');
    if (container) container.classList.remove('triage-mode');

    // Reset header state: show unauth button, hide auth controls
    const unauthActions = document.getElementById('unauth-header-actions');
    const authActions = document.getElementById('auth-header-actions');
    if (unauthActions) unauthActions.classList.remove('hidden');
    if (authActions) authActions.classList.add('hidden');

    // Reset moderator views
    const tabMod = document.getElementById('tab-mod');
    if (tabMod) tabMod.classList.remove('active');
    closeModDetail();

    clearError('mod-login-error');

    // Return to public whistleblower view
    switchWorkspace('whistleblower');
    switchTab('submit');

    showToast('Logged Out', 'Moderator session terminated.', 'info');
}

async function fetchModReports() {
    if (!modToken) return;
    clearError('mod-list-error');

    const statusFilter = document.getElementById('mod-filter-status');
    const categoryFilter = document.getElementById('mod-filter-category');
    const status = statusFilter ? statusFilter.value : '';
    const category = categoryFilter ? categoryFilter.value : '';

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
        const countBadge = document.getElementById('mod-queue-count');
        if (countBadge) countBadge.textContent = String(reports.length);

        if (!list) return;
        list.innerHTML = '';

        if (reports.length === 0) {
            list.innerHTML = `
                <li class="triage-queue-empty">
                    ${getIcon('search', 'icon icon-lg')}
                    <p>No reports found matching criteria.</p>
                </li>
            `;
            if (currentModReportId) {
                closeModDetail();
            }
            return;
        }

        reports.forEach(r => {
            const li = document.createElement('li');
            const isActive = currentModReportId === r.id;
            li.className = 'report-item' + (isActive ? ' active' : '');
            li.dataset.id = String(r.id);
            li.setAttribute('role', 'option');
            li.setAttribute('aria-selected', isActive ? 'true' : 'false');
            li.onclick = () => viewModReport(r.id);

            const relTime = r.created_at ? formatRelativeTime(r.created_at) : '';
            const fullDate = r.created_at ? new Date(r.created_at).toLocaleString() : '';

            li.innerHTML = `
                <div class="report-item-header">
                    <div class="report-item-title-row">
                        <span class="report-item-id">Report #${r.id}</span>
                        <span class="cat-badge">${r.category}</span>
                    </div>
                    <span class="report-item-time" title="${fullDate}">${relTime}</span>
                </div>
                <div class="report-item-desc">${escapeHtml(r.description)}</div>
                <div class="report-item-footer">
                    <span class="badge ${r.status}">${r.status.replace(/_/g, ' ')}</span>
                    ${r.evidence_url ? `<span class="report-has-evidence" title="Has scrubbed evidence">${getIcon('fileText', 'icon icon-xs')} Evidence</span>` : ''}
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

        // Update active highlight in queue list
        document.querySelectorAll('#mod-report-list .report-item').forEach(item => {
            if (parseInt(item.dataset.id, 10) === reportId) {
                item.classList.add('active');
                item.setAttribute('aria-selected', 'true');
            } else {
                item.classList.remove('active');
                item.setAttribute('aria-selected', 'false');
            }
        });

        // Hide empty state, show detail content
        const emptyEl = document.getElementById('mod-detail-empty');
        const contentEl = document.getElementById('mod-detail-content');
        if (emptyEl) emptyEl.classList.add('hidden');
        if (contentEl) contentEl.classList.remove('hidden');

        // Populate Details
        document.getElementById('mod-detail-heading').textContent = 'Report #' + data.id;
        document.getElementById('mod-det-id').textContent = '#' + data.id;

        const dateStr = data.created_at ? new Date(data.created_at).toLocaleString() : 'N/A';
        const relStr = data.created_at ? formatRelativeTime(data.created_at) : '';
        document.getElementById('mod-det-created').textContent = relStr ? `${dateStr} (${relStr})` : dateStr;

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
                    <button type="button" class="btn btn-primary" onclick="advanceStatus('UNDER_REVIEW')">
                        ${getIcon('search', 'icon icon-xs')} Move to Under Review
                    </button>
                    <button type="button" class="btn btn-outline" onclick="advanceStatus('DISMISSED')">
                        ${getIcon('x', 'icon icon-xs')} Dismiss Report
                    </button>
                `;
            } else if (data.status === 'UNDER_REVIEW') {
                actions.innerHTML = `
                    <button type="button" class="btn btn-primary" onclick="advanceStatus('RESOLVED')">
                        ${getIcon('check', 'icon icon-xs')} Mark as Resolved
                    </button>
                    <button type="button" class="btn btn-outline" onclick="advanceStatus('DISMISSED')">
                        ${getIcon('x', 'icon icon-xs')} Dismiss Report
                    </button>
                `;
            } else {
                actions.innerHTML = `<span class="workflow-terminal-notice">${getIcon('info', 'icon icon-xs')} No further forward workflow transitions available. Use Permanent Case Closure below to finalize and shred evidence.</span>`;
            }
        }

        // Render Thread
        renderThread('mod-thread', data.messages);

        // Ensure detail view is visible
        const detailView = document.getElementById('mod-detail-view');
        if (detailView) detailView.classList.remove('hidden');

    } catch (err) {
        showToast('Error', 'Failed to load report: ' + err.message, 'error');
    }
}

function closeModDetail() {
    currentModReportId = null;
    currentModReport = null;

    document.querySelectorAll('#mod-report-list .report-item').forEach(item => {
        item.classList.remove('active');
        item.setAttribute('aria-selected', 'false');
    });

    const emptyEl = document.getElementById('mod-detail-empty');
    const contentEl = document.getElementById('mod-detail-content');
    if (emptyEl) emptyEl.classList.remove('hidden');
    if (contentEl) contentEl.classList.add('hidden');
}

async function advanceStatus(targetStatus) {
    if (!modToken || !currentModReportId) return;
    clearError('mod-status-error');

    const noteInput = document.getElementById('mod-status-note');
    const statusUpdate = noteInput ? noteInput.value.trim() : '';

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

        if (noteInput) noteInput.value = '';
        showToast('Status Updated', `Report #${currentModReportId} advanced to ${targetStatus.replace(/_/g, ' ')}.`, 'success');

        await viewModReport(currentModReportId);
        await fetchModReports();

    } catch (err) {
        showError('mod-status-error', err.message);
    }
}

async function sendModReply(e) {
    e.preventDefault();
    if (!modToken || !currentModReportId) return;

    const textInput = document.getElementById('mod-reply-text');
    const content = textInput ? textInput.value.trim() : '';
    if (!content) return;

    clearError('mod-reply-error');
    setBtnLoading('btn-mod-reply', true, 'Sending...');

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
        showToast('Message Sent', 'Dead Drop reply posted to whistleblower.', 'success');
        await viewModReport(currentModReportId);

    } catch (err) {
        showError('mod-reply-error', err.message);
    } finally {
        setBtnLoading('btn-mod-reply', false, 'Send Dead Drop Message');
    }
}

async function triggerPermanentClosure() {
    openClosureModal();
}

async function executePermanentClosure() {
    if (!modToken || !currentModReportId) return;
    clearError('mod-close-error');
    clearError('mod-modal-close-error');

    const reasonInput = document.getElementById('mod-close-reason');
    const reason = reasonInput ? reasonInput.value.trim() : '';
    const payload = reason ? { status_note: reason } : {};

    setBtnLoading('btn-confirm-permanent-close', true, 'Closing Case...');
    setBtnLoading('btn-mod-close', true, 'Closing Case...');

    try {
        const res = await fetch('/api/v1/moderator/reports/' + currentModReportId + '/close', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + modToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (res.status === 401) {
            closeClosureModal();
            return modLogout();
        }
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Permanent closure failed.');
        }

        closeClosureModal();
        if (reasonInput) reasonInput.value = '';

        showToast(
            'Case Permanently Closed',
            'ADR-0002 data minimization enforced: description redacted, evidence shredded, thread frozen.',
            'destructive',
            6000
        );

        await viewModReport(currentModReportId);
        await fetchModReports();

    } catch (err) {
        showError('mod-modal-close-error', err.message);
        showError('mod-close-error', err.message);
    } finally {
        setBtnLoading('btn-confirm-permanent-close', false, 'Confirm Permanent Closure');
        setBtnLoading('btn-mod-close', false, 'Irreversibly Close Case');
    }
}

// --- Window Global Bindings & Initialization ---
window.openLoginModal = openLoginModal;
window.closeLoginModal = closeLoginModal;
window.handleModalOverlayClick = handleModalOverlayClick;
window.openClosureModal = openClosureModal;
window.closeClosureModal = closeClosureModal;
window.handleClosureModalOverlayClick = handleClosureModalOverlayClick;
window.switchWorkspace = switchWorkspace;
window.switchTab = switchTab;
window.modLogin = modLogin;
window.modLogout = modLogout;
window.fetchModReports = fetchModReports;
window.viewModReport = viewModReport;
window.closeModDetail = closeModDetail;
window.advanceStatus = advanceStatus;
window.sendModReply = sendModReply;
window.triggerPermanentClosure = triggerPermanentClosure;
window.executePermanentClosure = executePermanentClosure;
window.formatRelativeTime = formatRelativeTime;
window.escapeHtml = escapeHtml;
window.handleFileSelection = handleFileSelection;
window.clearEvidenceFile = clearEvidenceFile;
window.updateWorkflowStepper = updateWorkflowStepper;
window.trackCaseFromSuccess = trackCaseFromSuccess;
window.copyCaseCode = copyCaseCode;
window.submitReport = submitReport;
window.resetSubmit = resetSubmit;
window.trackReport = trackReport;
window.resetTrack = resetTrack;
window.sendTrackReply = sendTrackReply;
window.renderThread = renderThread;

// Initialize components when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropzone);
} else {
    initDropzone();
}

