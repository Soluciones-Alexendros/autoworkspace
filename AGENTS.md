# AGENTS.md — contrato para Mantenedor y agentes

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
- Gates CI en este orden: `quality` → `test` → `build` → `smoke` (`e2e` opcional en webs).
- En **este** canon no hay runtime: `quality` valida estructura, `test` es el hook documentado, `smoke` ejecuta `scripts/smoke.sh`.
- En repos de producto, `test` incluye unit/function y cobertura **≥70%** (documenta **80%** en módulos críticos).
- Bot de deps: **solo Renovate**. No añadas `.github/dependabot.yml` de version-updates. Las Dependabot Alerts de seguridad pueden quedar ON a nivel org.
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
