import json
import os
import base64
from cryptography.fernet import Fernet


class ServerStore:
    """Persists monitored server configurations in a JSON file.
    
    Credentials are obfuscated using a Fernet key derived from the
    application secret. In production, store the key in a secure
    secret manager.
    """
    
    def __init__(self, storage_path=None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'servers.json'
        )
        if not os.path.exists(self.storage_path):
            self._save({})
        self._ensure_key()
    
    def _ensure_key(self):
        secret = os.getenv('SECRET_KEY')
        if not secret:
            raise RuntimeError('SECRET_KEY must be set in the environment (via .env).')
        digest = __import__('hashlib').sha256(secret.encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))
    
    def _encrypt(self, value):
        if not value:
            return None
        return self._fernet.encrypt(value.encode()).decode()
    
    def _decrypt(self, value):
        if not value:
            return None
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception:
            return None
    
    def _load(self):
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save(self, data):
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_server(self, server):
        data = self._load()
        host = server['host']
        if host in data:
            return False
        server['password'] = self._encrypt(server.get('password'))
        server['sudo_password'] = self._encrypt(server.get('sudo_password'))
        data[host] = server
        self._save(data)
        return True
    
    def update_server(self, host, updates):
        data = self._load()
        if host not in data:
            return False
        if 'password' in updates and updates.get('password'):
            updates['password'] = self._encrypt(updates['password'])
        if 'sudo_password' in updates and updates.get('sudo_password'):
            updates['sudo_password'] = self._encrypt(updates['sudo_password'])
        data[host].update(updates)
        self._save(data)
        return True
    
    def remove_server(self, host):
        data = self._load()
        if host in data:
            del data[host]
            self._save(data)
            return True
        return False
    
    def get_server(self, host, with_credentials=False):
        data = self._load()
        server = data.get(host)
        if not server:
            return None
        server = dict(server)
        if with_credentials:
            server['password'] = self._decrypt(server.get('password'))
            server['sudo_password'] = self._decrypt(server.get('sudo_password'))
        else:
            server.pop('password', None)
            server.pop('sudo_password', None)
        return server
    
    def list_servers(self, os_type=None):
        data = self._load()
        servers = []
        for host, server in data.items():
            item = dict(server)
            item['host'] = host
            item.pop('password', None)
            item.pop('sudo_password', None)
            if os_type and item.get('os_type') != os_type:
                continue
            servers.append(item)
        return servers


LOCAL_HOSTS = frozenset({'localhost', '127.0.0.1', '::1'})


def is_local_host(host: str) -> bool:
    """True when metrics can be read on this machine, with no SSH login."""
    return (host or '').strip().lower() in LOCAL_HOSTS


store = ServerStore()
