# Tests

### Propósito de este documento

- **Objetivos:** Pirámide CI (`quality`/`test`/`build`/`smoke`/`e2e`), coverage y contrato de smoke; el check required es `ci-gate`.
- **Estructura:** Esta meta-sección → Pirámide → Coverage → Smoke → e2e.
- **Contenido a integrar según contexto:** En producto, cambia ejemplos por comandos reales. Declara si hay artefacto (`build` sí/no). El gate ≥70% es opcional hasta suite estable ([ADR-0007](../architecture/decisions/ADR-0007-coverage-gate-opcional.md)); el reusable default es 80%. Sustituye el `smoke.sh` demo.

## Pirámide de la flota

| Capa              | Job (dentro del reusable) | Qué demuestra                                                                                      |
| ----------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| Calidad estática  | `quality`                 | format, lint, types, estructura, título de PR                                                      |
| Unit / function   | `test`                    | comportamiento de dominio + coverage                                                               |
| Artefacto         | `build`                   | el producto compila / genera output                                                                |
| Rutas / resultado | `smoke`                   | el artefacto responde (barato, ≤5 min)                                                             |
| UI / flujos       | `e2e` (opcional)          | Playwright u equivalente en webs P1                                                                |
| Agregado required | **`ci-gate`** (caller)    | todas las fases en success ([ADR-0013](../architecture/decisions/ADR-0013-check-unico-ci-gate.md)) |

El ruleset / branch protection exige **solo** `ci-gate` (app 15368).

## Coverage

- **Default del reusable:** **80%** de líneas (input `coverage-threshold`). Baja el input si la suite aún no es estable.
- **Umbral de flota documentado:** ≥ **70%** cuando el gate está activo ([ADR-0007](../architecture/decisions/ADR-0007-coverage-gate-opcional.md)).
- **Módulos críticos** (auth, pagos, parsers, crypto, pipelines): documenta **80%**.
- El gate vive **dentro** del job `test` del reusable. No hay check `coverage` aparte.
- Job `build`: solo si hay artefacto; si no, no se declara.

## Smoke (contrato)

Script `scripts/smoke.sh` o `make smoke` / `pnpm smoke`:

- Pocas aserciones. Sin dependencias de producción. Usa `.env.example` o mocks.
- Ejemplos: `GET /` o `/api/health` → 200 + marcador; CLI `--help` exit 0; infra `make validate`.
- En CI: job `smoke` del reusable después de `build` (o de `quality`+`test` si no hay build).

El `scripts/smoke.sh` de este repo es un **demo**: sale 0 y documenta el contrato. Sustitúyelo en producto.

## e2e

- Webs P1: Playwright (Chromium) recomendado vía input `e2e: true` del reusable-node.
- Feature branches: mismo job; `continue-on-error: false` en paths web.
