#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.anti_scan import is_sensitive_path, sanitize_error
from core.security import SecurityManager

def test_anti_scan():
    assert is_sensitive_path("/.env")
    assert is_sensitive_path("/data/users.json")
    assert not is_sensitive_path("/api/v1/stats")
    assert "failed" in sanitize_error("error in /secret/path")

def test_security_manager():
    sm = SecurityManager()
    assert sm is not None
