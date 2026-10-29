# Routing Avanzado — Determinista + LLM

## Objetivo

Fluidez en invocación automatizada por agentes de código sin depender solo del LLM.

## Componentes

1. `skill-index.json` — índice machine-readable con keywords, triggers, routes
2. `tools/skill-router/intent-map.yaml` — patrones ES/EN
3. `tools/skill-router/route.py` — scoring TF + trigger boost (0 dependencias)
4. `scripts/install-cursor.sh` y `scripts/install-pi.sh` — publican el catálogo; el agente lee `SKILL.md` desde el symlink

## Flujo

```
User Prompt
  → route.py (determinista, <50ms)
    → top 3 skills con score
  → AGENTS.md rule: MUST use skill tool if score > threshold
  → skill tool loads SKILL.md
  → agent follows SKILL.md
```

En un plan de implementación, la cadena es planificación → `role-*` →
`plan-validators` → `project-publish`. El router de fase solo ofrece un fallback:
antes de cada tarea o acción independiente se vuelve a evaluar la superficie y se
invocan todos los roles aplicables, aunque la acción anterior usara otro rol. El
trabajo mixto backend/frontend/diseño requiere contratos y handoffs explícitos.

## Ejemplo

Prompt: "audita y publica este repo"

- route.py:
  9.5 plan-continue -> skills/plan-continue/SKILL.md
  8.8 project-publish -> skills/project-publish/SKILL.md
- El agente (Cursor o Pi) ejecuta plan-continue (análisis / roadmap), luego handoff a project-publish

## Añadir triggers

Edita `intent-map.yaml` y `metadata.keywords` en SKILL.md, luego rebuild:

```bash
python tools/skill-index/generate.py --sync-docs
```

## Validación

```bash
python tools/skill-router/route.py --interactive
prompt> por donde empiezo con este repo
8.90 plan-continue -> skills/plan-continue/SKILL.md
```

## Vendor-neutral

Este router no usa APIs externas, funciona offline y sin dependencias de un único vendor.
