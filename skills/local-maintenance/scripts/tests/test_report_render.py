"""Tests report_render.py: --help, inválidos, input ausente -> 1, doradas."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import report_render

EXIT_USAGE = 2

SCRIPT = "report_render.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=".",
    )


def _sample() -> dict[str, Any]:
    return {
        "metadata": {
            "timestamp": "t",
            "hostname": "h",
            "mode": "audit-quick",
            "distro": "d",
            "family": "f",
            "kernel": "k",
            "duration_seconds": 1,
        },
        "health_score": {"overall": 80, "security": 80, "updates": 80, "hygiene": 80, "resources": 80},
        "findings": [
            {
                "id": "X-01",
                "category": "security",
                "severity": "P0",
                "title": "T",
                "description": "D",
                "control": "C",
                "status": "FAIL",
                "evidence": "E",
                "remediation": "R",
                "risk_level": "R2",
            }
        ],
        "summary": {
            "total_checks": 1,
            "passed": 0,
            "failed": 1,
            "warned": 0,
            "skipped": 0,
            "errors": 0,
            "by_severity": {"P0": 1, "P1": 0, "P2": 0, "P3": 0, "P4": 0},
        },
    }


def test_help_exit0() -> None:
    r = _run("--help")
    assert r.returncode == 0


def test_invalid_args_exit2() -> None:
    r = _run("--opcion-invalida-xyz")
    assert r.returncode == EXIT_USAGE
    r2 = _run("--format", "xml", "--input", "x.json")
    assert r2.returncode == EXIT_USAGE


def test_error_input_ausente_exit1(tmp_path: Path) -> None:
    missing = tmp_path / "noexiste.json"
    assert report_render.main(["--input", str(missing), "--output", str(tmp_path / "o.md")]) == 1
    r = _run("--input", str(missing), "--output", str(tmp_path / "o2.md"))
    assert r.returncode == 1


def test_error_input_corrupto_exit1(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert report_render.main(["--input", str(bad), "--output", str(tmp_path / "o.md")]) == 1


def test_calculate_trend_golden() -> None:
    assert report_render.calculate_trend(80, None) == "first_run"
    assert report_render.calculate_trend(90, 80) == "improving"
    assert report_render.calculate_trend(60, 80) == "degrading"
    assert report_render.calculate_trend(82, 80) == "stable"


def test_severity_helpers_golden() -> None:
    assert report_render.severity_emoji("P0") == "🔴"
    assert report_render.severity_color("P1") == "#fd7e14"
    assert report_render.severity_emoji("PX") != ""


def test_render_markdown_golden(tmp_path: Path) -> None:
    data = _sample()
    md = report_render.render_markdown(data)
    assert "# Informe" in md and "Health Score" in md and "X-01" in md


def test_render_md_file_golden(tmp_path: Path) -> None:
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(_sample()), encoding="utf-8")
    out = tmp_path / "rep.md"
    assert report_render.main(["--input", str(inp), "--output", str(out)]) == 0
    assert "Health Score" in out.read_text(encoding="utf-8")


def test_render_html_file_golden(tmp_path: Path) -> None:
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(_sample()), encoding="utf-8")
    out = tmp_path / "rep.html"
    assert report_render.main(["--input", str(inp), "--output", str(out), "--format", "html"]) == 0
    assert "<html" in out.read_text(encoding="utf-8")
