# Repo skill standard

Based on the [Agent Skills specification](https://agentskills.io/specification). The `tools/validate/skill_spec.py` validator enforces these rules.

## `SKILL.md` frontmatter (required)

```yaml
---
name: my-skill # = directory name; kebab-case, 1–64 chars, no -- or edge -
description: >- # 1–1024 chars; template below
  ...
license: MIT # repo-wide license
metadata:
  author: Soluciones-Alexendros
  version: "0.1.0" # skill semver
  domain: plan # one of docs/TAXONOMY.md: plan | local | project | web | role
  type: atomic # atomic | orchestrator | router | audit
  language: en
---
```

Optional spec fields (`compatibility`, `allowed-tools`) may be added when they add value.

## Description (template)

Third person, within 1024 characters:

`[Capability]. Use when [contexts]. Not for [limit] (→ neighbor-skill).`

The phrases `Use when` and the exclusion clause (`Not for` / `Do not use`) are literal (the validator requires them). The `→ name` arrow only when `name` is a real folder in `skills/`.

## Body

- Hard limit: **≤ 500 lines** and **≤ 5000 tokens**. When it grows, extract to `references/*.md` and leave a summary with a link.
- Canonical English H2s. Required: **Overview**, **When to Use**. With `.py` or `.sh` executables outside `tests/`: **Tools**.
- Optional with real content: Scope, Procedure, Output format, Edge cases, Validation, plus the domain sections the procedure needs (Routing, Phases, Modes).
- Forbidden: `What it does / Purpose`, `When to use me / Triggering`, a `Usage` repeating the description, an inventory `Structure`, host-specific profile headings, `sudoers.d` paths, and concrete host names.
- Relative links only to files that exist (`tools/validate/skill_links.py`).
- `references/` is flat: no subdirectories. `assets/` and `scripts/` are resources, not progressive reading.

## Directory structure

```text
skills/<name>/
├── SKILL.md
├── references/   # progressive reading (flat md)
├── scripts/      # executables + tests/ (smoke at scripts/tests/smoke_sh.sh)
├── assets/       # templates, schemas, statics
└── configs/      # sample configurations
```

Forbidden in the repo: `__pycache__/`, `.pytest_cache/`, `.archivado-*` dirs, per-skill `LICENSE` files, loose `agents/`, `infrastructure/`, `languages/` dirs (flattened into `references/`). The validator only fails when those residues are tracked by git.

## Procedures (scripts and logic)

Structure: **Precondition → Action → Expected → Error → Recovery**.
Scripts: **INPUT → validate → execute → inspect → structured output → exit code**.
Structured output: JSON for machine consumption, Markdown for humans.
Exit codes: `0` OK, `1` error or negative verdict, `2` invalid input, `3` missing dependency, `4` permission denied.

Smoke: `skills/<name>/scripts/tests/smoke_sh.sh` is required if and only if there are `.py` or `.sh` executables outside `tests/` and `test_*.py`.

## MCP Tools

Convention: `ServerName:tool_name` (e.g. `firecrawl:firecrawl_search`, `github:github_search_code`).

## Versions (two axes)

1. **Skill** — `metadata.version` in each `SKILL.md`. CI (`version.yml`) requires a bump in PRs touching that skill.
2. **Repo** — `package.json` `version` + annotated tag `vX.Y.Z` + [CHANGELOG.md](../CHANGELOG.md) section. The release workflow cuts the tag and publishes the GitHub Release when the manifest is ahead of the last tag and the changelog has notes.

Skill autoversioning with `tools/version/bump.py`:

| Magnitude | Aliases                | Effect              | When                        |
| --------- | ---------------------- | ------------------- | --------------------------- |
| `major`   | breaking, incompatible | `X.y.z` → `X+1.0.0` | incompatible instructions   |
| `minor`   | feature, functionality | `x.Y.z` → `x.Y+1.0` | new compatible capability   |
| `patch`   | fix, docs, typos       | `x.y.Z` → `x.y.Z+1` | compatible fix, docs, typos |

```bash
python3 tools/version/bump.py --type minor --skills web-owasp
python3 tools/version/bump.py --type patch --all --dry-run
python3 tools/version/bump.py --check --auto --base origin/main
python3 tools/version/cut_tag.py --dry-run
```

Repo tag cutting: `tools/version/cut_tag.py` (the `main` workflow applies it; do not tag by hand in the working tree).
