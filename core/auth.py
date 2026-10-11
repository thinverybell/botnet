"""core/auth.py — Auth RBAC + MFA TOTP + ABAC + sessions"""
import hashlib
import secrets
import time
import json
import base64
import struct
import hmac
from typing import Optional, Dict, Any, List

def _b32_encode(data: bytes) -> str:
    return base64.b32encode(data).decode("ascii").replace("=", "")

def _b32_decode(s: str) -> bytes:
    pad = "=" * ((8 - len(s) % 8) % 8)
    return base64.b32decode(s.upper() + pad)

def totp_at(secret_b32: str, for_time: float = None, step: int = 30, digits: int = 6) -> str:
    """RFC 6238 TOTP (stdlib only)."""
    if for_time is None:
        for_time = time.time()
    key = _b32_decode(secret_b32)
    counter = int(for_time // step)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[-1] & 0x0F
    code = (struct.unpack(">I", h[o:o+4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)

def verify_totp(secret_b32: str, code: str, window: int = 1) -> bool:
    now = time.time()
    code = str(code).strip()
    for w in range(-window, window + 1):
        if totp_at(secret_b32, now + w * 30) == code:
            return True
    return False


class AuthManager:
    def __init__(self, db, admin_user: str = "admin", admin_pass: str = "ryzenc2_secure_2026"):
        self.db = db
        self._admin_user = admin_user
        self._admin_pass = admin_pass
        self._sessions: Dict[str, Dict] = {}
        self._lockout: Dict[str, Dict] = {}
        self._ensure_admin()

    def _hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _ensure_admin(self):
        if not self.db.find_one("users", {"username": self._admin_user}):
            try:
                self.register(self._admin_user, self._admin_pass, role="admin")
            except ValueError:
                pass

    def register(self, username: str, password: str, role: str = "viewer", email: str = "") -> Dict:
        if self.db.find_one("users", {"username": username}):
            raise ValueError("user exists")
        if len(password) < 8:
            raise ValueError("password too short")
        rec = {
            "username": username,
            "password_hash": self._hash(password),
            "email": email,
            "role": role,
            "created_at": time.time(),
            "last_login": None,
            "mfa_enabled": False,
            "mfa_secret": None,
            "mfa_backup_codes": [],
            "failed_attempts": 0,
            "locked_until": None,
            "permissions": self._default_perms(role),
            "attributes": {"dept": "ops", "clearance": "standard"},  # ABAC
            "tenant_id": "default",
        }
        return self.db.insert("users", rec)

    def _default_perms(self, role: str) -> List[str]:
        if role == "admin":
            return ["*"]
        if role == "operator":
            return ["bots:read", "bots:write", "attacks:read", "attacks:write", "proxies:read", "proxies:write", "stats:read"]
        return ["bots:read", "attacks:read", "proxies:read", "stats:read"]

    def _check_lockout(self, username: str) -> bool:
        info = self._lockout.get(username)
        if not info:
            return False
        if time.time() < info.get("until", 0):
            return True
        self._lockout.pop(username, None)
        return False

    def login(self, username: str, password: str, totp_code: str = None) -> Optional[Dict]:
        if self._check_lockout(username):
            return None
        user = self.db.find_one("users", {"username": username})
        if not user or user.get("password_hash") != self._hash(password):
            lo = dict(self._lockout.get(username) or {"fails": 0, "until": 0})
            lo["fails"] = int(lo.get("fails") or 0) + 1
            if lo["fails"] >= 5:
                lo["until"] = time.time() + 900
            self._lockout[username] = lo
            return None
        # MFA
        if user.get("mfa_enabled") and user.get("mfa_secret"):
            ok = False
            if totp_code:
                if verify_totp(user["mfa_secret"], totp_code):
                    ok = True
                elif totp_code in (user.get("mfa_backup_codes") or []):
                    ok = True
                    codes = [c for c in user["mfa_backup_codes"] if c != totp_code]
                    self.db.update("users", user["id"], {"mfa_backup_codes": codes})
            if not ok:
                return {"mfa_required": True, "username": username}
        self._lockout.pop(username, None)
        sid = secrets.token_hex(24)
        session = {
            "session_id": sid,
            "username": username,
            "role": user.get("role", "viewer"),
            "permissions": user.get("permissions") or self._default_perms(user.get("role", "viewer")),
            "attributes": user.get("attributes") or {},
            "tenant_id": user.get("tenant_id", "default"),
            "created_at": time.time(),
            "expires_at": time.time() + 86400,
        }
        self._sessions[sid] = session
        self.db.update("users", user["id"], {"last_login": time.time(), "failed_attempts": 0})
        return session

    def logout(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def get_session(self, session_id: str) -> Optional[Dict]:
        s = self._sessions.get(session_id)
        if not s:
            return None
        if time.time() > s.get("expires_at", 0):
            self._sessions.pop(session_id, None)
            return None
        return s

    def has_permission(self, session: Dict, perm: str) -> bool:
        """RBAC check."""
        perms = session.get("permissions") or []
        if "*" in perms:
            return True
        if perm in perms:
            return True
        # prefix: attacks:write covers attacks:*
        resource = perm.split(":")[0] if ":" in perm else perm
        if f"{resource}:*" in perms:
            return True
        return False

    def check_abac(self, session: Dict, resource_attrs: Dict) -> bool:
        """Simple ABAC: session attributes must satisfy resource requirements."""
        attrs = session.get("attributes") or {}
        # example rules
        if resource_attrs.get("requires_clearance") == "high":
            if attrs.get("clearance") not in ("high", "top"):
                return False
        if resource_attrs.get("tenant_id"):
            if session.get("tenant_id") != resource_attrs["tenant_id"] and session.get("role") != "admin":
                return False
        return True

    def enable_mfa(self, username: str) -> Dict:
        user = self.db.find_one("users", {"username": username})
        if not user:
            raise ValueError("user not found")
        secret = _b32_encode(secrets.token_bytes(20))
        backup = [secrets.token_hex(4) for _ in range(8)]
        self.db.update("users", user["id"], {
            "mfa_secret": secret,
            "mfa_enabled": True,
            "mfa_backup_codes": backup,
        })
        return {
            "secret": secret,
            "otpauth_uri": f"otpauth://totp/RyzenC2:{username}?secret={secret}&issuer=RyzenC2",
            "backup_codes": backup,
        }

    def disable_mfa(self, username: str) -> bool:
        user = self.db.find_one("users", {"username": username})
        if not user:
            return False
        self.db.update("users", user["id"], {
            "mfa_enabled": False,
            "mfa_secret": None,
            "mfa_backup_codes": [],
        })
        return True

    def verify_mfa(self, username: str, code: str) -> bool:
        user = self.db.find_one("users", {"username": username})
        if not user or not user.get("mfa_secret"):
            return False
        return verify_totp(user["mfa_secret"], code)
