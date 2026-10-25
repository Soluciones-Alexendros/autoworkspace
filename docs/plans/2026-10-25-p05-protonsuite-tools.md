# P5 · protonsuite-tools (CLI Node + imagen OCI)

```
Repo: Soluciones-Alexendros/protonsuite-tools. Paquete @alexendros/protonsuite-agent (private: false); ya publica imagen en GHCR y usa semantic-release (.releaserc.json, release-preview.yml, pr-title.yml).
Tareas:
1. Adopta el caller node de autoworkspace@<SHA> # v6.x + ci-gate.
   Mueve a jobs incluidos en ci-gate: Knip, license-check, zizmor, actionlint, markdown/link check, E2E GreenMail y Pass, Docker build smoke y Validate Renovate config. La cobertura se mantiene con su umbral actual (coverage:check).
2. Sustituye semantic-release por release-please (release-type node, versión del manifest = último tag v1.7.3). Elimina .releaserc.json, release-preview.yml y pr-title.yml (el título lo valida el reusable), y sus dependencias.
3. Packaging en release.yml: package-kind npm-pack (tarball adjunto) + oci (Dockerfile y Dockerfile.bridge → dos imágenes ghcr.io/soluciones-alexendros/protonsuite-tools[-bridge]:<semver>), SHA256SUMS y attest-build-provenance (también push-to-registry para las imágenes).
   Publicar en npmjs.org solo si ya se hacía antes; si se hace, con trusted publishing/provenance (npm publish --provenance), nunca con un token en claro.
4. Elimina coverage-badge.yml si hace push directo a main (el ruleset lo bloqueará); sustitúyelo por el resumen de cobertura en el job summary.
5. automerge.yml.
Criterios de éxito:
- ci-gate verde.
- Release v1.8.0 (o la que corresponda) con el .tgz, SHA256SUMS e imágenes en GHCR con attestation verificable: gh attestation verify oci://ghcr.io/soluciones-alexendros/protonsuite-tools:<v> -o Soluciones-Alexendros.
Último paso obligatorio: actualiza el apartado «P5 · protonsuite-tools» en la página de Notion de la política (NOTION_POLICY_PAGE).
```
