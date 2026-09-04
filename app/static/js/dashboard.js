const REFRESH_INTERVAL = 3000;
let previousNetStats = null;

function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

function formatSpeed(bytesPerSec) {
    if (bytesPerSec < 0) return '--';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytesPerSec) / Math.log(k));
    if (i < 0 || i >= sizes.length) return '0 B/s';
    return parseFloat((bytesPerSec / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getUsageClass(percent) {
    if (percent >= 80) return 'usage-high';
    if (percent >= 60) return 'usage-medium';
    return 'usage-low';
}

function updateConnectionStatus(online) {
    const status = document.getElementById('connectionStatus');
    const text = document.getElementById('statusText');
    if (online) {
        status.classList.remove('offline');
        text.textContent = 'Live';
    } else {
        status.classList.add('offline');
        text.textContent = 'Offline';
    }
}

function updateCPU(cpu) {
    const percent = Math.round(cpu.percent);
    const percentEl = document.getElementById('cpuPercent');
    const barEl = document.getElementById('cpuBar');
    
    percentEl.textContent = percent;
    percentEl.className = getUsageClass(percent);
    barEl.style.width = percent + '%';
    
    document.getElementById('cpuCount').textContent = cpu.count + ' cores';
    document.getElementById('cpuFreq').textContent = (cpu.frequency?.current || 0).toFixed(0) + ' MHz';
}

function updateMemory(memory) {
    const percent = Math.round(memory.percent);
    const percentEl = document.getElementById('memPercent');
    const barEl = document.getElementById('memBar');
    
    percentEl.textContent = percent;
    percentEl.className = getUsageClass(percent);
    barEl.style.width = percent + '%';
    
    document.getElementById('memUsed').textContent = formatBytes(memory.used) + ' used';
    document.getElementById('memTotal').textContent = 'Total: ' + formatBytes(memory.total);
}

function updateNetwork(network) {
    const now = Date.now();
    const total = network.bytes_sent + network.bytes_recv;
    
    const speedEl = document.getElementById('netSpeed');
    
    if (previousNetStats) {
        const elapsed = (now - previousNetStats.time) / 1000;
        if (elapsed > 0) {
            const upSpeed = (network.bytes_sent - previousNetStats.sent) / elapsed;
            const downSpeed = (network.bytes_recv - previousNetStats.recv) / elapsed;
            
            document.getElementById('netUp').textContent = formatSpeed(upSpeed);
            document.getElementById('netDown').textContent = formatSpeed(downSpeed);
            speedEl.textContent = formatSpeed(upSpeed + downSpeed);
        }
    } else {
        document.getElementById('netUp').textContent = '--';
        document.getElementById('netDown').textContent = '--';
        speedEl.textContent = '--';
    }
    
    previousNetStats = {
        time: now,
        sent: network.bytes_sent,
        recv: network.bytes_recv
    };
}

function updateDisks(disks) {
    const diskList = document.getElementById('diskList');
    if (!disks || disks.length === 0) {
        diskList.innerHTML = '<div class="loading">No disk partitions found</div>';
        return;
    }
    
    diskList.innerHTML = disks.map(disk => {
        const percent = Math.round(disk.percent);
        const fillClass = getUsageClass(percent);
        return `
            <div class="disk-item">
                <div class="disk-info">
                    <span class="disk-name"><i class="fas fa-hard-drive"></i> ${disk.mountpoint}</span>
                    <span class="disk-stats">${formatBytes(disk.used)} / ${formatBytes(disk.total)} (${percent}%)</span>
                </div>
                <div class="disk-bar">
                    <div class="disk-bar-fill ${fillClass}" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

function updateProcesses(processes) {
    const tableBody = document.getElementById('processTable');
    if (!processes || processes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="loading">No process data</td></tr>';
        return;
    }
    
    tableBody.innerHTML = processes.map(proc => {
        const cpuClass = getUsageClass(proc.cpu_percent);
        const memClass = getUsageClass(proc.memory_percent);
        const isRunning = proc.status === 'running';
        return `
            <tr>
                <td>${proc.pid}</td>
                <td class="process-name">${escapeHtml(proc.name)}</td>
                <td class="${cpuClass}">${proc.cpu_percent.toFixed(1)}%</td>
                <td class="${memClass}">${proc.memory_percent.toFixed(1)}%</td>
                <td>
                    <span class="status-badge ${isRunning ? 'status-running' : ''}">${proc.status || 'N/A'}</span>
                </td>
            </tr>
        `;
    }).join('');
}

function updatePorts(ports) {
    const tableBody = document.getElementById('portTable');
    const portCount = document.getElementById('portCount');
    
    if (!ports || ports.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" class="loading">No open ports found</td></tr>';
        portCount.textContent = '0';
        return;
    }
    
    portCount.textContent = ports.length;
    tableBody.innerHTML = ports.map(conn => {
        const localAddr = conn.local_address || 'N/A';
        const portMatch = localAddr.match(/:(\d+)$/);
        const port = portMatch ? portMatch[1] : localAddr;
        const protocol = (conn.type_name || conn.type || '').includes('SOCK_STREAM') ? 'TCP' : 'UDP';
        
        return `
            <tr>
                <td><span class="status-badge">${port}</span></td>
                <td>${protocol}</td>
                <td>${conn.pid ? 'PID ' + conn.pid : 'N/A'}</td>
            </tr>
        `;
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function fetchStats() {
    try {
        const host = window.MONITOR_HOST || 'localhost';
        const url = host === 'localhost' ? '/api/stats' : `/api/stats/${encodeURIComponent(host)}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to fetch stats');
        }
        
        const data = await response.json();
        
        updateConnectionStatus(true);
        updateCPU(data.cpu);
        updateMemory(data.memory);
        updateNetwork(data.network);
        updateDisks(data.disk);
        updateProcesses(data.processes);
        updatePorts(data.ports);
    } catch (error) {
        console.error('Error fetching stats:', error);
        updateConnectionStatus(false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    setInterval(fetchStats, REFRESH_INTERVAL);
});
