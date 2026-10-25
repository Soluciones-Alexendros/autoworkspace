# Patrones de CI/CD en GitHub Actions

Adapta el patrón al stack. Usa `stacks/<stack>/ci.yml` del canon (host autoworkspace) pineado por SHA. No copies un caller de un stack sobre otro ecosistema. Rulesets como código: `rulesets/` (P2/P10).

| Stack | Setup | Comprobación mínima |
|---|---|---|
| Node | `actions/setup-node` con versión declarada en `.nvmrc` o `node-version` | `npm ci` y los scripts que el manifiesto declara. Si el script no existe, el job falla. |
| Python | `actions/setup-python` | Instalar desde el lockfile (`uv lock`, `poetry.lock`, `requirements.txt` pineado). No uses un `pip install` sin lock si el repo ya tiene uno. |
| Rust | toolchain fijada en `rust-toolchain.toml` o acción pineada | `cargo test --locked` |
| Go | `actions/setup-go` | `go test ./...` con `go.sum` presente |

Cada `uses:` se pinea con el procedimiento de `references/actions-security.md`. Preferir `cache: npm` (o el equivalente del setup oficial) a una caché manual. Si hace falta `actions/cache`, la clave incluye el hash del lockfile y `restore-keys` solo degrada dentro del mismo gestor. No mezcles gestores en la misma caché. No cachees directorios de credenciales.

No uses `npm test --if-present` ni el equivalente de otros gestores. Un script ausente tiene que fallar el job, o el checklist marca el check `N/A` con motivo. Un required check que se salta solo no cuenta como verde.

## Matrices

Una matriz de sistema operativo por versión del runtime solo donde aporte señal. Una librería publicada sí. Una aplicación con un solo destino, no. `fail-fast: false` cuando quieras ver todos los fallos. `fail-fast: true` en pull requests si el minuto de CI importa.

Separa el job rápido (lint y unit) del lento (integración). El lento declara `needs` del rápido. El job de integración instala el runtime otra vez: `needs` no arrastra el workspace.

## Required checks y paths

Un check obligatorio tiene que ejecutarse en cada pull request a la rama protegida y conservar el mismo nombre. Un filtro `paths` hace que el check no se cree, y la protección se queda esperando o considera el check omitido.

`actionlint` es barato: ejecútalo siempre. El escaneo de secretos también va en cada pull request y en cada push a la rama por defecto, con historial completo (`fetch-depth: 0`).

## Entornos

`environment: production` con required reviewers para desplegar a producción. Secretos y variables del entorno, no del repo, cuando el despliegue lo justifique. El job de despliegue pide `id-token: write` solo si usa OIDC.

`concurrency` de CI por rama, con `cancel-in-progress: true`. En despliegue, el grupo es el entorno y `cancel-in-progress: false`.

`timeout-minutes` en cada job. Un valor de partida: 10 para lint, 15 para unit tests, 30 para integración.

## Despliegue y rollback

Elige la estrategia por el riesgo. Si el repo no despliega, el ítem es `N/A`.

| Estrategia | Cuándo | Requisito |
|---|---|---|
| Rolling | Servicio sin estado y bajo riesgo | La versión N convive con N-1 |
| Blue/green | Corte inmediato | Dos entornos y un cambio de tráfico reversible |
| Canary | Mucho tráfico | Métrica y criterio de aborto |
| Feature flags | Separar deploy de release | Quién retira el flag y cuándo |

Sin rollback documentado, un repo que sí despliega no pasa el gate. El rollback redespliega el artefacto de la versión anterior. No reconstruye un commit viejo en caliente. Conserva al menos las dos versiones anteriores.

Imágenes firmadas y provenance SLSA solo en repo crítico o si el usuario las pide. Ver permisos en `references/actions-security.md`.

## Linting local

El mismo `actionlint` pineado que en CI tiene que poder correr en local. Documenta el comando en CONTRIBUTING cuando el repo tenga esa guía. No hace falta CONTRIBUTING solo para alojar ese comando: puede vivir en el README si el repo es pequeño.
