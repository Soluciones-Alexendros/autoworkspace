# Harnesses

## Pi

- Distribution: Git package (`pi install git:…@vX.Y.Z`) or local package path
- Discovery: model-free RPC `get_commands` via `tools/harness/pi.py`
- Extension: `extensions/machineroom/` (`mr_subagent`, `mr-status`)
- Subagent: `PiSubagentAdapter` with optional `--model`

## Cursor

- Distribution: plugin (`.cursor-plugin/`) and `install.sh --components full`
- Partial skills-only install must be reported as partial
- Agents: `mr-planner`, `mr-worker`, `mr-verifier`
- Hooks: `sessionStart`, `beforeShellExecution` (`shell_gate.py`)
- Headless CLI: `agent` on PATH; version recorded in evidence

## Levels A / B / C

| Level | Meaning |
| --- | --- |
| A | Static install: links, manifests, versions |
| B | Native discovery of skills / rules / agents / package commands |
| C | Policy: allow creates sentinel; deny idle; ask waits |

`not_run` or `blocked` never aggregates to PASS when the check is required.
