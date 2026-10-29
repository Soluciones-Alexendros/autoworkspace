# Tasks: Execution registry + mínimo privilegio (7.0.0-alpha.1)

Roles se reevalúan al empezar cada tarea. No hay superficie UI: no entran `role-front` ni `role-design`.

## Task 0: Canon escrito

**Description:** Dejar SPEC.md, PLAN.md y TASKS.md en este directorio. No crear `tasks/plan.md` ni `tasks/todo.md`.

**Acceptance criteria:**

- [ ] Los tres archivos existen y citan mapa de capacidades, 25 ops y versión `7.0.0-alpha.1`
- [ ] Roles `role-back` / `role-clean-code` y superficies registry / skill_spec / execution quedan escritos

**Verification:**

- [ ] Los tres paths están en disco

**Dependencies:** None

**Implementation roles:** ninguno de producto

**Test surfaces:** ninguna

**Files likely touched:**

- `docs/plans/2026-10-29-execution-registry-min-priv/SPEC.md`
- `docs/plans/2026-10-29-execution-registry-min-priv/PLAN.md`
- `docs/plans/2026-10-29-execution-registry-min-priv/TASKS.md`

**Estimated scope:** XS

## Task 1: Bump 7.0.0-alpha.1

**Description:** Alinear manifiestos y CHANGELOG. `package.json` (+ lock si aplica) → `7.0.0-alpha.1`; `tools/pyproject.toml` + `tools/uv.lock` → `7.0.0a1`; sección CHANGELOG Fixed.

**Acceptance criteria:**

- [ ] `release_coherence` acepta la pareja alpha.1 / a1
- [ ] CHANGELOG tiene `## [7.0.0-alpha.1] - 2026-10-29`

**Verification:**

- [ ] `uv run --project tools pytest tools/validate/tests/test_release_coherence.py`

**Dependencies:** Task 0

**Implementation roles:** role-back

**Test surfaces:** `release_coherence`

**Files likely touched:**

- `package.json`, `package-lock.json` (si existe)
- `tools/pyproject.toml`, `tools/uv.lock`
- `CHANGELOG.md`
- `README.md` (versión declarada)

**Estimated scope:** S

## Task 2: Registry schema + YAML + --check

**Description:** Crear schema JSON y `registry.yaml` con 11 tools / 25 ops migradas desde execution.yaml no-audit. `registry.py` carga el YAML, valida schema, expone ops y soporta `--check`.

**Acceptance criteria:**

- [ ] `uv run --project tools python -m tools.execution.registry --check` exit 0
- [ ] Exactamente 25 operations y 11 tool_id
- [ ] Ops runtime existentes (`create_snapshot`, `proton_send`, `local_gates`, …) siguen resolubles

**Verification:**

- [ ] Comando `--check`
- [ ] pytest de execution que use get_operation / known_operation_ids

**Dependencies:** Task 1

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `tools/execution/registry.py`, schema

**Files likely touched:**

- `tools/execution/registry.yaml`
- `tools/execution/schemas/registry.schema.json`
- `tools/execution/registry.py`

**Estimated scope:** M

## Task 3: Consumers → registry

**Description:** Actualizar contracts loader/validate, `test_product_closure_catalog.py` (`EXPECTED_OPERATIONS=25`), `test_verifiable_closure.py`, y cualquier referencia a `skills/*/execution.yaml`. `run-validation.sh` valida el registry. Ajustar `intent-map` solo si apunta a execution files.

**Acceptance criteria:**

- [ ] Ningún test requiere `skills/*/execution.yaml`
- [ ] `validate_contracts` / paso de validation no falla por audits sin execution file

**Verification:**

- [ ] `uv run --project tools pytest tools/execution/tests tools/contracts/tests`

**Dependencies:** Task 2

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** contracts, product_closure_catalog, verifiable_closure, run-validation

**Files likely touched:**

- `tools/contracts/loader.py`, `validate_contracts.py`
- `tools/execution/tests/test_product_closure_catalog.py`
- `tools/execution/tests/test_verifiable_closure.py`
- `run-validation.sh`
- `tools/skill-router/intent-map.yaml` (si aplica)

**Estimated scope:** M

## Task 4: Borrar execution.yaml + metadata.execution

**Description:** Borrar los 16 `skills/*/execution.yaml`. En las 11 no-audit añadir `metadata.execution: <tool_id>` (igual al skill name). Subir `metadata.version` a `7.0.0-alpha.1` en las 16 (puede ir aquí o en Task 5 junto con type/allowed-tools).

**Acceptance criteria:**

- [ ] `find skills/ -name execution.yaml | wc -l` == 0
- [ ] 11 skills con `metadata.execution`; 5 audit sin esa clave

**Verification:**

- [ ] find + grep metadata.execution

**Dependencies:** Task 3

**Implementation roles:** role-clean-code

**Test surfaces:** skill_spec (tras Task 5)

**Files likely touched:**

- `skills/*/execution.yaml` (delete)
- `skills/*/SKILL.md`

**Estimated scope:** S

## Task 5: Min-priv matrix + reclasificar audits

**Description:** En `skill_spec.py` definir máximos por tipo; FAIL si se exceden; FAIL si audit tiene Write/Bash; FAIL si existe execution.yaml bajo skills/; validar `metadata.execution` contra registry. Reclasificar las 5 audit y bajar allowed-tools según tabla del SPEC. Justificar Bash en description de orchestrators/atomics que lo conservan (frase breve si falta).

**Acceptance criteria:**

- [ ] Ningún audit con Write/Bash
- [ ] skill_spec OK sobre las 16
- [ ] Fixture de exceso de permisos falla en tests

**Verification:**

- [ ] `uv run --project tools python tools/validate/skill_spec.py`
- [ ] pytest de skill_spec / validate

**Dependencies:** Task 4

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `skill_spec`

**Files likely touched:**

- `tools/validate/skill_spec.py`
- `tools/validate/tests/` (si hay)
- `skills/*/SKILL.md`

**Estimated scope:** M

## Task 6: Template SKILL

**Description:** Actualizar `templates/SKILL_TEMPLATE.md` con la matriz allowed-tools por tipo y nota de `metadata.execution`.

**Acceptance criteria:**

- [ ] Template documenta audit/atomic/orchestrator/router y el enlace execution

**Verification:**

- [ ] Lectura del template

**Dependencies:** Task 5

**Implementation roles:** role-clean-code

**Test surfaces:** ninguna automatizada

**Files likely touched:**

- `templates/SKILL_TEMPLATE.md`

**Estimated scope:** XS

## Task 7: Docs + ADR-0017

**Description:** ADR-0017 Accepted; actualizar ARCHITECTURE.md, AGENTS.md, docs/harness-setup.md, README (nomenclatura/frontmatter), índice ADR, menciones a execution.yaml local.

**Acceptance criteria:**

- [ ] ADR-0017 en `docs/architecture/decisions/`
- [ ] Docs ya no prometen `execution.yaml` por skill como extensión local estándar

**Verification:**

- [ ] grep de promesas obsoletas en docs tocados

**Dependencies:** Task 6

**Implementation roles:** role-clean-code

**Test surfaces:** ninguna

**Files likely touched:**

- `docs/architecture/decisions/ADR-0017-centralizacion-execution-min-priv.md`
- `docs/architecture/decisions/README.md`
- `ARCHITECTURE.md`, `AGENTS.md`, `docs/harness-setup.md`, `README.md`
- `skills/plan-continue/references/adrs-indice.md` (si lista ADRs)

**Estimated scope:** S

## Task 8: Cierre validación

**Description:** Regenerar skill-index; asegurar README/TAXONOMY; installs en `/tmp/test-cursor` y `/tmp/test-pi`; `run-validation.sh` + make targets verdes.

**Acceptance criteria:**

- [ ] Criterios de hecho del SPEC
- [ ] 16 symlinks en ambos installs de prueba

**Verification:**

- [ ] `bash run-validation.sh`
- [ ] `make validate && make test && make smoke`
- [ ] `python3 tools/skill-index/generate.py`
- [ ] installs `--target /tmp/...`

**Dependencies:** Task 7

**Implementation roles:** role-back

**Test surfaces:** validation completa, install scripts

**Files likely touched:**

- generados locales (no commitear skill-index.json)
- posiblemente README/TAXONOMY marcadores

**Estimated scope:** M
