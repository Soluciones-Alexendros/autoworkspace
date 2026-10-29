# Tasks: Corte estable 7.0.0

Roles se reevalúan al empezar cada tarea. No hay superficie UI: no entran `role-front` ni `role-design`.

El paquete SPEC/PLAN/TASKS no es BUILD. Las tareas 1–6 se ejecutan solo después del OK del operador. BUILD es: bump a `7.0.0`, snapshot, `release.yml` → `v7.0.0` estable y Release, y al final el PATCH `is_template=true`.

## Task 1: Gate de versión estable

**Description:** Hacer que `--release-gate` exija un manifiesto estable y una sección CHANGELOG de esa versión. Los parsers siguen aceptando prerelease. `cut_tag.py` permite anunciar `v7.0.0` y sigue rechazando un alpha. No se relaja `_refuse_prerelease`. Registry y `allowed-tools` no se editan.

**Acceptance criteria:**

- [ ] Un fixture `7.0.0` pasa `release_coherence` (package, README, pyproject `7.0.0`, locks, sección CHANGELOG)
- [ ] Un fixture prerelease sigue parseando en `canonical_version` y en `skill_spec` `SEMVER_RE`
- [ ] `--release-gate` falla si el manifiesto es prerelease o si falta la sección estable
- [ ] `cut_tag` con paquete `7.0.0` y notas no llama a `_refuse_prerelease`; `7.0.0-alpha.1` sigue refused
- [ ] `tools/execution/registry.yaml` no está en el diff

**Verification:**

- [ ] `uv run --project tools pytest tools/validate/tests/test_release_coherence.py tools/validate/tests/test_skill_spec.py tools/version/tests/ -q`

**Dependencies:** None

**Implementation roles:** role-back

**Test surfaces:** `release_coherence`, `skill_spec`, `cut_tag.py`

**Files likely touched:**

- `tools/validate/release_coherence.py`
- `tools/validate/tests/test_release_coherence.py`
- `tools/validate/tests/test_skill_spec.py`
- `tools/version/tests/` (test de permiso del estable; `cut_tag.py` solo si el test demuestra un hueco)

**Estimated scope:** S

## Task 2: Bump 7.0.0

**Description:** Alinear manifiestos y la sección estable del CHANGELOG. `package.json` y `package-lock.json` (raíz y `packages[""].version`) → `7.0.0`. `tools/pyproject.toml` → `7.0.0` y `uv lock --project tools`. `metadata.version` de las 16 skills → `7.0.0`. `INDEX_VERSION` en `generate.py` → `7.0.0`. README: `Versión **7.0.0**`. CHANGELOG: `## [7.0.0] - 2026-10-29` con Fixed de promoción (registry y mínimo privilegio de alpha.1, catálogo congelado). Conservar `[7.0.0-alpha.1]` y `[7.0.0-alpha.0]`.

**Acceptance criteria:**

- [ ] package, lock npm, pyproject y uv.lock declaran `7.0.0` y `release_coherence` los trata como la misma versión
- [ ] Las 16 skills tienen `metadata.version: "7.0.0"` y ningún otro cambio de frontmatter
- [ ] CHANGELOG tiene la sección estable del 2026-10-29 y las dos secciones alpha siguen
- [ ] Si `uv lock` mueve dependencias no pedidas, se para y no se mezcla ese diff

**Verification:**

- [ ] `uv run --project tools pytest tools/validate/tests/test_release_coherence.py -q`
- [ ] `python3 tools/validate/release_coherence.py --root .`

**Dependencies:** Task 1

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `release_coherence`, `generate.py` (`INDEX_VERSION`)

**Files likely touched:**

- `package.json`
- `package-lock.json`
- `tools/pyproject.toml`
- `tools/uv.lock`
- `skills/*/SKILL.md` (solo la línea de versión)
- `tools/skill-index/generate.py` (`INDEX_VERSION`)
- `README.md` (línea de versión)
- `CHANGELOG.md`

**Estimated scope:** M

## Checkpoint: After Tasks 1–2

- [ ] Parsers verdes con `7.0.0` y con un prerelease de fixture
- [ ] `--release-gate` no acepta un manifiesto alpha
- [ ] Secciones alpha del CHANGELOG intactas

## Task 3: Congelar el catálogo

**Description:** Añadir `--json` a `generate.py` (stdout = índice canónico, sin escribir `skill-index.json`). Generar una vez `docs/architecture/skill-index-7.0.0.json` con `version` `7.0.0`. Meter en `run-validation.sh` el diff de abajo y fallar si no es 0. Reescribir README y TAXONOMY solo con `--sync-docs`.

El gate de `catalog-freeze` es exactamente:

```bash
python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json
```

**Acceptance criteria:**

- [ ] Ese comando sale 0
- [ ] `jq -r .version docs/architecture/skill-index-7.0.0.json` es `7.0.0`
- [ ] `skill-index.json` sigue en `.gitignore` y no entra en el commit
- [ ] El bloque entre `<!-- SKILL-INDEX:START -->` y `<!-- SKILL-INDEX:END -->` de README y TAXONOMY coincide con el generador
- [ ] Dos generaciones seguidas producen el mismo JSON

**Verification:**

- [ ] `python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json`
- [ ] `bash run-validation.sh`

**Dependencies:** Task 2

**Implementation roles:** role-back

**Test surfaces:** `generate.py`, `run-validation.sh`, marcadores de README y `docs/TAXONOMY.md`

**Files likely touched:**

- `tools/skill-index/generate.py`
- `docs/architecture/skill-index-7.0.0.json`
- `run-validation.sh`
- `README.md` (solo el bloque de marcadores)
- `docs/TAXONOMY.md` (solo el bloque de marcadores)
- tests del generador si ya cubren el índice

**Estimated scope:** M

## Checkpoint: After Tasks 2–3

- [ ] `bash run-validation.sh` verde
- [ ] `jq -r .version docs/architecture/skill-index-7.0.0.json` es `7.0.0`
- [ ] El diff `--json` sale 0

## Task 4: Template de producto

**Description:** Dejar `templates/product/` arrancable como esqueleto y documentar el template de GitHub. Añadir `.cursor/skills/.gitkeep`, `.pi/skills/.gitkeep`, `.autoworkspace/project.yaml` y `.autoworkspace/status.yaml` copiados de `templates/harness/`, y un `run-validation.sh` mínimo. El `validate` del Makefile de la plantilla invoca ese wrapper, para que la copia no llame a un `scripts/check-structure.sh` ausente. El README explica `Use this template`, `gh repo create --template Soluciones-Alexendros/autoworkspace` (clon del repo entero) y `make new-product` (solo el esqueleto), con inicio rápido hacia `templates/harness/`. No crear `template-sync.yml`. No llamar a la API de `is_template` en esta tarea.

**Acceptance criteria:**

- [ ] `make new-product DEST=/tmp/prod-test` crea el árbol y `ls` muestra `.cursor/skills`, `.pi/skills`, `.autoworkspace`, `Makefile` y `run-validation.sh`
- [ ] `make new-harness DEST=/tmp/harness-test` deja `project.yaml` y `status.yaml` en `DEST/.autoworkspace/`
- [ ] El README distingue el clon completo del esqueleto y apunta al harness
- [ ] No existe `.github/workflows/template-sync.yml` nuevo

**Verification:**

- [ ] `make new-product DEST=/tmp/prod-test && ls /tmp/prod-test`
- [ ] `make new-harness DEST=/tmp/harness-test && ls /tmp/harness-test/.autoworkspace`
- [ ] `bash /tmp/prod-test/run-validation.sh` sale 0 (stub del esqueleto, no la suite del canon)

**Dependencies:** None. Puede ir en paralelo con Task 3 después de Task 2 si el README de la plantilla no cita la versión alpha.

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `make new-product`, `make new-harness`, README de `templates/product/`

**Files likely touched:**

- `templates/product/.cursor/skills/.gitkeep`
- `templates/product/.pi/skills/.gitkeep`
- `templates/product/.autoworkspace/project.yaml`
- `templates/product/.autoworkspace/status.yaml`
- `templates/product/run-validation.sh`
- `templates/product/Makefile`
- `templates/product/README.md`

**Estimated scope:** M

## Task 5: Limpieza alpha e installs

**Description:** Confirmar que el canon vivo no dice `7.0.0-alpha`. No reescribir `CHANGELOG.md`, `docs/plans/` ni `docs/architecture/decisions/`. Comprobar installs y los conteos del catálogo. Si `ARCHITECTURE.md` o `docs/harness-setup.md` siguen sin la cadena, no se editan.

**Acceptance criteria:**

- [ ] El grep acotado sale 0
- [ ] Cada install deja 16 symlinks absolutos
- [ ] `ls skills | wc -l` es 16, `find skills -name execution.yaml | wc -l` es 0, y `grep -R "opencode\|codex\|copilot" skills/` no encuentra nada

**Verification:**

- [ ] `grep -R "7.0.0-alpha" --include="*.md" . | grep -v '/CHANGELOG.md' | grep -v '/docs/plans/' | grep -v '/docs/architecture/decisions/' | wc -l` → `0`
- [ ] `bash scripts/install-cursor.sh --target /tmp/test-cursor`
- [ ] `bash scripts/install-pi.sh --target /tmp/test-pi`
- [ ] `find /tmp/test-cursor /tmp/test-pi -type l | wc -l` es 32 y los destinos son absolutos

**Dependencies:** Task 2. Después de Task 3 si el `--sync-docs` reescribe README.

**Implementation roles:** role-clean-code

**Test surfaces:** installs, grep del canon vivo, conteo de `skills/`

**Files likely touched:**

- Solo markdown vivo que aún contenga `7.0.0-alpha` fuera de las tres exclusiones. Si Task 2 ya limpió README y las skills, esta tarea no edita archivos.

**Estimated scope:** S

## Checkpoint: After Tasks 4–5

- [ ] Plantilla y harness de prueba listados
- [ ] Grep acotado a 0
- [ ] 16 + 16 symlinks
- [ ] `make validate && make test && make smoke` aún no es el cierre de publicación; si se lanza aquí, un fallo para el BUILD

## Task 6: Publicar v7.0.0 y, al final, marcar template

**Description:** Cerrar BUILD con la suite local, el PR a `main` en squash auto-merge y la publicación que ya hace `release.yml`: `cut_tag.py --apply` crea `v7.0.0` y `gh release create` publica el Release sin `--prerelease`. Antes del push, `cut_tag.py --dry-run` solo anuncia el tag.

`is_template` es el último paso de esta tarea y de todo el BUILD. No se ejecuta junto con el merge ni con el Release. Cuando el tag y el Release estable ya existen, se muestra el PATCH y se espera un sí explícito en ese turno:

```bash
gh api --method PATCH /repos/Soluciones-Alexendros/autoworkspace -f is_template=true
```

GitHub no deja deshacerlo sin API. La vuelta atrás es otro PATCH con `is_template=false`, no un clic en la UI. Sin ese sí, la tarea termina con el Release publicado y el repo sin marcar como template.

**Acceptance criteria:**

- [ ] `bash run-validation.sh` y `make validate && make test && make smoke` verdes antes de sincronizar
- [ ] `cut_tag.py --dry-run` imprime `v7.0.0` y no crea el tag
- [ ] El PR entra por squash auto-merge; el tag lo crea `release.yml`, no un `git tag` del worktree
- [ ] El GitHub Release `v7.0.0` existe y no es prerelease; las notas salen de la sección `[7.0.0]`
- [ ] El PATCH `is_template=true` es el último comando y solo corre tras un sí explícito en el turno
- [ ] Si no hay sí, no se llama a la API

**Verification:**

- [ ] `bash run-validation.sh`
- [ ] `make validate && make test && make smoke`
- [ ] `python3 tools/version/cut_tag.py --dry-run`
- [ ] Tras el workflow: `gh release view v7.0.0 --json tagName,isPrerelease` con `isPrerelease` false
- [ ] El PATCH, si el operador dijo sí, se comprueba con `gh repo view Soluciones-Alexendros/autoworkspace --json isTemplate`

**Dependencies:** Tasks 3, 4 y 5

**Implementation roles:** role-back

**Test surfaces:** `run-validation.sh`, `make validate`, `make test`, `make smoke`, `cut_tag.py --dry-run`, `release.yml`, `gh release view`

**Files likely touched:**

- Ninguno de producto en el paso del PATCH. El PR de las tasks 1–5 ya está en `main` antes de este cierre.

**Estimated scope:** M
