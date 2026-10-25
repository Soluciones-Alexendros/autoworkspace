# Skill Spec v3.0 — Estándar OpenCode

## Frontmatter (6 keys permitidas)

- name: kebab-case, == dirname, ≤64
- description: 1-1024 chars, formato: What it does + Use when + Not for → other-skill
- license: MIT
- compatibility: "opencode, codex, cursor, copilot"
- metadata: map string→string con author, version, domain, type, language, keywords
- allowed-tools: space-separated experimental, ej "Read, Grep, Bash"

No se permiten otras keys top-level.

## Domains

build, design, operate, planning, verify

## Types

atomic, orchestrator, router, audit

## Body headings canónicos

## Overview

## When to Use

## Process

## Tools

## References

## Examples

## Progressive disclosure

SKILL.md <200 líneas. Detalle en references/, scripts/, assets/

## Validation

bash run-validation.sh checks: frontmatter whitelist, name==dir, description length, metadata strings, references exist, arrows resolve, compatibility includes opencode
