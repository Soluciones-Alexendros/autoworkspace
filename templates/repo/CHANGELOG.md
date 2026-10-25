# Changelog

Registro SemVer del **contrato** de `repo-standard` (no de un runtime). Keep a Changelog no admite una sección larga «Propósito de este documento»: el propósito es solo listar cambios del estándar; el versionado y qué cuenta como breaking están en [ADR-0010](docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md).

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y el versionado [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Changed

- **BREAKING:** el único check required de la flota pasa a ser **`ci-gate`** (GitHub Actions, `integration_id` 15368). Dejan de ser required los nombres de fase `quality` / `test` / `smoke` / `build` / `e2e` ([ADR-0013](docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)). Migración: ruleset/protection → solo `ci-gate`; caller con `pipeline` + `ci-gate`.
- **BREAKING:** auto-merge squash sin revisión y **sin** etiqueta `automerge`; 0 approvals; break-glass = desactivar ruleset; etiqueta opcional `hold` ([ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)). Supersede [ADR-0006](docs/architecture/decisions/ADR-0006-reviews-por-perfil.md).
- CI empaquetado como workflows reutilizables pineados por SHA (`reusable-{node,rust,python,static}.yml`); plantillas en `stacks/<stack>/ci.yml` ([ADR-0014](docs/architecture/decisions/ADR-0014-release-please-y-packaging-por-stack.md)). Este major de contrato es **2.0.0**.

### Added

- [ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md), [ADR-0013](docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md), [ADR-0014](docs/architecture/decisions/ADR-0014-release-please-y-packaging-por-stack.md).
- Stack `stacks/python/` (uv).
- ADRs de mejoras del estándar (Mantenedor, 2026-09-24):
  - **P0 Accepted:** [ADR-0002](docs/architecture/decisions/ADR-0002-proteccion-metadatos-como-codigo.md) metadatos/protección como código; [ADR-0003](docs/architecture/decisions/ADR-0003-job-build-y-required-checks.md) job `build` solo si hay artefacto (superseded en required checks por ADR-0013); [ADR-0004](docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md) App Renovate a nivel org + Alerts vs version-updates; [ADR-0005](docs/architecture/decisions/ADR-0005-secret-scanning-org.md) secret scanning / push protection de flota.
  - **P1 Proposed:** [ADR-0006](docs/architecture/decisions/ADR-0006-reviews-por-perfil.md) (superseded por ADR-0012); [ADR-0007](docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md) coverage ≥70% como gate opcional; [ADR-0008](docs/architecture/decisions/ADR-0008-snippets-reales-post-oleada.md) snippets Astro+Vercel y Python skills; [ADR-0009](docs/architecture/decisions/ADR-0009-scorecard-cumplimiento-p0.md) scorecard P0; [ADR-0010](docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md) SemVer del contrato; [ADR-0011](docs/architecture/decisions/ADR-0011-bootstrap-desde-plantilla.md) bootstrap fail-closed.
- Meta-sección estable «Propósito de este documento» (Objetivos / Estructura / Contenido a integrar) en los markdown contractuales. Excepción: este CHANGELOG (párrafo breve, sin sección larga).
- Esqueleto canónico P0+P1: docs (`architecture`, `guides`, `runbooks`), `AGENTS.md`, `ARCHITECTURE.md`.
- Contrato CI de la flota: jobs `quality` (estructura), `test` (hook) y `smoke` (`scripts/smoke.sh`).
- `scripts/check-structure.sh` para validar los archivos obligatorios de este canon.
- Snippets de referencia en `stacks/typescript`, `stacks/rust` y `stacks/infra`.
- Renovate como único bot de dependencias (`.github/renovate.json`); sin Dependabot de version-updates.
- Plantillas de issue/PR, `CODEOWNERS`, `SECURITY.md`, `CODE_OF_CONDUCT.md` y guía `docs/REUTILIZACION.md`.
