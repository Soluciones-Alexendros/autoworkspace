# pass-cli — referencia de comandos

> LEGACY: el canon vive en protonsuite-tools @ v1.5.0 (`docs/mcp-tools/pass.md`). Este fichero conserva la referencia local (v2.2.0+; para JSON ver v2.3+ en `protonsuite-pass-2024-2026.md`).

Referencia operativa del CLI oficial `pass-cli` para Proton Pass (v2.2.0+). Sintaxis de
items: `pass://<Bóveda>/<Item>/<campo>`.

## Comandos de sesión

| Comando | Uso |
|---|---|
| `pass-cli login` | Inicia sesión (flujo web, idempotente). Ya activa → no-op. |
| `pass-cli logout` | Cierra la sesión y borra la credencial local. |
| `pass-cli sync` | Sincroniza las bóvedas locales con el servidor. |

## Comandos de items

| Comando | Uso |
|---|---|
| `pass-cli list` | Lista items de una bóveda _(ejemplo: `pass-cli list --vault Personal`)_ |
| `pass-cli show <item>` | Muestra campos de un item; `--field <campo>` para uno concreto |
| `pass-cli insert <ruta>` | Crea un item interactivo _(ejemplo: `pass-cli insert Personal/app.com`)_ |
| `pass-cli edit <item>` | Edita un item (nombre, campos, bóveda) |
| `pass-cli rm <item>` | Elimina un item |
| `pass-cli mv <item> <ruta-nueva>` | Mueve un item a otra bóveda o ruta |
| `pass-cli cp <item> <ruta-nueva>` | Copia un item |
| `pass-cli generate` | Genera una contraseña aleatoria _(ejemplo: `pass-cli generate --length 20`)_ |

## Comandos de compartición

| Comando | Uso |
|---|---|
| `pass-cli share` | Gestiona compartición con otros usuarios Proton _(ejemplo: `pass-cli share list`)_ |

## Flujo habitual

1. `pass-cli login` → confirmar sesión activa.
2. `pass-cli sync` → asegurar datos frescos.
3. `pass-cli list` → localizar el item.
4. `pass-cli show <item> --field password` → obtener el secreto sin volcar el resto.
5. Usar el secreto y **no** dejarlo en salida de logs ni en código.

## Errores frecuentes

| Síntoma | Causa | Acción |
|---|---|---|
| Sesión caducada | Token expirado | `pass-cli login` (flujo web) |
| `sync` falla | Red / servidor | Reintentar; verificar conectividad con Proton |
| Item no está | Bóveda incorrecta | `pass-cli list` sin filtro y localizar la bóveda real |
