# Fachada local = mismos nombres en toda la flota.
# En repos de producto, sustituye los stubs por los comandos del stack
# (ver stacks/typescript, stacks/rust, stacks/infra).

.PHONY: help lint test smoke validate

help:
	@echo "Targets canónicos:"
	@echo "  make validate  — integridad de estructura (este canon)"
	@echo "  make lint      — quality local (stub aquí; format/lint/types en producto)"
	@echo "  make test      — unit/function + coverage (stub aquí)"
	@echo "  make smoke     — comprobaciones baratas post-build"

lint:
	@echo "lint: este canon no tiene código de aplicación."
	@echo "En un repo TS: pnpm format:check && pnpm lint && pnpm typecheck"
	@echo "En un repo Rust: cargo fmt --check && cargo clippy -- -D warnings"
	@echo "En infra: make lint && make typecheck && actionlint"
	@true

test:
	@echo "test: placeholder del hook de producto."
	@echo "Engancha aquí unit/function tests y el gate de cobertura (≥70%; 80% en críticos)."
	@echo "FAIL deliberado para prueba ci-gate (revertir)"
	@false

smoke:
	@bash scripts/smoke.sh

validate:
	@bash scripts/check-structure.sh
