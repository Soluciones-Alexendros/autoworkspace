# P7 · autoworkspace (skills Python/JS) · **SUSTITUIDO por P11 (§1 ci.yml + ci-gate) y P2 (§2–3 release-please y tarball atestado; §4 automerge)**. No lanzar; se conserva como referencia.

```
Repo: Soluciones-Alexendros/autoworkspace.
Hoy la protection exige `check-bump`, un bump manual de versión, que contradice el versionado automático. Hay version.yml, release.yml (publish + attest source archive) y quality.yml/validate.yml.
Tareas:
1. ci.yml con el reusable python (ruff, mypy --strict sobre los scripts Python, pytest con cobertura) + los jobs propios validate e hygiene (hygiene.py y su denylist) dentro de ci-gate.
   Si hay JS (package.json: lint/typecheck), añade el reusable node como segundo job `pipeline-node`, también en needs del ci-gate.
2. Elimina version.yml/check-bump. release-please release-type simple (o python si hay pyproject), con la versión del manifest tomada del último tag (v5.0.0) o de package.json (5.1.0), la que sea mayor, y extra-files para que actualice package.json y los frontmatter de versión de skills si existen.
3. package-kind: tarball del árbol de skills (git archive) + SHA256SUMS + attest-build-provenance (sustituye "Attest source archive").
4. automerge.yml.
Criterios de éxito: ci-gate verde; un PR feat: produce un release minor automático con el archivo y su attestation; no queda ningún check que exija editar versiones a mano.
Último paso obligatorio: actualiza el apartado «P7 · autoworkspace» en la página de Notion de la política (NOTION_POLICY_PAGE).
```
