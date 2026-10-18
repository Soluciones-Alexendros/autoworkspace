---
name: project-publish
description: "Close a GitHub repository or work increment with local quality gates, version publication, CI/CD audit, Husky, lint-staged, tests, e2e, PR and merge-watch. Use when configuring or running pre-commit/pre-push gates, publishing versions, or closing a plan. Not for implementing product features, test authorship (→ plan-validators), or forges distinct from github.com."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "4.3.1"
  domain: project
  type: atomic
  language: en
  keywords: project-publish, husky, lint-staged, pre-commit, release
compatibility: opencode, codex, cursor, copilot
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Project Publish

## Overview

Close a GitHub repository or work increment with one continuous quality and
release flow. Local Husky gates, lint-staged, formatting, typechecking and tests
are prerequisites for the CI/CD, versioning, PR and merge-watch stages. Use for
semantic versioning, Keep a Changelog, Actions supply-chain and post-plan closure.

## When to Use

- Configure or run pre-commit hooks, Husky or lint-staged
- Run the local quality gate before a push, PR or release
- Add formatting, typechecking or tests to pre-commit and e2e to pre-push
- Audit CI/CD, publish a version or close a completed plan

## Not for:

- Implementing product features
- Test strategy or test-case authorship (→ plan-validators)
- Forges distinct from github.com

## Local Gates

1. Follow the repository's existing package manager and quality commands.
2. Keep pre-commit fast: lint-staged, formatting, typecheck and unit tests.
3. When e2e configuration exists, place the appropriate suite in pre-push or run
   it explicitly during work closure; do not invent a second test stack.
4. Run `scripts/gate-husky.sh` against the target repository to install missing
   conventional hooks and execute the gate. A missing optional package script is
   reported and skipped; a failing existing gate blocks closure.

## Closure Flow

```text
End of plan
       │
       ▼
Local Husky + test gates
       │
       ▼
CI/CD audit + e2e when applicable
       │
       ▼
Version publication when requested
       │
       ▼
PR + merge-watch
```

## Tools

- `scripts/gate-husky.sh` — install conventional local hooks and run the pre-commit gate.
- `scripts/review-vs-plan.py` — contrast plan vs execution when closing work.

## References

- [cierre-trabajo.md](references/cierre-trabajo.md) — ordered local gates, PR and merge-watch closure.
