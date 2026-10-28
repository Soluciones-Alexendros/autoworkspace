# Documentación

### Propósito de este documento

- **Objetivos:** Índice de la documentación del producto autoworkspace y del canon de flota alojado aquí ([ADR-0016](architecture/decisions/ADR-0016-autoworkspace-host-del-canon.md)).
- **Estructura:** Esta meta-sección → guías de producto → canon de flota → planes → raíz.
- **Contenido a integrar según contexto:** El README raíz presenta el producto; este índice solo navega `docs/`.

## Guías de producto

| Documento                          | Contenido                                                |
| ---------------------------------- | -------------------------------------------------------- |
| [STANDARD.md](STANDARD.md)         | Contrato de `SKILL.md` (frontmatter, longitud, headings) |
| [TAXONOMY.md](TAXONOMY.md)         | Dominios y tipos de skill                                |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Puntero a la guía canónica en la raíz                    |

## Canon de flota

| Documento                                            | Contenido                                                            |
| ---------------------------------------------------- | -------------------------------------------------------------------- |
| [REUTILIZACION.md](REUTILIZACION.md)                 | Alinear un repo existente; crear desde `templates/repo/`             |
| [architecture/overview.md](architecture/overview.md) | Diseño del canon                                                     |
| [architecture/decisions/](architecture/decisions/)   | ADRs (0001…0016)                                                     |
| [guides/](guides/)                                   | Setup, estilo, tests                                                 |
| [runbooks/](runbooks/)                               | Deploy, rollback, secretos                                           |
| [plan-template.md](plan-template.md)                 | Cabecera NORMA DE FLOTA + esqueleto de plan-prompt                   |
| [plans/](plans/)                                     | Plan-prompts P1–P11 (Notion → `NOTION_POLICY_PAGE`)                  |
| [archives/](archives/)                               | Documentos históricos retirados (`skill-spec-v3`, `migration-v2-v3`) |

Política vigente: check único `ci-gate`, merge `gh pr merge --auto --squash`, **sin** exigir etiqueta `automerge` ([ADR-0012](architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md), [ADR-0013](architecture/decisions/ADR-0013-check-unico-ci-gate.md)).

## Raíz del repo

- [CONTRIBUTING.md](../CONTRIBUTING.md) — cómo contribuir
- [ARCHITECTURE.md](../ARCHITECTURE.md) — pipeline, capas canon/CI
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) — conducta de la comunidad
- [SECURITY.md](../SECURITY.md) — divulgación de vulnerabilidades
- [AGENTS.md](../AGENTS.md) — contrato de enrutado + flota
- [templates/repo/](../templates/repo/) — esqueleto P0/P1 de producto
