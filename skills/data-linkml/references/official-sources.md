# Official sources — canonical list and verification policy

Verified on 2026-11-12. Canonical list for the skill; extend only with
official or reputable sources, recording the verification date.

## Primary (official)

| # | Source | URL |
| - | ------ | --- |
| F1 | LinkML documentation | https://linkml.io/linkml/ |
| F2 | `linkml` tools repo / PyPI | https://github.com/linkml/linkml · https://pypi.org/pypi/linkml (1.12.1, Apache-2.0, Python ≥3.10) |
| F3 | Metamodel and specification | https://github.com/linkml/linkml-model |
| F4 | Install guide | https://linkml.io/linkml/intro/install.html |
| F5 | CLI `linkml validate` | https://linkml.io/linkml/cli/validate.html |
| F6 | CLI `linkml lint` | https://linkml.io/linkml/cli/lint.html |
| F7 | CLI `linkml generate` + generators | https://linkml.io/linkml/cli/generate.html · https://linkml.io/linkml/generators/ |
| F8 | Data validation | https://linkml.io/linkml/data/validating-data.html |
| F9 | Data conversion | https://linkml.io/linkml/data/conversion.html |
| F10 | `gen-project` | https://linkml.io/linkml/generators/project-generator.html |
| F11 | Ecosystem | https://linkml.io/linkml/ecosystem.html |
| F12 | Support repos | linkml/linkml-runtime · linkml/linkml-map · linkml/linkml-store · linkml/schemasheets · linkml/schema-automator |
| F13 | Arch official repos | https://archlinux.org/packages/search/json/?name=python · `python` (core), `python-pip` (extra) |
| F14 | AUR | https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=python-linkml — no package exists |
| F15 | Arch Wiki · Python | https://wiki.archlinux.org/title/Python — venv recommended |
| F16 | PyPI metadata `linkml==1.12.1` | https://pypi.org/pypi/linkml/1.12.1/json — no extras; wheels for linux x86_64 |

## Context7 (up-to-date docs lookup)

- `/websites/linkml_io_linkml` — official docs (high reputation)
- `/linkml/linkml` — toolchain repo
- `/linkml/linkml-model` — metamodel

Use context7 (resolve library id → query docs) before asserting that an API,
version, config key or flag exists.

## Internal references (read-only, by agreement)

- Notion page "LinkML" (project «Diagnosis y Actualización del
  Español-Castellano»): real case with LinkML 1.12.1 schema, 19 tables,
  validators V01–V25. Read-only; never edited from this skill.
- Notion skill "Modelar y trabajar con LinkML" and its child pages
  ("Ecosistema y fuentes LinkML", "Guía práctica y pruebas LinkML"): internal
  procedure and practice guide; reference material, not executed evidence.

## Verification policy

1. Do not assert a command, flag, version, generator or URL without checking
   it against the installed version (`--help`, `--version`), the official docs
   or context7.
2. When docs and installed behavior differ, the executed version wins; explain
   the discrepancy in the cycle record.
3. Never invent data, relationships or execution results; record
   "not executed" honestly.
