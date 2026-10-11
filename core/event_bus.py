"""core/event_bus.py — sync event bus"""
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()

    def on(self, event: str, handler: Callable):
        with self._lock:
            self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable):
        with self._lock:
            if handler in self._handlers[event]:
                self._handlers[event].remove(handler)

    def emit(self, event: str, payload: Any = None):
        with self._lock:
            handlers = list(self._handlers.get(event, []))
        for h in handlers:
            try:
                h(payload)
            except Exception:
                pass

BUS = EventBus()
