---
version: "1.0.0"
date: "2026-09-24"
status: "Proposed"
adr_id: "ADR-0008"
priority: "P1"
---

# ADR-0008: Snippets reales post-oleada (Astro+pnpm+Vercel y skills/Python)

**Fecha:** 2026-09-24
**Estado:** Proposed
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Comprometer snippets de CI **reales** (no genéricos) para los dos stacks que la oleada va a repetir: web Astro+pnpm+Vercel y skills/Python `validate` (agents).
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. Cuando existan, copia `stacks/astro/` o `stacks/python-skills/` al `ci.yml` del producto y sustituye URLs/comandos. No uses `website-landingpage-template` como canon.

## Contexto

Hoy `stacks/` tiene fragmentos TypeScript genérico, Rust e infra. La oleada 1–2 incluye webs Astro (landing, miwebsite) y repos de agents/skills con Python `validate`. Copiar el snippet TS genérico obliga a reescribir pnpm/Vercel o el entrypoint de skills en cada PR, que es justo lo que el canon quería ahorrar.

`website-landingpage-template` es **plantilla de producto**, no el meta-estándar: los snippets viven aquí, extraídos _después_ de la oleada (cuando haya un gold ya alineado), no al revés.

## Decisión

1. Tras la oleada (o en cuanto un repo gold esté alineado), este canon añade:
   - `stacks/astro/` — Astro + pnpm + deploy/smoke orientado a **Vercel** (jobs `quality` / `build` / `smoke`; `e2e` opcional).
   - `stacks/python-skills/` — Python skills/agents: `quality` (ruff/format/types según el gold) + `test` + `smoke`/`validate` (el comando real del repo de agents, no un echo).
2. Cada directorio: `README.md` con meta-sección + snippets YAML de jobs, mismos **nombres** de la flota.
3. Los snippets actuales `stacks/typescript`, `stacks/rust`, `stacks/infra` se mantienen; Astro no sustituye a TS genérico (Next/SaaS sigue usando typescript).
4. No se copia el árbol de `website-landingpage-template` a este repo. Se extraen **solo** los steps de CI y los nombres de script.

## Consecuencias

- Los PRs de oleada 3+ pegan menos YAML inventado.
- Hay que vigilar el drift: si el gold cambia el comando, se actualiza el snippet aquí (minor del contrato si solo es el cuerpo; breaking si cambia el nombre del job).
- Más superficie en `check-structure.sh` (archivos nuevos required).

## Prioridad

**P1.** Primero alinear con snippets actuales; luego extraer los reales.

## Checklist de implementación

- [ ] Crear `stacks/astro/README.md` + `ci.quality.snippet.yml` + `ci.build.snippet.yml` + `ci.smoke.snippet.yml` (Vercel: smoke contra preview URL o `astro preview` local en CI).
- [ ] Crear `stacks/python-skills/README.md` + snippets `quality` / `test` / `validate` (comando real post-oleada).
- [ ] Meta-sección en esos README.
- [ ] Registrar archivos en `scripts/check-structure.sh`.
- [ ] Enlazar desde docs/README y REUTILIZACION (tabla copiar vs adaptar).
- [ ] CHANGELOG: Added snippets; no es breaking.

## Alternativas

- **Usar website-landingpage-template como canon:** se descartó en ADR-0001 y en este encargo.
- **Un único snippet «Node» para Astro y Next:** se descartó; los scripts y el smoke (preview vs `next start`) no coinciden.
- **Escribir los snippets ahora con comandos inventados:** se descartó; este ADR espera el gold alineado para no documentar mentiras.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0011](./ADR-0011-bootstrap-desde-plantilla.md)
- [stacks/typescript/README.md](../../../stacks/typescript/README.md)
