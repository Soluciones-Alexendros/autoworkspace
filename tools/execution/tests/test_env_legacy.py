"""D3/H2: the approval env reads the new prefix and the pre-8.0 fallback."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from execution.approval import env_with_legacy  # noqa: E402
from pytest import MonkeyPatch  # noqa: E402


def test_current_prefix_wins(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MACHINEROOM_APPROVAL_PROVIDER", "interactive")
    monkeypatch.setenv("AUTOWORKSPACE_APPROVAL_PROVIDER", "deny")
    assert env_with_legacy("APPROVAL_PROVIDER", "deny") == "interactive"


def test_legacy_fallback_applies(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("MACHINEROOM_APPROVAL_PROVIDER", raising=False)
    monkeypatch.setenv("AUTOWORKSPACE_APPROVAL_PROVIDER", "interactive")
    assert env_with_legacy("APPROVAL_PROVIDER", "deny") == "interactive"


def test_default_when_neither_is_set(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("MACHINEROOM_APPROVAL_PROVIDER", raising=False)
    monkeypatch.delenv("AUTOWORKSPACE_APPROVAL_PROVIDER", raising=False)
    assert env_with_legacy("APPROVAL_PROVIDER", "deny") == "deny"
