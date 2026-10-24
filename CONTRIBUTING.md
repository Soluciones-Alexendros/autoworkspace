# Contributing

### Propósito de este documento

- **Objetivos:** Cómo añadir o cambiar skills, bump de versión, gates locales y de CI, y convenciones de PR en este repositorio.
- **Estructura:** Esta meta-sección → skills → versionado → smoke → PRs → issues → planificación.
- **Contenido a integrar según contexto:** El árbol canónico de producto está en [docs/repo-standard/structure.md](docs/repo-standard/structure.md). Detalle de skill en [docs/STANDARD.md](docs/STANDARD.md).

## Adding or changing a skill

1. The directory must match the frontmatter `name` (kebab-case).
2. Frontmatter must declare `metadata.language: en` and `metadata.type: atomic|orchestrator|router|audit` — every skill is written in English.
3. Follow [docs/STANDARD.md](docs/STANDARD.md): complete frontmatter (including `type`), body ≤ 500 lines and ≤ 5000 tokens, taxonomy in [docs/TAXONOMY.md](docs/TAXONOMY.md), canonical headings.
4. No trailing whitespace — CI rejects it.
5. Record changes in [CHANGELOG.md](CHANGELOG.md).
6. Pass local validation green before the PR:

```bash
pip install -r requirements-dev.txt
make validate
# equivalent: bash run-validation.sh
```

## Severity levels (`metadata.version` bump)

| Type    | When to use                                                              | Example                                             |
| ------- | ------------------------------------------------------------------------ | --------------------------------------------------- |
| `major` | Incompatible change: restructures, removes sections, or changes behavior | Merging two skills, changing the frontmatter format |
| `minor` | Compatible new functionality: adds sections, references, or scripts      | Adding `references/new-guide.md`                    |
| `patch` | Compatible fix: typo, broken link, minor tweak                           | Fixing a URL, formatting a table                    |

Canonical: `--type major|minor|patch` (`bump.py` also accepts Spanish aliases).

The **repo** version (`package.json`) goes up on publish. A change to a released CHANGELOG.md section, `.github/workflows/release.yml`, or `tools/version/cut_tag.py` requires `package.json` to stay ahead of the last tag.

## Smoke tests

Every skill with `.py` or `.sh` executables outside `tests/` ships `scripts/tests/smoke_sh.sh`. It runs the tools on synthetic data and checks the output. CI runs it alone.

```bash
bash skills/<skill>/scripts/tests/smoke_sh.sh
```

## PRs

- Describe which skill changes and why; bump `metadata.version` when instructions change (`python3 tools/version/bump.py --auto --type <major|minor|patch>`; CI enforces it in `version.yml`).
- CI runs `validate.yml` (spec, links, coherence, tests), `version.yml` (required bump), and `quality.yml` (hygiene). All must be green.
- Do not commit residues (`__pycache__/`, `.pytest_cache/`, `.log`, `.tmp`): they are in `.gitignore` and CI rejects them when tracked by git.
- Use the PR template: [`.github/pull_request_template.md`](.github/pull_request_template.md).
- Conventional Commits. Renovate is the only dependency update bot; do not add `dependabot.yml` for version updates.

## Issues

Use the `.github/ISSUE_TEMPLATE/` templates (bug or skill proposal/improvement).

## Task planning

For multi-step projects or research tasks, keep `task_plan.md`, `findings.md`, and `progress.md` on disk.
