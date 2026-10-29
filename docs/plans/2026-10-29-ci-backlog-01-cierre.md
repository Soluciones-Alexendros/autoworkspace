---
name: CI-BACKLOG-01 denylist not_run
status: done
blocked_by: none
implements_on_order: "Implementa fix denylist not_run"
---

# CI-BACKLOG-01 — Fix denylist `not_run` + estabilización

**Estado:** implementado. Config ausente/vacía → `NOT_RUN` exit 0 + WARN; fail-closed solo con patrones válidos.

## Estado congelado (v7.0.2)

- PRs mergeados: [#52](https://github.com/Soluciones-Alexendros/autoworkspace/pull/52) (7.0.1), [#53](https://github.com/Soluciones-Alexendros/autoworkspace/pull/53) (7.0.2 Pi install), [#54](https://github.com/Soluciones-Alexendros/autoworkspace/pull/54) (CHANGELOG 7.0.2).
- Tag / Release: [v7.0.2](https://github.com/Soluciones-Alexendros/autoworkspace/releases/tag/v7.0.2) — `isPrerelease=false`, `isDraft=false`.
- `is_template=true`. Install desde el tag: cursor + pi → 16 symlinks absolutos, `version==7.0.2`.
- Tag publicado vía fallback `cut_tag --apply --push` porque `release.yml` falla en el paso denylist.

## Comportamiento actual (post-fix)

[`tools/validate/private_denylist.py`](../../tools/validate/private_denylist.py):

| Condición                                | Código emitido                      | Exit |
| ---------------------------------------- | ----------------------------------- | ---- |
| Env ausente (`CONFIG_MISSING`)           | `NOT_RUN` + WARN (`CONFIG_MISSING`) | 0    |
| Vacío / solo whitespace (`CONFIG_EMPTY`) | `NOT_RUN` + WARN (`CONFIG_EMPTY`)   | 0    |
| Regex inválida                           | `REGEX_INVALID`                     | 1    |
| Match                                    | `DENYLIST_MATCH`                    | 1    |
| Sin match                                | `CLEAR`                             | 0    |

Tests `test_d01`–`test_d03`: `NOT_RUN` + exit 0. Workflows (`ci.yml`, `quality.yml`, `release.yml`) no necesitan wrapper: exit 0 basta.

### Fail-open vs fail-closed

| Modo                              | Cuándo                                                          | Comportamiento                                                         |
| --------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **not_run (fail-open de config)** | Secreto ausente, vacío o solo whitespace                        | Paso documentado como omitido; CI verde; no hay inspección de patrones |
| **fail-closed real**              | Secreto `HYGIENE_DENYLIST` con ≥1 patrón válido (uno por línea) | CLEAR → verde; match / regex inválida → rojo                           |

Configurar fail-closed: Settings → Secrets → Actions → `HYGIENE_DENYLIST` con patrones personales (uno por línea, sin valores vacíos). Local: `AUTOWORKSPACE_PRIVATE_PATTERNS`.

### Rama y merge previstos

- Rama: `fix/ci-denylist-not-run`
- PR → `main`, `gh pr merge --auto --squash --delete-branch`
- Sin tag `v7.0.3` ni `project-publish` en este fix salvo orden aparte

### Criterios de hecho (fix)

```bash
HYGIENE_DENYLIST="" python3 tools/validate/private_denylist.py --root .   # NOT_RUN, exit 0
env -u HYGIENE_DENYLIST -u AUTOWORKSPACE_PRIVATE_PATTERNS \
  python3 tools/validate/private_denylist.py --root .                     # NOT_RUN, exit 0
# Con secreto no vacío válido: CLEAR o DENYLIST_MATCH según contenido
make validate && make test && make smoke
uv run --project tools bash run-validation.sh   # All checks passed
```

CI en `main`/`release` verde con secreto vacío o ausente.

## Fuera de alcance de esta fase

- 7.1.0 skills content (no crear `docs/plans/skill-content-improvement-7.1.0.md`)
- Tag `v7.0.3` / `project-publish`
- Mutar `metadata.version` de skills o `docs/architecture/skill-index-7.0.0.json`
- `CLOSURE*.md` en la raíz del repo

## Ship log 7.0.2

| Ítem                                | Ref                                                                                                                               |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 7.0.1 install AI API                | [#52](https://github.com/Soluciones-Alexendros/autoworkspace/pull/52)                                                             |
| 7.0.2 Pi install (contrato oficial) | [#53](https://github.com/Soluciones-Alexendros/autoworkspace/pull/53)                                                             |
| CHANGELOG → `[7.0.2] - 2026-10-29`  | [#54](https://github.com/Soluciones-Alexendros/autoworkspace/pull/54)                                                             |
| Tag + Release                       | [v7.0.2](https://github.com/Soluciones-Alexendros/autoworkspace/releases/tag/v7.0.2) via `cut_tag` fallback (notes del CHANGELOG) |

## Cierre

Orden `Implementa fix denylist not_run` ejecutada en `fix/ci-denylist-not-run`. Sin tag `v7.0.3` salvo orden aparte.
