# P9 · Activación · rulesets con ci-gate + retirada de branch protection clásica + ajustes de org

```
Ejecuta con gh en el box. Prerrequisitos: P1–P8 fusionados y Alejandro ha ejecutado `gh auth refresh -h github.com -s admin:org` (comprueba con gh auth status; si falta el scope, haz solo la parte por repo y lista lo pendiente).
Carpeta de trabajo y log: /workspace/10-ingenieros/github-org-policy/<fecha>/ (log.md con quién/qué/sobre qué/cuándo en hora de Madrid/por qué/resultado; snapshot before/ y after/). Commit en el git del workspace al terminar.
Pasos:
1. Para cada repo activo: verifica que el HEAD de la rama por defecto tiene check-run `ci-gate` = success emitido por la app github-actions (gh api repos/O/R/commits/<branch>/check-runs). Si no, sáltalo y anótalo.
2. Aplica con autoworkspace/scripts/apply-ruleset.sh (repo-standard queda excluido: archivado tras P11):
   - Públicos de la org: rulesets/repo-ci-gate-public.json.
   - Privados de la org: repo-ci-gate.json.
   - clienteafirma: repo-ci-gate-fork-clienteafirma.json.
   - archmaker y alexendrosdev: repo-ci-gate.json, sin code_scanning si CodeQL no está activo.
   Primero enforcement "evaluate" 24 h; revisa Rule Insights; luego "active".
3. Con el ruleset activo y verificado (un PR de prueba se auto-fusiona), elimina la branch protection clásica de ese repo (snapshot previo en before/). Es destructivo pero reversible con el snapshot. Alejandro lo autoriza en este plan para los repos que superen el paso 2.
   En archmaker, borra el ruleset "Protect main (externals)" (bypass always) tras activar el nuevo.
4. Org (con admin:org): ejecuta rulesets/org-actions-and-security.sh por secciones:
   (1) default_workflow_permissions=read y can_approve_pull_request_reviews=false, ya con la App en uso;
   (2) sha_pinning_required=true solo si grep confirma que todos los workflows activos usan SHA;
   (3) configuraciones de seguridad SIN coste (pública 'GitHub recommended'; privada propia sin GHAS);
   (4) rulesets de org org-base.json en evaluate y org-ci-gate.json con la lista real de repos migrados.
   Cuando los rulesets de org cubran lo mismo, los rulesets por repo de la org se pueden retirar (los de la cuenta personal se quedan).
5. Verificación final: para cada repo, gh api repos/O/R/rules/branches/<default> muestra pull_request (0, squash), required_status_checks [ci-gate, strict], non_fast_forward, deletion y linear history (salvo el fork) y bypass vacío; allow_auto_merge=true.
Criterios de éxito: 100 % de los repos activos con ruleset ci-gate activo y sin branch protection clásica; un PR de prueba por stack auto-fusionado sin interacción; log.md y snapshots commiteados.
Último paso obligatorio: actualiza el apartado «P9 · Activación» en la página de Notion de la política (NOTION_POLICY_PAGE) con la tabla final repo → ruleset → estado, y marca la política como implantada.
```

---

## Norma para todos los plan-prompts (cabecera obligatoria, desde P10)

Pega este bloque al inicio de cada plan. Se versiona en autoworkspace (antes repo-standard) como `docs/plan-template.md` (copia local: `plantillas-p10/plan-template.md`). ADR: `adr-flujo-planes-deploy.md`.

```
NORMA DE FLOTA (autoworkspace docs/plan-template.md @ <SHA>). Plan <ID> «<título>» · repo(s): <owner/repo>.
1. Rama de integración: crea `plan/<id>-<slug>` desde main y abre YA el PR borrador `plan/<id>-<slug> → main` (título Conventional). Cada tarea = rama de trabajo propia → PR a `plan/<id>-<slug>` (nunca a main), título Conventional, `gh pr merge --auto --squash`. Prohibido `--merge`, `--rebase`, `--admin`, push directo y tocar rulesets/entornos.
2. Fase 1 (integración) termina con el squash del PR del plan en main con ci-gate verde (incluido e2e contra el preview de la cabeza de plan/*). No despliegues ni publiques nada a mano: ni `vercel --prod`, ni `npm publish`, ni releases o tags.
3. Fase 2 (publicación) es automática: release-please versiona → publish.yml empaqueta, atesta y publica desde el tag v*. Si el plan no tiene ningún feat/fix/perf/deps, no se publica (lo esperado).
4. No modifiques .github/, vercel.json, renovate.json ni release-please-config.json salvo que el plan lo pida y coincida con la plantilla del canon (autoworkspace); si no, etiqueta `policy-exception` + entrada en .github/policy-exceptions.md.
5. Al terminar: marca el PR del plan como listo (se fusiona solo) y actualiza su apartado en Notion con PRs, versión publicada y URL del despliegue.
```

Orden revisado (tras P11): **P10-F0 ya** (no necesita la App) → P1 ✔ → **P11** (no necesita la App) → P2 (incluye P7 §2–4) → **P10-F1/F2** → P3 → P4 (incluye P10-F3) → P5, P6, P8 → P9. P7 queda sustituido.
