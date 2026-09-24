# Stack Rust / Cargo

### Propósito de este documento

- **Objetivos:** Nombres de comandos Cargo y fachada Makefile para CLIs/workspaces de la flota.
- **Estructura:** Esta meta-sección → comandos → Makefile típico → Coverage → extra P1 → Smoke.
- **Contenido a integrar según contexto:** Sustituye `APP` por el binario real. Ajusta `--workspace` si es crate único. Coverage con `cargo llvm-cov` cuando la suite sea estable. No pegues `CARGO_HOME` ni tokens.

Referencia para CLIs y workspaces Cargo (patrón zedazo, recortado a los nombres de la flota).

## Comandos canónicos

```bash
cargo fmt --check
cargo clippy --workspace -- -D warnings
cargo test --workspace
```

Makefile típico:

```make
lint:
	cargo fmt --check && cargo clippy --workspace -- -D warnings

test:
	cargo test --workspace

smoke:
	./target/debug/APP --help

validate:
	cargo check --workspace
```

## Coverage

- Por defecto ≥70% (`cargo llvm-cov` u equivalente).
- Críticos (parsers, crypto, dominio puro): 80%.

## Extra P1 (no obligatorio en el primer PR de alineación)

- `cargo audit` / `cargo deny` en `security.yml` semanal.
- MSRV job si el crate se publica.

## Smoke

Binario `--help` o `version` / `doctor` con exit 0. Sin red de producción. Fixtures sintéticos.
