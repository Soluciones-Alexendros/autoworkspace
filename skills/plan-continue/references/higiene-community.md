# Higiene de repositorio (community standards)

Checklist absorbida de la antigua skill `repo-hygiene`. Solo lectura; la remediación va en las fases 5–6 de `plan-continue` tras confirmación.

Para la flota Soluciones-Alexendros el contrato P0/P1/P2 completo está en `references/` (fuente: [repo-standard](https://github.com/Soluciones-Alexendros/autoworkspace)). Esta hoja cubre el mínimo community standards cuando el repo aún no se alinea al canon de flota.

## Checks obligatorios

| ID | Qué verificar | Severidad si falta |
|----|---------------|-------------------|
| repo-001 | `README.md` (o `README`) con propósito e instalación | high |
| repo-002 | `LICENSE` o `LICENSE.md` | high (público) / medium (privado) |
| repo-003 | `.gitignore` acorde al stack | high |
| repo-004 | `CHANGELOG.md` o sección de cambios en README | medium |
| repo-005 | `CONTRIBUTING.md` si el repo acepta PRs externos | medium |
| repo-006 | Al menos un workflow en `.github/workflows/` con job de test o lint | high |
| repo-007 | Ningún `.env` real trackeado (excluir `.env.example`, `.env.sample`, `.env.template`) | critical |
| repo-008 | Sin binarios grandes (>1 MiB) en el índice git | medium |

## Cómo comprobar

```bash
# Documentación y licencia
test -f README.md -o -f README
ls LICENSE* 2>/dev/null
test -f .gitignore
test -f CHANGELOG.md

# CI
ls .github/workflows/*.{yml,yaml} 2>/dev/null

# Secretos trackeados (excluir plantillas)
git ls-files | grep -E '(^|/)\.env($|\.)' | grep -vE '\.env\.(example|sample|template)$' || true

# Binarios grandes en el índice
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '/^blob/ && $3 > 1048576 { print $3, $4 }' | sort -nr | head
```

## Remediación tipica (solo tras sí del operador)

- Añadir plantillas mínimas desde el canon del stack, no inventar licencia.
- `git rm --cached .env` y rotar la credencial fuera de esta pasada.
- Mover assets grandes a LFS o a almacenamiento externo si el operador lo pide.
