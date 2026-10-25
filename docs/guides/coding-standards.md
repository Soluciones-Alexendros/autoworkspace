# Estándares de código

### Propósito de este documento

- **Objetivos:** Convenios transversales y por stack (nombres de scripts, locks, docs). Homogeneiza contratos, no el lenguaje.
- **Estructura:** Esta meta-sección → Transversal → bloques por stack (TS / Rust / Infra) → Docs (árbol + ADR + meta-sección).
- **Contenido a integrar según contexto:** Borra los bloques de stacks que no uses. Añade el del producto (Astro, Python skills, Go…). Los **nombres** de script/job son el contrato; las herramientas son ejemplo.

Homogeneizamos **nombres y contratos**, no el lenguaje.

## Transversal

- Conventional Commits; ramas `feat/` `fix/` `chore/` `docs/` `ci/` `deps/`.
- Español en docs, PRs y mensajes a humanos.
- Sin secretos en el árbol. Placeholders solo en `.env.example`.
- PRs pequeños. Squash a `main`.
- CODEOWNERS: `* @Alexendros` (añade equipos cuando existan).

## TypeScript / pnpm

Scripts canónicos (nombres, no implementación):

```text
format:check · lint · typecheck · test · test:coverage · build · smoke
```

- Lockfile `pnpm-lock.yaml` commiteado.
- CI con `--frozen-lockfile`.
- Format (Prettier u equivalente) en check, no solo en write local.

## Rust / Cargo

```text
cargo fmt --check
cargo clippy -- -D warnings
cargo test
```

- `Cargo.lock` commiteado en binarios y workspaces de producto.
- Fixtures sintéticos; sin PII real.
- Audit/deny semanal según el repo (modelo zedazo).

## Infra / Makefile

```text
make lint
make typecheck
make validate
make test
```

- `actionlint` sobre `.github/workflows`.
- Dry-run de stacks; nada que mute prod desde un PR de feature.

## Docs

- Árbol `docs/` de la plantilla. No sueltes markdown suelto en la raíz salvo los resúmenes pactados.
- ADRs: `ADR-NNNN-titulo-kebab.md` con Contexto, Decisión, Consecuencias, Prioridad P0/P1, Checklist de implementación, Alternativas.
- Todo markdown contractual lleva, tras el H1, la sección **Propósito de este documento** (Objetivos / Estructura / Contenido a integrar). Excepción: `CHANGELOG.md` (Keep a Changelog). Detalle en [REUTILIZACION.md](../REUTILIZACION.md).
