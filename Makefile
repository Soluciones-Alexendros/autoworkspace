.PHONY: quality validate lint test smoke help

# Carga .env local si existe (sin commitear; ver .env.example / docs/USAGE.md).
ifneq (,$(wildcard .env))
include .env
export
endif

help:
	@echo "Targets:"
	@echo "  make validate  — run-validation.sh (canonical gate)"
	@echo "  make quality   — hygiene.py"
	@echo "  make lint      — hygiene (quality local)"
	@echo "  make test      — pytest tools/ + skill script tests"
	@echo "  make smoke     — scripts/smoke.sh (canon contract)"

quality:
	uv run uv run python3 tools/validate/hygiene.py

validate:
	bash run-validation.sh

lint: quality

test:
	uv run pytest tools/ \
		skills/local-maintenance/scripts/tests/ \
		skills/web-compliance/tests/ \
		skills/local-security/scripts/tests/ \
		skills/local-proton/scripts/ \
		-q

smoke:
	bash scripts/smoke.sh
