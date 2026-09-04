"""Support for other operating systems can be added here in the future.

Example:
- Linux:    from .linux_monitor import LinuxMonitor
- Windows:  from .windows_monitor import WindowsMonitor
"""

from .base_monitor import BaseMonitor
from .macos_monitor import MacOSMonitor
import platform


def get_monitor():
    system = platform.system()
    
    if system == 'Darwin':
        return MacOSMonitor()
    elif system == 'Linux':
        # return LinuxMonitor()
        return MacOSMonitor()
    elif system == 'Windows':
        # return WindowsMonitor()
        return MacOSMonitor()
    else:
        return MacOSMonitor()
