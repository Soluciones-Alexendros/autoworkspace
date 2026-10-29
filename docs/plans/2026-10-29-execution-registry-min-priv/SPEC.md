# Spec: Execution registry + mínimo privilegio (7.0.0-alpha.1)

## Capability map

Un solo incremento. Criterios cruzan módulos; un SPEC, sin trackers paralelos.

| Module id          | Responsibility                                                                                                                                 | Depends on                          |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| version-alpha1     | Alinear `7.0.0-alpha.1` / `7.0.0a1` en package, pyproject, lock, 16 skills, índice, CHANGELOG                                                  | —                                   |
| execution-registry | `tools/execution/registry.yaml` + schema; migrar ops no-audit; borrar `skills/*/execution.yaml`; `metadata.execution`; loader/`run_registered` | version-alpha1                      |
| min-priv-matrix    | Matriz allowed-tools por `metadata.type` en `skill_spec.py`; reclasificar 5 audits; bajar permisos                                             | execution-registry                  |
| validation-gates   | Prohibir `execution.yaml` bajo skills/; validar registry; actualizar contracts/tests/closure                                                   | execution-registry, min-priv-matrix |
| docs-adr           | ARCHITECTURE, AGENTS, harness-setup, README, template, ADR-0017                                                                                | validation-gates                    |

Build order: version-alpha1 → execution-registry → min-priv-matrix → validation-gates → docs-adr.

## Objective

Centralizar la ejecución mutadora en un registry canónico bajo `tools/execution/` y aplicar mínimo privilegio en `allowed-tools` según `metadata.type`, de modo que Cursor/Pi solo vean `SKILL.md` estándar (`compatibility: cursor, pi`) sin extensión local `execution.yaml`.

## Assumptions

1. Versión objetivo: **`7.0.0-alpha.1`** (hardening del corte `alpha.0`, no minor nueva). `package.json` / locks npm → `7.0.0-alpha.1`; `tools/pyproject.toml` + `tools/uv.lock` → `7.0.0a1` (PEP 440); coherencia trata ambas como la misma versión.
2. Las 16 skills suben `metadata.version` a `7.0.0-alpha.1` por alineación de release, aunque solo un subconjunto cambie type/allowed-tools.
3. Enlace skill↔tool: **`metadata.execution: <tool_id>`** (opcional). Las 6 claves top-level no cambian. `skill_spec.py` permite `execution` en metadata (kebab-case, debe existir en registry si está presente).
4. Skills **audit** (sin registry, se borran sus `execution.yaml`): `web-compliance`, `web-owasp`, `web-performance`, `project-architecture`, `project-libraries` → `type: audit` + `allowed-tools: Read, Grep, Glob`.
5. SBOM/`write-workspace` de `project-libraries` deja de ser contrato de ejecución en este incremento; el audit es informe read-only (sin Write en allowed-tools). Un tool registrado futuro queda fuera de alcance.
6. Registry recibe el contenido migrado de los `execution.yaml` de las **11** skills no-audit (**25** operaciones). Las 5 audit no tienen entrada (se descartan **7** ops).
7. `run_registered` y aprobación siguen siendo el único camino mutador de producto; `allowed-tools` no autoriza en Cursor (sigue siendo contrato de catálogo + gate de `skill_spec`).
8. ADR siguiente: **ADR-0017** — Centralización de execution y mínimo privilegio por tipo.
9. Sin skills nuevas, sin migración de lenguaje, sin tag estable `v7.0.0`.
10. Roles de implementación: `role-back` + `role-clean-code` (superficies: registry, `skill_spec`, contracts, execution). Sin `role-front`/`role-design`.

## Tech stack

Python 3 del repo, uv, pytest, jsonschema (ya en tools), Ruff, Mypy. Sin dependencias nuevas salvo reutilizar jsonschema del stack de `tools/contracts`.

## Commands

```bash
uv run --project tools python -m tools.execution.registry --check
uv run bash run-validation.sh
make validate && make test && make smoke
python3 tools/skill-index/generate.py
bash scripts/install-cursor.sh --target /tmp/test-cursor
bash scripts/install-pi.sh --target /tmp/test-pi
find skills/ -name execution.yaml | wc -l   # == 0
```

## Project structure

- `tools/execution/registry.yaml` — SSOT de tools/ops (nuevo)
- `tools/execution/schemas/registry.schema.json` — schema JSON (nuevo)
- `tools/execution/registry.py` — carga YAML + `--check`; `OPERATIONS` derivado del registry
- `tools/execution/ops.py` — `run_registered` sin cambio de semántica de aprobación
- `tools/contracts/` — deja de exigir `skills/*/execution.yaml`; valida contra registry
- `tools/validate/skill_spec.py` — matriz min-priv + fail si `skills/**/execution.yaml` + validar `metadata.execution`
- `templates/SKILL_TEMPLATE.md` — matriz por tipo
- `docs/architecture/decisions/ADR-0017-*.md` — ADR nuevo
- Skills: solo `SKILL.md` (+ scripts/references existentes); **cero** `execution.yaml`

Forma canónica de entrada en `registry.yaml` (por `tool_id`):

```yaml
tools:
  - tool_id: local-maintenance # kebab-case
    skill: local-maintenance # skills/<nombre>
    entrypoint: tools/execution # o ruta concreta bajo tools/
    description: "..."
    operations: [...] # id, effect, approval_required, ...
```

## Matriz allowed-tools (normativa)

| `metadata.type` | Máximo permitido                | Notas                                                          |
| --------------- | ------------------------------- | -------------------------------------------------------------- |
| `audit`         | `Read, Grep, Glob`              | Nunca `Write` ni `Bash`                                        |
| `atomic`        | `Read, Write, Grep, Glob`       | `Bash` solo con justificación en description o en ADR/template |
| `orchestrator`  | `Read, Grep, Glob, Bash, Write` | Justificación obligatoria en description                       |
| `router`        | `Read, Glob`                    | Ninguna skill del catálogo 16 es `router` hoy; la regla queda  |

### Asignación concreta (16 skills)

| Skill                | type (tras)  | allowed-tools                 | `metadata.execution` | Bash justificado                           |
| -------------------- | ------------ | ----------------------------- | -------------------- | ------------------------------------------ |
| web-compliance       | audit        | Read, Grep, Glob              | —                    | —                                          |
| web-owasp            | audit        | Read, Grep, Glob              | —                    | —                                          |
| web-performance      | audit        | Read, Grep, Glob              | —                    | —                                          |
| project-architecture | audit        | Read, Grep, Glob              | —                    | —                                          |
| project-libraries    | audit        | Read, Grep, Glob              | —                    | —                                          |
| plan-specification   | orchestrator | Read, Grep, Glob, Bash, Write | sí                   | escribe SPEC/PLAN/TASKS + validación local |
| plan-continue        | orchestrator | Read, Grep, Glob, Bash, Write | sí                   | scaffold `.autoworkspace` + router         |
| plan-validators      | atomic       | Read, Write, Grep, Glob, Bash | sí                   | red/green de suites del proyecto           |
| local-email          | atomic       | Read, Write, Grep, Glob, Bash | sí                   | driver Proton / bridge                     |
| local-maintenance    | atomic       | Read, Write, Grep, Glob, Bash | sí                   | mutación host vía `run_registered`         |
| local-security       | atomic       | Read, Write, Grep, Glob, Bash | sí                   | hardening host vía `run_registered`        |
| project-publish      | atomic       | Read, Write, Grep, Glob, Bash | sí                   | gates, publish, git/gh                     |
| role-back            | atomic       | Read, Write, Grep, Glob, Bash | sí                   | implementa/muta código backend             |
| role-front           | atomic       | Read, Write, Grep, Glob, Bash | sí                   | implementa/muta UI                         |
| role-design          | atomic       | Read, Write, Grep, Glob, Bash | sí                   | muta tokens/CSS/superficies                |
| role-clean-code      | atomic       | Read, Write, Grep, Glob, Bash | sí                   | refactor mutador                           |

## Code style

- Contratos técnicos e ids en inglés; docs de operador del plan en español.
- No lógica de negocio nueva en skills: solo declaración (type, allowed-tools, metadata.execution) y borrado de `execution.yaml`.
- `tool_id` kebab-case; por defecto `tool_id == skill` salvo colisión documentada.

## Testing strategy

- Extender `skill_spec.py`: FAIL si type=audit y allowed-tools ⊇ Write\|Bash; FAIL si existe `skills/**/execution.yaml`; FAIL si allowed-tools excede el máximo del tipo; FAIL si `metadata.execution` no resuelve a `tool_id` del registry.
- `run-validation.sh`: validar `registry.yaml` con jsonschema; adaptar `tools/contracts/validate_contracts.py` (ya no exige pilots con `execution.yaml` bajo skills/).
- Actualizar `test_product_closure_catalog.py`, `test_verifiable_closure.py`, loader/tests de contracts: fuente = registry; **EXPECTED_OPERATIONS = 25**.
- `release_coherence.py` sigue aceptando prerelease.
- Installs `/tmp/test-cursor` y `/tmp/test-pi` → 16 symlinks.

## Boundaries

- Always: gate local verde antes de sincronizar; regenerar índice; no commitear `skill-index.json`.
- Ask first: cambiar el set de las 5 audit; añadir dependencia nueva; tocar semántica de aprobación.
- Never: skills nuevas; reescritura de lógica de negocio de skills; migrar lenguaje; tag estable; invocar `local-*` / `project-publish` mutadores en este incremento salvo tests dry/blocked.

## Success criteria

- `find skills/ -name execution.yaml | wc -l` == 0
- Existe `tools/execution/registry.yaml` y `uv run --project tools python -m tools.execution.registry --check` pasa
- Ningún `type: audit` con Write/Bash en `allowed-tools`
- `bash run-validation.sh` verde; `make validate && make test && make smoke` verde
- `python3 tools/skill-index/generate.py` índice determinista en `7.0.0-alpha.1`
- Installs de prueba: 16 symlinks
- Versiones: package `7.0.0-alpha.1`, pyproject `7.0.0a1`, CHANGELOG sección `[7.0.0-alpha.1] - 2026-10-29` con Fixed de registry + min-priv
- ADR-0017 Accepted en `docs/architecture/decisions/`
- Docs tocados: ARCHITECTURE.md, AGENTS.md, docs/harness-setup.md, README (nomenclatura/frontmatter), templates/SKILL_TEMPLATE.md

## Open questions

Ninguna. Versión y enlace metadata cerrados por el operador.
