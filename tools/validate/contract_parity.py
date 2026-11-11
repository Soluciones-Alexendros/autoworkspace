"""Contract parity: the Cursor rule is the SSOT and the hook only points at it.

Checks, in order:
1. `.cursor/rules/machineroom.mdc` exists, keeps YAML frontmatter and sets
   ``alwaysApply: true``.
2. ``session_start.py`` emits a summary whose ``rule_sha256=`` prefix matches the
   current rule digest, so editing the rule without refreshing the hook fails.
3. The hook does not copy the rule body: no line longer than the pointer budget
   is taken verbatim from the rule.
4. ``scripts/cursor-user-rule.sh`` prints that same rule file.

Failure output is ``FAIL <component> <function>: <detail>`` with exit code 1, or
``not_run``/exit 3 when the rule is missing, so a missing artifact is never read
as a green gate.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / ".cursor" / "rules" / "machineroom.mdc"
HOOK = ROOT / ".cursor" / "hooks" / "session_start.py"
USER_RULE_SCRIPT = ROOT / "scripts" / "cursor-user-rule.sh"
DIGEST_PREFIX = "rule_sha256="
MAX_SUMMARY_CHARS = 700
MIN_COPIED_LINE_CHARS = 60


class ParityError(RuntimeError):
    """Structured parity failure: component + function + detail."""

    def __init__(self, function: str, detail: str) -> None:
        self.component = "contract"
        self.function = function
        self.detail = detail
        super().__init__(f"FAIL {self.component} {function}: {detail}")


def rule_digest(path: Path | None = None) -> str:
    """SHA-256 of the rule bytes (current ``RULE`` unless overridden)."""
    return hashlib.sha256((path or RULE).read_bytes()).hexdigest()


def hook_payload(hook: Path = HOOK) -> dict[str, str]:
    """Run the sessionStart hook and return its JSON payload."""
    try:
        proc = subprocess.run(
            [sys.executable, str(hook)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ParityError("hook_payload", f"cannot run {hook}: {exc}") from exc
    if proc.returncode != 0:
        raise ParityError("hook_payload", f"hook exited {proc.returncode}: {proc.stderr.strip()[:200]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ParityError("hook_payload", f"hook stdout is not JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("additional_context"), str):
        raise ParityError("hook_payload", "hook payload lacks additional_context")
    return payload


def check_rule() -> None:
    """The SSOT rule must exist with frontmatter that applies always."""
    if not RULE.is_file():
        raise ParityError("check_rule", f"missing {RULE}")
    text = RULE.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ParityError("check_rule", "rule has no YAML frontmatter block")
    frontmatter = text.split("---", 2)[1]
    if not re.search(r"^alwaysApply:\s*true\s*$", frontmatter, re.MULTILINE):
        raise ParityError("check_rule", "rule must set alwaysApply: true")
    if not re.search(r"^description:\s*\S", frontmatter, re.MULTILINE):
        raise ParityError("check_rule", "rule must declare a description")


def check_hook_digest() -> None:
    """The hook summary must carry the digest of the current rule."""
    context = hook_payload()["additional_context"]
    match = re.search(rf"{DIGEST_PREFIX}([0-9a-f]+)", context)
    if match is None:
        raise ParityError("check_hook_digest", f"summary lacks {DIGEST_PREFIX}<hex>")
    expected = rule_digest()[: len(match.group(1))]
    if match.group(1) != expected:
        raise ParityError(
            "check_hook_digest",
            f"stale digest in session_start.py: hook={match.group(1)} rule={expected}; refresh the summary",
        )


def check_hook_is_a_pointer() -> None:
    """The hook must stay a pointer: short, and not a copy of the rule body."""
    context = hook_payload()["additional_context"]
    if len(context) > MAX_SUMMARY_CHARS:
        raise ParityError(
            "check_hook_is_a_pointer",
            f"summary is {len(context)} chars (budget {MAX_SUMMARY_CHARS}); it is duplicating the rule",
        )
    body_lines = {
        line.strip()
        for line in RULE.read_text(encoding="utf-8").splitlines()
        if len(line.strip()) > MIN_COPIED_LINE_CHARS and not line.strip().startswith("---")
    }
    copied = [line for line in body_lines if line in context]
    if copied:
        raise ParityError("check_hook_is_a_pointer", f"summary copies {len(copied)} rule line(s) verbatim")


def check_user_rule_script() -> None:
    """The paste helper must print the same SSOT file."""
    if not USER_RULE_SCRIPT.is_file():
        raise ParityError("check_user_rule_script", f"missing {USER_RULE_SCRIPT}")
    text = USER_RULE_SCRIPT.read_text(encoding="utf-8")
    if "rules/machineroom.mdc" not in text:
        raise ParityError("check_user_rule_script", "helper does not reference rules/machineroom.mdc")


CHECKS = (check_rule, check_hook_digest, check_hook_is_a_pointer, check_user_rule_script)


def main() -> int:
    if not RULE.is_file():
        print(f"not_run: contract rule missing: {RULE}", file=sys.stderr)
        return 3
    failures = 0
    for check in CHECKS:
        try:
            check()
        except ParityError as exc:
            print(exc, file=sys.stderr)
            failures += 1
    if failures:
        print(f"CONTRACT: FAIL ({failures})", file=sys.stderr)
        return 1
    print(f"contract parity OK (rule {rule_digest()[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
