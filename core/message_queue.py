"""core/message_queue.py — in-process MQ (Kafka-ready interface)"""
import threading
import queue
import time
from typing import Dict, Any, Callable, List

class MessageQueue:
    def __init__(self):
        self._topics: Dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        self._subs: Dict[str, List[Callable]] = {}

    def _q(self, topic: str) -> queue.Queue:
        with self._lock:
            if topic not in self._topics:
                self._topics[topic] = queue.Queue(maxsize=10000)
            return self._topics[topic]

    def publish(self, topic: str, message: Dict[str, Any]):
        self._q(topic).put({"ts": time.time(), "payload": message})
        for cb in list(self._subs.get(topic, [])):
            try:
                cb(message)
            except Exception:
                pass

    def consume(self, topic: str, timeout: float = 1.0):
        try:
            return self._q(topic).get(timeout=timeout)
        except queue.Empty:
            return None

    def subscribe(self, topic: str, callback: Callable):
        with self._lock:
            self._subs.setdefault(topic, []).append(callback)

MQ = MessageQueue()
