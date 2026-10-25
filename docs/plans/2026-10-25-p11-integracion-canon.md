# P11 · Integración repo-standard + autoworkspace (autoworkspace pasa a ser el host del canon de flota)

Análisis y decisión: `integracion-repo-standard-autoworkspace.md` (opción A). Va **antes de P2** y no necesita la GitHub App.

```text
NORMA DE FLOTA (autoworkspace docs/plan-template.md @ <SHA>; hasta que exista, copia local plantillas-p10/plan-template.md). Plan P11 «Integración repo-standard + autoworkspace» · repo(s): Soluciones-Alexendros/autoworkspace (destino) y Soluciones-Alexendros/repo-standard (origen, solo lectura).
1. Rama de integración: crea `plan/p11-integracion-canon` desde main y abre YA el PR borrador `plan/p11-integracion-canon → main` (título Conventional). Cada tarea = rama de trabajo propia → PR a `plan/p11-integracion-canon` (nunca a main), título Conventional, `gh pr merge --auto --squash`. Prohibido `--merge`, `--rebase`, `--admin`, push directo y tocar rulesets/entornos.
2. Fase 1 (integración) termina con el squash del PR del plan en main con ci-gate verde (incluido e2e contra el preview de la cabeza de plan/*). No despliegues ni publiques nada a mano: ni `vercel --prod`, ni `npm publish`, ni releases o tags.
3. Fase 2 (publicación) es automática: release-please versiona → publish.yml empaqueta, atesta y publica desde el tag v*. Si el plan no tiene ningún feat/fix/perf/deps, no se publica (lo esperado).
4. No modifiques .github/, vercel.json, renovate.json ni release-please-config.json salvo que el plan lo pida y coincida con la plantilla del canon (autoworkspace); si no, etiqueta `policy-exception` + entrada en .github/policy-exceptions.md.
5. Al terminar: marca el PR del plan como listo (se fusiona solo) y actualiza su apartado en Notion con PRs, versión publicada y URL del despliegue.

Contexto obligatorio: /workspace/10-ingenieros/github-org-policy/2026-10-25/integracion-repo-standard-autoworkspace.md (inventario, solapes, estructura final y datos sensibles por ubicación), diseno.md, adr-flujo-planes-deploy.md, plantillas-p10/ y rulesets/. Lee AGENTS.md de ambos repos y docs/architecture/decisions/ de repo-standard (ADR-0001…0014).
Estado de partida (25/10/2026): repo-standard main = e518eb1 (P1 fusionado, sin tags, privado); autoworkspace main = 62f7fd6 (v5.0.0 etiquetada, package.json 5.1.0, público, required checks clásicos validate/hygiene/check-bump). 0 workflows de otros repos llaman a repo-standard (gh search code). Si algo ha cambiado, dilo y ajusta antes de tocar código.
Transición de este plan: hasta P2 sigue vigente el circuito actual de autoworkspace. check-bump exige subir metadata.version de cada skill tocada, y release.yml corta el tag desde package.json + CHANGELOG. branch-policy/policy-conformance aún no existen: cumple la norma a mano.
Prerrequisitos de Alejandro: (a) decisión de historial: excepción única de merge commit para el PR de importación (por defecto), o squash con línea de trazabilidad; (b) secreto de repo HYGIENE_DENYLIST en autoworkspace (patrones personales, uno por línea). Si (a) no está decidido, haz todo menos la Tarea 0 y detente. Si falta (b), el paso de CI correspondiente se salta con aviso explícito (nunca en verde falso: "not_run" con motivo).

Tarea 0 · Importación con historial (única excepción del plan, PR directo a main):
1. git fetch https://github.com/Soluciones-Alexendros/repo-standard.git main; git switch -c import/repo-standard-pre FETCH_HEAD.
   Commit "chore(canon): mueve los ficheros raíz del canon a templates/repo/". Con git mv lleva a templates/repo/ las 13 rutas que colisionan (.github/CODEOWNERS, .github/renovate.json, .gitignore, AGENTS.md, ARCHITECTURE.md, CHANGELOG.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, LICENSE, Makefile, README.md, SECURITY.md, docs/README.md), más .env.example, .github/ISSUE_TEMPLATE/ y .github/PULL_REQUEST_TEMPLATE.md. Nada más se mueve: ADRs, docs/guides, docs/runbooks, docs/REUTILIZACION.md, stacks/, scripts/ y .github/workflows/ conservan su ruta.
2. git switch -c import/repo-standard origin/main; git merge --allow-unrelated-histories --no-ff import/repo-standard-pre -m "chore(canon)!: importa Soluciones-Alexendros/repo-standard@e518eb1 con historial". Debe salir sin conflictos; si hay alguno, detente.
3. En la misma rama, commit "ci(canon): adapta el CI del canon importado":
   - .github/workflows/ci.yml importado: el job pipeline llama a `./.github/workflows/reusable-static.yml` (local) en vez de la ruta completa de repo-standard; check-structure.sh valida templates/repo/ (parámetro de raíz) y el árbol del canon en la raíz;
   - el job ci-gate añade en needs los jobs de quality.yml y validate.yml (copiados como jobs de ci.yml; los workflows antiguos siguen hasta P9 porque sus checks son required);
   - security.yml sin cambios funcionales.
4. PR import/repo-standard → main, título "chore(canon)!: importa repo-standard con historial", con etiqueta policy-exception y .github/policy-exceptions.md creado (motivo: preservar historial; autorizado por Alejandro el <fecha>; PR #n).
   Si Alejandro autorizó el merge commit: él activa allow_merge_commit, se fusiona con `gh pr merge <n> --merge` cuando validate, hygiene y check-bump estén verdes, y él lo vuelve a desactivar (o lo haces tú con gh si te lo autoriza expresamente, registrándolo en log.md con quién/qué/sobre qué/cuándo en hora de Madrid/por qué/resultado).
   Si eligió squash: `gh pr merge --auto --squash` con "Importa Soluciones-Alexendros/repo-standard@e518eb1 (historial en el repo archivado)" en el cuerpo.
   Después crea plan/p11-integracion-canon desde el main resultante.

Tareas del plan (un PR por tarea hacia plan/p11-integracion-canon):
T1 · Consolidar raíz y contrato de agentes (refactor/docs):
- README.md: producto autoworkspace + sección «Canon de flota (repo-standard)» con el índice de ADRs, stacks, rulesets y reusables. ARCHITECTURE.md: añade las capas canon/CI.
- CONTRIBUTING.md, SECURITY.md y CODE_OF_CONDUCT.md: los de autoworkspace, completados con lo que solo esté en templates/repo.
- Makefile: une los objetivos (validate, lint, test, smoke).
- AGENTS.md: mantiene el contrato de routing y declara que el repo cumple el contrato de flota de templates/repo/AGENTS.md §1–8. ELIMINA de «Learned User Preferences» la regla `gh pr merge --auto --merge` (nunca squash) y la sustituye por la norma vigente: `gh pr merge --auto --squash`, flujo plan/*, prohibido --merge/--rebase/--admin. grep -n -- "--merge" AGENTS.md solo puede aparecer como prohibición.
- CHANGELOG.md: entrada BREAKING en [Unreleased].
- README de templates/repo: «copiar a un repo nuevo» con `gh repo create … && cp -a templates/repo/. <repo>/`. Corrige «Iniciativas-Alexendros» → «Soluciones-Alexendros» en todo el canon (grep -rn Iniciativas = 0).
T2 · ADR y estructura de planes (docs):
- docs/architecture/decisions/ADR-0016-autoworkspace-host-del-canon.md (formato del canon). Contexto: host público y único; GitHub Actions no sigue redirecciones. Decisión: opción A, versión única de autoworkspace desde v6.0.0 y ADR-0010 aplicado a autoworkspace. Consecuencias: callers por SHA de autoworkspace; repo-standard archivado; «Use this template» → templates/repo.
- Marca ADR-0001 «Este repo es el canon» como Superseded en parte por ADR-0016, y ADR-0011 (bootstrap desde plantilla) como sustituido por templates/repo.
- docs/plan-template.md = plantillas-p10/plan-template.md con «autoworkspace» como origen, seguido del esqueleto obligatorio de plan-prompt: Repos · Contexto · Prerrequisitos · Tareas · Criterios de éxito verificables · Último paso Notion.
- docs/plans/ con P1–P11 de /workspace/10-ingenieros/github-org-policy/2026-10-25/planes-prompt.md, un fichero por plan (AAAA-MM-DD-pNN-<slug>.md). Sustituye las URLs de Notion por «la página de Notion de la política (NOTION_POLICY_PAGE)».
- docs/architecture (canon) / docs/REUTILIZACION.md/ se elimina: structure/ci-cd/release/security se integran en los docs del canon (REUTILIZACION, guides) con la política vigente (ci-gate, squash, sin etiqueta automerge) y skill-spec.md pasa a docs/skill-spec.md. Arregla los enlaces (skill_links.py en verde).
T3 · Desduplicar skills sin crear skills nuevas (fix; sube metadata.version de cada skill tocada):
- plan-continue/references: canon.md, adrs-indice.md, reutilizacion.md, overview.md y convenciones-y-canon.md quedan como resumen breve + rutas del canon dentro de autoworkspace (docs/architecture/decisions/, docs/REUTILIZACION.md, templates/repo/). Fuera las copias.
- project-publish/assets/ruleset.json y assets/workflows/*: se eliminan y se apunta a rulesets/ y stacks/.
- Los composite actions de project-publish/actions/ se quedan (no son reusables), alineados con los SHAs del canon.
- Amplía el validador EXISTENTE (tools/validate/skill_links.py o release_coherence.py, sin herramienta nueva): falla si una skill cita un ADR inexistente o con otro estado que el fichero de docs/architecture/decisions/.
- package-standalone-skill.sh incluye en el paquete los ficheros del canon que la skill cite (con un test en scripts/tests/test_standalone_package.sh).
- Regenera skill-index.json.
T4 · Configuración por entorno y datos locales fuera del código (fix/security; criterio de Alejandro t104u):
- .env.example en la raíz, versionado: SOLO nombres y valores de ejemplo, con un comentario por variable (qué hace, si es obligatoria, valor por defecto). Cubre como mínimo las que el código ya lee: SNAPSHOT_DIR, LOG_DIR, SESSION_ID, OUTPUT_JSON, NO_COLOR, PROTON_IMAP_HOST/PORT, PROTON_SMTP_HOST/PORT, PROTON_USER (user@example.com), PROTON_PASS (vacío), AUTOWORKSPACE_APPROVAL_PROVIDER, AUTOWORKSPACE_ALLOW_NETWORK, AUTOWORKSPACE_PRIVATE_PATTERNS.
- .gitignore: añade `.env`, `.env.*` y `!.env.example`.
- Lectura: os.environ.get con valores por defecto seguros (solo lectura, sin red, rutas XDG/$HOME) y, para las obligatorias, una función require_env(nombre, ayuda) en el módulo común existente de cada skill o en tools/contracts (sin dependencias nuevas, sin python-dotenv) que termine con código ≠0 y el mensaje «Falta la variable X: <ayuda>; ver .env.example». Documenta en docs/USAGE.md cómo cargarla: `set -a; . ./.env; set +a` o el objetivo de make que la carga si existe.
- Sustituye por variables o marcadores (ubicaciones exactas en el §5 del análisis; no copies los valores a PRs ni a logs):
  - rutas personales de skills/local-maintenance/references/pitfalls.md L9–13 y L34, tasks/plan-executable-skills.md L17 y docs/archives/reflexiones-constitucion.md L79 → $HOME, $XDG_*, $LOG_DIR, redactado genérico;
  - el email de skills/local-proton/references/setup.md L48 → PROTON_USER;
  - el fragmento literal de hostname de tools/validate/skill_spec.py L166 → patrones leídos de AUTOWORKSPACE_PRIVATE_PATTERNS (local) y del secreto HYGIENE_DENYLIST en CI (paso con env: desde secrets; si el secreto no existe, "not_run" con aviso).
- tools/validate/hygiene.py: excepción para *.example (hoy marca .env.example) y fallo si `git ls-files` contiene `.env` o `.env.*` que no sea `.env.example`, con test en tools/validate/tests (fixture con .env versionado → falla; con .env.example → pasa).
- Verifica con gh api que siguen activos secret scanning, push protection y validity checks (solo lectura; si no, tarea para Alejandro).
- NO reescribas historia. El historial ya público con datos locales (commits del §5) queda como decisión de Alejandro; anótalo en la descripción del PR solo con commit y ruta.
T5 · CI y gobierno del canon dentro de autoworkspace (ci):
- .github/workflows/ci.yml único con job `ci-gate` (nombre exacto) y needs de: pipeline-python (`./.github/workflows/reusable-python.yml` con los scripts Python de tools/ y skills/; umbral de cobertura = el actual redondeado hacia abajo como trinquete), validate (run-validation.sh), hygiene, canon (actionlint + scripts/check-structure.sh sobre templates/repo + smoke.sh) y check-bump mientras exista. Si hay JS, pipeline-node.
- Un job de prueba llama a uno de los reusables por ruta completa `Soluciones-Alexendros/autoworkspace/.github/workflows/reusable-static.yml@<SHA de la cabeza del plan>`, para verificar el direccionamiento que usarán los callers.
- quality.yml y validate.yml se quedan hasta P9 (son required clásicos) pero sin lógica duplicada: llaman a los mismos scripts.
- stacks/<stack>/ci.yml y la documentación: `uses: Soluciones-Alexendros/autoworkspace/.github/workflows/reusable-<stack>.yml@<SHA> # v6.0.0`. grep -rn "Soluciones-Alexendros/repo-standard/.github" .github stacks docs/REUTILIZACION.md templates = 0.
- .github/CODEOWNERS: @Alexendros en /.github/workflows/, /stacks/, /rulesets/, /docs/architecture/decisions/ y /templates/repo/.
- .github/renovate.json = plantillas-p10/renovate.json, conservando las reglas propias de pip justificadas.
- rulesets/ y scripts/apply-ruleset.sh NO se crean aquí (los trae P2/P10 ya con host autoworkspace).
T6 · Versión (chore(release)): package.json → 6.0.0, con la sección 6.0.0 del CHANGELOG en Keep a Changelog (BREAKING: autoworkspace es el host del canon; método de merge squash). release.yml actual corta v6.0.0 al fusionar el PR del plan. No crees tags a mano.

Fuera de este plan (no lo hagas): reusable-automerge/release (P2), reusable-publish/plan-body/fleet-drift/rulesets (P10), cambios en otros repos de la flota, rulesets o branch protection, crear skills o familias nuevas, reescribir historia, publicar repo-standard.
Tareas para Alejandro (en la descripción del PR del plan): archivar Soluciones-Alexendros/repo-standard (Settings → Archive) tras el merge, con descripción «Movido a Soluciones-Alexendros/autoworkspace»; decidir el historial público de autoworkspace (§5: aceptar o repo nuevo); reapuntar las instalaciones locales si cambió alguna ruta (`bash scripts/install.sh --target …`).

Criterios de éxito (verificables, con enlaces):
- Historial: `git merge-base --is-ancestor e518eb1 origin/main` = verdadero y `git log --follow --oneline docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md` muestra fcfd350, o (si fue squash) el cuerpo del commit cita repo-standard@e518eb1. policy-exceptions.md cita el PR.
- Árbol final del §6 del análisis: docs/architecture (canon) / docs/REUTILIZACION.md/ no existe; templates/repo/ existe; ADR-0001…0016 presentes con estados correctos; docs/plan-template.md y docs/plans/ (P1–P11) presentes.
- grep -rn "Soluciones-Alexendros/repo-standard/.github" .github stacks templates docs/REUTILIZACION.md = 0; grep -rn "Iniciativas-Alexendros" = 0; ningún doc ni skill exige la etiqueta automerge (grep -rn "label `automerge`" docs skills = 0).
- AGENTS.md no prescribe --merge; el validador de índice de ADRs falla con un fixture que diga «ADR-0006 Proposed» y pasa en HEAD.
- `.env.example` versionado; `git check-ignore -q .env .env.local` = 0 y `git check-ignore -q .env.example` ≠ 0; el test de hygiene con .env versionado falla y con .env.example pasa; `AUTOWORKSPACE_PRIVATE_PATTERNS=<patrones> git grep -nEf <(printf '%s\n' "$AUTOWORKSPACE_PRIVATE_PATTERNS")` = 0 en HEAD (salvo los falsos positivos documentados); un script con una variable obligatoria ausente termina ≠0 con el mensaje «Falta la variable…». (errata P12: `git check-ignore -q` admite un solo path por llamada; ver docs/plan-template.md §Criterios)
- gh api repos/Soluciones-Alexendros/autoworkspace --jq .security_and_analysis: secret_scanning, push_protection y validity_checks = enabled.
- En los PRs del plan y en main: check `ci-gate` con ese nombre exacto (gh pr checks), en verde, más validate, hygiene y check-bump en verde. El job de prueba por ruta completa, en verde.
- bash run-validation.sh y skill-index --check en verde; metadata.version subida en cada skill tocada.
- Tras el squash del PR del plan: tag v6.0.0 + GitHub Release + attestation (gh attestation verify autoworkspace-6.0.0.tar.gz -R Soluciones-Alexendros/autoworkspace).
- repo-standard archivado (gh api repos/Soluciones-Alexendros/repo-standard --jq .archived = true) cuando Alejandro lo haga; si no, queda como pendiente.

Último paso obligatorio: actualiza el apartado «P11 · Integración repo-standard + autoworkspace» en la página de Notion de la política (NOTION_POLICY_PAGE) con: estado, decisión de historial (merge commit o squash), PR de importación y PR del plan, tag v6.0.0 y attestation, resultado de los criterios, estado del archivado de repo-standard, decisión pendiente sobre el historial público y fecha y hora de Madrid.
```
