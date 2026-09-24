---
version: "1.0.0"
date: "2026-09-24"
status: "Accepted"
adr_id: "ADR-0005"
priority: "P0"
---

# ADR-0005: Secret scanning y push protection a nivel org

**Fecha:** 2026-09-24  
**Estado:** Accepted  
**Prioridad:** P0 (hacer pronto)

### Propósito de este documento

- **Objetivos:** Declarar secret scanning + push protection como control P0 de seguridad de flota, a nivel org, no repo a repo.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: no commitees secretos; mantén `.env.example` con placeholders; el runbook de rotación es [rotate-secrets.md](../../runbooks/rotate-secrets.md).

## Contexto

Los runbooks ya piden «secret scanning + push protection ON», pero el interruptor vive en Settings de org/repo y no estaba en el contrato P0 del canon. Un repo nuevo o un push de agente puede filtrar un token antes de que alguien active el checkbox.

Este ADR no introduce secretos reales ni tokens de ejemplo realistas. Tampoco pide al agente que mute la org.

## Decisión

1. **P0 de flota:** GitHub Secret scanning y **Push protection** están ON a nivel **organización** `Iniciativas-Alexendros` (todos los repos, incluidos privados). Validity checks ON si el plan lo permite.
2. Repos que por plan no hereden el default de org: el Mantenedor los activa a mano; el scorecard los marca en rojo hasta entonces.
3. Complementos recomendados (P1, no bloquean este ADR): `gitleaks` u equivalente en pre-commit; job de scan en `security.yml` si el producto ya lo tiene.
4. Si push protection bloquea un falso positivo: bypass documentado (motivo + issue), nunca «apagar para el repo».
5. El agente **no** desactiva scanning, no añade secretos de prueba reales y no cambia org settings.

## Consecuencias

- Primera línea de defensa homogénea: un push con `ghp_` / AWS key / etc. se rechaza igual en toda la flota.
- Falsos positivos (fixtures de tests) requieren allowlist o mock no-secreto; no se relaja el control org.
- El runbook de rotación sigue siendo el procedimiento **después** de una filtración; este ADR intenta que no llegue.

## Prioridad

**P0 de seguridad de flota.** Va en paralelo a ADR-0002/0004 (gobierno GitHub), no espera a snippets ni scorecard.

## Checklist de implementación

- [ ] Mantenedor: confirmar Secret scanning + Push protection ON en org (captura o nota en el runbook de settings, sin tokens).
- [ ] Mencionar el prerrequisito org en SECURITY.md y en `docs/runbooks/rotate-secrets.md`.
- [ ] Incluir el control en el scorecard P0 ([ADR-0009](./ADR-0009-scorecard-cumplimiento-p0.md)).
- [ ] En REUTILIZACION: «no desactives secret scanning en el PR de alineación».
- [ ] CHANGELOG cuando el prerrequisito quede documentado como contrato.

## Alternativas

- **Solo pre-commit gitleaks:** se descartó como único control; se salta en `--no-verify` y no cubre la UI de GitHub.
- **Activar repo a repo:** se descartó como P0; olvidos en repos nuevos.
- **Trufflehog self-hosted obligatorio en P0:** reserva P2; el control nativo basta para empezar.

## Relacionados

- [ADR-0002](./ADR-0002-proteccion-metadatos-como-codigo.md)
- [ADR-0004](./ADR-0004-renovate-org-y-dependabot.md)
- [SECURITY.md](../../../SECURITY.md)
- [rotate-secrets.md](../../runbooks/rotate-secrets.md)
