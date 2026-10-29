---
name: plan-specification
description: "Write a structured specification before writing any code, then decompose it into small verifiable tasks with explicit acceptance criteria. The spec is the shared source of truth — it defines what we build, why, and how we know it is done. Use when starting a project or feature, when requirements are ambiguous, or when the change touches multiple modules. Not for single-line fixes or typo corrections."
license: MIT
metadata:
  author: addyosmani (adapted)
  version: "7.0.0-alpha.0"
  domain: plan
  type: orchestrator
  language: en
  keywords: plan-specification
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Plan Specification

## Overview

Write a structured specification before writing any code, then break it into
small, verifiable tasks. The spec is the shared source of truth between you and
the human engineer. Code without a spec is guessing; a plan without sized tasks
is a tangled mess.

## When to Use

- Starting a new project or feature
- Requirements are ambiguous or incomplete
- The change touches multiple files or modules
- Work must be parallelized or ordered by dependency

**When NOT to use:** Single-line fixes, typo corrections, or changes where
requirements are unambiguous and already well-defined as tasks.

## Process

Four phases, preceded by a scope check (Phase 0) when one request bundles
several independently testable capabilities. Do not advance until the current
phase is validated.

```text
SPECIFY ────→ PLAN ────→ TASKS ────→ IMPLEMENT
```

### Phase 0: Scope Check

Skip when the request describes one capability. Detect multi-capability bundles
when distinct capabilities have their own consumers or data, acceptance criteria
cluster into separately shippable groups, or one capability could be cut without
rewriting the others. Propose a capability map (stable kebab-case ids, one-way
dependencies) before writing any module spec. Detail: [spec-templates.md](references/spec-templates.md).

### Phase 1: Specify

Surface assumptions immediately (stack, auth, data store, platform). Write a
spec covering Objective, Commands, Project Structure, Code Style, Testing
Strategy, Boundaries, Success Criteria and Open Questions. Template:
[spec-templates.md](references/spec-templates.md).

**Stop after writing the spec.** Summarize, ask for approval, and STOP the turn.
Planning starts only after the human approves in a later turn.

### Phase 2: Plan

With the validated spec, generate a technical plan: major components,
dependencies, order, risks, parallel vs sequential work, verification
checkpoints. Save to `tasks/plan.md`. Human reviews before Tasks.

### Phase 3: Tasks

Decompose into discrete, implementable units (mechanics below). Default task
list target: `tasks/todo.md`. Template: [spec-templates.md](references/spec-templates.md).

### Phase 4: Implement

Execute tasks one at a time following → plan-validators. Before every task or
independent implementation action, re-evaluate its scope and invoke every
matching `role-*` skill, even when a different role handled the previous action.
Load only the spec sections and source files needed per step. Keep the spec alive
when decisions change. Detail: [spec-quality.md](references/spec-quality.md).

## Task Breakdown

Every task should be small enough to implement, test, and verify in a single
focused session.

1. **Plan in read-only mode** — inspect spec and codebase; do not write code.
2. **Map dependencies** — foundations at the bottom, implement bottom-up.
   Graph and sizing: [task-patterns.md](references/task-patterns.md).
3. **Slice vertically** — one complete feature path at a time (schema + API + UI).
4. **Write tasks** — one outcome, acceptance criteria, verification, dependencies,
   implementation roles, test surfaces, likely files, size XS–M. Fields:
   [plan-templates.md](references/plan-templates.md).
5. **Order and checkpoint** — keep the system working after every task; put
   high-risk work early; checkpoint every 2–3 tasks. Same work → update in place;
   different work → stop and ask before touching `tasks/`.

Anti-patterns: [anti-patterns.md](references/anti-patterns.md).

## Recurrent Role Routing

Every implementation task declares **Implementation roles** and **Test surfaces**.
Select roles at plan start, then repeat the selection before each task or
independent action; an earlier invocation never covers later work.

| Current surface                              | Required role   |
| -------------------------------------------- | --------------- |
| Backend, API, persistence, jobs, queues      | role-back       |
| Frontend, client routes, state, interactions | role-front      |
| Visual direction, tokens, component styling  | role-design     |
| Clean code, refactoring, duplication cleanup | role-clean-code |

For mixed work, invoke all matching roles and define their contracts and handoffs.
Re-evaluate whenever scope changes. Cover every declared route, function, job and
end-to-end flow through → plan-validators and the project's standard test suite.

## Tools

Use Read, Grep, and Glob to inspect before specifying; Write for specs, plans
and task lists; Bash only for the project's own build/test/lint. Related:
→ plan-validators (implementation and integrated-test loop), → plan-continue
(roadmap / repo next steps), → project-libraries (supply-chain before adding dependencies).

## References

- [spec-templates.md](references/spec-templates.md) — capability map, assumptions, spec and task templates.
- [spec-quality.md](references/spec-quality.md) — living-spec rules, rationalizations, checklist.
- [task-patterns.md](references/task-patterns.md) — dependency graphs, vertical slicing, sizing.
- [plan-templates.md](references/plan-templates.md) — task fields, checkpoints, plan document.
- [anti-patterns.md](references/anti-patterns.md) — parallelization pitfalls, red flags.
