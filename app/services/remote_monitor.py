import re
import time
import paramiko


class RemoteMonitor:
    """Monitors remote Linux/Windows machines over SSH.
    
    Commands are platform-specific; new operating systems can be added
    by registering additional command sets.
    """
    
    LINUX_COMMANDS = {
        'cpu_sample': (
            "A=$(awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8, $5}' /proc/stat); "
            "sleep 0.6; "
            "B=$(awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8, $5}' /proc/stat); "
            "echo \"$A|$B\""
        ),
        'cpu_count': "nproc",
        'cpu_freq': (
            "awk -F': ' '/cpu MHz/ {print $2; exit}' /proc/cpuinfo 2>/dev/null || "
            "echo 0"
        ),
        'memory': "free -b | awk '/Mem:/{print $2,$3,$7} /Swap:/{print $2,$3}'",
        'disk': "df -B1 --output=source,target,fstype,size,used,avail,pcent 2>/dev/null",
        'netstat': (
            "head -n1 /proc/net/dev; "
            "grep -E ':' /proc/net/dev | while read iface rx tx rest; do "
            "echo \"$iface ${rx%:} $tx\"; done"
        ),
        'net_speed': (
            "IF1=$(cat /sys/class/net/*/statistics/rx_bytes | awk '{s+=$1} END{print s}'); "
            "IF2=$(cat /sys/class/net/*/statistics/tx_bytes | awk '{s+=$1} END{print s}'); "
            "echo \"$IF1 $IF2\""
        ),
        'ports': "ss -tln 2>/dev/null || netstat -tln",
        'processes': (
            "ps -eo pid,comm,pcpu,pmem,stat --sort=-pcpu | head -n 11 | tail -n 10"
        ),
        'uptime': "uptime",
    }
    
    WINDOWS_COMMANDS = {
        'cpu': (
            "powershell -NoProfile -Command "
            "\"Get-CimInstance Win32_Processor | Select-Object NumberOfCores,CurrentClockSpeed;"
            "(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor)[0].PercentProcessorTime\""
        ),
        'memory': (
            "powershell -NoProfile -Command "
            "\"$c=Get-CimInstance Win32_OperatingSystem;"
            "'{0} {1} {2}' -f $c.TotalVisibleMemorySize,$c.FreePhysicalMemory,((Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory).AvailableBytes)\""
        ),
        'processes': (
            "powershell -NoProfile -Command "
            "\"Get-Process | Sort-Object CPU -Descending | "
            "Select-Object -First 10 Id,ProcessName,CPU,@{N='Mem';E={[math]::Round($_.WS/1MB,1)}} | "
            "Format-Table -HideTableHeaders\""
        ),
    }
    
    def __init__(self, host, username, password, port=22, os_type='linux',
                 sudo_password=None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.os_type = os_type.lower()
        self.sudo_password = sudo_password or password
    
    def _connect(self, timeout=10):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False
        )
        return client
    
    def _exec(self, client, command, timeout=15):
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read().decode(errors='ignore')
        err = stderr.read().decode(errors='ignore')
        return out.strip(), err.strip()
    
    def _sftp_read(self, client, path):
        try:
            sftp = client.open_sftp()
            with sftp.open(path, 'r') as f:
                return f.read().decode(errors='ignore')
            sftp.close()
        except Exception:
            return None
    
    def _run(self, command, timeout=15):
        client = self._connect()
        try:
            return self._exec(client, command, timeout)
        finally:
            client.close()
    
    def _parse_linux(self):
        client = self._connect()
        try:
            cpu_sample, _ = self._exec(client, self.LINUX_COMMANDS['cpu_sample'])
            cpu_count, _ = self._exec(client, self.LINUX_COMMANDS['cpu_count'])
            cpu_freq, _ = self._exec(client, self.LINUX_COMMANDS['cpu_freq'])
            memory, _ = self._exec(client, self.LINUX_COMMANDS['memory'])
            disk, _ = self._exec(client, self.LINUX_COMMANDS['disk'])
            netstat, _ = self._exec(client, self.LINUX_COMMANDS['netstat'])
            net_speed, _ = self._exec(client, self.LINUX_COMMANDS['net_speed'])
            ports, _ = self._exec(client, self.LINUX_COMMANDS['ports'])
            processes, _ = self._exec(client, self.LINUX_COMMANDS['processes'])
            return dict(
                cpu_sample=cpu_sample, cpu_count=cpu_count, cpu_freq=cpu_freq,
                memory=memory, disk=disk, netstat=netstat, net_speed=net_speed,
                ports=ports, processes=processes
            )
        finally:
            client.close()
    
    def get_all_stats(self):
        if self.os_type in ('linux', 'ubuntu', 'debian', 'centos', 'fedora', 'redhat'):
            return self._collect_linux()
        elif self.os_type in ('windows', 'win'):
            return self._collect_windows()
        else:
            return self._collect_linux()
    
    def _collect_linux(self):
        raw = self._parse_linux()
        return {
            'cpu': self._cpu_linux(raw),
            'memory': self._memory_linux(raw),
            'disk': self._disk_linux(raw),
            'network': self._network_linux(raw),
            'ports': self._ports_linux(raw),
            'processes': self._processes_linux(raw),
            'host': self.host,
            'os_type': 'linux'
        }
    
    def _cpu_linux(self, raw):
        parts = raw['cpu_sample'].split('|')
        if len(parts) == 2:
            try:
                a_total, a_idle = [int(x) for x in parts[0].split()]
                b_total, b_idle = [int(x) for x in parts[1].split()]
                dt = b_total - a_total
                di = b_idle - a_idle
                if dt > 0:
                    percent = max(0.0, (dt - di) / dt * 100.0)
                else:
                    percent = 0.0
            except ValueError:
                percent = 0.0
        else:
            percent = 0.0
        try:
            count = int(raw['cpu_count'].strip())
        except (ValueError, AttributeError):
            count = 0
        try:
            freq = float(raw['cpu_freq'].strip())
        except (ValueError, AttributeError):
            freq = 0
        return {
            'percent': round(percent, 1),
            'count': count,
            'frequency': {'current': freq}
        }
    
    def _memory_linux(self, raw):
        m = raw['memory'].splitlines()
        mem = m[0].split() if m else []
        used_bytes = int(mem[1]) if len(mem) > 1 else 0
        total_bytes = int(mem[0]) if len(mem) > 0 else 0
        percent = (used_bytes / total_bytes * 100) if total_bytes else 0
        swap = m[1].split() if len(m) > 1 else []
        return {
            'total': total_bytes,
            'used': used_bytes,
            'available': int(mem[2]) if len(mem) > 2 else 0,
            'percent': round(percent, 1),
            'swap_total': int(swap[0]) if swap else 0,
            'swap_used': int(swap[1]) if len(swap) > 1 else 0,
            'swap_percent': (int(swap[1]) / int(swap[0]) * 100) if swap and int(swap[0]) else 0
        }
    
    def _disk_linux(self, raw):
        partitions = []
        for line in raw['disk'].splitlines()[1:]:
            parts = line.split()
            if len(parts) < 7:
                continue
            size, used, avail = int(parts[3]), int(parts[4]), int(parts[5])
            if size <= 0:
                continue
            percent = int(parts[6].rstrip('%'))
            partitions.append({
                'device': parts[0],
                'mountpoint': parts[1],
                'fstype': parts[2],
                'total': size,
                'used': used,
                'free': avail,
                'percent': percent
            })
        return partitions
    
    def _network_linux(self, raw):
        total_rx = 0
        total_tx = 0
        for line in raw['netstat'].splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3 and parts[0].endswith(':') and parts[1].isdigit():
                total_rx += int(parts[1])
                total_tx += int(parts[2])
        return {
            'bytes_sent': total_tx,
            'bytes_recv': total_rx,
            'packets_sent': 0,
            'packets_recv': 0,
            'interfaces': {}
        }
    
    def _ports_linux(self, raw):
        ports = []
        for line in raw['ports'].splitlines():
            if 'LISTEN' in line:
                match = re.search(r':(\d+)\s', line)
                if match:
                    addr = re.search(r'(\S+):\d+\s', line)
                    local = f"{addr.group(1)}:{match.group(1)}" if addr else f"0.0.0.0:{match.group(1)}"
                    ports.append({
                        'local_address': local,
                        'status': 'LISTEN',
                        'pid': None,
                        'type': 'SOCK_STREAM',
                        'family': 'AF_INET',
                        'remote_address': None,
                        'fd': None
                    })
        return ports
    
    def _processes_linux(self, raw):
        processes = []
        for line in raw['processes'].splitlines():
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            try:
                processes.append({
                    'pid': int(parts[0]),
                    'name': parts[1],
                    'cpu_percent': float(parts[2]),
                    'memory_percent': float(parts[3]),
                    'status': parts[4].strip()
                })
            except ValueError:
                continue
        return processes
    
    def _collect_windows(self):
        client = self._connect()
        try:
            cpu, _ = self._exec(client, self.WINDOWS_COMMANDS['cpu'])
            memory, _ = self._exec(client, self.WINDOWS_COMMANDS['memory'])
            processes, _ = self._exec(client, self.WINDOWS_COMMANDS['processes'])
        finally:
            client.close()
        return {
            'cpu': self._cpu_windows(cpu),
            'memory': self._memory_windows(memory),
            'disk': [],
            'network': {'bytes_sent': 0, 'bytes_recv': 0, 'interfaces': {}},
            'ports': [],
            'processes': self._processes_windows(processes),
            'host': self.host,
            'os_type': 'windows'
        }
    
    def _cpu_windows(self, output):
        lines = output.splitlines()
        cores = 0
        freq = 0
        percent = 0
        if lines:
            try:
                row = lines[0].split()
                if len(row) >= 2:
                    cores = int(row[0])
                    freq = int(row[1])
            except ValueError:
                pass
        if len(lines) >= 2:
            try:
                percent = float(lines[1])
            except ValueError:
                percent = 0
        return {'percent': percent, 'count': cores, 'frequency': {'current': freq}}
    
    def _memory_windows(self, output):
        parts = output.split()
        percent = 0
        total = 0
        used = 0
        return {'percent': percent, 'total': total, 'used': used, 'available': 0}
    
    def _processes_windows(self, output):
        processes = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                try:
                    processes.append({
                        'pid': int(parts[0]),
                        'name': parts[1],
                        'cpu_percent': 0,
                        'memory_percent': 0,
                        'status': 'running'
                    })
                except ValueError:
                    continue
        return processes
    
    def test_connection(self):
        try:
            client = self._connect(timeout=8)
            client.close()
            return True, 'Connection successful'
        except paramiko.ssh_exception.AuthenticationException:
            return False, 'Authentication failed'
        except Exception as e:
            return False, str(e)
