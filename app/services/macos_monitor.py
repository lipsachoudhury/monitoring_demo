import psutil
import platform
from .base_monitor import BaseMonitor


class MacOSMonitor(BaseMonitor):
    
    def get_cpu_usage(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'percent': cpu_percent,
            'count': cpu_count,
            'frequency': {
                'current': cpu_freq.current if cpu_freq else 0,
                'min': cpu_freq.min if cpu_freq else 0,
                'max': cpu_freq.max if cpu_freq else 0
            }
        }
    
    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
    
    def get_disk_usage(self):
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        
        return partitions
    
    def get_network_usage(self):
        net_io = psutil.net_io_counters()
        interfaces = {}
        
        for iface, addrs in psutil.net_if_addrs().items():
            addresses = []
            for addr in addrs:
                if addr.family.name == 'AF_INET':
                    addresses.append({
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
            if addresses:
                interfaces[iface] = addresses
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'interfaces': interfaces
        }
    
    def get_open_ports(self):
        ports = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    ports.append({
                        'fd': conn.fd,
                        'family': conn.family.name,
                        'type': conn.type.name,
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
        except (psutil.AccessDenied, PermissionError):
            ports = self._get_ports_via_netstat()
        return sorted(ports, key=lambda x: x.get('local_address') or '')
    
    def _get_ports_via_netstat(self):
        """Fallback for when psutil does not have the needed permissions."""
        import subprocess
        ports = []
        try:
            result = subprocess.run(
                ['netstat', '-anv', '-p', 'tcp'],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.splitlines()[1:]:
                columns = line.split()
                if len(columns) < 4:
                    continue
                state = columns[5] if len(columns) > 5 else ''
                if state != 'LISTEN':
                    continue
                local = columns[3] if len(columns) > 3 else ''
                if '.' in local:
                    ip, port = local.rsplit('.', 1)
                    if port.isdigit():
                        ports.append({
                            'fd': None,
                            'family': 'AF_INET',
                            'type': 'SOCK_STREAM',
                            'local_address': f"{ip}:{port}",
                            'remote_address': None,
                            'status': 'LISTEN',
                            'pid': None
                        })
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return ports
    
    def get_top_processes(self, limit=10):
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] is not None and pinfo['memory_percent'] is not None:
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': round(pinfo['memory_percent'], 2),
                        'status': pinfo['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:limit]
