# Plantilla de producto (P0/P1)

### Propósito de este documento

- **Objetivos:** Puerta de entrada del esqueleto que se copia a un repo nuevo: qué es, cómo arrancar y dónde está el resto de la docs del canon.
- **Estructura:** Esta meta-sección → Qué hace / no hace → Crear repo → Scripts → índice → decisiones cerradas → licencia.
- **Contenido a integrar según contexto:** Sustituye el H1 y «Qué hace» por el *producto*. Enlaza el contrato vigente en autoworkspace ([ADR-0010](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md)). Ajusta badges, description y topics.

Esqueleto P0/P1 de **Soluciones-Alexendros**. El canon vivo (ADRs, reusables, stacks) está en [`Soluciones-Alexendros/autoworkspace`](https://github.com/Soluciones-Alexendros/autoworkspace).

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## Qué hace / qué no hace

**Hace**

- Fija el esqueleto de docs de producto, Renovate, CODEOWNERS y plantillas de issue/PR.
- Declara el contrato de agentes (`AGENTS.md` §1–8) alineado con la flota.
- Deja hooks de Makefile (`validate` / `lint` / `test` / `smoke`) para el stack del producto.

**No hace**

- No incluye los reusables CI ni los ADRs (viven en autoworkspace; los callers se pinean por SHA).
- No es una app ni un starter de Next/Astro/Rust.
- No sustituye `website-landingpage-template` como plantilla de landing.

## Crear un repo nuevo desde esta plantilla

```bash
gh repo create Soluciones-Alexendros/<n> --private --clone
cp -a /ruta/a/autoworkspace/templates/repo/. <n>/
cd <n>
# Ajusta README, .env.example, CODEOWNERS; copia stacks/<stack>/ci.yml → .github/workflows/ci.yml pineado al SHA de autoworkspace
make validate || true   # en producto, sustituye stubs
```

Para **alinear un repo existente**: checklist en [`docs/REUTILIZACION.md`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/REUTILIZACION.md).

## Scripts / Makefile

| Comando | En esta plantilla | En un repo de producto |
| --- | --- | --- |
| `make validate` | stub / estructura | integridad / schemas |
| `make lint` | stub documentado | format + lint + types |
| `make test` | placeholder | unit/function + coverage |
| `make smoke` | contrato documentado | health / `--help` |

## Documentación (canon en autoworkspace)

| Doc | Para quién |
| --- | --- |
| [`docs/REUTILIZACION.md`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/REUTILIZACION.md) | Mantenedor que alinea un repo existente |
| [`docs/architecture/overview.md`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/overview.md) | Diseño del canon |
| [`docs/guides/`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/guides/) | Setup, estilo, tests |
| [`docs/runbooks/`](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/runbooks/) | Deploy, rollback, secretos |
| [`AGENTS.md`](AGENTS.md) | Agentes IA / Mantenedor (viaja con la plantilla) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Resumen de 1 página (viaja con la plantilla) |
| [`docs/README.md`](docs/README.md) | Índice local de esta plantilla |

## Decisiones cerradas (no reabrir)

- **Renovate** es el único bot de version-updates ([ADR-0004](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)).
- Auto-merge squash con `ci-gate` verde; 0 approvals; etiqueta opcional `hold` ([ADR-0012](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).
- Required check: solo `ci-gate` ([ADR-0013](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)).
- Secret scanning + push protection ON a nivel org ([ADR-0005](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0005-secret-scanning-org.md)).

## Licencia

[MIT](./LICENSE) © Soluciones Alexendros / Alejandro Domingo Agustí.
