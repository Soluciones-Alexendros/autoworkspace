# Implementation Plan: Corte estable 7.0.0

## Overview

Promover autoworkspace de `7.0.0-alpha.1` a `7.0.0`, congelar las 16 skills en un snapshot versionado y documentar el repo como template de GitHub. Canon de este incremento: este directorio. No se escribe `tasks/plan.md` ni `tasks/todo.md`.

BUILD, cuando el operador dé el OK sobre este paquete: bump a `7.0.0`, snapshot, `release.yml` corta `v7.0.0` estable y el Release, y el último paso es `gh api` PATCH `is_template=true` con sí explícito en ese turno. Este plan no ejecuta ese BUILD.

## Architecture decisions

- **Versión única estable.** npm, locks, 16 `metadata.version`, `INDEX_VERSION` y la línea `Versión **7.0.0**` del README coinciden. Python pasa de `7.0.0a1` a `7.0.0`. `uv lock --project tools` regenera `tools/uv.lock`.
- **Prerelease sigue siendo válido en parsers.** `canonical_version` en `release_coherence.py` y `SEMVER_RE` en `skill_spec.py` aceptan `X.Y.Z` y `X.Y.Z-prerelease`. `--release-gate` deja de dar OK a una sección alpha: falla si el manifiesto es prerelease o si falta `## [7.0.0]`.
- **Tag solo por el workflow.** `cut_tag.py` ya rechaza prerelease y, con manifiesto estable, propone `v7.0.0` (`STABLE_TAG_RE` ignora `v7.0.0-alpha.*`). BUILD añade el test. El tag real lo crea `release.yml` (`cut_tag.py --apply` y `gh release create` sin `--prerelease`). Localmente solo `--dry-run`.
- **Snapshot commiteado, índice de trabajo gitignored.** `generate.py --json` escribe el índice canónico a stdout y no pisa `skill-index.json`. El gate de `catalog-freeze`, sin ambigüedad, es:

```bash
python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json
```

`run-validation.sh` ejecuta ese diff y sale distinto de 0 si falla. `write_index` mantiene la doble generación. README y TAXONOMY salen de `--sync-docs`, no de edición manual del bloque entre marcadores.

- **Limpieza acotada.** Cero `7.0.0-alpha` fuera de `CHANGELOG.md`, `docs/plans/` y `docs/architecture/decisions/`. Esos tres sitios conservan el archivo histórico, ADR-0017 incluido.
- **Dos caminos de alta.** `is_template` clona `Soluciones-Alexendros/autoworkspace` entero. `make new-product` copia `templates/product/`. `make new-harness` sigue volcando `templates/harness/` en `DEST/.autoworkspace/`. El README de la plantilla dice los dos. No hay `.github/workflows/template-sync.yml`.
- **`is_template` es terminal.** Último paso de la Task 6. Sí explícito en el turno. GitHub no lo deshace sin API (`PATCH` con `is_template=false`).
- **Registry cerrado.** `tools/execution/registry.yaml` y `allowed-tools` no entran en el diff. Superficie de no-cambio, comprobada por ausencia en el diff de esas rutas.
- **Cierre del PR.** Squash auto-merge (`ADR-0012`, `AGENTS.md` de este repo). Commit, push, PR, tag, Release y PATCH solo en BUILD.

## Components

| Component                                       | Change                                         |
| ----------------------------------------------- | ---------------------------------------------- |
| `package.json`, `package-lock.json`             | `7.0.0-alpha.1` → `7.0.0`                      |
| `tools/pyproject.toml`, `tools/uv.lock`         | `7.0.0a1` → `7.0.0`                            |
| `skills/*/SKILL.md`                             | solo `metadata.version`                        |
| `tools/skill-index/generate.py`                 | `INDEX_VERSION`, `--json`                      |
| `docs/architecture/skill-index-7.0.0.json`      | snapshot nuevo                                 |
| `run-validation.sh`                             | diff del snapshot                              |
| `tools/validate/release_coherence.py`           | `--release-gate` exige estable                 |
| `tools/validate/skill_spec.py`                  | sin cambio de parser; test de `7.0.0`          |
| `tools/version/cut_tag.py`                      | sin relajar el rechazo alpha; test de `v7.0.0` |
| `CHANGELOG.md`, `README.md`, `docs/TAXONOMY.md` | sección estable y tabla generada               |
| `templates/product/`                            | gitkeeps, `.autoworkspace/`, wrapper, README   |
| `tools/execution/registry.yaml`                 | sin cambio                                     |
| `.github/workflows/template-sync.yml`           | no se crea                                     |
| `.github/workflows/release.yml`                 | sin cambio de flags                            |

## Task list

Detalle en `TASKS.md`.

### Phase 1: Parsers

- [ ] Task 1: `--release-gate` estable y tests de `7.0.0` / prerelease en `release_coherence`, `skill_spec` y `cut_tag`

### Phase 2: Bump y catálogo

- [ ] Task 2: bump de manifiestos, 16 skills, `INDEX_VERSION`, README y CHANGELOG
- [ ] Task 3: `--json`, snapshot y diff en `run-validation.sh`; `--sync-docs`

### Checkpoint: versión y catálogo

- [ ] `release_coherence.py --release-gate` verde con sección `[7.0.0]`
- [ ] `python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json` sale 0
- [ ] `jq -r .version docs/architecture/skill-index-7.0.0.json` es `7.0.0`

### Phase 3: Template y limpieza

- [ ] Task 4: esqueleto `templates/product/` y los dos caminos en el README
- [ ] Task 5: grep acotado, installs y conteos del catálogo

### Checkpoint: canon vivo

- [ ] grep acotado de `7.0.0-alpha` sale 0
- [ ] `make new-product` y `make new-harness` listan el `DEST`
- [ ] 16 symlinks en cada install de `/tmp`

### Phase 4: Publicación

- [ ] Task 6: validación, PR squash, `release.yml` → `v7.0.0` y Release estable; `is_template` el último, con sí explícito

### Checkpoint: publicado

- [ ] Tag `v7.0.0` y Release sin marca prerelease
- [ ] `is_template` solo después de ese Release y del sí del turno

## Risks and mitigations

| Risk                                                                 | Impact | Mitigation                                                                           |
| -------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------ |
| `uv lock --project tools` reescribe más que la versión               | Med    | Revisar el diff del lock; si mueve deps no pedidas, parar y no mezclarlo con el bump |
| El stdout `Index OK` se usa como snapshot                            | High   | El único gate es `--json \| diff -q`; `run-validation.sh` no compara el gitignored   |
| Editar una skill deja el snapshot mentiroso                          | Med    | El diff en CI falla; no se actualiza el JSON a mano                                  |
| `is_template` clona tools, skills y secrets de docs, no el esqueleto | High   | El README lo dice; el PATCH es el último paso y espera un sí. Deshacer es otro PATCH |
| Un `git tag` local y `release.yml` duplican `v7.0.0`                 | High   | Solo `--dry-run` en local; el tag lo crea el workflow en `main`                      |
| El grep global borra historia                                        | Med    | Excluir `CHANGELOG.md`, `docs/plans/` y `docs/architecture/decisions/`               |

## Verification checkpoints

1. Tras Task 1: un fixture prerelease parsea y `--release-gate` lo rechaza; `7.0.0` no entra en `_refuse_prerelease`.
2. Tras Task 2–3: versiones alineadas, diff del snapshot a 0, `run-validation.sh` verde.
3. Tras Task 4–5: plantilla listable, installs a 16, grep acotado a 0.
4. Tras Task 6: Release estable publicado. `is_template` queda pendiente del sí explícito de ese turno y no se adelanta.

## Open questions

Ninguna.
