# Soluciones-Alexendros Autoworkspace — Routing Contract

## Discovery

All skills live in `skills/<skill-name>/SKILL.md`. Flat layout, one folder per skill. Name == directory name.

## Mandatory Rule — OpenCode & Code Harness

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

## OpenCode Specific

OpenCode searches in this order:

- .opencode/skills/<name>/SKILL.md
- ~/.config/opencode/skills/<name>/SKILL.md
- .agents/skills/<name>/SKILL.md
- ./skills/<name>/SKILL.md (project fallback)

The agent must load `opencode.json` for `skills.paths` (OpenCode ≥1.18; not the obsolete `skillDirectories` key).

## Language

Skill bodies and technical contracts are written in English. Frontmatter `description` is bilingual (EN + ES triggers) for discovery. Operator-facing plans and reports in this repo may be Spanish. Canonical detail: `docs/STANDARD.md` and `docs/repo-standard/`.

## Progressive Disclosure

SKILL.md body should stay focused (repo gate: ≤500 lines / token budget in `tools/validate/skill_spec.py`). Prefer <200 lines when practical. Heavy docs live in `references/`. Read them only when SKILL.md says so.

## Learned User Preferences

- Al cerrar el modo BUILD de un plan (implementación completa): validar en local (pre-commit / que el proyecto monte) antes de sincronizar; crear el commit sin esperar a que el usuario diga «commit»; crear el PR según el plan; el verde local debe anticipar CI verde.
- Tras abrir el PR: `gh pr merge <n> --auto --merge --delete-branch` (merge commit; nunca squash/rebase/`--admin`). Suscribir `subscribe_github_ci` (rama head) + `subscribe_github_pr` (scope pr), declarar qué se espera y terminar el turno — escuchar notificaciones de fallo o merge; no hacer polling/babysitting.
- No crear skills de lenguajes de programación; para dudas o fallos de lenguaje usar Context7 / documentación oficial vigente.

## Learned Workspace Facts

- El catálogo canónico son 16 skills en 5 dominios: `plan`, `local`, `project`, `web`, `role` (prefijo del nombre = dominio).
- Producto: **autoworkspace** — pipeline agéntico, no vitrina de skills.
- Actualización de dependencias: Renovate (no Dependabot).
