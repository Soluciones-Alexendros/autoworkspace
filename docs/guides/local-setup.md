# Setup local

### Propósito de este documento

- **Objetivos:** Cómo clonar y dejar el repo listo para el primer PR (canon o producto).
- **Estructura:** Esta meta-sección → setup de este repo → setup de producto por stack → hooks recomendados.
- **Contenido a integrar según contexto:** En producto, deja un solo camino (el del stack). Sustituye versiones (Node/pnpm, MSRV). Si naciste de la plantilla, declara comandos reales o usa el bootstrap ([ADR-0011](../architecture/decisions/ADR-0011-bootstrap-desde-plantilla.md)). Nunca commitees `.env`.

## Este canon

```bash
git clone https://github.com/Soluciones-Alexendros/repo-standard.git
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
