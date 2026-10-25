# P3 · Piloto · website-landingpage-template (TS web)

```
Repo: Soluciones-Alexendros/website-landingpage-template (plantilla de las webs: si funciona aquí, se replica). Requiere P11 y P2 fusionados (canon en autoworkspace, release posterior a P2).
Tareas:
1. Sustituye .github/workflows/ci.yml por el caller stacks/typescript/ci.yml de autoworkspace@<SHA> # v6.x. Mapea los scripts existentes (format:check, lint, typecheck, test, build, smoke).
   Endurece eslint con typescript-eslint strictTypeChecked + stylisticTypeChecked y las reglas core complexity 10, max-depth 3, max-params 4 y max-lines-per-function 60. Arregla el código hasta 0 errores, sin eslint-disable salvo con justificación en línea.
   tsconfig strict: true y noUncheckedIndexedAccess: true. Cobertura vitest con thresholds 80 (o el valor real actual redondeado hacia abajo si es menor, documentado como trinquete).
2. Añade automerge.yml y release.yml (callers de P2). Usa release-please-config.json (release-type node, package-kind none: el deploy es Vercel) y el manifest con la versión actual de package.json (0.1.0).
3. Quita el workflow de Dependabot version-updates si queda alguno; alinea .github/renovate.json con la base (extends del preset del canon en autoworkspace si se define como preset compartido).
4. Resuelve o cierra el PR de Renovate #106 (está DIRTY: en conflicto) después del merge.
Criterios de éxito:
- `ci-gate` verde en PR y en main.
- Un PR de prueba (docs) se auto-fusiona sin interacción.
- release-please abre el release PR y este se auto-fusiona → tag v0.1.1 o v0.2.0 + GitHub Release.
- Vercel Production sigue en verde.
Último paso obligatorio: actualiza el apartado «P3 · Piloto landingpage-template» en la página de Notion de la política (NOTION_POLICY_PAGE).
```
