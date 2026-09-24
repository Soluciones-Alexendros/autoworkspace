# Tests

## Pirámide de la flota

| Capa | Job CI | Qué demuestra |
|------|--------|----------------|
| Calidad estática | `quality` | format, lint, types, estructura |
| Unit / function | `test` | comportamiento de dominio |
| Artefacto | `build` | el producto compila / genera output |
| Rutas / resultado | `smoke` | el artefacto responde (barato, ≤5 min) |
| UI / flujos | `e2e` (opcional) | Playwright u equivalente en webs P1 |

## Coverage

- **Por defecto:** ≥ **70%** de líneas en el job `test` de producto.
- **Módulos críticos** (auth, pagos, parsers, crypto, pipelines de datos): documenta umbral **80%** en el README o en este archivo del producto.
- Fallo de coverage = bloqueo de merge.
- Este canon no ejecuta un runner de coverage: el job `test` es el hook donde el producto lo engancha.

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
