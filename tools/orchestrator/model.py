"""Shared orchestration context and run summaries."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from orchestrator.ports import AdapterResult


@dataclass(frozen=True)
class RunContext:
    repo: Path
    plan_id: str
    plan_digest: str
    base_revision: str
    run_id: str
    adapter: str
    dry_run: bool = False
    cancel_event: threading.Event = field(default_factory=threading.Event)


@dataclass(frozen=True)
class RunSummary:
    outcome: str
    results: tuple[AdapterResult, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "results": [
                {"outcome": result.outcome, "run_id": result.run_id, "detail": result.detail}
                for result in self.results
            ],
        }
