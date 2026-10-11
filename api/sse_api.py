"""api/sse_api.py — Server-Sent Events streams"""
import json
import time
from typing import Generator, Any, Callable

STREAMS = ["/sse/stats", "/sse/bots", "/sse/attacks", "/sse/proxies", "/sse/logs", "/sse/notifications"]

def sse_format(data: Any, event: str = None) -> str:
    payload = json.dumps(data, default=str, ensure_ascii=False)
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {payload}")
    lines.append("")
    return "\n".join(lines) + "\n"

def stream_stats(get_stats: Callable, interval: float = 2.0) -> Generator[str, None, None]:
    while True:
        try:
            yield sse_format(get_stats(), event="stats")
        except Exception as e:
            yield sse_format({"error": str(e)}, event="error")
        time.sleep(interval)
