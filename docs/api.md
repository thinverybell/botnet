# API Reference

Base: `http://HOST:8080`  
Header: `X-API-Key: ryzenc2_api_key_change_me`

## Health / Stats
- GET /api/v1/stats
- GET /api/v1/health

## Bots
- GET /api/v1/bots
- GET /api/v1/bots/stats
- POST /api/v1/bots/simulate

## Attacks
- GET /api/v1/attacks
- GET /api/v1/attacks/running
- POST /api/v1/attacks
- POST /api/v1/attacks/{id}/start
- POST /api/v1/attacks/{id}/stop

## Proxies
- GET /api/v1/proxies
- GET /api/v1/proxies/stats
- GET /api/v1/proxies/providers
- POST /api/v1/proxies/scrape
- POST /api/v1/proxies/check-all
- POST /api/v1/proxies/remove-dead
- POST /api/v1/proxies/simulate

## Methods
- GET /api/v1/methods
- GET /api/v1/methods/l4
- GET /api/v1/methods/l7

## AI
- POST /api/v1/ai/plan
- POST /api/v1/ai/analyze
- POST /api/v1/ai/bypass
- POST /api/v1/ai/chat

## Auth
- POST /api/v1/auth/login
