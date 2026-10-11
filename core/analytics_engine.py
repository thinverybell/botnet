"""core/analytics_engine.py - Realtime analytics"""
import time
from typing import Dict, List, Optional
from collections import deque

class AnalyticsEngine:
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self._pps = deque(maxlen=max_points)
        self._bps = deque(maxlen=max_points)
        self._bot_online = deque(maxlen=max_points)
        self._events: List[Dict] = []

    def record_metrics(self, pps: int = 0, bps: int = 0, bots_online: int = 0):
        ts = time.time()
        self._pps.append({"ts": ts, "v": pps})
        self._bps.append({"ts": ts, "v": bps})
        self._bot_online.append({"ts": ts, "v": bots_online})

    def record_event(self, event_type: str, data: Optional[Dict] = None):
        self._events.append({"ts": time.time(), "type": event_type, "data": data or {}})
        if len(self._events) > 5000:
            self._events = self._events[-2500:]

    def get_timeseries(self, metric: str = "pps", last_n: int = 100) -> List[Dict]:
        src = {"pps": self._pps, "bps": self._bps, "bots": self._bot_online}.get(metric, self._pps)
        return list(src)[-last_n:]

    def get_summary(self) -> Dict:
        def _avg(dq):
            if not dq: return 0
            return sum(x["v"] for x in dq) / len(dq)
        return {
            "avg_pps": int(_avg(self._pps)),
            "avg_bps": int(_avg(self._bps)),
            "avg_bots": int(_avg(self._bot_online)),
            "points": len(self._pps),
            "events": len(self._events),
            "last_events": self._events[-10:],
        }

    def get_attack_stats(self, attacks: List[Dict]) -> Dict:
        by_method, by_layer, by_status = {}, {}, {}
        for a in attacks:
            m = a.get("method","?"); by_method[m] = by_method.get(m,0)+1
            l = a.get("layer","?"); by_layer[l] = by_layer.get(l,0)+1
            s = a.get("status","?"); by_status[s] = by_status.get(s,0)+1
        return {"by_method":by_method,"by_layer":by_layer,"by_status":by_status,"total":len(attacks)}
