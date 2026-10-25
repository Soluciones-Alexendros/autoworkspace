---
version: "1.0.0"
date: "2026-09-24"
status: "Accepted"
adr_id: "ADR-0002"
priority: "P0"
---

# ADR-0002: Protección de rama y metadatos de repo como código

**Fecha:** 2026-09-24  
**Estado:** Accepted  
**Prioridad:** P0 (hacer pronto)

### Propósito de este documento

- **Objetivos:** Fijar que description, topics, branch protection, auto-delete y auto-merge se versionan junto al canon, no solo en clics de Settings.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto. En producto, enlaza el ADR del canon que adoptas o escribe uno propio si el hosting GitHub difiere (Enterprise vs cloud).

## Contexto

El inventario 2026-09-24 y [REUTILIZACION.md](../../REUTILIZACION.md) dejan la protección de `main` y los metadatos (description, topics) como trabajo **manual del Mantenedor**. Eso produce deriva: repos sin description, topics incompletos, checks required distintos y auto-merge/auto-delete apagados.

El agente **no** debe mutar settings de org ni de otros repos desde un PR de alineación. Hace falta un contrato versionado (runbook + script `gh` y/o org rulesets) que un humano ejecute de forma repetible.

## Decisión

1. El canon versiona un **runbook** (`docs/runbooks/github-repo-settings.md`) y un **script idempotente** (`scripts/apply-github-settings.sh`, o equivalente con `gh`) que documenta y, cuando el Mantenedor lo lance, aplica:
   - `description` (formato `[tipo] — [qué hace] — [stack]`, ≤120)
   - `topics` (≥4 en P0; ≥6 en P2)
   - protección de `main`: PR obligatorio, historia lineal, conversaciones resueltas, sin force-push, sin bypass
   - checks required: solo `ci-gate` (app 15368) según [ADR-0013](./ADR-0013-check-unico-ci-gate.md)
   - Allow auto-merge ON
   - auto-delete de ramas head ON
2. Preferencia: **org rulesets** de GitHub para lo que sea común a la flota (protección de `main`, required checks de nombres canónicos). El script `gh` cubre lo que el ruleset no puede (description, topics, flags de auto-merge/auto-delete del repo).
3. El script es **opt-in y humano**: no corre en CI de PRs de producto, no usa tokens de org en el árbol, no imprime secretos. Dry-run por defecto; `--apply` explícito.
4. Este ADR **no autoriza** a agentes a cambiar settings de org ni de repos ajenos. Solo el Mantenedor ejecuta `--apply` sobre el repo destino.

## Consecuencias

- La deriva de metadatos deja de ser «memoria del Mantenedor»: el contrato vive junto al canon y se alinea en la oleada.
- Un ruleset de org que exija nombres de fase (`quality`, `build`, …) en lugar de `ci-gate` crea checks fantasma; el ruleset debe respetar [ADR-0013](./ADR-0013-check-unico-ci-gate.md).
- El script necesita `gh` autenticado con scopes `repo` / `admin:org` (rulesets). Esos tokens no se commitean.

## Prioridad

**P0.** Sin esto, cada PR de alineación deja Settings a medias y el scorecard de [ADR-0009](./ADR-0009-scorecard-cumplimiento-p0.md) no puede medirse.

## Checklist de implementación

- [ ] Redactar `docs/runbooks/github-repo-settings.md` (pasos humanos + qué hace el script + qué queda en org ruleset).
- [ ] Añadir `scripts/apply-github-settings.sh` con dry-run por defecto y `--apply`.
- [ ] Documentar variables (`OWNER`, `REPO`, `DESCRIPTION`, `TOPICS`) solo como placeholders.
- [ ] Decidir y documentar el ruleset de org (nombres de checks, sin exigir `build` global).
- [ ] Enlazar el runbook desde [REUTILIZACION.md](../../REUTILIZACION.md) (sección «Protección de `main`»).
- [ ] Registrar en `CHANGELOG.md` cuando el script/runbook existan (contrato visible).

## Alternativas

- **Solo documentación (status quo):** se descartó; ya produce deriva.
- **Terraform/`github` provider como única vía:** se reserva a P2 si la flota crece; `gh` + rulesets cubre P0 con menos superficie.
- **Aplicar settings desde CI del canon hacia toda la org:** se descartó (demasiado privilegio, viola «no cambies otros repos»).

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0003](./ADR-0003-job-build-y-required-checks.md) (superseded)
- [ADR-0012](./ADR-0012-solo-dev-automerge-sin-revision.md)
- [ADR-0013](./ADR-0013-check-unico-ci-gate.md)
- [ADR-0005](./ADR-0005-secret-scanning-org.md)
- [REUTILIZACION.md](../../REUTILIZACION.md)
