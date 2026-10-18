# OpenCode Setup — autoworkspace (vendor-neutral)

Esta guía explica cómo usar Autoworkspace con OpenCode de forma agent-driven (sin slash commands).

## Harness verificado

- **OpenCode objetivo:** `1.18.34` (`opencode --version`)
- **Config nativa:** `opencode.json` usa `skills.paths` (OpenCode ≥1.18). La clave legacy `skillDirectories` no es válida.
- **Smoke:** `opencode debug skill` desde el checkout debe listar las 16 skills del catálogo (sin `--auto`).

## Overview

OpenCode no tiene plugin system nativo. Logramos paridad con:

- System prompt fuerte (`AGENTS.md`)
- Built-in `skill` tool
- Descubrimiento consistente desde `skills.paths` + `skill-index.json`

## Instalación

1. Clone:

```bash
git clone https://github.com/Soluciones-Alexendros/autoworkspace.git
```

2. Abre proyecto en OpenCode
3. Asegura que existen:

- `AGENTS.md` (root)
- `opencode.json`
- `skills/` directorio
- `.opencode/agents/skill-router.md`

No requiere instalación adicional.

## Cómo funciona

### 1. Skill Discovery

Todas las skills viven en:

```
skills/<skill-name>/SKILL.md
```

OpenCode agents son instruidos vía AGENTS.md a:

- Detectar cuándo aplica una skill
- Invocar `skill` tool
- Seguir la skill exactamente

### 2. Automatic Skill Invocation

El agente evalúa cada request y mapea a skill apropiada.
Ejemplos:

- "limpia mi Arch" → `local-maintenance`
- "revisa la arquitectura" → `project-architecture`
- "prepara release" → `project-publish`
- "audita compliance" → `web-compliance`
- "implementa el frontend" → `role-front`
- "refactoriza con clean code" → `role-clean-code`

El usuario NO necesita pedir skills explícitamente.

### 3. Lifecycle Mapping

- DEFINE → plan-specification
- CONTINUE → plan-continue
- IMPLEMENT → role-* + plan-validators
- INTEGRATE → project-publish
- WEB AUDITS → web-*
- LOCAL (local OS) → local-*

La secuencia de implementación es planificación → roles → `plan-validators` →
`project-publish`. Antes de cada tarea o acción independiente se reevalúa el
alcance y se invocan todos los roles aplicables: backend/API/jobs → `role-back`,
frontend/rutas cliente → `role-front`, diseño/tokens → `role-design`,
clean-code/refactor → `role-clean-code`. Una invocación anterior no cubre las
acciones siguientes; el trabajo mixto exige contratos y handoffs entre roles.

### Agent Expectations (Critical)

- Always check if a skill applies before acting
- If a skill applies, it MUST be used
- Never skip required workflows
- Do not jump directly to implementation
- Re-invoke matching roles before every implementation action

Estas reglas son forzadas vía AGENTS.md y `tools/skill-router/route.py`.

## Recommended Workflow

Usa lenguaje natural:

- "especifica esta feature"
- "por dónde empiezo con este repo"
- "publica la release"
- "audita OWASP este código"
