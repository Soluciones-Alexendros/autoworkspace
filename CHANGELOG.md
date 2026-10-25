# Changelog

Todas las versiones notables de este repositorio se documentan aquí. Formato: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Versionado: [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

La versión `2.1.0` de `package.json` no se publicó (no hubo tag ni sección de changelog). Su contenido queda absorbido en 2.2.0.

## [Unreleased]

### Changed

- **BREAKING:** autoworkspace es el host público del canon de flota (absorbe `repo-standard@e518eb1`). Callers pasan a `Soluciones-Alexendros/autoworkspace/.github/workflows/reusable-<stack>.yml@<SHA>`. Método de merge de la flota: `gh pr merge --auto --squash` (prohibidos `--merge` / `--rebase` / `--admin`). Plantilla de producto en `templates/repo/`.

- `plan-continue` 4.3.1 -> 4.3.2 (patch)

  Avoid CodeQL secret string literals in inicio_plan/scan_repo user-facing text and pattern type names.

- `plan-continue` 4.3.0 -> 4.3.1 (patch)

  Rename pattern-hit keys so CodeQL clear-text sinks stop treating report fields as secret sources.

- `local-maintenance` 5.1.2 -> 5.1.3 (patch)

- `local-maintenance` 5.1.1 -> 5.1.2 (patch)

- `local-maintenance` 5.0.0 -> 5.1.0 (minor)
- `local-proton` 5.0.0 -> 5.1.0 (minor)
- `local-security` 5.0.0 -> 5.1.0 (minor)
- `plan-continue` 4.2.0 -> 4.3.0 (minor)
- `plan-specification` 4.1.0 -> 4.2.0 (minor)
- `plan-validators` 5.0.0 -> 5.1.0 (minor)
- `project-architecture` 4.0.0 -> 4.1.0 (minor)
- `project-libraries` 4.0.1 -> 4.1.0 (minor)
- `project-publish` 4.2.0 -> 4.3.0 (minor)
- `role-back` 1.1.0 -> 1.2.0 (minor)
- `role-clean-code` 1.1.0 -> 1.2.0 (minor)
- `role-design` 4.1.0 -> 4.2.0 (minor)
- `role-front` 1.1.0 -> 1.2.0 (minor)
- `web-compliance` 4.0.0 -> 4.1.0 (minor)
- `web-owasp` 4.1.0 -> 4.2.0 (minor)
- `web-performance` 4.0.0 -> 4.1.0 (minor)

  execution contracts + P0 containment + canonical gate

## [5.0.0] - 2026-10-17

### Changed

- **Breaking:** taxonomía v5 — catálogo de **16 skills** en 5 dominios (`plan`, `local`, `project`, `web`, `role`), sin aliases ni carpetas vacías de compatibilidad. `system-maintenance`, `system-security` y `system-proton` pasan a `local-maintenance`, `local-security` y `local-proton` 5.0.0; `plan-validation` pasa a `plan-validators` 5.0.0.
- `local-maintenance` absorbe la skill `system-health`: medir la salud del sistema es una subfase del mantenimiento (`probe_system` → `audit_quick`/`audit_full` → `report_render` → remediación).
- Health Score con 5 categorías ponderadas: `security` 35, `updates` 25, `hygiene` 20, `resources` 10, `stability` 10 (nueva: LOG-06/LOG-08 salen de seguridad). Puntuación ponderada por severidad (`STATUS_VALUES` PASS 100 / WARN 40 / FAIL 0; `SEVERITY_WEIGHTS` P0 8 … P4 1); `SKIP`/`ERROR` ya no penalizan.
- `check_pkg_06` en apt compara contra `apt-cache dumpavail` (antes `apt list --manual-installed`, falso positivo de ~335 paquetes): solo cuenta paquetes realmente fuera de repositorio.
- `check_fs_11_inodes` emite PASS (P4) cuando los inodos están sanos.
- `plan-validators` absorbe `project-testing`: inventario obligatorio de comportamiento y pruebas integradas para rutas HTTP/cliente, funciones, jobs/colas/cron y flujos E2E, con trazabilidad a la suite estándar.
- `project-publish` 4.2.0 absorbe `project-hooks`: Husky, lint-staged, pre-commit, pre-push y gates locales forman parte del cierre de trabajo.
- Invocación recurrente de roles: `plan-specification` 4.1.0 y `plan-continue` 4.2.0 exigen reevaluar e invocar `role-back` 1.1.0, `role-front` 1.1.0, `role-design` 4.1.0 y `role-clean-code` 1.1.0 al iniciar un plan y antes de cada acción de implementación; el router y las plantillas recogen la misma regla.

### Removed

- Skill `system-health` (contenido integrado en `local-maintenance`).
- Skill `project-testing` (contenido integrado en `plan-validators`).
- Skill `project-hooks` (contenido integrado en `project-publish`).

## [4.1.0] - 2026-10-17

### Added

- `role-clean-code` 1.0.0: método ejecutable e idiomático para escribir código limpio y refactorizar con comportamiento preservado, basado en los fundamentos de _Clean Code_. Incluye principios esenciales, protocolo de refactor, diseño emergente/concurrencia y heurísticas priorizadas en referencias progresivas. Catálogo: **19 skills** en 5 dominios.
- Routing determinista y semántico ES/EN para «clean code», «código limpio», refactorización, nombres significativos, funciones pequeñas y código duplicado.

## [4.0.0] - 2026-10-11

### Added

- Pipeline Autoworkspace: `templates/autoworkspace/` (`project.yaml`, `status.yaml`) y `tools/workspace-router/` (fases DEFINE→STATUS + bump declarativo).
- Renovate cubre también `pip_requirements` / `pep621`; referencia `renovate-grouped.md`.
- `role-front` 1.0.0 y `role-back` 1.0.0: agentes especialistas de implementación con métodos ejecutables.

### Security

- `pytest` 8.3.5 → 9.0.3 (GHSA-6w46-j5rx-g56g).
- Hallazgos de secretos en `scan_repo` / `inicio_plan`: solo path/línea/tipo/fingerprint (sin valor).

### Changed

- **Breaking:** producto renombrado a **autoworkspace** (antes agent-skills).
- **Breaking:** taxonomía v4 — 18 skills en 5 dominios (`plan`, `system`, `project`, `web`, `role`). Prefijo del nombre = dominio.
  - `planning-*` → `plan-specification`, `plan-continue`, `plan-validation` (sin sufijo `driven-development`).
  - `operate-{health,maintenance,security}` → `system-*`; `build-proton-suite` → `system-proton`.
  - `verify-{hooks,testing,architecture,dependencies}` → `project-{hooks,testing,architecture,libraries}`; `operate-release` → `project-publish`.
  - `verify-{compliance,owasp,performance}` → `web-*`.
  - `build` pasa a dominio `role`: `role-front`, `role-back`, `role-design` (fusión interface + design-system).
- `plan-continue` absorbe el análisis de repo de `verify-repo` (scripts y refs de inicio de plan).
- `plan-specification` absorbe el desglose de `planning-task-breakdown`.
- `role-back` destila patrones serverless (caché/KV, colas, rate limit, blobs, búsqueda); Upstash como proveedor de ejemplo.
- `project-publish` 4.0.0 → 4.1.0 (merge-watch listen + política merge commit).

### Removed

- Skills finas: `operate-lifecycle`, `operate-monitoring`, `verify-fullaudit`, `build-automation`.
- Skills de lenguaje/ecosistema: `build-typescript`, `build-upstash` (contenido útil en `role-back`).
- Skills absorbidas: `planning-task-breakdown`, `verify-repo`, `build-interface`, `build-design-system`.

## [3.0.2] - 2026-10-05

### Changed

- Bump del grupo de GitHub Actions (Dependabot #7): actualización de los SHA fijados en `.github/workflows/*`.

## [3.0.1] - 2026-10-05

### Changed

- `devDependencies.lint-staged` 15.5.2 → 17.6.0 (Dependabot #8).

## [3.0.0] - 2026-10-05

### Changed

- **Breaking:** estándar v3.0 OpenCode-first: 25 skills en layout plano `skills/<name>/SKILL.md`.
- **Breaking:** nombres en inglés (`operate-health`, `operate-maintenance`, `operate-security`, `verify-dependencies`) y frontmatter de 6 claves (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`); `compatibility` = `opencode, codex, cursor, copilot`, `metadata` string→string, sin dependencia de un único vendor.
- 4 skills largas extraídas a `references/` manteniendo `SKILL.md` < 200 líneas; referencias `→` reescritas a nombres ingleses; `docs/TAXONOMY.md` actualizado.

### Added

- Router determinista `tools/skill-router/` (`route.py`, `build_index.py`, `intent-map.yaml`) y `skill-index.json` regenerable (25 skills).
- Harness OpenCode-first: `AGENTS.md`, `opencode.json`, `.opencode/agents/`, `templates/SKILL_TEMPLATE.md`.
- Validación v3 en `run-validation.sh` (frontmatter, referencias, arcos domain-scoped, paridad de índice, smoke del router) y guías en `docs/`.

## [2.2.0] - 2026-09-30

### Added

- Skills `verificar-dependencias` 1.0.1 y `operar-salud-sistema` 1.1.0 al catálogo (19 skills).
- Validadores `tools/validate/release_coherence.py` y `tools/validate/hygiene.py`.
- Corte de tag y GitHub Release: `tools/version/cut_tag.py` y workflow `release.yml` (notas desde el changelog, SHA pinning, provenance).
- `SECURITY.md`, `.github/CODEOWNERS`, `.github/dependabot.yml`, `requirements-dev.txt`.
- Archivo de operador `docs/archives/perfil-equipo-local.md` (fuera del paquete de la skill).

### Changed

- Canon de formulación en español (`docs/STANDARD.md`): descripción `Usar cuando` / `No usar para`, encabezados Propósito / Cuándo usar / Referencias.
- Puntos de entrada de las 19 skills alineados al canon. Minor: `operar-mantenimiento` 2.2.0, `disenar-constitucion` 1.2.0, `operar-salud-sistema` 1.1.0, `operar-seguridad` 2.2.0, `verificar-owasp` 2.2.0. Patch en el resto.
- Encabezados históricos del changelog a `## [X.Y.Z] - AAAA-MM-DD`.
- `contrast.py`: exit 1 cuando el par no cumple AA.

### Fixed

- Catálogo README (decía 17) alineado a 19 carpetas y a TAXONOMY.
- `verificar-owasp`: valla del formato de informe y sección Estructura que citaba `languages/`, `infrastructure/` y LICENSE inexistentes.
- `verificar-dependencias`: dejaba de documentar scripts que no existen.
- `release.yml` instalaba PyYAML, extraía notas del changelog y dejaba de usar `generate_release_notes`.

## [2.0.0] - 2026-09-27

- `construir-typescript` 2.0.0 -> 2.0.1 (patch)
- `construir-upstash` 1.0.0 -> 1.0.1 (patch)
- `verificar-compliance` 2.0.0 -> 2.0.1 (patch)

  Limpieza de referencias aspiracionales a skills inexistentes (web-nextjs, datos-*, cli-upstash, entorno-aislado); linaje absorbido (web-playwright, webapp-testing, web-rendimiento) conservado

- `construir-typescript` 1.0.0 -> 2.0.0 (major)
- `construir-upstash` 0.4.0 -> 1.0.0 (major)
- `disenar-arquitectura` 0.3.0 -> 1.0.0 (major)
- `disenar-constitucion` 0.2.1 -> 1.0.0 (major)
- `disenar-design-system` 0.2.0 -> 1.0.0 (major)
- `disenar-interfaz` 0.3.0 -> 1.0.0 (major)
- `operar-lifecycle` 0.1.0 -> 1.0.0 (major)
- `operar-mantenimiento` 1.0.0 -> 2.0.0 (major)
- `operar-release` 1.0.0 -> 2.0.0 (major)
- `operar-seguridad` 1.0.0 -> 2.0.0 (major)
- `verificar-compliance` 1.0.0 -> 2.0.0 (major)
- `verificar-fullaudit` 1.0.0 -> 2.0.0 (major)
- `verificar-hooks` 2.0.0 -> 3.0.0 (major)
- `verificar-owasp` 1.0.0 -> 2.0.0 (major)
- `verificar-performance` 2.0.0 -> 3.0.0 (major)
- `verificar-repo` 1.0.0 -> 2.0.0 (major)

  Reestructuración a 4 familias por fase SDLC (disenar/construir/verificar/operar); fusión email-proton+protonpass → construir-proton-suite v1.0.0; dominios alignux, datos, integraciones suprimidos

## [1.0.0] - 2026-09-27

- Consolidación FASE-4 (18 skills, 7 dominios): `docs/TAXONOMY.md`, `README.md` y `tools/validate/skill_spec.py` alineados a los nombres reales; `web-seguridad` con cuerpo íntegramente en ES (tecnicismos en inglés preservados).
- Tabla de renombros/fusiones:
  | Antes                 | Ahora               | Tipo                                  |
  | --------------------- | ------------------- | ------------------------------------- |
  | `web-rendimiento`     | `web-performance`   | renombro                              |
  | `design-system`       | `web-design-system` | renombro                              |
  | `typescript-avanzado` | `codigo-typescript` | renombro                              |
  | `repo-starting`       | `repo-audit`        | renombro                              |
  | `repo-precommit`      | `repo-hooks`        | renombro                              |
  | `repo-ending`         | `repo-release`      | renombro                              |
  | —                     | `repo-lifecycle`    | nueva (enrutador audit/hooks/release) |
  | —                     | `web-fullaudit`     | nueva (orquestador de auditoría web)  |
  | `web-playwright`      | —                   | suprimida                             |
  | `webapp-testing`      | —                   | suprimida                             |
- Canon `docs/architecture/ + docs/REUTILIZACION.md (P11) ` (solo lectura): `structure.md`, `ci-cd.md`, `release.md`, `security.md`, `templates/` (PR, issues, commitlint)
- Autoversionado semver por magnitud: `tools/version/bump.py`.

## [0.1.0] - 2026-09-26

Primera publicación pública del repo `Soluciones-Alexendros/autoworkspace` (21 skills, licencia MIT).

- Estructura `skills/<nombre>/` con frontmatter normalizado (`license: MIT`, `metadata` con autor, versión, dominio e idioma).
- Validadores `tools/validate/` (spec + enlaces), CI en `.github/workflows/` y `run-validation.sh` agregado.

[Unreleased]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v5.0.0...HEAD
[5.0.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v4.1.0...v5.0.0
[4.1.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v3.0.2...v4.0.0
[3.0.2]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v2.2.0...v3.0.0
[2.2.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v2.0.0...v2.2.0
[2.0.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Soluciones-Alexendros/autoworkspace/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/Soluciones-Alexendros/autoworkspace/releases/tag/v0.1.0
