#!/usr/bin/env python3
"""Tests hardening para proton_bridge.py (sin red real: monkeypatch IMAP/SMTP)."""
from __future__ import annotations

import sys
import unittest
from email.message import EmailMessage
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import proton_bridge  # noqa: E402


class FakeIMAP:
    def __init__(self, *a, **k):
        self.selected = None
        self.stored = []

    def starttls(self, ssl_context=None):
        return None

    def login(self, user, password):
        return ("OK", [])

    def select(self, box, readonly=True):
        self.selected = (box, readonly)
        return ("OK", [])

    def search(self, *args):
        return ("OK", [b"1 2"])

    def fetch(self, uid, _spec):
        raw = b"From: Test <t@example.com>\r\nSubject: Hola\r\nMessage-ID: <1>\r\nDate: Thu, 01 Jan 2026 00:00:00 +0000\r\n\r\nBody"
        return ("OK", [(b"1", raw)])

    def list(self):
        return ("OK", [b'(HasNoChildren) "/" "INBOX"'])

    def store(self, uid, flag, val):
        self.stored.append((uid, flag, val))
        return ("OK", [])

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeSMTP:
    sent = None

    def __init__(self, *a, **k):
        pass

    def starttls(self, context=None):
        return None

    def login(self, user, password):
        return None

    def send_message(self, msg):
        FakeSMTP.sent = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _with_creds(testcase):
    testcase._old = dict(proton_bridge.os.environ)
    proton_bridge.os.environ["PROTON_USER"] = "u@example.com"
    proton_bridge.os.environ["PROTON_PASS"] = "bridge-pass"
    testcase.addCleanup(lambda: proton_bridge.os.environ.clear() or proton_bridge.os.environ.update(testcase._old))


class ProtonBridgeCli(unittest.TestCase):
    def test_help_exit_0(self):
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_subcommand_help_exit_0(self):
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["unread", "--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_args_invalidos_exit_2(self):
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["--opcion-inexistente"])
        self.assertEqual(cm.exception.code, 2)

    def test_sin_subcomando_exit_2(self):
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main([])
        self.assertEqual(cm.exception.code, 2)

    def test_credenciales_ausentes_exit_1(self):
        old = dict(proton_bridge.os.environ)
        try:
            proton_bridge.os.environ.pop("PROTON_USER", None)
            proton_bridge.os.environ.pop("PROTON_PASS", None)
            rc = proton_bridge.main(["unread"])
            self.assertEqual(rc, 1)
        finally:
            proton_bridge.os.environ.clear()
            proton_bridge.os.environ.update(old)

    def test_bridge_caido_exit_1(self):
        _with_creds(self)

        def _boom(*a, **k):
            raise OSError("conexión rechazada (simulada)")

        old = proton_bridge.connect
        proton_bridge.connect = _boom
        try:
            rc = proton_bridge.main(["unread"])
            self.assertEqual(rc, 1)
        finally:
            proton_bridge.connect = old

    def test_unread_ok_con_mock(self):
        _with_creds(self)
        old = proton_bridge.connect
        proton_bridge.connect = lambda *a, **k: FakeIMAP()
        try:
            rc = proton_bridge.main(["unread", "--limit", "5"])
            self.assertEqual(rc, 0)
        finally:
            proton_bridge.connect = old

    def test_send_blocked_without_approval(self):
        _with_creds(self)
        rc = proton_bridge.main(["send", "--to", "a@b.com", "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)

    def test_send_ok_con_mock(self):
        import sys
        from pathlib import Path
        from unittest.mock import patch

        tools = Path(__file__).resolve().parents[3] / "tools"
        sys.path.insert(0, str(tools))
        from execution.approval import ApprovalDecision, ApprovalProvider, ApprovalRequest

        class Allow(ApprovalProvider):
            def decide(self, request: ApprovalRequest) -> ApprovalDecision:
                return ApprovalDecision(True, "test", "test", request.plan_digest)

        _with_creds(self)
        old_c, old_s = proton_bridge.connect, proton_bridge.connect_smtp
        proton_bridge.connect = lambda *a, **k: FakeIMAP()
        proton_bridge.connect_smtp = lambda *a, **k: FakeSMTP()
        try:
            with patch("execution.ops.provider_from_env", lambda: Allow()):
                rc = proton_bridge.main(
                    [
                        "send",
                        "--to",
                        "a@b.com",
                        "--subject",
                        "s",
                        "--body",
                        "b",
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertIsNotNone(FakeSMTP.sent)
        finally:
            proton_bridge.connect = old_c
            proton_bridge.connect_smtp = old_s

    def test_fetch_no_encontrado_exit_1(self):
        _with_creds(self)

        class Empty(FakeIMAP):
            def fetch(self, uid, _spec):  # type: ignore[override]
                return ("OK", [None])

        old = proton_bridge.connect
        proton_bridge.connect = lambda *a, **k: Empty()
        try:
            rc = proton_bridge.main(["fetch", "--uid", "999"])
            self.assertEqual(rc, 1)
        finally:
            proton_bridge.connect = old


class ProtonBridgePure(unittest.TestCase):
    def test_decode_header_value(self):
        self.assertEqual(proton_bridge.decode_header_value(""), "")
        self.assertEqual(proton_bridge.decode_header_value(None), "")
        self.assertEqual(proton_bridge.decode_header_value("Hola"), "Hola")

    def test_extract_body_simple(self):
        msg = EmailMessage()
        msg.set_content("cuerpo plano")
        self.assertIn("cuerpo plano", proton_bridge.extract_body(msg))

    def test_get_config_lee_entorno(self):
        old = dict(proton_bridge.os.environ)
        try:
            proton_bridge.os.environ["PROTON_USER"] = "x@y.com"
            proton_bridge.os.environ["PROTON_PASS"] = "p"
            _, _, _, _, user, pw = proton_bridge.get_config()
            self.assertEqual(user, "x@y.com")
            self.assertEqual(pw, "p")
        finally:
            proton_bridge.os.environ.clear()
            proton_bridge.os.environ.update(old)

    def test_require_creds_falla_sin_env(self):
        old = dict(proton_bridge.os.environ)
        try:
            proton_bridge.os.environ.pop("PROTON_USER", None)
            proton_bridge.os.environ.pop("PROTON_PASS", None)
            with self.assertRaises(proton_bridge.ProtonBridgeError):
                proton_bridge.require_creds()
        finally:
            proton_bridge.os.environ.clear()
            proton_bridge.os.environ.update(old)


if __name__ == "__main__":
    unittest.main()
