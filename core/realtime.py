"""core/realtime.py — in-process pub/sub for SSE / simple push"""
import threading
import queue
import time
from typing import Dict, Any, List

class RealtimeHub:
    def __init__(self):
        self._subs: Dict[str, List[queue.Queue]] = {}
        self._lock = threading.Lock()

    def subscribe(self, channel: str) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=100)
        with self._lock:
            self._subs.setdefault(channel, []).append(q)
        return q

    def unsubscribe(self, channel: str, q: queue.Queue):
        with self._lock:
            lst = self._subs.get(channel, [])
            if q in lst:
                lst.remove(q)

    def publish(self, channel: str, message: Dict[str, Any]):
        with self._lock:
            lst = list(self._subs.get(channel, []))
        dead = []
        for q in lst:
            try:
                q.put_nowait(message)
            except queue.Full:
                dead.append(q)
        for q in dead:
            self.unsubscribe(channel, q)

HUB = RealtimeHub()
