# repo-standard

### Propósito de este documento

- **Objetivos:** Puerta de entrada del canon (y, en un producto, del repo): qué es, qué no es, cómo arrancar y dónde está el resto de la docs.
- **Estructura:** Esta meta-sección → badges → Qué hace / no hace → Requisitos → Quickstart → Scripts → índice de docs → decisiones cerradas → metadatos → seguridad → licencia.
- **Contenido a integrar según contexto:** Sustituye el H1 y «Qué hace» por el *producto*. No copies «este repo es el meta-estándar». Enlaza `repo-standard ≥x.y` ([ADR-0010](docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md)). Ajusta badges, description y topics. Los comandos de la tabla Makefile deben ser los reales del stack, no los stubs.

Canon de plataforma de **Iniciativas-Alexendros**: el contrato P0/P1 que el resto de la flota copia o alinea.

[![CI](https://github.com/Iniciativas-Alexendros/repo-standard/actions/workflows/ci.yml/badge.svg)](https://github.com/Iniciativas-Alexendros/repo-standard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## Qué hace / qué no hace

**Hace**

- Fija el esqueleto de docs, CI (fases `quality` → `test` → `build` → `smoke`; check required `ci-gate`), Renovate, CODEOWNERS y plantillas.
- Define perfiles **P0 Base**, **P1 Producto** y **P2 Público**.
- Explica cómo aplicar el estándar a un **repo ya existente** (`docs/REUTILIZACION.md`).
- Ofrece workflows reutilizables y callers por stack (`stacks/typescript`, `stacks/rust`, `stacks/python`, `stacks/infra`) sin aplastar el runtime.

**No hace**

- No es una app ni un starter de Next/Astro/Rust.
- No unifica el framework de producto.
- No despliega a producción ni guarda secretos reales.
- No sustituye `website-landingpage-template` como plantilla de landing: este repo es el meta-estándar.

## Requisitos

Para **usar este repo como plantilla GitHub** (repo nuevo):

- Cuenta con permiso de crear repos en `Iniciativas-Alexendros` (o un fork personal).
- `git` y, en local, `bash` + `make`.

Para **alinear un repo existente**: no hace falta clonar este árbol entero. Sigue el checklist de [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md).

## Quickstart (≤10 min)

### A. Crear un repo nuevo desde este canon

1. En GitHub: **Use this template** → crea el repo (marca *Include all branches* solo si lo necesitas).
2. Si el botón no aparece, un mantenedor debe activar **Template repository** en Settings de `repo-standard`.
3. Clona, crea una rama `feat/…` y ajusta:
   - `README.md` (qué es el producto)
   - `.env.example` (keys reales del runtime, siguen siendo placeholders)
   - `stacks/` → copia `stacks/<stack>/ci.yml` a `.github/workflows/ci.yml` (pin SHA del reusable)
   - `docs/architecture/overview.md` (límites del sistema)
4. En local:

   ```bash
   make validate
   make test
   make smoke
   ```

5. Abre un PR a `main`. El único check required es **`ci-gate`** ([ADR-0013](docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)). Auto-merge squash sin revisión ([ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).

### B. Alinear un repo que ya existe

No copies a ciegas. Checklist y orden: **[`docs/REUTILIZACION.md`](docs/REUTILIZACION.md)**.

## Scripts / Makefile

| Comando | Qué hace en este canon | En un repo de producto |
|---------|------------------------|------------------------|
| `make validate` | `scripts/check-structure.sh` | integridad / `check:env` / schemas |
| `make lint` | stub documentado | format + lint + types |
| `make test` | placeholder que documenta el hook | unit/function + coverage ≥70% |
| `make smoke` | `scripts/smoke.sh` (exit 0 + contrato) | health/rutas/binario `--help` |

## Documentación

Índice: [`docs/README.md`](docs/README.md)

| Doc | Para quién |
|-----|------------|
| [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md) | Mantenedor que alinea un repo existente |
| [`docs/architecture/overview.md`](docs/architecture/overview.md) | Diseño del canon |
| [`docs/guides/`](docs/guides/) | Setup, estilo, tests |
| [`docs/runbooks/`](docs/runbooks/) | Deploy, rollback, secretos |
| [`AGENTS.md`](AGENTS.md) | Agentes IA / Mantenedor |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Resumen de 1 página |

## Decisiones cerradas (no reabrir)

- **Renovate** es el único bot de version-updates. No hay `dependabot.yml` de bump de versiones. Las Dependabot Alerts de seguridad pueden quedar ON.
- Docs en **español**.
- Coverage por defecto **≥70%**; documenta **80%** en módulos críticos.
- Auto-merge squash humano/agente con `ci-gate` verde; 0 approvals; etiqueta opcional `hold` ([ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).
- Fases: quality → test → build → smoke (`e2e` opcional). Required check: solo `ci-gate`. `build` solo si hay artefacto ([ADR-0013](docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)).
- Prerrequisito org: GitHub App **Renovate** instalada ([ADR-0004](docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)). Dependabot Alerts ON; sin version-updates de Dependabot.
- Secret scanning + push protection ON a nivel org ([ADR-0005](docs/architecture/decisions/ADR-0005-secret-scanning-org.md)).
- Ampliaciones P0/P1: índice en [`docs/architecture/decisions/`](docs/architecture/decisions/).

## Metadatos recomendados (Settings del repo)

Description (≤120): `Canon de plataforma — plantilla P0/P1 para homogeneizar la flota — docs, CI, Renovate`

Topics: `template` · `github-actions` · `documentation` · `standards` · `renovate` · `platform`

## Seguridad

Reportes privados: [`SECURITY.md`](SECURITY.md).

## Licencia

[MIT](./LICENSE) © Iniciativas Alexendros / Alejandro Domingo Agustí.
