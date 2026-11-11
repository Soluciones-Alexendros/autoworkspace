"""MCP parity: canonical server list documented, no secret carried in the repo."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs" / "harness-integration.md"
SERVER_FILES = (
    ROOT / ".pi" / "mcp.json",
    ROOT / ".cursor" / "mcp.json",
    ROOT / "mcp.json",
)
CANONICAL = ("github", "context7", "playwright", "chrome-devtools", "notion")
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{12,}"),
    re.compile(r'"Authorization"\s*:\s*"!(?!echo\s+Bearer)'),
    re.compile(r"(api[_-]?key|token|secret)\"?\s*[:=]\s*\"[A-Za-z0-9_\-]{20,}\"", re.IGNORECASE),
)


def test_doc_lists_every_canonical_server() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "## MCP servers (canonical list)" in text
    for server in CANONICAL:
        assert f"`{server}`" in text, server


def test_doc_sends_secrets_to_user_files() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "~/.pi/agent/mcp.json" in text
    assert "~/.cursor/mcp.json" in text
    assert "not part of this repository's diff" in text


def test_no_committed_mcp_file_carries_a_secret() -> None:
    for path in SERVER_FILES:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        json.loads(content)
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(content), f"possible secret in {path}: {pattern.pattern}"


def test_project_mcp_file_declares_no_secret_server() -> None:
    project = ROOT / ".pi" / "mcp.json"
    if not project.is_file():
        return
    data = json.loads(project.read_text(encoding="utf-8"))
    for name, server in (data.get("mcpServers") or {}).items():
        assert not server.get("headers"), f"{name} declares headers; move it to the user file"
        assert not server.get("env"), f"{name} declares env; move it to the user file"
