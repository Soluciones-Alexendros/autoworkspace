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
