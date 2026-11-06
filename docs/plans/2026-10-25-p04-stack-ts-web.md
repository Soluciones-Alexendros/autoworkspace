# P4 · Despliegue stack TS/web (Vercel) · 10 repos, un PR por repo

```
Repos, en este orden (de menor a mayor riesgo):
ecommerce-rejasballesta (privado), saas-atlaps (privado), ecommerce-graficasnasve, saas-afiladocs, webconfig, website-frontvalencia, vapelog, website-alexendrosme (Soluciones-Alexendros) y alexendrosdev (Alexendros, cuenta personal).
Patrón: el validado en P3 (caller ci.yml de autoworkspace@<SHA> # v6.x por SHA + job ci-gate + automerge.yml + release.yml + release-please). Un PR por repo, con título "ci: adopta el canon repo-standard de autoworkspace (ci-gate, auto-merge, release-please)".
Reglas comunes:
- Conserva como jobs dentro de `pipeline` (inputs) o como jobs extra en ci.yml los checks valiosos que ya existen (e2e, lighthouse/lhci, a11y, visual, sql-integration, supply-chain…). TODOS deben ir en needs del ci-gate: lo que hoy es informativo y falla se arregla o se elimina, no se deja colgando.
- Endurece lint/types/cobertura como en P3. Si el código no cumple, arréglalo en el mismo PR o, si es muy grande, en PRs previos "refactor:" (cada uno con ci-gate verde).
- Sustituye el sistema de release previo:
  - semantic-release (.releaserc.json) en webconfig y alexendrosdev: elimina .releaserc y dependencias.
  - changesets en website-frontvalencia: elimina .changeset; release-please manifest monorepo con un paquete por app (frontvalencia-web, tools, @frontvalencia/quality) y versiones actuales tomadas de los últimos tags.
  - scripts propios: vapelog (release-ready + "chore(release)" de github-actions: el aggregator `release-ready` pasa a llamarse ci-gate), website-alexendrosme (check-version/do-release/release:prepare).
  - El manifest inicial se toma SIEMPRE del último tag existente para no retroceder versiones.
- Elimina cualquier dependencia de RELEASE_PAT o de GITHUB_TOKEN para crear PRs/tags.
- package-kind none (deploy Vercel). webconfig: npm-pack si su CLI site.bundle se distribuye; si no, none.
- alexendrosdev está en la cuenta personal. Si la App no está instalada en Alexendros (ver tareas de Alejandro), deja automerge/release preparados pero desactivados con un comentario y anótalo; no uses PAT.
- Privados (rejasballesta, atlaps): dependency-review se salta solo (no hay GHAS); nada más cambia.
Criterios de éxito por repo:
- ci-gate verde en main; un PR de prueba se auto-fusiona.
- El primer release de release-please continúa la numeración existente (p. ej. vapelog v0.13.x → v0.14.0, alexendrosdev v1.26.x → …).
- Vercel Production verde.
- 0 ficheros de release antiguos.
Último paso obligatorio: actualiza el apartado «P4 · Stack TS/web» en la página de Notion de la política (NOTION_POLICY_PAGE), con una fila por repo (PR, versión resultante, estado).
```
