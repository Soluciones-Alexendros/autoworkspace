# Spec: Skill `data-linkml` (nuevo ramo `data` en machineroom)

## Objective

Crear en `machineroom` la skill `data-linkml`, primera del ramo (dominio) `data`,
que habilite al agente para **modelar, validar, generar y evolucionar esquemas y
datos con LinkML** de forma trazable y verificable: clases, slots, relaciones,
vocabularios, instancias YAML/JSON, generadores de artefactos (JSON Schema,
Python/Pydantic, SQL, JSON-LD, SHACL, documentación), conversión de datos y
verificación en capas. Es la habilidad necesaria para el proyecto «Diagnosis y
Actualización del Español-Castellano» (Notion, solo lectura) que ya usa LinkML
1.12.1 con esquema validado y validadores V01–V25, y punto de partida para
cualquier modelado de datos del operador.

Entregables de la skill: `SKILL.md` (normativa machineroom), `references/` de
lectura progresiva, `scripts/` deterministas con smoke test, `assets/` con
plantillas y ejemplos, más los cambios transversales que exige abrir el ramo
`data` (taxonomía, validador de skills, router, índice, changelog).

## Fuentes oficiales y reputadas (recopiladas y verificadas)

Todas verificadas el 2026-11-12. La skill las cita como referencia canónica y
**nunca afirma un comando, flag, versión o generador sin verificarlo** contra la
documentación oficial, `--help` de la versión instalada o context7 (regla de
flota).

### Oficiales (primarias)

| #   | Fuente                              | URL                                                                                                         | Qué aporta                                                                                                                                                                                                                                                                                  |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | Documentación oficial LinkML        | https://linkml.io/linkml/                                                                                   | Tutoriales 1–9, schemas, working with data, generadores, CLI, FAQ, ecosystem                                                                                                                                                                                                                |
| F2  | Repo de herramientas `linkml`       | https://github.com/linkml/linkml                                                                            | Código del CLI y generadores; PyPI `linkml` 1.12.1, Apache-2.0, Python ≥3.10                                                                                                                                                                                                                |
| F3  | Metamodelo y especificación         | https://github.com/linkml/linkml-model                                                                      | Metamodelo del lenguaje (clases ClassDefinition, SlotDefinition, etc.)                                                                                                                                                                                                                      |
| F4  | Instalación oficial                 | https://linkml.io/linkml/intro/install.html                                                                 | `pip install linkml` en venv; imagen OCI oficial `docker.io/linkml/linkml`                                                                                                                                                                                                                  |
| F5  | CLI `linkml validate`               | https://linkml.io/linkml/cli/validate.html                                                                  | `-s/--schema`, `-C/--target-class`, `--fix`, `--config`; sin `-s` valida contra el metamodelo                                                                                                                                                                                               |
| F6  | CLI `linkml lint`                   | https://linkml.io/linkml/cli/lint.html                                                                      | Reglas de calidad del esquema, configuración, `--fix`                                                                                                                                                                                                                                       |
| F7  | CLI `linkml generate` + generadores | https://linkml.io/linkml/cli/generate.html, https://linkml.io/linkml/generators/                            | Generadores: json-schema, python, pydantic, sqlddl, sqlalchemy, jsonld(-context), rdf, sparql, shex, shacl, owl, graphql, protobuf, openapi, markdown, er-diagram, plantuml, java, go, typescript, rust, csv, excel, yaml, prefix, sssom, terminusdb; dashboard de cobertura por feature    |
| F8  | Validación de datos                 | https://linkml.io/linkml/data/validating-data.html                                                          | Estrategias (runtime, JSON Schema, ShEx/SHACL) y límites de cobertura                                                                                                                                                                                                                       |
| F9  | Conversión de datos                 | https://linkml.io/linkml/data/conversion.html                                                               | `linkml-convert` (loaders/dumpers: JSON, YAML, RDF/Turtle, TSV/CSV)                                                                                                                                                                                                                         |
| F10 | Entrypoint `gen-project`            | https://linkml.io/linkml/generators/project-generator.html                                                  | Proyecto completo: `-d`, `-I/--include`, `-X/--exclude`, `-A/--generator-arguments`, `--mergeimports`                                                                                                                                                                                       |
| F11 | Ecosistema                          | https://linkml.io/linkml/ecosystem.html                                                                     | linkml-runtime, linkml-map, linkml-store, schemasheets, schema-automator, linkml-project-copier, linkml-owl, linkml-transformer, SSSOM, OAK, OntoGPT, DataHarmonizer                                                                                                                        |
| F12 | Repos de soporte                    | linkml/linkml-runtime, linkml/linkml-map, linkml/linkml-store, linkml/schemasheets, linkml/schema-automator | Runtime de modelos, mapeos declarativos, almacenamiento, hojas de cálculo, inferencia de esquemas                                                                                                                                                                                           |
| F13 | Repos oficiales Arch                | https://archlinux.org/packages/search/json/?name=python y `python-pip`                                      | `python` 3.14.10 (repo core, incluye el módulo `venv`) y `python-pip` 26.2.2 (extra). Verificado el 2026-11-12                                                                                                                                                                              |
| F14 | AUR                                 | https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=python-linkml                                            | **No existe** paquete `python-linkml` en AUR ni `linkml` en repos oficiales (verificado el 2026-11-12) → pip en venv es la vía de instalación en Arch                                                                                                                                       |
| F15 | Arch Wiki · Python                  | https://wiki.archlinux.org/title/Python                                                                     | Recomienda venv aislado por proyecto para paquetes no disponibles en los repos de Arch; pip global no es vía soportada en Arch                                                                                                                                                              |
| F16 | Metadatos PyPI `linkml==1.12.1`     | https://pypi.org/pypi/linkml/1.12.1/json                                                                    | Sin extras declarados (`provides_extra: null`); dependencias directas: linkml-runtime≥1.12, pydantic≥2.13, rdflib≥7.6, pyshex/pyshexc, sqlalchemy≥2, jsonschema, pyyaml, openpyxl, graphviz, antlr4-runtime… todas con wheels para linux x86_64 (sin compilación: no requiere `base-devel`) |

### Verificación por contexto (context7, API de docs actualizada)

- Library ID documentación: `/websites/linkml_io_linkml` (9 413 snippets, reputación alta)
- Library ID repo: `/linkml/linkml`
- Library ID metamodelo: `/linkml/linkml-model`
- Uso: resolver/consultar antes de afirmar existencia de API, flag o versión.

### Profesionales reputados (secundarias, para contraste)

- Blog/procedimiento propio del operador en Notion (habilidad «Modelar y trabajar
  con LinkML» y sus hijas «Ecosistema y fuentes LinkML» y «Guía práctica y
  pruebas LinkML») — **solo lectura, punto de partida de contenidos**.
- Proyecto «Diagnosis y Actualización del Español-Castellano» (Notion) — caso
  real con esquema LinkML 1.12.1, 19 tablas, validadores V01–V25, adaptadores
  por fuente (BOE API REST, Wikidata SPARQL, MediaWiki), proyecciones SQL y
  JSON-LD. Referencia de caso en la skill, sin acoplar la skill al proyecto.
- Materiales de la comunidad LinkML (tutoriales y FAQ oficiales) como únicas
  guías de procedimiento; no se admite contenido de blogs no verificables.

## Tech Stack

- Skill: Markdown + YAML frontmatter según `docs/STANDARD.md` y
  `templates/SKILL_TEMPLATE.md` de machineroom (spec Agent Skills).
- Scripts: Python 3 stdlib y Bash (sin dependencias nuevas; la skill no instala
  LinkML por su cuenta — lo verifica y usa si está disponible). Exit codes canónicos:
  `0` OK, `1` error/veredicto negativo, `2` input inválido, `3` dependencia
  ausente, `4` permiso.
- Smoke: `scripts/tests/smoke_sh.sh` (patrón de `local-maintenance`).
- Entorno de ejecución LinkML: Python ≥3.10 con `pip install linkml` en venv
  aislado, o imagen OCI `docker.io/linkml/linkml`; versión fijada y registrada
  en cada ciclo (nunca instalación global no justificada).

### Instalación en Arch Linux — un solo script sobre venv

`scripts/bootstrap_arch.sh` configura todo en una pasada (programas del sistema,
venv, librerías y verificación). Inventario verificado (F13–F16):

| Componente          | Origen                             | Elemento                                                                                                                   |
| ------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Sistema             | pacman (repos oficiales, con sudo) | `python` (core) — incluye `venv`; `python-pip` (extra)                                                                     |
| Aislamiento         | `python -m venv`                   | venv dedicado en el directorio de proyecto: `~/Projects/linkml/venvs/linkml`, parametrizable con `--venv-dir`              |
| Librerías Python    | pip **dentro del venv**            | `linkml==1.12.1` (pin exacto) desde `assets/requirements-linkml.txt`; dependencias transitivas con wheels, sin compilación |
| Alternativa sin pip | Imagen OCI oficial                 | `docker.io/linkml/linkml` (documentada, no instalada por el bootstrap)                                                     |

Razones del diseño (verificadas): no existe paquete de LinkML en repos oficiales
ni en AUR (F14); Arch restringe el pip global (externally-managed / PEP 668) y
la Wiki recomienda venv por proyecto (F15). Por eso el bootstrap **nunca** usa
pip global: instala solo `python` + `python-pip` vía pacman y todo lo demás va
al venv.

Contrato del script único:

```text
bootstrap_arch.sh [--apply] [--venv-dir DIR] [--skip-pacman] [--verify]
  default: dry-run (no ejecuta nada, imprime el plan)
  preflight: ¿Arch Linux? ¿pacman? ¿sudo? ¿python ≥3.10? ¿red hacia PyPI?
  1. pacman: python + python-pip (solo si faltan; con sudo y confirmación)
  2. venv: python -m venv <dir>; upgrade de pip dentro del venv
  3. pip: -r assets/requirements-linkml.txt (pin linkml==1.12.1)
  4. verificar: linkml --version + laboratorio (validate/lint sobre assets/) con
     validate_cycle.py; registro: versión, comandos, resultados
  5. resumen final: cómo activar (source <venv>/bin/activate) y próximos pasos
  exit codes canónicos; idempotente (reinstala solo lo que falta)
```

## Project Structure (de la skill)

```text
skills/data-linkml/
├── SKILL.md                      # ≤500 líneas, ≤5000 tokens; H2: Overview, When to Use, Workflow, Tools, Validation Strategy, References
├── references/                   # plano (sin subdirectorios)
│   ├── installation.md            # Arch: bootstrap_arch.sh, pacman + venv, PEP 668, verificación, troubleshooting, desinstalación, alternativa OCI docker
│   ├── ecosystem.md              # mapa de decisión de herramientas y madurez (F11, F12 + Notion ecosistema)
│   ├── schema-authoring.md       # reglas de modelado: clases, slots, rangos, cardinalidad, enums, inlining, URIs, imports
│   ├── validation.md             # capas de validación (sintaxis→metamodelo→lint→instancia→dominio→artefacto), límites del validador oficial
│   ├── generators.md             # catálogo de generadores, cobertura y verificación de artefactos generados
│   ├── official-sources.md       # lista canónica de fuentes F1–F16 + context7 IDs + política de verificación
│   └── project-integration.md    # patrón de integración (Notion/SQL/JSON-LD) + caso español-castellano como ejemplo
├── scripts/
│   ├── bootstrap_arch.sh          # instalación completa en Arch: pacman → venv → pip → verificación (dry-run por defecto, --apply ejecuta)
│   ├── linkml_env.py             # pre-flight: python y linkml presentes, versión, informe (exit 3 si falta)
│   ├── validate_cycle.py         # capas 1–4 (YAML, metamodelo, lint, instancia con -C) + informe Markdown/JSON
│   └── tests/
│       └── smoke_sh.sh           # --help exit 0 + py_compile de cada script + dry-run del bootstrap sin efectos
└── assets/
    ├── requirements-linkml.txt    # pin de librerías del venv: linkml==1.12.1 (sin extras; deps transitivas por wheels)
    ├── schema-template.yaml      # esqueleto mínimo: id, name, prefixes, imports linkml:types, default_range, classes
    ├── instance-valid.yaml       # instancia válida de demostración
    ├── instance-invalid.yaml     # instancia inválida (campo requerido ausente)
```

(El archivo de configuración de lint es `.linkmllint.yaml` por defecto; sus
reglas se documentan en `references/validation.md` con las opciones verificadas
`-c/--config`, `-f/--format` terminal|markdown|json|tsv, `--ignore-warnings` y
`--max-warnings`, sin claves de reglas inventadas.)

## Formato de la skill (frontmatter y normativa)

Conforme a `docs/STANDARD.md`, `docs/TAXONOMY.md`, `README.md` §Nomenclatura y
`templates/SKILL_TEMPLATE.md`:

```yaml
---
name: data-linkml
description: >- # 1–1024 chars, con "Use when" literal y cláusula de exclusión
  [Model and validate data with LinkML: schema authoring, lint, instance
  validation, artifact generation and data conversion, with layered verification
  and provenance records. Use when the operator asks to model data, create or
  fix LinkML schemas, validate data or generate artifacts. Not for dependency
  auditing (→ project-libraries) nor backend application logic (→ role-back).]
license: MIT
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob, Bash, Write"
metadata:
  author: Soluciones-Alexendros
  version: "0.1.0"
  domain: data # ramo nuevo — requiere abrir la taxonomía (ver Boundaries)
  type: orchestrator # flujo multi-paso: encuadrar → diseñar → esquema → verificar/generar → integrar
  language: en
  keywords: "data-linkml, linkml, schema, modelado de datos, validar datos, yaml schema"
---
```

Reglas que debe cumplir el SKILL.md:

- H2 canónicos en inglés: `Overview`, `When to Use` (+ `Tools` por tener scripts).
  Prohibidos: `Usage`, `Structure`, `What it does / Purpose`, `When to use me / Triggering`.
- Descripción en tercera persona con `Use when` y `Not for` literales; flechas
  `→` solo a skills existentes (`project-libraries`, `role-back`).
- Sin trailing whitespace; enlaces relativos solo a archivos existentes;
  `references/` plano; sin residuos (`__pycache__/`, etc.).
- `metadata.execution` solo si se registra un tool en `tools/execution/registry.yaml`
  — **no planificado** para esta skill (los scripts son helpers del agente, no
  operaciones mutadoras del host).

## Contenidos de la skill (mapa de conocimiento)

Procedimiento operativo adaptado de la habilidad Notion (5 fases), con la
disciplina de verificación de machineroom:

1. **Encuadrar** — precisar objetivo, consumidor, límites, datos reales de
   ejemplo, destinos y sensibilidad. Distinguir modelo conceptual → esquema
   LinkML → instancias → artefactos generados.
2. **Diseñar el dominio** — entidades con identidad, relaciones y cardinalidad,
   ciclo de vida, objeto anidado vs referencia por id, ausencia/desconocido/no
   aplicable, unidades y temporalidad, vocabularios cerrados solo si se
   conocen. Separar entidad/recurso/fuente/versión/ficha y atribución de
   transcripción/inferencia (necesario para el proyecto español-castellano).
3. **Escribir el esquema** — YAML con `id`, `name`, `prefixes`, `imports`
   (`linkml:types`), `classes`/`slots`; tipos, `required`, cardinalidad, rangos,
   enums; reutilizar slots por significado real; una raíz (`tree_root`) cuando
   el formato la necesite; al menos una instancia válida y una inválida por
   regla crítica.
4. **Verificar y generar** — orden estricto: YAML bien formado → `linkml validate`
   (metamodelo) → `linkml lint` → `linkml validate -s -C` (instancia, casos
   positivo y negativo) → controles de dominio propios (unicidad, integridad
   referencial, procedencia — el validador oficial no los cubre: patrón V08–V25
   del proyecto). Generar solo artefactos necesarios y probar el artefacto de
   salida; no asumir equivalencia semántica entre generadores.
5. **Integrar y evolucionar** — esquema canónico versionado y proyecciones;
   cambios compatibles vs rupturas, migración y rollback antes de tocar
   contratos; integración con Notion/SQL como proyección con mapeo y pérdida
   semántica evaluada; sensibilidad de datos.

Formato de entrega del agente: resumen (objetivo, recomendación, estado de
verificación), modelo, artefactos con rutas, pruebas (comando, entradas válidas
e inválidas, resultado real o «no ejecutado», reglas no cubiertas), decisiones
pendientes. Registro mínimo de ejecución: entorno y versiones, entradas con
hash, operación exacta, resultado y código de salida, cobertura, siguiente paso.

Restricciones de conducta heredadas de la habilidad Notion: no atribuir
veracidad/vigencia a un dato por cumplir un esquema; no inventar comandos,
flags ni versiones; no `--fix`, migraciones ni sobrescrituras destructivas sin
revisar alcance y autorización; no raspar fuentes sin API por el hecho de no
tenerla; no instalar dependencias globales sin justificación.

## Commands (validación del repo, no de la skill)

```bash
uv sync --frozen --project tools          # entorno del validador (una vez)
make validate                              # o: uv run bash run-validation.sh
bash skills/data-linkml/scripts/tests/smoke_sh.sh
bash skills/data-linkml/scripts/bootstrap_arch.sh            # dry-run: muestra el plan
bash skills/data-linkml/scripts/bootstrap_arch.sh --apply --verify   # instala y comprueba (sudo para pacman)
python3 tools/skill-router/route.py --interactive   # prueba de routing
python3 tools/skill-index/generate.py --sync-docs   # regenerar catálogo
```

## Testing Strategy

- **Validación estática**: `make validate` (skill_spec.py + skill_links.py +
  paridad de catálogo) en verde; exige actualizar el validador para el dominio
  `data` (ver Boundaries).
- **Smoke de scripts**: `scripts/tests/smoke_sh.sh` — `--help` exit 0 y
  `py_compile` de cada `.py` (sin dependencias de red); para `bootstrap_arch.sh`
  el smoke ejecuta el modo dry-run (sin sudo ni red, sin efectos secundarios) y
  verifica el plan impreso.
- **Prueba funcional del bootstrap (Arch)**: ejecución real en la máquina del
  operador con venv en ruta temporal: pacman resuelve `python`/`python-pip`,
  venv creado, `linkml==1.12.1` instalado, `linkml --version` correcto y
  laboratorio verde. Segunda pasada idempotente (no reinstala). Después se
  borra el venv temporal.
- **Prueba funcional de la skill**: con un laboratorio mínimo (assets): esquema
  válido contra metamodelo, lint sin errores, instancia válida aceptada e
  inválida rechazada (`linkml validate -s -C`), generación de un artefacto
  (json-schema) y comprobación de cobertura. Resultado registrado con versión
  de LinkML ejecutada.
- **Prueba de routing**: `route.py` con prompts típicos («valida este esquema
  linkml», «modela estas fichas de datos») devuelve `data-linkml` entre los 3
  primeros; triggers añadidos en `intent-map.yaml`.

## Boundaries

- **Always**: respetar STANDARD.md y la taxonomía; verificación de comandos
  contra la versión instalada y documentación oficial antes de afirmarlos;
  scripts deterministas con exit codes canónicos y salida estructurada
  (JSON/Markdown); referencias solo a URLs oficiales verificadas; responder en
  español. El bootstrap: dry-run por defecto, idempotente, pip solo dentro del
  venv, y preflight que detecta Arch/pacman/sudo/red antes de tocar nada.
- **Ask first**: abrir el ramo `data` en la taxonomía (cambio normativo: se
  propone en el PR como exige TAXONOMY.md); modificar `tools/validate/skill_spec.py`
  (`DOMINIOS`, regex de prefijos `SKILL_TOKEN_RE`/`ARROW_RE` para `data`);
  cualquier cambio en `docs/TAXONOMY.md` o `README.md` que altere «17 skills en
  5 dominios»; registrar tool en `tools/execution/registry.yaml` (no planificado);
  instalar paquetes del sistema vía pacman (el bootstrap pide confirmación
  explícita con sudo y lista los paquetes exactos).
- **Never**: editar la página Notion «LinkML» ni sus hijas (solo lectura);
  instalar LinkML globalmente; afirmar versiones/flags/generadores sin
  verificación (context7 o `--help` local); incluir en la skill datos privados
  del proyecto (solo el patrón genérico y ejemplos ficticios); commitear ni
  pushear sin pedirlo (norma del operador).

## Cambios transversales requeridos (abrir el ramo `data`)

| Pieza                                | Cambio                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `docs/TAXONOMY.md`                   | Dominio `data` en lista cerrada y fila de `data-linkml` en el índice (marcador SKILL-INDEX regenerado) |
| `tools/validate/skill_spec.py`       | `DOMINIOS` + `data`; regex `SKILL_TOKEN_RE` y `ARROW_RE` aceptan prefijo `data-`                       |
| `tools/skill-router/intent-map.yaml` | Intents: modelado de datos, linkml, esquema, validar datos, yaml schema…                               |
| `skill-index.json`                   | Regenerado con `generate.py --sync-docs`                                                               |
| `README.md`                          | «17 skills en 5 dominios» → 18 en 6                                                                    |
| `CHANGELOG.md`                       | Entrada del cambio (minor de repo; skill nace en `0.1.0`)                                              |

## Success Criteria

1. `make validate` en verde con la skill presente (incluido el validador ya
   ampliado para `data`).
2. `bash skills/data-linkml/scripts/tests/smoke_sh.sh` en verde.
3. `SKILL.md` ≤500 líneas y ≤5000 tokens, H2 canónicos, descripción con
   `Use when`/`Not for` y flechas válidas.
4. Laboratorio funcional ejecutado y registrado: esquema válido (metamodelo),
   lint limpio, instancia válida aceptada, inválida rechazada, artefacto
   json-schema generado y comprobado, con la versión de LinkML usada anotada.
5. `route.py` enruta al menos 3 prompts típicos hacia `data-linkml` en el top 3.
6. Las 6 `references/` existen, son planas y enlazan solo a URLs oficiales
   verificadas (F1–F12) o a archivos propios de la skill.
7. La página Notion «LinkML» y sus hijas no han sido modificadas.
8. `bootstrap_arch.sh` probado en Arch: dry-run correcto, venv funcional con
   `linkml==1.12.1`, `linkml --version` coherente, laboratorio verde y segunda
   pasada idempotente.

## Open Questions

1. ¿`type: orchestrator` es el adecuado, o prefieres `atomic`? (propongo
   orchestrator por el flujo multi-paso).
2. ¿Los scripts se mantienen como helpers de solo lectura + informe, o quieres
   además un wrapper mutador (p. ej. `gen_artifacts.py`) que escriba artefactos
   en el repo de trabajo? (propongo sí, con `--dry-run` por defecto).
3. ¿El nombre `data-linkml` es definitivo? (alternativa: `data-modeling`, pero
   `data-linkml` encaja con la convención `<ramo>-<herramienta>` y deja hueco
   para futuras `data-*`).
4. ¿La skill debe citar el proyecto español-castellano por su nombre en
   `references/project-integration.md`, o mantenerlo anónimo como «caso de
   referencia»? (propongo citarlo como caso real documentado en Notion, sin
   datos).
5. ¿Abrimos el ramo `data` en este mismo trabajo (cambios transversales) o
   primero solo la skill con dominio `plan` temporal y la apertura va en PR
   separado? (la taxonomía exige proponer el dominio en el PR; propongo abrirlo
   en el mismo PR).
6. ¿Pin exacto `linkml==1.12.1` en `requirements-linkml.txt` o rango `~=1.12`?
   (propongo pin exacto: versionado reproducible y la skill declara en cada
   ciclo la versión realmente ejecutada).
7. ¿Ubicación por defecto del venv? **Resuelto (2026-11-12):** `~/Projects/linkml/venvs/linkml`,
   con todos los entornos bajo `~/Projects/linkml/venvs/`.
8. ¿El bootstrap instala también `docker` como ruta alternativa OCI, o solo
   documenta la imagen `docker.io/linkml/linkml`? (propongo solo documentarla).
