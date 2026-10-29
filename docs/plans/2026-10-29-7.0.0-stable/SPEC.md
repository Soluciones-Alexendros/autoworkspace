# Spec: Corte estable 7.0.0

## Capability map

Un solo incremento. Un SPEC. Canon en este directorio. No se escribe `tasks/plan.md` ni `tasks/todo.md`.

| Module id        | Responsibility                                                                                                         | Depends on  |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------- |
| stable-bump      | Manifiestos `7.0.0`, 16 `metadata.version`, CHANGELOG estable, parsers y `--release-gate`                              | —           |
| catalog-freeze   | Snapshot `docs/architecture/skill-index-7.0.0.json` y diff en `run-validation.sh`. `skill-index.json` sigue gitignored | stable-bump |
| product-template | Esqueleto en `templates/product/` y docs de `Use this template`. Sin `template-sync.yml`                               | —           |
| alpha-cleanup    | Cero `7.0.0-alpha` en el canon vivo                                                                                    | stable-bump |
| publish          | Tag y GitHub Release vía `release.yml`; `is_template` el último paso, con sí explícito                                 | los cuatro  |

Build order: `stable-bump` → `catalog-freeze` y `product-template` en paralelo → `alpha-cleanup` → `publish`.

## Objective

Cerrar la línea alpha de autoworkspace, congelar el catálogo de 16 skills y dejar el repo listo para publicarse como template de GitHub en el corte estable `7.0.0`.

El operador usa el canon en Cursor y Pi. El template de GitHub clona el repo entero. `make new-product` sigue copiando solo `templates/product/`.

## Assumptions

1. Versión objetivo: **`7.0.0`**. `package.json` y `package-lock.json` (raíz y `packages[""].version`) → `7.0.0`. `tools/pyproject.toml` y `tools/uv.lock` → `7.0.0` (PEP 440 estable; hoy el Python está en `7.0.0a1`). La equivalencia `7.0.0aN` ↔ `7.0.0-alpha.N` se conserva para prereleases futuros.
2. Las 16 skills suben `metadata.version` a `7.0.0`. No cambia `allowed-tools`, `metadata.type` ni `tools/execution/registry.yaml`.
3. `tools/skill-index/generate.py` deja `INDEX_VERSION = "7.0.0"`. El stdout actual (`Index OK`) no es el índice. BUILD añade `--json`: imprime el JSON canónico y no escribe el `skill-index.json` gitignored.
4. El validador de `catalog-freeze` es este comando, y solo este. Exit 0 congela el catálogo; cualquier diff es FAIL:

```bash
python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json
```

5. README y `docs/TAXONOMY.md` se actualizan con `generate.py --sync-docs` entre `<!-- SKILL-INDEX:START -->` y `<!-- SKILL-INDEX:END -->`. No a mano.
6. CHANGELOG gana `## [7.0.0] - 2026-10-29` con Fixed de promoción. Las secciones `[7.0.0-alpha.1]` y `[7.0.0-alpha.0]` se quedan.
7. Limpieza de `7.0.0-alpha` en markdown vivo: README, `ARCHITECTURE.md`, `docs/harness-setup.md`, `docs/TAXONOMY.md`, `docs/USAGE.md`, `docs/STANDARD.md`, `templates/` y `skills/`. La cadena se conserva en `CHANGELOG.md`, `docs/plans/` (este paquete y los de alpha) y `docs/architecture/decisions/` (ADR-0017). `ARCHITECTURE.md` y `docs/harness-setup.md` no la contienen hoy.
8. `cut_tag.py` sigue rechazando un prerelease. Con manifiesto `7.0.0` el tag permitido es `v7.0.0`. El tag y el Release los crea `.github/workflows/release.yml` al entrar en `main` (`cut_tag.py --apply`, `gh release create` sin `--prerelease`). Prueba local: `cut_tag.py --dry-run`. No hay `git tag` a mano en el worktree.
9. `is_template=true` es el último paso de BUILD. Requiere un sí explícito en ese turno. GitHub no lo deshace sin otra llamada a la API (`is_template=false`). Clona el repo entero, no solo `templates/product/`.
10. Roles de implementación: `role-back` y `role-clean-code`. Sin `role-front` ni `role-design`.
11. Sin skills nuevas. Sin `template-sync.yml`. Sin reescribir planes históricos ni ADR-0017.

## Tech stack

Python 3.12 del repo, uv, pytest, Ruff y Mypy ya configurados. Node solo para `package.json` / `package-lock.json`. Sin dependencias nuevas. Sin `--bump` del workspace router.

## Commands

```bash
uv lock --project tools
python3 tools/validate/release_coherence.py --root .
python3 tools/validate/release_coherence.py --root . --release-gate
python3 tools/version/cut_tag.py --dry-run
python3 tools/skill-index/generate.py --sync-docs
python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json
jq -r .version docs/architecture/skill-index-7.0.0.json
bash run-validation.sh
make validate && make test && make smoke
bash scripts/install-cursor.sh --target /tmp/test-cursor
bash scripts/install-pi.sh --target /tmp/test-pi
make new-product DEST=/tmp/prod-test && ls /tmp/prod-test
make new-harness DEST=/tmp/harness-test && ls /tmp/harness-test/.autoworkspace
ls skills | wc -l
find skills -name execution.yaml | wc -l
grep -R "opencode\|codex\|copilot" skills/ || true
grep -R "7.0.0-alpha" --include="*.md" . \
  | grep -v '/CHANGELOG.md' \
  | grep -v '/docs/plans/' \
  | grep -v '/docs/architecture/decisions/' \
  | wc -l
```

El `diff -q` de `--json` es el gate de `catalog-freeze`. No vale comparar el mensaje `Index OK` ni el `skill-index.json` gitignored.

## Project structure

- `package.json`, `package-lock.json` — versión npm `7.0.0`
- `tools/pyproject.toml`, `tools/uv.lock` — versión Python `7.0.0`
- `tools/skill-index/generate.py` — `INDEX_VERSION` y flag `--json`
- `tools/validate/release_coherence.py` — `--release-gate` exige versión estable y sección CHANGELOG de esa versión
- `tools/validate/skill_spec.py` — el parser ya acepta `X.Y.Z` y prerelease; el cambio es el test
- `tools/version/cut_tag.py` — el estable `v7.0.0` pasa; un alpha sigue en `_refuse_prerelease`
- `docs/architecture/skill-index-7.0.0.json` — snapshot congelado, versionado
- `run-validation.sh` — ejecuta el diff del snapshot y falla si no es idéntico
- `README.md`, `docs/TAXONOMY.md` — tabla solo vía marcadores del generador
- `CHANGELOG.md` — sección `[7.0.0]` nueva; alphas intactas
- `templates/product/` — `.cursor/skills/.gitkeep`, `.pi/skills/.gitkeep`, `.autoworkspace/` copiado de `templates/harness/` (`project.yaml`, `status.yaml`), `run-validation.sh` mínimo, README con los dos caminos de alta
- `templates/product/Makefile` — `validate` invoca el wrapper; el esqueleto no llama a un `scripts/check-structure.sh` que no viaja con la copia
- `.github/workflows/release.yml` — sin cambio de flags: el Release de un tag estable no lleva `--prerelease`

`skill-index.json` en la raíz sigue en `.gitignore`.

## Code style

Contratos, ids de módulo, flags y comandos en inglés. Este paquete y el informe al operador, en español. El bump de versión no reescribe cuerpos de skill. `role-clean-code` no aprovecha el diff para refactors vecinos. Registry y `allowed-tools` no se tocan.

## Testing strategy

- `tools/validate/tests/test_release_coherence.py`: `7.0.0` coherente entre package, README, pyproject, locks y CHANGELOG; un prerelease sigue parseando (`canonical_version`); `--release-gate` falla si el manifiesto es prerelease o si falta la sección estable.
- `tools/validate/tests/test_skill_spec.py`: `metadata.version: "7.0.0"` pasa el `SEMVER_RE`; un prerelease sigue pasando.
- Tests de `tools/version/cut_tag.py`: paquete `7.0.0` con notas no entra en `_refuse_prerelease`; `7.0.0-alpha.1` sigue refused. `--dry-run` no crea el tag.
- `generate.py`: dos `build_index` seguidos son iguales (ya está en `write_index`); `--json` es determinista y el snapshot commiteado coincide byte a byte con ese stdout.
- `run-validation.sh` incluye el diff. Un snapshot viejo o una skill editada es FAIL, no warning.
- Installs en `/tmp`: 16 symlinks absolutos cada uno.
- `make new-product` y `make new-harness` se comprueban por listado del `DEST`, no por la suite del canon dentro de la copia.

No hay superficie UI. No entra browser.

## Boundaries

- Always: el gate local del validador en verde antes de dar por hecha una tarea de código; no llamar PASS a un skip, una dependencia ausente o un `not_run`; regenerar el snapshot solo desde `generate.py`; no commitear `skill-index.json`.
- Ask first: tag, push del tag, GitHub Release, y el PATCH `is_template`. El PATCH es el último paso y exige un sí explícito en ese turno. También cualquier edición de `registry.yaml` o de `allowed-tools`.
- Never: skills nuevas; reintroducir `.opencode`, `.agents` o `skill-index.json` versionado; `template-sync.yml`; reescribir planes históricos o ADR-0017 para borrar la cadena alpha; `--bump` del workspace router; scripts mutadores de skill fuera de `run_registered`; `git tag` a mano en el worktree; marcar el repo como template antes del Release estable.

## Success criteria

- `bash run-validation.sh` verde
- `make validate && make test && make smoke` verde
- `ls skills | wc -l` == 16 y `find skills -name execution.yaml | wc -l` == 0
- `grep -R "opencode\|codex\|copilot" skills/` sin coincidencias
- `jq -r .version docs/architecture/skill-index-7.0.0.json` == `7.0.0`
- `python3 tools/skill-index/generate.py --json | diff -q - docs/architecture/skill-index-7.0.0.json` sale 0
- `package.json` es `7.0.0`, `tools/pyproject.toml` es `7.0.0`, CHANGELOG tiene `## [7.0.0] - 2026-10-29` y conserva las secciones alpha
- El grep acotado de `7.0.0-alpha` (Commands) sale 0
- Installs de prueba: 16 symlinks absolutos en cada target
- `cut_tag.py --dry-run` con manifiesto `7.0.0` anuncia `v7.0.0` y no lo crea
- En BUILD, `release.yml` publica el tag `v7.0.0` y un GitHub Release estable (sin `--prerelease`)
- `templates/product/README.md` documenta `Use this template` y `gh repo create --template Soluciones-Alexendros/autoworkspace`, y distingue ese clon del esqueleto `make new-product`
- `is_template=true` solo tras el Release y tras un sí explícito en el turno. Deshacerlo es otro PATCH de API

## Open questions

Ninguna. El alcance de la limpieza alpha y el comando del snapshot quedaron cerrados por el operador.
