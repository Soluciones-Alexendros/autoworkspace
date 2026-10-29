"""Tests de hygiene.py: .env versionado falla; .env.example pasa."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HYGIENE = Path(__file__).resolve().parents[1] / "hygiene.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HYGIENE), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_env_example_ok(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".env.example").write_text("FOO=bar\n", encoding="utf-8")
    subprocess.run(["git", "add", ".env.example"], cwd=tmp_path, check=True, capture_output=True)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_env_tracked_fails(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-f", ".env"], cwd=tmp_path, check=True, capture_output=True)
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "secreto rastreado: .env" in r.stdout


def _init_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)


def test_audit_quick_timestamp_tracked_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "audit-quick-20261027-134032.json"
    target.parent.mkdir(parents=True)
    # Contenido sintético; el guard no debe reimprimirlo.
    payload = (
        '{"metadata":{"hostname":"SHOULD_NOT_APPEAR","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n'
    )
    target.write_text(payload, encoding="utf-8")
    subprocess.run(
        ["git", "add", "-f", str(target.relative_to(tmp_path))], cwd=tmp_path, check=True, capture_output=True
    )
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado: skills/local-maintenance/audit-quick-20261027-134032.json" in r.stdout
    assert "SHOULD_NOT_APPEAR" not in r.stdout
    assert "SHOULD_NOT_APPEAR" not in r.stderr


def test_audit_quick_fixture_path_ok(tmp_path: Path) -> None:
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "fixtures" / "audit-quick-20261027-134032.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        '{"metadata":{"hostname":"fixture","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n',
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "-f", str(target.relative_to(tmp_path))], cwd=tmp_path, check=True, capture_output=True
    )
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_host_audit_schema_without_timestamp_name_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "host-report.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        '{"metadata":{"hostname":"LEAK","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n',
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "-f", str(target.relative_to(tmp_path))], cwd=tmp_path, check=True, capture_output=True
    )
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado: skills/local-maintenance/host-report.json" in r.stdout
    assert "LEAK" not in r.stdout
    assert "LEAK" not in r.stderr


def test_repos_taller_tracked_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    (tmp_path / "repos-taller.tsv").write_text("# secret-row\n", encoding="utf-8")
    subprocess.run(["git", "add", "-f", "repos-taller.tsv"], cwd=tmp_path, check=True, capture_output=True)
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado: repos-taller.tsv" in r.stdout
    assert "secret-row" not in r.stdout
    assert "secret-row" not in r.stderr
