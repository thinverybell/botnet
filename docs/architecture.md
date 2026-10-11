# Kiến trúc RyzenC2 PROMAX v8.0

## 9 tầng
1. Target Layer — mục tiêu được ủy quyền
2. Bot Layer — agent đa nền tảng
3. Proxy Layer — HTTP/SOCKS4/5, rotate, score
4. Storage Layer — JSON file-based atomic
5. Core Layer — auth, bot, attack, proxy, AI, analytics
6. Application Layer — CLI + HTTP API + static UI
7. Edge Layer — Nginx, optional Cloudflare Tunnel
8. API Gateway — rate limit, API key, routes
9. Operator Layer — Web UI, CLI, scripts

## File-based storage
- data/*.json — không SQL
- Atomic write + backup + lock
- Cache L1 memory / L2 file

## Proxy (MHDDoS-style)
- config.json proxy-providers (85+)
- Parallel scrape, check, rotate, pool.txt
