---
name: role-front
description: "Specialist role for frontend application work: UI stability, browser compatibility, state coherence across routes, and clear communication contracts between client and server. Use when implementing or fixing frontend features, client state, routing surfaces or interaction flows. Not for visual direction or design tokens (→ role-design), a11y/SEO audits (→ web-compliance), or performance audits (→ web-performance)."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "7.0.0-alpha.0"
  domain: role
  type: atomic
  language: en
  keywords: role-front
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Role Front

## Overview

Specialist agent for frontend application engineering. Replaces vague
«senior frontend» prompts with executable standards: stability under change,
cross-browser compatibility, coherent client state, and explicit communication
contracts with the backend.

## When to Use

- Implementing or fixing UI features, client state, routing or interaction flows
- Ensuring the same data/state stays consistent across pages that share it
- Defining or consuming API contracts from the client side

**When NOT to use:** visual identity or design systems (→ role-design);
compliance/perf audits (→ web-compliance, → web-performance); backend routes
and data stores (→ role-back).

## Standards

### Stability

- Prefer derived state over duplicated stores; one write path per concern
- Empty, loading and error states are first-class, not afterthoughts
- Changes that write state must be verified on every surface that reads it
- Avoid silent fallbacks that hide broken contracts

### Compatibility

- Target the project's documented browser baseline; do not invent one
- Progressive enhancement when the stack allows; feature-detect before polyfills
- Respect `prefers-reduced-motion` and system color scheme when the product does
- Consult official docs for the exact framework version in use

### Coherence

- Shared components own shared behavior; do not fork logic per page
- URL, query and local state stay aligned after navigation and refresh
- Forms: validation messages match server errors; disable double-submit
- Accessibility of interactive controls is part of correctness (labels, focus, keyboard)

### Communication

- Type or document request/response shapes at the boundary
- Handle timeouts, 4xx and 5xx with user-visible, actionable feedback
- Idempotent retries only where the API guarantees safety
- Never put secrets or privileged tokens in client-visible code

## Re-entry

- Re-invoke this role before every frontend, client-route, state or interaction action, not only at plan start.
- Re-evaluate the scope on every re-entry, including when another role handled the previous action.
- Hand backend, visual or other out-of-scope surfaces to their matching role with an explicit contract.

## Method

1. Read the existing frontend patterns in the repo before inventing new ones
2. Implement with → plan-validators (failing test or repro first when behavior changes)
3. Verify end-to-end: exercise the changed flow as a user would; check sibling routes
4. Hand visual polish to → role-design; hand API/schema work to → role-back

## Related

- Visual direction / tokens → role-design
- Backend data and routes → role-back
- CWV / Lighthouse → web-performance
- WCAG / SEO / legal → web-compliance
