# Spec: Pivot 7.0.0-alpha.0 Cursor y Pi

## Capability map

Un solo incremento. Los criterios de aceptación cruzan módulos, así que no hay un SPEC por módulo ni un segundo tracker en `tasks/`.

| Module id       | Responsibility                                                                      | Depends on                   |
| --------------- | ----------------------------------------------------------------------------------- | ---------------------------- |
| version-gate    | Aceptar `7.0.0-alpha.0` en validadores que hoy solo admiten `X.Y.Z`                 | —                            |
| harness-pivot   | Compatibilidad `cursor, pi`, instaladores y retirada de OpenCode, Codex y Copilot   | version-gate                 |
| catalog-ssot    | `skills/` única fuente; índice generado; tabla entre marcadores                     | harness-pivot                |
| template-rename | `templates/harness/` y `templates/product/`                                         | harness-pivot                |
| tooling-layout  | Proyecto Python bajo `tools/`; Ruff y Mypy en la raíz                               | version-gate                 |
| email-driver    | `local-proton` pasa a `local-email`; driver Proton en `tools/email/drivers/proton/` | catalog-ssot, tooling-layout |

Build order: version-gate → harness-pivot → catalog-ssot, template-rename y tooling-layout → email-driver → cierre de versión.

## Objective

Autoworkspace 7.0.0-alpha.0 solo descubre skills en Cursor (IDE) y Pi (terminal). `skills/` es la única fuente versionada. El operador instala symlinks con `scripts/install-cursor.sh` y `scripts/install-pi.sh`.

## Assumptions

1. Pi carga skills de proyecto en `.pi/skills/` y de usuario en `~/.pi/agent/skills/` (directorio del agente `~/.pi/agent`).
2. Cursor: proyecto `.cursor/skills/`, usuario `~/.cursor/skills/`.
3. `--target DIR` es el directorio de destino de los symlinks, con destino absoluto.
4. Nivel A de ambos harnesses es la puerta determinista de symlinks. CI no exige el binario de Pi ni de Cursor.
5. Las 16 skills cambian `compatibility`, así que `metadata.version` de las 16 pasa a `7.0.0-alpha.0`.
6. No se implementa driver Gmail. La description declara el hueco; el único driver que ejecuta es Proton.
7. Las operaciones `read_mail`, `search_mail`, `send_mail` y `access_secret` se conservan bajo `local-email`.
8. Husky se mantiene para Prettier en el pre-commit.
9. `.worktrees/` queda fuera.
10. Se conservan las entradas viejas de `CHANGELOG.md`, `docs/archives/`, los planes `docs/plans/2026-10-25-*`, `docs/plans/2026-10-29-ci-backlog-01-cierre.md` y `tasks/plan-*.md`.

## Tech stack

Python 3 del repo, uv, pytest, Ruff, Mypy, Prettier, Husky y lint-staged. Sin migración de lenguaje.

## Commands

```bash
uv run bash run-validation.sh
make validate && make test && make smoke
make new-product DEST=<dir>
make new-harness DEST=<dir>
bash scripts/install-cursor.sh --target /tmp/test-cursor
bash scripts/install-pi.sh --target /tmp/test-pi
python3 tools/skill-index/generate.py
```

Tras mover el proyecto Python, uv se invoca con `--project tools`. Hasta entonces sigue `uv run` desde la raíz.

## Project structure

- `skills/<nombre>/SKILL.md` — 16 directorios, incluido `local-email`
- `tools/pyproject.toml`, `tools/uv.lock`, `tools/skill-index/generate.py`, `tools/email/drivers/proton/`
- `templates/harness/` (`project.yaml`, `status.yaml`), `templates/product/`
- `scripts/install-cursor.sh`, `scripts/install-pi.sh` y librería interna de enlaces (journal, dry-run, conflictos, uninstall). Sin CLI pública `install.sh`
- `config/` para Prettier y lint-staged
- `ruff.toml` y `mypy.ini` en la raíz. `tools/pyproject.toml` no lleva `[tool.ruff]` ni `[tool.mypy]`
- `docs/harness-setup.md` sustituye a `docs/opencode-setup.md`
- `skill-index.json` generado y gitignored
- `README.md` y `docs/TAXONOMY.md` llevan el bloque entre `<!-- SKILL-INDEX:START -->` y `<!-- SKILL-INDEX:END -->`

`stacks/` permanece: `scripts/check-structure.sh` y el pin de CI lo exigen.

## Code style

Python existente del repo. Symlinks absolutos al directorio de cada skill. Description de `local-email`:

```text
Email local con drivers (proton, gmail via bridge). Use when operator requests email. Not for other providers without driver
```

En `plan-*`, `web-*` y `role-*` solo cambian `compatibility`, `metadata.version` y, donde exista, `compatibility` en `references/*-source.md`. En `plan-continue` también la ruta `templates/autoworkspace` → `templates/harness`.

## Testing strategy

Pytest de `tools/` y de las skills con scripts. `scripts/tests/test_install.sh` y el journal contra los instaladores nuevos. `skill_spec.py` comprueba que `compatibility` es solo el conjunto `cursor` y `pi`, que no hay `SKILL.md` fuera de `skills/`, y que el texto entre los marcadores de README y TAXONOMY es idéntico a la salida del generador. Esos marcadores son el único punto de inyección de `check_catalog`. El gate E2E deja de invocar el binario OpenCode. Ruff y Mypy se invocan con la config de la raíz.

## Boundaries

- Always: validar en local antes de sincronizar; no commitear `.env` ni el índice generado.
- Ask first: mover `stacks/` o implementar un driver Gmail.
- Never: skills nuevas; reescritura de la lógica de `plan-*`, `web-*` y `role-*`; borrar planes históricos; tag estable `v7.0.0` desde este alpha.

## Success criteria

- `bash run-validation.sh` pasa; `make validate && make test && make smoke` pasa.
- `grep -R "opencode\|codex\|copilot" skills/ --include="*.md" --include="*.json" --include="*.yaml"` no devuelve líneas.
- `ls .opencode .agents` falla.
- `git ls-files .cursor .opencode .agents opencode.json` no devuelve rutas.
- `ls skills/ | wc -l` es 16 e incluye `local-email`.
- Los dos `--target /tmp/...` crean un symlink por skill hacia `skills/<nombre>`.
- `package.json` es `7.0.0-alpha.0` y CHANGELOG tiene sección BREAKING de esa versión.
- README y TAXONOMY contienen `<!-- SKILL-INDEX:START -->` y `<!-- SKILL-INDEX:END -->`.

## Open questions

Ninguna abierta. Si `uv lock` rechaza `7.0.0-alpha.0` por PEP 440, `tools/pyproject.toml` y `tools/uv.lock` usan `7.0.0a0` y la coherencia trata ambas cadenas como la misma versión. `package.json`, README, CHANGELOG y el índice generado siguen en `7.0.0-alpha.0`.
