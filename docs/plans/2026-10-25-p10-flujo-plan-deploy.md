# P10 · Flujo plan/* y despliegue a producción solo en main (integración → publicación)

```
Repos: Soluciones-Alexendros/autoworkspace (núcleo, host del canon tras P11) y Soluciones-Alexendros/website-landingpage-template (piloto). La Fase 0 toca los 11 repos web. La adopción completa en el resto va dentro de P4.
Contexto obligatorio: /workspace/10-ingenieros/github-org-policy/2026-10-25/adr-flujo-planes-deploy.md (normas 1–18), plantillas en plantillas-p10/ y rulesets nuevos en rulesets/ (repo-plan-branches.json, repo-ci-gate-v2.json, repo-tags-release.json, environment-production.json).
Prerrequisitos: F0 ninguno. F1–F3: P11 y P2 fusionados y GitHub App de CI instalada (vars.CI_APP_CLIENT_ID, secrets.CI_APP_PRIVATE_KEY). autoworkspace ya es público. Si falta, haz solo F0 y detente; nunca uses PAT ni GITHUB_TOKEN como sustituto de la App.
Este plan se ejecuta ya con su propio flujo: rama plan/p10-flujo-plan-deploy en autoworkspace y PRs de tareas hacia ella. F0 va como hotfix/vercel-fase0 por repo, porque es urgente y no despliega.

F0 · Freno inmediato de cuota Vercel (11 repos: website-landingpage-template, alignux-app, ecommerce-rejasballesta, saas-atlaps, ecommerce-graficasnasve, saas-afiladocs, webconfig, website-frontvalencia, vapelog, website-alexendrosme, Alexendros/alexendrosdev):
1. Un PR por repo, título "fix(ci): limita despliegues Vercel a main, plan/** y hotfix/**":
   - Fusiona en vercel.json existente (sin perder sus otras claves) el bloque git.deploymentEnabled de plantillas-p10/vercel.fase0.json: {"**": false, "main": true, "plan/**": true, "hotfix/**": true}. Quita cualquier ignoreCommand cuyo fin sea ahorrar despliegues: no ahorra cuota, según docs de Vercel.
   - Sustituye .github/renovate.json por plantillas-p10/renovate.json, o fusiónalo conservando reglas propias justificadas.
   - En website-alexendrosme: el job deploy sigue (lo retira P4) y pr-summary pasa de --merge a --squash.
2. Cierra los PRs de Renovate abiertos que el nuevo agrupado sustituye (Renovate los recrea agrupados), después de que el PR se fusione.
Criterio F0: en las 24 h siguientes, list_deployments de Vercel (equipo alexendros-team) muestra 0 despliegues de ramas renovate/* y de ramas de trabajo. Adjunta el recuento por tipo, antes y después.

F1 · autoworkspace (canon; ADR-0015 «Flujo plan/* en dos fases y publicación desde tag»):
1. docs/architecture/decisions/ADR-0015 con el contenido de adr-flujo-planes-deploy.md, adaptado al formato del canon. Actualiza ADR-0014: package-kind vercel y publish por release: published.
   docs/plan-template.md = plantillas-p10/plan-template.md. AGENTS.md y CONTRIBUTING.md enlazan la plantilla y las normas.
2. Divide el reusable de release:
   - reusable-release.yml (push a main): solo release-please con token de la App.
   - reusable-publish.yml (workflow_call; caller stacks/common/publish.yml con on: release: types [published]):
     - Job con environment: {name: production, url: <URL>}. Input package-kind (none|npm-pack|oci|rust-bin|python-dist|tauri|vercel).
     - vercel:
       - vercel pull --yes --environment=production; vercel build --prod; tar de .vercel/output → SHA256SUMS → actions/attest-build-provenance sobre el tar (NO subir el tar a la Release; sí SHA256SUMS);
       - vercel deploy --prebuilt --prod, capturando la URL;
       - /version.json con {version, sha} generado antes del build.
     - Job summary con quién/qué/sobre qué/cuándo (TZ=Europe/Madrid)/por qué (PR del plan: gh api repos/{r}/commits/{sha}/pulls)/resultado.
     - npm: entorno npm + trusted publishing OIDC (id-token: write), sin NPM_TOKEN. GHCR: GITHUB_TOKEN con packages: write.
     - CLI de Vercel fijada por versión (npm i -g vercel@<x.y.z>) y acciones por SHA.
3. Nuevos jobs reutilizables, llamados desde reusable-<stack>.yml y en needs del ci-gate del caller:
   - branch-policy (bash, datos del evento por env, sin interpolar):
     - PR a main solo desde plan/*, hotfix/*, release-please--branches--main* o renovate/* (input extra-allowed para upstream-sync/* en clienteafirma).
     - PR a plan/* solo desde una rama no reservada del mismo repo.
     - hotfix exige título fix|perf|revert y "Motivo:" en el cuerpo.
     - plan→main exige 0 PRs abiertos con base en esa rama y al menos una unidad publicable en BEGIN_COMMIT_OVERRIDE (feat|fix|perf|deps|!), salvo etiqueta no-release.
   - policy-conformance: comprobaciones de la norma 13 de la ADR (lista permitida de reusables: Soluciones-Alexendros/autoworkspace/.github/workflows/...@<SHA>). Además falla si `git ls-files` contiene `.env` o `.env.*` distinto de `.env.example` (criterio de Alejandro t104u). Excepción solo con etiqueta policy-exception y una entrada en .github/policy-exceptions.md que cite el número del PR.
   - vercel-config (input web: true): vercel.json.git.deploymentEnabled == plantilla final {"**": false, "plan/**": true, "hotfix/**": true}. Durante la transición, input fase0 admite la de F0.
   - preview-e2e (solo PRs a main desde plan/* o hotfix/*):
     - espera hasta 15 min el GitHub Deployment cuyo environment empieza por "Preview" para head.sha (gh api repos/{r}/deployments?sha=… + statuses);
     - ejecuta el e2e del repo (input e2e-command) o un smoke curl contra target_url con cabecera x-vercel-protection-bypass (secreto de repo VERCEL_AUTOMATION_BYPASS_SECRET).
4. reusable-plan-body.yml: en push a plan/** y en pull_request opened/ready_for_review del PR plan→main, regenera con GITHUB_TOKEN (a propósito, para no redisparar CI) el bloque BEGIN_COMMIT_OVERRIDE…END_COMMIT_OVERRIDE del cuerpo con git log --first-parent --no-merges origin/main..HEAD --format=%s. Respeta el resto del cuerpo.
5. reusable-automerge.yml: update-behind también en push a plan/** (PRs con base plan/* en BEHIND). Para el PR plan→main, update-branch normal (merge main→plan).
6. .github/workflows/fleet-drift.yml (schedule semanal lunes 08:00 Madrid = cron en UTC + workflow_dispatch):
   - Solo lectura con token de la App (permisos de lectura administration, contents, deployments, environments) para los repos de la org y, si está instalada, de la cuenta personal.
   - Comprueba: rulesets (main, plan/*, tags v*) frente a rulesets/*.json; entorno production con política tags v*; vercel.json == plantilla; commits de main de los últimos 7 días con >1 padre (salvo clienteafirma upstream-sync) o sin PR asociado; Deployments de producción no creados por publish.yml; /version.json de cada web == último tag; lista de policy-exceptions y de hotfixes.
   - Abre o actualiza el issue "Deriva de flota AAAA-SS" en autoworkspace (GITHUB_TOKEN issues: write). Si no hay deriva, comenta "sin deriva".
7. Plantillas: stacks/web/vercel.json (= plantillas-p10/vercel.json), .github/renovate.json base (= plantillas-p10/renovate.json), stacks/common/publish.yml, rulesets/*.json nuevos (sin la clave _notas) y scripts/apply-ruleset.sh, que admite target tag y entornos (PUT environments + deployment-branch-policies).
8. CHANGELOG/ADR: el cambio es MAJOR para los callers si P2 ya publicó v2 (nuevos checks obligatorios en ci-gate) → BREAKING en el cuerpo.

F2 · Piloto website-landingpage-template (plan/p10-piloto):
1. Callers ci.yml, automerge.yml, release.yml y publish.yml (package-kind vercel) de autoworkspace@<SHA>. vercel.json final (main false) y /version.json.
2. Inventario de variables de sistema de Vercel usadas en build (grep VERCEL_ en src, next.config.*, scripts): sustitúyelas por variables explícitas o documenta la excepción "vercel deploy --prod" en la ADR del repo.
3. Lo que hace Alejandro antes del piloto (listado en tareas-alejandro.md):
   - entorno production (rulesets/environment-production.json) con secretos VERCEL_TOKEN (scoped), VERCEL_ORG_ID y VERCEL_PROJECT_ID;
   - secreto de repo VERCEL_AUTOMATION_BYPASS_SECRET;
   - ruleset de tags con el App ID.
4. Ensayo completo:
   - plan de prueba con 2 PRs (feat: y fix:) hacia plan/p10-piloto; PR plan→main;
   - un PR de una rama "cursor/x" directo a main debe fallar en branch-policy;
   - un PR que cambie vercel.json a main:true debe fallar en vercel-config;
   - un PR con "gh pr merge --rebase" en un workflow debe fallar en policy-conformance.
Criterios de éxito F1+F2 (verificables, con enlaces):
- Los PRs a plan/* tienen ci-gate verde y NINGÚN despliegue en Vercel; la cabeza de plan/* tiene 1 preview por merge (list_deployments filtrando branch).
- El PR plan→main pasa preview-e2e contra el preview de su head.sha; su cuerpo lleva BEGIN_COMMIT_OVERRIDE con los 2 títulos.
- Tras el squash en main: 0 despliegues de producción por Git; release-please abre el release PR, que se auto-fusiona; existe el tag v* creado por la App; publish.yml corre en refs/tags/v* con environment production → 1 despliegue de producción (target production, creado por CLI), GitHub Deployment con URL, attestation verificable (gh attestation verify <tar> -R Soluciones-Alexendros/website-landingpage-template), SHA256SUMS en la Release, /version.json == tag.
- El CHANGELOG del release contiene las 2 entradas (feat y fix) del override.
- Los 3 PRs trampa fallan en el job esperado; un intento de crear un tag v9.9.9 con gh api desde la sesión de Alexendros falla por el ruleset.
- Un workflow de PR que referencia environment: production no obtiene VERCEL_TOKEN (falla por la política de tags): enlaza el run.
- Renovate: el siguiente lunes hay como mucho 1 PR agrupado (no majors) con título chore(deps), sin preview y sin release. Un PR de vulnerabilityAlerts sale como fix(deps) (si no, aplica la packageRule alternativa de la ADR §8.7).
- fleet-drift.yml lanzado a mano crea el issue con 0 derivas en el piloto y detecta una deriva provocada a propósito (input de prueba que apunte a un repo/fixture con vercel.json alterado), sin escribir en ningún repo salvo el issue.

F3 · Despliegue al resto: dentro de P4 (repos web) y P5–P8 (publish.yml por stack), según §9 de la ADR. website-alexendrosme pierde el job deploy y su check obligatorio; vapelog adopta preview-e2e estándar.

Último paso obligatorio: actualiza el apartado «P10 · Flujo plan/* y deploy» en la página de Notion de la política (NOTION_POLICY_PAGE) con: estado por fase (F0 por repo, F1, F2), PRs, tag y Deployment del piloto, recuento de despliegues Vercel antes/después (24 h), enlaces a los runs de los PRs trampa y fecha y hora de Madrid.
```
