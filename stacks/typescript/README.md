# Stack TypeScript / pnpm

### Propósito de este documento

- **Objetivos:** Referencia de nombres de script y caller CI para repos Node (Next/SaaS/CLI). No aplastar el runtime.
- **Estructura:** Esta meta-sección → scripts `package.json` → Makefile → Coverage → e2e → archivos del directorio.
- **Contenido a integrar según contexto:** Copia `ci.yml` a `.github/workflows/ci.yml` y pineá el SHA de `reusable-node`. Cambia herramientas (Vitest vs Jest, Next vs otro). No uses el `ci.yml` de este canon tal cual. `run-build: true` si hay artefacto.

Referencia para repos web/SaaS/CLI en Node.

## Scripts canónicos (`package.json`)

```json
{
  "scripts": {
    "format:check": "prettier --check .",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:coverage": "vitest run --coverage",
    "build": "pnpm -r build",
    "smoke": "bash scripts/smoke.sh",
    "check:env": "node scripts/check-env.mjs"
  }
}
```

Herramientas (Prettier, ESLint, Vitest, Next, Astro) son **ejemplo**. Los **nombres** de script son el contrato.

## Makefile (cuerpo de producto)

```make
lint:
	pnpm format:check && pnpm lint && pnpm typecheck

test:
	pnpm test:coverage

smoke:
	pnpm smoke

validate:
	pnpm check:env
```

## Coverage

- Default del reusable: **80%** (`coverage-threshold`). Gate opcional ≥70% hasta suite estable ([ADR-0007](../../docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md)).
- Paquetes críticos (auth, billing, crypto): 80% documentado en `docs/guides/testing.md` del producto.

## e2e (opcional)

Input `e2e: true` en el caller. No sustituye a `smoke`. El check required sigue siendo solo `ci-gate`.

## Archivos de este directorio

- `ci.yml` — caller `pipeline` + `ci-gate` → `reusable-node.yml@SHA`
