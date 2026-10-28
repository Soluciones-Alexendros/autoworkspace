"""CLI: --help exit 0 y args inválidos exit 2 en los 4 scripts (sin red)."""

from typing import Any

import audit_page
import contrast
import pytest
import report as report_mod
import score as score_mod

EXIT_USAGE = 2


@pytest.mark.parametrize(
    "mod,args",
    [
        (audit_page, ["--help"]),
        (contrast, ["--help"]),
        (score_mod, ["--help"]),
        (report_mod, ["--help"]),
    ],
)
def test_help_exit_0(mod: Any, args: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        mod.main(args)
    assert e.value.code == 0


def test_audit_sin_args_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        audit_page.main([])
    assert e.value.code == EXIT_USAGE


def test_contrast_sin_args_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        contrast.main([])
    assert e.value.code == EXIT_USAGE


def test_score_sin_args_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        score_mod.main([])
    assert e.value.code == EXIT_USAGE


def test_report_sin_args_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as e:
        report_mod.main([])
    assert e.value.code == EXIT_USAGE


def test_contrast_color_invalido_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert contrast.main(["#zzz", "#fff"]) == EXIT_USAGE
    assert contrast.main(["#000", "#fff"]) == 0


def test_contrast_fail_exit_1(capsys: pytest.CaptureFixture[str]) -> None:
    assert contrast.main(["#777777", "#FFFFFF"]) == 1


def test_audit_fichero_inexistente_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit_page.main(["--file", "/no/existe-xyz.html"]) == EXIT_USAGE


def test_score_fichero_inexistente_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert score_mod.main(["/no/existe-xyz.json"]) == EXIT_USAGE


def test_report_fichero_inexistente_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert report_mod.main(["/no/existe-xyz.json"]) == EXIT_USAGE
