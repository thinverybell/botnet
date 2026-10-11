"""
Tor & I2P local SOCKS adapters.
Tor default: socks5://127.0.0.1:9050 (or 9150 Browser)
I2P default: socks://127.0.0.1:4447 (varies by install)
Only probes localhost — no external dependency required to import.
"""
import os
import socket
from typing import Dict, Optional, List


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


class TorProvider:
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("TOR_SOCKS_PORT", "9050"))
        self.alt_ports = [9050, 9150]

    def is_available(self) -> bool:
        if _port_open(self.host, self.port):
            return True
        for p in self.alt_ports:
            if p != self.port and _port_open(self.host, p):
                self.port = p
                return True
        return False

    def get_proxy(self) -> Optional[Dict]:
        if not self.is_available():
            return None
        return {
            "address": self.host,
            "port": self.port,
            "type": 5,
            "protocol": "socks5",
            "user": None,
            "password": None,
            "provider": "tor",
            "country": None,
            "alive": True,
            "score": 70,
        }

    def list_endpoints(self) -> List[Dict]:
        p = self.get_proxy()
        return [p] if p else []

    def status(self) -> Dict:
        avail = self.is_available()
        return {
            "provider": "tor",
            "available": avail,
            "host": self.host,
            "port": self.port,
            "hint": "Install tor / torbrowser; SOCKS 9050 or 9150",
        }


class I2PProvider:
    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("I2P_SOCKS_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("I2P_SOCKS_PORT", "4447"))

    def is_available(self) -> bool:
        return _port_open(self.host, self.port)

    def get_proxy(self) -> Optional[Dict]:
        if not self.is_available():
            return None
        return {
            "address": self.host,
            "port": self.port,
            "type": 5,
            "protocol": "socks5",
            "provider": "i2p",
            "alive": True,
            "score": 65,
        }

    def list_endpoints(self) -> List[Dict]:
        p = self.get_proxy()
        return [p] if p else []

    def status(self) -> Dict:
        return {
            "provider": "i2p",
            "available": self.is_available(),
            "host": self.host,
            "port": self.port,
            "hint": "Run I2P router; default SOCKS often 4447",
        }
