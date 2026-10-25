# P1 · repo-standard · Núcleo de CI reutilizable + ci-gate + ADRs (MAJOR v2.0.0) · ✔ HECHO

Estado (verificado el 25/10/2026): PR #3 fusionado a las 08:38 (hora de Madrid), con `ci-gate` verde en main y la prueba roja/verde (`de18510`/`631fa31`). Entró con merge commit porque el ruleset que dejó el agente solo admite merge. No hay que relanzarlo: su contenido e historial entran en autoworkspace con P11, y el «v2.0.0» pasa a ser autoworkspace v6.0.0.

```
Repo: Soluciones-Alexendros/repo-standard (rama nueva feat/ci-reusable-ci-gate, un PR).
Contexto: un solo desarrollador (Alejandro) que trabaja con agentes de IA. Objetivo de flota: PR → todos los checks verdes → squash-merge automático sin revisión. El único check obligatorio en toda la flota será el job `ci-gate`. Lee docs/architecture/decisions/ (ADR-0001…0011) y AGENTS.md antes de tocar nada.
AUTORIZACIÓN EXPRESA DE ALEJANDRO (25/10/2026): puedes sustituir ADR-0003 y ADR-0006 y cambiar el contrato de checks (esto es MAJOR según ADR-0010).

Tareas:
1. ADRs nuevos con el formato del canon (frontmatter + meta-sección):
   - ADR-0012 «Solo-dev con IA: auto-merge sin revisión». Supersede ADR-0006: se elimina la etiqueta `automerge` como requisito; 0 aprobaciones; sin bypass, ni siquiera el admin; break-glass = desactivar el ruleset (queda en el audit log) y reactivarlo; etiqueta opcional `hold` para excluir un PR.
   - ADR-0013 «Check único `ci-gate`». Supersede ADR-0003 en lo relativo a los required checks: las fases siguen siendo quality→test→build→smoke, pero solo `ci-gate` es required, fijado a integration_id 15368 (GitHub Actions).
   - ADR-0014 «Versionado release-please + packaging por stack».
   Marca ADR-0003 y ADR-0006 como "Superseded by …". Actualiza README, AGENTS.md, REUTILIZACION.md, CONTRIBUTING.md y docs/guides/testing.md para que no quede ninguna mención contradictoria (comprueba con grep "automerge", "required checks", "label").
2. Reusable workflows (on: workflow_call) en .github/workflows/:
   - reusable-node.yml: inputs node-version (default 22), package-manager (auto por lockfile: pnpm/npm), coverage-threshold (80), run-build (true), run-smoke (true), e2e (false), working-directory.
     Jobs: quality (format:check, lint, typecheck, título de PR), test (tests + coverage con umbral), build, smoke y security (dependency-review-action solo si el repo es público).
   - reusable-rust.yml: msrv opcional, clippy-pedantic (true).
     Jobs: quality (cargo fmt --check; cargo clippy --all-targets --all-features -- -D warnings [-W clippy::pedantic convertido en error por -D warnings]), test (cargo test + cargo llvm-cov --fail-under-lines N), build (cargo build --release --locked), smoke (binario --version/--help), security (cargo deny check o cargo audit, el que ya use el repo).
   - reusable-python.yml (uv): ruff format --check, ruff check con select E,F,W,I,B,UP,SIM,C90,N,PL,RUF y max-complexity 10, mypy --strict, pytest --cov --cov-fail-under=N, uv build, smoke.
   - reusable-static.yml: build si existe y comprobación de enlaces/HTML con lo que el repo ya tenga; sin herramientas nuevas.
   - Título de PR: paso bash en quality, solo en eventos pull_request. Valida github.event.pull_request.title contra
     ^(feat|fix|perf|refactor|docs|test|build|ci|chore|revert|style)(\([a-z0-9._/-]+\))?!?: .{1,100}$
     y falla con un mensaje claro. Pásalo por variable de entorno, nunca interpolado en el script (evita inyección).
   - Todas: `permissions: {}` arriba y mínimos por job; acciones fijadas por SHA completo con comentario `# vX.Y.Z`; timeout-minutes en cada job; persist-credentials: false en checkout.
3. Plantilla de caller en stacks/<stack>/ci.yml (reemplaza los *.snippet.yml):
   - on: pull_request (types: opened, synchronize, reopened, edited, ready_for_review) y push a main.
   - concurrency: group ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}, cancel-in-progress true en PR.
   - job `pipeline` con uses: Soluciones-Alexendros/repo-standard/.github/workflows/reusable-<stack>.yml@<SHA> # v2.0.0
   - job `ci-gate` (name: ci-gate) con needs: [pipeline] y if: always(). Paso bash que lee toJSON(needs) por env y falla si algún result es distinto de success (lista opcional de skips permitidos).
     El ci-gate va en el caller, NO en el reusable: así el check se llama exactamente `ci-gate` y no `pipeline / ci-gate`.
4. Migra el propio ci.yml de repo-standard a este patrón (stack infra/estático: actionlint + scripts/check-structure.sh + smoke.sh) emitiendo `ci-gate`. scripts/check-structure.sh debe seguir prohibiendo dependabot.yml.
5. CHANGELOG [Unreleased] con BREAKING: required checks → `ci-gate`.

Criterios de éxito (verificables):
- PR con título Conventional; actionlint verde; el check `ci-gate` aparece en el PR con ese nombre exacto (gh pr checks).
- Un PR de prueba con un fallo deliberado en test deja ci-gate en failure; revertido, vuelve a success. Enlaza ambos runs.
- grep -rn "uses: .*@v[0-9]" .github/workflows stacks devuelve 0 líneas (todo por SHA).
- ADR-0003/0006 marcados Superseded; ningún doc exige la etiqueta automerge.
Último paso obligatorio: actualiza el apartado «P1 · repo-standard núcleo CI» en la página de Notion de la política (NOTION_POLICY_PAGE) (estado, URL del PR, runs verde/rojo de prueba, fecha y hora de Madrid).
```
