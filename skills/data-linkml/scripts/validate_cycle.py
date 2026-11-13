#!/usr/bin/env python3
"""Ciclo de validación por capas para una skill data-linkml.

Capas 1–4 (sintaxis YAML → metamodelo → lint → instancia) con veredictos
esperados para casos positivos y negativos. Registra herramienta, versión,
comando, código de salida y resultado. Las capas 5–7 (conjunto/dominio,
artefacto, evidencia) quedan fuera: las cubren comprobadores propios del
proyecto (ver references/validation.md).

Convención de veredicto esperado por fichero de datos: si el nombre contiene
"invalid", se espera RECHAZO; en caso contrario, ACEPTACIÓN.

Exit codes canónicos: 0 OK, 1 error/veredicto negativo, 2 input inválido,
3 dependencia ausente, 4 permiso.

Uso:
  python3 validate_cycle.py --schema S.yaml --target-class C \
      --data a.yaml b-invalid.yaml [--linkml BIN] [--venv-dir DIR] [--json]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INPUT = 2
EXIT_MISSING = 3
EXIT_PERM = 4

try:
    import yaml

    HAS_YAML = True
except ImportError:  # pragma: no cover
    HAS_YAML = False


class LayerDict(TypedDict):
    layer: int
    name: str
    status: str
    detail: str
    command: str | None
    exit_code: int | None
    expected: str | None
    actual: str | None
    file: str | None


class ReportDict(TypedDict):
    tool: str
    version: str
    binary: str
    schema: str
    target_class: str
    layers: list[LayerDict]
    verdict: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Layered LinkML validation cycle (data-linkml skill).")
    parser.add_argument("--schema", required=True, help="LinkML schema YAML file")
    parser.add_argument("--target-class", required=True, help="target class for instance validation")
    parser.add_argument("--data", nargs="+", required=True, help="instance data files")
    parser.add_argument("--linkml", help="linkml executable (overrides discovery)")
    parser.add_argument("--venv-dir", help="virtualenv directory (bin/linkml inside)")
    parser.add_argument("--json", action="store_true", help="JSON output instead of Markdown")
    return parser.parse_args()


def find_linkml(args: argparse.Namespace) -> str | None:
    if args.linkml:
        path = Path(args.linkml)
        return str(path) if path.exists() else None
    if args.venv_dir:
        cand = Path(args.venv_dir) / "bin" / "linkml"
        if cand.exists():
            return str(cand)
    return shutil.which("linkml")


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def expected_verdict(filename: str) -> str:
    return "REJECT" if "invalid" in Path(filename).name.lower() else "ACCEPT"


def main() -> int:
    args = parse_args()
    schema = Path(args.schema)
    if not schema.is_file():
        print(f"ERROR: schema no encontrado: {schema}", file=sys.stderr)
        return EXIT_INPUT
    for data in args.data:
        if not Path(data).is_file():
            print(f"ERROR: fichero de datos no encontrado: {data}", file=sys.stderr)
            return EXIT_INPUT

    binpath = find_linkml(args)
    if not binpath:
        print(
            "ERROR: linkml CLI no encontrado. Instala con scripts/bootstrap_arch.sh o apunta --linkml/--venv-dir.",
            file=sys.stderr,
        )
        return EXIT_MISSING

    version = "unknown"
    rc, out, err = run([binpath, "--version"])
    if rc == 0:
        version = out or "unknown"

    report: ReportDict = {
        "tool": "linkml",
        "version": version,
        "binary": binpath,
        "schema": str(schema),
        "target_class": args.target_class,
        "layers": [],
        "verdict": "FAIL",
    }

    # Capa 1: sintaxis YAML (solo si PyYAML está disponible).
    if not HAS_YAML:
        report["layers"].append(
            {
                "layer": 1,
                "name": "yaml_syntax",
                "status": "not_run",
                "detail": "PyYAML no disponible; la sintaxis la cubrirá la capa 2",
                "command": None,
                "exit_code": None,
                "expected": None,
                "actual": None,
                "file": None,
            }
        )
    else:
        try:
            with open(schema, encoding="utf-8") as fh:
                yaml.safe_load(fh)
            for data in args.data:
                with open(data, encoding="utf-8") as fh:
                    yaml.safe_load(fh)
            report["layers"].append(
                {
                    "layer": 1,
                    "name": "yaml_syntax",
                    "status": "pass",
                    "detail": "YAML bien formado",
                    "command": None,
                    "exit_code": None,
                    "expected": None,
                    "actual": None,
                    "file": None,
                }
            )
        except yaml.YAMLError as exc:
            report["layers"].append(
                {
                    "layer": 1,
                    "name": "yaml_syntax",
                    "status": "fail",
                    "detail": str(exc),
                    "command": None,
                    "exit_code": None,
                    "expected": None,
                    "actual": None,
                    "file": None,
                }
            )

    # Capa 2: metamodelo.
    cmd = [binpath, "validate", str(schema)]
    rc, out, err = run(cmd)
    report["layers"].append(
        {
            "layer": 2,
            "name": "metamodel",
            "status": "pass" if rc == 0 else "fail",
            "command": " ".join(cmd),
            "exit_code": rc,
            "detail": (out or err)[:400],
            "expected": None,
            "actual": None,
            "file": None,
        }
    )

    # Capa 3: lint.
    cmd = [binpath, "lint", str(schema)]
    rc, out, err = run(cmd)
    report["layers"].append(
        {
            "layer": 3,
            "name": "lint",
            "status": "pass" if rc == 0 else "fail",
            "command": " ".join(cmd),
            "exit_code": rc,
            "detail": (out or err)[:400],
            "expected": None,
            "actual": None,
            "file": None,
        }
    )

    # Capa 4: instancias, positivo y negativo.
    for data in args.data:
        cmd = [binpath, "validate", "-s", str(schema), "-C", args.target_class, data]
        rc, out, err = run(cmd)
        actual = "ACCEPT" if rc == 0 else "REJECT"
        wanted = expected_verdict(data)
        ok = actual == wanted
        report["layers"].append(
            {
                "layer": 4,
                "name": "instance",
                "file": data,
                "expected": wanted,
                "actual": actual,
                "status": "pass" if ok else "fail",
                "command": " ".join(cmd),
                "exit_code": rc,
                "detail": (out or err)[:400],
            }
        )

    layers = report["layers"]
    blocking = [l for l in layers if l.get("status") in {"fail", "not_run"} and l.get("layer") in {1, 2, 3, 4}]
    report["verdict"] = "PASS" if not blocking else "FAIL"

    _emit(args, report)
    return EXIT_OK if report["verdict"] == "PASS" else EXIT_ERROR


def _emit(args: argparse.Namespace, report: ReportDict) -> None:
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print("# LinkML validation cycle")
    print(f"- tool: {report['tool']} {report['version']} ({report['binary']})")
    print(f"- schema: {report['schema']} (target class {report['target_class']})")
    for layer in report["layers"]:
        mark = "OK " if layer.get("status") == "pass" else ("N/R" if layer.get("status") == "not_run" else "FAIL")
        extra = f" [{layer.get('expected')}→{layer.get('actual')}]" if layer.get("expected") else ""
        print(f"- [{mark}] L{layer['layer']} {layer['name']}{extra}: {layer.get('detail', '')}")
    print(f"Verdict: {report['verdict']}")


if __name__ == "__main__":
    sys.exit(main())
