#!/usr/bin/env python3

"""Tests hardening para proton_bridge.py (sin red real: monkeypatch IMAP/SMTP)."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from collections.abc import Sequence
from email.message import EmailMessage
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, cast
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
TOOLS = Path(__file__).resolve().parents[3]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _load_driver() -> ModuleType:
    """Load the sibling driver by path to avoid colliding with the skill wrapper."""
    path = SCRIPTS / "proton_bridge.py"
    spec = importlib.util.spec_from_file_location("proton_bridge_driver", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


proton_bridge: Any = _load_driver()
from execution.approval import (  # noqa: E402
    ApprovalDecision,
    ApprovalProvider,
    ApprovalRequest,
)


class FakeIMAP:
    def __init__(self, *a: str, **k: Any) -> None:
        self.selected: tuple[str, bool] | None = None
        self.stored: list[tuple[Any, str, Any]] = []

    def starttls(self, ssl_context: Any = None) -> None:
        return None

    def login(self, user: str, password: str) -> tuple[str, Sequence[Any]]:
        return ("OK", [])

    def select(self, box: str, readonly: bool = True) -> tuple[str, Sequence[Any]]:
        self.selected = (box, readonly)
        return ("OK", [])

    def search(self, *args: str) -> tuple[str, Sequence[bytes]]:
        return ("OK", [b"1 2"])

    def fetch(self, uid: Any, _spec: Any) -> tuple[str, Sequence[tuple[bytes, bytes]]]:
        raw = (
            b"From: Test <t@example.com>\r\nSubject: Hola\r\nMessage-ID: <1>\r\n"
            b"Date: Thu, 01 Jan 2026 00:00:00 +0000\r\n\r\nBody"
        )
        return ("OK", [(b"1", raw)])

    def list(self) -> tuple[str, Sequence[bytes]]:
        return ("OK", [b'(HasNoChildren) "/" "INBOX"'])

    def store(self, uid: Any, flag: str, val: Any) -> tuple[str, Sequence[Any]]:
        self.stored.append((uid, flag, val))
        return ("OK", [])

    def __enter__(self) -> FakeIMAP:
        return self

    def __exit__(self, *a: str) -> Literal[False]:
        return False


class FakeSMTP:
    sent = None

    def __init__(self, *a: str, **k: Any) -> None:
        pass

    def starttls(self, context: Any = None) -> None:
        return None

    def login(self, user: str, password: str) -> None:
        return None

    def send_message(self, msg: Any) -> None:
        FakeSMTP.sent = msg

    def __enter__(self) -> FakeSMTP:
        return self

    def __exit__(self, *a: str) -> Literal[False]:
        return False


def _with_creds(testcase: Any) -> None:
    testcase._old = dict(os.environ)
    os.environ["PROTON_USER"] = "u@example.com"
    os.environ["PROTON_PASS"] = "bridge-pass"

    def _restore_env() -> None:
        os.environ.clear()
        os.environ.update(testcase._old)

    testcase.addCleanup(_restore_env)


class ProtonBridgeCli(unittest.TestCase):
    def test_help_exit_0(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_subcommand_help_exit_0(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["unread", "--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_args_invalidos_exit_2(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main(["--opcion-inexistente"])
        self.assertEqual(cm.exception.code, 2)

    def test_sin_subcomando_exit_2(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            proton_bridge.main([])
        self.assertEqual(cm.exception.code, 2)

    def test_credenciales_ausentes_exit_1(self) -> None:
        old = dict(os.environ)
        try:
            os.environ.pop("PROTON_USER", None)
            os.environ.pop("PROTON_PASS", None)
            rc = proton_bridge.main(["unread"])
            self.assertEqual(rc, 1)
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_bridge_caido_exit_1(self) -> None:
        _with_creds(self)

        def _boom(*a: str, **k: Any) -> None:
            raise OSError("conexión rechazada (simulada)")

        old = proton_bridge.connect
        proton_bridge.connect = cast("Any", _boom)
        try:
            rc = proton_bridge.main(["unread"])
            self.assertEqual(rc, 1)
        finally:
            proton_bridge.connect = old

    def test_unread_ok_con_mock(self) -> None:
        _with_creds(self)
        old = proton_bridge.connect
        proton_bridge.connect = lambda *a, **k: cast("Any", FakeIMAP())
        try:
            rc = proton_bridge.main(["unread", "--limit", "5"])
            self.assertEqual(rc, 0)
        finally:
            proton_bridge.connect = old

    def test_send_blocked_without_approval(self) -> None:
        _with_creds(self)
        rc = proton_bridge.main(["send", "--to", "a@b.com", "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)

    def test_send_ok_con_mock(self) -> None:
        class Allow(ApprovalProvider):
            def decide(self, request: ApprovalRequest) -> ApprovalDecision:
                return ApprovalDecision(True, "test", "test", request.plan_digest)

        _with_creds(self)
        old_c, old_s = proton_bridge.connect, proton_bridge.connect_smtp
        proton_bridge.connect = lambda *a, **k: cast("Any", FakeIMAP())
        proton_bridge.connect_smtp = lambda *a, **k: cast("Any", FakeSMTP())
        try:
            with patch("execution.ops.provider_from_env", Allow):
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

    def test_fetch_no_encontrado_exit_1(self) -> None:
        _with_creds(self)

        class Empty(FakeIMAP):
            def fetch(self, uid: Any, _spec: Any) -> tuple[str, list[Any]]:
                return ("OK", [None])

        old = proton_bridge.connect
        proton_bridge.connect = lambda *a, **k: cast("Any", Empty())
        try:
            rc = proton_bridge.main(["fetch", "--uid", "999"])
            self.assertEqual(rc, 1)
        finally:
            proton_bridge.connect = old


class ProtonBridgePure(unittest.TestCase):
    def test_decode_header_value(self) -> None:
        self.assertEqual(proton_bridge.decode_header_value(""), "")
        self.assertEqual(proton_bridge.decode_header_value(None), "")
        self.assertEqual(proton_bridge.decode_header_value("Hola"), "Hola")

    def test_extract_body_simple(self) -> None:
        msg = EmailMessage()
        msg.set_content("cuerpo plano")
        self.assertIn("cuerpo plano", proton_bridge.extract_body(msg))

    def test_get_config_lee_entorno(self) -> None:
        old = dict(os.environ)
        try:
            os.environ["PROTON_USER"] = "x@y.com"
            os.environ["PROTON_PASS"] = "p"
            _, _, _, _, user, pw = proton_bridge.get_config()
            self.assertEqual(user, "x@y.com")
            self.assertEqual(pw, "p")
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_require_creds_falla_sin_env(self) -> None:
        old = dict(os.environ)
        try:
            os.environ.pop("PROTON_USER", None)
            os.environ.pop("PROTON_PASS", None)
            with self.assertRaises(proton_bridge.ProtonBridgeError):
                proton_bridge.require_creds()
        finally:
            os.environ.clear()
            os.environ.update(old)


if __name__ == "__main__":
    unittest.main()
