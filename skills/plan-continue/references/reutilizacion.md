# Reutilización del canon (resumen)

Checklist y orden para alinear un repo existente:
[`docs/REUTILIZACION.md`](../../../docs/REUTILIZACION.md).

Repo nuevo: `gh repo create … && cp -a templates/product/. <repo>/`
([ADR-0016](../../../docs/architecture/decisions/ADR-0016-autoworkspace-host-del-canon.md)).

Merge de flota: `gh pr merge --auto --squash`. Required check: `ci-gate`
([ADR-0012](../../../docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md),
[ADR-0013](../../../docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)).
**No** exijas la etiqueta `automerge`.
