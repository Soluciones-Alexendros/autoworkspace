#!/usr/bin/env python3
"""Tests hardening para postura_seguridad.sh (solo lectura, sin cambios)."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

SH = Path(__file__).resolve().parent / "postura_seguridad.sh"


def run(*args):
    return subprocess.run(
        ["bash", str(SH), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


class PosturaCli(unittest.TestCase):
    def test_help_exit_0(self):
        p = run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Uso:", p.stdout)

    def test_help_corto_exit_0(self):
        p = run("-h")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Uso:", p.stdout)

    def test_args_invalidos_exit_2(self):
        p = run("--opcion-inexistente")
        self.assertEqual(p.returncode, 2)

    def test_posicional_invalido_exit_2(self):
        p = run("extra")
        self.assertEqual(p.returncode, 2)

    def test_ejecucion_normal_exit_0_formato(self):
        p = run()
        self.assertEqual(p.returncode, 0)
        # Formato "CLAVE: valor" en cada línea no vacía
        lines = [l for l in p.stdout.splitlines() if l.strip()]
        self.assertTrue(lines, "se esperaba al menos una línea CLAVE: valor")
        for line in lines:
            self.assertIn(": ", line)


if __name__ == "__main__":
    unittest.main()
