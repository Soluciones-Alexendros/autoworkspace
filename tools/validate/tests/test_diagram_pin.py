"""El renderer de diagramas tiene un solo pin: catálogo y job de CI (P12 T5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]
CATALOG = REPO / "docs" / "architecture" / "diagrams" / "catalog.json"
CI = REPO / ".github" / "workflows" / "ci.yml"
SHA_LEN = 40


def _catalog_renderer() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(CATALOG.read_text(encoding="utf-8"))
    return cast("dict[str, Any]", data["renderer"])


def _workflow() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load(CI.read_text(encoding="utf-8"))
    return data


def _diagram_steps() -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = _workflow()["jobs"]["diagrams"]["steps"]
    return [step for step in steps if step.get("uses", "").startswith("actions/checkout")]


def test_renderer_repo_is_pinned() -> None:
    renderer = _catalog_renderer()
    assert renderer["repo"] == "tt-a1i/archify"
    assert len(renderer["sha"]) == SHA_LEN
    assert all(char in "0123456789abcdef" for char in renderer["sha"])


@pytest.mark.parametrize("index", [0, 1])
def test_checkout_steps_pin_a_full_sha(index: int) -> None:
    uses = _diagram_steps()[index]["uses"]
    ref = uses.split("@", 1)[1].split()[0]
    assert len(ref) == SHA_LEN, f"la acción debe ir por SHA completo: {uses}"


def test_archify_checkout_matches_catalog_sha() -> None:
    renderer = _catalog_renderer()
    archify_step = _diagram_steps()[1]
    assert archify_step["with"]["repository"] == renderer["repo"]
    assert archify_step["with"]["ref"] == renderer["sha"], (
        "el ref de Archify en ci.yml debe coincidir con catalog.json.renderer.sha"
    )


def test_diagrams_job_feeds_ci_gate() -> None:
    needs = _workflow()["jobs"]["ci-gate"]["needs"]
    assert "diagrams" in needs


def test_every_catalog_entry_has_a_source() -> None:
    diagrams = json.loads(CATALOG.read_text(encoding="utf-8"))["diagrams"]
    assert [entry["id"] for entry in diagrams] == ["D01", "D02", "D03", "D04"]
    for entry in diagrams:
        assert (REPO / entry["source"]).is_file(), entry["source"]
        assert entry["adr"].startswith("ADR-")
