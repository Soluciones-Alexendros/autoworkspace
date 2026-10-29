---
name: <domain>-<slug>
description: >-
  What it does in English. Use when the operator asks for "trigger en español", "otro trigger", "English trigger". Not for other family (→ other-skill).
license: MIT
compatibility: "cursor, pi"
metadata:
  author: "Soluciones-Alexendros"
  version: "1.0.0"
  domain: "local"
  type: "atomic"
  language: "en"
  keywords: "keyword1, keyword2, español, trigger"
  # execution: <tool_id>   # only if tools/execution/registry.yaml has this tool
allowed-tools: "Read, Grep, Glob"
---

## Overview

One paragraph: what this skill produces and why.

## When to Use

- Use when: ...
- Keywords: mantenimiento, limpieza, etc.
- Do NOT use when: health-check audit or hardening (→ local-security)

## Process

1. Prerequisite: Check...
2. Read `references/...` if needed
3. Execute via scripts/... (mutating ops only through `run_registered`)
4. Produce report in ...

## Tools

| Script                  | Purpose             | Mode       |
| ----------------------- | ------------------- | ---------- |
| `scripts/check_deps.py` | Verify dependencies | pre-flight |
| `scripts/main.py`       | Main logic          | all        |

## References

- `references/safety-policy.md` — risk levels R0-R3
- `references/guided-interaction.md` — 4-phase flow

## Examples

> "Ejecuta mantenimiento semanal: muestra plan en dry-run antes de ejecutar"
> "Audita mi sistema y dame plan P1-P4 sin ejecutar"

## Structure

- `SKILL.md` — this file (<200 lines)
- `references/` — deep docs
- `scripts/` — deterministic helpers
- `assets/` — templates
- Do **not** add `execution.yaml` here — use `tools/execution/registry.yaml`

## allowed-tools matrix (minimum privilege)

| `metadata.type` | Maximum `allowed-tools`                          | Notes                       |
| --------------- | ------------------------------------------------ | --------------------------- |
| `audit`         | `Read, Grep, Glob`                               | Never `Write` or `Bash`     |
| `atomic`        | `Read, Write, Grep, Glob` (+ `Bash` if mutating) | Justify Bash in description |
| `orchestrator`  | `Read, Grep, Glob, Bash, Write`                  | Justify in description      |
| `router`        | `Read, Glob`                                     | No domain mutation          |

Audit skills have **no** `metadata.execution` and **no** registry entry.
