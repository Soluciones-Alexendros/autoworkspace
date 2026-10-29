# Spec: taxonomía v5 con role-clean-code

## Objective

Dejar el catálogo canónico en **16 skills** y 5 dominios (`plan`, `local`,
`project`, `web`, `role`), con `role-clean-code` integrado y sin nombres
retirados en el árbol vivo. El incremento ya está implementado en
`feat/local-taxonomy-validators` (PR #13). Esta especificación fija qué se
acepta como hecho antes de pasar a PLAN.

Historia de usuario: como operador del pipeline, quiero que `main` y la rama
de taxonomía describan el mismo catálogo, para que el router, el índice y los
handoffs apunten a skills que existen.

## Tech Stack

- Python 3 y Markdown. Herramientas en `tools/` (router, validador, versión).
- Node para gates locales: Husky 9, lint-staged 17, Prettier 3 (`package.json` 4.1.0).
- Forja: `github.com/Soluciones-Alexendros/autoworkspace`. Perfil declarado: P1.
- Sin runtime de producto, sin base de datos y sin autenticación.

## Commands

```text
npm test
npm run typecheck
npm run lint
bash run-validation.sh --pytest-only --smoke-only
python3 tools/skill-router/build_index.py
python3 tools/workspace-router/run.py --phase DEFINE --repo . --json
```

## Project Structure

```text
skills/<nombre>/SKILL.md     → catálogo canónico (16)
.cursor/skills/ y .pi/skills/ → symlinks locales, no versionados
tools/skill-router/          → intent-map.yaml + skill-index.json
tools/workspace-router/      → fase DEFINE…STATUS
.autoworkspace/              → project.yaml, status.yaml, esta spec
docs/TAXONOMY.md             → dominios normativos
```

Dominios vivos:

| Dominio | Skills                                                   |
| ------- | -------------------------------------------------------- |
| plan    | plan-specification, plan-continue, plan-validators       |
| local   | local-maintenance, local-security, local-email           |
| project | project-architecture, project-libraries, project-publish |
| web     | web-compliance, web-owasp, web-performance               |
| role    | role-back, role-clean-code, role-design, role-front      |

Retiradas, solo en el changelog: `system-health`, `system-maintenance`,
`system-security`, `system-proton`, `plan-validation`, `project-testing`,
`project-hooks`.

## Code Style

- Skills en inglés. Conversación y esta spec en español.
- Conventional Commits. Un merge commit integra `main`; no se reescribe historia.
- Handoffs de comportamiento y de suite apuntan a `plan-validators`.
- `role-clean-code` 1.1.0 entra en la invocación recurrente de roles
  (backend, frontend, diseño, clean-code) al empezar un plan y antes de cada
  acción de implementación.

## Testing Strategy

- Suite estándar: `npm test` (pytest de `tools/` + humo del router).
- El índice debe listar 16 skills y el router debe resolver `role-clean-code`.
- No hay UI que verificar en navegador.
- Hecho en `ac85b9e`: `npm test` en verde (34 pytest) y typecheck en el hook.

## Boundaries

- Always: correr `npm test` antes de un commit; no dejar marcadores de conflicto; mantener el índice generado con `build_index.py`.
- Ask first: push, merge del PR, remediación del árbol P1, dependencias nuevas, bump de versión publicada.
- Never: force-push, secretos, aliases o carpetas vacías de las skills retiradas, reescribir entradas históricas del changelog.

## Success Criteria

1. `skills/` y `skill-index.json` contienen las mismas 16 skills, incluido `role-clean-code`.
2. `docs/TAXONOMY.md`, `README.md`, `AGENTS.md` y `docs/harness-integration.md` dicen 16 skills y dominio `local`, no `system`.
3. Ningún fichero vivo enlaza a `project-testing`, `project-hooks`, `plan-validation` o `system-*` como skill actual. El changelog histórico puede nombrarlas. La ruta de estado de AppArmor en `local-security` no es un nombre de skill.
4. `npm test` pasa en el commit de integración.
5. El PR #13 está en origin y `package.json` va por delante del tag `v4.1.0`.

## Open Questions

1. Resuelta: la rama está publicada. El PR #13 dejó de estar `CONFLICTING`.
2. Resuelta en parte: el README lleva la meta-sección «Propósito de este documento» y la versión 5.0.0. El resto de la brecha P1 (CONTRIBUTING.md en la raíz, `ci.yml`, ARCHITECTURE.md, Makefile, `.env.example`, `docs/{architecture,guides,runbooks,README.md}` y la plantilla de PR) queda fuera.
3. Resuelta el 2026-10-17: tras aprobar la spec, el siguiente paso es PLAN
   (`tasks/plan.md`). INTEGRATE espera a que el plan y las tareas se aprueben.

## Assumptions

1. El incremento es una sola capacidad: cerrar el catálogo v5 con `role-clean-code`. No hay mapa de módulos aparte.
2. El check `cut_tag.py --check-repo` exige `package.json` por delante del tag porque `CHANGELOG.md` cambió. La versión del repo pasa a 5.0.0 y las notas salen de `[Unreleased]`.
3. `role-clean-code` 1.1.0 es el ajuste de handoffs a `plan-validators`, no un cambio de método.
4. Los hallazgos P2 de estructura del tablero de inicio son reales frente al canon P1 y no bloquean este merge.
5. El cierre autorizado es merge commit del PR #13 (`--auto --merge`), sin tag manual ni `gh release create`.
