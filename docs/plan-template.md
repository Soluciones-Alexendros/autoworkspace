<!-- docs/plan-template.md · cabecera OBLIGATORIA de todo plan-prompt (canon repo-standard, alojado en autoworkspace tras P11). No editar por plan: solo rellenar los campos <...>. -->

NORMA DE FLOTA (autoworkspace docs/plan-template.md @ <SHA>). Plan <ID> «<título>» · repo(s): <owner/repo>.

1. Rama de integración: crea `plan/<id>-<slug>` desde main y abre YA el PR borrador `plan/<id>-<slug> → main` (título Conventional). Cada tarea = rama de trabajo propia → PR a `plan/<id>-<slug>` (nunca a main), título Conventional, `gh pr merge --auto --squash`. Prohibido `--merge`, `--rebase`, `--admin`, push directo y tocar rulesets/entornos.
2. Fase 1 (integración) termina con el squash del PR del plan en main con ci-gate verde (incluido e2e contra el preview de la cabeza de plan/*). No despliegues ni publiques nada a mano: ni `vercel --prod`, ni `npm publish`, ni releases o tags.
3. Fase 2 (publicación) es automática: release-please versiona → publish.yml empaqueta, atesta y publica desde el tag v*. Si el plan no tiene ningún feat/fix/perf/deps, no se publica (lo esperado).
4. No modifiques .github/, vercel.json, renovate.json ni release-please-config.json salvo que el plan lo pida y coincida con la plantilla del canon (autoworkspace); si no, etiqueta `policy-exception` + entrada en .github/policy-exceptions.md.
5. Al terminar: marca el PR del plan como listo (se fusiona solo) y actualiza su apartado en Notion con PRs, versión publicada y URL del despliegue.

---

## Esqueleto obligatorio de plan-prompt

Tras la cabecera NORMA DE FLOTA, cada plan incluye (en este orden):

1. **Repos** — `owner/repo` (uno o varios).
2. **Contexto** — por qué ahora; enlaces a ADRs / análisis.
3. **Prerrequisitos** — humanos, App, secretos, decisiones previas.
4. **Tareas** — numeradas; cada una → rama de trabajo → PR a `plan/<id>-<slug>`.
5. **Criterios de éxito verificables** — con comandos/enlaces comprobables.
6. **Último paso Notion** — actualizar el apartado del plan en la página de Notion de la política (`NOTION_POLICY_PAGE`).

Origen canónico: este fichero en `Soluciones-Alexendros/autoworkspace`.
