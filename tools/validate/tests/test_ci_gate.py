"""G07-G13: matriz del agregador ci-gate."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

GATE = Path(__file__).resolve().parents[1] / "ci_gate.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ci_gate_mod", GATE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_gate_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def _needs(**results: str) -> dict[str, dict[str, str]]:
    return {k: {"result": v} for k, v in results.items()}


def test_g07_all_success() -> None:
    mod = _load()
    code, _ = mod.evaluate(_needs(a="success", b="success"), set(), False)
    assert code == 0


def test_g08_failure_blocks() -> None:
    mod = _load()
    code, msg = mod.evaluate(_needs(a="success", b="failure"), set(), False)
    assert code == 1
    assert "b=failure" in msg


def test_g09_cancelled_blocks() -> None:
    mod = _load()
    code, msg = mod.evaluate(_needs(a="cancelled"), set(), False)
    assert code == 1
    assert "cancelled" in msg


def test_g10_expected_skip_ok() -> None:
    mod = _load()
    code, _ = mod.evaluate(
        _needs(a="success", check_bump="skipped"),
        {"check_bump"},
        False,
    )
    assert code == 0


def test_g11_unexpected_skip_blocks() -> None:
    mod = _load()
    code, msg = mod.evaluate(_needs(a="success", hygiene="skipped"), set(), False)
    assert code == 1
    assert "hygiene=skipped" in msg


def test_g12_missing_blocks() -> None:
    mod = _load()
    code, msg = mod.evaluate({"a": {}}, set(), False)
    assert code == 1
    assert "missing" in msg


def test_g13_hold_blocks() -> None:
    mod = _load()
    code, msg = mod.evaluate(_needs(a="success"), set(), True)
    assert code == 1
    assert "hold" in msg


def test_cli_announces_private_na(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    mod = _load()
    needs = _needs(a="success", **{"private-denylist": "skipped"})
    monkeypatch.setenv("NEEDS_JSON", json.dumps(needs))
    monkeypatch.setenv("ALLOWED_SKIPS", "private-denylist")
    monkeypatch.setenv("HOLD", "false")
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert "PRIVATE_CHECK_NOT_APPLICABLE_TO_PR" in out
