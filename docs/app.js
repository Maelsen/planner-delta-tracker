/**
 * Planner Delta Tracker - Admin Panel
 *
 * This script manages the admin interface for configuring
 * the Planner Delta Tracker report settings.
 */

// Configuration stored in localStorage
const STORAGE_KEY = 'planner-admin-config';
const SETTINGS_FILE = 'settings.json';

// State
let config = null;
let settings = {
    recipients: [],
    schedule_day: 'monday',
    schedule_hour: 8,
    admin_password_hash: ''
};

// Day names for display
const dayNames = {
    monday: 'Montag',
    tuesday: 'Dienstag',
    wednesday: 'Mittwoch',
    thursday: 'Donnerstag',
    friday: 'Freitag',
    saturday: 'Samstag',
    sunday: 'Sonntag'
};

// Simple hash function for password (not cryptographically secure, but sufficient for this use case)
async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password + 'planner-salt-2024');
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Load config from localStorage
function loadConfig() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            return null;
        }
    }
    return null;
}

// Save config to localStorage
function saveConfig(cfg) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
}

// Clear config from localStorage
function clearConfig() {
    localStorage.removeItem(STORAGE_KEY);
}

// GitHub API helper
async function githubAPI(endpoint, options = {}) {
    const url = `https://api.github.com/repos/${config.repo}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            'Authorization': `Bearer ${config.token}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            ...options.headers
        }
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `GitHub API error: ${response.status}`);
    }

    return response.json();
}

// Load settings from GitHub
async function loadSettings() {
    try {
        const response = await githubAPI(`/contents/${SETTINGS_FILE}`);
        const content = atob(response.content);
        settings = JSON.parse(content);
        settings.sha = response.sha; // Store SHA for updates
        return settings;
    } catch (e) {
        if (e.message.includes('404')) {
            // File doesn't exist yet, use defaults
            return settings;
        }
        throw e;
    }
}

// Save settings to GitHub
async function saveSettings() {
    const content = btoa(JSON.stringify(settings, null, 2));
    const body = {
        message: 'Update settings via Admin UI',
        content: content
    };

    if (settings.sha) {
        body.sha = settings.sha;
    }

    const response = await githubAPI(`/contents/${SETTINGS_FILE}`, {
        method: 'PUT',
        body: JSON.stringify(body)
    });

    settings.sha = response.content.sha;
    return response;
}

// Get last workflow run
async function getLastWorkflowRun() {
    try {
        const response = await githubAPI('/actions/runs?per_page=1');
        if (response.workflow_runs && response.workflow_runs.length > 0) {
            const run = response.workflow_runs[0];
            return {
                status: run.conclusion || run.status,
                date: new Date(run.created_at).toLocaleString('de-CH'),
                url: run.html_url
            };
        }
    } catch (e) {
        console.error('Error fetching workflow runs:', e);
    }
    return null;
}

// Trigger workflow
async function triggerWorkflow() {
    await githubAPI('/actions/workflows/weekly-report.yml/dispatches', {
        method: 'POST',
        body: JSON.stringify({
            ref: 'main',
            inputs: {
                force_run: 'true'
            }
        })
    });
}

// Calculate next report date
function getNextReportDate() {
    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const targetDay = days.indexOf(settings.schedule_day);
    const now = new Date();
    const currentDay = now.getDay();

    let daysUntil = targetDay - currentDay;
    if (daysUntil <= 0) {
        daysUntil += 7;
    }

    const nextDate = new Date(now);
    nextDate.setDate(now.getDate() + daysUntil);
    nextDate.setHours(settings.schedule_hour, 0, 0, 0);

    return nextDate.toLocaleDateString('de-CH', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// UI Functions
function showElement(id) {
    document.getElementById(id).classList.remove('hidden');
}

function hideElement(id) {
    document.getElementById(id).classList.add('hidden');
}

function showStatus(message, type = 'loading') {
    const statusEl = document.getElementById('action-status');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    showElement('action-status');
}

function hideStatus() {
    hideElement('action-status');
}

function renderRecipients() {
    const container = document.getElementById('recipients-list');

    if (settings.recipients.length === 0) {
        container.innerHTML = '<div class="empty-state">Keine Empfänger konfiguriert</div>';
        return;
    }

    container.innerHTML = settings.recipients.map((email, index) => `
        <div class="recipient-item">
            <span>${email}</span>
            <button onclick="removeRecipient(${index})">Entfernen</button>
        </div>
    `).join('');
}

function updateUI() {
    // Update schedule selects
    document.getElementById('schedule-day').value = settings.schedule_day;
    document.getElementById('schedule-hour').value = settings.schedule_hour;

    // Update recipients
    renderRecipients();

    // Update next report
    document.getElementById('next-report').textContent = getNextReportDate();
}

async function updateWorkflowStatus() {
    const lastRun = await getLastWorkflowRun();
    const statusEl = document.getElementById('last-run');

    if (lastRun) {
        const statusEmoji = lastRun.status === 'success' ? '✓' :
                           lastRun.status === 'failure' ? '✗' : '⋯';
        statusEl.innerHTML = `<a href="${lastRun.url}" target="_blank">${statusEmoji} ${lastRun.date}</a>`;
    } else {
        statusEl.textContent = 'Keine Daten';
    }
}

// Event Handlers
function removeRecipient(index) {
    settings.recipients.splice(index, 1);
    renderRecipients();
}

function addRecipient() {
    const input = document.getElementById('new-recipient');
    const email = input.value.trim();

    if (!email) return;

    // Simple email validation
    if (!email.includes('@') || !email.includes('.')) {
        alert('Bitte geben Sie eine gültige E-Mail-Adresse ein.');
        return;
    }

    if (settings.recipients.includes(email)) {
        alert('Diese E-Mail-Adresse ist bereits in der Liste.');
        return;
    }

    settings.recipients.push(email);
    input.value = '';
    renderRecipients();
}

async function saveAllSettings() {
    try {
        showStatus('Speichere Einstellungen...', 'loading');

        // Get values from form
        settings.schedule_day = document.getElementById('schedule-day').value;
        settings.schedule_hour = parseInt(document.getElementById('schedule-hour').value);

        await saveSettings();

        showStatus('Einstellungen gespeichert!', 'success');
        updateUI();

        setTimeout(hideStatus, 3000);
    } catch (e) {
        showStatus(`Fehler: ${e.message}`, 'error');
    }
}

async function triggerReport() {
    try {
        showStatus('Starte Report...', 'loading');
        await triggerWorkflow();
        showStatus('Report gestartet! Der Workflow läuft jetzt.', 'success');

        // Update status after a delay
        setTimeout(async () => {
            await updateWorkflowStatus();
        }, 5000);

        setTimeout(hideStatus, 5000);
    } catch (e) {
        showStatus(`Fehler: ${e.message}`, 'error');
    }
}

// Password verification
async function verifyPassword(password) {
    const hash = await hashPassword(password);
    return hash === settings.admin_password_hash;
}

// Initialize
async function init() {
    config = loadConfig();

    if (!config) {
        // First time setup
        hideElement('password-modal');
        showElement('setup-modal');
        return;
    }

    // Try to load settings
    try {
        await loadSettings();
    } catch (e) {
        alert(`Fehler beim Laden: ${e.message}\nBitte überprüfen Sie den Token und das Repository.`);
        clearConfig();
        location.reload();
        return;
    }

    // Check if password is set
    if (!settings.admin_password_hash) {
        hideElement('password-modal');
        showElement('setup-modal');
        // Pre-fill repo if we have it
        document.getElementById('setup-repo').value = config.repo || '';
        document.getElementById('setup-token').value = config.token || '';
        return;
    }

    // Show password prompt
    showElement('password-modal');
}

// Setup Form Handler
document.getElementById('setup-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const password = document.getElementById('setup-password').value;
    const token = document.getElementById('setup-token').value;
    const repo = document.getElementById('setup-repo').value;
    const errorEl = document.getElementById('setup-error');

    try {
        // Validate token by making a test request
        config = { token, repo };

        // Test connection
        try {
            await githubAPI('/contents');
        } catch (e) {
            errorEl.textContent = 'Token oder Repository ungültig. Bitte überprüfen.';
            errorEl.classList.remove('hidden');
            return;
        }

        // Save config
        saveConfig(config);

        // Load or create settings
        try {
            await loadSettings();
        } catch (e) {
            // Settings file doesn't exist, will be created
        }

        // Set password hash
        settings.admin_password_hash = await hashPassword(password);
        await saveSettings();

        // Proceed to admin panel
        hideElement('setup-modal');
        showElement('admin-panel');
        updateUI();
        updateWorkflowStatus();

    } catch (e) {
        errorEl.textContent = e.message;
        errorEl.classList.remove('hidden');
    }
});

// Password Form Handler
document.getElementById('password-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const password = document.getElementById('password-input').value;
    const errorEl = document.getElementById('password-error');

    if (await verifyPassword(password)) {
        hideElement('password-modal');
        showElement('admin-panel');
        updateUI();
        updateWorkflowStatus();
    } else {
        errorEl.classList.remove('hidden');
        document.getElementById('password-input').value = '';
    }
});

// Button Event Listeners
document.getElementById('add-recipient-btn').addEventListener('click', addRecipient);
document.getElementById('new-recipient').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        addRecipient();
    }
});

document.getElementById('save-btn').addEventListener('click', saveAllSettings);
document.getElementById('trigger-btn').addEventListener('click', triggerReport);

document.getElementById('logout-btn').addEventListener('click', () => {
    location.reload();
});

// Start
init();
