"""Common harness checks, report aggregation and honest exit semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Check:
    check_id: str
    level: str
    outcome: str
    detail: str
    required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "level": self.level,
            "outcome": self.outcome,
            "detail": self.detail,
            "required": self.required,
        }


def _overall(checks: list[Check]) -> str:
    required = [check for check in checks if check.required]
    if any(check.outcome == "fail" for check in required):
        return "fail"
    if any(check.outcome == "blocked" for check in required):
        return "blocked"
    if any(check.outcome == "not_run" for check in required):
        return "not_run"
    return "pass"


def build_report(
    harness: str,
    checks: list[Check],
    *,
    harness_version: str | None = None,
    package_version: str | None = None,
    source: str = "",
    ref: str = "",
    target: str = "",
) -> dict[str, Any]:
    outcome = _overall(checks)
    capabilities: dict[str, str] = {}
    for level in ("A", "B", "C"):
        level_checks = [check for check in checks if check.level == level]
        if level_checks:
            capabilities[level] = _overall(level_checks)
    return {
        "schema_version": 1,
        "harness": harness,
        "harness_version": harness_version,
        "package_version": package_version,
        "source": source,
        "ref": ref,
        "target": target,
        "components": sorted(check.check_id for check in checks),
        "checks": [check.as_dict() for check in checks],
        "capabilities": capabilities,
        "outcome": outcome,
        "reasons": [f"{check.check_id}: {check.detail}" for check in checks if check.outcome != "pass"],
    }


def report_exit_code(report: dict[str, Any]) -> int:
    outcome = report.get("outcome")
    if outcome == "pass":
        return 0
    if outcome in {"blocked", "not_run"}:
        return 3
    return 1
