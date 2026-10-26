"""Tests del autoversionado (tools/version/bump.py). Sin dependencias externas."""

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

BUMP = Path(__file__).resolve().parents[1] / "bump.py"


def load_bump(tmp: Path | None = None) -> Any:
    spec = importlib.util.spec_from_file_location("bump", BUMP)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bump = load_bump()


def test_normalize_kind_aliases_es() -> None:
    assert bump.normalize_kind("major") == "major"
    assert bump.normalize_kind("actualización") == "major"
    assert bump.normalize_kind("actualizacion-mayor") == "major"
    assert bump.normalize_kind("desarrollo menor") == "minor"
    assert bump.normalize_kind("menor") == "minor"
    assert bump.normalize_kind("feature") == "minor"
    assert bump.normalize_kind("parche") == "patch"
    assert bump.normalize_kind("parcheado") == "patch"
    assert bump.normalize_kind("fix") == "patch"


def test_normalize_kind_unknown() -> None:
    try:
        bump.normalize_kind("enorme")
    except ValueError:
        return
    raise AssertionError("debió fallar con magnitud desconocida")


def test_bump_version_magnitudes() -> None:
    assert bump.bump_version("1.2.3", "major") == "2.0.0"
    assert bump.bump_version("1.2.3", "minor") == "1.3.0"
    assert bump.bump_version("1.2.3", "patch") == "1.2.4"
    assert bump.bump_version("0.1.0", "minor") == "0.2.0"


def test_bump_version_invalid() -> None:
    try:
        bump.bump_version("1.2", "patch")
    except ValueError:
        return
    raise AssertionError("debió fallar con version no semver")


def test_write_skill_version_preserves_format(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "demo-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: demo-skill\nmetadata:\n  version: "0.1.0"\n---\n\n# Demo\n',
        encoding="utf-8",
    )
    old = bump.write_skill_version(skill, "0.1.1")
    assert old == "0.1.0"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert 'version: "0.1.1"' in text
    assert bump.read_skill_version(skill) == "0.1.1"


def test_skills_from_paths() -> None:
    paths = [
        "skills/codigo-seguridad/SKILL.md",
        "skills/codigo-seguridad/references/x.md",
        "docs/STANDARD.md",
        "tools/version/bump.py",
    ]
    assert bump.skills_from_paths(paths) == ["codigo-seguridad"]


def test_main_dry_run_tmp_root(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "demo-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: demo-skill\nmetadata:\n  version: "0.1.0"\n---\n\n# Demo\n',
        encoding="utf-8",
    )
    rc = bump.main(["--root", str(tmp_path), "--type", "parche", "--skills", "demo-skill", "--dry-run"])
    assert rc == 0
    assert bump.read_skill_version(skill) == "0.1.0"


def test_main_unknown_skill_tmp_root(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    rc = bump.main(["--root", str(tmp_path), "--type", "minor", "--skills", "no-existe"])
    assert rc == 1


def test_bump_cli_help() -> None:
    r = subprocess.run(["python3", str(BUMP), "--help"], capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert "--type" in r.stdout
