"""proxy/proxy_scorer.py — scoring formula"""

def score(latency=999, bandwidth=0, reliability=0.5, anonymity=0.5, geo=0.5, uptime=0.5) -> float:
    """Higher is better. latency in ms."""
    lat_score = max(0.0, 25.0 * (1.0 / (1.0 + float(latency) / 100.0)))
    bw_score = min(20.0, float(bandwidth) / 1e6 * 20.0) if bandwidth else 5.0
    return round(
        lat_score
        + bw_score
        + float(reliability) * 20
        + float(anonymity) * 15
        + float(geo) * 10
        + float(uptime) * 10,
        1,
    )


def rank(proxies: list) -> list:
    def key(p):
        if isinstance(p, dict):
            return p.get("score", 0)
        return getattr(p, "score", 0)
    return sorted(proxies, key=key, reverse=True)
