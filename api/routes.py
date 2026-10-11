"""api/routes.py - Central route registration (stdlib HTTP or Flask-ready)"""
# Blueprint-style registration map for documentation / Flask integration
ROUTES = {
    "auth": [
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/register"),
        ("GET",  "/api/v1/auth/me"),
        ("POST", "/api/v1/auth/change-password"),
    ],
    "bots": [
        ("GET",    "/api/v1/bots"),
        ("GET",    "/api/v1/bots/<id>"),
        ("POST",   "/api/v1/bots"),
        ("DELETE", "/api/v1/bots/<id>"),
        ("GET",    "/api/v1/bots/stats"),
        ("POST",   "/api/v1/bots/simulate"),
    ],
    "attacks": [
        ("GET",  "/api/v1/attacks"),
        ("POST", "/api/v1/attacks"),
        ("POST", "/api/v1/attacks/<id>/start"),
        ("POST", "/api/v1/attacks/<id>/stop"),
        ("GET",  "/api/v1/attacks/running"),
        ("GET",  "/api/v1/attacks/stats"),
    ],
    "proxies": [
        ("GET",  "/api/v1/proxies"),
        ("POST", "/api/v1/proxies"),
        ("POST", "/api/v1/proxies/simulate"),
        ("GET",  "/api/v1/proxies/stats"),
        ("POST", "/api/v1/proxies/scrape"),
    ],
    "stats": [
        ("GET", "/api/v1/stats"),
        ("GET", "/api/v1/stats/overview"),
        ("GET", "/api/v1/health"),
    ],
    "ai": [
        ("POST", "/api/v1/ai/plan"),
        ("POST", "/api/v1/ai/analyze"),
        ("POST", "/api/v1/ai/bypass"),
        ("POST", "/api/v1/ai/chat"),
    ],
    "methods": [
        ("GET", "/api/v1/methods"),
        ("GET", "/api/v1/methods/l4"),
        ("GET", "/api/v1/methods/l7"),
    ],
}
