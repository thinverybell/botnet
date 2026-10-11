"""
config.py - Central configuration (reads .env)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

def _bool(v, default=False):
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "on")

def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

# Panel
PANEL_NAME = "RyzenC2 PROMAX"
PANEL_VERSION = "8.0 ULTIMATE"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = _int(os.getenv("PORT"), 8080)
API_PORT = _int(os.getenv("API_PORT"), 8080)
API_KEY = os.getenv("API_KEY", "ryzenc2_api_key_change_me")

# Auth
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "ryzenc2_secure_2026")
SESSION_TIMEOUT = _int(os.getenv("SESSION_TIMEOUT"), 86400)
LOGIN_MAX_ATTEMPTS = _int(os.getenv("LOGIN_MAX_ATTEMPTS"), 5)
LOCKOUT_DURATION = _int(os.getenv("LOCKOUT_DURATION"), 900)
MFA_ENABLED = _bool(os.getenv("MFA_ENABLED"), False)

# Storage
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file")
DATA_DIR = str(BASE_DIR / os.getenv("DATA_DIR", "data"))
LOG_DIR = str(BASE_DIR / os.getenv("LOG_DIR", "logs"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Bot / Attack
MAX_BOTS = _int(os.getenv("MAX_BOTS"), 14000)
BOT_TIMEOUT = _int(os.getenv("BOT_TIMEOUT"), 120)
MAX_CONCURRENT_ATTACKS = _int(os.getenv("MAX_CONCURRENT_ATTACKS"), 50)
DEFAULT_DURATION = 60
DEFAULT_THREADS = 100

# Proxy / OPSEC
PROXY_ROTATION = _bool(os.getenv("PROXY_ROTATION"), True)
STEALTH_MODE = _bool(os.getenv("STEALTH_MODE"), True)
DEBUG_MODE = _bool(os.getenv("DEBUG_MODE"), False)

# Redis (cache only)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = _int(os.getenv("REDIS_PORT"), 6379)
REDIS_TTL = _int(os.getenv("REDIS_TTL"), 3600)

# UI
UI_LANGUAGE = "vi"
UI_THEME = "dark"
UI_PAGE_SIZE = 50
