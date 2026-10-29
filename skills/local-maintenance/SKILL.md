---
name: local-maintenance
description: "Systematic Linux system maintenance by IA agent: hygiene, updates, ordering, optimization and suggestions. Graduated modes (health-check/quick audit, complete audit, routine, optimization, cleanup) with read-only execution by default, deterministic command validation by risk level, reversible snapshots and system health KPIs (health score 0-100, P0-P4 findings, system fingerprint, temporal diff). Defensive security (hardening, records/forensics, vulns, scans, AppArmor) NOT this skill: handled by sister local-security skill. Use when asked: auditing a Linux system, health-check, OS health status, routine review, cleaning packages/caches/logs, orphan pacman/AUR, boot or resource optimization, or periodic maintenance of Arch/EndeavourOS/CachyOS/Debian/RHEL. Includes guided interaction to select objective, mode and depth according to context. Not for defensive security hardening or forensics (→ local-security)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)

  version: "7.0.0-alpha.0"

  domain: local
  type: atomic
  language: en
  keywords: local-maintenance
  health: integrated
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
disable-model-invocation: true
---

# Local Maintenance

## Overview

Systematic Linux system maintenance by an IA agent: hygiene, updates, ordering, optimization and
suggestions. Graduated modes (quick/complete audit, routine, optimization, cleanup) with
read-only execution by default, deterministic command validation by risk level, reversible
snapshots and system health KPIs. Defensive security (hardening, records/forensics, vulnerabilities,
scans, AppArmor) is NOT this skill: handled by sister local-security skill. Use when asked:
auditing a Linux system, routine review, cleaning packages/caches/logs, orphan pacman/AUR,
boot or resource optimization, OS health-check, or periodic maintenance of Arch/EndeavourOS/
CachyOS/Debian/RHEL. Includes guided interaction to select objective, mode and depth according
to context.

## When to Use

- When asked to audit a Linux system
- For routine review
- For cleaning packages/caches/logs
- For pacman/AUR orphans
- For boot or resource optimization
- For OS health-check
- Periodic maintenance of Arch/EndeavourOS/CachyOS/Debian/RHEL

## Not for:

- Hardening/forensics (→ local-security)

## Graduated Modes

| Mode           | Description                                      |
| -------------- | ------------------------------------------------ |
| Health-check   | Fingerprint + quick audit (P0+P1) + Health Score |
| Complete audit | Full audit P0-P4 + Health Score + diff temporal  |
| Routine        | Scheduled routine maintenance                    |
| Optimization   | Resource and boot optimization                   |
| Cleanup        | Clean caches, logs and orphan packages           |

## Tools

- `scripts/check_deps.py` — dependency check.
- `scripts/probe_system.py` — system fingerprint (read-only, feeds the audit).
- `scripts/audit_quick.py` — read-only health-check (P0+P1).
- `scripts/audit_full.py` — complete audit (P0-P4) + health score.
- `scripts/snapshot_state.py` — reversible state snapshot.
- `scripts/risk_gate.py` — deterministic risk validation.
- `scripts/clean_routine.py` — cleanup routine.
- `scripts/report_render.py` — report rendering (HTML/Markdown/JSON).
- `scripts/session_logger.py` — session logging.
- `scripts/common.py` — shared helpers (checks, findings collector, scoring).

## Health Integration

The standalone health capability was merged here: measuring health is the
first phase of maintaining a system, and the audit output is the input the rest of the
pipeline acts on.

```
probe_system.py  →  audit_quick.py / audit_full.py  →  report_render.py  →  remediación
(fingerprint)       (hallazgos P0-P4, solo lectura)    (informe + score)    (routine/optimize/clean)
```

- **Health phase is read-only.** No script in the audit path modifies the system. Writing
  modes (`routine`, `optimize`, `clean`) require `snapshot_state.py` + `risk_gate.py`.
- **Health Score (0-100)** = weighted sum of 5 categories: security 35, updates 25,
  hygiene 20, resources 10, stability 10. Each category averages its findings
  (PASS 100, WARN 40, FAIL 0) weighted by severity (P0 x8, P1 x4, P2 x2, P3/P4 x1);
  SKIP/ERROR do not score, so a non-applicable check never penalizes.
- **`stability`** holds journal/boot error volume (LOG-06/LOG-08); it no longer drags
  `security`, which only covers exposure checks (NET-04). Pure hardening (SSH/KR/FS-05-08/
  AU/UA/CR/FW/SD) stays in `local-security`.
- Bands: 90-100 Excellent, 70-89 Good, 50-69 Fair, 0-49 Critical.
