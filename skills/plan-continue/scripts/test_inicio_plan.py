#!/usr/bin/env python3
"""Tests de biblioteca estándar para inicio_plan.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import inicio_plan  # noqa: E402


def _write(root: Path, rel: str, content: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _git_init(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.test"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)


class InicioPlanTests(unittest.TestCase):
    def test_help_exit_0(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            inicio_plan.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_ruta_inexistente_exit_2(self) -> None:
        rc = inicio_plan.main(["/no/existe/este/repo"])
        self.assertEqual(rc, 2)

    def test_tablero_en_repo_minimo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            out = Path(tmp) / "out"
            root.mkdir()
            _write(root, "README.md", "# demo\n")
            _write(root, "src/app.py", "print(1)\n")
            _write(root, "CHANGELOG.md", "## [Unreleased]\n\n- Una cosa\n")
            _git_init(root)
            rc = inicio_plan.main([str(root), "--profile", "P1", "--out", str(out)])
            self.assertIn(rc, (0, 1))
            self.assertTrue((out / "inicio.json").is_file())
            self.assertTrue((out / "ESTADO.md").is_file())
            self.assertTrue((out / "ESTADO.html").is_file())
            data = json.loads((out / "inicio.json").read_text(encoding="utf-8"))
            self.assertEqual(data["git"]["es_git"], True)
            self.assertIn("Una cosa", data["roadmap"]["unreleased"])
            md = (out / "ESTADO.md").read_text(encoding="utf-8")
            self.assertIn("Estado del repo", md)
            self.assertIn("Camino del producto", md)
            self.assertIn("Errores y fallos", md)
            html = (out / "ESTADO.html").read_text(encoding="utf-8")
            self.assertIn('lang="es"', html)
            self.assertIn("**Semáforo**", md)
            self.assertIn(data["semaforo"], ("verde", "amarillo", "rojo"))

    def test_html_escapa_contenido(self) -> None:
        rep = {
            "repo": "/tmp/x",
            "nombre": "a<b>",
            "generated_at": "2026-01-01T00:00:00Z",
            "profile": "P1",
            "semaforo": "verde",
            "git": {
                "es_git": True,
                "rama": "main",
                "sha": "abc",
                "sucio": False,
                "adelante": 0,
                "atras": 0,
                "upstream": None,
            },
            "estructura": {"ok": True},
            "github": {"disponible": False, "issues_abiertos": [], "prs_abiertos": []},
            "roadmap": {"titulos": ["<script>"], "unreleased": [], "fichero": None, "planes_locales": []},
            "fallos": [],
            "scan": {"resumen": {}},
        }
        html = inicio_plan.to_html(rep)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("a&lt;b&gt;", html)


if __name__ == "__main__":
    os.chdir(str(SCRIPTS))
    unittest.main()
