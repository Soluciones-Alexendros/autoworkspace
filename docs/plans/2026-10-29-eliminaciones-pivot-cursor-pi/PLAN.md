# Implementation Plan: Pivot 7.0.0-alpha.0 Cursor y Pi

## Overview

Corte breaking que deja autoworkspace compatible solo con Cursor y Pi, consolida `skills/` como única fuente, renombra las plantillas, mueve el proyecto Python a `tools/` y convierte `local-proton` en `local-email` con driver Proton. El canon de este incremento es este directorio. No se escribe `tasks/plan.md` ni `tasks/todo.md`.

## Architecture decisions

- `stacks/` se queda. `scripts/check-structure.sh` exige `stacks/{python,typescript,rust,infra}/ci.yml` y el workflow de CI comprueba el pin.
- El índice pasa a artefacto gitignored emitido por `tools/skill-index/generate.py`. `route.py` y `tools/workspace-router/run.py` lo leen después de generarlo. Un solo generador.
- `templates/autoworkspace/` se renombra a `templates/harness/` (scaffold de `.autoworkspace/`). `templates/repo/` se renombra a `templates/product/` (esqueleto de repo). No se fusionan.
- La raíz pierde `pyproject.toml` y `uv.lock`. Un solo `tools/pyproject.toml` cubre skill-router, workspace-router, execution, validate, skill-index y email, y no lleva `[tool.ruff]` ni `[tool.mypy]`. `package.json` se queda para Husky. `ruff.toml` y `mypy.ini` viven en la raíz, incluyen `skills/`, `scripts/` y `tools/`, y usan el entorno `uv --project tools`.
- `release_coherence` acepta prerelease. Si uv exige PEP 440, `7.0.0a0` en `tools/` equivale a `7.0.0-alpha.0` del manifiesto npm. `cut_tag.py` no publica un tag estable a partir de un alpha.
- `.cursor/`, `.opencode/`, `.agents/` y `opencode.json` salen del índice. Se borra la excepción `!.cursor/hooks.json`. `.cursor/` sigue ignorado entero.
- Marcador único de catálogo, igual en README y `docs/TAXONOMY.md`:

```markdown
<!-- SKILL-INDEX:START -->
<!-- SKILL-INDEX:END -->
```

- Nivel A de Cursor y de Pi es la puerta de symlinks, no una prueba de binario.

## Task list

El detalle de aceptación, roles y superficies está en `TASKS.md`.

### Phase 1: Fundaciones

- [ ] Task 0: canon escrito (SPEC, PLAN, TASKS)
- [ ] Task 1: semver de prerelease

### Checkpoint: parsers

- [ ] `6.1.0` sigue pasando y un fixture `7.0.0-alpha.0` parsea
- [ ] Un alpha no produce tag estable

### Phase 2: Harness

- [ ] Task 2: frontmatter `cursor, pi`
- [ ] Task 3: instaladores Cursor y Pi
- [ ] Task 4: retirada de superficies y docs

### Checkpoint: harness

- [ ] `uv run bash run-validation.sh` verde con versión de repo aún `6.1.0`
- [ ] `git ls-files .cursor .opencode .agents opencode.json` vacío
- [ ] El E2E no exige binario OpenCode

### Phase 3: Consolidación

- [ ] Task 5: índice generado y catálogo
- [ ] Task 6: plantillas harness y product
- [ ] Task 7: tooling Python bajo `tools/`
- [ ] Task 8: `local-email`

### Phase 4: Cierre

- [ ] Task 9: `7.0.0-alpha.0`, CHANGELOG y validación completa

### Checkpoint: complete

- [ ] `bash run-validation.sh` y `make validate && make test && make smoke`
- [ ] grep de `skills/` a cero; 16 skills; installs en `/tmp`

## Risks and mitigations

| Risk                                            | Impact | Mitigation                                                                |
| ----------------------------------------------- | ------ | ------------------------------------------------------------------------- |
| `uv sync` de CI sigue apuntando a la raíz       | High   | Grep de `uv sync` y `uv run` en `.github/` y `package.json` en la tarea 7 |
| Ruff o Mypy dejan de ver `skills/` y `scripts/` | High   | `ruff.toml` y `mypy.ini` permanecen en la raíz                            |
| `7.0.0-alpha.0` inválido en PEP 440             | Med    | Equivalencia `7.0.0a0` solo en `tools/pyproject.toml` y `uv.lock`         |
| Perder journal y rollback del instalador        | High   | Librería interna hereda el comportamiento; no un `ln -s` suelto           |
| Invocaciones externas a `local-proton`          | Med    | BREAKING en CHANGELOG; sin alias de skill                                 |
