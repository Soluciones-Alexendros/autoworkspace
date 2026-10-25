---
version: "1.0.0"
date: "2026-10-25"
status: "Accepted"
adr_id: "ADR-0016"
priority: "P0"
---

# ADR-0016: autoworkspace es el host del canon de flota

**Fecha:** 2026-10-25
**Estado:** Accepted
**Prioridad:** P0

### Propósito de este documento

- **Objetivos:** Cerrar que el host público y único del canon (reusables, ADRs, plantillas, stacks) es `Soluciones-Alexendros/autoworkspace`, no `repo-standard`.
- **Estructura:** Frontmatter → H1 → esta meta-sección → Contexto, Decisión, Consecuencias, Prioridad, Checklist, Alternativas, Relacionados.
- **Contenido a integrar según contexto:** No copies este ADR a un producto. Los callers pinean `autoworkspace/.github/workflows/reusable-*.yml@<SHA>`.

## Contexto

`repo-standard` era el canon privado (P1: ci-gate, reusables, ADRs). `autoworkspace` ya era público y tenía una copia desfasada del canon. GitHub Actions **no sigue redirecciones** de repos renombrados o movidos: había que elegir host **antes** de que la flota pineara callers (P3+). Un caller público solo puede usar reusables de repos públicos; la cuenta personal `Alexendros` tampoco cabía en la Access policy de un host privado de org.

Análisis y opción A: `integracion-repo-standard-autoworkspace.md` (2026-10-25).

## Decisión

1. **Host único y público:** `Soluciones-Alexendros/autoworkspace` absorbe el canon de `repo-standard@e518eb1` (P11). «repo-standard» sigue siendo el **nombre de la norma**, no el del repo host.
2. **Versión única** del producto+canon desde **autoworkspace v6.0.0**. [ADR-0010](./ADR-0010-semver-contrato-estandar.md) (SemVer del contrato) se aplica a autoworkspace: un cambio incompatible para callers es major.
3. **Callers:** `uses: Soluciones-Alexendros/autoworkspace/.github/workflows/reusable-<stack>.yml@<SHA> # vX.Y.Z`.
4. **Plantilla de producto:** `templates/repo/` sustituye «Use this template» de `repo-standard`. Crear repo: `gh repo create … && cp -a templates/repo/. <repo>/`.
5. **`repo-standard`:** se archiva (humano) con descripción «Movido a Soluciones-Alexendros/autoworkspace»; sin PR de despedida.
6. Esta decisión **supersede en parte** [ADR-0001](./ADR-0001-canon-repo-standard.md) (el host ya no es el repo `repo-standard`). [ADR-0011](./ADR-0011-bootstrap-desde-plantilla.md) queda **sustituido** por el flujo `templates/repo/` (sin bootstrap script nuevo en P11).

## Consecuencias

- Un solo `git clone` da skills, perfiles, ADRs, plantilla de planes y workflows en la misma versión.
- Cada release de skills mueve el digest de los callers; Renovate `group:allNonMajor` mitiga el ruido.
- Historial de `repo-standard` queda en el repo archivado; en `main` de autoworkspace la importación entró con squash citando `repo-standard@e518eb1` ([policy-exceptions](../../../.github/policy-exceptions.md) PR #22).

## Prioridad

**P0** — bloquea P2–P10 (callers y rulesets deben apuntar al host correcto).

## Checklist de implementación

- [x] Importación P11 T0 (`templates/repo/`, reusables, ADRs)
- [x] Consolidación raíz / AGENTS squash (T1)
- [ ] Callers `stacks/*` → autoworkspace@SHA (T5)
- [ ] `package.json` 6.0.0 + tag (T6 / release.yml)
- [ ] Archivar `repo-standard` (Alejandro)

## Alternativas

- **Host = repo-standard público:** descartado; más migración (tags v1–v5, install URLs) y seguía haciendo falta publicar el privado.
- **Dos repos (skills citan canon por tag):** descartado; no cumple «la herramienta al completo» y mantiene copias divergentes.

## Relacionados

- [ADR-0001](./ADR-0001-canon-repo-standard.md) (parcialmente superseded)
- [ADR-0010](./ADR-0010-semver-contrato-estandar.md)
- [ADR-0011](./ADR-0011-bootstrap-desde-plantilla.md) (sustituido por `templates/repo/`)
- [REUTILIZACION.md](../../REUTILIZACION.md)
