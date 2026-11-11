#!/usr/bin/env python3
"""sessionStart hook: inject a pointer to the SSOT rule, not a copy of it.

The execution contract lives in `.cursor/rules/machineroom.mdc` (alwaysApply).
Duplicating its prose here drifted once already, so this hook emits a short
summary bound to the rule digest: `tools/validate/contract_parity.py` recomputes
the digest and fails when the hook and the rule disagree.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RULE = Path(__file__).resolve().parents[1] / "rules" / "machineroom.mdc"


def rule_digest(path: Path) -> str:
    """SHA-256 of the rule bytes; the only value shared with the validator."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(digest: str) -> str:
    return (
        "Machineroom Cursor contract (SSOT: .cursor/rules/machineroom.mdc): "
        "Spanish with the operator, technical ids in English. Product mutation only via "
        "tools/execution run_registered; no ad-hoc skill scripts; no --bump; allowed-tools is "
        "not authorization. Never call a skip, missing dependency or not_run a PASS. "
        f"rule_sha256={digest[:16]}"
    )


def main() -> int:
    try:
        digest = rule_digest(RULE)
    except OSError as exc:
        print(
            f"FAIL contract session_start: unreadable rule {RULE}: {exc}",
            file=sys.stderr,
        )
        fallback = "machineroom contract unavailable; read .cursor/rules/machineroom.mdc"
        json.dump({"additional_context": fallback}, sys.stdout)
        sys.stdout.write("\n")
        return 0
    json.dump({"additional_context": summary(digest)}, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
