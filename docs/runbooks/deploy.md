# Runbook — deploy

### Propósito de este documento

- **Objetivos:** Pasos para publicar el canon (merge del plan + tag) y, en producto, para desplegar a su hosting real.
- **Estructura:** Esta meta-sección → canon (este repo) → repos de producto → qué no hacer.
- **Contenido a integrar según contexto:** En producto, **sustituye** el apartado de hosting (Vercel, Docker, Cargo release…). Confirma Environments y reviewers. Cero secretos en el texto. Post-check = smoke contra el artefacto, no logs con credenciales.

El canon **no se despliega** a un hosting de aplicación. «Publicar» el canon es fusionar el PR del plan a `main` y dejar que se corte el tag SemVer.

## Canon (este repo)

El flujo tiene dos fases ([docs/plan-template.md](../plan-template.md)):

1. **Fase 1 — integración.** Cada tarea va en su rama `rama de tarea` y abre un PR de tarea con squash hacia `plan/<id>-<slug>`. `ci-gate` verde es el único check obligatorio ([ADR-0013](../architecture/decisions/ADR-0013-check-unico-ci-gate.md)); no hay approvals de revisor ([ADR-0012](../architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).
2. **Fase 2 — publicación.** El PR del plan (`plan/<id>-<slug>` → `main`) se fusiona con squash. Al fusionar, `release.yml` corta el tag `vX.Y.Z` sobre `main` y crea la GitHub Release.

Reglas:

- El merge es siempre squash (`gh pr merge --auto --squash`). Prohibidos `--merge`, `--rebase` y `--admin`.
- El PR del plan lo abre y lo fusiona Alejandro; ningún agente lo marca listo ni lo fusiona.
- Los consumidores se alinean copiando contratos o abriendo PRs propios ([REUTILIZACION.md](../REUTILIZACION.md)).

> **Nota (hoy).** Hasta P2/P10, `release.yml` corta el tag y crea la Release. El destino es `publish.yml` desde tag `v*` (`push: tags`), con el tag creado por release-please usando la GitHub App de flota; mientras eso no esté fusionado, no hay `publish.yml` ni release-please en la ruta de publicación.

## Repos de producto (plantilla para copiar)

Sustituye este apartado por el hosting real:

1. Confirma el entorno `production`: solo despliega tags `v*` y no lleva revisor ni bypass de administradores.
2. Preview: deploy automático desde PR **solo** si el producto lo tiene (Vercel, Docker preview, etc.).
3. Producción: workflow de publicación disparado por el tag `v*`. Nunca desde una rama de tarea ni desde un PR.
4. Post-check: ejecuta el smoke contra la URL/artefacto publicado (no contra secretos de producción en el log).
5. Si falla: [rollback.md](./rollback.md).

## Qué no hacer

- Meter secretos en el workflow o en el repo.
- Desplegar con `ci-gate` en rojo.
- Publicar desde un PR, o crear/mover tags a mano.
- Saltar los entornos protegidos.
