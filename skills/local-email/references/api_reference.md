# Referencia del script proton_bridge.py

> LEGACY: el canon vive en protonsuite-tools @ v1.5.0 (`docs/bridge-core/api-reference.md`, `docs/mcp-tools/mail.md`). Este fichero documenta el script local deprecado pero funcional.

Todos los subcomandos imprimen por stdout; errores a stderr con código
de salida distinto de 0.

## unread

`unread [--limit N]`

Lista los UIDs no leídos de INBOX (los N más recientes, defecto 50) con
fecha, remitente, asunto y Message-ID. No marca nada como leído
(usa `BODY.PEEK`).

## search

`search [--from TXT] [--subject TXT] [--text TXT] [--since DD-Mon-YYYY] [--unread] [--limit N]`

Búsqueda IMAP en INBOX. `--since` en formato IMAP (`01-Jan-2026`).
Sin criterios equivale a `ALL`. Misma salida que `unread`.

## fetch

`fetch --uid UID [--headers]`

Descarga el RFC822 completo y muestra cabeceras básicas decodificadas y
el cuerpo (prefiere `text/plain`; cae a `text/html` si no hay texto
plano). Con `--headers` imprime primero todas las cabeceras completas
(útil para prueba documental: Received, Message-ID, fechas de tránsito).

## folders

Lista los buzones/etiquetas IMAP tal como los devuelve Bridge (con
flags y separador). Los acentos aparecen en UTF-7 modificado IMAP
(`&AOk-` etc.), es normal.

## mark

`mark --uid UID (--read | --unread)`

Añade o quita el flag `\Seen`. Abre INBOX en modo escritura.

## send

`send --to DEST --subject TXT --body TXT`

Envía por SMTP `127.0.0.1:1025` con STARTTLS y login con las mismas
credenciales. Texto plano UTF-8. Para adjuntos o HTML, editar
`cmd_send` (EmailMessage soporta `add_attachment`).

## Notas de implementación

- TLS: `ssl.CERT_NONE` porque Bridge usa certificado autofirmado local.
- Búsquedas por texto: IMAP `TEXT` busca en cabeceras y cuerpo; en
  buzones grandes puede tardar. Acotar con `--since`.
- UIDs: los devueltos por `search`/`unread` son válidos para `fetch` y
  `mark` mientras no se haga `EXPUNGE` en la carpeta.
