.PHONY: quality validate lint test smoke diagrams help new-product new-harness validate-harnesses e2e-orchestration readiness

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
	@echo "  make validate-harnesses — Pi/Cursor native A/B/C (exit 3 = blocked/not_run)"
	@echo "  make e2e-orchestration — core + Pi/Cursor native orchestration"
	@echo "  make readiness — validate+test+smoke+typecheck+lint+native+e2e (blocks on exit 3)"
	@echo "  make new-product DEST=dir — copy templates/product/"
	@echo "  make new-harness DEST=dir — copy harness yaml into DEST/.machineroom/"

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

validate-harnesses:
	bash scripts/tests/test_pi_native.sh
	bash scripts/tests/test_cursor_native.sh

e2e-orchestration:
	bash scripts/tests/test_orchestration_core.sh
	@status=0; \
	bash scripts/tests/test_pi_orchestration.sh || status=$$?; \
	if [ $$status -ne 0 ] && [ $$status -ne 3 ]; then exit $$status; fi; \
	cstatus=0; \
	bash scripts/tests/test_cursor_orchestration.sh || cstatus=$$?; \
	if [ $$cstatus -ne 0 ] && [ $$cstatus -ne 3 ]; then exit $$cstatus; fi; \
	if [ $$status -eq 3 ] || [ $$cstatus -eq 3 ]; then \
	  echo "e2e-orchestration: core pass; native lanes not_run/blocked (need MR_NATIVE_OPT_IN=1)" >&2; \
	  exit 3; \
	fi

# Aggregate release readiness. Exit 3 from native/e2e lanes is a hard block here
# (unlike casual local runs): missing opt-in, auth, or capability C ≠ PASS.
readiness:
	$(MAKE) validate
	$(MAKE) test
	$(MAKE) smoke
	npm run typecheck
	npm run lint
	$(MAKE) validate-harnesses
	$(MAKE) e2e-orchestration

diagrams:
	bash scripts/diagrams.sh

new-product:
	@test -n "$(DEST)" || (echo "DEST is required" && exit 2)
	mkdir -p "$(DEST)"
	cp -a templates/product/. "$(DEST)/"

new-harness:
	@test -n "$(DEST)" || (echo "DEST is required" && exit 2)
	mkdir -p "$(DEST)/.machineroom"
	cp -a templates/harness/project.yaml templates/harness/status.yaml "$(DEST)/.machineroom/"
