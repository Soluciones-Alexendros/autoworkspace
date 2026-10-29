---
name: web-compliance
description: "Web compliance audit: accessibility (WCAG 2.2 AA / EN 301 549), legal (GDPR, Consent Mode v2, privacy policy, cookies), SEO on-page/off-page/SEM/analytics. PASS/FAIL/N/A matrix, weighted scoring, web compliance verdict POSITIVE/NEGATIVE/PARTIAL and remediation plan RICE. Use when auditing web compliance, dictating web compliance or remediation plan for SEO/accessibility/legal. Not for performance audits (→ web-performance) nor dependency scanning (→ project-libraries)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "7.0.0-alpha.0"
  domain: web
  type: atomic
  language: en
  keywords: web-compliance
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Web Compliance

## Overview

Web compliance audit: accessibility (WCAG 2.2 AA / EN 301 549), legal (GDPR, Consent Mode v2,
privacy policy, cookies), SEO on-page/off-page/SEM/analytics. PASS/FAIL/N/A matrix, weighted
scoring, web compliance verdict POSITIVE/NEGATIVE/PARTIAL and remediation plan RICE. Use when
auditing web compliance, dictating web compliance or remediation plan for SEO/accessibility/legal.

## When to Use

- When web compliance audit is requested
- For web compliance verdict
- For SEO/accessibility/legal remediation plan

## Not for:

- Core Web Vitals (→ web-performance)
- Application security review (→ web-owasp)
- Dependency SCA (→ project-libraries)
- Certifying full GDPR or accessibility compliance from an automated scan alone

## Main Checks

### Accessibility (WCAG 2.2 AA)

- Color contrast
- Alternative text on images
- Keyboard navigation
- Screen readers

### Legal (GDPR)

- Legal notice
- Cookie policy
- Consent Mode v2

### SEO

- On-page factors
- Off-page factors
- SEM configuration

### Analytics

- Tracking configuration
- Key metrics

## Verdict

- **POSITIVE**: Meets critical requirements
- **PARTIAL**: Meets some requirements, others missing
- **NEGATIVE**: Does not meet critical requirements

## RICE Remediation Plan

- **Reach**: How many users affected?
- **Impact**: How much impact does non-compliance have?
- **Confidence**: How confident are you in the fix?
- **Effort**: How much effort does the remedy require?

## Tools

- `scripts/audit_page.py` — audit a page against the checks.
- `scripts/contrast.py` — WCAG contrast verification.
- `scripts/score.py` — weighted scoring.
- `scripts/report.py` — report rendering.
- `scripts/selftest.py` — toolchain self-test.
