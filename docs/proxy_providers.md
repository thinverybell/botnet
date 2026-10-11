# Proxy providers nâng cao (E06–E08, MaxMind)

## Bright Data
```bash
export BRIGHTDATA_CUSTOMER=...
export BRIGHTDATA_PASSWORD=...
export BRIGHTDATA_ZONE=residential
# API
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"countries":["us","de"],"sessions":2}' \
  http://127.0.0.1:8080/api/v1/proxies/load-paid
```

## Oxylabs
```bash
export OXYLABS_USERNAME=...
export OXYLABS_PASSWORD=...
# same endpoint /proxies/load-paid
```

## Tor
```bash
# Kali: sudo apt install tor && sudo systemctl start tor
# SOCKS 127.0.0.1:9050
curl -X POST -H "X-API-Key: $KEY" -d '{}' \
  http://127.0.0.1:8080/api/v1/proxies/load-tor
```

## I2P
Chạy I2P router; mặc định SOCKS `127.0.0.1:4447` (đổi bằng `I2P_SOCKS_PORT`).

## MaxMind geo
1. Đăng ký MaxMind license, tải GeoLite2-Country.mmdb  
2. Đặt vào `data/GeoLite2-Country.mmdb` hoặc `MAXMIND_DB_PATH`  
3. `pip install maxminddb`  
4. `POST /api/v1/proxies/geo-enrich`

## Status
`GET /api/v1/proxies/providers/status`
