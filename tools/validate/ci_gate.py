#!/usr/bin/env python3
"""Agregador ci-gate: evalúa needs JSON + hold + skips permitidos.

Entrada por entorno:
  NEEDS_JSON   — toJSON(needs)
  ALLOWED_SKIPS — nombres de jobs separados por espacio cuyo skip es esperado
  HOLD         — "true" para veto por etiqueta hold

Exit 0 solo si todos los jobs requeridos están en success.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def evaluate(needs: dict[str, Any], allowed_skips: set[str], hold: bool) -> tuple[int, str]:
    if hold:
        return 1, "ci-gate: hold activo"
    bad: list[str] = []
    for name, info in needs.items():
        if not isinstance(info, dict):
            bad.append(f"{name}=unknown")
            continue
        result = info.get("result")
        if result == "success":
            continue
        if result == "skipped" and name in allowed_skips:
            continue
        if result is None:
            bad.append(f"{name}=missing")
        else:
            bad.append(f"{name}={result}")
    # Jobs listed in allowed_skips that are absent entirely still OK (expected skip)
    if bad:
        return 1, "ci-gate: jobs no success: " + ", ".join(bad)
    return 0, "ci-gate: OK"


def main() -> int:
    hold = os.environ.get("HOLD", "").lower() == "true"
    skips_raw = os.environ.get("ALLOWED_SKIPS", "").strip()
    allowed = {s for s in skips_raw.split() if s}
    raw = os.environ.get("NEEDS_JSON", "")
    if not raw:
        print("ci-gate: NEEDS_JSON ausente", file=sys.stderr)
        return 1
    try:
        needs = json.loads(raw)
    except json.JSONDecodeError:
        print("ci-gate: NEEDS_JSON inválido", file=sys.stderr)
        return 1
    if not isinstance(needs, dict):
        print("ci-gate: NEEDS_JSON no es objeto", file=sys.stderr)
        return 1
    code, msg = evaluate(needs, allowed, hold)
    if code != 0:
        print(f"::error::{msg}")
    else:
        # Anunciar skips esperados sin llamar PASS al control omitido.
        for name in sorted(allowed):
            info = needs.get(name)
            if info is None or (isinstance(info, dict) and info.get("result") == "skipped"):
                if name == "private-denylist":
                    print("PRIVATE_CHECK_NOT_APPLICABLE_TO_PR")
                else:
                    print(f"ALLOWED_SKIP: {name}")
        print(msg)
    return code


if __name__ == "__main__":
    sys.exit(main())
