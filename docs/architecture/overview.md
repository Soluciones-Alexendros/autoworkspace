# Overview del canon

### Propósito de este documento

- **Objetivos:** Diseño del sistema: límites, flujos y relación con stacks/gold. En producto, overview del _producto_.
- **Estructura:** Esta meta-sección → diagrama → Límites (dentro/fuera) → Flujos → Relación con gold (canon) o cajas (producto) → Stacks.
- **Contenido a integrar según contexto:** Reescribe límites y flujos del producto. No copies la tabla de gold ni el diagrama del meta-estándar. Enlaza ADRs propios.

Diagramas de arquitectura (fuentes JSON validadas en `ci-gate`, HTML solo como artefacto de CI):

- **D01 `architecture`** — capas del canon: `skills/`, `tools/`, `.github/workflows/reusable-*`, `stacks/`, `templates/repo/` y `docs/architecture/decisions/`.
- **D02 `workflow`** — flujo en dos fases: rama de tarea → PR de tarea → `plan/<id>` → PR del plan → `main` → release → tag `v*` → publicación.
- **D03 `sequence`** — agregación de `ci-gate` con los jobs reales de `ci.yml`.
- **D04 `lifecycle`** — ciclo de vida de un ADR.

## Límites del sistema

**Dentro**

- Árbol canónico de raíz y `.github/`
- Arquitectura de documentación (`docs/`)
- Contrato de agentes (`AGENTS.md`)
- Fachada `Makefile` (`lint` `test` `smoke` `validate`)
- Política de deps (Renovate) y auto-merge squash vía `ci-gate`
- Perfiles P0 / P1 / P2

**Fuera**

- Código de negocio de cada producto
- Hosting, DNS, secretos de Environments
- Settings de organización (rulesets, billing, teams)
- Repos archivados y forks externos

## Flujos

1. **Repo nuevo:** GitHub Template → ajustar README/env/CI del stack → PR a `main`.
2. **Repo existente:** checklist de [REUTILIZACION.md](../REUTILIZACION.md) en un único PR.
3. **Cambio del canon:** ADR si toca una decisión (P0/P1 en [decisions/](./decisions/)); snippets de `stacks/` si toca un runtime; bump de contrato reflejado en `CHANGELOG.md` ([ADR-0010](./decisions/ADR-0010-semver-contrato-estandar.md)).

## Relación con los gold

El diseño fusiona lo que ya funciona:

| Fuente                         | Qué se hereda                                           |
| ------------------------------ | ------------------------------------------------------- |
| `website-landingpage-template` | Template GitHub, CI limpio, idea de `REUTILIZACION.md`  |
| `zedazo`                       | Governance: AGENTS, ARCHITECTURE, CoC, CODEOWNERS, ADRs |
| `saas-afiladocs`               | `check:env`, actionlint, runbooks, SUPPORT (P2)         |
| `miwebsite-alexendrosdev`      | SECURITY + CONTRIBUTING + AGENTS + issue forms          |
| `infraestructura-stack`        | Makefile fachada, ADRs, runbooks de infra               |

## Stacks

Los jobs se llaman igual; los comandos no:

| Stack             | Quality típico                       | Smoke típico                 |
| ----------------- | ------------------------------------ | ---------------------------- |
| TypeScript / pnpm | format, lint, typecheck              | URL `/` o `/api/health`      |
| Rust / Cargo      | fmt, clippy `-D warnings`            | binario `--help` / `version` |
| Infra / Makefile  | `make lint` `typecheck` `actionlint` | `make validate` + dry-run    |

Fragmentos listos para copiar: [`stacks/`](../../stacks/).
