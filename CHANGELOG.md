# Changelog

Todos los cambios relevantes de este canon se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y el versionado [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Esqueleto canónico P0+P1: docs (`architecture`, `guides`, `runbooks`), `AGENTS.md`, `ARCHITECTURE.md`.
- Contrato CI de la flota: jobs `quality` (estructura), `test` (hook) y `smoke` (`scripts/smoke.sh`).
- `scripts/check-structure.sh` para validar los archivos obligatorios de este canon.
- Snippets de referencia en `stacks/typescript`, `stacks/rust` y `stacks/infra`.
- Renovate como único bot de dependencias (`.github/renovate.json`); sin Dependabot de version-updates.
- Plantillas de issue/PR, `CODEOWNERS`, `SECURITY.md`, `CODE_OF_CONDUCT.md` y guía `docs/REUTILIZACION.md`.
