# P2 · autoworkspace (canon) · automerge + update-behind + release-please + packaging + Renovate + rulesets como código

> **Nota histórica (B09-B, 2026-10-29):** este borrador no es la política vigente de Renovate en el tip. La decisión operativa es: `platformAutomerge` + automerge de **patch/minor** (y Actions/Python agrupados); **majors sin automerge** con `minimumReleaseAge` 14 días; cuarentena general 3 días; managers Archify sin automerge. El punto «majors con automerge true» de abajo queda como texto histórico del plan P2, no como contrato actual. Release-please y retirar check-bump siguen siendo alcance pendiente de P2/P10, no de este cierre B09.

```
Repo: Soluciones-Alexendros/autoworkspace (host del canon tras P11; antes repo-standard). Requiere P11 fusionado. Prerrequisito: la GitHub App de la org existe (vars.CI_APP_CLIENT_ID y secrets.CI_APP_PRIVATE_KEY a nivel org); autoworkspace ya es público. Si falta algo, detente y dilo; no uses PAT ni GITHUB_TOKEN como sustituto.
Motivo de la App: los eventos creados con GITHUB_TOKEN no disparan workflows. El merge automático no lanzaría el release, y el release PR no ejecutaría CI.

Tareas:
1. .github/workflows/reusable-automerge.yml (workflow_call). Secrets: app-private-key; input: app-client-id.
   - Job enable: en pull_request opened/reopened/ready_for_review. Solo si el PR no es draft, su head repo es el mismo repo, el autor no es renovate[bot] y no lleva la etiqueta `hold`.
     Pasos: actions/create-github-app-token@<SHA v3> con permission-contents: write y permission-pull-requests: write → gh pr merge --auto --squash "$PR_URL" (GH_TOKEN = token de la App).
   - Job update-behind: en push a la rama por defecto, con el token de la App. Lista los PRs abiertos con autoMergeRequest != null y mergeStateStatus == BEHIND (gh pr list --json) y llama a PUT /repos/{repo}/pulls/{n}/update-branch para cada uno.
   - Caller de ejemplo en stacks/common/automerge.yml.
2. .github/workflows/reusable-release.yml (workflow_call), en push a main:
   - Job release: googleapis/release-please-action@<SHA v5> con token de la App (config-file release-please-config.json, manifest-file .release-please-manifest.json). Outputs: release_created, tag_name, version.
   - Job package (needs release, if release_created == 'true'), con GITHUB_TOKEN y permisos mínimos (contents: write para subir assets; packages: write si hay OCI; id-token: write y attestations: write).
     Input `package-kind` (none | npm-pack | oci | rust-bin | python-dist | tauri) y `oci-dockerfile`.
     Genera artefactos → SHA256SUMS → actions/attest-build-provenance@<SHA> sobre los artefactos (y sobre el digest en OCI, con push-to-registry) → gh release upload.
     OCI: docker/login-action + docker/build-push-action a ghcr.io/${{ github.repository }} con tags semver y latest.
     rust-bin: matriz x86_64-unknown-linux-gnu y aarch64-unknown-linux-gnu como mínimo.
     tauri: tauri-apps/tauri-action. python-dist: uv build.
   - Plantillas release-please por stack en stacks/<stack>/release-please-config.json:
     release-type node | rust | python | simple; bump-minor-pre-major true; include-v-in-tag true; changelog-sections en español (feat→Añadido, fix→Corregido, perf→Rendimiento, refactor→Refactor, docs→Documentación; chore/ci/test ocultas). Más un ejemplo de manifest monorepo.
   - El release PR que crea la App dispara automerge.yml (eventos de App sí disparan workflows), así que se fusiona solo cuando ci-gate está verde. Documenta la etiqueta `hold` para agrupar releases si algún día se quiere.
3. .github/renovate.json (base de flota):
   - extends config:recommended, helpers:pinGitHubActionDigests y :semanticCommits; platformAutomerge true; automergeType pr.
   - minimumReleaseAge "3 days" general y "14 days" para major; majors con automerge true (decisión ADR-0012: el único requisito es CI verde).
   - Se mantiene schedule Europe/Madrid "before 7am"; vulnerabilityAlerts habilitado, con minimumReleaseAge 0 y automerge.
   - Valida la configuración con renovate-config-validator en CI (npx --yes renovate@<versión fijada> renovate-config-validator).
4. rulesets/ con los JSON de /workspace/10-ingenieros/github-org-policy/2026-10-25/rulesets/ (repo-ci-gate.json, repo-ci-gate-public.json, repo-ci-gate-fork-clienteafirma.json, org-base.json, org-ci-gate.json) y scripts/apply-ruleset.sh <owner/repo> <json>:
   - Antes de aplicar, verifica que el último commit de main tiene el check `ci-gate` en success.
   - Guarda un snapshot JSON previo de la branch protection y los rulesets.
   - Aplica con gh api y escribe una línea de log (quién/qué/sobre qué/cuándo en hora de Madrid/por qué/resultado) en un fichero que el usuario indique.
   - Nunca borra branch protection sin el flag --remove-classic-bp.
5. Activa release-please en el propio autoworkspace (absorbe P7 §2–3). Release-type node (package.json private) con manifest desde 6.0.0 (tag de P11) y extra-files para los metadata.version de skills si se mantienen.
   Elimina version.yml/check-bump y el corte de tag de tools/version/cut_tag.py en release.yml. Package-kind: tarball `git archive` + SHA256SUMS + attest-build-provenance.
   Añade automerge.yml y release.yml con los callers locales (./.github/workflows/...).
6. Docs: REUTILIZACION.md con la sección «Adoptar en un repo en 5 pasos» y la tabla «stack → package-kind». ADR-0014 completo.

Criterios de éxito:
- Un PR de prueba abierto por Alejandro recibe auto-merge sin interacción (timeline: "enabled auto-merge" por la App) y se fusiona solo al quedar ci-gate verde.
- El push del merge dispara release-please; el release PR se auto-fusiona; existe el tag v6.x siguiente con GitHub Release, CHANGELOG, tarball y attestation; no queda ningún check que exija editar versiones a mano.
- Un segundo PR que queda BEHIND se actualiza solo (update-behind) y se fusiona.
- Renovate valida la configuración en CI.
Último paso obligatorio: actualiza el apartado «P2 · canon automerge/release» en la página de Notion de la política (NOTION_POLICY_PAGE) (estado, PRs, tag, evidencias, hora de Madrid).
```
