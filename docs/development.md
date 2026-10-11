# Development (Phần C)

## Tests
```bash
pip install -r requirements.txt
make test
# or
python3 -m pytest tests/ -q
```

## Lint
```bash
make lint
```

## CI
GitHub Actions: `.github/workflows/ci.yml`

## Pre-commit
```bash
pip install pre-commit
pre-commit install
```

## Mypy
```bash
pip install mypy types-requests
make mypy
```

## Coverage gate (≥90%)
```bash
make cov-gate
```

## Load / chaos tests
Included in `tests/test_load_chaos.py` (run via `make test`).

## Coverage gates
- `make cov-gate` — toàn bộ `core/` ≥ **55%** (hiện ~68%)
- `make cov-critical` — module lõi (database/auth/methods/…) ≥ **80%** (hướng tới 90% khi bổ sung test)

## Mypy
```bash
make mypy
```
Config: `mypy.ini` (ignore_missing_imports, check_untyped_defs)

## Load/chaos
`tests/test_load_chaos.py` — concurrent simulate, cache thrash, MQ burst, rate limiter
