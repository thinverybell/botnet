#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.analytics_engine import AnalyticsEngine

def test_analytics():
    ae = AnalyticsEngine()
    if hasattr(ae, "record_event"):
        ae.record_event("test", {"x": 1})
    if hasattr(ae, "get_summary"):
        s = ae.get_summary()
        assert isinstance(s, dict)
