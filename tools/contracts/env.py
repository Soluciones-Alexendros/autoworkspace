"""Lectura de variables de entorno sin dependencias (sin python-dotenv)."""
from __future__ import annotations

import os
import sys
from typing import NoReturn


def require_env(name: str, help_text: str) -> str:
    """Devuelve os.environ[name] o termina con código ≠0 y mensaje canónico."""
    value = os.environ.get(name)
    if value is None or value == "":
        print(
            f"Falta la variable {name}: {help_text}; ver .env.example",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return value


def env_or(name: str, default: str) -> str:
    return os.environ.get(name, default)
