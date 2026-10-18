# Migrations — verifiable closure

Increment: `autoworkspace-verifiable-closure-v2` (see `tasks/plan-verifiable-closure.md`).

## CLI / API

| Before                                                                  | After                                                                              |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `run_operation(..., effect="read", argv=[...], require_approval=False)` | Rejected. Use `run_registered(operation_id, params)` with a registered op.         |
| Caller-supplied `effect` / `argv` / `require_approval` in params        | Rejected as reserved parameters.                                                   |
| `snapshot_state.py <id>` create without registry                        | Exit 3 unless `AUTOWORKSPACE_EXECUTION_APPROVED=1` (set only by approved handler). |
| `--restore-root` existing temp dir                                      | Rejected. Program creates empty private staging.                                   |
| Evidence `work_digest` from path/size/mtime                             | Content manifest (SHA-256 of bytes); admin paths excluded.                         |
| Free-form `run_id` with `:`                                             | UUID only; path separators rejected.                                               |
| `--complete` ignoring invalid `project.yaml`                            | `ProjectConfigError` fails complete; allowlist/phases enforced.                    |
| STATUS→DEFINE via inequality                                            | Rejected unless explicit `allow_restart`.                                          |
| Same `run_id` complete twice                                            | Idempotent; no second advance.                                                     |

## Installers

- `scripts/install.sh` journals per-resource prior symlink targets and restores them on rollback (does not blindly `rm` pre-existing links).
- `scripts/install-opencode.sh` only treats planned skill names as conflicts; foreign non-colliding entries coexist.

## Standalone / preflight

- `shared_dependencies` (e.g. `tools/execution`) must resolve under skill root, `vendor/execution`, or workspace `../../tools/…`.
- Package for true standalone: `bash scripts/package-standalone-skill.sh --skill local-maintenance`.
- Hard `network: true` without `AUTOWORKSPACE_ALLOW_NETWORK=1` → preflight **blocked** (not optional success).
- `clean_routine` effective plan includes `keep_versions`, `journal_time`, `journal_size`, `pkg_mgr`; handlers apply approved params before acting (not stale globals).

## Historical GO

`tasks/plan-execution-closure.md` GO remains historical for that increment. It does not certify this closure. Dictamen for this increment is recorded in `tasks/plan-verifiable-closure.md` §8.
