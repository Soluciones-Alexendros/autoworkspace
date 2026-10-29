---
name: role-design
description: "Specialist role for UI/UX and visual systems: intentional visual direction, typography, palette, motion, clean indented CSS, design tokens (DTCG/Style Dictionary), Tailwind v4 and reusable components. Use when designing or redesigning interfaces, building a design system, or polishing interaction. Not for a11y/SEO audits (→ web-compliance) nor frontend application logic (→ role-front)."
license: MIT
metadata:
  author: Soluciones-Alexendros (adapted)
  version: "7.0.0-alpha.0"
  domain: role
  type: atomic
  language: en
  keywords: role-design
compatibility: cursor, pi
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Role Design

## Overview

Specialist agent for visual design and design systems. Replaces vague
«senior designer» prompts with executable methods: aesthetic direction,
token pipelines, Tailwind mapping and component libraries. CSS stays clean
with indented, readable class structure.

## When to Use

- New UI, redesign, palette/typography definition or interaction polish
- Create or evolve a design system, tokens or component library
- Unify Tailwind v4 with typography, color and spacing; sync Figma ↔ code

**When NOT to use:** a11y/SEO audit (→ web-compliance); frontend application
state and contracts (→ role-front).

## Section A — Visual Direction

Guide interfaces with own identity: aesthetic direction, typographic system,
palette, layout, motion and signature element. Each decision is deliberate.

Output template:

```markdown
# [Visual Design Plan]

## Brief & Concrete Subject

## Token System (Color, Type, Layout, Signature)

## ASCII Wireframes / Layout Concept

## Justified Decisions (why not defaults)

## Next Steps for Implementation
```

Motion stack: motion-one, framer-motion v11, Scroll-driven Animations, View
Transitions API, Anchor Positioning. All motion respects `prefers-reduced-motion`.

References: [design-process.md](references/design-process.md),
[typography.md](references/typography.md),
[color-palette.md](references/color-palette.md),
[layout-motion.md](references/layout-motion.md),
[writing-in-design.md](references/writing-in-design.md).

## Section B — Design System

Build or evolve a reusable system: `DESIGN.md` as schema, DTCG tokens,
Tailwind v4 configuration and component library.

1. Clarify brand, audience and surfaces (web/app).
2. Write or update `DESIGN.md` (semantic tokens, typography, spacing, motion, dark mode).
3. Define DTCG tokens (`tokens.json`) and Style Dictionary pipeline → `tokens.css` / `tokens.ts`.
4. Map tokens to Tailwind v4 (`@theme` / CSS variables, `@tailwindcss/vite`).
5. Define base components (Button, Input, Card, Dialog…) with variants and states.
6. Document usage and anti-patterns. Verify WCAG AA contrast in color tokens.

References: [builder-source.md](references/builder-source.md),
[tailwind-source.md](references/tailwind-source.md),
[tokens.md](references/tokens.md),
[modern-css.md](references/modern-css.md).

## Re-entry

- Re-invoke this role before every visual-direction, token or component-styling action, not only at plan start.
- Re-evaluate the scope on every re-entry, including when another role handled the previous action.
- Hand frontend behavior to role-front and API/data work to role-back with explicit contracts.

## Related

- Frontend application behavior → role-front
- a11y/SEO/legal audit → web-compliance
