# Setup local

## Este canon

```bash
git clone https://github.com/Iniciativas-Alexendros/repo-standard.git
cd repo-standard
make validate
make test
make smoke
```

Dependencias: `git`, `bash`, `make`. No hay `pnpm install` ni `cargo build`.

## Repo de producto (cuando copies el estándar)

1. Clona el repo de producto, no este.
2. Copia `.env.example` → `.env` y rellena placeholders (nunca commits de `.env`).
3. Instala el toolchain del stack:
   - **TS:** Node 22 + pnpm (versión de `packageManager` en `package.json`), `pnpm install --frozen-lockfile`
   - **Rust:** toolchain estable / MSRV documentado, `cargo test`
   - **Infra:** las tools que liste el Makefile (`terraform`, `actionlint`, …)
4. Arranca con el comando del README del producto.
5. Antes del primer PR: `make lint && make test && make smoke`.

## Hooks (recomendado en P1)

Si el producto tiene pre-commit / gitleaks (patrón landing y zedazo), instálalos. Este canon no impone un framework de hooks; sí impone **no commitear secretos**.
