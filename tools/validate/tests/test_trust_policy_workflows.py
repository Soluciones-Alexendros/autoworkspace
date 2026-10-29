"""G14-G17: política de confianza en workflows (estática, sin secreto real)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
CI = ROOT / ".github" / "workflows" / "ci.yml"
QUALITY = ROOT / ".github" / "workflows" / "quality.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_g14_pr_hygiene_job_has_no_secret_env() -> None:
    data = _load(CI)
    hygiene = data["jobs"]["hygiene"]
    for step in hygiene["steps"]:
        env = step.get("env") or {}
        assert "HYGIENE_DENYLIST" not in env
        assert "secrets.HYGIENE_DENYLIST" not in yaml.dump(step)


def test_g14_quality_pr_path_has_no_inline_pattern_print() -> None:
    text = QUALITY.read_text(encoding="utf-8")
    assert "git grep -nEe" not in text
    assert "exit 0" not in text or "PRIVATE_CHECK_NOT_APPLICABLE_TO_PR" in text


def test_g15_private_job_only_on_main_push() -> None:
    data = _load(CI)
    job = data["jobs"]["private-denylist"]
    assert "push" in job["if"]
    assert "refs/heads/main" in job["if"]


def test_g16_private_job_invokes_cli_not_git_grep() -> None:
    data = _load(CI)
    steps = data["jobs"]["private-denylist"]["steps"]
    runs = [s.get("run", "") for s in steps if isinstance(s, dict)]
    assert any("private_denylist.py" in r for r in runs)
    assert not any("git grep" in r for r in runs)


def test_g17_release_requires_private_before_cut() -> None:
    data = _load(RELEASE)
    steps = data["jobs"]["publish"]["steps"]
    names = [s.get("name", "") for s in steps if isinstance(s, dict)]
    priv = names.index("Private denylist required before publish")
    cut = names.index("Cut annotated tag on main")
    assert priv < cut
