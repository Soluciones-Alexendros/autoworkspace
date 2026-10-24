---
name: plan-continue
description: "Autoworkspace orchestrator: continue from roadmap or .autoworkspace status; when missing, audit the repo, scaffold project.yaml/status.yaml, and route DEFINE→SCHEMAS→IMPLEMENT→VALIDATE→INTEGRATE→STATUS. Use when asking where to start, plan mode, repo starting, or bringing a project up to date. Not for release close or version publication (→ project-publish)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "4.3.1"
  domain: plan
  type: orchestrator
  language: en
  keywords: plan-continue
compatibility: opencode, codex, cursor, copilot
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Plan Continue

## Overview

Continue according to the planned roadmap and the declarative Autoworkspace
status. When none exists, analyze the repository, scaffold `.autoworkspace/`,
and reason the next pipeline phase. Framework-specific decisions cite official
documentation.

## When to Use

- Operator asks where to start or opens plan mode
- Repo starting / bring a project up to date
- Drive work from `.autoworkspace/status.yaml`, `tasks/`, or a roadmap
- Mix of audit then continue implementation

**When NOT to use:** Release close or version publication (→ project-publish);
writing a fresh multi-module spec from scratch without orchestration
(→ plan-specification alone).

## Autoworkspace pipeline

```text
DEFINE → SCHEMAS → IMPLEMENT → VALIDATE → INTEGRATE → STATUS
```

1. Ensure `.autoworkspace/project.yaml` and `status.yaml` exist (copy from
   `templates/autoworkspace/` or run the router once).
2. Route the current phase:

```bash
# workspace-required: needs full checkout (skills/ + tools/workspace-router)
python tools/workspace-router/run.py --phase DEFINE --repo . --json
# first-time scaffold only:
python tools/workspace-router/run.py --init --repo .
```

3. Invoke the skill returned (`skill` field). Route does not execute the skill.
   Completing a phase requires verified evidence (see execution.yaml); legacy `--bump` is rejected.

| Phase     | Typical skill                                          | Output                                 |
| --------- | ------------------------------------------------------ | -------------------------------------- |
| DEFINE    | plan-specification                                     | Spec + tasks                           |
| SCHEMAS   | plan-continue (acceptance schemas)                     | `.autoworkspace/schemas/` + test stubs |
| IMPLEMENT | role-front / role-back / role-design / role-clean-code | Code                                   |
| VALIDATE  | plan-validators                                        | Red-green-refactor + integrated tests  |
| INTEGRATE | project-publish                                        | Local gates / CI / release handoff     |
| STATUS    | plan-continue                                          | `status.yaml` bump + ESTADO board      |

The phase router returns one typical skill as a fallback; it never replaces
per-task role selection. At plan start and before every task or independent
implementation action, re-evaluate the current surface and invoke all matching
roles: backend/API/jobs → role-back, frontend/client routes → role-front,
visual direction/tokens → role-design, and clean-code/refactoring →
role-clean-code. Repeat this even when the previous action used another role.
Mixed work requires explicit contracts and handoffs between all matching roles.

## Process

### 1. Detect existing plan / status

Look for `.autoworkspace/status.yaml`, `tasks/plan.md`, `tasks/todo.md`,
`ESTADO.md`, roadmap docs, or an active work branch.

- **Status/roadmap present** → route the current `phase` and continue.
- **None** → repository analysis, then scaffold `.autoworkspace/` and DEFINE.

### 2. Repository analysis (when no roadmap)

1. Sync clone with remote
2. Status board via `inicio_plan.py` (P0/P1/P2, Renovate, CI)
3. Contrast with repo-standard; apply unblockers
4. Write evolution plan; hand off to DEFINE if needed

Detail: [inicio-plan.md](references/inicio-plan.md).

### 3. SCHEMAS after approved spec

From the approved spec, write acceptance schemas and failing test stubs under
`.autoworkspace/schemas/` (and the project's test tree). Then IMPLEMENT with
recurrent role routing and VALIDATE with → plan-validators.

### 4. Source-backed decisions

Detect stack versions, fetch official docs for the feature page, cite sources.
Guides: [source-guide.md](references/source-guide.md),
[citation-guide.md](references/citation-guide.md).

### 5. Handoff

- Publish / close → → project-publish
- «Audítalo y publícalo» → analysis here, then → project-publish
- Supply-chain before new deps → → project-libraries

## Tools

- `scripts/scan_repo.py` — repository scan (secret findings: path/line/fingerprint only)
- `scripts/audit-repo.sh` — repo audit
- `scripts/check-product-structure.sh` — product structure check
- `scripts/inicio_plan.py` — plan initialization / status board
- `../../tools/workspace-router/run.py` — phase router + status bump

## References

- [inicio-plan.md](references/inicio-plan.md) — plan start / repo starting
- [plantilla-informe.md](references/plantilla-informe.md) — report template
- [source-guide.md](references/source-guide.md) — authority hierarchy
- [citation-guide.md](references/citation-guide.md) — citation formats
- [verification-guide.md](references/verification-guide.md) — checklist
