"""conftest: añade scripts/ al sys.path para importar módulos."""

import contextlib
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, SCRIPTS_DIR)

# Los tests historicos lanzan subprocesos con cwd="." y SCRIPT="nombre.py":
# fija el cwd a scripts/ para que pasen se invoque pytest desde donde se invoque.
with contextlib.suppress(OSError):
    os.chdir(SCRIPTS_DIR)
