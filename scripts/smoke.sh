#!/usr/bin/env bash
# Contrato de smoke de la flota (demo para este canon).
#
# En un repo de producto este script DEBE:
#   1. Ser barato (≤5 min) y determinista.
#   2. Ejecutarse después de build (o de quality+test si no hay artefacto).
#   3. Comprobar rutas/resultados reales del producto, por ejemplo:
#        - Web/SaaS: GET / y/o /api/health → HTTP 200 + marcador en el body
#        - CLI:      "$BIN" --help  (exit 0) y un subcomando version/doctor
#        - Infra:    make validate + dry-run de un stack
#   4. Usar .env.example o mocks. Cero dependencias de producción.
#   5. Salir ≠ 0 si cualquier aserción falla (set -euo pipefail).
#
# Este canon no tiene runtime: demostramos el contrato y salimos 0.

set -euo pipefail

echo "smoke: contrato de la flota (canon repo-standard)"
echo "  - job CI: smoke"
echo "  - fachada: make smoke"
echo "  - producto: sustituye este script por health/rutas/--help"
echo "smoke: OK"
exit 0
