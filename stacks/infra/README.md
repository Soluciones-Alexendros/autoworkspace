# Stack infra / Makefile

### Propósito de este documento

- **Objetivos:** Fachada Makefile y quality para repos de configuración/imágenes (sin apply a prod en un PR).
- **Estructura:** Esta meta-sección → comandos canónicos → Quality → Qué no va aquí.
- **Contenido a integrar según contexto:** Lista las tools reales (`terraform`, `actionlint`, …). `smoke` = validate + dry-run. Casi nunca hay job `build` de aplicación. Cero credenciales de cloud en el snippet.

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
- `actionlint` sobre `.github/workflows` (también corre en `security.yml` de la flota).

## Qué no va aquí

- Credenciales de cloud.
- `terraform apply` / mutaciones reales en un PR.
- Runners self-hosted hasta que existan labels sanas y documentadas.
