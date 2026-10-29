# Plantillas `.autoworkspace/`

Copiar al repo de producto:

```bash
mkdir -p .autoworkspace/schemas
cp templates/harness/project.yaml .autoworkspace/project.yaml
cp templates/harness/status.yaml .autoworkspace/status.yaml
```

- `project.yaml` — variables del proyecto (profile, stack, skills, handoffs).
- `status.yaml` — estado declarativo; cada avance del pipeline hace bump vía `tools/workspace-router/status_bump.py`.
- `schemas/` — esquemas de aceptación y stubs de test generados tras `plan-specification`.

Flujo: DEFINE → SCHEMAS → IMPLEMENT → VALIDATE → INTEGRATE → STATUS.
