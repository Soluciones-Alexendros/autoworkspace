# autoworkspace

### Propósito de este documento

- **Objetivos:** Presentar el pipeline, el catálogo de 16 skills y la instalación en los harnesses.
- **Estructura:** Esta meta-sección → qué es el producto → inicio rápido → skills por dominio → nomenclatura → validación.
- **Contenido a integrar según contexto:** El canon de flota vive en este mismo repo (`docs/architecture/`, `stacks/`, `templates/product/`). Este README presenta el producto y apunta al índice del canon.

Workspace agéntico de Soluciones-Alexendros (MIT): no es una vitrina de skills, sino un pipeline preprogramado con variables por proyecto — especificación → esquemas/tests → código → validación → integración → status declarativo versionado. También es el **host público del canon de flota** (antes `repo-standard`).

Versión **7.0.2**. 16 skills en 5 dominios (`plan`, `local`, `project`, `web`, `role`). Nombres y contenido de skills en inglés; conversaciones en español.

**Deps:** version-updates vía [Renovate](.github/renovate.json) (Dependabot Alerts de seguridad pueden quedar ON). App Renovate en la org es prerrequisito humano.

## Inicio rápido

```bash
git clone https://github.com/Soluciones-Alexendros/autoworkspace.git
bash autoworkspace/scripts/install-cursor.sh --user
```

## Configuración en Cursor y Pi

Cursor (IDE) y Pi (terminal) son los dos harnesses, ambos en nivel A: la puerta es el symlink, no un binario en CI. El catálogo versionado es solo `skills/`. Cursor versiona hooks, rules y agents bajo `.cursor/`; los symlinks de skills se crean con `install-cursor.sh`.

```bash
git clone https://github.com/Soluciones-Alexendros/autoworkspace.git
cd autoworkspace
bash scripts/install-cursor.sh --target .cursor/skills
bash scripts/install-cursor.sh --user
bash scripts/install-pi.sh --target .pi/skills
bash scripts/install-pi.sh --user
bash scripts/install.sh --harness pi --target /tmp/ai-pi --yes --json
bash run-validation.sh
```

Comprueba el enrutado con:

```bash
python tools/skill-router/route.py "limpia mi sistema Arch" --top 3
python tools/workspace-router/run.py --init --repo .   # scaffold once
python tools/workspace-router/run.py --phase DEFINE --repo . --json   # read-only route
```

La ejecución mutadora se declara en `tools/execution/registry.yaml` (schema validado). Las skills enlazan con `metadata.execution: <tool_id>` cuando aplica; las de tipo `audit` no tienen entrada. Mutación solo vía `run_registered` + aprobación. Migraciones del cierre verificable: `docs/verifiable-closure-migrations.md`. Harnesses: `docs/harness-integration.md` (Cursor y Pi, nivel A). [ADR-0017](docs/architecture/decisions/ADR-0017-centralizacion-execution-min-priv.md).

Plantillas de proyecto: `templates/harness/` → copiar a `<repo>/.autoworkspace/`.

Consulta `docs/harness-integration.md`, `docs/harness-setup.md` y `docs/routing.md`.

## Skills por dominio

16 skills en 5 dominios. La tabla la escribe `tools/skill-index/generate.py` entre los marcadores.

<!-- SKILL-INDEX:START -->

| Skill                  | Domain  | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `local-email`          | local   | Email local con drivers (proton, gmail via bridge). Use when operator requests email. Not for other providers without driver. Uses Bash/Write for Proton Bridge driver operations via run_registered.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `local-maintenance`    | local   | Systematic Linux system maintenance by IA agent: hygiene, updates, ordering, optimization and suggestions. Graduated modes (health-check/quick audit, complete audit, routine, optimization, cleanup) with read-only execution by default, deterministic command validation by risk level, reversible snapshots and system health KPIs (health score 0-100, P0-P4 findings, system fingerprint, temporal diff). Defensive security (hardening, records/forensics, vulns, scans, AppArmor) NOT this skill: handled by sister local-security skill. Use when asked: auditing a Linux system, health-check, OS health status, routine review, cleaning packages/caches/logs, orphan pacman/AUR, boot or resource optimization, or periodic maintenance of Arch/EndeavourOS/CachyOS/Debian/RHEL. Includes guided interaction to select objective, mode and depth according to context. Not for defensive security hardening or forensics (→ local-security). Uses Bash/Write for host mutations only via run_registered. |
| `local-security`       | local   | Defensive Linux host security: posture, light forensic record management, CVEs, sysctl/SSH hardening, AppArmor/SELinux, auditd and fail2ban. Use when the operator requests system security audit, host hardening or auth log review. Not for application code vulnerabilities (→ web-owasp) nor disk cleanup (→ local-maintenance). Uses Bash/Write for host hardening only via run_registered.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `plan-continue`        | plan    | Autoworkspace orchestrator: continue from roadmap or .autoworkspace status; when missing, audit the repo, scaffold project.yaml/status.yaml, and route DEFINE→SCHEMAS→IMPLEMENT→VALIDATE→INTEGRATE→STATUS. Use when asking where to start, plan mode, repo starting, or bringing a project up to date. Not for release close or version publication (→ project-publish). Uses Write/Bash to scaffold .autoworkspace and run phase routing.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `plan-specification`   | plan    | Write a structured specification before writing any code, then decompose it into small verifiable tasks with explicit acceptance criteria. The spec is the shared source of truth — it defines what we build, why, and how we know it is done. Use when starting a project or feature, when requirements are ambiguous, or when the change touches multiple modules. Not for single-line fixes or typo corrections. Uses Write/Bash for SPEC/PLAN/TASKS and local validation.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `plan-validators`      | plan    | Drive implementation and QA with integrated tests: red-green-refactor, bug reproduction, test strategy, quality metrics and behavior coverage for routes, functions and jobs. Use when implementing or changing behavior, writing or reviewing tests, or planning coverage. Not for pure configuration, documentation or static content changes, nor production host debugging (→ local-maintenance). Uses Write/Bash for red/green project test suites.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `project-architecture` | project | Code architecture verification and analysis. Use when analyzing code structure, dependencies, architectural drift, or refactoring opportunities. Use when the operator requests architectural analysis, dependency mapping, or code health assessment. Not for security code review (→ web-owasp) nor SCA/CVE dependency audits (→ project-libraries); minor implementation without architecture analysis uses role-* skills.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `project-libraries`    | project | Dependency audit (SCA/CVE): multi-language pipeline (npm/pip/cargo/go/maven/gradle/composer/gem) to detect vulnerabilities, malware, typosquatting, unused dependencies and outdated. Use when performing dependency audit, SCA, CVE scanning, supply chain security or SBOM generation. Not for code security review (→ web-owasp) nor web compliance audits (→ web-compliance).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `project-publish`      | project | Close a GitHub repository or work increment with local quality gates, version publication, CI/CD audit, Husky, lint-staged, tests, e2e, PR and merge-watch. Use when configuring or running pre-commit/pre-push gates, publishing versions, or closing a plan. Not for implementing product features, test authorship (→ plan-validators), or forges distinct from github.com. Uses Bash/Write for local gates, git/gh publish via run_registered.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `role-back`            | role    | Specialist role for backend application work: data at rest and in motion, routes, deployments, robustness and application security. Includes general patterns for cache/KV, queues, rate limiting, object storage and search (Upstash and equivalents as providers). Use when implementing APIs, persistence, jobs or server-side integrations. Not for host hardening (→ local-security), OWASP code audit (→ web-owasp), or dependency SCA (→ project-libraries). Uses Bash/Write to implement and mutate backend code.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `role-clean-code`      | role    | Implements Clean Code principles to write expressive, maintainable software and refactor existing code safely in any language. Use when the operator asks for 'clean code', 'código limpio', refactoring, meaningful names, smaller functions, fewer code smells, or cleanup of duplicated logic. Not for architecture-only assessments (→ project-architecture), test-suite audits (→ plan-validators), or security reviews (→ web-owasp). Uses Bash/Write for mutative refactoring.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `role-design`          | role    | Specialist role for UI/UX and visual systems: intentional visual direction, typography, palette, motion, clean indented CSS, design tokens (DTCG/Style Dictionary), Tailwind v4 and reusable components. Use when designing or redesigning interfaces, building a design system, or polishing interaction. Not for a11y/SEO audits (→ web-compliance) nor frontend application logic (→ role-front). Uses Bash/Write to mutate tokens, CSS and visual surfaces.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `role-front`           | role    | Specialist role for frontend application work: UI stability, browser compatibility, state coherence across routes, and clear communication contracts between client and server. Use when implementing or fixing frontend features, client state, routing surfaces or interaction flows. Not for visual direction or design tokens (→ role-design), a11y/SEO audits (→ web-compliance), or performance audits (→ web-performance). Uses Bash/Write to implement and mutate frontend code.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `web-compliance`       | web     | Web compliance audit: accessibility (WCAG 2.2 AA / EN 301 549), legal (GDPR, Consent Mode v2, privacy policy, cookies), SEO on-page/off-page/SEM/analytics. PASS/FAIL/N/A matrix, weighted scoring, web compliance verdict POSITIVE/NEGATIVE/PARTIAL and remediation plan RICE. Use when auditing web compliance, dictating web compliance or remediation plan for SEO/accessibility/legal. Not for performance audits (→ web-performance) nor dependency scanning (→ project-libraries).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `web-owasp`            | web     | Code security review (OWASP): injection, XSS, authn/authz, cryptography, SSRF, secrets and misconfiguration. Use when performing security review, OWASP or searching for vulnerabilities in this code. Not for dependency CVEs (→ project-libraries) nor web compliance (→ web-compliance).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `web-performance`      | web     | Web performance audit: Core Web Vitals (LCP, INP, CLS), Lighthouse 12, TTFB/FCP, rendering (SSR/SSG/ISR/islands), caching HTTP/CDN, load optimization and technical frontend diagnosis. Use when performing performance audit, Lighthouse/CWV, load optimization, stability visual, caching or technical frontend diagnosis. Not for compliance audits (→ web-compliance) nor backend load testing.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

<!-- SKILL-INDEX:END -->

Al iniciar un plan y antes de cada tarea o acción independiente, reevalúa el
alcance e invoca todos los roles aplicables. Las invocaciones anteriores no
cubren acciones posteriores; el trabajo mixto exige contratos y handoffs entre
roles.

## Nomenclatura y frontmatter

- Estructura plana: `skills/<nombre-de-la-skill>/SKILL.md`.
- El campo `name` es idéntico al nombre del directorio: `<dominio>-<slug>` en kebab-case. El prefijo es el dominio (normativo, no orientativo).
- El frontmatter lleva exactamente 6 claves: `name`, `description` (alcance y límites), `license: MIT`, `compatibility: "cursor, pi"`, `allowed-tools` y `metadata` con `author`, `version` (semver), `domain`, `type`, `keywords` y `language: en`. Opcional en metadata: `execution: <tool_id>` (referencia al registry central).
- Conjunto cerrado de tipos: `atomic` (una sola capacidad) · `orchestrator` (flujo de varios pasos) · `router` (deriva a otras skills) · `audit` (evaluación de solo lectura con informe).
- Máximo de `allowed-tools` por tipo (mínimo privilegio; gate en `skill_spec.py`): `audit` → Read, Grep, Glob; `atomic` → Read, Write, Grep, Glob (+ Bash si muta); `orchestrator` → Read, Grep, Glob, Bash, Write; `router` → Read, Glob.

## Añadir una nueva skill

Crea un directorio de primer nivel (estructura plana, sin anidamiento):

```bash
mkdir -p skills/<nombre-de-la-skill>
```

Incluye `SKILL.md` con el frontmatter estándar:

```yaml
---
name: <nombre-de-la-skill>
description: >-
  Qué hace. Use when the operator requests it. Not for other families.
license: MIT
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob"
metadata:
  author: Soluciones-Alexendros
  version: 1.0.0
  domain: plan
  type: audit
  language: en
  keywords: <nombre-de-la-skill>
---
```

Para skills mutadoras, usa el set permitido por tipo y, si hay ops en el registry, `metadata.execution: <tool_id>`.

El cuerpo debe incluir `## Overview` y `## When to Use`. Las skills que empaquetan scripts ejecutables también incluyen `## Tools` y `scripts/tests/smoke_sh.sh`.

## Referencias cruzadas

Las flechas (`→ otra-skill`) de las descripciones deben apuntar a una skill existente en este catálogo.

## Canon de flota

Este repositorio aloja el contrato P0/P1 de la flota. Índice rápido:

| Pieza                 | Ruta                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------- |
| ADRs                  | [`docs/architecture/decisions/`](docs/architecture/decisions/) (ADR-0001…; host: ADR-0016; execution: ADR-0017) |
| Reutilización         | [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md)                                                                |
| Callers por stack     | [`stacks/`](stacks/)                                                                                            |
| Reusables CI          | [`.github/workflows/reusable-*.yml`](.github/workflows/)                                                        |
| Plantilla de producto | [`templates/product/`](templates/product/) — `gh repo create … && cp -a templates/product/. <repo>/`            |
| Glosario              | [`docs/GLOSARIO.md`](docs/GLOSARIO.md) — un término canónico por concepto                                       |

Norma de planes (plantilla en `docs/` + carpeta `docs/plans/`) llegan en T2. Rulesets como código llegan con P2/P10 (`rulesets/`).

## Validación

```bash
bash run-validation.sh
# o: make validate && make test && make smoke
```

Comprueba: esquema del frontmatter, cláusulas de alcance de las descripciones, canon de encabezados, paridad del catálogo entre carpetas, README y TAXONOMY, resolución de referencias y smoke tests.
