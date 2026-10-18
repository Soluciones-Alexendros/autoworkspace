# Plan canónico: cierre de ejecución segura

Plan ID: `autoworkspace-execution-closure-v1`  
Base: `f7ee056898f14a98d6bfd3eb1dcd0aa264496741`  
Alcance: conectar controles existentes (P0–P6). Sin nuevas skills ni frameworks.

## Registro

| Campo        | Valor                                                   |
| ------------ | ------------------------------------------------------- |
| Run ID       | aw-closure-20261018                                     |
| Inicio       | 2026-10-18T11:59:57+02:00                               |
| HEAD partida | f7ee056898f14a98d6bfd3eb1dcd0aa264496741                |
| Rama         | feat/execution-closure                                  |
| OpenCode     | 1.18.34 (`opencode --version` + `opencode debug skill`) |
| Gate         | `bash run-validation.sh` → **All checks passed**        |
| Veredicto    | **GO** (criterios del plan de cierre)                   |

## Inventario entrypoints mutadores

| Entrypoint                           | Tratamiento                                                                 |
| ------------------------------------ | --------------------------------------------------------------------------- |
| `clean_routine.py --execute`         | `run_registered` + handlers únicos; sin `AUTOWORKSPACE_ALLOW_HOST_MUTATION` |
| `snapshot_state.py` create/restore   | create vía registry; restore solo staging tempfile                          |
| `proton_bridge.py send`              | `proton_send` + ApprovalProvider; sin CONFIRM_SEND                          |
| `apparmor_lifecycle --execute`       | blocked explícito (no registry)                                             |
| `install.sh` / `install-opencode.sh` | preflight → apply → finalize                                                |
| `status complete`                    | exige `run_id` de evidencia terminal                                        |

## Criterios GO (verificados)

1. Entrypoints mutadores no eluden política (DenyProvider por defecto).
2. Rechazo de política impide handler (`test_handler_not_invoked_when_denied`).
3. Dry-run install no escribe (matriz `scripts/tests/test_install.sh`).
4. `complete` exige evidencia real (`--run-id` + store).
5. Defectos adversarios de auth/contrato/install rompen tests del full gate.
6. OpenCode 1.18.34: `skills.paths` + `opencode debug skill` lista el catálogo.

## Paquetes

| Paquete               | Estado |
| --------------------- | ------ |
| P0 arranque           | done   |
| P1 auth/registry      | done   |
| P2 clean/snap/restore | done   |
| P3 install            | done   |
| P4 contracts/state    | done   |
| P5 gate               | done   |
| P6 OpenCode/E2E       | done   |

Publicación (push/PR/merge) solo tras orden `/project-publish`.
