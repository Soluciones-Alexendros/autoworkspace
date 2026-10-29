---
name: local-security
description: "Defensive Linux host security: posture, light forensic record management, CVEs, sysctl/SSH hardening, AppArmor/SELinux, auditd and fail2ban. Use when the operator requests system security audit, host hardening or auth log review. Not for application code vulnerabilities (→ web-owasp) nor disk cleanup (→ local-maintenance)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)

  version: "7.0.0-alpha.0"

  domain: local
  type: atomic
  language: en
  keywords: local-security
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
disable-model-invocation: true
---

# Local Security

## Overview

Defensive Linux host security: posture, light forensic record management, CVEs, sysctl/SSH
hardening, AppArmor/SELinux, auditd and fail2ban. Use when the operator requests system
security audit, host hardening or auth log review. Not for application code vulnerabilities
(→ web-owasp) nor disk cleanup (→ local-maintenance).

## When to Use

- System security audit
- Host hardening
- Auth log review

## Not for:

- Application code vulnerabilities (→ web-owasp)
- Disk cleanup (→ local-maintenance)

## Components

| Component        | Description                 |
| ---------------- | --------------------------- |
| Posture          | Security posture assessment |
| CVEs             | Vulnerability tracking      |
| sysctl           | System parameter hardening  |
| SSH              | SSH server hardening        |
| AppArmor/SELinux | Mandatory access control    |
| auditd           | Audit daemon configuration  |
| fail2ban         | Brute force protection      |

## Tools

- `scripts/postura_seguridad.sh` — defensive posture snapshot.
- `scripts/forense_collector.py` — log forensics collection.
- `scripts/vulns_check.py` — vulnerability check.
- `scripts/harden_plan.py` — hardening plan.
- `scripts/scan_orchestrator.py` — malware/rootkit scan orchestration.
- `scripts/apparmor_lifecycle.py` — AppArmor profile lifecycle.
