#!/usr/bin/env python3
"""Calculadora de contraste WCAG 2.2 (relación de luminancia relativa).

Uso:
    python3 contrast.py "#1a1a1a" "#ffffff" [--large]
    python3 contrast.py --selftest

Salida JSON con ratio y veredicto por nivel. Código de salida: 0 si el par
cumple AA (o AA large con --large), 1 si el veredicto es FAIL, 2 si el input
es inválido.
"""

import argparse
import json
import logging
import re
import sys
from typing import Any

logger = logging.getLogger("auditoria360.contrast")

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

THRESHOLDS = {
    "aa_normal": 4.5,
    "aa_large": 3.0,
    "aa_ui": 3.0,
    "aaa_normal": 7.0,
    "aaa_large": 4.5,
}

# Constantes con nombre (P12 T6e): sustituyen literales mágicos.
HEX_SHORT_LEN = 3
SRGB_LINEAR_THRESHOLD = 0.03928
RATIO_TOLERANCE = 0.02


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    m = HEX_RE.match(hex_color.strip())
    if not m:
        raise ValueError(f"Color inválido: '{hex_color}'. Usa formato #RGB o #RRGGBB.")
    h = m.group(1)
    if len(h) == HEX_SHORT_LEN:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def relative_luminance(hex_color: str) -> float:
    def linearize(c: float) -> float:
        return c / 12.92 if c <= SRGB_LINEAR_THRESHOLD else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (linearize(c) for c in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check(fg: str, bg: str, large_text: bool = False) -> dict[str, Any]:
    ratio = contrast_ratio(fg, bg)
    aa = THRESHOLDS["aa_large"] if large_text else THRESHOLDS["aa_normal"]
    aaa = THRESHOLDS["aaa_large"] if large_text else THRESHOLDS["aaa_normal"]
    return {
        "foreground": fg,
        "background": bg,
        "large_text": large_text,
        "ratio": round(ratio, 2),
        "aa": ratio >= aa,
        "aaa": ratio >= aaa,
        "aa_ui_components": ratio >= THRESHOLDS["aa_ui"],
        "veredicto": ("AAA" if ratio >= aaa else "AA" if ratio >= aa else "FAIL"),
    }


def selftest() -> list[str]:
    cases = [
        ("#000000", "#FFFFFF", 21.0, True),
        ("#767676", "#FFFFFF", 4.54, True),
        ("#767676", "#FFFF00", 4.23, False),  # corregido: el material fuente indicaba 2.59 (erróneo)
        ("#777777", "#FFFFFF", 4.48, False),
    ]
    failures: list[str] = []
    for fg, bg, expected_ratio, expected_aa in cases:
        r = check(fg, bg)
        if abs(r["ratio"] - expected_ratio) > RATIO_TOLERANCE or r["aa"] != expected_aa:
            failures.append(f"{fg} sobre {bg}: ratio={r['ratio']} (esperado {expected_ratio}), aa={r['aa']}")
    return failures


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Contraste WCAG entre dos colores")
    ap.add_argument("fg", nargs="?", help="Color de texto (#RRGGBB)")
    ap.add_argument("bg", nargs="?", help="Color de fondo (#RRGGBB)")
    ap.add_argument("--large", action="store_true", help="Texto grande (>=18pt o 14pt bold)")
    ap.add_argument("--selftest", action="store_true", help="Ejecutar tests internos")
    args = ap.parse_args(argv)

    if args.selftest:
        failures = selftest()
        print(json.dumps({"selftest": "PASS" if not failures else "FAIL", "failures": failures}, ensure_ascii=False))
        return 0 if not failures else 1

    if not args.fg or not args.bg:
        ap.error("Indica fg y bg, o usa --selftest")
    try:
        result = check(args.fg, args.bg, args.large)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ValueError as e:
        logger.error("color inválido: %s", e)
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 2
    return 0 if result["veredicto"] != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
