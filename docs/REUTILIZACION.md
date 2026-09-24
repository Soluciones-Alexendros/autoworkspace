# Reutilizar el estándar en un repo existente

Objetivo: **alinear**, no clonar a ciegas. El repo de producto conserva su stack, historial y nombre. Este canon aporta contratos (archivos, nombres de jobs, docs, Renovate).

Haz **un PR por repo**. Sin force-push. Checklist = plantilla §8.

## Antes de tocar nada

1. Confirma que el repo está **activo** (no archivado, no fork externo tipo `voicebox`).
2. Elige perfil: **P0** (mínimo), **P1** (hay runtime), **P2** (público / community).
3. Inventaría lo que ya existe (README, CI, Dependabot vs Renovate, `docs/`). No borres runbooks ni ADRs vivos: muévelos al árbol canónico.
4. No cambies settings de org ni de otros repos.

## Orden de trabajo recomendado

1. Archivos de raíz P0 (`README`, `LICENSE`, `SECURITY`, `CONTRIBUTING`, `CHANGELOG`).
2. `.github/CODEOWNERS`, plantillas de issue/PR.
3. CI: renombra jobs a `quality`, `test`, `smoke` (añade `build` si hay artefacto). Reutiliza snippets de `stacks/`.
4. Quita version-updates de Dependabot si existen; deja o añade `.github/renovate.json` (copia el de este canon y recorta `packageRules` al stack).
5. Árbol `docs/` P1 + `AGENTS.md` + `ARCHITECTURE.md` + `.env.example`.
6. Runbooks: adapta deploy/rollback/secretos al hosting real (Vercel, Docker, Cargo release…).
7. En el PR, pega el checklist §8 de abajo y márcalo con lo que **este** repo ya cumple.

## Qué copiar vs qué adaptar

| Pieza | Acción |
|-------|--------|
| `AGENTS.md` (secciones 1–8) | Copiar; reescribe «Hechos del workspace» |
| `ARCHITECTURE.md` | Reescribir: 1–2 páginas del *producto* + link a `docs/architecture/` |
| `docs/architecture/decisions/template.md` | Copiar |
| `docs/guides/*` | Adaptar comandos al stack |
| `docs/runbooks/*` | Adaptar a hosting / secretos reales (sigue sin commitear valores) |
| `.github/workflows/ci.yml` | **No** copies el de este canon tal cual: usa `stacks/<stack>/ci.*.snippet.yml` |
| `.github/renovate.json` | Copiar base; quita reglas que no apliquen |
| `scripts/check-structure.sh` | Opcional en producto. Si lo usas, cambia la lista de archivos a los del producto |
| `scripts/smoke.sh` | Sustituye el demo por health/rutas/`--help` |
| `Makefile` | Conserva targets `lint` `test` `smoke` `validate`; cambia el cuerpo |
| `LICENSE` | No pises una licencia ya elegida (dual Apache/MIT, GPL, privativa) |
| `CODE_OF_CONDUCT.md` | Obligatorio en P2; recomendado en P1 |
| `SUPPORT.md` | Solo P2 / SaaS |

## Dependabot → Renovate

1. Si hay `.github/dependabot.yml` con `package-ecosystem` de npm/cargo/actions/docker **para version-updates**, elimínalo en el mismo PR que añade Renovate.
2. No desactives Dependabot **Alerts** (seguridad) a nivel repo/org.
3. Renovate: schedule madrugada `Europe/Madrid`, automerge `patch`+`minor`, minors agrupados, label `dependencies`, **sin** automerge de majors.

## Protección de `main` (lo hace un humano en Settings)

El agente **no** cambia rulesets de org. El Mantenedor debe dejar:

- PR obligatorio + ≥1 review (CODEOWNERS)
- Checks required: `quality`, `test`, `smoke` (+ `e2e` si es web P1)
- Conversaciones resueltas, historia lineal, sin bypass, sin force-push
- Allow auto-merge ON; auto-delete head branches ON
- Automerge humano solo con label `automerge`

## Checklist §8 — P0

- [ ] README + LICENSE + CHANGELOG + SECURITY + CONTRIBUTING
- [ ] `.github/workflows/ci.yml` con `quality` + `test`
- [ ] CODEOWNERS (`* @Alexendros` como mínimo)
- [ ] Description no vacía (`[tipo] — [qué hace] — [stack]`)
- [ ] ≥4 topics (tipo + stack + hosting o dominio + estado)
- [ ] `main` protegida (PR + checks)
- [ ] Auto-delete branches ON
- [ ] Allow auto-merge ON

## Checklist §8 — P1

- [ ] `docs/` con architecture + guides + runbooks
- [ ] AGENTS.md + ARCHITECTURE.md
- [ ] `.env.example` si hay config runtime
- [ ] Job `smoke` required
- [ ] Bot de deps = Renovate (sin Dependabot version-updates)
- [ ] ISSUE + PR templates

## Checklist §8 — P2

- [ ] CODE_OF_CONDUCT + SUPPORT
- [ ] Topics ≥6 + description pública clara
- [ ] `security.yml` / audit schedule
- [ ] Coverage gate publicado (≥70% flota; 80% críticos)

## Oleadas de rollout (contexto)

No las ejecutes desde este PR. Orden de la plantilla: (1) baobab / agents / webconfig, (2) ecommerce / askartask / miwebsite, (3) afiladocs / zedazo / landing-template, (4) personales activos.

## Verificación

En el repo destino, como mínimo:

```bash
make validate   # o el quality del stack
make test
make smoke
```

CI del PR en verde (`quality`, `test`, `smoke`) antes de pedir review.
