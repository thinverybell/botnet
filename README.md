# RyzenC2 PROMAX v8.0
File-based JSON C2 panel. Kali ready.
## Start
./scripts/install.sh
source venv/bin/activate
python3 app.py
Login: admin / ryzenc2_secure_2026

## Full setup (Kali, root)

```bash
sudo bash scripts/setup.sh
# installs to /opt/ryzenc2, venv, nginx, systemd unit, ufw 8080, cloudflared, redis cache
cd /opt/ryzenc2 && source venv/bin/activate && python3 app.py
```

## Web UI
Sau khi bật API (menu 11), mở frontend:
```bash
cd frontend && python3 -m http.server 3000
# browser http://127.0.0.1:3000
```

