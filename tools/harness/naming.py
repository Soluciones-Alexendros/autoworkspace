"""SSOT for product brand, prefixes and legacy identifiers (machineroom)."""

from __future__ import annotations

BRAND = "machineroom"
BRAND_TITLE = "Machineroom"
PREFIX = "mr"
RUNTIME_DIRNAME = ".machineroom"
PROJECT_DIRNAME = ".machineroom"
REPO = "Soluciones-Alexendros/machineroom"

# Legacy names kept for D3 fallback and migration; nowhere else in live code.
LEGACY_BRAND = "autoworkspace"
LEGACY_BRAND_TITLE = "Autoworkspace"
LEGACY_PREFIX = "aw"
LEGACY_RUNTIME_DIRNAME = ".autoworkspace"
LEGACY_PROJECT_DIRNAME = ".autoworkspace"
LEGACY_REPO = "Soluciones-Alexendros/autoworkspace"
LEGACY_SKILL_SELF = "project-autoworkspace"
LEGACY_EXTENSION_DIR = "autoworkspace"
LEGACY_AGENTS = ("aw-planner", "aw-verifier", "aw-worker")
LEGACY_SUBAGENT = "aw_subagent"
LEGACY_STATUS_CMD = "/aw-status"

SKILL_SELF = "project-machineroom"
EXTENSION_DIR = "machineroom"
AGENTS = ("mr-planner", "mr-verifier", "mr-worker")
SUBAGENT = "mr_subagent"
STATUS_CMD = "/mr-status"
