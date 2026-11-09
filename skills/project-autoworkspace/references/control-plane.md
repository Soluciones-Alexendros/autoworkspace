# Control plane

| Component | Path | Responsibility |
| --- | --- | --- |
| Skill router | `tools/skill-router/` | Intent → skill selection |
| Workspace router | `tools/workspace-router/` | DEFINE→…→STATUS phases, plan status |
| Execution registry | `tools/execution/registry.yaml` | OpSpec, effects, approvals |
| Ops / evidence | `tools/execution/ops.py`, `evidence.py` | `run_verified`, digests, store |
| Orchestrator | `tools/orchestrator/` | DAG, worktrees, staging, adapters |
| Contracts | `tools/contracts/` | Schemas for plan, result, harness report |

Delegating to a subagent does not expand permissions. Adapters execute one task
packet; acceptance and publication stay outside the adapter.
