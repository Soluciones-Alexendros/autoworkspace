"""Integration tests for deterministic skill routing."""

import importlib.util
from pathlib import Path

import pytest

ROUTE = Path(__file__).resolve().parents[1] / "route.py"


def load():
    spec = importlib.util.spec_from_file_location("skill_route", ROUTE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("audita la salud del sistema", "local-maintenance"),
        ("configura husky y pre-commit", "project-publish"),
        ("define la cobertura de tests con TDD", "plan-validators"),
        ("implementa una API backend con background jobs", "role-back"),
        ("implementa una ruta cliente con un formulario frontend", "role-front"),
        ("define tokens y dirección visual", "role-design"),
    ],
)
def test_prompt_routes_to_expected_skill(prompt, expected):
    router = load()
    ranked = router.route(prompt, top=1)
    assert ranked[0][1]["name"] == expected
