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
- [ ] CI con jobs `quality` + `test`
- [ ] CODEOWNERS
- [ ] Sin secretos ni credenciales

**P1** (si el cambio toca producto / este canon)

- [ ] `docs/` actualizados (architecture / guides / runbooks)
- [ ] AGENTS.md / ARCHITECTURE.md / ADR si cambia una decisión
- [ ] Job `smoke` verde
- [ ] Renovate intacto (sin `dependabot.yml` de version-updates)
- [ ] `CHANGELOG.md` `[Unreleased]` si el contrato es visible

**Merge**

- [ ] Checks `quality`, `test`, `smoke` verdes
- [ ] Automerge humano solo con label `automerge`

## Notas para revisión

<!-- consideraciones especiales -->
