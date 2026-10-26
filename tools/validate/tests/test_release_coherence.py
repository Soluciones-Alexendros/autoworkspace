"""Tests de tools/validate/release_coherence.py y cut_tag.py."""

import importlib.util
from pathlib import Path

COH = Path(__file__).resolve().parents[1] / "release_coherence.py"
CUT = Path(__file__).resolve().parents[2] / "version" / "cut_tag.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture_root(tmp_path, readme_version, package_version):
    """Repositorio mínimo y coherente; solo varía la versión de README/package."""
    import json

    (tmp_path / "package.json").write_text(
        json.dumps({"name": "t", "version": package_version}), encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(
        f"# t\n\nVersión **{readme_version}**. Skills.\n", encoding="utf-8"
    )
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


def run_coherence(coh, root):
    coh.ERRORS.clear()
    version = coh.package_version(root)
    coh.check_readme_version(root, version)
    coh.check_changelog(root, version, False)
    coh.check_workflows(root)
    return list(coh.ERRORS)


def test_readme_version_mismatch_fails(tmp_path):
    """README «Versión **5.1.0**» con package.json 6.0.0 debe fallar."""
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "5.1.0", "6.0.0")
    errors = run_coherence(coh, root)
    assert any("README.md declara Versión **5.1.0**" in e for e in errors), errors


def test_readme_version_matches_package(tmp_path):
    coh = load(COH, "release_coherence")
    root = fixture_root(tmp_path, "6.0.0", "6.0.0")
    assert run_coherence(coh, root) == []


def test_repo_head_passes_readme_version():
    """El README real del repo declara la versión de package.json."""
    coh = load(COH, "release_coherence")
    root = COH.resolve().parents[2]
    coh.ERRORS.clear()
    coh.check_readme_version(root, coh.package_version(root))
    assert coh.ERRORS == []


def test_changelog_em_dash_rejected():
    coh = load(COH, "release_coherence")
    coh.ERRORS.clear()
    sections = coh.changelog_sections("# Changelog\n\n## [2.0.0] — 2026-09-27\n\n- x\n")
    assert "2.0.0" not in sections
    assert any("inválido" in e for e in coh.ERRORS)


def test_yanked_section():
    cut = load(CUT, "cut_tag")
    text = "## [1.2.3] - 2026-01-01 [YANKED]\n\nnotas\n"
    try:
        cut.extract_notes(text, "1.2.3")
    except ValueError as e:
        assert "YANKED" in str(e)
    else:
        raise AssertionError("debió rechazar yanked")


def test_extract_notes_ok():
    cut = load(CUT, "cut_tag")
    text = "## [Unreleased]\n\n## [2.2.0] - 2026-09-30\n\n### Added\n\n- foo\n\n## [2.0.0] - 2026-09-27\n\n- old\n"
    notes = cut.extract_notes(text, "2.2.0")
    assert "foo" in notes
    assert "old" not in notes


def test_should_cut():
    cut = load(CUT, "cut_tag")
    assert cut.should_cut("2.2.0", "2.0.0")
    assert not cut.should_cut("2.0.0", "2.0.0")
    assert not cut.should_cut("1.9.0", "2.0.0")


def test_cmd_cut_apply_skips_when_notes_missing(tmp_path, monkeypatch):
    """Main release job must not fail red when CHANGELOG lacks [package.version]."""
    import argparse
    import json

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
