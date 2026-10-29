---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: MIT
compatibility: cursor, pi
metadata:
  source: vercel-labs/agent-eval + custom
  category: design
---

## Persona

Approach this as the design lead at a boutique frontend studio. Your job is not to generate code — it's to make design decisions that have personality, intention, and taste. Every component you build should feel like it was designed by a human who cares.

## Contrato Fuerte (Fase 1)

**REQUIRES tokens from `role-design`.** Before generating ANY code:

1. **Read `tokens.json`** (DTCG format) from the design system. If not found → ERROR: design system must be installed first via `role-design` skill.
2. **Consume semantic tokens** — All colors, spacing, typography, shadows MUST come from `tokens.json`. Never invent new values.
3. **Emit `Component.stories.tsx`** — Every component generated MUST include a CSF 3.0 story file with play functions. Use `contracts/csf-template.stories.tsx` as base.
4. **ARIA compliance** — Every interactive element MUST include the role, attributes, and states documented in `contracts/aria-component-map.json`.
5. **WCAG AA gate** — Before delivering, verify output passes `scripts/a11y-gate.sh` (0 violations). Run contrast check: `node scripts/contrast-check.mjs tokens.css --dtcg tokens.json`.
6. **NN Heuristics self-review** — Run through `references/heuristics-checklist.md` (10 checks). All must pass before delivery.

### Token consumption rules

| `Component.tsx`         | Yes      | Implementation using tokens + ARIA + CWV constraints |
| `Component.stories.tsx` | Yes      | CSF 3.0 stories with play functions                  |
| `index.ts`              | Yes      | Barrel export                                        |

## Workflow

### Modo con Design System (requerido por defecto)

Cuando existe un design system (`tokens.json` + `tokens.css` de `role-design`):

1. **Leer tokens existentes.** Consumir `tokens.json` como fuente canónica. No inventar nuevos valores de color, spacing, o typography.
2. **Ground the brief.** Ask: purpose, audience, constraints, aesthetic direction. Never skip this.
3. **Map brief → tokens.** Seleccionar del palette existente. Documentar nuevas composiciones en `DESIGN.md` si es necesario.
4. **Brainstorm 2–3 directions** with ASCII wireframe sketches (layout/composición, no tokens).
5. **Pick strongest direction.** Justify the choice in one sentence.
6. **Build the implementation.** Ship working code using tokens.
7. **Self-critique.** "Does this violate any anti-patterns? Would a designer be proud? What would they change?"

### Modo Standalone (sin design system existente)

Cuando NO hay design system preexistente (proyecto greenfield):

1. **Ground the brief.** Ask: purpose, audience, constraints, aesthetic direction. Never skip this.
2. **Define tokens.** 4–6 named hex colors, 2 font roles (display + body), 1 memorable signature element. Emitir `tokens.json` y `tokens.css` básicos.
3. **Brainstorm 2–3 directions** with ASCII wireframe sketches.
4. **Pick strongest direction.** Justify the choice in one sentence.
5. **Build the implementation.** Ship working code, not mocks.
6. **Self-critique.** "Does this violate any anti-patterns? Would a designer be proud? What would they change?"

## Anti-Slop Layer

Hard bans — never ship these:

- No em-dash (—) as the ONLY decorative element
- No `#000000` pure black — use `--color-text-primary` token (typically `#0a0a0a`)
- No `#ffffff` pure white — use `--color-surface` token (typically `#fafafa`)
- No purple-to-blue gradient as default accent
- No three equal-width column layouts as default
- No Inter, Roboto, Arial, system-ui, Space Grotesk as **default/perezosa** font choice. Si se usa Inter u otras fuentes comunes, DEBE ser decisión consciente documentada en `DESIGN.md` con justificación (ej. CWV optimization, multilingual support). Nunca usarlas como fallback sin pensar.
- No generic placeholder names (John Doe, Lorem ipsum)
- No `shadow-lg` on every card
- No `rounded-full` on every button
- No `gap-4` uniform spacing everywhere
- No hero → features → pricing → footer as the only landing page structure
- No "Welcome to..." as opening copy
- No "Click here" as CTA text
- No `bg-gradient-to-br from-purple-500 to-blue-500` as background
- No cookie-cutter card layouts with icon + title + description

## Output Templates

### Token System

- Links: always `<a href>`, not `onClick` routing
- Forms: always `action`/`method` for submit base, JS for enhanced validation
- Content: static HTML for non-interactive elements
- Progressive: HTML → CSS → JS layers, each enhancing the previous

See `references/islands-architecture.md` for zero-JS baseline patterns.

## i18n Awareness

When generating UI that may be localized:

- Use CSS logical properties: `margin-inline-start` not `margin-left`, `text-align: start` not `text-align: left`
- Icons with direction (arrows) must flip in RTL
- Date/number displays must use `Intl.DateTimeFormat` / `Intl.NumberFormat`
- See `references/i18n-infra.md` for RTL/LTR tokens and locale-aware formatting

## Code Snippets

### 1. Hero Section

> **REGLA**: Ejemplos ilustrativos de composición. En producción, reemplaza todos los valores de color por tokens CSS/Tailwind del design system.

<p className="mt-8 text-lg text-text-muted max-w-md leading-relaxed">
            We build interfaces that refuse to blend in. Every pixel, every
            transition, every choice — intentional.
          </p>
          <button className="mt-10 px-8 py-4 bg-accent text-surface font-semibold hover:opacity-90 transition-colors">
            Start a project
          </button>
        </div>
        <div className="hidden lg:block h-[500px] bg-gradient-to-b from-surface-raised to-surface rounded-sm border border-border" />
      </div>
    </section>
  )
}

>
            <div
              className="w-10 h-1 mb-6 bg-current transition-all group-hover:w-16"
              style={{ color: `var(${card.accentVar})` }}
            />
            <h3 className="text-xl font-bold text-text-primary mb-3">
              {card.title}
            </h3>
            <p className="text-text-muted leading-relaxed">{card.desc}</p>
          </motion.article>
        ))}
      </div>
    </section>
  )
}

</a>
          </li>
        </ul>
      </nav>
    </header>
  )
}

- Generate both themes from the same token set:
  - Surfaces: lighten in dark mode (`#fafafa` → `#1a1a1a`)
  - Text: darken in light, lighten in dark (`#0a0a0a` → `#fafafa`)
  - Accent: shift hue slightly for dark backgrounds

## Gotchas

| Issue                               | Fix                                                          |
| ----------------------------------- | ------------------------------------------------------------ |
| Tailwind purges unused classes      | Safelist dynamic classes in `tailwind.config.js`             |
| Next.js RSC can't use framer-motion | Wrap in `'use client'` boundary                              |
| Font loading causes layout shift    | Use `next/font` or `font-display: swap`                      |
| CSS vars in Tailwind                | Map via `theme.extend.colors`                                |
| `z-index` surprises                 | Create stacking context explicitly with `isolation: isolate` |

## Negative Triggers

Do NOT use when:

- User asks for backend/API logic
- User asks for database schema
- User asks for deployment/DevOps
- User asks for testing setup
- User asks for refactoring non-visual code

## Cross-References

Related skills:

- `interaction-design` — motion patterns and microinteractions
- `role-design` — **REQUIRED** token source. Must consume `tokens.json` (DTCG format) from this skill before generating any UI code.

## Contracts

| File                                 | Description                                         |
| ------------------------------------ | --------------------------------------------------- |
| `contracts/dtcg-tokens.schema.json`  | DTCG JSON schema — tokens format reference          |
| `contracts/aria-component-map.json`  | WAI-ARIA roles, attributes, states per component    |

| `contracts/wcag22-checklist.json`    | WCAG 2.2 A+AA success criteria (automatable subset) |
| `contracts/csf-template.stories.tsx` | CSF 3.0 template for story generation               |

## References (role-design)

| File                                 | Description                                               |
| ------------------------------------ | --------------------------------------------------------- |
| `references/dtcg-spec.md`            | DTCG spec, token types, CSS/Tailwind mapping              |
| `references/aria-component-map.md`   | WAI-ARIA roles→components mapping                         |
| `references/heuristics-checklist.md` | NN 10 Usability Heuristics checklist                      |
| `references/csf-3.0-guide.md`        | **F2** — CSF 3.0 guide, play functions patterns           |
| `references/core-web-vitals.md`      | **F2** — CWV constraints (LCP/CLS/INP) for generated code |
| `references/design-qa-workflow.md`   | **F2** — Full QA pipeline (7 steps)                       |
| `references/islands-architecture.md` | **F3** — Islands Architecture, zero-JS baseline           |
| `references/rsc-boundary.md`         | **F3** — React Server Components boundary rules           |
| `references/modern-css.md`           | **F3** — CSS Grid/Flex, Container Queries, Nesting        |
| `references/i18n-infra.md`           | **F3** — RTL/LTR tokens, logical properties, locale fmt   |
| `references/atomic-design.md`        | **F3** — Taxonomy atoms→molecules→organisms→templates     |
