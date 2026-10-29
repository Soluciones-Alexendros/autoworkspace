# Proton Pass 2024-26: pass-cli v2.3+, JSON y MCP

Novedades del ecosistema Proton Pass 2024-26 relevantes para esta skill. El canon operativo vive en [protonsuite-tools @ v1.5.0](https://github.com/Soluciones-Alexendros/protonsuite-tools/tree/v1.5.0) (AGPL-3.0: solo enlazar); aquí solo criterio de decisión.

## Matriz de decisión: MCP → CLI → manual

| Vía | Cuándo | Notas |
|---|---|---|
| **MCP tools** (`docs/mcp-tools/pass.md`) | Entorno con servidor MCP (defecto en agentes) | Estructurado, sin parseo, sin subprocesos |
| **`pass-cli` v2.3+ con JSON** | Sin MCP, con sesión Pass disponible | `--json` por subcomando; parsear con `jq`/JSON, nunca con `grep` |
| **Texto plano de `pass-cli`** | Solo fallback si el JSON falla | Frágil ante cambios de formato; evitar |

## pass-cli v2.3+: salida JSON

La novedad relevante de v2.3+ es la salida JSON estable por subcomando (flag exacta por subcomando en `docs/mcp-tools/pass.md` del tag pineado; típicamente `--json` o `--output json`):

```bash
# Localizar sin parseo frágil: JSON + jq
pass-cli list --vault Personal --json | jq -r '.[].name'
pass-cli show 'Personal/app.com' --field password
```

Reglas del agente:

1. Pedir **un campo** (`--field password`), nunca volcar el item entero.
2. Consumir JSON siempre que el subcomando lo soporte; el parseo de texto es fallback legacy.
3. Sintaxis de items estable: `pass://<Bóveda>/<Item>/<campo>`.
4. Tras `login`/`sync`, reintentar el flujo de sesión ante fallo; no degradar a secretos hardcodeados ni pedidos en texto plano.

## MCP tools de Pass (resumen)

Detalle completo en `docs/mcp-tools/pass.md` del tag pineado. Cubren: listar, buscar, mostrar campo concreto y generar contraseñas. El agente los prefiere al CLI: evitan subprocesos, fugas en historial de shell y parseo.

## Seguridad (recordatorio)

El detalle local vive en `references/security-notes.md` (legacy; el canon en `docs/bridge-core/security-notes.md` del tag): sesión en `~/.local/share/proton-pass-cli/.session/` (no compartir), inyección por variable de entorno al proceso destino, `chmod 600` en temporales con borrado posterior, y borrado de portapapeles tras ~45 s si se usa.
