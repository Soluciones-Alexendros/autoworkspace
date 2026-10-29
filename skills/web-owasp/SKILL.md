---
name: web-owasp
description: "Code security review (OWASP): injection, XSS, authn/authz, cryptography, SSRF, secrets and misconfiguration. Use when performing security review, OWASP or searching for vulnerabilities in this code. Not for dependency CVEs (→ project-libraries) nor web compliance (→ web-compliance)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "7.0.0-alpha.0"
  domain: web
  type: atomic
  language: en
  keywords: web-owasp
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Web OWASP

## Overview

Code security review (OWASP): injection, XSS, authn/authz, cryptography, SSRF, secrets
and misconfiguration. Use when performing security review, OWASP or searching for vulnerabilities
in this code.

## When to Use

- When security review is requested
- To search for vulnerabilities in code
- OWASP security review

## Not for:

- OS hardening (→ local-security)
- Release closure (→ project-publish)
- Dependency audit/SCA (→ project-libraries)

## Normative edition

Declare and verify against a single official edition before mapping findings.
Default for this skill: **OWASP Top 10:2021** ([owasp.org/Top10](https://owasp.org/Top10/)).
Identifiers below follow 2021 labels. Do not mix editions in one report.
LLM/API Top 10 projects are separate; cite them only when that scope is explicit.

## OWASP Top 10:2021 categories (checklist, not certification)

### A01:2021 Broken Access Control

### A02:2021 Cryptographic Failures

### A03:2021 Injection

- SQL, NoSQL, OS injection, XSS as injection class where applicable
- Prevention: parametrized queries, input validation, output encoding

### A04:2021 Insecure Design

### A05:2021 Security Misconfiguration

- Default credentials, verbose errors, missing patches

### A06:2021 Vulnerable and Outdated Components

- Cross-check with → project-libraries for dependency SCA

### A07:2021 Identification and Authentication Failures

- Session handling, weak credentials, MFA, account lockout

### A08:2021 Software and Data Integrity Failures

### A09:2021 Security Logging and Monitoring Failures

### A10:2021 Server-Side Request Forgery (SSRF)

## Best Practices

- Input validation everywhere
- Output escaping
- Security headers (CSP, HSTS)
- Secure secret management
