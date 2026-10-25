# Decisiones de arquitectura (ADR)

### Propósito de este documento

- **Objetivos:** Índice del registro de ADRs del canon (y, en un producto, de las decisiones de *ese* sistema).
- **Estructura:** Esta meta-sección → estados del ciclo → tabla ID/título/estado/prioridad → cómo añadir una.
- **Contenido a integrar según contexto:** En producto, vacía la tabla y lista solo ADRs del producto. Enlaza los ADRs del canon que adoptes (`repo-standard ≥x.y`). No copies el contenido de ADR-0001…0014: son del meta-estándar.

Registro de decisiones del canon. Estados: **Proposed** → **Accepted** → **Superseded** / **Deprecated**.

Prioridad: **P0** (hacer pronto) · **P1** (después de P0). Un ADR puede estar Accepted (política cerrada) con checklist de implementación aún abierto.

## Índice

| ID | Título | Estado | Prioridad |
|----|--------|--------|-----------|
| [ADR-0001](./ADR-0001-canon-repo-standard.md) | Este repo es el canon de flota | Superseded in part by ADR-0016 | — |
| [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md) | Protección y metadatos como código | Accepted | P0 |
| [ADR-0003](./ADR-0003-job-build-y-required-checks.md) | Cuándo el job `build` es required | Superseded by ADR-0013 | P0 |
| [ADR-0004](./ADR-0004-renovate-org-y-dependabot.md) | Renovate org y política Dependabot | Accepted | P0 |
| [ADR-0005](./ADR-0005-secret-scanning-org.md) | Secret scanning / push protection org | Accepted | P0 |
| [ADR-0006](./ADR-0006-reviews-por-perfil.md) | Reviews por perfil y label `automerge` | Superseded by ADR-0012 | P1 |
| [ADR-0007](./ADR-0007-coverage-gate-opcional.md) | Coverage ≥70% como gate opcional | Proposed | P1 |
| [ADR-0008](./ADR-0008-snippets-reales-post-oleada.md) | Snippets Astro y Python skills | Proposed | P1 |
| [ADR-0009](./ADR-0009-scorecard-cumplimiento-p0.md) | Scorecard P0 rojo/ámbar/verde | Proposed | P1 |
| [ADR-0010](./ADR-0010-semver-contrato-estandar.md) | SemVer del contrato del estándar | Proposed | P1 |
| [ADR-0011](./ADR-0011-bootstrap-desde-plantilla.md) | Bootstrap al usar la plantilla | Superseded by templates/repo (ADR-0016) | P1 |
| [ADR-0012](./ADR-0012-solo-dev-automerge-sin-revision.md) | Solo-dev con IA: auto-merge sin revisión | Accepted | P0 |
| [ADR-0013](./ADR-0013-check-unico-ci-gate.md) | Check único `ci-gate` | Accepted | P0 |
| [ADR-0014](./ADR-0014-release-please-y-packaging-por-stack.md) | Versionado release-please + packaging por stack | Accepted | P1 |
| [ADR-0016](./ADR-0016-autoworkspace-host-del-canon.md) | autoworkspace es el host del canon | Accepted | P0 |

## Cómo añadir una

1. Copia [template.md](./template.md) a `ADR-NNNN-titulo-kebab.md`.
2. Incluye la meta-sección «Propósito de este documento», **Prioridad** (P0/P1) y **Checklist de implementación**.
3. Enlázala en esta tabla.
4. Si sustituye a otra, marca la antigua como Superseded y apunta aquí.
5. Resume el impacto en `CHANGELOG.md` `[Unreleased]` si cambia el contrato de flota.
