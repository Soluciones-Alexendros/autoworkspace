# Plan 7.0.2 — Instalabilidad Pi

Contrato oficial de Pi: proyecto `.pi/skills`, usuario `~/.pi/agent/skills` ([Pi Configuration](https://pi.dev/docs/latest/configuration)).

## Hecho en este corte

- `scripts/install.sh` ancla `.` y el resto de rutas relativas al checkout. Un segmento `..` sale con código 2. `--user` gana a `--target` y avisa en stderr.
- `scripts/lib/link-skills.sh` aplica la misma prioridad de `--user`, comprueba que el ancestro del destino de usuario es escribible sin crear directorios, y exige un symlink absoluto por recurso planeado. `VERSION` es `7.0.2`.
- `scripts/tests/test_install.sh` cubre el anclaje desde `/tmp`, la idempotencia Pi, el dry-run, un `HOME` falso y los symlinks absolutos.
- Versión `7.0.2` en `package.json`, `package-lock.json`, `tools/pyproject.toml`, `tools/uv.lock` y la línea de versión del README. El changelog queda en `[Unreleased]`.
- Quickstart Pi en `docs/harness-setup.md`. Tres líneas en la sección de template de GitHub de `templates/product/README.md`.

## Fuera

- Tag `v7.0.2`, `--release-gate` y `project-publish`.
- `metadata.version` de las skills y `docs/architecture/skill-index-7.0.0.json`.
- Canónico de proyecto `.pi/agent/skills` y `.pi/hooks/`.

## Verificación

```bash
make validate && make test && make smoke
bash run-validation.sh
```
