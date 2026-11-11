# Plantillas `.machineroom/`

Copiar al repo de producto:

```bash
mkdir -p .machineroom/schemas
cp templates/harness/project.yaml .machineroom/project.yaml
cp templates/harness/status.yaml .machineroom/status.yaml
```

- `project.yaml` — variables del proyecto (profile, stack, skills, handoffs).
- `status.yaml` — estado declarativo; cada avance del pipeline hace bump vía `tools/workspace-router/status_bump.py`.
- `schemas/` — esquemas de aceptación y stubs de test generados tras `plan-specification`.

Flujo: DEFINE → SCHEMAS → IMPLEMENT → VALIDATE → INTEGRATE → STATUS.

Skills de Pi: proyecto `.pi/skills`, usuario `~/.pi/agent/skills`. Comandos en [`docs/harness-setup.md`](../../docs/harness-setup.md).
