---
version: "1.0.0"
date: "2026-09-24"
status: "Accepted"
adr_id: "ADR-0004"
priority: "P0"
---

# ADR-0004: Prerrequisito Renovate a nivel org y política Dependabot

**Fecha:** 2026-09-24
**Estado:** Accepted
**Prioridad:** P0 (hacer pronto)

### Propósito de este documento

- **Objetivos:** Dejar por escrito que Renovate (GitHub App a nivel org) es prerrequisito de flota, y separar Dependabot **Alerts** (seguridad, ON) de Dependabot **version-updates** (prohibidos).
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: copia `.github/renovate.json` recortado al stack; no añadas `dependabot.yml` de bumps. El changelog de deps lo escribe Renovate.

## Contexto

[ADR-0001](./ADR-0001-canon-repo-standard.md) ya eligió Renovate como único bot de version-updates. En la práctica, un repo puede tener `renovate.json` y **cero PRs** si la GitHub App no está instalada en la org o el repo no está seleccionado. Mezclar Dependabot version-updates + Renovate duplica PRs (caso que el inventario señaló en gold).

Dependabot **Alerts** (y Security Updates puntuales de CVE) son otro producto: no sustituyen a Renovate y no deben apagarse.

## Decisión

1. **Prerrequisito de flota (humano, org):** la GitHub App [Renovate](https://github.com/apps/renovate) está instalada en `Soluciones-Alexendros` y habilitada para los repos activos (o «all repositories» si el Mantenedor lo prefiere). Sin la App, el JSON del canon no hace nada.
2. Cada repo P1+ versiona `.github/renovate.json` (base de este canon, `packageRules` recortadas al stack). Schedule: madrugada `Europe/Madrid`. Automerge `patch` + `minor`; minors agrupados; label `dependencies`; **sin** automerge de `major`.
3. **Prohibido** `.github/dependabot.yml` (o `dependabot.yml` en raíz) para version-updates de npm/cargo/actions/docker/etc.
4. **Dependabot Alerts: ON** a nivel org/repo. No se desactivan en PRs de alineación. Security Updates automáticos de Dependabot se evitan si generan bumps paralelos a Renovate; el parche de CVE lo toma Renovate o un PR humano.
5. El agente no instala la App ni cambia org settings. Documenta el prerrequisito y, si faltan PRs de Renovate, lo señala al Mantenedor.

## Consecuencias

- Un repo «alineado» sin la App instalada es **ámbar** en el scorecard ([ADR-0009](./ADR-0009-scorecard-cumplimiento-p0.md)): tiene JSON, no tiene bot.
- Quitar `dependabot.yml` en el mismo PR que añade Renovate evita una semana de PRs duplicados.
- Las Alerts siguen visibles en Security; el triage no se pierde.

## Prioridad

**P0.** Sin la App a nivel org, toda la oleada de `renovate.json` es teatro.

## Checklist de implementación

- [ ] Documentar en README / REUTILIZACION / SECURITY el prerrequisito «App Renovate instalada en la org».
- [ ] Checklist §8 P1: «Renovate App habilitada en este repo (no solo el JSON)».
- [ ] Confirmar (humano) instalación org + selección de repos; no lo hace el agente.
- [ ] Política Alerts ON / version-updates OFF publicada en `docs/guides/` o REUTILIZACION (ya esbozada; unificar redacción).
- [ ] `scripts/check-structure.sh` sigue fallando si aparece `dependabot.yml`.

## Alternativas

- **Solo Dependabot:** se descartó en ADR-0001 (gold ya en Renovate; agrupado + automerge finer).
- **Renovate SaaS self-hosted:** innecesario en P0; la App oficial basta.
- **Apagar Dependabot Alerts «para no mezclar»:** se descartó; pierde el canal nativo de CVE.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md)
- [ADR-0005](./ADR-0005-secret-scanning-org.md)
- [ADR-0009](./ADR-0009-scorecard-cumplimiento-p0.md)
- [`.github/renovate.json`](../../../.github/renovate.json)
