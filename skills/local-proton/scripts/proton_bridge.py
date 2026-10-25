#!/usr/bin/env python3
"""Cliente CLI para Proton Mail Bridge (IMAP 127.0.0.1:1143 / SMTP 127.0.0.1:1025).

LEGACY: funcional pero deprecado. El canon vive en protonsuite-tools
(tag v1.5.0, AGPL-3.0, solo enlazado). Se mantiene con tests en verde;
no añadir features. Preferir los MCP tools de Mail cuando existan.

Credenciales por entorno: PROTON_USER (email Proton), PROTON_PASS (password de Bridge).
Subcomandos: unread, search, fetch, folders, mark, send.
"""

import argparse
import email
import email.header
import imaplib
import logging
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

IMAP_HOST = os.environ.get("PROTON_IMAP_HOST", "127.0.0.1")
try:
    IMAP_PORT = int(os.environ.get("PROTON_IMAP_PORT", "1143"))
except ValueError:
    IMAP_PORT = 1143
SMTP_HOST = os.environ.get("PROTON_SMTP_HOST", "127.0.0.1")
try:
    SMTP_PORT = int(os.environ.get("PROTON_SMTP_PORT", "1025"))
except ValueError:
    SMTP_PORT = 1025

logger = logging.getLogger("proton_bridge")


class ProtonBridgeError(RuntimeError):
    """Error controlado del Bridge (credenciales, conexión, protocolo)."""


def get_config():
    """Lee la configuración desde el entorno en cada llamada (testeable)."""
    imap_host = os.environ.get("PROTON_IMAP_HOST", IMAP_HOST)
    smtp_host = os.environ.get("PROTON_SMTP_HOST", SMTP_HOST)
    try:
        imap_port = int(os.environ.get("PROTON_IMAP_PORT", str(IMAP_PORT)))
    except ValueError:
        imap_port = IMAP_PORT
    try:
        smtp_port = int(os.environ.get("PROTON_SMTP_PORT", str(SMTP_PORT)))
    except ValueError:
        smtp_port = SMTP_PORT
    user = os.environ.get("PROTON_USER")
    password = os.environ.get("PROTON_PASS")
    return imap_host, imap_port, smtp_host, smtp_port, user, password


def tls_ctx():
    # Bridge usa certificado autofirmado local: desactivar verificación.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def require_creds():
    _, _, _, _, user, password = get_config()
    if not user or not password:
        raise ProtonBridgeError(
            "Faltan PROTON_USER / PROTON_PASS en el entorno. Usa la contraseña generada por Bridge, no la de la cuenta."
        )
    return user, password


def connect(imap_host=None, imap_port=None):
    """Abre la conexión IMAP contra Bridge. Testeable: mockear esta función."""
    cfg_host, cfg_port, _, _, user, password = get_config()
    host = imap_host if imap_host is not None else cfg_host
    port = imap_port if imap_port is not None else cfg_port
    if not user or not password:
        raise ProtonBridgeError(
            "Faltan PROTON_USER / PROTON_PASS en el entorno. Usa la contraseña generada por Bridge, no la de la cuenta."
        )
    try:
        imap = imaplib.IMAP4(host, port)
        imap.starttls(ssl_context=tls_ctx())
        imap.login(user, password)
    except (OSError, imaplib.IMAP4.error, ssl.SSLError) as exc:
        raise ProtonBridgeError(f"No se pudo conectar al Bridge IMAP {host}:{port}: {exc}") from exc
    return imap


def connect_smtp(smtp_host=None, smtp_port=None):
    """Abre la conexión SMTP contra Bridge. Testeable: mockear esta función."""
    _, _, cfg_host, cfg_port, user, password = get_config()
    host = smtp_host if smtp_host is not None else cfg_host
    port = smtp_port if smtp_port is not None else cfg_port
    if not user or not password:
        raise ProtonBridgeError(
            "Faltan PROTON_USER / PROTON_PASS en el entorno. Usa la contraseña generada por Bridge, no la de la cuenta."
        )
    try:
        server = smtplib.SMTP(host, port)
        server.starttls(context=tls_ctx())
        server.login(user, password)
    except (OSError, smtplib.SMTPException, ssl.SSLError) as exc:
        raise ProtonBridgeError(f"No se pudo conectar al Bridge SMTP {host}:{port}: {exc}") from exc
    return server


def decode_header_value(v):
    if not v:
        return ""
    parts = email.header.decode_header(v)
    out = []
    for txt, enc in parts:
        out.append(txt.decode(enc or "utf-8", "replace") if isinstance(txt, bytes) else txt)
    return "".join(out)


def select_inbox(imap, readonly=True):
    imap.select("INBOX", readonly=readonly)


def print_summaries(imap, uids, limit):
    uids = uids[-limit:][::-1]  # más recientes primero
    for uid in uids:
        typ, data = imap.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])")
        if not data or not isinstance(data[0], tuple):
            continue
        msg = email.message_from_bytes(data[0][1])
        print(f"UID {uid.decode()}")
        print(f"  Fecha:    {msg.get('Date', '')}")
        print(f"  De:       {decode_header_value(msg.get('From', ''))}")
        print(f"  Asunto:   {decode_header_value(msg.get('Subject', ''))}")
        print(f"  Msg-ID:   {msg.get('Message-ID', '')}")
        print()


def cmd_unread(args):
    with connect() as imap:
        select_inbox(imap)
        typ, data = imap.search(None, "UNSEEN")
        uids = data[0].split() if data and data[0] else []
        print(f"No leídos en INBOX: {len(uids)}\n")
        print_summaries(imap, uids, args.limit)


def cmd_search(args):
    with connect() as imap:
        select_inbox(imap)
        criteria = []
        if args.unread:
            criteria.append("UNSEEN")
        if getattr(args, "from"):
            criteria += ["FROM", f'"{getattr(args, "from")}"']
        if args.subject:
            criteria += ["SUBJECT", f'"{args.subject}"']
        if args.text:
            criteria += ["TEXT", f'"{args.text}"']
        if args.since:
            criteria += ["SINCE", args.since]
        if not criteria:
            criteria = ["ALL"]
        typ, data = imap.search(None, *criteria)
        uids = data[0].split() if data and data[0] else []
        print(f"Resultados: {len(uids)}\n")
        print_summaries(imap, uids, args.limit)


def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
    payload = msg.get_payload(decode=True)
    return payload.decode(msg.get_content_charset() or "utf-8", "replace") if payload else ""


def cmd_fetch(args):
    with connect() as imap:
        select_inbox(imap)
        typ, data = imap.fetch(args.uid.encode(), "(RFC822)")
        if not data or not isinstance(data[0], tuple):
            raise ProtonBridgeError(f"UID {args.uid} no encontrado")
        msg = email.message_from_bytes(data[0][1])
        if args.headers:
            print("".join(f"{k}: {decode_header_value(v)}\n" for k, v in msg.items()))
        print(f"Fecha:  {msg.get('Date', '')}")
        print(f"De:     {decode_header_value(msg.get('From', ''))}")
        print(f"Para:   {decode_header_value(msg.get('To', ''))}")
        print(f"Asunto: {decode_header_value(msg.get('Subject', ''))}")
        print(f"Msg-ID: {msg.get('Message-ID', '')}")
        print("-" * 60)
        print(extract_body(msg))


def cmd_folders(_args):
    with connect() as imap:
        typ, boxes = imap.list()
        for b in boxes or []:
            print(b.decode("utf-8", "replace"))


def cmd_mark(args):
    with connect() as imap:
        select_inbox(imap, readonly=False)
        flag = "+FLAGS" if args.read else "-FLAGS"
        imap.store(args.uid.encode(), flag, "(\\Seen)")
        print(f"UID {args.uid}: {'leído' if args.read else 'no leído'}")


def cmd_send(args):
    """Send requires ApprovalProvider via execution registry (no CONFIRM_SEND/env)."""
    from pathlib import Path

    tools = Path(__file__).resolve().parents[3] / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from execution.ops import run_registered
    from execution.registry import register_handler

    params = {
        "to": args.to,
        "subject": args.subject,
        "body": args.body,
    }

    def _do_send(p: dict) -> int:
        _, _, _, _, user, _ = get_config()
        require_creds()
        msg = EmailMessage()
        msg["From"] = user
        msg["To"] = p["to"]
        msg["Subject"] = p["subject"]
        msg.set_content(p["body"])
        with connect_smtp() as s:
            s.send_message(msg)
        print(f"Enviado a {p['to']}")
        return 0

    register_handler("proton_send", _do_send)
    result = run_registered("proton_send", params, target=args.to)
    if result.outcome != "succeeded":
        print(
            f"BLOCKED: proton_send requires trusted ApprovalProvider "
            f"(digest={result.plan_digest[:16]}…). "
            "CONFIRM_SEND / PROTON_APPROVE_* / approved=true are not consent.",
            file=sys.stderr,
        )
        raise ProtonBridgeError(f"send blocked: {result.detail or result.outcome}")


def build_parser():
    p = argparse.ArgumentParser(description="Cliente Proton Mail Bridge")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("unread")
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(fn=cmd_unread)

    sp = sub.add_parser("search")
    sp.add_argument("--from", dest="from")
    sp.add_argument("--subject")
    sp.add_argument("--text")
    sp.add_argument("--since")
    sp.add_argument("--unread", action="store_true")
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(fn=cmd_search)

    sp = sub.add_parser("fetch")
    sp.add_argument("--uid", required=True)
    sp.add_argument("--headers", action="store_true")
    sp.set_defaults(fn=cmd_fetch)

    sp = sub.add_parser("folders")
    sp.set_defaults(fn=cmd_folders)

    sp = sub.add_parser("mark")
    sp.add_argument("--uid", required=True)
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--read", action="store_true")
    g.add_argument("--unread", action="store_true")
    sp.set_defaults(fn=cmd_mark)

    sp = sub.add_parser("send")
    sp.add_argument("--to", required=True)
    sp.add_argument("--subject", required=True)
    sp.add_argument("--body", required=True)
    sp.add_argument(
        "--approve-send",
        default="",
        help="Ignored (legacy). Approval goes through ApprovalProvider only.",
    )
    sp.add_argument(
        "--approve-digest",
        default="",
        help="Ignored (legacy). Plan digest is computed by the registry.",
    )
    sp.set_defaults(fn=cmd_send)
    return p


def main(argv=None):
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    p = build_parser()
    args = p.parse_args(argv)
    try:
        args.fn(args)
    except ProtonBridgeError as exc:
        logger.error("%s", exc)
        return 1
    except (OSError, imaplib.IMAP4.error, smtplib.SMTPException, ssl.SSLError) as exc:
        logger.error("Error del Bridge: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
