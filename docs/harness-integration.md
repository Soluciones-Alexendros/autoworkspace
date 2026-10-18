# Harness integration status

Classification of agent harnesses for autoworkspace skills.

| Harness  | Status                                                                                                    | Evidence                                                                                       |
| -------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| OpenCode | partial (A pass; B version; C help surface) — full ask/deny skill load still pending deeper harness proof | `opencode.json`, `scripts/install-opencode.sh --target`, `scripts/tests/test_execution_e2e.sh` |
| Cursor   | documented-not-proven                                                                                     | project `skills/` + optional `.agents/skills` symlinks                                         |
| Codex    | documented-not-proven                                                                                     | install target via `scripts/install.sh --target`                                               |
| Copilot  | documented-not-proven                                                                                     | folder layout only                                                                             |

## OpenCode acceptance levels

- **A (deterministic gate):** configuration, contracts, and `tools/execution` tests. No network/accounts/models. Required for every merge.
- **B (native discovery/load):** real OpenCode binary of a declared version (currently **1.18.34**) is present; version and skill discovery/load are demonstrated with redacted output.
- **C (permissions):** skill allow/deny independent of action permission; a denied action must not create a sentinel; no `--auto`. Ask/prompt proof requires a channel that actually surfaces the prompt.

If the binary is unavailable, B and C are `not_run` and the E2E script must **not** print an integral `E2E OK`. Gate A may still pass.

## Permissions

Loading a skill does not authorize Bash, network, secrets, or paths outside the project. Product restrictions (`DenyProvider`, `run_registered`, evidence binding) remain even when the harness can load the skill file.

## Execution API (product)

- Callers use `run_registered(operation_id, params)` only. Free-form `run_operation(..., argv=..., effect=...)` is rejected.
- Evidence uses content digests (SHA-256 of bytes), UUID `run_id`, and phase/skill/target binding before `--complete`.
- Status advances under a full read→validate→write lock with idempotent replay of the same `run_id`.
