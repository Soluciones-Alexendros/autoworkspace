# Plantilla de pull request

### Propósito de este documento

- **Objetivos:** Contrato del PR: qué/por qué, cómo probar, checklist §8 y notas de revisión.
- **Estructura:** Esta meta-sección → Qué → Por qué → Cómo probar → Lista §8 (P0 / P1 / Merge) → Notas.
- **Contenido a integrar según contexto:** Conserva el check `ci-gate` y la etiqueta opcional `hold`. Añade pasos de prueba del producto. En el body del PR, **marca** el checklist con lo que este cambio cumple. No pegues secretos ni logs con tokens.

## Qué

Resume en una o dos frases qué cambia este pull request.

## Por qué

Explica el motivo. Si cierra un issue, indica `Cierra #N`.

## Cómo probar

```bash
make validate
make test
make smoke
```

Pasos extra (si aplica):

1.
2.

## Lista de comprobación (plantilla §8)

**P0**

- [ ] README + LICENSE + CHANGELOG + SECURITY + CONTRIBUTING
- [ ] CI con jobs `pipeline` + `ci-gate`
- [ ] CODEOWNERS
- [ ] Sin secretos ni credenciales

**P1** (si el cambio toca producto / este canon)

- [ ] `docs/` actualizados (architecture / guides / runbooks)
- [ ] AGENTS.md / ARCHITECTURE.md / ADR si cambia una decisión
- [ ] Fases del reusable en verde (agregadas por `ci-gate`)
- [ ] Renovate intacto (sin `dependabot.yml` de version-updates)
- [ ] `CHANGELOG.md` `[Unreleased]` si el contrato es visible

**Merge**

- [ ] Check `ci-gate` verde
- [ ] Auto-merge squash activado (salvo etiqueta `hold`)

## Notas para revisión

<!-- consideraciones especiales -->
