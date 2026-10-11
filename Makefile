.PHONY: install run test test-cov lint mypy cov-gate cov-critical docker setup clean ci

install:
	./scripts/install.sh

setup:
	sudo bash scripts/setup.sh

run:
	python3 app.py

test:
	python3 -m pytest tests/ -q

test-cov:
	python3 -m pytest tests/ -q --cov=core --cov-config=.coveragerc --cov-report=term-missing

cov-gate:
	python3 -m pytest tests/ -q --cov=core --cov-config=.coveragerc --cov-fail-under=55

cov-critical:
	bash scripts/cov_critical.sh

lint:
	python3 -m py_compile app.py config.py
	python3 -m compileall -q core api bot proxy tests
	@echo "lint compile OK"

mypy:
	python3 -m mypy core api bot proxy app.py --config-file mypy.ini --no-error-summary 2>/dev/null || python3 -m mypy core/methods.py core/rate_limit.py core/anti_scan.py --config-file mypy.ini
	@echo "mypy done"

ci: lint test cov-gate

docker:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage .mypy_cache htmlcov
