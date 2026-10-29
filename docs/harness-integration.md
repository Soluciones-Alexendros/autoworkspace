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

## Permissions

Loading a skill does not authorize Bash, network, secrets, or paths outside the project. Product restrictions (`DenyProvider`, `run_registered`, evidence binding) remain even when the harness can load the skill file.

## Execution API (product)

- Callers use `run_registered(operation_id, params)` only. Free-form `run_operation(..., argv=..., effect=...)` is rejected.
- Evidence uses content digests (SHA-256 of bytes), UUID `run_id`, and phase/skill/target binding before `--complete`.
- Status advances under a full read→validate→write lock with idempotent replay of the same `run_id`.
