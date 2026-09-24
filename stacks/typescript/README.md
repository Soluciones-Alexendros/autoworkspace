# Stack TypeScript / pnpm

Referencia para repos web/SaaS/CLI en Node. Copia los snippets a `.github/workflows/ci.yml`; no uses el `ci.yml` de este canon tal cual.

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

- Gate del job `test`: ≥70% líneas.
- Paquetes críticos (auth, billing, crypto): 80% documentado en `docs/guides/testing.md` del producto.

## e2e (opcional)

Job `e2e` con Playwright Chromium, `needs: [build]`. Required en `main` para webs P1. No sustituye a `smoke`.

## Archivos de este directorio

- `ci.quality.snippet.yml` — steps de format/lint/typecheck
- `ci.smoke.snippet.yml` — job smoke post-build
