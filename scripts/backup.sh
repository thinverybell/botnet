#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$ROOT/data/backup"
tar -czf "$ROOT/data/backup/backup_$STAMP.tar.gz" -C "$ROOT" data/*.json 2>/dev/null || true
echo "[+] $ROOT/data/backup/backup_$STAMP.tar.gz"
