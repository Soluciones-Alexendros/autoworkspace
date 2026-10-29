# Implementation Plan: Execution registry + mínimo privilegio (7.0.0-alpha.1)

## Overview

Hardening del corte `7.0.0-alpha.0`: quitar `skills/*/execution.yaml` (extensión no estándar para Cursor/Pi), centralizar ops en `tools/execution/registry.yaml` con schema, y bajar `allowed-tools` al mínimo por `metadata.type`. Canon de este incremento: este directorio. No se escribe `tasks/plan.md` ni `tasks/todo.md`.

## Architecture decisions

- **Registry SSOT:** un YAML bajo `tools/execution/registry.yaml` con schema JSON. Cada entrada tiene `tool_id`, `skill`, `entrypoint`, `description`, `operations[]`. Las skills audit no aparecen.
- **Enlace:** `metadata.execution: <tool_id>` opcional en las 11 skills no-audit. Las 6 claves top-level del frontmatter no cambian.
- **Ops count:** 32 → **25** (se descartan 7 ops de las 5 audit). Actualizar `EXPECTED_OPERATIONS` y la matriz congelada en `tasks/plan-product-closure-final.md` si el test la cita.
- **`registry.py` hoy:** dict Python hardcodeado (`OPERATIONS`) con un subconjunto de ops runtime (`create_snapshot`, `proton_send`, …). Tras el cambio: el YAML es la fuente declarativa completa; el dict runtime de handlers/`OpSpec` se deriva o se cruza con el YAML (ids desconocidos en callers siguen fallando; ops solo-declarativas de agent/orchestrator no exigen handler Python).
- **Contracts:** `tools/contracts/validate_contracts.py` deja de escanear `skills/*/execution.yaml` y de exigir pilots ahí. Valida el registry central (o delega en `python -m tools.execution.registry --check`). `REQUIRED_PILOTS` con `web-compliance` se retira o se redefine como presencia en catálogo skill, no execution file.
- **Min-priv gate:** `ALLOWED_TOOLS_BY_TYPE` en `skill_spec.py`. `Bash` en `atomic`/`orchestrator` exige justificación detectable (frase en `description` o marca documentada en template); para este incremento, las 11 no-audit ya justifican Bash en la tabla del SPEC — el gate mínimo FAIL es exceder el set máximo del tipo; audit nunca Write/Bash.
- **Sin `execution.yaml` bajo skills/:** `skill_spec` y un find en validation fallan si aparece cualquiera.
- **Versión:** `7.0.0-alpha.1` / `7.0.0a1`; no minor `7.1.0`.

## Components

| Component                                      | Change                                |
| ---------------------------------------------- | ------------------------------------- |
| `tools/execution/registry.yaml`                | Nuevo; 11 tools, 25 ops               |
| `tools/execution/schemas/registry.schema.json` | Nuevo                                 |
| `tools/execution/registry.py`                  | Load YAML, `--check`, exponer ops     |
| `tools/execution/ops.py`                       | Sin cambio de semántica de aprobación |
| `tools/contracts/*`                            | Fuente = registry                     |
| `tools/validate/skill_spec.py`                 | Matriz + bans                         |
| `skills/*/SKILL.md`                            | version, type/allowed-tools/execution |
| `skills/*/execution.yaml`                      | Borrar las 16                         |
| Docs + ADR-0017 + template                     | Actualizar contrato                   |

## Task list

Detalle en `TASKS.md`.

### Phase 1: Canon + versión

- [ ] Task 0: canon escrito (SPEC, PLAN, TASKS)
- [ ] Task 1: bump `7.0.0-alpha.1` / `7.0.0a1` + CHANGELOG

### Phase 2: Registry

- [ ] Task 2: schema + `registry.yaml` (25 ops) + `registry.py --check`
- [ ] Task 3: migrar consumers (contracts, closure tests, intent-map si aplica)
- [ ] Task 4: borrar `skills/*/execution.yaml`; añadir `metadata.execution` en 11 skills

### Checkpoint: registry

- [ ] `find skills/ -name execution.yaml | wc -l` == 0
- [ ] `uv run --project tools python -m tools.execution.registry --check`

### Phase 3: Min-priv

- [ ] Task 5: matriz en `skill_spec.py` + reclasificar 5 audit + bajar allowed-tools
- [ ] Task 6: template + tests de skill_spec

### Phase 4: Docs + cierre

- [ ] Task 7: ADR-0017 + ARCHITECTURE + AGENTS + harness-setup + README
- [ ] Task 8: índice, installs, `run-validation.sh` + `make validate/test/smoke`

### Checkpoint: complete

- [ ] Criterios de hecho del SPEC en verde

## Risks and mitigations

| Risk                                                      | Impact | Mitigation                                                                                              |
| --------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------- |
| Tests de closure siguen leyendo `skills/*/execution.yaml` | High   | Actualizar en Task 3 antes de borrar archivos                                                           |
| `REQUIRED_PILOTS` exige `web-compliance` execution        | High   | Quitar pilot file-based; audit sin registry                                                             |
| `OPERATIONS` hardcodeado diverge del YAML                 | Med    | `--check` exige que todo `operation_id` runtime esté en registry; documentar ops solo-declarativas      |
| `allowed-tools` Bash sin justificación rompe gate         | Med    | SPEC ya lista justificación; description de orchestrators/atomics con Bash menciona mutación/validación |
| Contar mal las 25 ops                                     | Med    | Lista fija en Task 2; test `EXPECTED_OPERATIONS = 25`                                                   |

## Verification checkpoints

1. Tras Task 2–4: registry check + cero execution.yaml bajo skills/
2. Tras Task 5–6: ningún audit con Write/Bash; skill_spec OK
3. Tras Task 8: validation completa + 16 symlinks en installs de prueba
