# Tasks: Pivot 7.0.0-alpha.0 Cursor y Pi

Roles se reevalúan al empezar cada tarea. No hay superficie UI: no entran `role-front` ni `role-design`.

## Task 0: Canon escrito

**Description:** Dejar SPEC.md, PLAN.md y TASKS.md en este directorio. No crear `tasks/plan.md` ni `tasks/todo.md`.

**Acceptance criteria:**

- [ ] Los tres archivos existen y citan el mapa de capacidades
- [ ] El marcador `SKILL-INDEX` y la retirada de `.cursor/` quedan escritos

**Verification:**

- [ ] Los tres paths están en disco

**Dependencies:** None

**Implementation roles:** ninguno de producto

**Test surfaces:** ninguna

**Files likely touched:**

- `docs/plans/2026-10-29-eliminaciones-pivot-cursor-pi/SPEC.md`
- `docs/plans/2026-10-29-eliminaciones-pivot-cursor-pi/PLAN.md`
- `docs/plans/2026-10-29-eliminaciones-pivot-cursor-pi/TASKS.md`

**Estimated scope:** Medium

## Task 1: Semver de prerelease

**Description:** Ampliar el patrón `X.Y.Z` para aceptar `7.0.0-alpha.0`. El corte de tag rechaza publicar un alpha como estable. La versión del repo sigue en `6.1.0` al terminar.

**Acceptance criteria:**

- [ ] `6.1.0` sigue pasando los parsers
- [ ] Un fixture `7.0.0-alpha.0` pasa el parser de package, README y CHANGELOG
- [ ] `7.0.0a0` en pyproject equivale a `7.0.0-alpha.0` del manifiesto
- [ ] `cut_tag` no crea un tag estable desde un alpha

**Verification:**

- [ ] `uv run pytest tools/validate/tests/test_release_coherence.py tools/version/tests/test_bump.py`

**Dependencies:** Task 0

**Implementation roles:** role-back

**Test surfaces:** `release_coherence`, `skill_spec`, `bump.py --check`, `cut_tag.py --check-repo`

**Files likely touched:**

- `tools/validate/skill_spec.py`
- `tools/validate/release_coherence.py`
- `tools/version/bump.py`
- `tools/version/cut_tag.py`
- `tools/validate/tests/test_release_coherence.py`
- `tools/version/tests/test_bump.py`

**Estimated scope:** Medium

## Task 2: Frontmatter cursor, pi

**Description:** Sustituir `compatibility` y poner `metadata.version: "7.0.0-alpha.0"` en las 16 skills. En los cinco `references/*-source.md` que dicen `compatibility: opencode`, dejar `cursor, pi`. Regenerar el índice todavía commiteado. No cambiar procedimientos.

**Acceptance criteria:**

- [ ] El grep de `skills/` sobre md, json y yaml queda a cero
- [ ] `build_index.py --check` pasa

**Verification:**

- [ ] `python3 tools/skill-router/build_index.py --check`
- [ ] `uv run python3 tools/validate/skill_spec.py`

**Dependencies:** Task 1

**Implementation roles:** role-clean-code

**Test surfaces:** `tools/validate/skill_spec.py`

**Files likely touched:**

- `skills/*/SKILL.md`
- `skills/*/references/*-source.md`
- `skill-index.json`

**Estimated scope:** Medium

## Task 3: Instaladores Cursor y Pi

**Description:** Extraer journal, dry-run, conflictos y uninstall a una librería interna. `install-cursor.sh` enlaza `.cursor/skills` y, con `--user`, `$HOME/.cursor/skills`. `install-pi.sh` enlaza `.pi/skills` y, con `--user`, `$HOME/.pi/agent/skills`. `--target` no escribe en `$HOME`. Borrar `install.sh` e `install-opencode.sh`. Quitar el gate del binario OpenCode en el E2E.

**Acceptance criteria:**

- [ ] `--target /tmp/test-cursor` y `--target /tmp/test-pi` crean 16 symlinks absolutos
- [ ] `bash scripts/tests/test_install.sh` pasa
- [ ] El E2E no invoca el binario OpenCode

**Verification:**

- [ ] `bash scripts/tests/test_install.sh`
- [ ] `bash scripts/tests/test_install_journal_wa.sh`

**Dependencies:** Task 2

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** install dry-run, apply, uninstall, conflicto, journal; E2E sin binario OpenCode

**Files likely touched:**

- `scripts/lib/link-skills.sh`
- `scripts/install-cursor.sh`
- `scripts/install-pi.sh`
- `scripts/tests/test_install.sh`
- `scripts/tests/test_install_journal_wa.sh`
- `scripts/tests/test_execution_e2e.sh`

**Estimated scope:** Medium

## Task 4: Retirada de superficies y docs de harness

**Description:** Sacar del índice `.cursor/`, `.opencode/`, `.agents/` y `opencode.json` sin borrar estado local no versionado. Borrar la excepción `!.cursor/hooks.json`. Reescribir docs de harness a Cursor y Pi. Sustituir `docs/opencode-setup.md` por `docs/harness-setup.md`.

**Acceptance criteria:**

- [ ] `ls .opencode .agents` falla
- [ ] `git ls-files .cursor .opencode .agents opencode.json` no devuelve rutas
- [ ] `.gitignore` no contiene `!.cursor/hooks.json`

**Verification:**

- [ ] `git ls-files .cursor .opencode .agents opencode.json`
- [ ] `uv run bash run-validation.sh` con versión de repo aún `6.1.0`

**Dependencies:** Task 3

**Implementation roles:** role-clean-code; role-back en `migrate-frontmatter.py` y el router

**Test surfaces:** `run-validation.sh` pasos de índice e install; smoke de `route.py`

**Files likely touched:**

- `.gitignore`
- `AGENTS.md`
- `README.md`
- `docs/harness-integration.md`
- `docs/harness-setup.md`
- `docs/routing.md`
- `docs/USAGE.md`
- `Makefile`
- `run-validation.sh`

**Estimated scope:** Large, partido en gitignore, docs de operador y router

## Task 5: Índice generado y catálogo único

**Description:** `tools/skill-index/generate.py` emite el JSON gitignored con `version: 7.0.0-alpha.0` y escribe la tabla entre `<!-- SKILL-INDEX:START -->` y `<!-- SKILL-INDEX:END -->`. `check_catalog` solo compara esa región.

**Acceptance criteria:**

- [ ] Falta un marcador y el check falla
- [ ] El texto interior coincide con el generador
- [ ] `git check-ignore` ignora `skill-index.json`
- [ ] Todo `SKILL.md` está bajo `skills/` y `compatibility` solo contiene `cursor` y `pi`

**Verification:**

- [ ] Borrar `skill-index.json`, generar, y el router resuelve una skill
- [ ] `uv run python3 tools/validate/skill_spec.py`

**Dependencies:** Task 4

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `generate.py`, `skill_spec.check_catalog`, `route.py`, `workspace-router/run.py`

**Files likely touched:**

- `tools/skill-index/generate.py`
- `tools/validate/skill_spec.py`
- `tools/skill-router/route.py`
- `tools/workspace-router/run.py`
- `README.md`
- `docs/TAXONOMY.md`

**Estimated scope:** Medium

## Task 6: Plantillas

**Description:** Renombrar `templates/autoworkspace` a `templates/harness` y `templates/repo` a `templates/product`. Añadir `make new-product` y `make new-harness`. En `plan-continue` solo cambia la ruta de la plantilla.

**Acceptance criteria:**

- [ ] `bash scripts/check-structure.sh templates/product` pasa
- [ ] Un `--init` escribe desde `templates/harness`
- [ ] `make new-product` y `make new-harness` copian a `DEST`

**Verification:**

- [ ] `bash scripts/check-structure.sh templates/product`
- [ ] Targets make sobre un directorio temporal

**Dependencies:** Task 4

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `check-structure.sh`, `workspace-router --init`, targets make

**Files likely touched:**

- `templates/harness/`
- `templates/product/`
- `scripts/check-structure.sh`
- `tools/workspace-router/run.py`
- `Makefile`
- `.github/workflows/ci.yml`

**Estimated scope:** Medium

## Task 7: Tooling Python bajo tools/

**Description:** Mover `pyproject.toml` y `uv.lock` a `tools/`. Dejar `ruff.toml` y `mypy.ini` en la raíz como única config de lint y tipos, incluyendo `skills/`, `scripts/` y `tools/`. Prettier y lint-staged pasan a `config/`.

**Acceptance criteria:**

- [ ] No hay `pyproject.toml` ni `uv.lock` en la raíz
- [ ] Existen `ruff.toml` y `mypy.ini`
- [ ] Un archivo bajo `skills/` y otro bajo `scripts/` entran en el análisis
- [ ] `tools/pyproject.toml` no contiene `[tool.ruff]` ni `[tool.mypy]`

**Verification:**

- [ ] `uv sync --frozen --project tools`
- [ ] `uv run --project tools ruff check`
- [ ] `uv run --project tools mypy --strict`
- [ ] `make test`

**Dependencies:** Task 1, después del checkpoint de harness

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** uv, ruff, mypy, `npm run typecheck`

**Files likely touched:**

- `tools/pyproject.toml`
- `tools/uv.lock`
- `ruff.toml`
- `mypy.ini`
- `package.json`
- `Makefile`
- `.github/workflows/`

**Estimated scope:** Large, partido en proyecto uv, config de lint y workflows

## Task 8: local-email

**Description:** Renombrar `skills/local-proton/` a `skills/local-email/`. Mover la lógica Proton a `tools/email/drivers/proton/`. La skill conserva el contrato de ejecución y un script fino que delega.

**Acceptance criteria:**

- [ ] `ls skills | wc -l` es 16 e incluye `local-email`
- [ ] Siguen las cuatro operaciones
- [ ] El catálogo cuenta 16 skills y 32 operaciones

**Verification:**

- [ ] `uv run pytest tools/email tools/execution/tests/test_product_closure_catalog.py`

**Dependencies:** Tasks 5 y 7

**Implementation roles:** role-back, role-clean-code

**Test surfaces:** `read_mail`, `search_mail`, `send_mail`, `access_secret`; pytest del driver; catálogo

**Files likely touched:**

- `skills/local-email/`
- `tools/email/drivers/proton/`
- `tools/execution/registry.py`
- `tools/skill-router/intent-map.yaml`
- `.env.example`

**Estimated scope:** Medium

## Task 9: Cierre 7.0.0-alpha.0

**Description:** Subir `package.json` y el lock npm a `7.0.0-alpha.0`. Alinear el proyecto Python (o `7.0.0a0` si uv lo exige). CHANGELOG `## [7.0.0-alpha.0] - 2026-10-29` con el BREAKING del pivot.

**Acceptance criteria:**

- [ ] `bash run-validation.sh` pasa
- [ ] `make validate && make test && make smoke` pasa
- [ ] grep de `skills/` a cero
- [ ] `ls .opencode .agents` falla
- [ ] `git ls-files .cursor .opencode .agents opencode.json` vacío
- [ ] README y TAXONOMY tienen los marcadores
- [ ] `ls skills | wc -l` es 16
- [ ] Los installs a `/tmp/test-cursor` y `/tmp/test-pi` crean los symlinks

**Verification:**

- [ ] Los comandos de aceptación, en ese orden, antes de cualquier commit

**Dependencies:** Tasks 5, 6, 7 y 8

**Implementation roles:** role-back

**Test surfaces:** `release_coherence` sin publicar tag estable

**Files likely touched:**

- `package.json`
- `package-lock.json`
- `tools/pyproject.toml`
- `tools/uv.lock`
- `README.md`
- `CHANGELOG.md`

**Estimated scope:** Medium

## Checkpoint: After Tasks 0-1

- [ ] Parsers aceptan `6.1.0` y `7.0.0-alpha.0`
- [ ] El alpha no se etiqueta como estable

## Checkpoint: After Tasks 2-4

- [ ] Validación verde con repo en `6.1.0`
- [ ] Superficies OpenCode fuera del índice git

## Checkpoint: Complete

- [ ] Criterios de la tarea 9 en verde
