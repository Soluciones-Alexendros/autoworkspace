---
name: design-system-builder
description: "Genera design systems completos para React + Next.js/Vite con DESIGN.md como schema maestro. Crea árbol de archivos, tokens, componentes (shadcn-style), configuradores Tailwind/CSS vars, e instalación replicable. El eje central es DESIGN.md: un solo archivo que define toda la estructura, dependencias y swap points para retematizar sin deuda heredada. Usa cuando se pida crear, instalar o migrar un design system."
license: MIT
compatibility: cursor, pi
metadata:
  source: custom
  category: design
  stack: react,nextjs,vite,tailwind
---

# Design System Builder

Genera design systems production-ready con `DESIGN.md` _(ejemplo: artefacto generado)_ como schema maestro. Cambiar tokens en `DESIGN.md` _(ejemplo)_ + `tokens.css` _(ejemplo: artefacto generado)_ retematiza el sistema entero sin deuda heredada.

## Eje Central: DESIGN.md

`DESIGN.md` _(ejemplo: artefacto generado)_ es el único archivo que define el sistema completo: identidad visual, paleta, tipografía, espaciado, z-index, opacidades, motion, breakpoints, matrix de estados por componente y composiciones.

## Workflow: 3 Modes

1. **Install Mode** — Crear nuevo design system desde template
2. **Component Mode** — Añadir componente con forwardRef, cva, variantes
3. **Rethematize Mode** — Cambiar tema actualizando DESIGN.md + tokens

## Reglas Críticas

1. Nada hardcodeado — Todo usa tokens CSS o Tailwind
2. DESIGN.md como schema — El archivo maestro define el sistema
3. Componentes con forwardRef — Todos exportan con forwardRef
4. cva para variantes — class-variance-authority
5. Dark mode siempre — light, dark y system
6. ARIA obligatorio — Cada componente DEBE incluir role, atributos y estados
7. WCAG AA gate — 0 violaciones antes de entregar
8. Stories obligatorias — Cada componente DEBE tener .stories.tsx CSF 3.0

## Formatos de token

| Formato | Uso | Consumidor |
|---------|-----|------------|
| tokens.css _(ejemplo)_ | Variables CSS | CSS, Tailwind, browser |
| tokens.json | DTCG JSON | frontend-design, interaction-design _(pendiente: skills no existentes en este repo; texto plano, no enlaces)_ |
| tokens.ts | Constantes TS | Componentes React, test |

## Cross-References

- **frontend-design** _(pendiente: skill no existente en este repo)_ — REQUIERE tokens de este skill
- **interaction-design** _(pendiente: skill no existente en este repo)_ — REQUIERE tokens de este skill
