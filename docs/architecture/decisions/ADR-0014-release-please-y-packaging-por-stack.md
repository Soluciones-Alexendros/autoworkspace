---
version: "2.0.0"
date: "2026-10-25"
status: "Accepted"
adr_id: "ADR-0014"
priority: "P1"
---

# ADR-0014: Versionado release-please + packaging por stack

**Fecha:** 2026-10-25  
**Estado:** Accepted  
**Prioridad:** P1

### Propósito de este documento

- **Objetivos:** Versionar el contrato de `repo-standard` con release-please (un solo componente SemVer) y empaquetar el CI por stack como workflows reutilizables pineados por SHA.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR. En producto: pineá el reusable con `@<SHA> # vX.Y.Z` de este canon. No publiques un package npm/crate por stack.

## Contexto

[ADR-0010](./ADR-0010-semver-contrato-estandar.md) define SemVer del contrato pero no el cortador de releases. Los snippets YAML en `stacks/` se copiaban a mano y derivaban. Hace falta un empaquetado único (workflows `workflow_call`) y un proceso de tag alineado con Conventional Commits.

## Decisión

1. **Un solo componente SemVer** (el contrato de flota). release-please corta tags `vX.Y.Z` desde Conventional Commits + CHANGELOG. Este cambio de contrato (required → `ci-gate`, auto-merge sin `automerge`) es **2.0.0**.
2. **Packaging de CI:** workflows reutilizables en `.github/workflows/reusable-{node,rust,python,static}.yml`. Los callers en `stacks/<stack>/ci.yml` (y el `ci.yml` del producto) usan:
   `uses: Soluciones-Alexendros/repo-standard/.github/workflows/reusable-<stack>.yml@<SHA> # vX.Y.Z`
3. El comentario `# vX.Y.Z` nombra la versión de contrato a la que pertenece el pin. Actualizar el reusable exige actualizar el SHA en los callers.
4. **No** hay package de release-please por stack ni publicación a npm/crates.io de estos YAML.
5. El workflow y el manifest de release-please quedan en el checklist; **fuera de este PR** hasta que exista la App / tag base.

## Consecuencias

- Los consumidores alinean a `repo-standard ≥2.0` y pinean el SHA del tag.
- Drift de snippets desaparece: el cuerpo de CI vive en los reusable.
- Un pin `@v2` flotante se descarta (pin por SHA completo).

## Prioridad

**P1.** Los reusable y el major 2.0.0 cierran el contrato; el cortador release-please se cablea en un PR siguiente.

## Checklist de implementación

- [x] Publicar reusable workflows + plantillas `stacks/*/ci.yml`.
- [x] Documentar el pin `@SHA # v2.0.0` en REUTILIZACION y stacks.
- [ ] Añadir `.github/workflows/release-please.yml` + manifest (PR siguiente).
- [ ] Tag humano `v2.0.0` cuando Unreleased se publique.
- [ ] CHANGELOG: nota de packaging + BREAKING de checks.

## Alternativas

- **Seguir con snippets copiados:** se descartó; deriva entre repos.
- **Un reusable monolítico multi-stack:** se descartó; mezcla toolchains y alarga el job.
- **CalVer del contrato:** se descartó en ADR-0010.

## Relacionados

- [ADR-0010](./ADR-0010-semver-contrato-estandar.md)
- [ADR-0013](./ADR-0013-check-unico-ci-gate.md)
- [ADR-0008](./ADR-0008-snippets-reales-post-oleada.md)
- [CHANGELOG.md](../../../CHANGELOG.md)
