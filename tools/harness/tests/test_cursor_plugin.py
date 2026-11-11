"""Static completeness and portability checks for the Cursor plugin."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness.doctor import _json_version  # noqa: E402


def test_cursor_plugin_declares_all_components_and_matches_repo_version() -> None:
    plugin_path = ROOT / ".cursor-plugin" / "plugin.json"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert plugin["version"] == _json_version(ROOT / "package.json")
    for component in ("skills", "rules", "agents", "hooks"):
        assert component in plugin
        path = ROOT / plugin[component]
        assert path.exists(), component


def test_plugin_hooks_resolve_from_plugin_root() -> None:
    config = json.loads((ROOT / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
    for definitions in config["hooks"].values():
        for definition in definitions:
            command = definition["command"]
            assert not command.startswith("/")
            assert "$HOME" not in command
            for script in ("session_start.py", "shell_gate.py"):
                if script in command:
                    assert (ROOT / ".cursor" / "hooks" / script).is_file()


def test_marketplace_entry_targets_repository_root() -> None:
    marketplace = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    plugins = [entry for entry in marketplace["plugins"] if entry["name"] == "machineroom"]
    assert len(plugins) == 1
    assert plugins[0]["source"] == "."
