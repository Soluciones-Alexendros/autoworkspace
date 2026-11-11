"""Naming gate: the pre-8.0 name stays confined to an explicit allowlist."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from validate.naming_gate import ADR_FILENAME, ALLOWED_FILES, candidate_files, scan  # noqa: E402


def test_repository_is_clean() -> None:
    findings = scan(ROOT)
    assert findings == [], "\n".join(item.render() for item in findings)


def test_history_and_caches_are_out_of_scope() -> None:
    scanned = {path.relative_to(ROOT).as_posix() for path in candidate_files(ROOT)}
    assert not any(name.startswith("docs/plans/") for name in scanned)
    assert not any(name.startswith("docs/archives/") for name in scanned)
    assert "CHANGELOG.md" not in scanned
    assert not any("__pycache__" in name for name in scanned)
    assert not any(name.startswith("docs/architecture/diagrams/rendered/") for name in scanned)


def test_allowlist_entries_exist() -> None:
    missing = sorted(name for name in ALLOWED_FILES if not (ROOT / name).exists())
    assert missing == []


def test_new_leak_is_detected(tmp_path: Path) -> None:
    leak = tmp_path / "tools"
    leak.mkdir()
    (leak / "leak.py").write_text("# legacy brand: autoworkspace\n", encoding="utf-8")
    findings = scan(tmp_path, allowed=set())
    assert findings
    assert findings[0].path == "tools/leak.py"
    assert "legacy brand" in findings[0].text


def test_adr_filename_is_allowed_everywhere(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "note.md").write_text(f"See [{ADR_FILENAME}](decisions/{ADR_FILENAME}).\n", encoding="utf-8")
    assert scan(tmp_path, allowed=set()) == []
