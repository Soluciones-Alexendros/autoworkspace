# Soluciones-Alexendros Autoworkspace — Routing Contract

## Discovery

All skills live in `skills/<skill-name>/SKILL.md`. Flat layout, one folder per skill. Name == directory name.

## Mandatory Rule — Cursor, Pi and Code Harness

Before ANY action, you MUST evaluate if a skill in `skills/` applies.

- Read each SKILL.md `name` and `description` (discovery phase)
- If user intent matches `description` or `metadata.keywords` or `triggers`, you MUST invoke the `skill` tool
- Follow SKILL.md exactly, including reading its `references/` when instructed
- Never skip required workflows

## Lifecycle Enforcement (Autoworkspace pipeline)

Preprogrammed flow with per-project variables in `.autoworkspace/project.yaml`:

DEFINE (plan-specification) → SCHEMAS/TESTS → IMPLEMENT (role-*) → VALIDATE (plan-validators) → INTEGRATE (project-publish) → STATUS

Route a phase with:

```bash
python tools/workspace-router/run.py --phase DEFINE --repo . --json
python tools/workspace-router/run.py --phase STATUS --repo . --bump --note "advance"
```

- Ambiguous "¿por dónde empiezo?" or "pon al día este proyecto" → plan-continue (loads/creates `.autoworkspace/`)
- Mix audit+release ("audítalo y publícalo") → plan-continue first, then project-publish
- WEB AUDITS → web-* · LOCAL (local OS) → local-*
- At plan start and before EVERY task or independent implementation action, re-evaluate the scope and invoke all matching roles: backend/API/jobs → role-back; frontend/client routes → role-front; visual direction/tokens → role-design; clean-code/refactoring → role-clean-code. Previous role invocations do not cover later actions. Mixed work requires explicit contracts and handoffs. The phase router's single skill is only a fallback, never a substitute for per-task role selection.

## Harness discovery

`skills/` is the only versioned catalog. Cursor and Pi load symlinks created by the installers; those directories are not committed.

Cursor:

- `.cursor/skills/<name>/SKILL.md`
- `~/.cursor/skills/<name>/SKILL.md`

Pi ([skills](https://pi.dev/docs/latest/skills)):

- `.pi/skills/<name>/SKILL.md`
- `~/.pi/agent/skills/<name>/SKILL.md`

Install:

```bash
bash scripts/install-cursor.sh --target .cursor/skills
bash scripts/install-pi.sh --target .pi/skills
```

## Language

Skill bodies and technical contracts are written in English. Frontmatter `description` is bilingual (EN + ES triggers) for discovery. Operator-facing plans and reports in this repo may be Spanish. Canonical detail: `docs/STANDARD.md` and the fleet canon under `docs/architecture/`, `docs/REUTILIZACION.md`, `stacks/`, and `templates/product/`.

This repository **complies with the fleet contract** in `templates/product/AGENTS.md` §1–8 (ci-gate, squash auto-merge, Renovate-only, plan/* flow when adopted).

Canonical vocabulary (plan branch, task branch, `ci-gate`, `pipeline-<stack>`, publication, ADR states, language rule): [`docs/GLOSARIO.md`](docs/GLOSARIO.md).

## Progressive Disclosure

SKILL.md body should stay focused (repo gate: ≤500 lines / token budget in `tools/validate/skill_spec.py`). Prefer <200 lines when practical. Heavy docs live in `references/`. Read them only when SKILL.md says so.

## Learned User Preferences

- Al cerrar el modo BUILD de un plan (implementación completa): validar en local (pre-commit / que el proyecto monte) antes de sincronizar; crear el commit sin esperar a que el usuario diga «commit»; crear el PR según el plan; el verde local debe anticipar CI verde.
- Tras abrir el PR: `gh pr merge <n> --auto --squash --delete-branch`. Prohibido `--merge`, `--rebase` y `--admin`. Flujo `plan/*`: PRs de tarea → rama `plan/<id>-<slug>`; el PR del plan → `main`. Suscribir `subscribe_github_ci` (rama head) + `subscribe_github_pr` (scope pr), declarar qué se espera y terminar el turno — escuchar notificaciones de fallo o merge; no hacer polling/babysitting.
- Revisar o adjuntar un plan no autoriza implementación ni publicación: hace falta orden explícita del operador. Commit, push, PR, merge, tag, release y mutaciones de host requieren autorización específica; si el plan las excluye, prevalecen esos límites sobre el cierre BUILD habitual.
- Un incremento lleva un único plan canónico (p. ej. `tasks/plan-*.md`) como fuente de verdad; no crear trackers paralelos (`SPEC.md`, `tasks/todo.md`) ni sobrescribir planes históricos. Los todos internos solo reflejan ese documento.
- No crear skills de lenguajes de programación ni nuevas familias de skills; para dudas o fallos de lenguaje usar Context7 / documentación oficial vigente.
- No invocar `role-front` ni `role-design` sin una superficie UI/visual real que lo requiera.
- En puertas y aceptación: no convertir dependencia ausente, skip u omisión en PASS; usar `blocked` / `not_applicable` / `not_run` con motivo. Un `not_applicable` obligatorio debe justificarse con regla verificable.

## Learned Workspace Facts

- El catálogo canónico son 16 skills en 5 dominios: `plan`, `local`, `project`, `web`, `role` (prefijo del nombre = dominio).
- Producto: **autoworkspace** — pipeline agéntico, no vitrina de skills.
- Fuente canónica de skills en el checkout: `skills/<nombre>/SKILL.md`; no asumir que `.agents/skills/` existe o apunta al destino correcto sin resolver el enlace.
- Actualización de dependencias: Renovate (no Dependabot).
- Copia desechable, venv o HOME temporal no es sandbox de seguridad para scripts `local-*` (pueden tocar rutas absolutas, credenciales del proceso o red); inspeccionar antes de ejecutar y preferir deny-by-default en entrypoints mutadores.
- La ejecución controlada de operaciones de skill pasa por contratos `execution.yaml` y la capa `tools/execution/` (approval/ops/registry/evidence), no por invocación libre de scripts.
