#!/usr/bin/env python3
"""Pre-flight del entorno LinkML: Python y CLI presentes, versión, informe.

Exit codes canónicos: 0 OK, 1 error/veredicto negativo, 2 input inválido,
3 dependencia ausente, 4 permiso.

Uso:
  python3 linkml_env.py [--venv-dir DIR] [--json] [--linkml BIN]
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
MIN_PYTHON = (3, 10)


class CheckDict(TypedDict):
    id: str
    ok: bool
    detail: str


class ReportDict(TypedDict):
    checks: list[CheckDict]
    verdict: str
    detail: str | None
    environment: dict[str, str] | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-flight LinkML environment check (data-linkml skill)."
    )
    parser.add_argument("--venv-dir", help="virtualenv directory (bin/linkml inside)")
    parser.add_argument("--linkml", help="linkml executable to check (overrides discovery)")
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


def main() -> int:
    args = parse_args()
    report: ReportDict = {"checks": [], "verdict": "FAIL", "detail": None, "environment": None}

    py_ok = sys.version_info >= MIN_PYTHON
    report["checks"].append(
        {
            "id": "python",
            "ok": py_ok,
            "detail": f"python {sys.version.split()[0]} (>= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
        }
    )

    binpath = find_linkml(args)
    if not binpath:
        report["checks"].append(
            {
                "id": "linkml_cli",
                "ok": False,
                "detail": (
                    "linkml CLI no encontrado: usa scripts/bootstrap_arch.sh "
                    "(Arch) o instala en un venv con el pin de assets/"
                    "requirements-linkml.txt"
                ),
            }
        )
        report["detail"] = "missing dependency: linkml CLI"
        _emit(args, report)
        return EXIT_MISSING

    version = "unknown"
    ver_ok = False
    rc, out, err = run([binpath, "--version"])
    if rc == 0:
        version = out or "unknown"
        ver_ok = True
    report["checks"].append(
        {
            "id": "linkml_cli",
            "ok": ver_ok,
            "detail": f"{binpath} --version -> {version or err}",
        }
    )

    if not py_ok or not ver_ok:
        report["detail"] = "pre-flight failed"
        _emit(args, report)
        return EXIT_ERROR

    report["verdict"] = "PASS"
    report["environment"] = {"python": sys.version.split()[0], "linkml": version, "binary": binpath}
    _emit(args, report)
    return EXIT_OK


def _emit(args: argparse.Namespace, report: ReportDict) -> None:
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print("# LinkML environment pre-flight")
    for check in report["checks"]:
        mark = "OK " if check["ok"] else "FAIL"
        print(f"- [{mark}] {check['id']}: {check['detail']}")
    env = report.get("environment")
    if env:
        print(f"- [OK ] environment: {env}")
    print(f"Verdict: {report['verdict']}")


if __name__ == "__main__":
    sys.exit(main())