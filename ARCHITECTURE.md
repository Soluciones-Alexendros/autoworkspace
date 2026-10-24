# Architecture

### Propósito de este documento

- **Objetivos:** Describir el producto autoworkspace (pipeline agéntico), el árbol de skills y tools, y cómo se valida en CI.
- **Estructura:** Esta meta-sección → producto → árbol → pipeline → CI → supply chain → exclusiones conscientes.
- **Contenido a integrar según contexto:** Contratos de fase en `.autoworkspace/`; canon de flota en [docs/repo-standard/](docs/repo-standard/).

## Producto

**autoworkspace** is an agentic pipeline for Soluciones-Alexendros, not a skill showcase. Operators route work through skills under `skills/` and declarative project status under `.autoworkspace/`. There is no production web deploy: the deliverable is the skill catalog, validators, and routers.

## Tree

| Path                 | Role                                             |
| -------------------- | ------------------------------------------------ |
| `skills/<name>/`     | One skill per folder; `SKILL.md` is the contract |
| `tools/`             | Routers, validators, versioning, execution layer |
| `docs/`              | Product docs and embedded `repo-standard`        |
| `.github/workflows/` | Quality, validate, version, release              |
| `templates/`         | Scaffolding for `.autoworkspace/`                |

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

## Continuous integration

This repo uses **separate workflows** instead of a single `ci.yml` (the repo-standard product tree prefers one file with jobs `quality` → `test` → `build?` → `smoke`). Required behavior is preserved under stable job names:

| Workflow       | Job(s)                   | Role                                                                  |
| -------------- | ------------------------ | --------------------------------------------------------------------- |
| `quality.yml`  | `hygiene`                | Tracked residues, secrets hygiene, bash `-n`                          |
| `validate.yml` | `validate`               | Spec, links, release coherence, pytest, smoke via `run-validation.sh` |
| `version.yml`  | `check-bump`             | Skill `metadata.version` bump on PRs                                  |
| `release.yml`  | `publish` (+ provenance) | Tag cut and GitHub Release on `main` / tags                           |

Local equivalents: `make quality`, `make validate`.

There is no `build` job: there is no compiled artifact to publish beyond the git tree and release notes.

## Supply chain

- Dependency version updates: [Renovate](.github/renovate.json) only.
- Dependabot may keep **security alerts** on; do not add `dependabot.yml` for version PRs.
- Actions pinned by commit SHA; workflow `permissions` are explicit.

## Conscious exclusions vs product P1 checklist

- **No `.env.example`:** skills and tools do not declare a runtime env contract for a deployed app. Host secrets stay in the operator environment or Proton Pass (`local-proton`).
- **No single `ci.yml`:** see table above; renaming would break required checks.
- **No `docs/architecture|guides|runbooks` tree yet:** product docs live under `docs/` and `docs/repo-standard/`; expand when runbooks are needed.
