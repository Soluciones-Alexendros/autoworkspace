# Arquitectura — repo-standard

Este repositorio es el **canon de plataforma** de Iniciativas-Alexendros: un contrato reutilizable, no un runtime.

Detalle: [`docs/architecture/overview.md`](docs/architecture/overview.md). Decisiones: [`docs/architecture/decisions/`](docs/architecture/decisions/).

## Qué hay aquí

```
contrato de flota (docs + AGENTS + CI names)
        │
        ├── stacks/     fragmentos de quality/smoke por runtime
        ├── scripts/    smoke + validador de estructura de este canon
        └── .github/    workflows, Renovate, plantillas, CODEOWNERS
```

Tres perfiles, un esqueleto:

| Perfil | Para quién | Extra sobre el anterior |
|--------|------------|-------------------------|
| **P0 Base** | Todo repo activo | README, LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, CI `quality`+`test`, CODEOWNERS, metadatos |
| **P1 Producto** | Webs, SaaS, apps, CLIs | `docs/`, AGENTS, ARCHITECTURE, `.env.example`, `smoke`, Renovate, issue/PR templates |
| **P2 Público** | Contribución externa | CoC, SUPPORT, topics ricos, `security.yml` / audit, coverage publicado |

## Gates

Orden fijo en la flota:

`quality` → `test` (unit/function + coverage) → `build` → `smoke` → (`e2e` opcional)

En **este** repo no hay artefacto de aplicación: `quality` valida el árbol canónico, `test` documenta el hook, `smoke` demuestra el contrato del script.

## Qué no unifica este canon

- El framework de aplicación (Next vs Astro vs Rust).
- El historial ni los nombres de repos existentes.
- Archivados ni forks externos.

Para aplicar el contrato a un repo que ya existe: [`docs/REUTILIZACION.md`](docs/REUTILIZACION.md).
