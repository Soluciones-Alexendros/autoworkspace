# Architecture

### Propósito de este documento

- **Objetivos:** Describir el producto autoworkspace (pipeline agéntico), el árbol de skills y tools, las capas del canon/CI de flota, y cómo se valida.
- **Estructura:** Esta meta-sección → producto → árbol → pipeline → capas canon/CI → CI → supply chain.
- **Contenido a integrar según contexto:** Contratos de fase en `.autoworkspace/`; canon de flota en `docs/architecture/`, `stacks/` y `templates/repo/`.

## Producto

**autoworkspace** is an agentic pipeline for Soluciones-Alexendros, not a skill showcase. Operators route work through skills under `skills/` and declarative project status under `.autoworkspace/`. There is no production web deploy: the deliverable is the skill catalog, validators, routers, and (from P11) the **fleet canon** previously hosted in `repo-standard`.

## Tree

| Path                           | Role                                                       |
| ------------------------------ | ---------------------------------------------------------- |
| `skills/<name>/`               | One skill per folder; `SKILL.md` is the contract           |
| `tools/`                       | Routers, validators, versioning, execution layer           |
| `docs/`                        | Product docs + fleet ADRs, guides, runbooks, REUTILIZACION |
| `docs/architecture/decisions/` | ADR-0001… (fleet) + ADR-0016 (host)                        |
| `stacks/`                      | CI callers per runtime (pin reusable by SHA)               |
| `.github/workflows/`           | `ci.yml` + reusables + quality/validate/version/release    |
| `templates/repo/`              | Product P0/P1 skeleton (copy into a new repo)              |
| `templates/autoworkspace/`     | Scaffolding for `.autoworkspace/`                          |

Sixteen skills in five domains: `plan`, `local`, `project`, `web`, `role`.

## Pipeline

```text
DEFINE → SCHEMAS → IMPLEMENT → VALIDATE → INTEGRATE → STATUS
```

Phase routing:

```bash
python tools/workspace-router/run.py --phase DEFINE --repo . --json
```

Per-task role selection (backend / front / design / clean-code) is mandatory when the surface matches; the phase router skill is only a fallback.

## Capas canon / CI

1. **Contrato de flota** — `templates/repo/AGENTS.md` §1–8; este repo declara cumplimiento en `AGENTS.md`.
2. **ADRs** — `docs/architecture/decisions/` (ci-gate, squash auto-merge, SemVer del contrato, packaging).
3. **Reusables** — `.github/workflows/reusable-{node,rust,python,static}.yml` llamados por SHA desde `stacks/<stack>/ci.yml`.
4. **Caller local** — `.github/workflows/ci.yml` con job `ci-gate` (nombre exacto) que agrega pipeline + hygiene + validate (y, hasta P2, check-bump vía workflow aparte required).
5. **Plantilla de producto** — `templates/repo/` (sustituye «Use this template» de `repo-standard`).

## Continuous integration

| Workflow         | Job(s)                                                                                                                  | Role                                                                    |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `ci.yml`         | `pipeline-python`, `pipeline-node`, `canon`, `caller-reusable-path`, `hygiene`, `validate`, `check-bump`, **`ci-gate`** | Caller local + gate agregado (`ci-gate.needs` con los siete anteriores) |
| `quality.yml`    | `hygiene`                                                                                                               | Required clásico hasta P9                                               |
| `validate.yml`   | `validate`                                                                                                              | Required clásico hasta P9                                               |
| `version.yml`    | `check-bump`                                                                                                            | Skill `metadata.version` bump on PRs (hasta P2)                         |
| `release.yml`    | `publish`, `provenance`                                                                                                 | Tag cut, GitHub Release y atestación on `main`                          |
| `security.yml`   | `actionlint`                                                                                                            | Workflow lint                                                           |
| `reusable-*.yml` | `quality`, `test`, `build`, `smoke`, `e2e`, `link-check`, `security` (según stack)                                      | Reusables llamados por SHA desde `stacks/<stack>/ci.yml`                |

Local equivalents: `make validate`, `make lint`, `make test`, `make smoke`.

## Supply chain

- Dependency version updates: [Renovate](.github/renovate.json) only.
- Dependabot may keep **security alerts** on; do not add `dependabot.yml` for version PRs.
- Actions pinned by commit SHA; workflow `permissions` are explicit.
