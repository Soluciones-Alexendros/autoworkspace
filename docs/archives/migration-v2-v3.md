# Migración v2 → v3.0 (OpenCode, vendor-neutral)

> **Archivado (P12):** sustituido por [docs/STANDARD.md](../STANDARD.md) y [docs/TAXONOMY.md](../TAXONOMY.md). Se conserva solo como referencia histórica.

## Breaking changes

- Renaming ES → EN: operar-* → operate-_, verificar-_ → verify-_, construir-_ → build-_, disenar-_ → design-*
- Frontmatter: dominio/tipo/idioma → domain/type/language dentro de metadata
- Añadido compatibility y allowed-tools
- Eliminada toda referencia a un único vendor

## Pasos

1. git checkout -b feat/v3-standard
2. bash scripts/rename-skills.sh
3. python scripts/migrate-frontmatter.py
4. python tools/skill-router/build_index.py
5. bash run-validation.sh
6. bash scripts/install-opencode.sh
7. Test: python tools/skill-router/route.py "por donde empiezo"

## Rollback

git checkout main
