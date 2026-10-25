---
version: "1.0.0"
date: "2026-09-24"
status: "Superseded"
adr_id: "ADR-0006"
priority: "P1"
---

# ADR-0006: Reviews por perfil y label `automerge`

**Fecha:** 2026-09-24  
**Estado:** Superseded by [ADR-0012](./ADR-0012-solo-dev-automerge-sin-revision.md)  
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Definir cuántas approvals exige cada perfil y documentar el label `automerge` como único interruptor de merge automático humano/agente.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: ajusta branch protection a ≥1 o CODEOWNERS cuando haya equipo. El label `automerge` se crea en el repo (o org) con el mismo nombre.

## Contexto

[ADR-0001](./ADR-0001-canon-repo-standard.md) exige automerge humano solo con label `automerge` (+ CI verde + review). En un canon **solo-owner** (`* @Alexendros`), exigir ≥1 approval bloquea al único revisor o fuerza auto-approvals teatrales. En producto con equipo, 0 approvals es demasiado laxo.

El label existe en política pero no está descrito como contrato (quién lo pone, qué comprueba CI, qué no hace).

## Decisión

1. **Canon / repo solo-owner (sin equipo):** PR obligatorio + checks required + historia lineal. **0 approvals** mínimas en protection. El owner sigue siendo responsable del diff. CODEOWNERS informa, no bloquea.
2. **Producto con más de un mantenedor o equipo:** ≥ **1** approval. Si hay CODEOWNERS por path, required reviews de code owners.
3. Label **`automerge`** (minúsculas, sin namespace):
   - Lo pone un humano (o el owner) cuando el PR es rutinario y ya cumple DoD.
   - Condiciones: CI verde (`quality` + `test` + `smoke` + `build`/`e2e` si existen) y las approvals del perfil.
   - Renovate **no** usa este label: automergea `patch`/`minor` por su propia config.
   - Un major de deps, un cambio de workflow/CODEOWNERS/Renovate o un ADR Accepted **no** llevan `automerge`.
4. El agente **nunca** se auto-asigna el label salvo que el humano lo pida en el mismo hilo.

## Consecuencias

- Este repo puede fusionar sin review teatral cuando el owner + CI bastan.
- Un producto que crece a equipo debe **subir** el required reviews (cambio de Settings; documentado en ADR-0002).
- Menos merges accidentales de agentes: sin label, no hay auto-merge aunque CI esté verde.

## Prioridad

**P1.** No bloquea la oleada de archivos; sí el pulido de protection por perfil.

## Checklist de implementación

- [ ] Crear el label `automerge` (org o repo) y documentarlo en CONTRIBUTING + plantilla de PR.
- [ ] Actualizar REUTILIZACION: tabla «solo-owner → 0 approvals; producto con equipo → ≥1 / code owners».
- [ ] Incluir el perfil de review en el script/runbook de ADR-0002.
- [ ] AGENTS.md: una línea que apunte a este ADR (no reabrir «siempre ≥1»).
- [ ] CHANGELOG cuando el contrato de reviews se publique.

## Alternativas

- **≥1 approval en toda la flota:** se descartó para el canon solo-owner (auto-review inútil).
- **Automerge humano sin label, solo CI:** se descartó en ADR-0001.
- **Ruleset que exige code owners siempre:** prematuro hasta que existan equipos.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
