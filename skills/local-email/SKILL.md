---
name: local-email
description: "Email local con drivers (proton, gmail via bridge). Use when operator requests email. Not for other providers without driver. Uses Bash/Write for Proton Bridge driver operations via run_registered."
license: MIT
metadata:
  author: "Soluciones-Alexendros (adapted)"
  version: "7.0.0-alpha.1"
  domain: local
  type: atomic
  language: en
  keywords: local-email
  execution: local-email
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob, Bash, Write"
disable-model-invocation: true
---

# Local Email

## Overview

Local email with drivers. The Proton driver is the one that runs today (Bridge IMAP/SMTP and Proton Pass). Gmail via bridge has no driver yet: stop and say so. Do not use a provider that has no driver.

## When to Use

- When reading Proton Mail emails
- To search messages by sender or organization
- To classify email by case (court, registry, TGSS, notary, SMAC)
- To obtain tokens, passwords and API keys from Proton Pass
- To send emails from the Proton account

## Not for:

- Other email providers
- CI/GitHub secrets

## Workflow

```text
Read email
       │
       ▼
Search by sender
       │
       ▼
Classify by case
       │
       ▼
Obtain secrets
       │
       ▼
Send email
```

## Tools

- `scripts/proton_bridge.py` — delegates to `tools/email/drivers/proton/proton_bridge.py`.
