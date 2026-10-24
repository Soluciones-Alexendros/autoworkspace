#!/usr/bin/env python3
"""Tests de biblioteca estándar para scan_repo.py."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import scan_repo  # noqa: E402


def _write(root: Path, rel: str, content: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class ScanRepoTests(unittest.TestCase):
    def test_ratio_ignora_package_json_como_codigo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "package.json", '{"name":"x","dependencies":{"a":"1.0.0"}}')
            _write(root, "src/app.py", "print(1)\n")
            _write(root, "tests/test_app.py", "def test_ok():\n    assert True\n")
            rep = scan_repo.scan(str(root))
            self.assertEqual(rep["tests"]["ficheros_codigo"], 1)
            self.assertEqual(rep["tests"]["ficheros_test"], 1)

    def test_src_integration_no_es_suite_de_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "src/integration/client.py", "def connect():\n    pass\n")
            _write(root, "src/testing/helpers.py", "def helper():\n    pass\n")
            rep = scan_repo.scan(str(root))
            self.assertEqual(rep["tests"]["ficheros_test"], 0)
            self.assertEqual(rep["tests"]["ficheros_codigo"], 2)

    def test_app_tsx_no_es_nombre_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "src/App.tsx", "export default function App() { return null }\n")
            _write(root, "src/Main.java", "class Main {}\n")
            _write(root, "src/Bad Name.py", "pass\n")
            rep = scan_repo.scan(str(root))
            mayus = rep["nombrado"].get("con_mayusculas", [])
            self.assertFalse(any(p.endswith("App.tsx") for p in mayus))
            self.assertFalse(any(p.endswith("Main.java") for p in mayus))
            espacios = rep["nombrado"].get("con_espacios", [])
            self.assertTrue(any("Bad Name.py" in p for p in espacios))

    def test_requirements_con_rango_no_es_sin_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root,
                "requirements.txt",
                "requests>=2.28\nflask==2.0.0\norphan\n",
            )
            rep = scan_repo.scan(str(root))
            joined = "\n".join(rep["salud_dependencias"])
            self.assertNotIn("requests", joined)
            self.assertNotIn("flask", joined)
            self.assertIn("orphan", joined)

    def test_env_versionado_y_example_excluido(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, ".env", "KEY=short\n")
            _write(root, ".env.local", "KEY=x\n")
            _write(root, ".env.example", "KEY=\n")
            _write(root, ".env.sample", "KEY=\n")
            rep = scan_repo.scan(str(root))
            envs = set(rep["env_versionados"])
            self.assertIn(".env", envs)
            self.assertIn(".env.local", envs)
            self.assertNotIn(".env.example", envs)
            self.assertNotIn(".env.sample", envs)

    def test_secreto_en_docs_confianza_baja_sin_valor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root,
                "docs/ejemplo.md",
                'password = "supersecreto123"\n',
            )
            _write(
                root,
                "src/config.py",
                'password = "supersecreto123"\n',
            )
            rep = scan_repo.scan(str(root))
            hallazgos = rep["hallazgos_patrones"]
            self.assertTrue(hallazgos)
            self.assertEqual(hallazgos, rep["secretos_potenciales"])
            self.assertEqual(
                rep["resumen"]["n_hallazgos_patrones"],
                rep["resumen"]["n_secretos_potenciales"],
            )
            self.assertEqual(
                rep["resumen"]["n_hallazgos_alta"],
                rep["resumen"]["n_secretos_alta_confianza"],
            )
            dumped = json.dumps(rep)
            self.assertNotIn("supersecreto123", dumped)
            md = scan_repo.to_markdown(rep)
            self.assertNotIn("supersecreto123", md)
            by_file = {s["fichero"]: s for s in hallazgos}
            self.assertEqual(by_file["docs/ejemplo.md"]["confianza"], "baja")
            self.assertEqual(by_file["src/config.py"]["confianza"], "alta")
            for s in hallazgos:
                self.assertNotIn("valor", s)
                self.assertNotIn("value", s)
                self.assertNotIn("snippet", s)
                self.assertIn("fingerprint", s)
                self.assertEqual(len(s["fingerprint"]), 16)

    def test_directorios_test_guardan_ruta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "pkg/tests/test_a.py", "def test_a():\n    assert True\n")
            rep = scan_repo.scan(str(root))
            self.assertIn("pkg/tests", rep["tests"]["directorios_test"])

    def test_package_json_latest_y_lock_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root,
                "package.json",
                json.dumps({"dependencies": {"lodash": "latest", "ok": "^1.0.0"}}),
            )
            rep = scan_repo.scan(str(root))
            joined = "\n".join(rep["salud_dependencias"])
            self.assertIn("lodash", joined)
            self.assertIn("sin fichero lock", joined)
            self.assertNotIn("'ok'", joined)


class PureFunctionGoldens(unittest.TestCase):
    def test_version_is_unpinned_dorado(self):
        self.assertTrue(scan_repo.version_is_unpinned(""))
        self.assertTrue(scan_repo.version_is_unpinned("*"))
        self.assertTrue(scan_repo.version_is_unpinned("latest"))
        self.assertTrue(scan_repo.version_is_unpinned("https://example.com/a.tgz"))
        self.assertTrue(scan_repo.version_is_unpinned("git+https://example.com/a"))
        self.assertFalse(scan_repo.version_is_unpinned("^1.0.0"))
        self.assertFalse(scan_repo.version_is_unpinned("1.2.3"))

    def test_pip_line_unpinned_dorado(self):
        self.assertFalse(scan_repo.pip_line_unpinned(""))
        self.assertFalse(scan_repo.pip_line_unpinned("# comentario"))
        self.assertFalse(scan_repo.pip_line_unpinned("-r other.txt"))
        self.assertFalse(scan_repo.pip_line_unpinned("requests>=2.28"))
        self.assertFalse(scan_repo.pip_line_unpinned("flask==2.0.0"))
        self.assertTrue(scan_repo.pip_line_unpinned("orphan"))
        self.assertTrue(scan_repo.pip_line_unpinned("django"))

    def test_is_env_file_dorado(self):
        self.assertTrue(scan_repo.is_env_file(".env"))
        self.assertTrue(scan_repo.is_env_file(".env.local"))
        self.assertFalse(scan_repo.is_env_file(".env.example"))
        self.assertFalse(scan_repo.is_env_file(".env.sample"))
        self.assertFalse(scan_repo.is_env_file(".env.template"))
        self.assertFalse(scan_repo.is_env_file("app.py"))

    def test_naming_is_suspicious_dorado(self):
        self.assertEqual(scan_repo.naming_is_suspicious("Bad Name.py", ".py"), "con_espacios")
        self.assertIsNone(scan_repo.naming_is_suspicious("README.md", ".md"))
        self.assertIsNone(scan_repo.naming_is_suspicious("Makefile", ""))
        self.assertIsNone(scan_repo.naming_is_suspicious("App.tsx", ".tsx"))
        self.assertEqual(scan_repo.naming_is_suspicious("MiModulo.py", ".py"), "con_mayusculas")
        self.assertIsNone(scan_repo.naming_is_suspicious("modulo.py", ".py"))

    def test_is_dedicated_test_path_dorado(self):
        self.assertTrue(scan_repo.is_dedicated_test_path("tests/test_a.py", "test_a.py"))
        self.assertTrue(scan_repo.is_dedicated_test_path("src/test_app.py", "test_app.py"))
        self.assertTrue(scan_repo.is_dedicated_test_path("pkg/tests/helpers.py", "helpers.py"))
        self.assertFalse(scan_repo.is_dedicated_test_path("src/integration/client.py", "client.py"))
        self.assertFalse(scan_repo.is_dedicated_test_path("src/testing/helpers.py", "helpers.py"))
        self.assertFalse(scan_repo.is_dedicated_test_path("src/app.py", "app.py"))

    def test_path_confidence_dorado(self):
        self.assertEqual(scan_repo.path_confidence("scripts/scan_repo.py"), "omitido")
        self.assertEqual(scan_repo.path_confidence("docs/ejemplo.md"), "baja")
        self.assertEqual(scan_repo.path_confidence("tests/test_a.py"), "baja")
        self.assertEqual(scan_repo.path_confidence("src/app.py"), "alta")

    def test_should_ignore_dirname_dorado(self):
        self.assertTrue(scan_repo.should_ignore_dirname(".git"))
        self.assertTrue(scan_repo.should_ignore_dirname("node_modules"))
        self.assertTrue(scan_repo.should_ignore_dirname("pkg.egg-info"))
        self.assertFalse(scan_repo.should_ignore_dirname("src"))

    def test_to_markdown_contiene_secciones(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "src/app.py", "print(1)\n")
            rep = scan_repo.scan(str(root))
            md = scan_repo.to_markdown(rep)
            self.assertIn("# Escaneo estructural del repositorio", md)
            self.assertIn("## Lenguajes", md)
            self.assertIn("## Ficheros estándar", md)
            self.assertIn("## Alertas", md)

    def test_duplicados_exactos_por_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", "mismo contenido\n")
            _write(root, "b.txt", "mismo contenido\n")
            rep = scan_repo.scan(str(root))
            self.assertEqual(len(rep["duplicados"]), 1)
            self.assertEqual(len(rep["duplicados"][0]["ficheros"]), 2)


class ScanRepoCliHardening(unittest.TestCase):
    def test_help_exit_0(self):
        with self.assertRaises(SystemExit) as cm:
            scan_repo.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_args_invalidos_exit_2(self):
        with self.assertRaises(SystemExit) as cm:
            scan_repo.main(["--opcion-inexistente"])
        self.assertEqual(cm.exception.code, 2)

    def test_repo_inexistente_exit_1(self):
        rc = scan_repo.main([os.path.join(tempfile.gettempdir(), "scan_repo_no_existe_xyz")])
        self.assertEqual(rc, 1)

    def test_repo_valido_exit_0_con_json_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "src/app.py", "print(1)\n")
            out_json = str(root / "out.json")
            out_md = str(root / "out.md")
            # salidas fuera del repo auditado para no contaminar
            with tempfile.TemporaryDirectory() as out:
                oj = os.path.join(out, "r.json")
                om = os.path.join(out, "r.md")
                rc = scan_repo.main([str(root), "--json", oj, "--md", om])
                self.assertEqual(rc, 0)
                self.assertTrue(os.path.isfile(oj))
                self.assertTrue(os.path.isfile(om))
            _ = (out_json, out_md)


class CheckProductStructureCli(unittest.TestCase):
    SH = str(SCRIPTS / "check-product-structure.sh")

    def _run(self, *args):
        import subprocess
        return subprocess.run(
            ["bash", self.SH, *args],
            capture_output=True, text=True, timeout=30,
        )

    def test_help_exit_0(self):
        p = self._run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("Uso:", p.stdout)

    def test_args_invalidos_exit_2(self):
        p = self._run("--opcion-inexistente")
        self.assertEqual(p.returncode, 2)

    def test_perfil_invalido_exit_2(self):
        p = self._run(".", "--profile", "P9")
        self.assertEqual(p.returncode, 2)

    def test_repo_inexistente_exit_2(self):
        p = self._run(os.path.join(tempfile.gettempdir(), "check_ps_no_existe_xyz"))
        self.assertEqual(p.returncode, 2)

    def test_repo_vacio_fallo_controlado_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._run(tmp)
            self.assertEqual(p.returncode, 1)
            self.assertIn("FALLO", p.stdout)


if __name__ == "__main__":
    unittest.main()
