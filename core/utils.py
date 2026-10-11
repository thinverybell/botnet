"""core/utils.py"""
import re, time, uuid, hashlib, secrets, socket
from datetime import datetime
from typing import Any, List, Dict, Callable, Optional

def generate_uuid() -> str: return str(uuid.uuid4())
def generate_token(n: int = 32) -> str: return secrets.token_hex(n // 2)
def hash_string(s: str) -> str: return hashlib.sha256(s.encode()).hexdigest()
def verify_hash(s: str, h: str) -> bool: return hash_string(s) == h

def format_bytes(n: int) -> str:
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def format_number(n: int) -> str: return f"{n:,}"
def format_duration(s: float) -> str:
    s = int(s)
    if s < 60: return f"{s}s"
    if s < 3600: return f"{s//60}m {s%60}s"
    return f"{s//3600}h {(s%3600)//60}m"

def format_datetime(ts: float = None) -> str:
    if ts is None: ts = time.time()
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def validate_ip(ip: str) -> bool:
    try: socket.inet_aton(ip); return True
    except OSError: return False

def validate_port(port: int) -> bool: return isinstance(port, int) and 1 <= port <= 65535
def validate_url(url: str) -> bool: return bool(re.match(r"^https?://", url, re.I))

def is_private_ip(ip: str) -> bool:
    try:
        p = list(map(int, ip.split(".")))
        return p[0]==10 or p[0]==127 or (p[0]==172 and 16<=p[1]<=31) or (p[0]==192 and p[1]==168)
    except Exception: return False

def chunk(lst: List, size: int) -> List[List]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def group_by(lst: List[Dict], key: str) -> Dict[Any, List]:
    r: Dict[Any, List] = {}
    for item in lst: r.setdefault(item.get(key), []).append(item)
    return r

def filter_by(lst: List[Dict], key: str, value: Any) -> List[Dict]:
    return [x for x in lst if x.get(key) == value]

def find_by(lst: List[Dict], key: str, value: Any) -> Optional[Dict]:
    for x in lst:
        if x.get(key) == value: return x
    return None
