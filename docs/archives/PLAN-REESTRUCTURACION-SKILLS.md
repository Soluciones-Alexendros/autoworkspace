# Plan de reestructuración de skills

Fecha: 2026-09-26 · Repo: `agent-skills` (21 skills → objetivo 19)

## Petición inicial

> Unifica: auditoria-360-web y web-audit bajo el nombre web-compliance / Suprime: datos-postgress / Integra: dependency-audit en codigo-seguridad y renombra a web-seguridad / Renombra: playwright-e2e-audit a web-playwright / Suprime: planificacion-archivos / Renombra: git-hooks a repo-precommit / Para las skills de proton, extrae referencias y vincula directamente las mismas al contenido de: https://github.com/Soluciones-Alexendros/protonsuite-tools

## Decisiones de alcance (cuestionario previo)

1. **Split del dominio web en dos:** `auditoria-360-web` se convierte en `web-compliance` (absorbe y desarrolla todas las cuestiones de accesibilidad, legal, posicionamiento, etc.) y se crea `web-rendimiento` (todas las cuestiones de rapidez de carga, estabilidad, compatibilidad, renderizado, tecnologías, etc.).
2. **`web-seguridad` queda en dominio web** (no se mueve a `codigo-*`).
3. **Nuevo dominio `linux-*`** para `linux-seguridad` y `linux-mantenimiento`.
4. **Borrado directo** de las skills suprimidas, con limpieza de referencias.

## Pre-flight (verificado en exploración read-only)

- 21 skills inventariadas. Leídos los `SKILL.md` de: `auditoria-360-web` (51 checks ACC/TEC/ONP/OFF/SEM/ANA/LEG; scripts `audit_page/contrast/score/report/selftest`), `web-audit` (CWV/Lighthouse + SEO + WCAG 2.1, sin scripts), `codigo-seguridad` (OWASP, 19 refs), `dependency-audit` (pipeline 7 etapas npm/Socket/depcheck/pip/cargo), `playwright-e2e-audit` (42 checks, 8 fases; scripts `discovery/measure/score/report/validate`), `git-hooks` (Husky), `linux-seguridad` (postura), `linux-mantenimiento` (R0–R3), `email-proton` (Bridge `127.0.0.1:1143/1025`), `protonpass` (pass-cli), `datos-postgres` (36 reglas), `planificacion-archivos`.
- Estándares: `docs/STANDARD.md` (frontmatter, cuerpo < 500 líneas, references planas, `name == carpeta`), `docs/TAXONOMY.md` (cerrada), validador `skill_spec.py` (`DOMINIOS`, `NAME_RE`, SEMVER), `README.md` (21 skills), `CHANGELOG.md` (Unreleased), `CONTRIBUTING.md` (bump major/minor/patch).
- Referencias cruzadas detectadas vía grep: `repo-ending→git-hooks`, `upstash→datos-postgres`, `web-diseno/webapp-testing/design-system/repo-starting→web-audit/dependency-audit/playwright`, `proton` mutuas.
- `protonsuite-tools` verificado: MCP multi-producto v1.4.0, 47 tools (Mail 14, Pass 4+, Drive 8+, Calendar stub), docs `bridge-core/mcp-tools/agent-quickstart/deployment`, licencia AGPL-3.0 vs MIT del repo (solo enlaces, no vendorizar código).
- Riesgos: límite 500 líneas por `SKILL.md`, `skill_links`, deriva `main` vs tag pineado.

## §1 — Split web: `web-compliance` + `web-rendimiento`

- `git mv skills/auditoria-360-web skills/web-compliance`.
- Crear `skills/web-rendimiento/`.
- Reparto: `web-compliance` ← accesibilidad, legal, SEO/posicionamiento (ACC/ONP/OFF/SEM/ANA/LEG de 360 + SEO/WCAG-2.1 de `web-audit`); `web-rendimiento` ← rapidez de carga, estabilidad, compatibilidad, renderizado, tecnologías (TEC de 360 + CWV/Lighthouse/perf de `web-audit`).
- Tabla de migración de checks 360 (51) y de `web-audit` → destino compliance/rendimiento.
- Colisión a resolver: `score.py` / `report.py` existen en ambos orígenes → renombrar por dominio (`score_compliance.py`, `score_perf.py`, etc.) o subcarpetas `scripts/compliance/` y `scripts/perf/`.
- Eliminar `skills/web-audit` tras migrar su contenido (queda absorbida entre las dos nuevas).

## §2 — Supresiones: `datos-postgres` + `planificacion-archivos`

- `git rm -r skills/datos-postgres skills/planificacion-archivos` (nota: petición dice `datos-postgress`; la carpeta real es `datos-postgres`).
- Limpieza de referencias: `upstash` → quitar mención a `datos-postgres`; `CONTRIBUTING.md`, `README.md` (conteo 21 → 19), `docs/TAXONOMY.md`.

## §3 — `codigo-seguridad` → `web-seguridad` (absorbe `dependency-audit`)

- `git mv skills/codigo-seguridad skills/web-seguridad`.
- Absorber `dependency-audit`: pipeline 7 etapas (npm audit/Socket/depcheck/pip-audit/cargo) como sección o `references/dependencies.md` dentro de `web-seguridad`.
- `git rm -r skills/dependency-audit` tras la absorción.
- Actualizar referencias desde `web-diseno/webapp-testing/design-system/repo-starting`.

## §4 — Renombros simples (git mv + frontmatter + refs)

| Origen | Destino |
|---|---|
| `playwright-e2e-audit` | `web-playwright` |
| `git-hooks` | `repo-precommit` |

- En cada una: `git mv`, actualizar `name:` del frontmatter (`name == carpeta`), `skill_links` internas (`repo-ending→repo-precommit`), README y TAXONOMY.

## §5 — `docs/TAXONOMY.md` + validador + README + STANDARD

- TAXONOMY: alta de `web-compliance`, `web-rendimiento`, `web-seguridad`, `web-playwright`, `repo-precommit`, `linux-seguridad`, `linux-mantenimiento`; baja de `auditoria-360-web`, `web-audit`, `codigo-seguridad`, `dependency-audit`, `playwright-e2e-audit`, `git-hooks`, `datos-postgres`, `planificacion-archivos`.
- Validador `skill_spec.py`: añadir dominio `linux` (y `repo` si no existe) en `DOMINIOS`.
- README: conteo 21 → 19 + tabla actualizada.
- STANDARD: sin cambios salvo que se decida matizar el límite de 500 líneas ante fusiones grandes (se recomienda trocear a `references/`).

## §6 — Proton: thin-skills con enlaces a protonsuite-tools

- `email-proton` y `protonpass` pasan a thin-skills: conservar criterio de enrutado (cuándo usar cada una) y mover el cómo a enlaces directos a `https://github.com/Soluciones-Alexendros/protonsuite-tools`.
- Tabla de correspondencia: Bridge/IMAP/SMTP → `docs/bridge-core*`; Mail 14 tools → `docs/mcp-tools*`; Pass → sección Pass del repo; agent-quickstart/deployment pineados.
- URLs pinneadas a tag/commit concreto (evitar deriva de `main`); licencia: solo enlazar (AGPL-3.0 ≠ MIT), no vendorizar.
- Actualizar referencias mutuas entre ambas skills proton.

## §7 — Versionado + validación

- Versiones: `major` para skills renombradas/transformadas (`web-compliance`, `web-rendimiento`, `web-seguridad`, `web-playwright`, `repo-precommit`, `linux-*`, proton thin-skills); `minor` para skills que solo pierden una referencia (p. ej. `upstash`); `patch` para retoques de enlaces.
- `CHANGELOG.md` → entrada Unreleased con la tabla de renombros/supresiones.
- Cierre: `run-validation.sh` (o validador equivalente) en verde + `git status` limpio salvo los cambios previstos.
