---
name: interaction-design
description: Design and implement microinteractions, motion design, transitions, and user feedback patterns. Use when adding polish to UI interactions, implementing loading states, or creating delightful user experiences.
license: MIT
compatibility: cursor, pi
metadata:
  source: wshobson/agents + custom
  category: design
---

# Interaction Design

Create engaging, intuitive interactions through motion, feedback, and thoughtful state transitions that enhance usability and delight users.

## Contrato Fuerte (Fase 1)

**REQUIRES tokens from `role-design`.** Before generating ANY code:

1. **Read `tokens.json`** (DTCG format) from the design system. If not found → ERROR: design system must be installed first via `role-design` skill.
2. **Consume semantic tokens** — All animation durations, easings, colors MUST come from `tokens.json`. Never invent new values.
3. **Emit `Pattern.stories.tsx`** — Every microinteraction pattern MUST include a CSF 3.0 story file with play functions + visual baseline. Use `contracts/csf-template.stories.tsx` as base.
4. **ARIA compliance** — Every interactive pattern MUST include the role, attributes, and states documented in `contracts/aria-component-map.json`. Especially: `aria-live` for dynamic content, `aria-checked` for toggles, `role="switch"` for switches.
5. **WCAG AA gate** — Before delivering, verify output passes `scripts/a11y-gate.sh` (0 violations).
6. **NN Heuristics self-review** — Run through `references/heuristics-checklist.md`. Especially: Heuristic 1 (System Status), Heuristic 3 (User Control), Heuristic 9 (Error Recovery).

### Token consumption rules

| `Pattern.tsx`         | Yes      | Implementation using tokens + ARIA          |
| `Pattern.stories.tsx` | Yes      | CSF 3.0 stories with play + visual baseline |
| `index.ts`            | Yes      | Barrel export                               |

## When to Use This Skill

- Adding microinteractions to enhance user feedback
- Implementing smooth page and component transitions
- Designing loading states and skeleton screens
- Creating gesture-based interactions
- Building notification and toast systems
- Implementing drag-and-drop interfaces
- Adding scroll-triggered animations
- Designing hover and focus states

## Workflow

1. **Identify trigger** → What user action causes this?
2. **Choose duration** → micro(100-150ms), small(200-300ms), medium(300-500ms), complex(500ms+)
3. **Choose easing** → ease-out (entering), ease-in (exiting), spring (playful), ease-in-out (moving between)
4. **Implement** → Use framer-motion for React, CSS for static
5. **Verify reduced-motion** → Does it work without animation?

## Timing Guidelines

Use token paths from `tokens.json` — values below are reference ranges, not hardcoded numbers.

| Duration token path             | Range     | Use Case                                  |
| ------------------------------- | --------- | ----------------------------------------- |
| `motion.duration.micro.$value`  | 100-150ms | Micro-feedback (hovers, clicks)           |
| `motion.duration.small.$value`  | 200-300ms | Small transitions (toggles, dropdowns)    |
| `motion.duration.normal.$value` | 300-500ms | Medium transitions (modals, page changes) |
| `motion.duration.slow.$value`   | 500ms+    | Complex choreographed animations          |

## Easing Functions

--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); /* Both - moving between */
--spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* Overshoot - playful */

All components MUST use CSS variables, never hardcoded colors:

style={{ width, height, borderRadius }}
      animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
    />
  )
}

```

## Scroll-Triggered Animation

// CORRECT — direction-aware
const x = direction === 'rtl' ? -100 : 100
animate={{ x: `${x}%` }}

// WRONG — hardcoded direction
animate={{ x: '100%' }}

## Reduced Motion Alternatives

| Pattern        | Static Alternative                                 |
| -------------- | -------------------------------------------------- |
| Button         | No scale on hover/tap, keep focus ring             |
| Toggle         | Instant switch (no transition), keep color change  |
| Skeleton       | Static placeholder (no shimmer), use opacity pulse |
| Toast          | Instant appear/disappear                           |
| PageTransition | No enter/exit animation                            |
| ScrollReveal   | No scroll trigger, content always visible          |

- **Focus**: Visible focus indicators, never `outline: none` without replacement (WCAG 2.4.7).
- **Timing**: Allow users to pause/stop auto-playing animations (WCAG 2.2.2).
- **ARIA roles**: Toggle → `role="switch"` + `aria-checked`. Toast → `role="status"`. Alert → `role="alert"`. Per `contracts/aria-component-map.json`.
- Auto-review with `references/heuristics-checklist.md` (NN 10 Usability Heuristics).

### QA Pipeline (before every delivery)

| `contracts/aria-component-map.json`  | WAI-ARIA roles, attributes, states per component |
| `contracts/wcag22-checklist.json`    | WCAG 2.2 A+AA success criteria                   |
| `contracts/csf-template.stories.tsx` | CSF 3.0 template for story generation            |

## References (role-design)

| File                                 | Description                                                  |
| ------------------------------------ | ------------------------------------------------------------ |
| `references/dtcg-spec.md`            | DTCG spec, token types, CSS/Tailwind mapping                 |
| `references/aria-component-map.md`   | WAI-ARIA roles→components mapping                            |
| `references/heuristics-checklist.md` | NN 10 Usability Heuristics checklist                         |
| `references/csf-3.0-guide.md`        | **F2** — CSF 3.0 guide, play functions for microinteractions |
| `references/core-web-vitals.md`      | **F2** — CWV constraints (CLS/INP) for animation code        |
| `references/design-qa-workflow.md`   | **F2** — Full QA pipeline (7 steps)                          |
| `references/islands-architecture.md` | **F3** — Islands Architecture, zero-JS baseline              |
| `references/rsc-boundary.md`         | **F3** — React Server Components boundary rules              |
| `references/modern-css.md`           | **F3** — CSS Grid/Flex, Container Queries, Nesting, Layers   |
| `references/i18n-infra.md`           | **F3** — RTL/LTR tokens, logical properties, locale fmt      |
| `references/atomic-design.md`        | **F3** — Taxonomy atoms→molecules→organisms→templates        |
