#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $EUID -eq 0 ]]; then
  echo "[*] Root detected — chạy full setup.sh"
  exec bash "$ROOT/scripts/setup.sh"
fi
echo "[*] User mode install (venv only)"
cd "$ROOT"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install colorama requests python-dotenv -q
chmod +x app.py scripts/*.sh bot/bot_client.py 2>/dev/null || true
mkdir -p data logs data/cache data/backup export import ssl
echo "[+] Done. source venv/bin/activate && python3 app.py"
echo "    Login: admin / ryzenc2_secure_2026"
echo "    Full Kali setup: sudo bash scripts/setup.sh"
