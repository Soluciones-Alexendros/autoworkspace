# Stack infra / Makefile

### Propósito de este documento

- **Objetivos:** Fachada Makefile y caller `reusable-static` para repos de configuración/imágenes.
- **Estructura:** Esta meta-sección → comandos canónicos → Quality → Qué no va aquí → archivos.
- **Contenido a integrar según contexto:** Copia `ci.yml` y ajusta `quality-command` / `test-command` / `smoke-command`. Lista las tools reales (`terraform`, `actionlint`, …). Casi nunca hay `build-command`. Cero credenciales de cloud.

Referencia para repos de configuración, imágenes y automatización (patrón `infraestructura-stack`).

## Comandos canónicos

La fachada **es** el Makefile:

```bash
make lint
make typecheck
make validate
make test
make smoke
```

`smoke` en infra = `make validate` + dry-run de un stack (nunca apply a prod).

## Quality

- Linters del lenguaje que use el repo (JS/TS de scripts, shellcheck, terraform fmt, …).
- `actionlint` sobre `.github/workflows` (también en `security.yml` de la flota).
- Este canon: actionlint + `scripts/check-structure.sh`.

## Qué no va aquí

- Credenciales de cloud.
- `terraform apply` / mutaciones reales en un PR.
- Runners self-hosted hasta que existan labels sanas y documentadas.
- Herramientas nuevas de link-check: solo si el repo ya las tiene (`link-check-command`).

## Archivos de este directorio

- `ci.yml` — caller `pipeline` + `ci-gate` → `reusable-static.yml@SHA`
