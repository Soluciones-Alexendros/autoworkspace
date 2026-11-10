# G — Cierre de trabajo al finalizar un plan

Cierra el incremento que el plan acaba de implementar. No es una auditoría del repo ni un corte de versión: es la cola de `/execute-plan` (o de un `task_plan.md` con todas las fases `complete`).

Leer este fichero cuando el operador pida repo ending, cierre de trabajo, finalizar el plan, mergear el plan o ship del plan. Tras `/execute-plan` con PRs abiertos, continuar aquí: el informe de stack no es el final.

## Autorización

Pedir este cierre autoriza, en el repo del plan:

1. Ejecutar el gate local (Husky, typecheck, tests, e2e).
2. Una ronda crítica de revisión contra el resultado esperado del plan y los commits de corrección.
3. Abrir o actualizar PRs contra `main` (draft → ready).
4. Auto-merge con **squash** (`--auto --squash`) y suscripción a CI/PR
   (escuchar avisos; no `--merge` / `--rebase` / `--admin`). Norma de flota:
   [ADR-0012](../../../docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md).
5. Borrar ramas ya mergeadas y temporales locales del plan.

Sigue exigiendo sí aparte: tag anotado, `gh release create`, borrar el repositorio remoto, tocar repos archivados o `voicebox`. Nunca force-push a `main`/`master`.

## Precondiciones

- `gh auth status` OK. Remoto `github.com`.
- Rama por defecto del remoto (`defaultBranchRef`); en la flota es `main`.
- Repo no archivado. Si es `voicebox` o archivado: parar y preguntar.
- Plan localizable: design doc de `/execute-plan`, o `task_plan.md` / `.planning/<id>/task_plan.md` con fases `complete`.
- Árbol de trabajo: commits del plan en ramas de feature, no en `main`.

Si falta health check y el repo es desconocido: derivar a `plan-continue` Fase 8 y volver.

## Secuencia

Ejecutar en orden. Un paso en rojo detiene el siguiente hasta corregir.

### 1. Gate Husky integrado

Usar `scripts/gate-husky.sh` de esta skill. Si no hay `.husky/pre-commit`, lo configura (modo instalar). Luego ejecuta el **modo gate** sobre el head del plan, no solo deja el hook instalado.

Esperado: lint-staged, typecheck y tests unitarios en verde. Error: corregir en la rama del PR, repetir el gate. Recovery: si `package.json` no declara `typecheck` o `test`, omitir esa línea y anotarlo.

### 2. Gate e2e Playwright

Si el repo tiene UI o scripts `e2e` / `test:e2e` / `playwright`: cargar `webapp-testing` (o Playwright MCP) y ejercitar el flujo que el plan promete.

Precondition: servidor de desarrollo o preview del propio repo. Action: Chromium headless, aserciones del flujo, fallo con mensaje claro. Expected: 0 fallos. Error: última tanda de correcciones (paso 3) y repetir. Recovery: sin UI y sin script e2e → `N/A` y seguir.

El e2e del cierre vive aquí. El pre-commit de Husky sigue siendo rápido (lint + tipos + unit). Si existe script e2e, esta misma skill puede dejarlo en `pre-push`.

### 3. Revisión crítica contra el plan

Leer el plan y el diff `main...HEAD` de cada PR. Lanzar un reviewer (persona `reviewer`; `security-auditor` si hay auth/secretos/input). Alcance: ¿el resultado esperado del plan está en el diff? Bugs y desviaciones se corrigen ahora. Nits de estilo que el plan no pide se dejan.

Expected: 0 bugs abiertos relativos al plan. Error: implementer corrige, commit, repetir gate 1–2. Recovery: desacuerdo reviewer/implementer → escalar al operador; su decisión cierra el ítem.

### 4. PRs contra main

Si `/execute-plan` ya abrió PRs (Graphite stack o `gh pr create`): reutilizarlos, marcar ready cuando el gate esté verde. Si no hay PR:

```bash
gh pr create --base main --head <rama> --fill --draft
```

Un PR por incremento lineal; en stack, base = padre del stack, el fondo contra `main`. Título y cuerpo en el idioma del plan. Squash (`--squash`) es la política de flota; nunca `--merge`, `--rebase` ni `--admin`.

Tags y changelog: solo si el plan incluye bump de versión. Entonces Fases B y F de `SKILL.md` **antes** del tag. Un sí a este cierre no publica una release.

### 5. Merge-watch (escuchar)

Seguir `merge-watch.md`:

```bash
gh pr merge <n> --auto --squash --delete-branch
```

Luego `subscribe_github_ci` (rama head) + `subscribe_github_pr` (scope pr), declarar qué se espera y **terminar el turno**. No polling. Ante notificación de fallo → corregir y re-suscribir; ante merged → paso 6.

Un job no requerido en rojo se documenta y no bloquea el auto-merge si los required están verdes.

### 6. Limpieza

Tras MERGED:

```bash
git fetch --prune origin
git checkout main
git pull --ff-only origin main
git branch --merged main | grep -v '^\*' | grep -v main | xargs -r git branch -d
```

Borrar worktrees del plan (`grok worktree rm --force` si el aislamiento los creó). Borrar scratch del plan (resúmenes, reviews) con el helper de host del skill, no a mano en `/tmp`. Conservar el state file de `/execute-plan` hasta que el operador lo pida. No borrar el repositorio remoto. No `git clean -x`.

## Entregable

```markdown
## Cierre de trabajo

| Paso             | Estado          | Nota               |
| ---------------- | --------------- | ------------------ |
| Husky            | OK / FAIL       |                    |
| e2e              | OK / N/A / FAIL |                    |
| Revisión vs plan | OK              | bugs corregidos: N |
| PR               | #N MERGED       | squash, SHA        |
| Limpieza         | OK              | ramas y worktrees  |
```

Si un paso queda `FAIL` o bloqueado, la tabla lo dice y el siguiente no se finge hecho.
