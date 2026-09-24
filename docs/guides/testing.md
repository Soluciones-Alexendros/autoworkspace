# Tests

### Propósito de este documento

- **Objetivos:** Pirámide CI (`quality`/`test`/`build`/`smoke`/`e2e`), coverage y contrato de smoke.
- **Estructura:** Esta meta-sección → Pirámide → Coverage → Smoke → e2e.
- **Contenido a integrar según contexto:** En producto, cambia ejemplos por comandos reales. Declara si hay artefacto (`build` sí/no, [ADR-0003](../architecture/decisions/ADR-0003-job-build-y-required-checks.md)). El gate ≥70% es opcional hasta suite estable ([ADR-0007](../architecture/decisions/ADR-0007-coverage-gate-opcional.md)); documenta 80% en críticos. Sustituye el `smoke.sh` demo.

## Pirámide de la flota

| Capa | Job CI | Qué demuestra |
|------|--------|----------------|
| Calidad estática | `quality` | format, lint, types, estructura |
| Unit / function | `test` | comportamiento de dominio |
| Artefacto | `build` | el producto compila / genera output |
| Rutas / resultado | `smoke` | el artefacto responde (barato, ≤5 min) |
| UI / flujos | `e2e` (opcional) | Playwright u equivalente en webs P1 |

## Coverage

- **Umbral de flota:** ≥ **70%** de líneas, **dentro** del job `test` (no un check `coverage` aparte).
- **Módulos críticos** (auth, pagos, parsers, crypto, pipelines de datos): documenta umbral **80%** en el README o en este archivo del producto.
- El gate es **opcional hasta que la suite sea estable** ([ADR-0007](../architecture/decisions/ADR-0007-coverage-gate-opcional.md)). Cuando está ON, fallar coverage bloquea el merge.
- Este canon no ejecuta un runner de coverage: el job `test` es el hook donde el producto lo engancha.
- Job `build`: solo si hay artefacto; si no, **no se declara** ([ADR-0003](../architecture/decisions/ADR-0003-job-build-y-required-checks.md)).

## Smoke (contrato)

Script `scripts/smoke.sh` o `make smoke` / `pnpm smoke`:

- Pocas aserciones. Sin dependencias de producción. Usa `.env.example` o mocks.
- Ejemplos: `GET /` o `/api/health` → 200 + marcador; CLI `--help` exit 0; infra `make validate`.
- En CI: job `smoke` después de `build` (o después de `quality`+`test` si no hay build, como aquí).

El `scripts/smoke.sh` de este repo es un **demo**: sale 0 y documenta el contrato. Sustitúyelo en producto.

## e2e

- Webs P1: Playwright (Chromium) recomendado, required en `main` si el coste lo permite.
- Feature branches: mismo job; `continue-on-error: false` en paths web.
- No sustituye a smoke.
