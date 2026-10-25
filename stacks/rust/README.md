# Stack Rust / Cargo

### Propósito de este documento

- **Objetivos:** Nombres de comandos Cargo y caller CI para CLIs/workspaces de la flota.
- **Estructura:** Esta meta-sección → comandos → Makefile típico → Coverage → Extra → Smoke → archivos.
- **Contenido a integrar según contexto:** Copia `ci.yml` y pineá el SHA de `reusable-rust`. Sustituye el binario real. Ajusta `msrv` y `clippy-pedantic`. Coverage con `cargo llvm-cov` (default 80%).

Referencia para CLIs y workspaces Cargo (patrón zedazo, recortado a los nombres de la flota).

## Comandos canónicos

```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings -W clippy::pedantic
cargo test --workspace
cargo llvm-cov --workspace --fail-under-lines 80
cargo build --release --locked
```

Makefile típico:

```make
lint:
	cargo fmt --check && cargo clippy --workspace -- -D warnings

test:
	cargo test --workspace

smoke:
	./target/release/APP --help

validate:
	cargo check --workspace
```

## Coverage

- Default del reusable: **80%**.
- Críticos (parsers, crypto, dominio puro): 80% documentado.

## Extra

- `cargo deny` si existe `deny.toml`; si no, `cargo audit` (job `security` del reusable).
- Input `msrv` opcional.

## Smoke

Binario en `target/release` con `--version` o `--help`, exit 0.

## Archivos de este directorio

- `ci.yml` — caller `pipeline` + `ci-gate` → `reusable-rust.yml@SHA`
