.PHONY: quality validate lint test smoke diagrams help new-product new-harness

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
	@echo "  make new-product DEST=dir — copy templates/product/"
	@echo "  make new-harness DEST=dir — copy harness yaml into DEST/.autoworkspace/"

quality:
	uv run --project tools python3 tools/validate/hygiene.py

validate:
	uv run --project tools bash run-validation.sh

lint: quality

test:
	uv run --project tools pytest tools/ \
		skills/local-maintenance/scripts/tests/ \
		skills/web-compliance/tests/ \
		skills/local-security/scripts/tests/ \
		tools/email/drivers/proton/ \
		-q

smoke:
	bash scripts/smoke.sh

diagrams:
	bash scripts/diagrams.sh

new-product:
	@test -n "$(DEST)" || (echo "DEST is required" && exit 2)
	mkdir -p "$(DEST)"
	cp -a templates/product/. "$(DEST)/"

new-harness:
	@test -n "$(DEST)" || (echo "DEST is required" && exit 2)
	mkdir -p "$(DEST)/.autoworkspace"
	cp -a templates/harness/project.yaml templates/harness/status.yaml "$(DEST)/.autoworkspace/"
