"""CLI: --help exit 0 y args inválidos exit 2 en los 4 scripts (sin red)."""

import audit_page
import contrast
import pytest
import report as report_mod
import score as score_mod


@pytest.mark.parametrize(
    "mod,args",
    [
        (audit_page, ["--help"]),
        (contrast, ["--help"]),
        (score_mod, ["--help"]),
        (report_mod, ["--help"]),
    ],
)
def test_help_exit_0(mod, args, capsys):
    with pytest.raises(SystemExit) as e:
        mod.main(args)
    assert e.value.code == 0


def test_audit_sin_args_exit_2(capsys):
    with pytest.raises(SystemExit) as e:
        audit_page.main([])
    assert e.value.code == 2


def test_contrast_sin_args_exit_2(capsys):
    with pytest.raises(SystemExit) as e:
        contrast.main([])
    assert e.value.code == 2


def test_score_sin_args_exit_2(capsys):
    with pytest.raises(SystemExit) as e:
        score_mod.main([])
    assert e.value.code == 2


def test_report_sin_args_exit_2(capsys):
    with pytest.raises(SystemExit) as e:
        report_mod.main([])
    assert e.value.code == 2


def test_contrast_color_invalido_exit_2(capsys):
    assert contrast.main(["#zzz", "#fff"]) == 2
    assert contrast.main(["#000", "#fff"]) == 0


def test_contrast_fail_exit_1(capsys):
    assert contrast.main(["#777777", "#FFFFFF"]) == 1


def test_audit_fichero_inexistente_exit_2(capsys):
    assert audit_page.main(["--file", "/no/existe-xyz.html"]) == 2


def test_score_fichero_inexistente_exit_2(capsys):
    assert score_mod.main(["/no/existe-xyz.json"]) == 2


def test_report_fichero_inexistente_exit_2(capsys):
    assert report_mod.main(["/no/existe-xyz.json"]) == 2
