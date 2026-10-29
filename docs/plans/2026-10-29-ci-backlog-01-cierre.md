---
name: CI-BACKLOG-01 denylist not_run
status: documented-not-started
blocked_by: none
implements_on_order: "Implementa fix denylist not_run"
---

# CI-BACKLOG-01 — Fix denylist `not_run` + estabilización

**Decisión del operador (cierre hilo 7.0.2):** solo documentar esta fase. No implementar aún. No iniciar 7.1.0.

## Estado congelado (v7.0.2)

- PRs mergeados: [#52](https://github.com/Soluciones-Alexendros/autoworkspace/pull/52) (7.0.1), [#53](https://github.com/Soluciones-Alexendros/autoworkspace/pull/53) (7.0.2 Pi install), [#54](https://github.com/Soluciones-Alexendros/autoworkspace/pull/54) (CHANGELOG 7.0.2).
- Tag / Release: [v7.0.2](https://github.com/Soluciones-Alexendros/autoworkspace/releases/tag/v7.0.2) — `isPrerelease=false`, `isDraft=false`.
- `is_template=true`. Install desde el tag: cursor + pi → 16 symlinks absolutos, `version==7.0.2`.
- Tag publicado vía fallback `cut_tag --apply --push` porque `release.yml` falla en el paso denylist.

## Gap actual

[`tools/validate/private_denylist.py`](../../tools/validate/private_denylist.py) es fail-closed en configuración:

| Condición                                | Código emitido   | Exit hoy |
| ---------------------------------------- | ---------------- | -------- |
| Env ausente (`CONFIG_MISSING`)           | `CONFIG_MISSING` | 1        |
| Vacío / solo whitespace (`CONFIG_EMPTY`) | `CONFIG_EMPTY`   | 1        |
| Regex inválida                           | `REGEX_INVALID`  | 1        |
| Match                                    | `DENYLIST_MATCH` | 1        |
| Sin match                                | `CLEAR`          | 0        |

Los tests `test_d01`–`test_d03` en [`tools/validate/tests/test_private_denylist.py`](../../tools/validate/tests/test_private_denylist.py) fijan exit ≠ 0 para missing/empty/whitespace.

Workflows que invocan el CLI sin wrapper `not_run`:

- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
- [`.github/workflows/quality.yml`](../../.github/workflows/quality.yml)
- [`.github/workflows/release.yml`](../../.github/workflows/release.yml)

Inyectan `secrets.HYGIENE_DENYLIST` (alias `AUTOWORKSPACE_PRIVATE_PATTERNS`). Si el secreto existe pero está vacío, CI/release quedan en rojo aunque el producto 7.0.2 sea válido. Diseño anterior (P11): ausencia → `not_run` con aviso, nunca verde falso.

## Fix requerido (cuando se ordene implementar)

1. **`private_denylist.py`:** missing, empty o whitespace → emitir código estable `NOT_RUN` (o conservar `CONFIG_*` mapeado a not_run), **exit 0**, WARN en stderr. **FAIL (exit 1)** solo con patrones inválidos, errores de escaneo, timeout o `DENYLIST_MATCH`.
2. **Tests:** `test_d01` / `test_d02` / `test_d03` → `not_run` + exit 0; casos con secreto no vacío válido siguen PASS/FAIL según match.
3. **Workflows:** el paso no debe fallar el job cuando el CLI reporta not_run (exit 0 basta si el CLI ya no falla; si se mantiene exit 1 para CONFIG_*, el YAML debe mapear a warning/`continue-on-error` solo para esos códigos — preferir exit 0 en el CLI).
4. **Docs en este archivo:** actualizar status a `done` tras el merge del fix.

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

## Próxima orden explícita

```text
Implementa fix denylist not_run
```

Hasta entonces: repo en **v7.0.2** estable; CI rojo conocido por `CONFIG_EMPTY` si el secreto está vacío.
