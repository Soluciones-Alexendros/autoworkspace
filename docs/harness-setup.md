# Harness setup — Cursor and Pi

`skills/` is the only catalog that is committed. Installers create symlinks; they do not copy skill bodies.

## Machine runtime (`~/.autoworkspace`)

User-scope installs (`--user`) never link into a development checkout. They read a real directory at `$HOME/.autoworkspace` (not a symlink) that holds the harness payload: `skills/`, `.cursor/` (agents, hooks, rules, `hooks.json`), `extensions/autoworkspace/` and `package.json`.

```bash
bash scripts/runtime-sync.sh sync --from /path/to/checkout   # copy payload from a checkout
bash scripts/runtime-sync.sh install --version 7.1.2         # verified release extract
```

Then install Cursor and Pi user links (relative paths into the runtime):

```bash
bash scripts/install.sh --harness cursor --components full --user --yes --json
bash scripts/install-pi.sh --user --yes --json
```

| Default path                              | Link kind                                                  |
| ----------------------------------------- | ---------------------------------------------------------- |
| `~/.cursor/skills/<name>`                 | directory symlink → `../../.autoworkspace/skills/<name>`   |
| `~/.cursor/agents/*.md`                   | file symlink                                               |
| `~/.cursor/hooks/*.py`                    | file symlink                                               |
| `~/.cursor/hooks.json`                    | file symlink (runtime holds user-scoped commands)          |
| `~/.pi/agent/skills/<name>`               | directory symlink                                          |
| `~/.pi/agent/extensions/autoworkspace.ts` | file symlink → runtime `extensions/autoworkspace/index.ts` |

Project installs (`--target`, checkout `.cursor/skills`) keep absolute symlinks into the checkout that runs the installer. That is the CI/fixture contract.

On failure, install and sync print `FAIL <component> <function>: <detail>` on stderr. With `--json`, the object also includes `failures` (each entry has `component`, `function`, `detail`) so an update can name the exact skill, hook or extension that broke.

## Pi native Git package (release installation)

Install an immutable release as one Pi package; no symlink installer is needed:

```bash
pi install git:github.com/Soluciones-Alexendros/autoworkspace@v7.1.1
```

Use `--local` for a project-local declaration, subject to Pi project trust. `pi list` shows the configured package. Updating requires selecting a new tag explicitly; a pinned ref does not move on `pi update`. npm distribution is not part of this release channel.

The symlink installers below remain the development flow for a local checkout.

## Public API (flat destinations)

| Destination                               | Command                                                    |
| ----------------------------------------- | ---------------------------------------------------------- |
| Project `.cursor/skills` (default)        | `bash scripts/install-cursor.sh`                           |
| Project `.cursor/skills` via `--target .` | `bash scripts/install-cursor.sh --target .`                |
| Project `.cursor/skills` explicit         | `bash scripts/install-cursor.sh --target .cursor/skills`   |
| User `~/.cursor/skills`                   | `bash scripts/install-cursor.sh --user`                    |
| Any directory (flat 17 symlinks)          | `bash scripts/install-cursor.sh --target /tmp/test-cursor` |
| Project `.pi/skills` (default)            | `bash scripts/install-pi.sh`                               |
| Project `.pi/skills` via `--target .`     | `bash scripts/install-pi.sh --target .`                    |
| User `~/.pi/agent/skills`                 | `bash scripts/install-pi.sh --user`                        |
| Any directory (flat 17 symlinks)          | `bash scripts/install-pi.sh --target /tmp/test-pi`         |

`--target .` (or the checkout root) resolves to the harness default skills directory — it does **not** place symlinks in the repository root. Arbitrary `--target DIR` stays flat (compat 7.0.0).

`--target` never writes `$HOME`. `--dry-run` performs no filesystem writes. `--uninstall` removes only symlinks recorded in the manifest and still owned by this checkout. `--yes` is non-interactive (foreign/real-dir conflicts still refuse). `--json` prints a single JSON object on stdout.

## AI wrapper (`install.sh --harness`)

| Destination                     | Command                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------- |
| `/tmp/ai-cursor/.cursor/skills` | `bash scripts/install.sh --harness cursor --target /tmp/ai-cursor --yes --json` |
| `/tmp/ai-pi/.pi/skills`         | `bash scripts/install.sh --harness pi --target /tmp/ai-pi --yes --json`         |
| User cursor/pi skills           | `bash scripts/install.sh --harness cursor\|pi --user --yes`                     |

The wrapper nests under `.cursor/skills` or `.pi/skills` unless the path already ends in a skills directory. `.` and any other relative `--target` anchor to this checkout, not the current working directory. `--user` overrides `--target` and warns on stderr. Public `install-cursor.sh --target /tmp/test-cursor` remains flat.

### Cursor component modes

The default `--components skills` is explicitly a partial installation. To install skills, rules, agents and hooks transactionally into a project root:

```bash
bash scripts/install.sh --harness cursor --components full --target /tmp/ai-cursor --yes --json
```

A full target is the project root, not its skills directory. Full dry-run writes nothing; uninstall uses the full manifest and retains foreign or changed resources. The Cursor plugin remains the native distribution for the complete harness.

`--user --components full` targets `~/.cursor` and is scope-aware, because Cursor reads different surfaces per scope:

| Component                 | Project scope `<project>/.cursor` | User scope `~/.cursor` (from `~/.autoworkspace`)                 |
| ------------------------- | --------------------------------- | ---------------------------------------------------------------- |
| `skills/*`                | absolute symlink                  | relative directory symlink                                       |
| `agents/*.md`             | absolute symlink                  | relative file symlink                                            |
| `rules/autoworkspace.mdc` | absolute symlink                  | **omitted** — user rules live in Customize → Rules               |
| `hooks.json`              | absolute symlink                  | relative symlink; runtime JSON uses `python3 hooks/...` commands |
| `hooks/*.py`              | absolute symlink                  | relative file symlink                                            |

To apply the execution contract globally, paste the whole rule into Customize → Rules (Cursor keeps user rules in Settings and syncs them with the account, so no file can carry them). The pasted text keeps its YAML frontmatter (`description`, `alwaysApply: true`), like any other user rule:

```bash
bash scripts/cursor-user-rule.sh --copy   # whole rule, frontmatter included
```

The JSON result reports `scope`, `omitted`, `notes` and (on upgrades) `pruned`. A pre-existing foreign `~/.cursor/hooks.json` is never overwritten: the install fails closed with a `foreign file conflict`. To get the execution contract globally, paste `rules/autoworkspace.mdc` into Customize → Rules.

## Pi notes

Pi loads project skills from `.pi/skills/` and user skills from `~/.pi/agent/skills/`. Source: [Pi Configuration](https://pi.dev/docs/latest/configuration). Skill loading behavior: [Skills](https://pi.dev/docs/latest/skills).

After install or update of user-level skills, run `/reload` (or start a new Pi session) so `<available_skills>` picks up the catalog.

Quickstart (sync the runtime once, then install project and user surfaces; the last line is the idempotent user rerun):

```bash
bash scripts/runtime-sync.sh sync
bash scripts/install-pi.sh
bash scripts/install-pi.sh --user --yes --json
bash scripts/install.sh --harness pi --target /tmp/ai-pi --yes --json | jq .installed
bash scripts/install-pi.sh --user --yes --json | jq '{installed,changed,skipped}'
```

## Verified release bootstrap

With `gh`, `uv` and the selected harness available, this one-line flow clones the installer at an immutable tag, downloads the release assets, verifies SHA-256 and provenance before extraction, installs, and runs the doctor:

```bash
git clone --depth 1 --branch v7.1.1 https://github.com/Soluciones-Alexendros/autoworkspace.git /tmp/autoworkspace-7.1.1 && bash /tmp/autoworkspace-7.1.1/scripts/bootstrap.sh --version 7.1.1 --harness cursor --target /path/to/project --json
```

Use `--harness pi` for the bootstrap flow, or the simpler native `pi install git:…@vX.Y.Z` command above. `--dry-run` performs no writes. A checksum, attestation, extraction or doctor failure prevents installation or triggers owned-resource rollback. No `curl | bash` is used.

## Release readiness vs publication

Local readiness aggregates deterministic and native gates; it does **not** create tags or releases:

```bash
make readiness
# requires AW_NATIVE_OPT_IN=1 for model e2e lanes; exit 3 (blocked/not_run) fails readiness
```

Publication remains a separate, operator-authorized step (`project-publish`). The GitHub `release` workflow uploads attested assets and runs a post-release smoke (download → checksum → attestation → bootstrap Pi/Cursor without models). A green smoke after an unauthorized local readiness run is not closure GO.

## Execution and privileges

Harnesses only need `SKILL.md` (plus `references/` / `scripts/` as linked). Mutating product operations are declared in `tools/execution/registry.yaml` and invoked via `run_registered` with approval — not via per-skill `execution.yaml` (forbidden under `skills/`). Skills may set `metadata.execution: <tool_id>`. `allowed-tools` is a catalog privilege ceiling by `metadata.type` (see ADR-0017); it does not authorize Cursor tools by itself.
