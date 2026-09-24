# AGENTS.md — contrato para Mantenedor y agentes

### Propósito de este documento

- **Objetivos:** Contrato operativo para agentes y Mantenedor: fuentes de verdad, autonomía, gates, DoD. En un producto, el mismo contrato de flota + hechos de *ese* workspace.
- **Estructura:** Esta meta-sección → §1 Rol → §2 Fuentes → §3 Ficha → §4 Autonomía → §5 Working agreement → §6 Comandos → §7 Zonas prohibidas → §8 Definition of Done → §9 Hechos del workspace.
- **Contenido a integrar según contexto:** Copia §1–8. Reescribe **solo** §9 (stack, validador, CODEOWNERS, perfiles). No reabras decisiones cerradas. No pegues secretos ni URLs de prod reales.

**Destinatarios:** agentes de código y el rol Mantenedor que trabajen en **este canon** o en un repo que lo haya adoptado.  
**Idioma:** español en commits, PRs y mensajes a humanos.

Copia este archivo a la raíz de cada repo de producto y ajusta solo la sección «Hechos del workspace». El resto es el contrato de flota.

---

## 1. Rol

- El humano dirige, revisa diffs y fusiona. El agente implementa una unidad cohesiva por sesión.
- Una sesión = un PR pequeño. CI verde antes de pedir revisión.
- No reabras decisiones cerradas del estándar (Renovate único, cobertura por defecto, automerge humano, idioma de docs, orden de gates).

## 2. Fuentes de verdad (orden)

1. `README.md` del repo en el que trabajas
2. Este archivo
3. `ARCHITECTURE.md` y `docs/architecture/`
4. ADRs en `docs/architecture/decisions/` (los Accepted ganan)
5. `CONTRIBUTING.md` y `docs/guides/`
6. En este canon: `docs/REUTILIZACION.md` para rollout a repos existentes

No inventes requisitos. Si falta ancla, paras y preguntas.

## 3. Ficha de unidad de trabajo

```
Objetivo: <resultado verificable>
Traza: <ADR / issue / sección de docs>
Alcance: <archivos>
Exclusiones: <qué no harás>
Pruebas: make validate && make test && make smoke
Criterio de cierre: CI verde + Definition of Done
```

## 4. Autonomía

**Puedes sin preguntar**

- Implementar lo ya especificado (issue, ADR Accepted, guía)
- Tests que fijan comportamiento aceptado
- Corregir lint/format/CI causados por tu cambio
- Refactors locales que no cambien el contrato público

**Requiere confirmación**

- Dependencia nueva o bump **major**
- Cambiar workflows, CODEOWNERS, Renovate o protección de `main`
- Alterar un ADR Accepted (abre uno nuevo que lo sustituya)
- Secretos, credenciales, deploy a producción
- Automerge: nunca en PRs humanos/agentes sin label `automerge`

## 5. Working agreement de la flota

- `main` solo recibe PR verde + revisión. Sin push directo.
- Gates CI en este orden: `quality` → `test` → `build` → `smoke` (`e2e` opcional en webs). `build` **no se declara** si no hay artefacto ([ADR-0003](docs/architecture/decisions/ADR-0003-job-build-y-required-checks.md)).
- En **este** canon no hay runtime: `quality` valida estructura, `test` es el hook documentado, `smoke` ejecuta `scripts/smoke.sh`.
- En repos de producto, `test` incluye unit/function. Coverage **≥70%** (80% en críticos) es gate **opcional** cuando la suite es estable ([ADR-0007](docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md)).
- Bot de deps: **solo Renovate** (GitHub App a nivel org, [ADR-0004](docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)). No añadas `.github/dependabot.yml` de version-updates. Dependabot Alerts ON.
- Secret scanning + push protection: prerrequisito org ([ADR-0005](docs/architecture/decisions/ADR-0005-secret-scanning-org.md)). No los desactives.
- `.env` nunca se commitea. `.env.example` solo con placeholders documentados.
- Homogeneiza **nombres** de jobs y la carpeta `.github/`; no aplastes el stack (TS/pnpm, Rust/Cargo, infra/Makefile).

## 6. Comandos

```bash
make validate   # integridad de estructura / contratos
make lint       # quality local (format, lint, types — según stack)
make test       # unit + coverage
make smoke      # pocas comprobaciones post-build, sin prod real
```

Snippets por stack: `stacks/typescript`, `stacks/rust`, `stacks/infra`.

## 7. Zonas que no se tocan a ciegas

- Secretos, tokens, `.env` reales, keys de producción
- Settings de org u otros repos (salvo que el humano lo pida de forma explícita)
- Archivados y forks externos
- Historial (no force-push, no rewrites de `main`)
- Deploy a producción sin aprobación explícita

## 8. Definition of Done

- Criterios de la traza cumplidos
- `make validate` + `make test` + `make smoke` en verde (y `build`/`e2e` si aplican)
- Docs canónicas actualizadas si cambia el contrato
- `CHANGELOG.md` `[Unreleased]` si el cambio es visible para consumidores
- Sin secretos en el diff
- PR en español, checklist de la plantilla marcado

## 9. Hechos de este workspace (repo-standard)

- Producto de plataforma, no app. No hay `package.json` / `Cargo.toml` de runtime.
- El validador de este canon es `scripts/check-structure.sh`.
- CODEOWNERS: `* @Alexendros`.
- Perfiles: P0 Base (todo repo activo), P1 Producto (runtime + env + smoke + runbooks), P2 Público (CoC, SUPPORT, topics ricos).
- Gold de origen: `website-landingpage-template`, `zedazo`, `saas-afiladocs`, `miwebsite-alexendrosdev`, `infraestructura-stack`.
