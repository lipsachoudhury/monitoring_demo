from functools import wraps
from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for
from app.services.server_store import store
from app.services.remote_monitor import RemoteMonitor

servers_bp = Blueprint('servers', __name__)

VALID_OS = {'linux', 'windows'}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@servers_bp.route('/servers')
@login_required
def index():
    os_type = request.args.get('os_type', 'linux')
    if os_type not in VALID_OS:
        os_type = 'linux'
    servers = store.list_servers(os_type=os_type)
    return render_template('servers.html', os_type=os_type, servers=servers)


@servers_bp.route('/api/servers')
@login_required
def list_servers():
    os_type = request.args.get('os_type')
    servers = store.list_servers(os_type=os_type)
    return jsonify(servers)


@servers_bp.route('/api/servers', methods=['POST'])
@login_required
def add_server():
    data = request.get_json()
    host = (data.get('host') or '').strip()
    os_type = (data.get('os_type') or 'linux').lower()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    port = int(data.get('port') or 22)

    if not host or not username:
        return jsonify({'error': 'Host and username are required'}), 400
    if os_type not in VALID_OS:
        return jsonify({'error': 'Invalid OS type'}), 400

    server = {
        'host': host,
        'os_type': os_type,
        'username': username,
        'password': password,
        'port': port,
        'name': (data.get('name') or host).strip()
    }

    if not store.add_server(server):
        return jsonify({'error': f'Server {host} already exists'}), 409
    return jsonify({'success': True, 'host': host}), 201


@servers_bp.route('/api/servers/<host>', methods=['PUT'])
@login_required
def update_server(host):
    data = request.get_json()
    updates = {}
    if 'port' in data:
        updates['port'] = int(data['port'])
    if 'password' in data and data['password']:
        updates['password'] = data['password']
    if 'name' in data:
        updates['name'] = (data['name'] or host).strip()
    if not store.update_server(host, updates):
        return jsonify({'error': 'Server not found'}), 404
    return jsonify({'success': True})


@servers_bp.route('/api/servers/<host>', methods=['DELETE'])
@login_required
def delete_server(host):
    if not store.remove_server(host):
        return jsonify({'error': 'Server not found'}), 404
    return jsonify({'success': True})


@servers_bp.route('/api/servers/test', methods=['POST'])
@login_required
def test_connection():
    data = request.get_json()
    monitor = RemoteMonitor(
        host=data.get('host'),
        username=data.get('username'),
        password=data.get('password') or '',
        port=int(data.get('port') or 22),
        os_type=data.get('os_type') or 'linux'
    )
    ok, message = monitor.test_connection()
    return jsonify({'success': ok, 'message': message})


@servers_bp.route('/api/servers/<host>/stats')
@login_required
def server_stats(host):
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
        stats = monitor.get_all_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 502
