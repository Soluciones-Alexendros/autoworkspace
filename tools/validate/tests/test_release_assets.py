"""Release assets must be uploaded with checksum and provenance evidence."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from validate.release_coherence import release_asset_errors  # noqa: E402


def test_release_workflow_uploads_attested_archive_and_checksums() -> None:
    assert release_asset_errors(ROOT) == []


def test_missing_upload_or_wrong_order_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["provenance"]["steps"]
    data["jobs"]["provenance"]["steps"] = [
        step for step in steps if "gh release upload" not in str(step.get("run", ""))
    ]
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(yaml.safe_dump(data, sort_keys=False))
    assert any("upload" in error for error in release_asset_errors(tmp_path))


def test_archive_and_checksum_fixture_round_trip(tmp_path: Path) -> None:
    archive = tmp_path / "autoworkspace-fixture.tar.gz"
    subprocess.run(
        ["git", "archive", "--format=tar.gz", "--prefix=autoworkspace-fixture/", "-o", str(archive), "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    checksum = subprocess.run(
        ["sha256sum", archive.name], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout
    (tmp_path / "SHA256SUMS").write_text(checksum, encoding="utf-8")
    subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=tmp_path, check=True, capture_output=True)


def test_historical_vmain_version_fallback_is_rejected(tmp_path: Path) -> None:
    """v7.1.0 failed when upload resolved VERSION from branch name (vmain)."""
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    for step in data["jobs"]["provenance"]["steps"]:
        run = str(step.get("run", ""))
        if "gh release upload" in run:
            step["run"] = run.replace(
                'gh release upload "v${VERSION}"',
                'VERSION="${VERSION:-${GITHUB_REF_NAME#v}}"\ngh release upload "v${VERSION}"',
                1,
            )
            break
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(yaml.safe_dump(data, sort_keys=False))
    errors = release_asset_errors(tmp_path)
    assert any("GITHUB_REF_NAME" in error for error in errors), errors


def test_missing_post_release_smoke_is_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"))
    del data["jobs"]["post-release-smoke"]
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(yaml.safe_dump(data, sort_keys=False))
    errors = release_asset_errors(tmp_path)
    assert any("post-release-smoke" in error for error in errors), errors
