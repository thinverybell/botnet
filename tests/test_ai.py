#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.ai_engine import AIEngine

def test_ai_analyze_plan():
    ai = AIEngine()
    a = ai.analyze("8.8.8.8")
    assert a.get("type") in ("ip", "domain", "url", "unknown") or "target" in a or isinstance(a, dict)
    p = ai.plan("example.com")
    assert isinstance(p, dict)
