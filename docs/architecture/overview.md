# Overview del canon

```
                 repo-standard (este repo)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    contratos docs    nombres CI     metadata GitHub
    (P0/P1/P2)     quality/test/     CODEOWNERS,
                    build/smoke      Renovate, templates
                          │
                          ▼
              stacks/ (TS · Rust · infra)
                    solo snippets
```

## Límites del sistema

**Dentro**

- Árbol canónico de raíz y `.github/`
- Arquitectura de documentación (`docs/`)
- Contrato de agentes (`AGENTS.md`)
- Fachada `Makefile` (`lint` `test` `smoke` `validate`)
- Política de deps (Renovate) y automerge
- Perfiles P0 / P1 / P2

**Fuera**

- Código de negocio de cada producto
- Hosting, DNS, secretos de Environments
- Settings de organización (rulesets, billing, teams)
- Repos archivados y forks externos

## Flujos

1. **Repo nuevo:** GitHub Template → ajustar README/env/CI del stack → PR a `main`.
2. **Repo existente:** checklist de [REUTILIZACION.md](../REUTILIZACION.md) en un único PR.
3. **Cambio del canon:** ADR si toca una decisión; snippets de `stacks/` si toca un runtime; bump de contrato reflejado en `CHANGELOG.md`.

## Relación con los gold

El diseño fusiona lo que ya funciona:

| Fuente | Qué se hereda |
|--------|----------------|
| `website-landingpage-template` | Template GitHub, CI limpio, idea de `REUTILIZACION.md` |
| `zedazo` | Governance: AGENTS, ARCHITECTURE, CoC, CODEOWNERS, ADRs |
| `saas-afiladocs` | `check:env`, actionlint, runbooks, SUPPORT (P2) |
| `miwebsite-alexendrosdev` | SECURITY + CONTRIBUTING + AGENTS + issue forms |
| `infraestructura-stack` | Makefile fachada, ADRs, runbooks de infra |

## Stacks

Los jobs se llaman igual; los comandos no:

| Stack | Quality típico | Smoke típico |
|-------|----------------|--------------|
| TypeScript / pnpm | format, lint, typecheck | URL `/` o `/api/health` |
| Rust / Cargo | fmt, clippy `-D warnings` | binario `--help` / `version` |
| Infra / Makefile | `make lint` `typecheck` `actionlint` | `make validate` + dry-run |

Fragmentos listos para copiar: [`stacks/`](../../stacks/).
