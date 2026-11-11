"""Contract SSOT parity: the rule owns the prose, the hook only points at it."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))


def _parity() -> ModuleType:
    spec = importlib.util.spec_from_file_location("contract_parity", ROOT / "tools" / "validate" / "contract_parity.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rule_is_the_ssot() -> None:
    parity = _parity()
    parity.check_rule()
    text = parity.RULE.read_text(encoding="utf-8")
    assert "alwaysApply: true" in text
    assert "# Contrato de ejecución de machineroom" in text


def test_hook_digest_matches_the_rule() -> None:
    parity = _parity()
    parity.check_hook_digest()
    context = parity.hook_payload()["additional_context"]
    assert context.startswith("Machineroom Cursor contract")


def test_hook_is_a_pointer_not_a_copy() -> None:
    parity = _parity()
    parity.check_hook_is_a_pointer()


def test_stale_digest_is_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parity = _parity()
    fake_rule = tmp_path / "machineroom.mdc"
    fake_rule.write_text("---\ndescription: x\nalwaysApply: true\n---\n\n# Otro\n", encoding="utf-8")
    monkeypatch.setattr(parity, "RULE", fake_rule)
    with pytest.raises(parity.ParityError) as caught:
        parity.check_hook_digest()
    assert caught.value.component == "contract"
    assert "stale digest" in caught.value.detail


def test_policy_error_output_is_structured(tmp_path: Path) -> None:
    parity = _parity()
    with pytest.raises(parity.ParityError) as caught:
        parity.hook_payload(tmp_path / "missing.py")
    assert caught.value.function == "hook_payload"


def test_cli_is_green_and_reports_the_digest() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate" / "contract_parity.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "contract parity OK" in proc.stdout


def test_hook_payload_is_valid_json_contract() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / ".cursor" / "hooks" / "session_start.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert set(payload) == {"additional_context"}
    assert "rule_sha256=" in payload["additional_context"]
