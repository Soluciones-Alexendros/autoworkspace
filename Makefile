.PHONY: quality validate lint test smoke help

help:
	@echo "Targets:"
	@echo "  make validate  — run-validation.sh (canonical gate)"
	@echo "  make quality   — hygiene.py"
	@echo "  make lint      — hygiene (quality local)"
	@echo "  make test      — pytest tools/ + skill script tests"
	@echo "  make smoke     — scripts/smoke.sh (canon contract)"

quality:
	python3 tools/validate/hygiene.py

validate:
	bash run-validation.sh

lint: quality

test:
	python3 -m pytest tools/ \
		skills/local-maintenance/scripts/tests/ \
		skills/web-compliance/tests/ \
		skills/local-security/scripts/tests/ \
		skills/local-proton/scripts/ \
		-q

smoke:
	bash scripts/smoke.sh
