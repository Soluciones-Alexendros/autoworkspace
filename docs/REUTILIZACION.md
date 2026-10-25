# Reutilizar el estándar en un repo existente

### Propósito de este documento

- **Objetivos:** Cómo **alinear** un repo que ya existe (un PR, sin clonar a ciegas): orden, qué copiar, Dependabot→Renovate, protection, checklist §8.
- **Estructura:** Esta meta-sección → Antes de tocar nada → Orden → Copiar vs adaptar → Meta-sección obligatoria → Dependabot → Protección → Checklists P0/P1/P2 → Oleadas → Verificación.
- **Contenido a integrar según contexto:** En un producto ya alineado puedes dejar este archivo como «cumple el canon en `autoworkspace` ≥6.0.0 (ADR-0016)» + checklist marcado, o conservarlo entero. No ejecutes oleadas desde el PR del producto. No cambies settings de org.

Objetivo: **alinear**, no clonar a ciegas. El repo de producto conserva su stack, historial y nombre. Este canon aporta contratos (archivos, nombres de jobs, docs, Renovate).

Haz **un PR por repo**. Sin force-push. Checklist = plantilla §8.

Repo nuevo desde esqueleto: `gh repo create Soluciones-Alexendros/<n> --private --clone && cp -a templates/repo/. <n>/` ([ADR-0016](./architecture/decisions/ADR-0016-autoworkspace-host-del-canon.md)). Merge de flota: `gh pr merge --auto --squash`; required check: `ci-gate` (sin etiqueta `automerge`).

## Antes de tocar nada

1. Confirma que el repo está **activo** (no archivado, no fork externo tipo `voicebox`).
2. Elige perfil: **P0** (mínimo), **P1** (hay runtime), **P2** (público / community).
3. Inventaría lo que ya existe (README, CI, Dependabot vs Renovate, `docs/`). No borres runbooks ni ADRs vivos: muévelos al árbol canónico.
4. No cambies settings de org ni de otros repos.

## Orden de trabajo recomendado

1. Archivos de raíz P0 (`README`, `LICENSE`, `SECURITY`, `CONTRIBUTING`, `CHANGELOG`).
2. `.github/CODEOWNERS`, plantillas de issue/PR.
3. CI: copia `stacks/<stack>/ci.yml` a `.github/workflows/ci.yml` y pineá el SHA del reusable en `Soluciones-Alexendros/autoworkspace` ([ADR-0014](./architecture/decisions/ADR-0014-release-please-y-packaging-por-stack.md)). El único check required es `ci-gate` ([ADR-0013](./architecture/decisions/ADR-0013-check-unico-ci-gate.md)).
4. Quita version-updates de Dependabot si existen; deja o añade `.github/renovate.json` (copia el de este canon y recorta `packageRules` al stack). La App Renovate a nivel org es prerrequisito ([ADR-0004](./architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)).
5. Árbol `docs/` P1 + `AGENTS.md` + `ARCHITECTURE.md` + `.env.example`. Cada markdown contractual lleva la meta-sección (abajo).
6. Runbooks: adapta deploy/rollback/secretos al hosting real (Vercel, Docker, Cargo release…).
7. En el PR, pega el checklist §8 de abajo y márcalo con lo que **este** repo ya cumple.

## Qué copiar vs qué adaptar

| Pieza                                     | Acción                                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| `AGENTS.md` (secciones 1–8)               | Copiar; reescribe «Hechos del workspace»                                                    |
| `ARCHITECTURE.md`                         | Reescribir: 1–2 páginas del _producto_ + link a `docs/architecture/`                        |
| `docs/architecture/decisions/template.md` | Copiar                                                                                      |
| `docs/guides/*`                           | Adaptar comandos al stack                                                                   |
| `docs/runbooks/*`                         | Adaptar a hosting / secretos reales (sigue sin commitear valores)                           |
| `.github/workflows/ci.yml`                | **No** copies el de este canon tal cual: usa `stacks/<stack>/ci.yml` (pin SHA del reusable) |
| `.github/renovate.json`                   | Copiar base; quita reglas que no apliquen                                                   |
| `scripts/check-structure.sh`              | Opcional en producto. Si lo usas, cambia la lista de archivos a los del producto            |
| `scripts/smoke.sh`                        | Sustituye el demo por health/rutas/`--help`                                                 |
| `Makefile`                                | Conserva targets `lint` `test` `smoke` `validate`; cambia el cuerpo                         |
| `LICENSE`                                 | No pises una licencia ya elegida (dual Apache/MIT, GPL, privativa)                          |
| `CODE_OF_CONDUCT.md`                      | Obligatorio en P2; recomendado en P1                                                        |
| `SUPPORT.md`                              | Solo P2 / SaaS                                                                              |

## Meta-sección obligatoria en docs de producto

Al alinear o crear desde plantilla, **cada** markdown contractual debe incluir, **dentro del propio archivo** y preferiblemente justo después del H1, esta sección estable:

```markdown
### Propósito de este documento

- **Objetivos:** …
- **Estructura:** …
- **Contenido a integrar según contexto:** …
```

Aplica a: raíz (`README`, `AGENTS`, `ARCHITECTURE`, `SECURITY`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SUPPORT` si existe), `docs/**` (README, architecture, guides, runbooks, este archivo), plantillas de issue/PR si son `.md`, y `stacks/**/*.md` si las copias.

**No** aplica a `LICENSE`, JSON/YAML, scripts ni binarios.

**Excepción:** `CHANGELOG.md` sigue Keep a Changelog. No insertes una sección larga: un párrafo breve al inicio o ninguna. Documenta la excepción en el PR si omites el párrafo.

La meta-sección es de **plantilla usable**: corta, accionable. Si el doc ya tenía intro, fusiónala aquí. No copies el texto de este canon: rellena objetivos/estructura/placeholders del _producto_ (web vs CLI vs skills vs infra). Qué no copiar tal cual: el `ci.yml` estático de este canon, runbooks de «este repo no se despliega», §9 de AGENTS ajeno.

## Dependabot → Renovate

1. Si hay `.github/dependabot.yml` con `package-ecosystem` de npm/cargo/actions/docker **para version-updates**, elimínalo en el mismo PR que añade Renovate.
2. No desactives Dependabot **Alerts** (seguridad) a nivel repo/org ([ADR-0004](./architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)).
3. Renovate: schedule madrugada `Europe/Madrid`, automerge `patch`+`minor`, minors agrupados, label `dependencies`, **sin** automerge de majors.
4. Sin la GitHub App Renovate instalada en la org (o habilitada en el repo), el JSON no genera PRs: es prerrequisito humano, no lo activa el agente.

## Protección de `main` (lo hace un humano en Settings)

El agente **no** cambia rulesets de org ni de otros repos. El contrato versionado (runbook + script `gh` / org rulesets) está en [ADR-0002](./architecture/decisions/ADR-0002-proteccion-metadatos-como-codigo.md). Hasta que exista, el Mantenedor deja:

- PR obligatorio. **0 approvals**. Sin bypass (ni admin). Squash-merge ([ADR-0012](./architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md))
- Check required: solo **`ci-gate`** (GitHub Actions, `integration_id` 15368) ([ADR-0013](./architecture/decisions/ADR-0013-check-unico-ci-gate.md))
- Conversaciones resueltas, historia lineal, sin force-push
- Allow auto-merge ON; auto-delete head branches ON
- Etiqueta opcional `hold` para excluir un PR del auto-merge
- No desactives secret scanning / push protection de org ([ADR-0005](./architecture/decisions/ADR-0005-secret-scanning-org.md))

## Checklist §8 — P0

- [ ] README + LICENSE + CHANGELOG + SECURITY + CONTRIBUTING
- [ ] `.github/workflows/ci.yml` con `pipeline` + `ci-gate`
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
- [ ] Bot de deps = Renovate (JSON + App org habilitada; sin Dependabot version-updates)
- [ ] ISSUE + PR templates
- [ ] Meta-sección «Propósito de este documento» en los markdown contractuales

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
