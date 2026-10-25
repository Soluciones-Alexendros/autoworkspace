# Seguridad de GitHub Actions

Contrasta esta lista con la guía vigente antes de aplicarla:

- https://docs.github.com/en/actions/reference/security/secure-use
- https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/
- https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases

Si una URL no responde, dilo en el informe. No la sustituyas por un número de discusión sin abrir.

## Procedimiento de pinning

Hazlo para cada `uses:` de un tercero, y también para `actions/*` y `github/*` cuando el repo sea crítico. No des por bueno un SHA solo porque `GET /commits/{sha}` responde 200: eso prueba que el objeto existe, no que sea la release que crees.

1. Fija owner, repo y tag de la release que vas a pinnear (`actions/checkout`, `v7.0.1`).
2. `gh api repos/OWNER/REPO --jq '{fork:.fork,full_name:.full_name}'`. Si `fork` es true, descarta el pin.
3. `gh api repos/OWNER/REPO/git/ref/tags/TAG`.
4. Si `object.type` es `commit`, ese SHA es el pin.
5. Si `object.type` es `tag` (tag anotado), `gh api repos/OWNER/REPO/git/tags/OBJECT_SHA` y usa `object.sha`. Tiene que ser un commit.
6. `gh api repos/OWNER/REPO/commits/COMMIT_SHA --jq .sha` debe ser exactamente ese commit.
7. Escribe `uses: owner/repo@COMMIT # vX.Y.Z`.
8. No hagas commit de `@vX`, `@main`, `@master` ni de un placeholder.

Los callers canónicos viven en `stacks/<stack>/ci.yml` y los reusables en `.github/workflows/reusable-*.yml` (pinea SHA de autoworkspace). Los composite actions de esta skill (`actions/`) se alinean a esos SHAs. Si un digest falla verificación, marca `[PENDIENTE]` y no inventes el SHA.

Mantén los pins con Renovate (`github-actions`), en pull requests revisables. La política del repo o de la org puede exigir `sha_pinning_required`.

Immutable releases evitan mover el tag y los assets de una release ya publicada. El pin a commit sigue siendo la referencia que el workflow debe usar. No hay, en la política nativa, un interruptor que obligue a consumir solo immutable releases; el control que sí existe es el de SHA completo.

## Triggers peligrosos

`pull_request_target` y `workflow_run` ejecutan el workflow del repo base, con secretos y con el `GITHUB_TOKEN` de ese repo, aunque el código venga de un fork.

No hagas checkout de `github.event.pull_request.head.sha` (ni del head de un fork) en esos triggers si después el job ejecuta ese código. Separa un workflow sin privilegios, que solo produce artefactos ya evaluados, de otro que comenta o etiqueta.

Un entorno con required reviewers para runs de forks es un complemento, no un sustituto de esa separación.

## Permisos

Declara `permissions` en el workflow. El defecto es `contents: read`. Un job que fija `permissions` reemplaza las del workflow; los ámbitos no indicados quedan en none.

Sube el ámbito solo en el job que lo usa:

- `contents: write` para publicar una release.
- `pull-requests: write` para comentar en un pull request.
- `actions: write` para subir artefactos.
- `id-token: write` y `attestations: write` para attestations. `contents: read` en ese mismo job. No pongas `id-token: write` en el workflow entero.

`persist-credentials: false` en `actions/checkout` cuando el token no hace falta después del clone. `gh` debe recibir `GH_TOKEN: ${{ github.token }}` en el paso que lo usa.

## Script injection

No interpoles en `run:` títulos, cuerpos, nombres de rama, `github.head_ref` ni el mensaje de un tag. Pasa el valor por entorno y léelo desde el script.

Esto también vale para el nombre de la versión dentro de `node -e`, `python -c` o `awk`. Un tag `v1.2.3'; ...` no debe poder romper el script. Valida el formato y usa el valor solo desde el entorno.

En `actions/github-script`, lee `process.env`. No metas `${{ }}` dentro de un template literal de JavaScript.

## Secretos

Secretos de despliegue en un `environment` con protection rules cuando el riesgo lo justifique. No los escribas en logs, cachés ni artefactos. No cachees `~/.aws`, `~/.ssh` ni tokens de npm o pip.

El escaneo de secretos va en cada pull request y en cada push a la rama por defecto, sin filtro `paths`: un required check que no aparece en el PR no protege la rama. Los comentarios del escáner solo en `pull_request`, con `pull-requests: write` en ese job. No subas el SARIF si puede incluir el secreto.

Un secreto en el historial está comprometido. Rota el valor. No lo dejes en un artefacto de CI.

`gitleaks-action` v3 pide `GITLEAKS_LICENSE` en cuentas de organización y no en cuentas personales. No inventes ni commitees la licencia. Si falta, el ítem queda `[PENDIENTE]`.

## Instalación de actionlint

No instales actionlint con `curl | bash` contra la rama `main`. Baja el asset de una release concreta y comprueba el SHA-256 publicado en `actionlint_<version>_checksums.txt` de esa misma release. El checksum de linux amd64 de v1.7.12, leído de ese archivo el 2026-09-23, es `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`. En otra arquitectura, resuelve el asset correspondiente. No reutilices el hash amd64.

Desde v1.7.11 el proyecto publica attestations. `gh attestation verify --repo rhysd/actionlint <archivo>` es el complemento del checksum, si `gh` está autenticado.

## OIDC

Sustituye claves de cloud de larga duración por OIDC (`id-token: write` solo en el job que asume el rol), con el subject limitado a repo, rama y entorno. Para npm y PyPI, trusted publishing en lugar de un token de API persistente.

## Self-hosted runners

No uses self-hosted runners en repos públicos. En privados: runners efímeros, sin workspace reutilizado, egress restringido. Anota en el informe qué jobs los necesitan.

## Incidentes de referencia

Comprueba el relato en la guía de secure use o en el aviso del proyecto antes de repetir detalles en un informe.

- **tj-actions/changed-files (marzo 2025):** un tag mutable pasó a apuntar a un commit que filtraba secretos por los logs. El pin a SHA completo habría seguido en el commit anterior.
- **reviewdog / trivy-action (marzo 2025):** compromiso encadenado de acciones de terceros. Trata cada acción como una dependencia: pin, revisión y actualización en un PR.

## Attestations

Para un binario, el job que firma lleva `id-token: write`, `contents: read` y `attestations: write`, y usa `actions/attest-build-provenance` (o `actions/attest`) con el SHA verificado. No actives ese paso con los permisos de escritura de la release en el mismo job si puedes separarlos. En repos privados hace falta un plan que incluya attestations; si la API lo rechaza, es `N/A` justificado, no un SHA inventado.
