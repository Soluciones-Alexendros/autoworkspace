"""Fixtures compartidos: scripts/ en sys.path con aislamiento de imports."""

import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_PATH = os.path.join(ROOT, "scripts")

# Insertar al principio para prioridad, pero también registrar en un dict para importlib
sys.path.insert(0, SCRIPTS_PATH)

# Guardar referencia para imports explícitos
import importlib.util

_WEB_COMPLIANCE_SCRIPTS = SCRIPTS_PATH
