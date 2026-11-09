#!/usr/bin/env bash
# Complete controlled orchestration path on disposable Git worktrees.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
uv run --project tools --frozen pytest tools/orchestrator/tests/test_full_flow.py -q
