# Contribuir a repo-standard

### Propósito de este documento

- **Objetivos:** Cómo se contribuye: ramas, commits, calidad local, checklist de PR y dónde vive cada tipo de cambio.
- **Estructura:** Esta meta-sección → intro → Flujo → Commits → Calidad local → Checklist → Dónde va cada cosa → Issues.
- **Contenido a integrar según contexto:** Conserva Conventional Commits, squash y el label `automerge`. Sustituye los comandos stub por los del stack. En producto, el H1 y el primer párrafo hablan del *producto*, no del canon. Reviews: [ADR-0006](docs/architecture/decisions/ADR-0006-reviews-por-perfil.md).

Gracias por mejorar el canon de la flota Iniciativas-Alexendros.

Este repositorio **no es una aplicación**. Cambia contratos que otros repos copiarán: docs, CI, perfiles P0/P1/P2 y convenciones de stacks. Trata cada PR como un cambio de plataforma.

## Flujo

- `main` es sagrada: solo entra código vía PR verde + revisión.
- Ramas: `feat/…`, `fix/…`, `docs/…`, `chore/…`, `ci/…`, `deps/…`.
- Merge preferido: **squash**. Historia lineal. Sin force-push a `main`.
- Automerge de humanos o agentes: **solo** con checks verdes, aprobación y label `automerge`.
- Automerge de Renovate: `patch` y `minor` con CI verde. Los `major` son revisión humana.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/): `tipo(alcance): descripción`.

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`, `chore`, `build`.

Ejemplo: `docs(reutilizacion): aclara el checklist P1 para repos existentes`.

Idioma: **español** en commits, PRs y documentación.

## Calidad local (antes del PR)

```bash
make validate   # scripts/check-structure.sh — P0/P1 de este canon
make lint       # stub: en repos de producto engancha format/lint/typecheck
make test       # stub: en repos de producto engancha unit + coverage
make smoke      # scripts/smoke.sh — contrato de smoke
```

En un repo de producto el mismo Makefile debe llamar a los scripts reales del stack (ver `stacks/`).

## Checklist de PR

- [ ] CI verde: `quality`, `test`, `smoke` (y `build` / `e2e` si el producto los tiene).
- [ ] Docs actualizadas (`README.md`, `docs/`, ADR si cambia una decisión).
- [ ] `CHANGELOG.md` en `[Unreleased]` si el cambio es relevante para consumidores del estándar.
- [ ] Sin secretos ni credenciales reales.
- [ ] Si el cambio altera el contrato de flota, hay ADR o se actualiza uno existente.

## Dónde va cada cosa

| Cambio | Sitio |
|--------|--------|
| Contrato para agentes | `AGENTS.md` |
| Arquitectura del estándar | `ARCHITECTURE.md` + `docs/architecture/` |
| Cómo aplicar a un repo ya existente | `docs/REUTILIZACION.md` |
| Snippets de CI por stack | `stacks/<stack>/` |
| Gates CI de este canon | `.github/workflows/ci.yml` |
| Decisión de diseño | `docs/architecture/decisions/` |

## Issues

Usa las plantillas de `.github/ISSUE_TEMPLATE/`. Vulnerabilidades: `SECURITY.md`, nunca un issue público.
