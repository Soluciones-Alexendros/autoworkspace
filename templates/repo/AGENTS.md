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

- El humano dirige y el agente implementa una unidad cohesiva por sesión.
- Una sesión = un PR pequeño. CI verde (`ci-gate`) + squash auto-merge ([ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).
- No reabras decisiones cerradas del estándar (Renovate único, cobertura por defecto, idioma de docs, orden de fases, check único `ci-gate`).

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
Criterio de cierre: ci-gate verde + Definition of Done + auto-merge squash
```

## 4. Autonomía

**Puedes sin preguntar**

- Implementar lo ya especificado (issue, ADR Accepted, guía)
- Tests que fijan comportamiento aceptado
- Corregir lint/format/CI causados por tu cambio
- Refactors locales que no cambien el contrato público
- Activar `gh pr merge --auto --squash` al abrir el PR (salvo etiqueta `hold`)

**Requiere confirmación**

- Dependencia nueva o bump **major**
- Cambiar workflows, CODEOWNERS, Renovate o protección de `main`
- Alterar un ADR Accepted (abre uno nuevo que lo sustituya)
- Secretos, credenciales, deploy a producción
- Break-glass (desactivar ruleset): solo el humano

## 5. Working agreement de la flota

- `main` solo recibe PR con `ci-gate` verde y squash-merge. Sin push directo. 0 approvals. Sin bypass admin ([ADR-0012](docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md)).
- Fases CI: `quality` → `test` → `build` → `smoke` (`e2e` opcional). El único check **required** es `ci-gate` ([ADR-0013](docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md)). `build` solo si hay artefacto.
- En **este** canon: `pipeline` llama a `reusable-static`; `ci-gate` agrega el resultado.
- En repos de producto, `test` incluye unit/function. Coverage default del reusable **80%**; el gate ≥70% sigue siendo opcional hasta suite estable ([ADR-0007](docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md)).
- Bot de deps: **solo Renovate** ([ADR-0004](docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md)). No añadas `.github/dependabot.yml` de version-updates. Dependabot Alerts ON.
- Secret scanning + push protection: prerrequisito org ([ADR-0005](docs/architecture/decisions/ADR-0005-secret-scanning-org.md)).
- `.env` nunca se commitea. `.env.example` solo con placeholders documentados.
- Callers pinean reusable por SHA (`stacks/<stack>/ci.yml`); no aplastes el stack.

## 6. Comandos

```bash
make validate   # integridad de estructura / contratos
make lint       # quality local (format, lint, types — según stack)
make test       # unit + coverage
make smoke      # pocas comprobaciones post-build, sin prod real
```

Plantillas caller: `stacks/typescript`, `stacks/rust`, `stacks/python`, `stacks/infra`.

## 7. Zonas que no se tocan a ciegas

- Secretos, tokens, `.env` reales, keys de producción
- Settings de org u otros repos (salvo que el humano lo pida de forma explícita)
- Archivados y forks externos
- Historial (no force-push, no rewrites de `main`)
- Deploy a producción sin aprobación explícita

## 8. Definition of Done

- Criterios de la traza cumplidos
- `make validate` + `make test` + `make smoke` en verde (y fases del reusable)
- Check `ci-gate` verde en el PR
- Docs canónicas actualizadas si cambia el contrato
- `CHANGELOG.md` `[Unreleased]` si el cambio es visible para consumidores
- Sin secretos en el diff
- PR en español, checklist de la plantilla marcado; auto-merge squash activado (salvo `hold`)

## 9. Hechos de este workspace (repo-standard)

- Producto de plataforma, no app. No hay `package.json` / `Cargo.toml` de runtime.
- El validador de este canon es `scripts/check-structure.sh`.
- CODEOWNERS: `* @Alexendros`.
- Perfiles: P0 Base (todo repo activo), P1 Producto (runtime + env + smoke + runbooks), P2 Público (CoC, SUPPORT, topics ricos).
- Gold de origen: `website-landingpage-template`, `zedazo`, `saas-afiladocs`, `miwebsite-alexendrosdev`, `infraestructura-stack`.
