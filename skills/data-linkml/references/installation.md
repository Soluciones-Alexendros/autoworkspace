# Installation — Arch Linux one-shot bootstrap

## Verified inventory (2026-11-12)

| Component | Origin | Element |
| --------- | ------ | ------- |
| System | pacman (official repos, sudo) | `python` (core; includes the `venv` module) and `python-pip` (extra) |
| Isolation | `python -m venv` | Dedicated venv under the LinkML project directory: default `~/Projects/linkml/venvs/linkml`, override with `--venv-dir` |
| Libraries | pip **inside the venv** | `linkml==1.12.1` (exact pin) from `assets/requirements-linkml.txt`; transitive deps ship wheels for linux x86_64 (no compilation, no `base-devel`) |
| Alternative | Official OCI image | `docker.io/linkml/linkml` (documented, not installed by the bootstrap) |

Facts checked against official sources: there is no LinkML package in the
official Arch repos nor `python-linkml` in the AUR (F14); Arch marks system
Python as externally-managed (PEP 668), so global pip is not a supported path;
the Arch Wiki recommends an isolated venv per project (F15).

## Project directory layout

```text
~/Projects/linkml/
├── venvs/
│   └── linkml/          # venv creado por el bootstrap (pin linkml==1.12.1)
└── README.md            # nota de propósito del directorio (no versionado)
```

El bootstrap crea el directorio si falta (`mkdir -p`) y deja todos los entornos
bajo `venvs/`, de modo que un proyecto concreto puede añadir su propio venv con
`--venv-dir ~/Projects/linkml/venvs/<proyecto>` sin mezclar dependencias.

## Single script

```bash
bash skills/data-linkml/scripts/bootstrap_arch.sh                 # dry-run: prints the plan
bash skills/data-linkml/scripts/bootstrap_arch.sh --apply --verify  # installs and checks
```

Behavior:

1. Preflight: Arch Linux (`/etc/os-release`), `pacman`, `sudo`, system
   `python3` ≥ 3.10, network to PyPI. In dry-run, network is reported as
   "not checked".
2. pacman: installs `python` and `python-pip` only if missing, with explicit
   confirmation and sudo, listing exact packages.
3. venv: `mkdir -p` del directorio del proyecto y `python3 -m venv <venv-dir>`
   (por defecto `~/Projects/linkml/venvs/linkml`); actualiza pip dentro del venv.
4. pip: `-r assets/requirements-linkml.txt` (pin `linkml==1.12.1`).
5. Verify (`--verify`): `linkml --version` plus the lab cycle
   (`scripts/validate_cycle.py` on `assets/schema-template.yaml` and both
   instance files), recording versions, commands and results.
6. Summary: how to activate (`source <venv>/bin/activate`) and next steps.

Idempotent: a second run reinstalls only what is missing. Exit codes are the
canonical set (`0` OK, `1` error, `2` invalid input, `3` missing dependency,
`4` permission denied).

## Using the environment

```bash
source ~/Projects/linkml/venvs/linkml/bin/activate
linkml --version
deactivate
```

The skill's scripts accept `--venv-dir` to locate the binaries without
activating.

## Troubleshooting

| Symptom | Cause / fix |
| ------- | ----------- |
| `pip install` blocked outside venv | PEP 668 externally-managed marker on Arch; always use the venv |
| No sudo | Use `--skip-pacman` with a venv created from any Python ≥ 3.10 |
| Non-x86_64 arch without wheels | Dependencies must compile; install `base-devel` before pip, then retry |
| Network blocked | Use the OCI image route: `docker run -v ./:/work -w /work/ --rm -ti docker.io/linkml/linkml` |
| Version drift | Record the executed version in every cycle; never assert a version without checking `linkml --version` |

## Uninstall

Remove the venv (`rm -rf ~/Projects/linkml/venvs/linkml`). System packages were only added
if missing; remove them with `sudo pacman -Rs python-pip python` only if no
other project needs them — review before removing system packages.

## Official references

- https://linkml.io/linkml/intro/install.html (pip in venv, OCI image)
- https://archlinux.org/packages/search/json/?name=python
- https://wiki.archlinux.org/title/Python (venv recommendation)
