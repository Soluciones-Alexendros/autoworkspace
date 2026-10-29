# Harness setup — Cursor and Pi

`skills/` is the only catalog that is committed. Installers create symlinks; they do not copy skill bodies.

## Public API (flat destinations)

| Destination | Command |
| ----------- | ------- |
| Project `.cursor/skills` (default) | `bash scripts/install-cursor.sh` |
| Project `.cursor/skills` via `--target .` | `bash scripts/install-cursor.sh --target .` |
| Project `.cursor/skills` explicit | `bash scripts/install-cursor.sh --target .cursor/skills` |
| User `~/.cursor/skills` | `bash scripts/install-cursor.sh --user` |
| Any directory (flat 16 symlinks) | `bash scripts/install-cursor.sh --target /tmp/test-cursor` |
| Project `.pi/skills` (default) | `bash scripts/install-pi.sh` |
| Project `.pi/skills` via `--target .` | `bash scripts/install-pi.sh --target .` |
| User `~/.pi/agent/skills` | `bash scripts/install-pi.sh --user` |
| Any directory (flat 16 symlinks) | `bash scripts/install-pi.sh --target /tmp/test-pi` |

`--target .` (or the checkout root) resolves to the harness default skills directory — it does **not** place symlinks in the repository root. Arbitrary `--target DIR` stays flat (compat 7.0.0).

`--target` never writes `$HOME`. `--dry-run` performs no filesystem writes. `--uninstall` removes only symlinks recorded in the manifest and still owned by this checkout. `--yes` is non-interactive (foreign/real-dir conflicts still refuse). `--json` prints a single JSON object on stdout.

## AI wrapper (`install.sh --harness`)

| Destination | Command |
| ----------- | ------- |
| `/tmp/ai-cursor/.cursor/skills` | `bash scripts/install.sh --harness cursor --target /tmp/ai-cursor --yes --json` |
| `/tmp/ai-pi/.pi/skills` | `bash scripts/install.sh --harness pi --target /tmp/ai-pi --yes --json` |
| User cursor/pi skills | `bash scripts/install.sh --harness cursor\|pi --user --yes` |

The wrapper nests under `.cursor/skills` or `.pi/skills` unless the path already ends in a skills directory. Public `install-cursor.sh --target /tmp/test-cursor` remains flat.

## Pi notes

Pi loads project skills from `.pi/skills/` and user skills from `~/.pi/agent/skills/` ([documentation](https://pi.dev/docs/latest/skills)).

## Execution and privileges

Harnesses only need `SKILL.md` (plus `references/` / `scripts/` as linked). Mutating product operations are declared in `tools/execution/registry.yaml` and invoked via `run_registered` with approval — not via per-skill `execution.yaml` (forbidden under `skills/`). Skills may set `metadata.execution: <tool_id>`. `allowed-tools` is a catalog privilege ceiling by `metadata.type` (see ADR-0017); it does not authorize Cursor tools by itself.
