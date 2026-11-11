<!-- tasks/plan-machineroom-rename-harness.md · Plan SDD canónico (self-change) · no crear trackers paralelos -->

NORMA DE FLOTA (autoworkspace→machineroom, self-change). Plan `machineroom-rename-harness` «Rediseño de harness (Pi + Cursor) y rename a machineroom» · repo: `Soluciones-Alexendros/autoworkspace` (→ `Soluciones-Alexendros/machineroom`).

Reglas de flujo heredadas del canon y aplicadas a este self-change: rama de integración `plan/machineroom-rename-harness` desde `main` con PR borrador → `main`; cada tarea = rama de trabajo → PR a la rama del plan (nunca a `main`), título Conventional, `gh pr merge --auto --squash`. Prohibido `--merge`, `--rebase`, `--admin`, push directo y tocar rulesets/entornos. Commit/push/PR/merge/rename de repo y mutaciones de host requieren autorización explícita del operador. Este documento es la única fuente de verdad del incremento. No iniciar implementación sin orden explícita.

---

## 1. Repos

- `Soluciones-Alexendros/autoworkspace` → **`Soluciones-Alexendros/machineroom`** (rename de forja, tarea 10, con autorización).
- Local: `~/Work/autoworkspace` → **`~/Work/machineroom`** (tarea 10).

## 2. Contexto — resultado de la inspección

Inspección completa de Pi (terminal) y Cursor (IDE) realizada el día de este plan. Inventario y hallazgos.

### 2.1 Pi (terminal)

| Superficie | Ruta                                     | Estado                                                                                                                                                                                                                                                                                                                       |
| ---------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Settings   | `~/.pi/agent/settings.json`              | tema `omarchy-system`, `defaultModel` `deepseek-v4.1-flash-free`, `defaultProvider: opencode`, `defaultThinkingLevel: max`, `defaultProjectTrust: ask`, thinking-level por modelo, `tuiMode: fullscreen`, `shellCommandPrefix: export CI=1`. `enabledModels` incluye 5 ids `opencode-go/*` que **no** están en `models.json` |
| Models     | `~/.pi/agent/models.json`                | 1 provider `opencode` × 3 modelos free (nemotron, deepseek, glm). Distinto del set activo: `models.json` es ese catálogo; `settings.json` es más amplio                                                                                                                                                                      |
| AGENTS.md  | `~/.pi/agent/AGENTS.md`                  | Contexto del operador (español). No es el contrato de ejecución                                                                                                                                                                                                                                                              |
| Prompts    | `~/.pi/agent/prompts/verify.md`          | 1 plantilla                                                                                                                                                                                                                                                                                                                  |
| Themes     | `~/.pi/agent/themes/omarchy-system.json` | 1 tema                                                                                                                                                                                                                                                                                                                       |
| Skills     | `~/.pi/agent/skills/`                    | 17 symlinks → `~/.autoworkspace/skills/<name>` + manifest; 3 skills OS (`diagnose-crash`, `omarchy`, `omarchy-app`) → `/usr/share/omarchy/...`                                                                                                                                                                               |
| Extensions | `~/.pi/agent/extensions/`                | `autoworkspace.ts` (symlink → runtime `extensions/autoworkspace/index.ts`) y `path-guard.ts`                                                                                                                                                                                                                                 |
| MCP        | `~/.pi/agent/mcp.json`                   | 5 servidores (ver §2.3)                                                                                                                                                                                                                                                                                                      |

Capacidades de la extensión Pi (`extensions/autoworkspace/index.ts`):

- Comando `/aw-status` (marcador de carga).
- Tool `aw_subagent`: lanza un proceso `pi` aislado (`--no-session`, `-p`, `--tools read,grep,find,ls[,write,edit][,bash]`), con `ALLOWED_SKILLS` (7 skills, whitelist hardcoded), `allowedCwd` (cwd o subdirectorio, o `/tmp/autoworkspace-*`), timeout, y parseo JSONL.
- `path-guard.ts`: gate de `write`/`edit` (bloqueo duro + confirmación) para rutas sensibles fuera de `~/Work/` (`~/.ssh`, `~/.gnupg`, `~/.config/hypr`, `~/.pi/agent/extensions`, `~/.aws`, `~/.kube`, `auth.json`, home raíz, segmentos `.env`/`.git`/`node_modules`; confirmación para `settings.json`, `mcp.json`, `AGENTS.md`, `~/.bashrc`, etc.).

### 2.2 Cursor (IDE)

| Superficie | Ruta (repo)                                                              | Estado                                                                                                                |
| ---------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Rules      | `.cursor/rules/autoworkspace.mdc`                                        | `alwaysApply: true`, contrato de ejecución                                                                            |
| Hooks      | `.cursor/hooks.json` + `.cursor/hooks/{session_start.py, shell_gate.py}` | `sessionStart` (fire-and-forget, inyecta contrato) + `beforeShellExecution` (gate deny/ask/allow, `failClosed: true`) |
| Agents     | `.cursor/agents/{aw-planner, aw-verifier, aw-worker}.md`                 | planner (readonly), verifier (readonly), worker                                                                       |
| Skills     | `.cursor/skills/`                                                        | 17 symlinks (no versionados) + manifest                                                                               |
| Plugin     | `.cursor-plugin/{marketplace.json, plugin.json}`                         | distribución nativa Cursor                                                                                            |

Runtime usuario `~/.cursor/`: `agents/*.md`, `hooks/*.py`, `hooks.json` (symlink → `~/.autoworkspace/.cursor/hooks.json`), `skills/` (17 symlinks relativos), `.autoworkspace-full-manifest.json`. `~/.cursor/skills-cursor/` son skills nativas de Cursor, fuera del alcance de este repo.

### 2.3 MCP

| Servidor          | Pi                                                       | Cursor                                      | Notas       |
| ----------------- | -------------------------------------------------------- | ------------------------------------------- | ----------- |
| `github`          | deferred, token `!gh auth token`, `toolExposure` parcial | solo este (vía wrapper `cursor-github-mcp`) | —           |
| `context7`        | codemode                                                 | **ausente**                                 | sin secreto |
| `playwright`      | codemode (npx)                                           | **ausente**                                 | sin secreto |
| `chrome-devtools` | codemode (npx)                                           | **ausente**                                 | sin secreto |
| `notion`          | deferred (OAuth)                                         | **ausente**                                 | OAuth       |

### 2.4 Runtime compartido `~/.autoworkspace`

`skills/`, `.cursor/{agents,hooks,rules,hooks.json}`, `extensions/autoworkspace/{index.ts,agents/worker.md}`, `package.json`, `.runtime-manifest.json`. Constante `RUNTIME_DIRNAME = ".autoworkspace"` en `tools/harness/runtime.py`. Instaladores: `scripts/{install-cursor.sh, install-pi.sh, install.sh, runtime-sync.sh, bootstrap.sh, lib/link-skills.sh}`.

`path-guard.ts` hoy es un fichero suelto en `~/.pi/agent/extensions/` (no está en el repo ni en el runtime). Entra al repo en `extensions/machineroom/path-guard.ts`, enlazado desde `~/.pi/agent/extensions/`. El install sustituye ese fichero suelto. Sin ese alta, el gate queda fuera del PR y del doctor (tarea 5).

### 2.5 Hallazgos (deriva y huecos)

1. **Recuento de skills en deriva**: `README.md`, `docs/TAXONOMY.md` y `skill-index.json` dicen 17; `ARCHITECTURE.md` y `.autoworkspace/SPEC.md` dicen 16 (SPEC además es v5/`role-clean-code`, obsoleta).
2. **Asimetría de contrato de ejecución entre harnesses**: Cursor tiene `shell_gate.py` (gate de bash host/red) + rule `alwaysApply`. Pi solo tiene `path-guard` (gate de write/edit) y **no** tiene gate de comandos bash/`!`, ni rule `alwaysApply` equivalente (su `AGENTS.md` de usuario es contexto de operador; el contrato vive disperso en el `AGENTS.md` del repo y en las skills).
3. **Contrato en dos textos largos y un resumen**: `.cursor/rules/autoworkspace.mdc` y `AGENTS.md` son dos textos largos. `.cursor/hooks/session_start.py` ya inyecta un resumen, no una tercera copia íntegra. D5 añade el check de paridad de ese resumen contra el SSOT; no consiste en «dejar de copiar el texto completo».
4. **Forma de `hooks.json` cerrada** (ya no es pregunta): proyecto = `python3 .cursor/hooks/...`; usuario = `python3 hooks/...`. Lo exigen `write_user_hooks_config` en `tools/harness/runtime.py`, `tools/harness/tests/test_runtime.py` y `scripts/tests/test_install.sh`. El runtime vivo (`~/.autoworkspace/.cursor/hooks.json`, symlink desde `~/.cursor/hooks.json`) sigue en `python3 .cursor/hooks/...` porque no pasó por el install `--user`. La tarea 7 lo repara llamando a `write_user_hooks_config` (o al install `--user`) y alinea la prosa de `docs/harness-integration.md` y `docs/harness-setup.md` con ese código. La comprobación real en el IDE es `not_run` en CI.
5. **Deriva MCP entre harnesses**: Pi = 5 servidores; Cursor = 1. Sin lista canónica única.
6. **`aw_subagent` con whitelist hardcoded** (`ALLOWED_SKILLS` = 7): frágil ante el rename de skills (`project-autoworkspace` → `project-machineroom` rompería la coherencia si no se actualiza en el mismo cambio).
7. **3 skills `local-*` y el loader de Pi** (H4 **verificada**): los symlinks y el manifest existen (17). La descripción de `local-maintenance` mide 980/1024 chars (bajo el límite). Evidencia 2026-11-10: `pi --mode rpc --no-session` + `get_commands` (proceso fresco, equivalente a `/reload` en sesión nueva) descubrió las **17** del catálogo, incluidas `local-email`, `local-maintenance` y `local-security`, tanto con cwd del repo (`.pi/skills/`, origin `top-level`) como con cwd vacío en `/tmp` (`~/.pi/agent/skills/`, origin `top-level`). Más las 3 Omarchy. **Causa raíz:** sesión Pi stale sin reload, no rechazo del loader ni del frontmatter. Estado del hallazgo: **`pass`**. La tarea 9 re-verifica tras el rename.
8. **Fragmentación de nombre** (motor del rename): `aw-*` (agents, `aw_subagent`, `/aw-status`), marca `Autoworkspace`, `~/.autoworkspace` (runtime), `.autoworkspace/` (estado por proyecto), skill `project-autoworkspace`. Todo deriva de "autoworkspace".
9. **Rule de usuario Cursor no versionable como fichero**: Cursor guarda las user rules en Settings; se aplica pegando el texto (`scripts/cursor-user-rule.sh --copy`). Paso manual aceptado; documentar.
10. **`path-guard` y el runtime**: no protege `~/.autoworkspace` (tras el rename, `~/.machineroom`). Hoy, fuera de `~/Work/`, una ruta no listada devuelve `undefined` (permite). Decisión H1: fail-closed — denegar por defecto; con UI, pedir confirmación; allowlist mínima explícita (p. ej. `/tmp`). Además, `~/.machineroom` entra en la lista dura.

## 3. Decisiones a aprobar (registro de decisión)

> Estado de aprobación (operador): **D1–D10 APROBADAS** (confirmadas por el operador en dos respuestas).

- **D1 — Caso y marca**: todo minúscula `machineroom` para identificadores, rutas, directorio, repo, nombre npm y paquete Pi. Título humano "Machineroom" (H1 de README, descripciones). Prefijo corto **`mr-`** sustituye a `aw-`: `mr-planner`/`mr-verifier`/`mr-worker`, tool `mr_subagent`, comando `/mr-status`. Skill `project-autoworkspace` → `project-machineroom`.
- **D2 — Runtime de máquina**: `~/.autoworkspace` → `~/.machineroom` (`RUNTIME_DIRNAME`). Migración única con `scripts/runtime-sync.sh` + relink + doctor; sin doble runtime.
- **D3 — Estado por proyecto**: `.autoworkspace/` → `.machineroom/` en este repo y en `templates/{harness,product}`. Compat transitoria: `workspace-router` y `execution` leen `.machineroom` con fallback a `.autoworkspace` + aviso de deprecación y flag `--migrate` (evita romper los repos de producto ya adoptados de golpe). Ventana (H2): fallback activo en toda la línea **8.x**; eliminación en **9.0.0**.
- **D4 — Simetría de gates**: añadir gate de comandos a Pi (tool `bash` + `user_bash`) que replique la deny/ask/allow de `shell_gate.py`. Lista de deny como **único fichero de datos compartido** consumido por `shell_gate.py` y por la extensión Pi (sin duplicar regexes).
- **D5 — Contrato de ejecución single-source**: un único documento canónico (la rule `machineroom.mdc` como SSOT), `session_start.py` inyecta un puntero/resumen derivado (no el texto completo), y un check de paridad en CI (`tools/validate`) que falle si el resumen diverge del SSOT.
- **D6 — Estrategia MCP**: secretos siempre en ficheros de usuario (nunca en repo). Lista canónica documentada en el repo; `context7`/`playwright`/`chrome-devtools`/`notion` se alinean en Cursor vía `~/.cursor/mcp.json` (usuario). Opcional: `.pi/mcp.json` de proyecto **solo** con servidores sin secreto. No versionar tokens ni headers `!comando` en el repo.
- **D7 — `mr_subagent`**: renombrar y **derivar `ALLOWED_SKILLS` del catálogo/config** (no hardcodear), manteniendo mínimo privilegio (excluir por defecto mutación/publish/local/web); incluir `project-machineroom` (auto-auditoría).
- **D8 — Rule Cursor de usuario**: se mantiene el pegado manual (limitación de Cursor); `cursor-user-rule.sh` genera el payload desde la rule versionada y `session_start.py` emite resumen/puntero (no duplica el texto).
- **D9 — Versión**: rename = BREAKING → **8.0.0** (`package.json`, `CHANGELOG.md` sección Unreleased→8.0.0, `metadata.version` de skills tocadas, docs, tag `v8.0.0` y paquete Pi `machineroom@v8.0.0`).
- **D10 — Historia inmutable**: `CHANGELOG.md` histórico, `docs/plans/*`, `docs/archives/*`, `tasks/plan-*.md` existentes y ADRs (`ADR-0016`, `ADR-0017`) no se reescriben. El rename añade **ADR-0018** (rename autoworkspace→machineroom) en vez de editar ADR-0016. Las referencias históricas a "autoworkspace" se conservan.

## 4. Objetivo

Rediseñar el diseño de plugins/integraciones/MCP/reglas/hooks de Pi y Cursor para eliminar deriva y asimetría, integrarlo en el repo, y renombrar todo el producto a `machineroom` (repo GitHub, directorio local, runtime, estado por proyecto, skills, harness surfaces, marca) sin romper los repos de producto que ya usan `.autoworkspace/`.

## 5. Mapa de capacidades y orden de construcción

| Módulo                  | Responsabilidad                                                                                                                                                         | Depende de                    |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| rename-core             | Marca/paquete/docs vivos de raíz (README, ARCHITECTURE, AGENTS, package.json, Makefile, .env.example, docs vivos, templates, glosario, taxonomía, índice)               | —                             |
| rename-runtime          | `RUNTIME_DIRNAME` → `~/.machineroom`, runtime-sync, instaladores, doctor, manifests, migración                                                                          | rename-core                   |
| rename-project-state    | `.autoworkspace/` → `.machineroom/` + compat/fallback en router/execution/contracts                                                                                     | rename-core                   |
| rename-skills           | `project-autoworkspace` → `project-machineroom` + descriptions + references + skill-index + manifests                                                                   | rename-core                   |
| rename-harness-surfaces | Agents `mr-*`, plugin, extensión Pi (`machineroom`, `mr_subagent`, `/mr-status`) y `path-guard` versionado. No edita el texto SSOT ni la forma de los comandos de hooks | rename-runtime, rename-skills |
| pi-shell-gate           | Gate Pi de bash/`!` + deny-list compartida + tests de extensión                                                                                                         | rename-harness-surfaces       |
| contract-ssot           | Dueña de `machineroom.mdc`, resumen de `session_start.py`, `contract_parity.py` y reescritura de hooks                                                                  | rename-harness-surfaces       |
| mcp-parity              | Lista canónica en docs + `.pi/mcp.json` opcional sin secretos. `~/.cursor/mcp.json` fuera del diff (H3 cerrada: no)                                                     | rename-core                   |
| verify-local-skills     | Tras `rename-skills`: gate automático de 17. Re-verifica H4 (ya `pass` pre-rename con RPC fresco)                                                                       | rename-skills                 |
| closure                 | Versión 8.0.0, CHANGELOG, ADR-0018, rename de directorio local y repo GitHub, release                                                                                   | todos                         |

**Nota de implementación (SSOT de naming)**: para evitar reemplazos dispersos y divergentes, se añade un módulo único `tools/harness/naming.py` con constantes (`BRAND = "machineroom"`, `PREFIX = "mr"`, `RUNTIME_DIRNAME = ".machineroom"`, `PROJECT_DIRNAME = ".machineroom"`, `REPO = "Soluciones-Alexendros/machineroom"`, `LEGACY_*` para fallback). Todo el código Python/TS/bash lee de ahí o de su equivalente. Los tests afirman la coherencia del mapa. Literales `autoworkspace` / `aw-` solo se permiten en las constantes `LEGACY_*` de `tools/harness/naming.py` y en la historia inmutable. El resto del código vivo no los repite. D3 necesita el nombre viejo en `LEGACY_*`; un grep total a cero haría el test imposible.

## 6. Diseño objetivo

1. **Catálogo SSOT** — `skills/` sigue siendo la única fuente versionada; symlinks en `.cursor/skills` y `.pi/skills`; índice generado.
2. **Capa de contrato** — `machineroom.mdc` (SSOT). `session_start.py` emite resumen/puntero; check de paridad en CI.
3. **Capa de gates** — Cursor `shell_gate.py` y Pi shell gate consumen un único `tools/execution/deny-list.json`; `path-guard` vive en `extensions/machineroom/path-guard.ts`, añade `~/.machineroom` a la lista dura y es fail-closed fuera de `~/Work/` (H1), con allowlist mínima explícita.
4. **Capa de agents** — Cursor `mr-planner`/`mr-verifier`/`mr-worker`; Pi `mr_subagent` + `worker.md`.
5. **Instalación/runtime** — instaladores idempotentes, `~/.machineroom`, doctor y manifests bajo la marca nueva.
6. **MCP** — secretos solo en usuario; lista canónica en docs; `.pi/mcp.json` opcional sin secretos. Escribir `~/.cursor/mcp.json` queda fuera del diff de la tarea 8 (H3); hace falta autorización de host aparte (D6 sigue vigente como estrategia).

## 7. Alcance completo del rename

**Renombrar (superficies vivas)** — criterio de cierre = §12: cero `autoworkspace` en superficies vivas, con exclusiones reales (basename `plans`, `archives`, `decisions`; `docs/architecture/skill-index-7.0.0.json`; líneas `LEGACY_*` de `tools/harness/naming.py`). No es `grep -i machineroom == 0`.

- Raíz: `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `package.json`, `package-lock.json`, `Makefile`, `.env.example`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- `skills/` (incluye `project-autoworkspace` → `project-machineroom` y strings "Autoworkspace"/"autoworkspace" en descriptions y `references/`).
- `.cursor/`, `.cursor-plugin/`, `extensions/`, `scripts/`, `tools/`, `templates/`, `stacks/`, `.github/` (issue template, renovate, policy-exceptions, workflows que referencien nombre).
- `docs/` **excepto** los directorios cuyo basename es `plans`, `archives` o `decisions`, y excepto el fichero inmutable `docs/architecture/skill-index-7.0.0.json`. `docs/architecture/diagrams/` se regenera desde `sources/`.
- Tras la tarea 3 este repo no tiene directorio `.autoworkspace/`. El estado de este checkout queda en `.machineroom/` (la nota de obsolescencia de `SPEC.md` viaja con ese rename). El fallback a `.autoworkspace` es código para otros repos, no un directorio viejo en este checkout.
- `skill-index.json` (regenerado), manifests `.autoworkspace-install-manifest.json` / `.runtime-manifest.json` / `.autoworkspace-full-manifest.json`.

**Conservar (historia inmutable)**: `CHANGELOG.md` secciones históricas (se añade 8.0.0 nueva), `docs/plans/*`, `docs/archives/*`, `docs/architecture/decisions/` (ADR-0016/0017 intactos; se añade ADR-0018), `docs/architecture/skill-index-7.0.0.json`, `tasks/plan-*.md` existentes.

**Sufijos de identificador**: `aw-` → `mr-`; `~/.autoworkspace` → `~/.machineroom`; `.autoworkspace/` → `.machineroom/`; `extensions/autoworkspace` → `extensions/machineroom`; `path-guard.ts` suelto → `extensions/machineroom/path-guard.ts` (symlink de install en `~/.pi/agent/extensions/`); `~/.pi/agent/extensions/autoworkspace.ts` → `machineroom.ts`; skill `project-autoworkspace` → `project-machineroom`; `aw_subagent` → `mr_subagent`; `/aw-status` → `/mr-status`.

## 8. Contrato de resultados, fallos y finalizaciones

Requisito transversal para **todo** código nuevo o modificado (Python, TypeScript y bash). Objetivo: ningún fallo/finalización queda opaco; todo camino de error es observable, estructurado y testable.

### 8.1 Envelope de resultado unificado (Python)

- Se extienden `InstallFailure` y `format_failure` ya existentes en `tools/harness/runtime.py`. Hogar propuesto: `tools/harness/outcome.py` (`runtime.py` reexporta). No se crea una jerarquía paralela (`ProjectConfigError`, `DenyListError`, etc.).
- `InstallFailure` lleva `component`, `function`, `detail` (mensaje humano accionable) y, cuando aplique, `run_id`, `evidence` (SHA-256), `exitCode`.
- `format_failure(component, function, detail)` → `FAIL <component> <function>: <detail>` en stderr. Se usa en deny-list loader, contract parity, migración y shell gate.
- `outcome` ∈ conjunto cerrado `{succeeded, failed, cancelled, blocked, not_run, not_applicable}`. `not_run`/`blocked` se usan para dependencia ausente o autorización denegada; **nunca** se convierten en `succeeded`.
- Códigos de salida fijados: `0` éxito · `2` uso incorrecto · `3` `not_run`/`blocked` · `1` fallo real (detalle en §8.2).
- Prohibido: `raise Exception` genérico, `except: pass`, retornar `None` para indicar error, y `os._exit` dentro de gates/instaladores.

### 8.2 Códigos de salida y CLI

- `0` éxito · `2` uso incorrecto · `3` `not_run`/`blocked` (dependencia o autorización) · `1` fallo real.
- Todo CLI mutador/instalador acepta `--json` y emite **un solo objeto JSON** en stdout con `status`, `failures[]` (cada uno `component`/`function`/`detail`) y `changed`/`skipped`/`installed`; los fallos también van a stderr en texto.
- `doctor.py --full` reporta, para cada componente, estado y detalle (no booleano escueto).

### 8.3 Extensión Pi (`mr_subagent`, shell gate, `path-guard`)

- `mr_subagent`: el envelope `{outcome, exitCode, output, detail, reconciliationRequired}` + `isError` vale también para las ramas que hoy no lo emiten. Esas ramas se nombran `skillRejected` y `cwdRejected`. Cada rama de fallo (`skillRejected`, `cwdRejected`, `parseError`, `modelFailed`, `timedOut`, `aborted`, `exitCode !== 0`) produce un `detail` distinto; `detail` incorpora `component` y `function`. `reconciliationRequired: true` solo para timeout/abort.
- Shell gate Pi: responde `{permission: deny|ask|allow, user_message, agent_message}` idéntico a `shell_gate.py`; error interno → `deny` (fail-closed, nunca crash-open). Entradas no string o payload malformado → `deny` explícito.
- `path-guard` (H1 **cerrada** — fail-closed): fuera de `~/Work/`, toda ruta no listada se deniega por defecto (`{block: true, reason}`). Con UI, se pide confirmación antes de permitir; sin UI, se bloquea con `reason` de "requiere confirmación". Allowlist mínima explícita (p. ej. `/tmp` y prefijos que el implementador documente en el mismo fichero) mitiga writes legítimos a destinos temporales. `~/.machineroom` entra en la lista dura. Coherente con el shell gate fail-closed y con ADR-0017 (mínimo privilegio).

### 8.4 `shell_gate.py`

- Mantiene deny/ask/allow JSON y "nunca exit 2" (failClosed cubre crash real). Se añade `component`/`function` a `user_message`/`agent_message` y se documenta cada rama (deny por patrón, ask por red, allow por help/version o tmp aprobado).

### 8.5 Documentación de funciones

Toda función nueva o modificada lleva docstring con: propósito, parámetros, retorno, **lista explícita de modos de fallo** y efectos secundarios. Los DoD y las test surfaces de §11, junto con la matriz de §10, revisan que los paths de error estén cubiertos por tests.

## 9. Guías clean-code por área

Aplicables a las modificaciones de este plan. Fuente de método: skill `role-clean-code` + convenciones del repo (Ruff, mypy `--strict`, Prettier, Conventional Commits, mínimo privilegio ADR-0017).

| Área / lenguaje           | Reglas                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python (`tools/`)         | Ruff (`ruff.toml`) + mypy `--strict`; type hints; funciones de responsabilidad única; sin números mágicos (deny-list y naming en datos/constantes); excepciones de dominio (no `Exception`); dataclasses para `Result`/config; `for` explícito antes que comprensiones densas en paths de error.                                                                                         |
| TypeScript (extensión Pi) | Schemas TypeBox tipados; sin `any` nuevo (tipar el `any[]` de eventos actual); constantes arriba; helpers por fichero (`index.ts` delgado, `gates.ts`, `subagent.ts`, `path-guard.ts`); `ALLOWED_SKILLS` derivado, no literal. Shell gate Pi y `path-guard.ts`: fail-closed explícito (payload malformado → deny; ruta no listada fuera de `~/Work/` → block/confirm, allowlist mínima). |
| Bash (`scripts/`)         | `set -euo pipefail`; funciones con comentario de propósito; sin `curl \| bash`; salidas `--json` estructuradas; `--dry-run` sin escritura.                                                                                                                                                                                                                                               |
| Markdown (skills/docs)    | SKILL.md ≤500 líneas, cuerpo <200 preferible; `references/` para lo denso; description ≤1024 chars; frontmatter con las claves canónicas; name == dir.                                                                                                                                                                                                                                   |
| Naming global             | `mr-` prefijo, kebab-case, Conventional Commits; SSOT `tools/harness/naming.py`. Literales `autoworkspace` / `aw-` solo en `LEGACY_*` y en historia inmutable.                                                                                                                                                                                                                           |
| DRY / SSOT                | deny-list único, contrato único, naming único, mapa de rename único. Cada duplicación es un test rojo.                                                                                                                                                                                                                                                                                   |

**Aplicación a las áreas del plan**: `rename-core` (Markdown + naming SSOT), `rename-runtime`/`rename-project-state` (Python, envelope de resultado), `rename-skills` (Markdown, ≤1024 desc), `rename-harness-surfaces` (TS tipado + Markdown agents), `pi-shell-gate` (Python + TS, deny-list SSOT, fail-closed), `contract-ssot` (Markdown SSOT + validador), `mcp-parity` (JSON, sin secretos), `verify-local-skills` (diagnóstico con resultado estructurado), `closure` (CHANGELOG/ADR, historia inmutable).

## 10. Plan de pruebas integradas

Estrategia red-green (skill `plan-validators`): test rojo primero por cada comportamiento, luego implementación. Cobertura obligatoria de ramas de fallo, no solo happy path (§8).

### 10.1 Matriz de capas

| Capa                | Herramienta                                                                                                                     | Cobertura en este plan                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Unit Python         | pytest (`uv run --project tools pytest`)                                                                                        | naming, deny-list (paridad de datos), contract parity, migración de runtime y de estado, router legacy fallback |
| Unit TS / extensión | smoke estático + `npm run typecheck` + tests de extensión junto a `test_pi_extension.py` / `test_pi_subagent.py`                | schemas, ramas de resultado, deny/ask/allow del interceptor Pi. Ningún pytest importa TypeScript                |
| Harness             | `scripts/tests/test_*.sh`                                                                                                       | instaladores, runtime-sync, doctor, manifests, bootstrap                                                        |
| Smoke               | `make smoke` + `run-validation.sh --smoke-only`                                                                                 | smoke de skills con scripts y del router                                                                        |
| E2E integrado       | `scripts/tests/test_execution_e2e.sh`, `test_orchestration_core.sh`, `test_pi_orchestration.sh`, `test_cursor_orchestration.sh` | flujo DEFINE→…→STATUS y gates sobre runtime renombrado                                                          |
| CI                  | `ci.yml` `validate` + `ci-gate`; `make readiness`                                                                               | agregación de todo lo anterior                                                                                  |

### 10.2 Tests nuevos (red primero)

- `tools/harness/tests/test_naming.py` — constantes SSOT. Literales `autoworkspace` / `aw-` solo en `LEGACY_*` de `tools/harness/naming.py` y en historia inmutable; el resto del código vivo no los repite. El barrido del árbol completo es el criterio de §12, no el DoD de la tarea 1.
- `tools/harness/tests/test_runtime_migration.py` — `scripts/runtime-sync.sh` migra `~/.autoworkspace` → `~/.machineroom`, relink, manifiesto, doctor, rollback ante fallo. No hay un segundo entrypoint.
- `tools/execution/tests/test_deny_list.py` — solo carga del fichero compartido y **paridad de datos** entre `shell_gate.py` y el gate Pi.
- Ramas deny/ask/allow del interceptor Pi (TypeScript), más payload malformado → deny: en la capa de extensión, junto a `tools/harness/tests/test_pi_extension.py` y `test_pi_subagent.py`. No existe un pytest que importe el TypeScript.
- `tools/validate/tests/test_contract_parity.py` — resumen de `session_start.py` coherente con SSOT `machineroom.mdc`.
- `tools/workspace-router/tests/test_legacy_state_migration.py` — fallback `.autoworkspace` → `.machineroom` + `--migrate`.
- `tools/skill-router/tests/test_catalog_17.py` — 17 skills, incluye `project-machineroom`, sin `project-autoworkspace`.
- `tools/harness/tests/test_pi_subagent.py` (actualizado) — `mr_subagent` + `ALLOWED_SKILLS` derivado.

### 10.3 Tests existentes a actualizar (referencian `.autoworkspace`/`autoworkspace`)

- `tools/harness/tests/test_doctor.py`, `test_runtime.py`, `test_cursor_install.py`, `test_bootstrap.py`, `test_pi.py`, `test_pi_extension.py`, `test_install_failures.py`, `test_cursor_plugin.py` (hoy afirma `name == "autoworkspace"`).
- Asserts de `write_user_hooks_config` en `test_runtime.py`, `test_cursor_install.py` y `scripts/tests/test_install.sh`: usuario = `python3 hooks/...`; se rechaza `.cursor/hooks/` en ese alcance.
- `tools/execution/tests/test_product_closure_evidence.py`, `test_product_closure_state_release.py`, `test_run_verified.py`, `test_verifiable_closure.py`.
- `tools/workspace-router/tests/test_project_load.py`, `test_plan_state.py`, `test_status_bump.py`.
- `scripts/tests/test_install.sh`, `test_pi_native.sh`, `test_cursor_native.sh`, `test_standalone_package.sh`, `test_bootstrap.sh`.
- `tools/validate/tests/test_shell_gate.py` (mensajes y deny-list compartida).

### 10.4 Verificación de descubrimiento de skills

- Gate automático (CI): `ls skills/ | wc -l` == 17 y `python3 tools/skill-index/generate.py` idempotente, con `project-machineroom` y sin `project-autoworkspace`.
- Evidencia Pi (H4 pre-rename **`pass`**, 2026-11-10): `pi --mode rpc --no-session` + `get_commands` listó las 17 del catálogo (incluidas `local-*`) en repo y en alcance usuario. Post-rename: repetir en la tarea 9. Customize → Skills en Cursor sigue siendo evidencia de operador (`not_run` en CI si no se mira).

## 11. Tareas

Cada tarea → rama de trabajo → PR a la rama del plan (squash). Cada tarea termina con: tests red→green de **su** superficie (§10), envelope de resultado (§8), clean-code (§9) y el DoD de esa tarea. Roles de implementación en todas: `role-back` y `role-clean-code`. No hay superficie UI de producto (`role-front` y `role-design` no aplican). Un artefacto tiene un solo dueño.

1. **rename-core** — `chore/01-rename-core`. Alcance: raíz viva, `docs/` vivos, `templates/`, `stacks/`, `.github/`, `tools/harness/naming.py`, regenerar `skill-index.json`, recuento 17 en `ARCHITECTURE.md`, nota de obsolescencia en `.autoworkspace/SPEC.md`. La `version` de `package.json` sigue en `7.1.3` (la sube la tarea 10). **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** constantes de `test_naming.py`; `tools/skill-index/generate.py` idempotente en los marcadores que esta tarea regenera. **Ficheros probables:** `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, `package.json` (nombre, no versión), `Makefile`, `.env.example`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `docs/` vivos, `templates/`, `stacks/`, `.github/`, `tools/harness/naming.py`, `skill-index.json`, `.autoworkspace/SPEC.md`. `docs/harness-integration.md` y `docs/harness-setup.md` no se editan aquí: su texto lo cierra la tarea 7, y los pines `v7.1.1` que queden los cierra la tarea 10. **DoD:** `ARCHITECTURE.md` dice 17; `SPEC.md` queda marcada obsoleta; `naming.py` define `BRAND`, `PREFIX`, `RUNTIME_DIRNAME`, `PROJECT_DIRNAME`, `REPO` y `LEGACY_*`; `test_naming.py` cubre esas constantes. No exige cero `autoworkspace` en `skill-index.json` ni en docs que aún nombran la skill vieja (eso lo cierra la tarea 4 y el criterio §12). El grep final de §7/§12 no es este DoD.
2. **rename-runtime** — `chore/02-rename-runtime`. Un solo entrypoint de migración, el de D2: `scripts/runtime-sync.sh` mueve `~/.autoworkspace` → `~/.machineroom` y relinka. No se crea `scripts/migrate-runtime.sh`. `RUNTIME_DIRNAME` sale de `naming.py`. También `install-*.sh`, `bootstrap.sh` (`REPOSITORY=Soluciones-Alexendros/machineroom`), `doctor.py`, manifests. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_runtime_migration.py`, `scripts/tests/test_install.sh`. **Ficheros probables:** `tools/harness/runtime.py`, `tools/harness/naming.py` (solo lectura de constantes), `scripts/runtime-sync.sh`, `scripts/install-cursor.sh`, `scripts/install-pi.sh`, `scripts/install.sh`, `scripts/bootstrap.sh`, `tools/harness/doctor.py`. **DoD:** esos dos tests verdes; `runtime-sync.sh --dry-run` nombra `~/.machineroom`; no existe `migrate-runtime.sh`.
3. **rename-project-state** — `chore/03-rename-project-state`. `.autoworkspace/` → `.machineroom/` en este repo y en `tools/workspace-router`, `tools/execution`, `tools/contracts`, `templates/{harness,product}`; fallback con aviso y `--migrate`. La nota de `SPEC.md` viaja al directorio nuevo. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_legacy_state_migration.py`; `python3 tools/workspace-router/run.py --phase DEFINE --repo . --json`. **Ficheros probables:** `tools/workspace-router/`, `tools/execution/`, `tools/contracts/`, `templates/harness/`, `templates/product/`, `.machineroom/`. **DoD:** el test verde; el router lee `.machineroom/` y acepta `.autoworkspace/` ajeno con aviso; en este repo no queda directorio `.autoworkspace/`.

**Checkpoint tras las tareas 1–3.** Suite de lo ya tocado en verde. No se sigue sin ese verde.

4. **rename-skills** — `chore/04-rename-skills`. `project-autoworkspace` → `project-machineroom` (dir, frontmatter, `references/canon-map.md`, `references/harnesses.md`); strings en `plan-continue`, `plan-specification`, `project-publish` y `local-*`; regenerar índice; `tools/skill-router/intent-map.yaml`. No usa `scripts/rename-skills.sh`: es un mapa v3 de carpetas ES→EN, no este rename. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_catalog_17.py`; descriptions ≤1024 (`tools/validate/skill_spec.py`). **Ficheros probables:** `skills/project-machineroom/`, las skills citadas, `skill-index.json`, `tools/skill-router/intent-map.yaml`. **DoD:** `test_catalog_17.py` verde; ninguna description pasa de 1024; `scripts/rename-skills.sh` no se ha ejecutado ni adaptado para este rename.
5. **rename-harness-surfaces** — `chore/05-rename-harness-surfaces`. Agents `mr-*`, plugin `.cursor-plugin`, extensión `extensions/machineroom/` (`mr_subagent`, `/mr-status`, `ALLOWED_SKILLS` derivado, incluye `project-machineroom`), alta de `extensions/machineroom/path-guard.ts` enlazado desde `~/.pi/agent/extensions/` (el install sustituye el fichero suelto), `~/.machineroom` en la lista dura y fail-closed H1 (ruta no listada fuera de `~/Work/` → block/confirm; allowlist mínima). No edita el texto SSOT de la rule ni la forma de los comandos de hooks (dueña: tarea 7). **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_pi_subagent.py`, `test_pi_extension.py`; ramas de `path-guard` (lista dura, confirm, fail-closed, allowlist). **Ficheros probables:** `.cursor/agents/mr-*.md`, `.cursor-plugin/`, `extensions/machineroom/`, instalador Pi que enlaza `path-guard.ts`. **DoD:** esos tests verdes; `path-guard.ts` en el repo; lista dura con `~/.machineroom`; fail-closed + allowlist documentada. El grep global de `aw-` no es este DoD.
6. **pi-shell-gate** — `feat/06-pi-shell-gate`. `extensions/machineroom/deny-list.json`; `shell_gate.py` lo consume vía `tools/execution/deny_list.py`; la extensión Pi intercepta `tool_call` (bash) y `user_bash` con deny/ask/allow, fail-closed si el payload es malformado. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_deny_list.py` (solo paridad de datos); ramas deny/ask/allow en la capa de extensión, junto a `test_pi_extension.py` / `test_pi_subagent.py`. **Ficheros probables:** `extensions/machineroom/deny-list.json`, `tools/execution/deny_list.py`, `.cursor/hooks/shell_gate.py`, `extensions/machineroom/gates.ts`. **DoD:** `test_deny_list.py` verde y las ramas del interceptor verdes en esa capa. No hay pytest que importe TypeScript.

**Checkpoint tras las tareas 4–6.** Suite de lo ya tocado en verde. No se sigue sin ese verde.

7. **contract-ssot** — `chore/07-contract-ssot`. Dueña única de `machineroom.mdc`, del resumen derivado en `session_start.py`, de `tools/validate/contract_parity.py` (enganchado en `run-validation.sh`) y de la reescritura de hooks. Repara el runtime vivo con `write_user_hooks_config` o con el install `--user`, y alinea `docs/harness-integration.md` y `docs/harness-setup.md` con el código: usuario = `python3 hooks/...`, proyecto = `python3 .cursor/hooks/...`. La prueba en el IDE queda `not_run` en CI. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_contract_parity.py`; asserts de `write_user_hooks_config` en `test_runtime.py`, `test_cursor_install.py` y `scripts/tests/test_install.sh`. **Ficheros probables:** `.cursor/rules/machineroom.mdc`, `.cursor/hooks/session_start.py`, `.cursor/hooks.json`, `tools/validate/contract_parity.py`, `run-validation.sh`, `docs/harness-integration.md`, `docs/harness-setup.md`, `scripts/cursor-user-rule.sh`. **DoD:** `test_contract_parity.py` verde; `run-validation.sh` incluye la paridad; los tests de hooks aceptan la forma canónica y rechazan `.cursor/hooks/` en alcance usuario.
8. **mcp-parity** — `chore/08-mcp-parity`. H3 **cerrada: no**. El PR solo documenta la lista canónica y, si se incluye, un `.pi/mcp.json` de proyecto solo con servidores sin secreto. Documenta OAuth sin pegar secretos ni headers `!comando`. Escribir `~/.cursor/mcp.json` es paso de host con autorización explícita, fuera del diff. D6 no se reabre: los secretos siguen en ficheros de usuario. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** grep de tokens versionados sobre el diff; no hay test de red. **Ficheros probables:** `docs/harness-integration.md`, `.pi/mcp.json` opcional. **DoD:** la lista canónica está en el doc; el diff no contiene tokens ni `~/.cursor/mcp.json`.
9. **verify-local-skills** — `fix/09-verify-local-skills`. Va **después** de `rename-skills`. Gate automático: `ls skills/` + índice = 17, con `project-machineroom`. H4 pre-rename ya es **`pass`** (RPC fresco 2026-11-10; causa = sesión stale). Esta tarea **re-verifica** tras el rename con el mismo método (`pi --mode rpc --no-session` + `get_commands`, o `/reload` en TUI) y documenta el resultado. No hace falta tocar frontmatter de `local-*` salvo regresión. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `test_catalog_17.py`, generador de índice, RPC Pi post-rename. **Ficheros probables:** nota en docs de harness si el mensaje de `/reload` debe quedar explícito. **DoD:** gate automático verde; RPC/TUI post-rename con las 17 (o `fail`/`not_run` con motivo).

**Checkpoint tras las tareas 7–9.** Suite de lo ya tocado en verde. No se entra en closure sin ese verde.

10. **closure** — `chore/10-closure`. Base de versión: `7.1.3`. Tres checkpoints internos, sin cambiar D9. **Implementation roles:** `role-back`, `role-clean-code`. **Test surfaces:** `make validate && make test && make smoke` y `run-validation.sh` en el checkpoint 1; §12 completo solo al cerrar el checkpoint que corresponda. **Ficheros probables:** `package.json`, `CHANGELOG.md` (sección nueva 8.0.0), `docs/architecture/decisions/ADR-0018`, docs vivos que aún citen el ejemplo `v7.1.1`.
    - Checkpoint 1 — `8.0.0` en `package.json`, sección nueva de `CHANGELOG.md`, ADR-0018, y `make validate && make test && make smoke` en verde. Los ejemplos `v7.1.1` de bootstrap se quedan como historia o pasan a `v8.0.0` solo en docs vivos. No se reescriben `docs/plans/` ni las secciones viejas del CHANGELOG.
    - Checkpoint 2 — `mv ~/Work/autoworkspace ~/Work/machineroom` y `gh repo rename` solo con un sí del operador. Fuera de ese sí, no se hace.
    - Checkpoint 3 — tag `v8.0.0` y paquete Pi solo con `project-publish` autorizado aparte.

## 12. Criterios de éxito verificables

- Gate de naming: `python3 tools/validate/naming_gate.py` en verde (enganchado en
  `run-validation.sh` como `[3a]`). El gate escanea las superficies vivas
  (`skills/`, `.cursor/`, `.cursor-plugin/`, `extensions/`, `scripts/`, `tools/`,
  `templates/`, `stacks/`, `docs/` y los ficheros de raíz) y falla si aparece el
  nombre pre-8.0 fuera de una allowlist revisada. La allowlist cubre solo lo que
  debe seguir nombrando el pasado: `naming.py`, `state_paths.py`, `GLOSARIO.md`,
  los tests de migración/fallback, los instaladores que reconocen el runtime
  viejo, el loader de contratos (dialecto legacy), la keyword `aw-plan`
  embebida en planes históricos y el fallback documentado de bootstrap. Quedan
  fuera por diseño la historia (`docs/plans/`, `docs/archives/`,
  `docs/architecture/decisions/`, `CHANGELOG.md`, snapshots congelados) y los
  artefactos generados (`docs/architecture/diagrams/rendered/`).

- En este repo no existe el directorio `.autoworkspace/` (`test ! -d .autoworkspace`). El estado está en `.machineroom/`.
- `ls skills/ | wc -l` == 17 e incluye `project-machineroom`; `ls skills/ | grep -c 'project-autoworkspace'` == 0.
- `python3 tools/skill-index/generate.py` produce 17 y `README.md`/`docs/TAXONOMY.md` entre marcadores idénticos al generador.
- El gate cubre también los identificadores `aw-planner`, `aw-verifier`, `aw-worker`, `aw_subagent` y `/aw-status`: ninguna superficie viva los usa ya.
- `grep -rn 'RUNTIME_DIRNAME' tools/harness/` referencia `naming.py`/`.machineroom`; `bash scripts/runtime-sync.sh --dry-run` referencia `~/.machineroom`.
- `bash run-validation.sh` y `make validate && make test && make smoke` en verde; `make readiness` sin bloqueos (model lanes opt-in `MR_NATIVE_OPT_IN=1`).
- `python3 tools/workspace-router/run.py --phase DEFINE --repo . --json` lee `.machineroom/` (y acepta `.autoworkspace/` legacy con aviso).
- Tests nuevos de §10.2 verdes y tests actualizados de §10.3 verdes.
- `package.json` == `8.0.0`, CHANGELOG con sección 8.0.0, ADR-0018 presente.
- `git remote get-url origin` == `https://github.com/Soluciones-Alexendros/machineroom.git` (tras autorización).

## 13. Riesgos y preguntas abiertas

Cerrado (no reabrir). El «H1» del título humano de README (D1) no es esta lista:

- Forma de `hooks.json`: usuario = `python3 hooks/...`; proyecto = `python3 .cursor/hooks/...` (§2.5.4). La comprobación en el IDE sigue `not_run` en CI.
- Orden único: la tarea 9 va después de `rename-skills`. Invertirlo requiere aprobación explícita del operador.
- `mr-` queda fijado por D1.
- `package.json` es `private: true` y se instala como paquete Pi por git, no por npm. El rename no toca el canal npm.
- `gh repo rename`: GitHub redirige la URL antigua. Los clones pineados a tags previos (ejemplo histórico `v7.1.1`) siguen en el nombre viejo. Es historia; se documenta, no se reescribe.
- **H1 — fail-closed.** Fuera de `~/Work/`, denegar por defecto toda ruta no listada; con UI, confirmación; allowlist mínima explícita. Escrito en §8.3. Coherente con shell gate y ADR-0017.
- **H2 — ventana de un major.** Fallback `.autoworkspace/` activo en **8.x** con aviso de deprecación; eliminación en **9.0.0**. Detalle de D3.
- **H3 — no.** La tarea 8 solo documenta la lista canónica y un `.pi/mcp.json` opcional sin secretos. Escribir `~/.cursor/mcp.json` es paso de host con autorización explícita, fuera del diff.

Verificación:

- **H4 — `pass` (2026-11-10).** Método: `pi --mode rpc --no-session` + `get_commands` (proceso fresco ≈ `/reload`). Resultado: 17 skills del catálogo + 3 Omarchy; `local-email`, `local-maintenance`, `local-security` presentes en cwd del repo y en cwd `/tmp` (usuario). Causa del anuncio incompleto en sesión previa: **sesión stale**, no loader ni descripción. La tarea 9 re-verifica tras el rename.

## 14. Estado de ejecución (2026-11-10)

Tareas 1–9 y checkpoint 1 de la tarea 10 ejecutadas en ramas `chore/*` y
`feat/*`, cada una con la suite del repo en verde antes del commit.

| Tarea                     | Estado                        | Evidencia                                                          |
| ------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| 1 rename-core             | hecho                         | `naming.py`, marca en docs vivos, `ARCHITECTURE.md` a 17           |
| 2 rename-runtime          | hecho                         | `~/.machineroom`, `migrate_legacy_runtime`, assets `machineroom-*` |
| 3 rename-project-state    | hecho                         | `state_paths.py`, fallback con aviso, `--migrate`                  |
| 4 rename-skills           | hecho                         | `project-machineroom`, registry e intent-map                       |
| 5 rename-harness-surfaces | hecho                         | `mr-*`, `path-guard.ts` versionado, `mr_subagent`                  |
| 6 pi-shell-gate           | hecho                         | deny-list compartida + gate Pi (paridad Node/Python)               |
| 7 contract-ssot           | hecho                         | rule SSOT, puntero con digest, `contract_parity.py`                |
| 8 mcp-parity              | hecho                         | lista canónica en `docs/harness-integration.md`                    |
| 9 verify-local-skills     | hecho                         | `test_catalog_17.py`, RPC Pi post-rename                           |
| 10 closure (1)            | hecho                         | `8.0.0`, CHANGELOG, ADR-0018, `naming_gate.py`                     |
| 10 closure (2)            | **pendiente de autorización** | `mv ~/Work/...`, `gh repo rename`, relink de usuario               |
| 10 closure (3)            | **pendiente de autorización** | tag `v8.0.0` y paquete Pi vía `project-publish`                    |

Desviaciones registradas:

1. La deny-list vive en `extensions/machineroom/deny-list.json`, no en
   `tools/execution/`: así viaja en el payload del runtime y Cursor y Pi leen el
   mismo fichero.
2. La keyword `aw-plan` del bloque de plan embebido se conserva: renombrarla
   invalidaría todos los planes ya commiteados. Queda en la allowlist del gate.
3. `docs/architecture/diagrams/rendered/` no se regenera aquí (Archify no está
   instalado); el gate lo trata como artefacto generado.
4. Los nombres de fichero de ADR previos (`ADR-0016-autoworkspace-...`) son
   historia: los enlaces los conservan y el gate los permite explícitamente.
5. Variables de entorno pasan a `MR_*`; `MR_BOOTSTRAP_REPOSITORY` mantiene
   fallback a la variable antigua.

## 15. Último paso

Actualizar el apartado del plan en Notion (política) con PRs, versión 8.0.0 publicada y URL del repo renombrado, cuando el operador lo apruebe.
