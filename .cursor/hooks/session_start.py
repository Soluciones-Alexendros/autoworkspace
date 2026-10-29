#!/usr/bin/env python3
"""sessionStart hook: inject short execution contract (fire-and-forget)."""

from __future__ import annotations

import json
import sys

CONTRACT = (
    "Autoworkspace Cursor contract: Spanish with the operator; technical ids in "
    "English. Product mutation only via tools/execution and run_registered — no "
    "ad-hoc skill scripts. Do not use --bump. allowed-tools is not authorization. "
    "Do not run local-maintenance, local-security, local-email, or "
    "project-publish without an explicit operator request (/name if needed). "
    "role-front and role-design only with a real UI surface. Never call skip, "
    "missing dependency, or not_run a PASS. Re-evaluate role-* before each task "
    "(see AGENTS.md Lifecycle). This hook does not run on Cloud Agents; the "
    "alwaysApply project rule carries the same contract."
)


def main() -> int:
    json.dump({"additional_context": CONTRACT}, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
