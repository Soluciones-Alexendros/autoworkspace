"""Tests de tools/validate/release_coherence.py y cut_tag.py."""

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

COH = Path(__file__).resolve().parents[1] / "release_coherence.py"
CUT = Path(__file__).resolve().parents[2] / "version" / "cut_tag.py"


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture_root(
    tmp_path: Path,
    readme_version: str,
    package_version: str,
    overrides: dict[str, str] | None = None,
) -> Path:
    """Repositorio mínimo y coherente; solo varía la versión de README/package."""
    ov = overrides or {}
    py_ver = ov.get("pyproject", package_version)
    lk_ver = ov.get("lock", package_version)
    uv_ver = ov.get("uv", package_version)
    (tmp_path / "package.json").write_text(json.dumps({"name": "t", "version": package_version}), encoding="utf-8")
    (tmp_path / "README.md").write_text(f"# t\n\nVersión **{readme_version}**. Skills.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "t"\nversion = "{py_ver}"\n', encoding="utf-8")
    lock_doc = {
        "name": "t",
        "version": lk_ver,
        "lockfileVersion": 3,
        "packages": {"": {"name": "t", "version": lk_ver}},
    }
    (tmp_path / "package-lock.json").write_text(json.dumps(lock_doc), encoding="utf-8")
    uv_text = f'version = 1\n\n[[package]]\nname = "autoworkspace"\nversion = "{uv_ver}"\n'
    (tmp_path / "uv.lock").write_text(uv_text, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [Unreleased]\n\n- pending\n\n## [{package_version}] - 2026-10-26\n\n- x\n",
        encoding="utf-8",
    )
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        "name: ci\non: push\npermissions:\n  contents: read\njobs:\n"
        "  ok:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n"
        "    steps:\n      - run: echo ok\n",
        encoding="utf-8",
    )
    return tmp_path


def run_coherence(coh: Any, root: Path) -> list[str]:
    coh.ERRORS.clear()
    version = coh.package_version(root)
    coh.check_readme_version(root, version)
    coh.check_pyproject_version(root, version)
    coh.check_package_lock_version(root, version)
    coh.check_uv_lock_version(root, version)
    coh.check_changelog(root, version, False)
    coh.check_workflows(root)
    return list(coh.ERRORS)


def test_readme_version_mismatch_fails(tmp_path: Path) -> None:
    """README «Versión **5.1.0**» con package.json 6.0.0 debe fallar."""
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "5.1.0", "6.0.0")
    errors = run_coherence(coh, root)
    assert any("README.md declara Versión **5.1.0**" in e for e in errors), errors


def test_prerelease_fixture_parses(tmp_path: Path) -> None:
    """7.0.0-alpha.0 es semver válido; 7.0.0a0 en pyproject y uv.lock equivale."""
    coh = load(COH, "release_coherence_pre")
    root = fixture_root(
        tmp_path,
        "7.0.0-alpha.0",
        "7.0.0-alpha.0",
        {"pyproject": "7.0.0a0", "uv": "7.0.0a0"},
    )
    assert run_coherence(coh, root) == []


def test_stable_7_0_0_release_gate_passes(tmp_path: Path) -> None:
    """7.0.0 estable con sección CHANGELOG pasa el gate de publicación."""
    coh = load(COH, "release_coherence_700")
    root = fixture_root(tmp_path, "7.0.0", "7.0.0")
    assert coh.run_coherence(root, release_gate=True) == 0
    assert coh.ERRORS == []


def test_release_gate_rejects_prerelease(tmp_path: Path) -> None:
    """El prerelease sigue parseando; --release-gate exige sección estable."""
    coh = load(COH, "release_coherence_gate_pre")
    root = fixture_root(
        tmp_path,
        "7.0.0-alpha.1",
        "7.0.0-alpha.1",
        {"pyproject": "7.0.0a1", "uv": "7.0.0a1"},
    )
    assert run_coherence(coh, root) == []
    assert coh.run_coherence(root, release_gate=True) == 1
    assert any("versión estable" in e for e in coh.ERRORS), coh.ERRORS


def test_release_gate_missing_stable_section(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence_gate_missing")
    root = fixture_root(tmp_path, "7.0.0", "7.0.0")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- pending\n",
        encoding="utf-8",
    )
    assert coh.run_coherence(root, release_gate=False) == 0
    assert coh.run_coherence(root, release_gate=True) == 1
    assert any("no tiene sección [7.0.0]" in e for e in coh.ERRORS), coh.ERRORS


def test_stable_6_1_0_still_parses(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence_stable")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0")
    assert run_coherence(coh, root) == []


def test_cut_allows_stable_7_0_0_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """v7.0.0 se anuncia en dry-run y no se crea el tag."""
    cut = load(CUT, "cut_tag_stable")
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "t", "version": "7.0.0"}),
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [7.0.0] - 2026-10-29\n\n- stable\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cut, "latest_tag", lambda root: None)
    monkeypatch.setattr(cut, "git", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("git")))
    monkeypatch.setattr(cut, "write_output", lambda **kwargs: None)
    args = argparse.Namespace(
        root=tmp_path,
        apply=False,
        push=False,
        notes_file=None,
        dry_run=True,
        strict_readiness=False,
    )
    assert cut.is_prerelease("7.0.0") is False
    assert cut.cmd_cut(args) == 0
    assert cut.cmd_readiness(args) == 0


def test_cut_refuses_prerelease_stable_tag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cut = load(CUT, "cut_tag_pre")
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "t", "version": "7.0.0-alpha.0"}),
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [7.0.0-alpha.0] - 2026-10-29\n\n- breaking\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cut, "latest_tag", lambda root: "6.1.0")
    monkeypatch.setattr(cut, "git", lambda *args, **kwargs: None)
    monkeypatch.setattr(cut, "write_output", lambda **kwargs: None)
    args = argparse.Namespace(
        root=tmp_path,
        apply=True,
        push=False,
        notes_file=None,
        dry_run=False,
        strict_readiness=False,
    )
    assert cut.cmd_cut(args) == 1
    assert cut.cmd_readiness(args) == 1


def test_readme_version_matches_package(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.0.0", "6.0.0")
    assert run_coherence(coh, root) == []


def test_v02_pyproject_drift_fails(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0", {"pyproject": "6.0.0"})
    errors = run_coherence(coh, root)
    assert any("pyproject.toml" in e for e in errors), errors


def test_v02_package_lock_drift_fails(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0", {"lock": "5.0.0"})
    errors = run_coherence(coh, root)
    assert any("package-lock.json" in e for e in errors), errors


def test_v02_uv_lock_drift_fails(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0", {"uv": "6.0.0"})
    errors = run_coherence(coh, root)
    assert any("uv.lock" in e for e in errors), errors


def test_v04_skill_metadata_not_tied_to_global(tmp_path: Path) -> None:
    """Skills conservan metadata.version propio; no se exige igualdad global."""
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0")
    skill = root / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: demo\nmetadata:\n  version: "9.9.9"\n---\n',
        encoding="utf-8",
    )
    assert run_coherence(coh, root) == []


def test_v05_check_does_not_modify_files(tmp_path: Path) -> None:
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.1.0", "6.1.0")
    before = (root / "package.json").read_text(encoding="utf-8")
    assert run_coherence(coh, root) == []
    assert (root / "package.json").read_text(encoding="utf-8") == before


def test_repo_head_passes_readme_version() -> None:
    """El README real del repo declara la versión de package.json."""
    coh = load(COH, "release_coherence")
    root = COH.resolve().parents[2]
    coh.ERRORS.clear()
    coh.check_readme_version(root, coh.package_version(root))
    assert coh.ERRORS == []


def test_changelog_em_dash_rejected() -> None:
    coh = load(COH, "release_coherence")
    coh.ERRORS.clear()
    sections = coh.changelog_sections("# Changelog\n\n## [2.0.0] — 2026-09-27\n\n- x\n")
    assert "2.0.0" not in sections
    assert any("inválido" in e for e in coh.ERRORS)


def test_yanked_section() -> None:
    cut = load(CUT, "cut_tag")
    text = "## [1.2.3] - 2026-01-01 [YANKED]\n\nnotas\n"
    try:
        cut.extract_notes(text, "1.2.3")
    except ValueError as e:
        assert "YANKED" in str(e)
    else:
        raise AssertionError("debió rechazar yanked")


def test_extract_notes_ok() -> None:
    cut = load(CUT, "cut_tag")
    text = "## [Unreleased]\n\n## [2.2.0] - 2026-09-30\n\n### Added\n\n- foo\n\n## [2.0.0] - 2026-09-27\n\n- old\n"
    notes = cut.extract_notes(text, "2.2.0")
    assert "foo" in notes
    assert "old" not in notes


def test_should_cut() -> None:
    cut = load(CUT, "cut_tag")
    assert cut.should_cut("2.2.0", "2.0.0")
    assert not cut.should_cut("2.0.0", "2.0.0")
    assert not cut.should_cut("1.9.0", "2.0.0")


def test_cmd_cut_apply_skips_when_notes_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Main release job must not fail red when CHANGELOG lacks [package.version]."""

    cut = load(CUT, "cut_tag")
    (tmp_path / "package.json").write_text(json.dumps({"name": "t", "version": "5.1.0"}), encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- pending\n\n## [5.0.0] - 2026-10-17\n\n- old\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cut, "latest_tag", lambda root: "5.0.0")
    monkeypatch.setattr(cut, "write_output", lambda **kwargs: None)
    args = argparse.Namespace(
        root=tmp_path,
        apply=True,
        push=False,
        notes_file=None,
        dry_run=False,
        strict_readiness=False,
    )
    assert cut.cmd_cut(args) == 0
