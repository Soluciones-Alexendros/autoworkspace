"""Ports between the neutral scheduler and concrete harness adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from execution.ops import OpResult

from orchestrator.model import RunContext


@dataclass(frozen=True)
class AdapterResult:
    outcome: str
    run_id: str = ""
    detail: str = ""
    operation_result: OpResult | None = None


class SubagentAdapter(Protocol):
    def execute(self, task: dict[str, Any], context: RunContext) -> AdapterResult:
        """Execute exactly one task packet without deciding plan policy."""
        ...
