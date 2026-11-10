# Harness integration status

Cursor and Pi are the only supported harnesses. Both sit at level A: the deterministic symlink gate. CI does not require either binary.

| Harness | Level | Evidence                                                                      |
| ------- | ----- | ----------------------------------------------------------------------------- |
| Cursor  | A     | `bash scripts/install-cursor.sh --target <dir>` symlinks each `skills/<name>` |
| Pi      | A     | `bash scripts/install-pi.sh --target <dir>` symlinks each `skills/<name>`     |

## Level A

- Symlinks are absolute and resolve to `skills/<name>`.
- `--target` does not write `$HOME`. `--user` is the only path that writes the user skills directory.
- Dry-run creates neither the destination nor the manifest.
- `scripts/tests/test_install.sh` and `scripts/tests/test_execution_e2e.sh` cover the gate. The E2E script does not invoke a harness binary.

## Cursor contract surfaces

Versioned under `.cursor/` (skills symlinks are **not** committed; run `install-cursor.sh`):

- `.cursor/rules/autoworkspace.mdc` (`alwaysApply: true`)
- `.cursor/hooks.json`, `.cursor/hooks/session_start.py`, `.cursor/hooks/shell_gate.py`
- `.cursor/agents/aw-verifier.md`
- `tools/validate/tests/test_shell_gate.py`

Surfaces are scope-aware under `--user`: the catalog is `$HOME/.autoworkspace`, and every owned path under `~/.cursor` / `~/.pi/agent` is a relative symlink into that runtime. The project rule is omitted because Cursor keeps user rules in Settings. `hooks.json` is rewritten in the runtime with `hooks/...` commands (user hooks run from `~/.cursor`) and linked from `~/.cursor/hooks.json`. `doctor.py --full` accepts both scopes.

Levels beyond A:

- **B (native discovery/load):** Customize → Skills lists all 17; `/plan-continue` routes. Human IDE only → **`not_run` in CI**.
- **C (shell gate in IDE):** an agent-proposed host-mutating shell (e.g. `apt-get upgrade`) is `deny` or `ask`. The `beforeShellExecution` matcher is whole-word, so it covers host mutation and outbound network only; ordinary commands (`python`, `git`, `npm`, `pytest`) stay open even when their text contains substrings such as `chapter`, `adapter` or `curly`. Human IDE only → **`not_run` in CI**.

## Permissions

Loading a skill does not authorize Bash, network, secrets, or paths outside the project. Product restrictions (`DenyProvider`, `run_registered`, evidence binding) remain even when the harness can load the skill file.

## Execution API (product)

- Callers use `run_registered(operation_id, params)` only. Free-form `run_operation(..., argv=..., effect=...)` is rejected.
- Evidence uses content digests (SHA-256 of bytes), UUID `run_id`, and phase/skill/target binding before `--complete`.
- Status advances under a full read→validate→write lock with idempotent replay of the same `run_id`.
