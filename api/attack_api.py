"""api/attack_api.py"""
ENDPOINTS = [
    "GET /api/v1/attacks", "POST /api/v1/attacks",
    "POST /api/v1/attacks/<id>/start", "POST /api/v1/attacks/<id>/stop",
    "GET /api/v1/attacks/running", "GET /api/v1/attacks/stats",
]
