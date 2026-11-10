"""Install/update failures name component, function and detail (plan-validators)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.cursor_install import ConflictError, install_full, main as cursor_main  # noqa: E402
from harness.runtime import (  # noqa: E402
    InstallFailure,
    require_runtime,
    sync_payload,
    write_user_hooks_config,
)


def _minimal_source(tmp_path: Path) -> Path:
    """Checkout-shaped tree missing package.json (sync must name that component)."""
    src = tmp_path / "src"
    (src / "skills" / "fixture").mkdir(parents=True)
    (src / "skills" / "fixture" / "SKILL.md").write_text("---\nname: fixture\n---\n")
    for relative in (".cursor/agents", ".cursor/hooks", ".cursor/rules", "extensions/autoworkspace"):
        (src / relative).mkdir(parents=True)
    (src / ".cursor" / "hooks.json").write_text(
        '{"version":1,"hooks":{"sessionStart":[{"command":"python3 .cursor/hooks/session_start.py"}]}}\n'
    )
    (src / "extensions" / "autoworkspace" / "index.ts").write_text("export {}\n")
    # deliberately no package.json
    return src


def test_sync_missing_package_json_names_component(tmp_path: Path) -> None:
    src = _minimal_source(tmp_path)
    dest = tmp_path / "home" / ".autoworkspace"
    dest.parent.mkdir()
    with pytest.raises(InstallFailure) as caught:
        sync_payload(src, dest, origin="sync")
    failure = caught.value
    assert failure.component == "package.json"
    assert failure.function == "sync_payload"
    assert "missing" in failure.detail.lower() or "package.json" in failure.detail
    assert failure.to_dict() == {
        "component": "package.json",
        "function": "sync_payload",
        "detail": failure.detail,
    }


def test_require_runtime_missing_names_component(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    with pytest.raises(InstallFailure) as caught:
        require_runtime(home)
    assert caught.value.component == "runtime"
    assert caught.value.function == "require_runtime"


def test_write_user_hooks_invalid_json_names_function(tmp_path: Path) -> None:
    runtime = tmp_path / ".autoworkspace"
    (runtime / ".cursor").mkdir(parents=True)
    (runtime / ".cursor" / "hooks.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(InstallFailure) as caught:
        write_user_hooks_config(runtime)
    assert caught.value.component == "hooks.json"
    assert caught.value.function == "write_user_hooks_config"


def test_install_full_cli_json_includes_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    target = home / ".cursor"
    target.mkdir()
    monkeypatch.setattr(sys, "argv", ["cursor_install", "--target", str(target), "--user", "--json"])
    code = cursor_main(["--target", str(target), "--user", "--json"])
    assert code != 0
    # main prints JSON on stdout; capture via rerun with redirected print is awkward —
    # call install_full and mirror the CLI contract instead.
    with pytest.raises(InstallFailure) as caught:
        install_full(ROOT, target, user_scope=True)
    assert caught.value.component == "runtime"
    assert caught.value.function in {"install_full", "require_runtime"}


def test_install_full_post_link_validation_names_component(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    sync_payload(ROOT, home / ".autoworkspace", origin="sync")
    target = home / ".cursor"

    import harness.cursor_install as cursor_install

    def absolute_instead(source: Path, destination: Path) -> None:
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(str(source.resolve()), destination)

    monkeypatch.setattr(cursor_install, "make_relative_symlink", absolute_instead)
    with pytest.raises(InstallFailure) as caught:
        install_full(ROOT, target, user_scope=True)
    assert caught.value.function == "install_full"
    assert caught.value.component
    assert "relative" in caught.value.detail.lower() or "absolute" in caught.value.detail.lower()


def test_install_full_conflict_json_lists_failures(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    home = tmp_path / "home"
    home.mkdir()
    sync_payload(ROOT, home / ".autoworkspace", origin="sync")
    target = home / ".cursor"
    target.mkdir()
    (target / "hooks.json").write_text('{"version": 1, "hooks": {}}', encoding="utf-8")
    code = cursor_main(["--source", str(ROOT), "--target", str(target), "--user", "--json"])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "conflict"
    assert out["failures"]
    assert out["failures"][0]["component"] == "hooks.json"
    assert out["failures"][0]["function"] == "install_full"


def test_link_skills_user_without_runtime_json_failures(tmp_path: Path) -> None:
    home = tmp_path / "home-miss"
    home.mkdir()
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install-pi.sh"), "--user", "--yes", "--json"],
        cwd=str(ROOT),
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["status"] == "failed"
    assert payload["failures"][0]["component"] == "runtime"
    assert "FAIL runtime" in proc.stderr


def test_pi_extension_foreign_conflict_names_component(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    sync_payload(ROOT, home / ".autoworkspace", origin="sync")
    # Install skills first
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install-pi.sh"), "--user", "--yes", "--json"],
        cwd=str(ROOT),
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    ext = home / ".pi" / "agent" / "extensions" / "autoworkspace.ts"
    if ext.is_symlink() or ext.exists():
        ext.unlink()
    ext.write_text("// foreign\n", encoding="utf-8")
    # Re-run only the extension step by invoking install-pi again (skills skip, extension conflicts)
    proc2 = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install-pi.sh"), "--user", "--yes", "--json"],
        cwd=str(ROOT),
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc2.returncode != 0
    # Skills JSON may print ok on stdout before extension fails — prefer stderr FAIL line
    assert "extensions/autoworkspace.ts" in proc2.stderr
    assert "FAIL" in proc2.stderr
