---
name: project-libraries
description: "Dependency audit (SCA/CVE): multi-language pipeline (npm/pip/cargo/go/maven/gradle/composer/gem) to detect vulnerabilities, malware, typosquatting, unused dependencies and outdated. Use when performing dependency audit, SCA, CVE scanning, supply chain security or SBOM generation. Not for code security review (→ web-owasp) nor web compliance audits (→ web-compliance)."
license: MIT
metadata:
  author: "Soluciones-Alexendros (adapted)"
  version: "7.0.0"
  domain: project
  type: audit
  language: en
  keywords: project-libraries
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob"
---

# Project Libraries

## Overview

Dependency audit (SCA/CVE): multi-language pipeline (npm/pip/cargo/go/maven/gradle/composer/gem)
to detect vulnerabilities, malware, typosquatting, unused dependencies and outdated. Use when
performing dependency audit, SCA, CVE scanning, supply chain security or SBOM generation.

## When to Use

- When dependency audit is requested
- For SCA (Software Composition Analysis)
- For CVE (Common Vulnerabilities and Exposures) scanning
- For supply chain security
- For SBOM (Software Bill of Materials) generation

## Not for:

- Code OWASP review (→ web-owasp)
- OS hardening (→ local-security)
- Disk cleanup (→ local-maintenance)

## Supported Pipeline

| Language                                   | Dependency File                              |
| ------------------------------------------ | -------------------------------------------- |
| npm/pip/cargo/go/maven/gradle/composer/gem | package.json, requirements.txt, go.mod, etc. |

## What It Detects

- Vulnerabilities (CVE)
- Malware
- Typosquatting
- Outdated dependencies
- Unused dependencies

## SBOM Generation

- Complete list of all dependencies
- Exact versions
- Licenses
- Metadata for each package
