from functools import wraps
from flask import Blueprint, jsonify, redirect, render_template, session, url_for
from app.services import get_monitor
from app.services.server_store import is_local_host, store
from app.services.remote_monitor import RemoteMonitor

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/')
@login_required
def index():
    servers = store.list_servers()
    linux_servers = [s for s in servers if s.get('os_type') == 'linux']
    windows_servers = [s for s in servers if s.get('os_type') == 'windows']
    return render_template('index.html',
                           linux_servers=linux_servers,
                           windows_servers=windows_servers)


@dashboard_bp.route('/monitor/<path:host>')
@login_required
def monitor(host):
    if is_local_host(host):
        return render_template('monitor.html', host=host, system_type='linux')
    server = store.get_server(host)
    if not server:
        return redirect(url_for('dashboard.index'))
    return render_template('monitor.html', host=host,
                           system_type=server.get('os_type'))


@dashboard_bp.route('/api/stats')
@login_required
def get_stats():
    monitor = get_monitor()
    return jsonify(monitor.get_all_stats())


@dashboard_bp.route('/api/stats/<path:host>')
@login_required
def get_remote_stats(host):
    if is_local_host(host):
        monitor = get_monitor()
        return jsonify(monitor.get_all_stats())
    server = store.get_server(host, with_credentials=True)
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    try:
        monitor = RemoteMonitor(
            host=server['host'],
            username=server['username'],
            password=server['password'] or '',
            port=int(server['port'] or 22),
            os_type=server['os_type']
        )
        return jsonify(monitor.get_all_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 502
