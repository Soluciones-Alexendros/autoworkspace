# Documentación de repo-standard

Índice del canon. La raíz del repo (`README.md`, `ARCHITECTURE.md`, `AGENTS.md`) son **resúmenes**; el detalle vive aquí.

## Para quién

| Eres… | Empieza por |
|-------|-------------|
| Mantenedor alineando un repo existente | [REUTILIZACION.md](./REUTILIZACION.md) |
| Alguien que crea un repo nuevo | [README raíz](../README.md) → Quickstart A |
| Agente / Mantenedor implementando | [AGENTS.md](../AGENTS.md) + [guides/](./guides/) |
| Ops / incidente | [runbooks/](./runbooks/) |
| Diseño del estándar | [architecture/overview.md](./architecture/overview.md) y [decisions/](./architecture/decisions/) |

## Mapa

```
docs/
├── README.md                 ← estás aquí
├── REUTILIZACION.md          ← aplicar el estándar a un repo existente
├── architecture/
│   ├── overview.md
│   └── decisions/            ← ADRs
├── guides/
│   ├── local-setup.md
│   ├── coding-standards.md
│   └── testing.md
├── runbooks/
│   ├── deploy.md
│   ├── rollback.md
│   └── rotate-secrets.md
├── api/                      ← créala cuando haya contrato OpenAPI
└── archive/                  ← docs históricas; no borrar a ciegas
```

`api/` y `archive/` son huecos del árbol P1: créalos en el repo de producto cuando existan contratos o documentos retirados.

## Relacionados en raíz

- [CONTRIBUTING.md](../CONTRIBUTING.md) — ramas, commits, checklist de PR
- [SECURITY.md](../SECURITY.md) — canal de vulnerabilidades
- [CHANGELOG.md](../CHANGELOG.md) — solo cambios de release
- [stacks/](../stacks/) — snippets CI por runtime
