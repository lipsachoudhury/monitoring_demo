const OS_TYPE = window.CURRENT_OS || 'linux';
let pendingDeleteHost = null;

function showMessage(message, type) {
    const el = document.getElementById('formMessage');
    el.textContent = message;
    el.className = 'form-message ' + (type || '');
    setTimeout(() => {
        el.textContent = '';
        el.className = 'form-message';
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadServers() {
    try {
        const response = await fetch(`/api/servers?os_type=${OS_TYPE}`);
        if (!response.ok) throw new Error('Failed to load servers');
        const servers = await response.json();
        renderServers(servers);
    } catch (err) {
        console.error(err);
        const tbody = document.getElementById('serversTable');
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Failed to load servers</td></tr>';
    }
}

function renderServers(servers) {
    const tbody = document.getElementById('serversTable');
    if (!servers || servers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading">No ${OS_TYPE} servers connected yet</td></tr>`;
        return;
    }
    tbody.innerHTML = servers.map(s => `
        <tr>
            <td class="table-primary">${escapeHtml(s.name)}</td>
            <td>${escapeHtml(s.host)}</td>
            <td>${escapeHtml(s.username)}</td>
            <td>${s.port}</td>
            <td class="action-cell">
                <a href="/monitor/${encodeURIComponent(s.host)}" class="btn-view">
                    <i class="fas fa-chart-line"></i> Monitor
                </a>
                <button class="btn-delete" data-host="${escapeHtml(s.host)}" data-name="${escapeHtml(s.name)}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tbody.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', () => openDeleteModal(btn.dataset.host, btn.dataset.name));
    });
}

function openDeleteModal(host, name) {
    pendingDeleteHost = host;
    document.getElementById('deleteHostName').textContent = name;
    document.getElementById('deleteModal').classList.add('active');
}

function closeModal() {
    document.getElementById('deleteModal').classList.remove('active');
    pendingDeleteHost = null;
}

async function deleteServer() {
    if (!pendingDeleteHost) return;
    try {
        const response = await fetch(`/api/servers/${encodeURIComponent(pendingDeleteHost)}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to remove server');
        closeModal();
        loadServers();
    } catch (err) {
        console.error(err);
        alert('Failed to remove server');
    }
}

async function testConnection() {
    const form = document.getElementById('addServerForm');
    const button = document.getElementById('testConnectionBtn');
    
    const host = document.getElementById('host').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const port = document.getElementById('port').value || 22;
    
    if (!host || !username || !password) {
        showMessage('Please fill in host, username and password first', 'error');
        return;
    }
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    
    try {
        const response = await fetch('/api/servers/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, username, password, port, os_type: OS_TYPE })
        });
        const data = await response.json();
        if (data.success) {
            showMessage('Connection successful!', 'success');
        } else {
            showMessage('Test failed: ' + data.message, 'error');
        }
    } catch (err) {
        showMessage('Test failed: ' + err.message, 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-plug"></i> Test Connection';
    }
}

async function addServer(e) {
    e.preventDefault();
    const form = document.getElementById('addServerForm');
    
    const host = document.getElementById('host').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const port = document.getElementById('port').value || 22;
    const name = document.getElementById('name').value.trim();
    
    try {
        const response = await fetch('/api/servers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, username, password, port, os_type: OS_TYPE, name })
        });
        const data = await response.json();
        if (response.ok) {
            showMessage('Server added successfully!', 'success');
            form.reset();
            document.getElementById('port').value = 22;
            loadServers();
        } else {
            showMessage(data.error || 'Failed to add server', 'error');
        }
    } catch (err) {
        showMessage('Failed to add server: ' + err.message, 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadServers();
    
    document.getElementById('addServerForm').addEventListener('submit', addServer);
    document.getElementById('testConnectionBtn').addEventListener('click', testConnection);
    document.getElementById('confirmDeleteBtn').addEventListener('click', deleteServer);
    
    document.querySelectorAll('[data-close]').forEach(el => {
        el.addEventListener('click', closeModal);
    });
    
    const modal = document.getElementById('deleteModal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
});
