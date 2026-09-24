# Runbook — deploy

### Propósito de este documento

- **Objetivos:** Pasos para publicar (canon = merge + tag; producto = hosting real).
- **Estructura:** Esta meta-sección → procedimiento de este repo → plantilla de producto → qué no hacer.
- **Contenido a integrar según contexto:** En producto, **sustituye** el apartado de hosting (Vercel, Docker, Cargo release…). Confirma Environments y reviewers. Cero secretos en el texto. Post-check = smoke contra el artefacto, no logs con credenciales.

Este canon **no se despliega** a un hosting de aplicación. «Publicar» el estándar es mergear a `main` y, cuando toque, etiquetar SemVer.

## Canon (este repo)

1. PR a `main` con CI `quality` + `test` + `smoke` verde.
2. Review de CODEOWNERS (`@Alexendros`).
3. Squash merge. No deploy desde la rama de feature.
4. Release opcional: tag SemVer + entrada en `CHANGELOG.md` (mueve `[Unreleased]`).
5. Los consumidores actualizan copiando contratos o abriendo PRs de alineación ([REUTILIZACION.md](../REUTILIZACION.md)).

## Repos de producto (plantilla para copiar)

Sustituye este apartado por el hosting real:

1. Confirma Environments (`preview`, `production`) y que `production` exige reviewer.
2. Preview: deploy automático desde PR **solo** si el producto lo tiene (Vercel, Docker preview, etc.).
3. Production: workflow `release.yml` en tag o botón manual. Nunca desde un PR de feature.
4. Post-check: ejecuta el smoke contra la URL/artefacto publicado (no contra prod secrets en el log).
5. Si falla: [rollback.md](./rollback.md).

## Qué no hacer

- Meter secretos en el workflow o en el repo.
- Desplegar con CI rojo.
- Saltar Environments protegidos.
