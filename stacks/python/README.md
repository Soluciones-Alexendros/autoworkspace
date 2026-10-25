# Stack Python / uv

### Propósito de este documento

- **Objetivos:** Nombres de comandos uv/ruff/mypy/pytest y plantilla caller para repos Python de la flota.
- **Estructura:** Esta meta-sección → comandos → Coverage → Smoke → archivos del directorio.
- **Contenido a integrar según contexto:** Copia `ci.yml` a `.github/workflows/ci.yml` y pineá el SHA del reusable-python del tag `repo-standard ≥2.0`. Ajusta `coverage-threshold` mientras la suite no sea estable ([ADR-0007](../../docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md)).

Referencia para skills/agents y CLIs Python con **uv**.

## Comandos canónicos

```bash
uv sync --frozen
uv run ruff format --check .
uv run ruff check . --select E,F,W,I,B,UP,SIM,C90,N,PL,RUF --config 'lint.mccabe.max-complexity = 10'
uv run mypy --strict .
uv run pytest --cov --cov-fail-under=80
uv build
make smoke   # o scripts/smoke.sh
```

## Coverage

- Default del reusable: **80%**. Baja el input del caller si la suite aún no es estable.
- Críticos (auth, parsers, crypto): documenta 80% en la guía del producto.

## Archivos de este directorio

- `ci.yml` — caller con `pipeline` + `ci-gate` → `reusable-python.yml@SHA`
