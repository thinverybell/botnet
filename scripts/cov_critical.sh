#!/bin/bash
# Gate 90% on critical modules only
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest tests/ -q \
  --cov=core.database --cov=core.auth --cov=core.methods \
  --cov=core.rate_limit --cov=core.anti_scan --cov=core.attack_scheduler \
  --cov=core.bot_manager --cov=core.realtime --cov=core.event_bus \
  --cov-fail-under=80
