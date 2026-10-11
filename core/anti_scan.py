"""core/anti_scan.py — light hardening helpers"""
SENSITIVE = {".env", ".git", "CREDENTIALS.txt", "__pycache__", "data/", "logs/"}

def is_sensitive_path(path: str) -> bool:
    p = path.lower()
    return any(s in p for s in SENSITIVE)

def sanitize_error(msg: str) -> str:
    # avoid leaking paths
    return "request failed" if ("/" in msg or "\\" in msg) else msg
