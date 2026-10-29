# Documentación de `<repo>`

### Propósito de este documento

- **Objetivos:** Índice de `docs/` y mapa de a quién le toca cada carpeta.
- **Estructura:** Esta meta-sección → Para quién → Mapa del árbol → Relacionados en raíz. Huecos `api/` y `archive/` cuando existan.
- **Contenido a integrar según contexto:** En producto, cambia el H1 y la tabla «Para quién». Añade `api/` si hay OpenAPI y `archive/` si retiras docs. Cada `.md` contractual debe llevar la meta-sección «Propósito de este documento» ([REUTILIZACION.md](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/REUTILIZACION.md)).

Índice del canon. La raíz del repo (`README.md`, `ARCHITECTURE.md`, `AGENTS.md`) son **resúmenes**; el detalle vive aquí.

## Para quién

| Eres…                                  | Empieza por                                                                                                                                                                                                                              |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mantenedor alineando un repo existente | [REUTILIZACION.md](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/REUTILIZACION.md)                                                                                                                               |
| Alguien que crea un repo nuevo         | [README raíz](../README.md) → Quickstart A                                                                                                                                                                                               |
| Agente / Mantenedor implementando      | [AGENTS.md](../AGENTS.md) + [guides/](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/guides/)                                                                                                                     |
| Ops / incidente                        | [runbooks/](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/runbooks/)                                                                                                                                             |
| Diseño del estándar                    | [architecture/overview.md](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/overview.md) y [decisions/](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/) |

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
- [stacks/](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/stacks/) — callers CI por runtime (pin SHA del reusable)
