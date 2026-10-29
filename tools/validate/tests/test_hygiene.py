"""Tests de hygiene.py: fail-closed, secretos e informes sintéticos."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

HYGIENE = Path(__file__).resolve().parents[1] / "hygiene.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HYGIENE), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _init_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)


def _add(tmp_path: Path, rel: str) -> None:
    subprocess.run(["git", "add", "-f", "--", rel], cwd=tmp_path, check=True, capture_output=True)


# --- Controles existentes (H02-H04, H09-H11, H18) ---


def test_env_example_ok(tmp_path: Path) -> None:
    _init_git(tmp_path)
    (tmp_path / ".env.example").write_text("FOO=bar\n", encoding="utf-8")
    _add(tmp_path, ".env.example")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_env_tracked_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    _add(tmp_path, ".env")
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "secreto rastreado: .env" in r.stdout


def test_empty_valid_repo_ok(tmp_path: Path) -> None:
    """H01: repositorio Git válido sin tracked es limpio."""
    _init_git(tmp_path)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_normal_tracked_file_ok(tmp_path: Path) -> None:
    """H02: archivo normal versionado no falla."""
    _init_git(tmp_path)
    (tmp_path / "README.md").write_text("ok\n", encoding="utf-8")
    _add(tmp_path, "README.md")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_audit_quick_timestamp_tracked_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "audit-quick-20261027-134032.json"
    target.parent.mkdir(parents=True)
    payload = (
        '{"metadata":{"hostname":"SHOULD_NOT_APPEAR","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n'
    )
    target.write_text(payload, encoding="utf-8")
    _add(tmp_path, str(target.relative_to(tmp_path)))
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
    _add(tmp_path, str(target.relative_to(tmp_path)))
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
    _add(tmp_path, str(target.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado: skills/local-maintenance/host-report.json" in r.stdout
    assert "LEAK" not in r.stdout
    assert "LEAK" not in r.stderr


def test_repos_taller_tracked_fails(tmp_path: Path) -> None:
    _init_git(tmp_path)
    (tmp_path / "repos-taller.tsv").write_text("# secret-row\n", encoding="utf-8")
    _add(tmp_path, "repos-taller.tsv")
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado: repos-taller.tsv" in r.stdout
    assert "secret-row" not in r.stdout
    assert "secret-row" not in r.stderr


# --- Fail-closed enumeration (H05-H08) ---


def _load_hygiene(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, HYGIENE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_git_absent_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H05: Git ausente no es limpio."""
    _init_git(tmp_path)
    mod = _load_hygiene("hygiene_under_test")

    def boom(*_a: Any, **_k: Any) -> Any:
        raise FileNotFoundError("git missing")

    monkeypatch.setattr(mod.subprocess, "run", boom)
    result = mod.enumerate_tracked(tmp_path)
    assert result.status == "error"
    assert mod.run_hygiene(tmp_path) != 0


def test_git_ls_files_nonzero_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H06: git ls-files rc != 0 no es limpio."""
    _init_git(tmp_path)
    mod = _load_hygiene("hygiene_h06")
    calls = {"n": 0}

    def fake_run(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[Any]:
        calls["n"] += 1
        if calls["n"] == 1:
            # rev-parse ok
            return subprocess.CompletedProcess(args=["git"], returncode=0, stdout="true\n", stderr="")
        return subprocess.CompletedProcess(args=["git", "ls-files", "-z"], returncode=128, stdout=b"", stderr=b"fatal")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.run_hygiene(tmp_path) != 0


def test_git_ls_files_timeout_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H07: timeout de enumeración no es limpio."""
    _init_git(tmp_path)
    mod = _load_hygiene("hygiene_h07")
    calls = {"n": 0}

    def fake_run(*_a: Any, **_k: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 1:
            return subprocess.CompletedProcess(args=["git"], returncode=0, stdout="true\n", stderr="")
        raise subprocess.TimeoutExpired(cmd="git", timeout=1)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.run_hygiene(tmp_path) != 0


def test_non_git_root_is_error(tmp_path: Path) -> None:
    """H08: directorio no Git no equivale a repo vacío limpio."""
    (tmp_path / "readme.txt").write_text("x\n", encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "HYGIENE: OK" not in r.stdout


# --- Lectura / límites / symlink (H12-H17, H19-H20) ---


def test_read_failure_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """H12: fallo de lectura determinista (fault injection)."""
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "opaque.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"x":1}\n', encoding="utf-8")
    _add(tmp_path, str(target.relative_to(tmp_path)))
    mod = _load_hygiene("hygiene_h12")
    real_open = Path.open

    def flaky_open(self: Path, *a: Any, **k: Any) -> Any:
        if self.name == "opaque.json":
            raise OSError("injected read failure")
        return real_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", flaky_open)
    assert mod.run_hygiene(tmp_path) != 0


def test_oversize_json_is_error(tmp_path: Path) -> None:
    """H13: JSON elegible mayor del presupuesto no es limpio."""
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "big.json"
    target.parent.mkdir(parents=True)
    budget = 2_000_000
    target.write_bytes(b"{" + (b"a" * (budget + 10)) + b"}")
    _add(tmp_path, str(target.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "inspeccionable" in r.stdout or "presupuesto" in r.stdout or "ERROR" in r.stdout


def test_exact_budget_json_schema_match(tmp_path: Path) -> None:
    """H14: tamaño exacto al límite sigue inspeccionable; esquema detectado."""
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "exact.json"
    target.parent.mkdir(parents=True)
    mod = _load_hygiene("hygiene_h14")
    meta = b'{"metadata":{"hostname":"EXACT_MARKER","kernel":"x"},"health_score":{},"findings":[],"summary":{},"pad":"'
    end = b'"}'
    mid = mod.HOST_AUDIT_MAX_BYTES - len(meta) - len(end)
    assert mid > 0
    target.write_bytes(meta + (b"y" * mid) + end)
    assert target.stat().st_size == mod.HOST_AUDIT_MAX_BYTES
    _add(tmp_path, str(target.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado:" in r.stdout
    assert "EXACT_MARKER" not in r.stdout
    assert "EXACT_MARKER" not in r.stderr


def test_invalid_json_not_host_report(tmp_path: Path) -> None:
    """H15: JSON inválido en alcance no se trata como informe; no es ERROR de lectura."""
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "broken.json"
    target.parent.mkdir(parents=True)
    target.write_text("{not-json", encoding="utf-8")
    _add(tmp_path, str(target.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HYGIENE: OK" in r.stdout


def test_filename_with_space_and_newline(tmp_path: Path) -> None:
    """H16: nombres con espacio y salto de línea se enumeran con -z."""
    _init_git(tmp_path)
    weird = tmp_path / "skills" / "local-maintenance"
    weird.mkdir(parents=True)
    spaced = weird / "my report.json"
    spaced.write_text(
        '{"metadata":{"hostname":"SPACE_MARK","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n',
        encoding="utf-8",
    )
    nl_name = "line\nbreak.json"
    nl_path = weird / nl_name
    nl_path.write_text("{}", encoding="utf-8")
    # git add -f -- path with newline needs -z / pathspec from stdin
    subprocess.run(
        ["git", "add", "-f", "--", str(spaced.relative_to(tmp_path))],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    # Newline in filename: use git update-index --add --stdin -z
    rel_nl = str(nl_path.relative_to(tmp_path)).encode("utf-8") + b"\0"
    subprocess.run(
        ["git", "update-index", "--add", "-z", "--stdin"],
        cwd=tmp_path,
        input=rel_nl,
        check=True,
        capture_output=True,
    )
    r = _run(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "informe de host rastreado:" in r.stdout
    assert "SPACE_MARK" not in r.stdout


def test_external_symlink_is_error(tmp_path: Path) -> None:
    """H17: symlink a fuera del root no se sigue; resultado explícito no limpio."""
    _init_git(tmp_path)
    outside = tmp_path.parent / f"outside-{tmp_path.name}.json"
    outside.write_text(
        '{"metadata":{"hostname":"SYMLINK_MARK","kernel":"x"},"health_score":{},"findings":[],"summary":{}}\n',
        encoding="utf-8",
    )
    dest_dir = tmp_path / "skills" / "local-maintenance"
    dest_dir.mkdir(parents=True)
    link = dest_dir / "linked.json"
    link.symlink_to(outside)
    _add(tmp_path, str(link.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "SYMLINK_MARK" not in r.stdout
    assert "SYMLINK_MARK" not in r.stderr
    outside.unlink(missing_ok=True)


def test_double_invocation_no_error_bleed(tmp_path: Path) -> None:
    """H19: segunda invocación no arrastra errores de la primera."""
    _init_git(tmp_path)
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    _add(tmp_path, ".env")
    mod = _load_hygiene("hygiene_h19")
    assert mod.run_hygiene(tmp_path) == 1
    other = tmp_path / "other"
    other.mkdir()
    _init_git(other)
    assert mod.run_hygiene(other) == 0


def test_private_marker_absent_from_outputs(tmp_path: Path) -> None:
    """H20: marcador privado de fixture no aparece en stdout/stderr."""
    _init_git(tmp_path)
    target = tmp_path / "skills" / "local-maintenance" / "host-report.json"
    target.parent.mkdir(parents=True)
    marker = "PRIVATE_MARKER_CI_BACKLOG_01"
    target.write_text(
        f'{{"metadata":{{"hostname":"{marker}","kernel":"x"}},"health_score":{{}},"findings":[],"summary":{{}}}}\n',
        encoding="utf-8",
    )
    _add(tmp_path, str(target.relative_to(tmp_path)))
    r = _run(tmp_path)
    assert r.returncode == 1
    assert marker not in r.stdout
    assert marker not in r.stderr
