# Glosario del canon de flota

### Propósito de este documento

- **Objetivos:** Fijar el término canónico de cada concepto del canon, el que se evita y sus excepciones, para que documentación, commits y código usen una sola palabra por cosa.
- **Estructura:** Esta meta-sección → regla de idioma → tabla de términos → bloque máquina que valida la terminología.
- **Contenido a integrar según contexto:** Añade una fila por concepto nuevo y, si la palabra incorrecta es detectable sin falsos positivos, una entrada en el bloque máquina. El validador es `check_terminology` en `tools/validate/skill_links.py`.

## Regla de idioma

La documentación del **canon de flota** (README raíz, `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `SECURITY.md` y `docs/` salvo lo que sigue) va en **español**. La **especificación y la documentación de skills** va en **inglés**: `docs/STANDARD.md`, `docs/TAXONOMY.md`, `docs/harness-integration.md`, `docs/verifiable-closure-migrations.md` y todo `skills/**`.

Los identificadores y el código van en inglés; los commits y los PR, en español. No se traducen ficheros enteros para cumplir la regla: solo se corrigen los que mezclan idiomas.

## Términos canónicos

| Término canónico            | Definición                                                                                                                               | Evitar                                     | Excepciones                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------- |
| **canon de flota**          | Conjunto de reglas, workflows, stacks, plantillas y ADRs que comparten los repos de Soluciones-Alexendros. Vive en `autoworkspace`.      | «repo-standard» como nombre vigente        | Citas históricas en `docs/archives/` y `docs/plans/`                                   |
| **autoworkspace**           | Repo que aloja el producto (catálogo de skills y pipeline agéntico) y el canon de flota.                                                 | «repo-standard» para el host actual        | —                                                                                      |
| **repo-standard**           | Nombre **histórico** del repositorio del canon, archivado. Solo se usa al hablar de su pasado.                                           | Usarlo para el host vigente                | `docs/architecture/decisions/ADR-0001*`, `ADR-0016*`, `CHANGELOG.md`, `docs/archives/` |
| **pipeline agéntico**       | Nombre del producto: el flujo preprogramado especificación → esquemas/tests → código → validación → integración → status. Solo en prosa. | Llamar «pipeline» a un agregado de CI      | —                                                                                      |
| **integración (Fase 1)**    | Fase en que las ramas de tarea entran en `plan/<id>-<slug>` mediante PRs de tarea con squash.                                            | «merge», «fusión» genéricos                | —                                                                                      |
| **publicación (Fase 2)**    | Fase en que el PR del plan entra en `main` y se corta el tag `v*` con su Release.                                                        | «deploy» para el canon                     | —                                                                                      |
| **despliegue**              | Poner en marcha un producto en su hosting real. No aplica al canon.                                                                      | Usarlo para publicar el canon              | —                                                                                      |
| **producción**              | Solo el nombre del entorno `production` de un producto.                                                                                  | «producción» como sinónimo de `main`       | —                                                                                      |
| **rama de plan**            | `plan/<id>-<slug>`: rama de integración del plan.                                                                                        | «rama de integración» informal             | —                                                                                      |
| **rama de tarea**           | Rama corta `<tipo>/<slug>` que sale de la rama de plan y muere en su PR de tarea.                                                        | «rama de feature»                          | Citas históricas                                                                       |
| **PR de tarea**             | PR de una rama de tarea hacia la rama de plan.                                                                                           | «PR parcial»                               | —                                                                                      |
| **PR del plan**             | PR de la rama de plan hacia `main`; lo abre y lo fusiona Alejandro.                                                                      | «PR final»                                 | —                                                                                      |
| **`ci-gate`**               | Check obligatorio y job agregador de la CI. Es el único required.                                                                        | «pipeline» para el agregado de CI          | —                                                                                      |
| **`pipeline-<stack>`**      | Nombre en código de los jobs de CI por stack: `pipeline-python`, `pipeline-node`, `pipeline-rust`, `pipeline-static`, `pipeline-infra`.  | Escribirlo como «pipeline python» en prosa | Nombres de job en YAML                                                                 |
| **etiqueta**                | Marca de GitHub sobre un PR. Las del canon son `hold` y `policy-exception`.                                                              | «label» en prosa española                  | Nombres literales en YAML/CLI                                                          |
| **squash**                  | Método de fusión único permitido: un commit por PR.                                                                                      | `--merge`, `--rebase`                      | —                                                                                      |
| **BEGIN_COMMIT_OVERRIDE**   | Bloque de la descripción del PR del plan con una línea por PR de tarea, que da forma al commit de squash.                                | —                                          | —                                                                                      |
| **release-please**          | Automatización que abrirá el PR de release y creará el tag cuando la GitHub App de flota esté conectada (P13).                           | Usarlo como si ya estuviera activo         | —                                                                                      |
| **tag `v*`**                | Etiqueta SemVer `vX.Y.Z` sobre `main` que dispara la publicación.                                                                        | `vX.Y.Z` inventado o movido a mano         | —                                                                                      |
| **trusted publishing**      | Publicación npm sin token de larga duración, mediante identidad OIDC del workflow.                                                       | —                                          | —                                                                                      |
| **provenance / atestación** | Prueba firmada de que un artefacto se construyó desde un commit y un workflow concretos.                                                 | —                                          | —                                                                                      |
| **ADR**                     | Registro de decisión de arquitectura en `docs/architecture/decisions/`.                                                                  | «decisión» suelta sin ADR                  | —                                                                                      |
| **estados de ADR**          | `Proposed`, `Accepted`, `Superseded by`, `Superseded in part by`, `Deprecated`.                                                          | «aprobado», «vigente», «obsoleto»          | —                                                                                      |
| **excepción de política**   | Etiqueta `policy-exception` más una fila en `.github/policy-exceptions.md` que autoriza tocar rutas de política.                         | Tocarlas sin excepción                     | —                                                                                      |
| **deuda congelada**         | Diagnósticos de ruff/mypy que se toleraban con `per-file-ignores` y overrides. En retirada durante P12.                                  | Usarla como excusa permanente              | —                                                                                      |
| **`not_run`**               | Estado de un paso o gate que no se ejecutó; nunca equivale a PASS.                                                                       | Contarlo como verde                        | —                                                                                      |

## Regla de idioma (términos)

Los términos de esta tabla son canónicos en español. Los nombres de fichero, job, etiqueta, comando y variable se citan literalmente y no se traducen.

## Bloque máquina

El validador `check_terminology` lee este bloque y recorre `*.md`, `*.yml`, `*.yaml` y `*.json` bajo `docs/`, `templates/`, `stacks/`, `.github/` y la raíz. Una línea con `<!-- term-ok: <motivo> -->` queda exenta.

```json
{
  "forbidden": [
    {
      "pattern": "Iniciativas-Alexendros",
      "use": "Soluciones-Alexendros",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    },
    {
      "pattern": "Soluciones-Alexendros/repo-standard(/|\\.git)",
      "use": "Soluciones-Alexendros/autoworkspace",
      "allow_paths": [
        "docs/plans/**",
        "docs/archives/**",
        "CHANGELOG.md",
        ".github/policy-exceptions.md",
        "docs/architecture/decisions/ADR-0001*",
        "docs/architecture/decisions/ADR-0016*"
      ]
    },
    {
      "pattern": "repo-standard ≥",
      "use": "autoworkspace ≥",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    },
    {
      "pattern": "rama de feature",
      "use": "rama de tarea",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    },
    {
      "pattern": "# v[0-9]+\\.x\\b",
      "use": "# vX.Y.Z con el SHA exacto",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    },
    {
      "pattern": "`quality` \\+ `test` \\+ `smoke`",
      "use": "ci-gate",
      "allow_paths": [
        "docs/architecture/decisions/ADR-0003*",
        "docs/architecture/decisions/ADR-0006*",
        "docs/architecture/decisions/ADR-0013*",
        "docs/plans/**",
        "docs/archives/**"
      ]
    },
    {
      "pattern": "(?<!sin )(?<!\\*\\*sin\\*\\* )(label|etiqueta) .?automerge.?",
      "use": "sin etiqueta automerge",
      "allow_paths": [
        "docs/architecture/decisions/ADR-0001*",
        "docs/architecture/decisions/ADR-0006*",
        "docs/architecture/decisions/ADR-0010*",
        "docs/architecture/decisions/ADR-0012*",
        "docs/README.md",
        "docs/plans/**",
        "docs/archives/**"
      ]
    },
    {
      "pattern": "gh pr merge(?![^\\n]*(?i:prohib))[^\\n]*--(merge|rebase)\\b",
      "use": "gh pr merge --auto --squash",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    },
    {
      "pattern": "(?i)\\bpipeline\\b(?=\\s+(de\\s+)?(CI|integraci[oó]n continua|GitHub Actions))",
      "use": "ci-gate",
      "allow_paths": ["docs/plans/**", "docs/archives/**"]
    }
  ]
}
```
