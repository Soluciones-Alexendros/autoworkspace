# Plugin de Herdr — Machineroom

Envoltorio de [Herdr](https://herdr.dev) para este repositorio: expone el catálogo de skills,
el enrutado de fase, el estado de `.machineroom/`, el gate de validación y los doctores de
harness como acciones y paneles.

Todo el plugin son dos piezas: `herdr-plugin.toml` (manifiesto) y `bin/mmctl.py` (stdlib de
Python, sin dependencias). El trabajo real lo siguen haciendo las herramientas del repo:
`tools/skill-router`, `tools/workspace-router`, `tools/harness/doctor.py` y `make validate`.

## Enlace

El plugin vive versionado aquí y se enlaza en local, sin instalación desde GitHub:

```bash
herdr plugin link ~/Work/machineroom/herdr
herdr plugin list
herdr plugin action list --plugin machineroom
herdr plugin pane open --plugin machineroom --entrypoint skills-pane
```

`herdr plugin unlink machineroom` lo retira sin tocar ficheros.

## Acciones

| Acción      | Contexto  | Qué hace                                                          |
| ----------- | --------- | ----------------------------------------------------------------- |
| `dashboard` | workspace | Panel con git, fase y accesos rápidos                             |
| `skills`    | workspace | Las 18 skills por dominio desde `skill-index.json`                |
| `route`     | selection | `tools/skill-router/route.py --top 3` sobre el texto seleccionado |
| `status`    | workspace | Git, fase declarada y contenido de `.machineroom/`                |
| `phase`     | workspace | Menú de fases → `tools/workspace-router/run.py --json`            |
| `validate`  | workspace | `make validate` en un panel dividido                              |
| `doctor`    | global    | `tools/harness/doctor.py` + enlaces de skills en Pi y Cursor      |

## Paneles

`dashboard-pane`, `skills-pane`, `route-pane`, `status-pane`, `phase-pane`, `doctor-pane`
(overlay) y `validate-pane` (split). Los paneles son la superficie de teclado; las acciones sólo
piden a Herdr que abra el panel correspondiente con `herdr plugin pane open --cwd <repo>`.

## Atajos sugeridos

En `~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "prefix+m"
type = "plugin_action"
command = "machineroom.dashboard"
description = "machineroom: panel"

[[keys.command]]
key = "prefix+shift+m"
type = "plugin_action"
command = "machineroom.skills"
description = "machineroom: skills"

[[keys.command]]
key = "prefix+g"
type = "plugin_action"
command = "machineroom.route"
description = "machineroom: enrutar selección"

[[keys.command]]
key = "prefix+shift+v"
type = "plugin_action"
command = "machineroom.validate"
description = "machineroom: validar repo"
```

`prefix+o` abre los doctores (`machineroom.doctor`).

## Contrato de entorno

Herdr inyecta `HERDR_PLUGIN_ROOT`, `HERDR_PLUGIN_ID`, `HERDR_PLUGIN_CONTEXT_JSON` y
`HERDR_BIN_PATH`. El plugin resuelve el checkout de Machineroom como el directorio padre de
`HERDR_PLUGIN_ROOT` y el repo destino desde el contexto (`worktree.path`, `workspace_cwd`,
`focused_pane_cwd`), buscando el `.machineroom/` más cercano hacia arriba.

`tools/workspace-router` necesita PyYAML: se ejecuta con `uv run --project tools`, igual que el
`Makefile`. Si `uv` no está en `PATH`, cae a `python3` y avisa con el error del router.
