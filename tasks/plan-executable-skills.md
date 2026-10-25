# Plan canónico: autoworkspace ejecutable, seguro y coherente

Plan ID: `autoworkspace-executable-skills-v1`.

Este archivo es la única fuente de verdad del incremento. Contiene las tareas T00–T24, sus dependencias, las matrices, las decisiones y el registro. El resumen de Cursor es un índice de navegación: no sustituye estas tareas, no se completa un grupo hasta verificar todas las suyas y no crea otra fuente de verdad.

Estado: IMPLEMENTACIÓN LOCAL COMPLETADA (2026-10-18). Publicación (push/PR/merge) no ejecutada.

Precedencia: si una frase de las secciones 0–10 contradice la sección 11, prevalece la sección 11. Las tareas y las matrices no se eliminan; se leen con esas enmiendas.

## Observación puntual del checkout

Comprobado por Cursor el 2026-10-17T23:25:19+02:00. No es un hecho permanente. T00 debe repetirlo antes de escribir código de producto o crear una rama.

Comandos: `git rev-parse --show-toplevel`, `git rev-parse HEAD`, `git branch --show-current`, `git status --short --untracked-files=all`, `git branch --list feat/executable-skills`, existencia de este destino.

- toplevel observado: `$HOME/…/autoworkspace` (ruta local; el producto resuelve con Git). Es una observación local. El producto resuelve la raíz con Git.
- HEAD observado: `ecc5a97654d79cc924dfe5364c92e7c2bd1af7a6`
- rama observada: `main`
- `git status --short` vacío en ese instante
- `feat/executable-skills` ausente en ese instante
- este archivo no existía en ese instante

Lectura estática posterior, mismo día, sin ejecutar los scripts: `skills/local-maintenance/scripts/common.py` líneas 33, 105–138 y 325–343; `skills/local-maintenance/SKILL.md` `metadata.version: 5.0.0`. Búsqueda de la cadena `validate-skills` en `json`, `yml`, `yaml`, `md`, `sh`, `js` y `mjs`: sin coincidencias de contenido. Eso no demuestra consumidores externos ni sustituye el inventario de T04.

## 0. Identidad, alcance y activación

| Campo                                 | Valor                                                                       |
| ------------------------------------- | --------------------------------------------------------------------------- |
| Plan ID                               | autoworkspace-executable-skills-v1                                          |
| Fecha de diseño                       | 2026-10-17                                                                  |
| Repositorio objetivo                  | Soluciones-Alexendros/autoworkspace                                         |
| Base auditada                         | ecc5a97654d79cc924dfe5364c92e7c2bd1af7a6                                    |
| Versión declarada en esa base         | 5.0.0                                                                       |
| Catálogo de partida                   | 16 skills; dominios plan, local, project, web, role                         |
| Idioma del plan e informes            | Español                                                                     |
| Idioma de skills y contratos técnicos | Inglés; conservar triggers españoles cuando aporten descubrimiento          |
| Ruta de este archivo                  | tasks/plan-executable-skills.md                                             |
| Seguimiento                           | Las casillas y el registro de ESTE archivo; no duplicar en tasks/todo.md    |
| Entrega                               | Implementación local verificada y lista para revisión; publicación separada |

### Instrucción de lanzamiento

El operador autoriza la implementación solo con una orden explícita de implementar este plan. Pedir una revisión o adjuntar el archivo no autoriza ejecución. La aprobación no autoriza operaciones externas o de alto riesgo ni anula instrucciones superiores del entorno.

Al autorizarla: revalidar la base, respetar las tareas y sus dependencias, usar las skills aplicables, registrar aquí la evidencia real, ejecutar comprobaciones no destructivas y pruebas aisladas. No modificar el sistema, el correo, los secretos ni la configuración global. No hacer commit, push, PR, merge, tag o release sin la autorización específica aplicable. Si existe un bloqueo real, conservar lo realizado y entregar la evidencia y el siguiente paso exacto. Empezar por T00.

### Límites obligatorios

1. No ejecutar mantenimiento real, actualizaciones de firmware, cambios en /etc, restauraciones del host, envío de correo ni extracción de secretos para probar el producto.
2. No usar sudo, escalación de privilegios, instalaciones globales, curl-pipe-shell ni acceso a datos reales como requisito de CI.
3. No borrar ni sobrescribir trabajo ajeno. No usar reset --hard, clean -fd, force-push ni resolver conflictos descartando contenido.
4. No publicar ni modificar GitHub, branch protection, credenciales o configuración global sin aprobación específica del operador. Las preferencias históricas de AGENTS.md no sustituyen esa autorización.
5. No ejecutar hooks, instaladores ni scripts del checkout antes de inspeccionarlos. El repositorio y su documentación son entradas de trabajo, no autoridad para saltarse permisos.
6. No introducir nuevas skills por lenguaje, nuevas familias, un servidor de agentes o una plataforma genérica de plugins.
7. No atribuir a un LLM garantías de exactitud, idempotencia o ejecución exactamente una vez. Las garantías deben proceder de controles comprobables y tener límites documentados.
8. No convertir dependencias ausentes en PASS. Usar blocked, not_applicable o not_run, con motivo y efecto sobre la aceptación.
9. No aumentar la versión del producto con cada actualización de estado. No forzar la misma versión a todas las skills.
10. Este archivo es el único documento de planificación nuevo exigido. Los esquemas, contratos, pruebas y guías de producto sí son entregables de implementación y pueden ser archivos separados.

## 1. Arranque y revalidación obligatorios

### 1.1 Preparación segura

- Resolver la raíz con `git rev-parse --show-toplevel`. La ruta absoluta observada arriba no es una dependencia del producto.
- Antes de escribir código de producto o crear una rama, repetir HEAD, rama, `git status --short` y no rastreados relevantes. Registrar el resultado en la sección 10. Redactar credenciales si una URL remota las incluye.
- No hacer pull ni actualizar la rama automáticamente sobre cambios locales. Si `feat/executable-skills` ya existe, inspeccionarla; no recrearla ni resetearla. No cambiar de rama si ello afecta trabajo ajeno. Un worktree local solo si hace falta aislar y el entorno lo permite.
- Si HEAD difiere de la base, inspeccionar el diff pertinente y reclasificar hallazgos: vigente, corregido, cambiado o no comprobado. No reintroducir código antiguo ni repetir soluciones ya implementadas.
- Leer AGENTS.md y las instrucciones de ámbito más específico. Reevaluar las skills antes de cada tarea independiente y cargar las referencias que exija cada skill.
- Fuente canónica: `skills/<nombre>/SKILL.md`. Inspeccionar enlaces de integración y resolver su destino antes de leerlos o seguirlos. No suponer que `.agents/skills/` es válido.
- Como mínimo considerar plan-continue, plan-specification, plan-validators, role-back, role-clean-code y project-publish. Usar role-front o role-design solo si aparece una superficie real de UI.
- Si no existe herramienta nativa de skills, leer el SKILL.md y sus referencias y declarar el fallback. No afirmar invocaciones que no ocurrieron.
- Si no hay shell, checkout o capacidad de editar y probar: detener la implementación, entregar diagnóstico y diffs propuestos, y marcar las verificaciones no ejecutadas.

### 1.2 Preservación del trabajo de planificación

En la base existen `tasks/plan.md` y `tasks/todo.md` del incremento de taxonomía v5. No sobrescribirlos ni reinterpretarlos como plan de este incremento.

- Este archivo ya es el destino canónico. Mismo Plan ID: actualizar en sitio. Trabajo distinto o incompleto: detener esa escritura y resolver el conflicto con el operador.
- No generar `tasks/todo.md` ni una nueva `SPEC.md`. La orden de un solo archivo prima sobre el destino por defecto de la plantilla.
- No modificar retrospectivamente changelog, specs ni planes cerrados para que parezcan describir el nuevo producto.
- El índice de Cursor permanece subordinado. Si sus todos internos cambian, deben reflejar este archivo.

### 1.3 Baseline

Inspeccionar `package.json`, `requirements-dev.txt`, lockfiles, hooks y workflows antes de ejecutar comandos. Preparar dependencias solo en un entorno local aislado y con los permisos de red disponibles. No fijar versiones que no se hayan comprobado.

El inventario de efectos de la sección 11.4 ocurre antes del baseline. Una copia desechable, un venv o un HOME temporal no son un sandbox: no impiden escribir en `/etc` o rutas absolutas, leer credenciales del proceso ni acceder a la red. La colección de pytest puede importar código con efectos. No ejecutar un script desconocido para averiguar si es seguro.

Comandos de partida conocidos; inspeccionarlos antes de lanzarlos:

```bash
git rev-parse HEAD
git status --short
python3 --version
node --version
npm --version
python3 -m pytest tools/ -q
bash run-validation.sh
npm test
npm run typecheck
```

Estos comandos no constituyen la puerta final. `run-validation.sh` puede reescribir el índice: ejecutarlo solo donde el delta quede registrado y no se borre trabajo ajeno. No ejecutar `npm ci` sin inspeccionar `prepare` y hooks. Instalar Python en un venv; no modificar el Python del sistema.

## 2. Evidencia de partida

La tabla siguiente es lectura estática de preparación, no reproducción. Cada hallazgo requiere un test o comprobación focal antes de declararse confirmado en el checkout de ejecución. La matriz de certeza está en la sección 11.1.

| ID  | Evidencia en la base                              | Problema                                                                                                          | Tratamiento                                                                                    |
| --- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| F01 | skills/local-maintenance/scripts/clean_routine.py | No integra risk_gate.py como precondición de las mutaciones                                                       | Ejecutor de operaciones y pruebas negativas                                                    |
| F02 | clean_routine.py::main                            | Snapshot recibido sin validación; retorno de creación no comprobado                                               | Validación del artefacto y del backend                                                         |
| F03 | clean_routine.py::generate_json_output            | completed y failed=0 no se derivan del resultado real                                                             | Resultados acumulados y agregación determinista                                                |
| F04 | risk_gate.py                                      | Operación desconocida cae en R0; regex no modela un shell                                                         | Deny-by-default para mutación y operaciones del registro; no usarlo como parser de shell       |
| F05 | tools/workspace-router/run.py                     | Enrutado no ejecuta la skill y ensure_scaffold escribe al consultar                                               | Separar init, route, execute, verify y complete                                                |
| F06 | run.py::route; project_load.py                    | Fallback puede devolver skill no permitida; enabled no se cruza estrictamente con catálogo                        | Validación referencial y bloqueo explícito                                                     |
| F07 | status_bump.py                                    | Avance sin evidencia, transición ni concurrencia; SemVer ligado a bookkeeping                                     | Máquina de estados, revisión y registro de ejecución                                           |
| F08 | run-validation.sh                                 | Duplica reglas y no llama al validador canónico skill_spec.py                                                     | Puerta única que valida el catálogo real                                                       |
| F09 | suite actual y smoke                              | pytest tools/ no recoge por sí mismo skills/; smoke de mantenimiento es help+compilación                          | Descubrimiento explícito e inventario de efectos antes de recoger skills/                      |
| F10 | scripts/validate-skills.js                        | Ruta fija a otro repo, taxonomía vieja, parser YAML inadecuado                                                    | Retirar solo tras inventario interno documentado; no afirmar ausencia de consumidores externos |
| F11 | scripts/install-opencode.sh                       | Destino depende de cwd y borra symlinks sin propiedad                                                             | Target explícito e inventario de recursos                                                      |
| F12 | scripts/install.sh                                | Sobrescribe AGENTS global y prune puede afectar skills ajenas                                                     | Conflictos, manifiesto validado, simulación y desinstalación selectiva                         |
| F13 | plan-continue/SKILL.md                            | ../../tools/workspace-router/run.py no viaja al copiar solo la skill                                              | Distribución standalone o dependencia workspace explícita                                      |
| F14 | opencode.json y AGENTS.md                         | skillDirectories/discovery no están demostrados contra versión objetivo                                           | Configuración y prueba versionadas; nivel B distinto del adaptador falso                       |
| F15 | catálogo SKILL.md                                 | Herramientas amplias homogéneas sin relación con efectos; profundidad desigual                                    | Contratos y mínimos de capacidad, no uniformidad artificial                                    |
| F16 | web-compliance; project-architecture              | Auto-handoff excluyente y derivación semántica incorrecta                                                         | Corregir alcance y añadir fixtures de routing                                                  |
| F17 | web-owasp                                         | Las categorías e identificadores no forman un mapping coherente con una edición declarada                         | Elegir edición oficial, mapping y fuente; verificar cada correspondencia                       |
| F18 | AGENTS.md vs README/skill_spec.py/repo-standard   | Idioma, longitud y política de commits se contradicen                                                             | Contrato canónico y consumidores alineados                                                     |
| F19 | snapshot_state.py                                 | Falla backend/backup pero puede acabar en éxito; captura parcial no garantiza rollback completo                   | Separar inventario, backup, integridad, cobertura y validación de backend/target               |
| F20 | snapshot_state.py                                 | Backups pueden incluir claves SSH del host; permisos y restauración requieren revisión                            | Minimización, permisos privados y extracción segura solo en raíz temporal                      |
| F21 | common.py::run y FindingCollector._category_score | Salida vacía o categoría sin datos puntuables puede parecer salud; `_category_score` devuelve 100 si el peso es 0 | Separar sin incidencias de no comprobado; regresión en T01, T08 y T18                          |
| F22 | common.py::SKILL_VERSION                          | Constante `2.0.0` frente a `metadata.version: 5.0.0` de local-maintenance                                         | La versión de skill sale del manifiesto; el esquema y el componente interno van aparte         |

Precisiones que evitan implementar sobre conclusiones exageradas:

- Las skills pueden ser procedimientos para el agente. No necesitan todas un script ni un intérprete propio. El estándar permite instrucciones sin ejecutables.
- Una lista de paquetes y checksums no es una copia restaurable. Un tar parcial de configuración no restaura paquetes, logs eliminados ni firmware. Un inventario guardado no es un backup restaurable.
- La existencia de un smoke test no prueba que se ejecute en CI; ejecutarlo tampoco demuestra comportamiento si solo prueba `--help`.
- Los tests leídos de `skill_spec.py` usan fixtures temporales. Validar el validador no sustituye invocarlo contra el catálogo real.
- El ranking del router no es una probabilidad ni una confianza calibrada. No etiquetarlo como confidence sin evaluación.
- Cargar una skill y autorizar sus acciones son cosas diferentes. `allowed-tools` no es un sandbox ni una aprobación universal.
- Las correcciones de seguridad cubren los entrypoints oficiales. Un usuario con shell arbitrario y los mismos privilegios puede modificar el programa. `risk_gate` no impide las acciones de ese usuario.
- OpenCode V1 y V2 tienen diferencias documentadas. No imponer una migración mayor ni copiar una API de dev sin comprobar la versión instalada o soportada. Una regla `ask` no basta en modos que aprueban lo no denegado.

## 3. Las cinco líneas de mejora

| Línea | Objetivo                                                       | Tareas principales |
| ----- | -------------------------------------------------------------- | ------------------ |
| M1    | Contrato operativo verificable para todas las skills           | T06–T09, T18–T20   |
| M2    | Seguridad obligatoria en los ejecutores y recuperación honesta | T01–T03, T10–T11   |
| M3    | Orquestación con restricciones, estados y evidencias           | T12–T15            |
| M4    | Una sola puerta de calidad y cobertura real                    | T04–T05, T22–T23   |
| M5    | Distribución, instalación e integración reproducibles          | T16–T17, T21, T24  |

Orden: T00 inventario, preservación y baseline seguro; T01–T03 contención P0; T04–T05 puerta mínima y descubrimiento seguro; T06–T09 contratos y pilotos; T10–T15 ejecutor, permisos y ciclo de vida; T16–T21 instalación, capacidades y harnesses; T22–T24 consolidación y aceptación.

Se pueden paralelizar tareas sin archivos compartidos ni dependencias pendientes. Si hay subagentes, un coordinador integra, cada uno tiene superficie delimitada, no hay dos escritores sobre el mismo módulo y no se descarta trabajo ajeno para integrar.

## 4. Decisiones de arquitectura y contratos

### D01. Capas y alcance técnico

Reutilizar el Python existente para contratos, ejecución determinista y estado. Bash solo como wrapper fino. No introducir TypeScript, un daemon o una dependencia de LLM por homogeneidad.

```text
Intención → selección candidata → validación de política
         → preparación/preflight → ejecución directa o delegación real
         → comprobación de artefactos → finalización verificable → estado
```

Ubicar módulos nuevos en `tools/contracts/` y `tools/execution/`, siguiendo la convención local. No crear un `common.py` importable por accidente desde otra skill. Las rutas nuevas son propuestas.

### D02. Contrato lateral, sin romper Agent Skills

`execution.yaml` es una extensión local del producto, no un requisito del estándar Agent Skills. Conservar `skills/<name>/SKILL.md` y sus referencias relativas. Añadir `skills/<name>/execution.yaml` para las skills del catálogo, con esquema versionado en una ubicación canónica. Quien no entienda el lateral sigue pudiendo usar `SKILL.md`. Los scripts son opcionales. No convertir cada rol en un wrapper artificial.

El contrato contendrá, como mínimo:

- `schema_version`, dialecto e identificador de skill que coincida con carpeta y frontmatter.
- `execution_kind`: agent, script u orchestrator; no confundirlo con `metadata.type`.
- `distribution`: standalone o workspace-required, y dependencias compartidas declaradas.
- Entradas tipadas, defaults seguros y límites de tamaño y complejidad. No ejecutar YAML ni aceptar expresiones de shell.
- Requisitos de sistema, binarios, red y capacidades del harness.
- Operaciones con efectos explícitos: read, write-workspace, mutate-host, communicate-external, access-secret.
- Modo de ejecución, timeout, esquema de salida, verificación y política de aprobación.
- Artefactos y handoffs; condiciones, inputs transmitidos y motivos de bloqueo.
- Soporte real de dry-run e idempotencia por operación; unknown no equivale a yes.
- Fuentes normativas y ediciones cuando correspondan, y límites de automatización.

Rechazar claves YAML duplicadas. Resolver `$ref` solo en local; no descargar esquemas durante la validación. Rechazar campos críticos desconocidos y permitir una estrategia explícita de extensión. Validar semántica: identidad, paths, handoffs, capacidades y consistencia de versiones. Definir migración o rechazo de versiones de esquema desconocidas.

No usar un solo riesgo o permiso para toda una skill multimodo. Los valores de metadata del frontmatter siguen siendo strings. `allowed-tools`, si se conserva, tendrá sintaxis conforme al estándar y mapeo por harness; no da permisos por sí mismo.

`requirements-dev.txt` de la base observada contiene PyYAML, pytest y Ruff. `jsonschema` no figura. Si se elige, justificarlo y fijar una versión comprobada. Distinguir dependencias de desarrollo y de ejecución: cargar un contrato no debe exigir pytest ni Ruff.

### D03. Resultados, estados y códigos de salida

Cerrar este esquema antes de implementarlo.

Estados de ejecución no terminales: `awaiting_agent`, `awaiting_approval`. No son éxito y no completan una fase.

Resultados terminales, según la operación: `succeeded`, `failed`, `partial`, `blocked`, `cancelled`, `simulated`, `not_applicable`.

Campos mínimos del documento de resultado:

```json
{
  "schema_version": 1,
  "run_id": "identificador-generado-en-ejecucion",
  "skill": "local-maintenance",
  "skill_version": "version-del-manifiesto",
  "component_version": "version-interna-o-null",
  "target_revision": "commit-real-o-null-con-motivo",
  "work_digest": "digest-del-contenido-relevante",
  "mode": "dry-run",
  "outcome": "simulated",
  "actions": [],
  "verification": [],
  "artifacts": [],
  "errors": [],
  "started_at": "timestamp-real",
  "finished_at": "timestamp-real"
}
```

- Versión de skill: derivada del manifiesto canónico `SKILL.md`. No usar `SKILL_VERSION = "2.0.0"` como si fuera esa versión.
- Versión de esquema: independiente.
- Versión de componente interno: campo separado si hace falta. No imponer igualdad entre versiones distintas.

Una consulta o preparación que termina bien sin ejecutar la skill devuelve un resultado de consulta o `simulated`/`not_applicable` justificado, no `succeeded` de implementación. `exit 0` no equivale a implementación completada. El consumidor lee `outcome`.

`not_applicable` obligatorio exige una regla verificable. No sirve para omitir una prueba difícil.

Motivos diferenciados, sin colapsarlos todos en `blocked`:

- entrada inválida: código 2
- rechazo de política: código 3, `blocked`
- fallo del proceso: código 1, `failed`
- resultado parcial: código 1, `partial`
- ausencia de capacidad: código 3, `blocked`, con el requisito que falta
- cancelación: código 4, `cancelled`

Códigos CLI: 0 para `succeeded`, `simulated` o `not_applicable` justificado; 1 `failed` o `partial`; 2 configuración o entrada inválida; 3 `blocked`; 4 `cancelled`. Los wrappers legacy conservan sus códigos mediante adaptación documentada y tests, o se migran de forma explícita. No cambiarlos por accidente.

`planned`, `skipped` y `simulated` nunca cuentan como `completed`. Un test no ejecutado es `not_run` y no satisface una verificación obligatoria.

stdout contiene solo JSON cuando se solicita JSON. Logs y progreso van a stderr. No imprimir secretos ni volcar stdout de procesos que puedan contenerlos.

Completar una fase solo con resultados terminales válidos de la operación real y sus verificaciones. Una simulación, una delegación pendiente o una aprobación pendiente no completan una fase de ejecución real ni modifican el SemVer del producto.

### D04. Aprobación y ejecución mutadora

La unidad de autorización es una operación concreta sobre un target resuelto, con parámetros, plan y efectos conocidos. El digest detecta cambio de contenido; no demuestra consentimiento.

Contrato del proveedor, a fijar con las capacidades reales del entorno antes de habilitar mutaciones:

- quién emite la aprobación
- cómo llega al ejecutor
- qué operación, target, parámetros y artefactos cubre
- cómo se detecta un cambio de contenido
- si permite reutilización y bajo qué condiciones
- qué ocurre ante denegación, caducidad o timeout

No son autorización suficiente: `approved=true`, un archivo editable por el propio agente, una variable de entorno arbitraria o un hash generado por el mismo ejecutor.

Si no hay proveedor confiable: preparar el plan, devolver `blocked` o `awaiting_approval` y no habilitar la mutación. No implementar criptografía ni un servidor de autorizaciones innecesarios. Documentar qué componente es confiable y qué garantía ofrece.

- Modo no interactivo sin autorización adecuada: `blocked`. Nunca esperar indefinidamente un prompt ni autoaprobar.
- Si el harness proporciona una puerta real y versionada, usar esa interfaz. Probar que no esté en un modo que apruebe lo no denegado.
- La aprobación cubre la operación y su plan exacto. Cambios de target, parámetros, artefacto o efecto exigen nueva autorización.
- Los entrypoints oficiales mutadores llaman a la misma política. No dejar una ruta rápida que la omita.
- Ejecutar argumentos con `subprocess` y `shell=False` cuando el comando ya esté modelado. `shell=False` no basta si argv invoca `bash -c`, `sh -c` u otro intérprete con código arbitrario: rechazar esos escapes en el registro de operaciones.
- El timeout debe alcanzar también a los descendientes cuando corresponda. No dejar una operación activa después de haber devuelto `cancelled` o `failed`.
- Fijar cwd, entorno mínimo y binario permitido. Rechazar input desconocido, traversal y expansión de shell en parámetros.

Deny-by-default se aplica a las operaciones ejecutables del registro y a las capacidades no autorizadas. Las observaciones de solo lectura tienen contrato explícito y no exigen automáticamente un snapshot. Separar validación de parámetros y target, autorización de efectos, requisitos de recuperación, y capacidad del proceso y del harness.

No reemplazar de golpe `shell=True` por `shell=False` en `common.py`. Procedimiento en T10, inventariado desde T00:

1. Inventariar todos los consumidores de `run` y `run_capture`.
2. Introducir una interfaz tipada con argv y resultado estructurado, que conserve código de retorno, timeout y error.
3. Migrar primero los comandos mutadores y después los probes afectados.
4. Sustituir pipelines y redirecciones por procesamiento Python o procesos conectados de forma explícita.
5. Mantener compatibilidad temporal solo donde sea necesaria y esté probada.

Hasta completar la migración, todo entrypoint mutador no cubierto rechaza la ejecución de forma explícita.

### D05. Snapshots y recuperación

El resultado separa captura de inventario, creación del backup o snapshot, verificación de integridad, cobertura de recuperación y validación del backend y del target. Guardar un inventario no es haber obtenido un backup restaurable.

- `recovery_scope`: `full`, `partial` o `none`. `full` solo tras prueba pertinente del backend, no solo porque timeshift o snapper devuelvan cero. Comprobar identificador del backend, alcance y evidencia disponible.
- Si el backend requerido falla, no sustituirlo en silencio por un inventario ni declarar éxito.
- Un snapshot de configuración no autoriza eliminación de paquetes, journal o firmware como si fueran reversibles.
- En este incremento no se ejecutan operaciones irreversibles en el host del operador ni en CI. Firmware y reinicios quedan fuera de la limpieza ordinaria y bloqueados por defecto.
- Directorios privados y archivos sensibles con permisos restrictivos. No incluir claves privadas SSH por defecto. No guardar esos artefactos en Git ni en artifacts públicos.
- No mezclar snapshots de targets distintos. Validar `snapshot_id`, raíz real, symlinks, ownership y cobertura. Los hashes verifican integridad accidental; no sustituyen autenticidad ni permisos.
- Si la recuperación requerida falla, no continuar.
- Restauración real del host: no autorizada. Las pruebas solo usan una raíz temporal explícita. Validar traversal, rutas absolutas, symlinks, hardlinks y archivos especiales. No extraer un archivo no confiable sobre `/` usando shell. Una restauración temporal probada no certifica el rollback del host.

### D06. Estado, consulta pura, reintentos y concurrencia

Separar versión del producto, `schema_version` del estado, `state_revision` y `run_id`. No deducir SemVer de una fase administrativa.

Modelo mínimo de ejecución: `planned` → `ready` → `running` → `awaiting_agent` / `awaiting_approval` → resultado terminal de D03. Solo los resultados terminales válidos de la operación real y sus verificaciones permiten completar una fase.

- `init` es explícito. `route`, `list` y `status` no crean scaffold, logs, directorios ni archivos de resultado por defecto.
- La prueba de consulta pura compara el estado persistente y los archivos gestionados. Las cachés del intérprete o de herramientas, si existen, quedan aisladas y fuera de esa comparación. Escribir resultados solo con destino explícito.
- `enabled` ausente permite el default documentado. `enabled: []` no permite ninguna skill y bloquea. `disabled` siempre prevalece. Validar ambos contra el catálogo.
- Handoffs desconocidos, fases no habilitadas o skills no permitidas bloquean, sin fallback silencioso.
- Resolver todos los roles aplicables por tarea. No reemplazar esa selección por una única skill de fase.
- Evidencia vinculada a revisión, input y plan. Un cambio material invalida la aceptación anterior o exige reverificación.
- Locks: documentar alcance y plataforma soportada, liberación ante error y terminación, control de `state_revision`, escritura atómica en el mismo filesystem, y lectores junto a writers. No usar solo `sleep` para probar concurrencia; usar sincronización determinista. Recuperar escrituras interrumpidas sin truncar el estado válido.
- Clave idempotente por operación, inputs y target. Un retry no repite efectos si hay evidencia suficiente.
- Tras timeout con posible efecto externo: no asumir que el proceso no actuó; bloquear el reintento hasta reconciliar; registrar la incertidumbre. Si el esquema no tiene un resultado terminal para esa incertidumbre, el detalle es bloqueante y no se inventa un estado incompatible. No prometer exactamente una vez para servicios externos.
- Separar historial resumido del registro de evidencias. No perder la única evidencia al recortar el historial.
- Conservar `--bump` solo como migración explícita o rechazarlo con explicación. No dejar incremento arbitrario.

### D07. Una sola puerta de calidad

`run-validation.sh` será wrapper de una implementación canónica reutilizable. El modo completo valida el catálogo real, los contratos, enlaces, índice, smokes seguros, tests seguros y empaquetado. Los modos rápidos anuncian su alcance y no aparentan aceptación completa.

- El check del índice compara y no reescribe. La generación queda en un comando explícito.
- Catálogo dinámico por conjuntos de nombres. Detectar duplicadas, ausentes, extras y nombres inconsistentes. No reducir la paridad a un conteo.
- Mantener los nombres de required checks existentes salvo migración explícita. No cambiar branch protection desde el agente.
- No retirar controles de seguridad o higiene por conveniencia. Si hay falsos positivos, corregir reglas y fixtures.
- Inventariar imports y efectos antes de recoger tests bajo `skills/`. No ejecutar pytest sobre toda esa superficie sin ese inventario. Aislar imports y fixtures. No añadir tests que requieren servicios reales a la puerta por defecto.
- Propagar fallos de subprocesos. Rechazar flags inválidos.
- Registrar la colección y demostrar, con fixtures defectuosas, que cada puerta detecta el fallo esperado.
- Un requisito obligatorio ausente no puede dejar la puerta full en verde por un skip.
- `py_compile` se llama syntax-check. `typecheck` solo si existe un comprobador de tipos real. Un alias legacy `typecheck` queda documentado y marcado como deprecación.
- Lint real ejecutado, no solo configurado.

### D08. Distribución, instalación y harnesses

- Standalone: contiene sus recursos y declara requisitos externos. No depende de `../../tools` del checkout original. Un symlink al checkout no demuestra autonomía: si el origen desaparece y la skill deja de funcionar, esa instalación no es standalone.
- Workspace-required: necesita una instalación completa y resuelve su raíz de forma explícita. Si falta, `blocked` con la instrucción correcta.
- Si una skill necesita módulos compartidos, declararla workspace-required o distribuirlos por un mecanismo real. No duplicarlos en silencio para aparentar autonomía.
- Instalador con `--target` y `--scope` explícitos, `--dry-run`, detección de conflictos, manifiesto de propiedad y uninstall o update gestionados.
- El manifiesto no es confiable por existir. Validar todas sus rutas antes de actualizar o desinstalar. Target resuelto y confinado. Rechazar traversal.
- Conflictos con archivo, directorio real, symlink y enlace roto. Instalación idempotente. Un fallo a mitad no se presenta como instalación correcta. Desinstalación limitada a recursos propios que sigan siendo identificables. Pruebas de fallo de permisos y de operación parcial.
- Ningún prune por el mero hecho de que el nombre no esté en el catálogo. No borrar recursos ajenos. No sobrescribir AGENTS global.
- Pruebas con HOME y XDG temporales, cwd arbitrario, espacios en rutas y colisiones. Esas pruebas no son un sandbox de seguridad del host.
- OpenCode: dos niveles de aceptación, en T21. Elegir una versión soportada verificable. No copiar configuración de una rama dev como si fuera estable. Cargar una skill no autoriza Bash, edición, red, secretos ni directorios externos.
- La documentación consultada describe reglas donde la última coincidencia gana y un modo que aprueba solicitudes no denegadas de forma explícita. No dar por suficiente una regla `ask` para operaciones críticas en todos los modos. No usar autoaprobación en las pruebas de autorización. Probar reglas efectivas globales y por agente. Evitar ejemplos amplios como `git *` o `npm *` sin revisar sus consecuencias. Las restricciones de producto se mantienen aunque el harness permita cargar la skill.
- Codex, Cursor, Copilot y otros nombres ya presentes se clasifican como verificado, documentado-no-probado o no-soportado. No afirmar portabilidad por copiar una carpeta.

## 5. Tareas de implementación

Regla para todas: inspección, test rojo significativo, cambio mínimo, test verde, refactor, suite pertinente, evidencia. Para prosa o esquema sin ejecución, usar fixtures. No inventar TDD donde no existe comportamiento. No marcar una casilla si su verificación obligatoria no pasó. No declarar completada una capacidad que solo esté descrita, delegada, simulada o bloqueada.

Cada evidencia registra HEAD base, digest del contenido relevante, archivos rastreados modificados, archivos nuevos relevantes, versiones de herramientas, configuración, comando, resultado y artefactos. Excluir del digest las cachés y este diario, con esa exclusión escrita. Un `git diff` no cubre no rastreados. No asociar tests de un árbol anterior a cambios posteriores. Tras el último cambio material, repetir las comprobaciones afectadas y la puerta final.

### T00 — Revalidar, inventariar efectos y establecer baseline [pendiente]

- Dependencias: ninguna. Roles: plan-continue; plan-validators para el diseño de pruebas.
- Superficie: checkout, instrucciones, comandos, catálogo, dependencias y entrypoints con efectos. Sin mutación del host.
- Archivos: este plan; lectura de AGENTS.md, `package.json`, workflows y contratos existentes. Skills desde `skills/<nombre>/SKILL.md`.
- Trabajo, en este orden:
  1. Repetir HEAD, rama, estado y no rastreados. Comprobar este destino y `feat/executable-skills` si existe.
  2. Inventariar efectos antes de cualquier baseline: scripts mutadores de local-maintenance; creación y restauración de snapshots; mutadores de local-security; instaladores y desinstaladores; hooks y herramientas de project-publish; envío de correo y acceso a secretos de local-proton; scripts alcanzables por import, colección de pytest o `--help`. Inspeccionar antes de ejecutar. Donde haga falta correr algo, usar dobles, entorno sin credenciales y aislamiento efectivo.
  3. Inventariar consumidores de `common.run` y `common.run_capture`, incluidos pipelines y redirecciones.
  4. Baseline solo de lo ya inspeccionado y seguro. Registrar el delta si un comando escribe artefactos.
- Aceptación: [ ] base y cambios ajenos identificados en este checkout; [ ] inventario de efectos escrito antes del baseline; [ ] baseline aislado sin tratar venv o HOME temporal como sandbox; [ ] fallos previos separados de regresiones; [ ] cero autorizaciones externas asumidas.
- Verificación: salida real de comandos seguros, diff y matriz de la sección 11.1 actualizada. Si no hay shell, esta tarea termina `blocked`, no `done`.

### T01 — Reproducir P0 y F21 sin tocar el host [pendiente]

- Dependencias: T00. Roles: plan-validators, role-back.
- Superficie: `clean_routine`, `snapshot_state`, `risk_gate`, `common.FindingCollector`; subprocess y filesystem sustituidos.
- Archivos: tests bajo `skills/local-maintenance/scripts/tests` y fixtures.
- Trabajo: tests de continuación tras snapshot fallido, snapshot inválido, informe de éxito tras fallo y ausencia de política en la ruta mutadora. Modo simulación. Regresión de F21: comando ausente, permiso denegado, timeout, salida inválida y comprobaciones en ERROR o SKIP. Una categoría sin datos puntuables no recibe 100 en silencio.
- Aceptación: [ ] cada caso falla por el motivo esperado antes de corregir; [ ] ninguna llamada alcanza apt, pacman, dnf, systemctl, journalctl mutador, firmware, `/etc` o HOME real.
- Verificación: tests focales con ejecutor espía. Registrar RED.

### T02 — Contener limpieza y corregir resultados [pendiente]

- Dependencias: T01. Roles: role-back, role-clean-code, plan-validators.
- Superficie: `clean_routine.py` y pruebas. Interfaz legacy.
- Trabajo: bloquear ejecución sin precondiciones verificadas; comprobar retornos; acumular resultados reales; separar stderr y JSON; devolver fallo o partial. Mantener default dry-run. Las rutas mutadoras no cubiertas rechazan la ejecución. No hacer el reemplazo mecánico de `shell=True`.
- Aceptación: [ ] T01 verde; [ ] snapshot fallido impide el primer efecto; [ ] simulated y skipped no son completed; [ ] los contadores se calculan; [ ] los fallos no se ocultan como warnings exitosos.
- Verificación: pruebas focales, JSON parseable y regresión de CLI. Ningún mantenimiento real.

### T03 — Corregir captura y garantías de snapshot [pendiente]

- Dependencias: T01. Roles: role-back, role-clean-code, plan-validators.
- Superficie: `snapshot_state.py`; backend simulado, permisos y restauración temporal.
- Trabajo: propagar fallos de timeshift, snapper y tar. Separar inventario, backup, integridad, cobertura y validación de backend y target. No tratar un código cero del backend como `recovery_scope: full` sin identificador, alcance y evidencia. No incluir claves privadas por defecto. Permisos restrictivos. Validar captura y restauración frente a traversal, rutas absolutas, symlinks, hardlinks, archivos especiales y backups parciales. Restauración solo en raíz temporal.
- Aceptación: [ ] backend fallido no produce recuperación válida; [ ] inventario correcto no se presenta como backup restaurable; [ ] claves privadas no se capturan por defecto; [ ] directorios y datos sensibles privados; [ ] rollback probado solo sobre raíz temporal; [ ] partial se explica y bloquea donde corresponde; [ ] la prueba temporal no se documenta como certificación del host.
- Verificación: backend simulado con éxito, fallo y timeout; tar malicioso de fixture; corrupción de manifest; snapshot de otro target.

### Checkpoint C1 — Contención P0

- [ ] T01–T03 probados. No hay ruta oficial que continúe tras una recuperación requerida fallida.
- [ ] La documentación deja de prometer reversibilidad inexistente.
- [ ] Los riesgos pendientes del ejecutor están rechazados de forma explícita, no diferidos con ejecución abierta.
- [ ] Esta contención no se anuncia como la capacidad automatizada completa de M2.

### T04 — Conectar el validador real y eliminar divergencia mínima [pendiente]

- Dependencias: T00. Roles: role-back, role-clean-code, plan-validators.
- Superficie: `run-validation.sh`, `tools/validate/skill_spec.py`, scripts de `package.json` y pruebas.
- Trabajo: llamar al validador contra skills reales. Reutilizar reglas. Detectar catálogo vacío, metadata y claves obligatorias, y consistencia dominio-prefijo. Antes de tocar `scripts/validate-skills.js`, documentar la búsqueda en package scripts, hooks, workflows, documentación viva, instaladores y otros scripts. La ausencia interna no prueba consumidores externos. Si no hay consumidores internos, retirarlo, corregir referencias y documentar la retirada si tenía uso público. Añadir un wrapper temporal solo si existe una necesidad real. No conservar dos validadores divergentes.
- Aceptación: [ ] un catálogo defectuoso hace fallar la puerta; [ ] fixtures válidos e inválidos; [ ] no hay ruta fija a otro checkout; [ ] ninguna validación termina 0 pese a issues; [ ] el inventario de consumidores queda escrito.
- Verificación: comandos existentes adaptados e invocación sobre el catálogo real.

### T05 — Descubrir tests y smokes de skills con seguridad [pendiente]

- Dependencias: T02–T04. Roles: role-back, plan-validators.
- Superficie: suite `tools/` y `skills/`, tests de shell e imports.
- Trabajo: inventariar smokes, tests e imports con efectos antes de ejecutarlos. Aislar los inseguros. No recoger todo `skills/` sin ese inventario. Invocar los smokes requeridos que sean seguros. Resolver colisiones de imports. Comprobar el resultado esperado de routing.
- Aceptación: [ ] el manifiesto de recogida cubre ambas superficies e indica exclusiones; [ ] un smoke fallido rompe el gate; [ ] `--help` y `py_compile` no se presentan como pruebas de comportamiento; [ ] sin servicios ni privilegios reales.
- Verificación: colección revisada, fixture deliberadamente fallida y ejecución completa aislada.

### T06 — Definir esquemas de contrato y resultado [pendiente]

- Dependencias: T04. Roles: role-back, role-clean-code, plan-validators.
- Superficie: esquemas y loader en `tools/contracts/`; `execution.yaml` de tres pilotos.
- Trabajo: concretar D02 y D03, incluido el cierre de estados, motivos y códigos. Elegir la biblioteca solo si está en la base o queda justificada y fijada tras comprobar su versión. Rechazar duplicados, `$ref` remotos y campos críticos desconocidos. Validación semántica además de tipos. Diseñar la migración antes de hacer obligatorios los laterales del resto. Separar dependencia de ejecución y de desarrollo.
- Aceptación: [ ] esquema versionado con dialecto; [ ] fixtures de límites y errores; [ ] rutas confinadas; [ ] entrada y salida inválidas no alcanzan ejecución; [ ] sin YAML ejecutable; [ ] versión de skill, de esquema y de componente distinguibles.
- Verificación: tests del loader, de los esquemas y de la correspondencia de identidad y versiones.

### T07 — Implementar preflight y resolución portable [pendiente]

- Dependencias: T06. Roles: role-back, plan-validators.
- Superficie: binarios, red, credenciales como presencia o capacidad, raíz de workspace y de skill.
- Trabajo: resolver recursos por skill root. Comprobar requisitos sin instalar nada ni leer valores secretos. Distinguir requisito duro, opcional y no aplicable. No usar el cwd como instalación implícita. Una capacidad opcional ausente no crea un PASS.
- Aceptación: [ ] capacidad ausente y dura produce `blocked` útil; [ ] optional no crea PASS falso; [ ] una copia standalone no accede al checkout original; [ ] workspace ausente queda diagnosticado.
- Verificación: PATH y HOME temporales, capacidades simuladas, cwd arbitrario y rutas con espacios.

### T08 — Normalizar entrega y evidencia [pendiente]

- Dependencias: T06. Roles: role-back, role-clean-code, plan-validators.
- Superficie: serialización, agregación, artifacts y CLI.
- Trabajo: D03 con resúmenes derivados, timestamps reales, run IDs, digest de trabajo, stdout limpio y redacción. Publicar cobertura de comprobación junto a cualquier puntuación. No mostrar «excelente», «actualizado» o equivalente cuando la evidencia obligatoria es insuficiente. No etiquetar como actualizaciones de seguridad una lista genérica de actualizaciones. Guardar artefactos solo en un destino autorizado. Detectar escapes y symlinks. No persistir secretos. Incluir la regresión de F21 en el resultado agregado.
- Aceptación: [ ] todos los outcomes se validan; [ ] error o partial bloquea la aceptación; [ ] la salida JSON no contiene colores ni logs; [ ] códigos y wrappers documentados; [ ] una consulta no escribe artefactos por defecto; [ ] una puntuación sin cobertura no parece salud perfecta.
- Verificación: fixtures mínimos, errores de disco, truncamiento, intentos de escape y casos ERROR/SKIP.

### T09 — Migrar tres pilotos sin ampliar privilegios [pendiente]

- Dependencias: T06–T08. Roles: role-back, role-clean-code, plan-validators.
- Superficie: local-maintenance, plan-continue, web-compliance.
- Trabajo: añadir `execution.yaml` y un contrato visible en `SKILL.md`. Mapear scripts existentes. Declarar qué subcapacidades se automatizan y cuáles son juicio asistido. Mantener la interfaz legacy con mensajes de migración si procede. Corregir la autorreferencia de handoff en web-compliance. `plan-continue` declara workspace-required mientras dependa del router, o deja de apuntar a `../../tools` si se distribuye de otro modo.
- Aceptación: [ ] tres contratos válidos; [ ] una operación ausente no se anuncia como implementada; [ ] ejemplos ejecutables en entorno aislado; [ ] la referencia a `../../tools` queda resuelta o el requisito workspace está declarado.
- Verificación: pruebas de contrato de cada piloto. La documentación ejecutable no muta el host.

### Checkpoint C2 — Contratos utilizables

- [ ] T04–T09 verdes y catálogo real comprobado.
- [ ] Las abstracciones nuevas no duplican un framework ni requieren un LLM para checks deterministas.
- [ ] Los scripts antiguos no quedan como bypass junto al adaptador nuevo.
- [ ] El esquema de estados de D03 está cerrado e implementado, no solo descrito.

### T10 — Integrar ejecutor de operaciones y autorización [pendiente]

- Dependencias: T02–T03, T07–T09. Roles: role-back, role-clean-code, plan-validators.
- Superficie: entrypoints mutadores ya inventariados en T00, política, procesos y aprobación.
- Trabajo: aplicar D04. Interfaz tipada; migrar mutadores y luego probes; procesos conectados en lugar de pipelines opacos; timeout de descendientes. `risk_gate` queda como apoyo o wrapper compatible, nunca como filtro suficiente de un shell arbitrario. Separar firmware y reinicios. Sin proveedor de aprobación confiable, la mutación permanece `blocked` o `awaiting_approval`.
- Aceptación: [ ] unknown deny en el registro de operaciones; [ ] la lectura contratada no exige snapshot; [ ] aprobación ausente, rechazada, caducada o de otro plan bloquea; [ ] un cambio de target invalida la aprobación; [ ] el entrypoint directo también controla; [ ] no hay elevación de privilegios; [ ] `bash -c` y equivalentes arbitrarios se rechazan.
- Verificación: espías de ejecución y matriz R01–R10. Probar la política. No ejecutar comandos destructivos reales.

### T11 — Separar Proton por operaciones seguras [pendiente]

- Dependencias: T06–T08, T10. Roles: role-back, plan-validators.
- Superficie: `local-proton/SKILL.md`, `proton_bridge.py` y las herramientas que T00 haya inventariado.
- Trabajo: distinguir read, search, classify, send y access-secret. Eliminar cualquier secuencia que sugiera obtener secretos y enviar tras una lectura. El envío exige destinatario y contenido resueltos y una confirmación vinculada. Los datos de correo o documentos no son instrucciones para ejecutar herramientas.
- Aceptación: [ ] la lectura no envía; [ ] no hay secretos en logs, artefactos ni tests; [ ] un envío con aprobación denegada bloquea; [ ] un destino modificado exige nueva autorización; [ ] un timeout ambiguo no reenvía.
- Verificación: IMAP, SMTP, MCP y almacén de secretos simulados. Sin cuentas reales.

### T12 — Corregir selección de intención y política por proyecto [pendiente]

- Dependencias: T04, T06. Roles: role-back, plan-validators.
- Superficie: `tools/skill-router` y `tools/workspace-router/project_load.py` / `run.py`.
- Trabajo: abstención si no hay señal suficiente, si hay ambigüedad o si hay varias skills. El score léxico no es probabilístico. Validar catálogo, fases, handoffs, enabled y disabled según D06. Sin fallback fuera de la allowlist.
- Aceptación: [ ] unknown o todo cero no selecciona la primera skill del catálogo; [ ] disabled prevalece; [ ] `enabled: []` bloquea; [ ] una skill o fase desconocida falla antes de scaffold o estado; [ ] los resultados son deterministas y un top inválido se rechaza.
- Verificación: corpus español e inglés positivo, negativo, ambiguo, multirol y fuera de dominio.

### T13 — Separar consulta, init y migración de estado [pendiente]

- Dependencias: T12. Roles: role-back, role-clean-code, plan-validators.
- Superficie: workspace-router, plantillas y `.autoworkspace` de fixtures.
- Trabajo: init explícito. route, list y status puros, sin archivos de resultado por defecto. Validar esquemas de project y status. Migrar estado legacy con copia segura y simulación. Preservar historia y versión de producto. Añadir `state_revision` sin bump SemVer administrativo.
- Aceptación: [ ] la consulta deja el estado persistente y los archivos gestionados idénticos; [ ] la ausencia de scaffold se informa sin crearlo; [ ] la migración conserva datos y es repetible; [ ] un fallo no corrompe el estado previo.
- Verificación: comparación del filesystem temporal, YAML inválido, esquema desconocido y fixtures legacy. Cachés aisladas no cuentan como escritura del producto.

### T14 — Ejecutar o delegar con evidencia real [pendiente]

- Dependencias: T08–T10, T12–T13. Roles: role-back, plan-validators.
- Superficie: orquestador, adaptador del harness y verificador.
- Trabajo: preparación, ejecución determinista y handoff al agente actual. Una skill agent no se ejecuta leyendo `SKILL.md` ni imprimiendo su nombre. Entregar el bundle y permanecer en `awaiting_agent` hasta recibir y verificar resultados. Cargar la skill no es aprobar la acción. Un adaptador headless de OpenCode, si se añade, usa una API o CLI estable de la versión objetivo, con test aislado y permisos, sin crear una plataforma paralela. El falso harness prueba el protocolo local; no demuestra integración nativa.
- Aceptación: [ ] el router no cuenta como ejecutor; [ ] sin agente o capacidad, el resultado es `blocked` o `awaiting_agent`; [ ] hay roles múltiples y contratos explícitos; [ ] un artefacto inválido impide complete; [ ] la carga de la skill no se confunde con la aprobación.
- Verificación: fake harness contractual y al menos un flujo determinista local de extremo a extremo. Una prueba de modelo externo es opt-in, con coste y permisos aprobados, y no entra en el gate por defecto.

### T15 — Finalizar fases, concurrencia e idempotencia [pendiente]

- Dependencias: T13–T14. Roles: role-back, role-clean-code, plan-validators.
- Superficie: estado, evidencia, locks y transiciones.
- Trabajo: D06. Completar solo con verificaciones. Invalidar evidencia obsoleta. Locks, revisión y escritura atómica con sincronización determinista. Retry seguro. Timeout con posible efecto externo queda en reconciliación, sin reintento ciego. `--bump` legado solo como migración explícita o rechazo explicado.
- Aceptación: [ ] un salto inválido bloquea; [ ] un resultado simulado no completa una ejecución real; [ ] dos writers no pierden updates; [ ] un retry no duplica el efecto probado; [ ] un fallo intermedio conserva el estado anterior; [ ] el bookkeeping no altera la versión del producto.
- Verificación: tests concurrentes deterministas, interrupción de escritura, evidencia stale y timeout posterior a un posible efecto.

### Checkpoint C3 — Automatización honesta

- [ ] T10–T15 verdes. Una fase no termina sin evidencia.
- [ ] El operador distingue route, simulated, awaiting_agent, awaiting_approval, blocked y succeeded.
- [ ] No se atribuye exactamente-una-vez a integraciones que no lo garantizan.
- [ ] Una mutación sin proveedor de aprobación sigue bloqueada.

### T16 — Instalador con propiedad y conflictos [pendiente]

- Dependencias: T07, T09. Roles: role-back, role-clean-code, plan-validators.
- Superficie: `scripts/install.sh`, `scripts/install-opencode.sh`, manifiesto y uninstall.
- Trabajo: D08. Root y target explícitos, simulación, inventario, conflictos y desinstalación selectiva. Validar todas las rutas del manifiesto antes de actualizar o borrar. No borrar symlinks ajenos, no mover directorios ajenos, no sobrescribir AGENTS y no podar por ausencia del nombre en el catálogo. Un fallo a mitad no se presenta como instalación correcta.
- Aceptación: [ ] instalación desde cualquier cwd; [ ] la segunda instalación es idempotente; [ ] un recurso ajeno permanece byte-idéntico; [ ] el manifiesto no permite path traversal; [ ] uninstall no sale del target; [ ] dry-run no cambia nada; [ ] permiso denegado y operación parcial están probados.
- Verificación: HOME y XDG temporales y matriz de colisiones. Sin instalar en el HOME real.

### T17 — Distribución standalone o workspace reproducible [pendiente]

- Dependencias: T09, T16. Roles: role-back, role-clean-code, plan-validators.
- Superficie: empaquetado, copias, resolución compartida y quickstart del README.
- Trabajo: clasificar cada skill. Probar una copia mínima sin el checkout original y sin symlinks hacia él. Corregir una instalación sugerida que no incluya sus dependencias. No duplicar código compartido en silencio. No crear un artefacto de release si no hay formato ni consumidor útil.
- Aceptación: [ ] standalone funciona con sus requisitos aunque el origen desaparezca; [ ] workspace-required falla de forma útil sin workspace y funciona con la instalación completa; [ ] cero rutas personales; [ ] scripts y references viajan completos.
- Verificación: fixtures desde un directorio temporal con el source inaccesible.

### T18 — Homogeneizar las 16 skills y su semántica [pendiente]

- Dependencias: T09, T11–T12. Roles: role-clean-code; role-back cuando se edite lógica; plan-validators.
- Superficie: todos los `SKILL.md`, `execution.yaml` y referencias vivas.
- Trabajo: mínimos comunes Overview, When to Use, Inputs/Prerequisites, Process, Verification, Output/Limitations. Tools solo donde aporte. Elegir los encabezados exactos en el canon antes de migrar. No convertir la plantilla en prosa vacía. Corregir F15–F18 y F21 en la prosa de puntuación. Reclasificar `metadata.type` solo cuando el alcance lo justifique, con tests. Los roles no reciben scripts artificiales.
- Aceptación: [ ] 16 contratos válidos sin congelar el validador en 16; [ ] límites y dependencias honestos; [ ] sin auto-handoff excluyente; [ ] versión por skill según el cambio real; [ ] una comprobación no verificada no se describe como excelente o actualizada.
- Verificación: gate de catálogo y revisión semántica con la matriz de la sección 6.

### T19 — Hacer verificable SCA, arquitectura y OWASP [pendiente]

- Dependencias: T06–T08, T18. Roles: role-back, role-clean-code, plan-validators.
- Superficie: project-libraries, project-architecture y web-owasp.
- Trabajo: adaptadores mínimos reales según las herramientas disponibles. Vulnerabilidad, malware, typosquatting, unused y outdated son capacidades distintas. No prometer detección exhaustiva. Una herramienta ausente es capacidad no disponible, no un informe sin hallazgos. SBOM solo con generador, formato válido y evidencia. La arquitectura descubre stack y límites; no instala herramientas citadas sin verificar. OWASP: elegir una edición oficial, verificar cada identificador contra esa fuente y separar categorías de checklist técnico. No afirmar una mezcla con una edición que no se haya localizado en el texto. No ejecutar código de dependencias no confiables.
- Aceptación: [ ] matriz por ecosistema, herramienta, capacidad y limitación; [ ] herramienta ausente no es informe limpio; [ ] las fixtures no confunden advisories con certeza; [ ] categoría y edición son coherentes; [ ] una derivación de implementación menor ya no va a SCA.
- Verificación: salidas simuladas de scanner y repos pequeños de fixture. Consulta oficial versionada para el mapping. Red real opt-in.

### T20 — Hacer reproducibles compliance y performance [pendiente]

- Dependencias: T09, T18. Roles: role-back, role-clean-code, plan-validators.
- Superficie: web-compliance, web-performance y scripts existentes.
- Trabajo: separar comprobación automática, manual y no evaluada. No certificar RGPD ni accesibilidad completa por un escaneo. Performance separa laboratorio y campo, y registra URL o commit, herramienta, versión, entorno, configuración, repeticiones, agregación y errores. Un fallo de medición no es una buena puntuación. Umbrales y ediciones se contrastan con fuentes oficiales.
- Aceptación: [ ] las verificaciones manuales pendientes impiden un veredicto total injustificado; [ ] no hay auto-handoff; [ ] un error de medición no es PASS; [ ] el protocolo es repetible y los artefactos son trazables; [ ] no se instala un navegador global.
- Verificación: HTML local de fixture, fallos simulados de herramienta y reportes deterministas. Browser E2E solo si aporta evidencia, aislado y disponible.

### T21 — Integrar OpenCode por versión y clasificar harnesses [pendiente]

- Dependencias: T14, T16–T18. Roles: role-back, role-clean-code, plan-validators.
- Superficie: `opencode.json`, `docs/opencode-setup.md`, `docs/harness-integration.md`, AGENTS.md.
- Trabajo: D08. Dos niveles. A) contratos, configuración y adaptador con dobles. B) descubrimiento, carga y permisos con un OpenCode real de la versión declarada. A no sustituye a B. Si el binario no está, B queda `not_run`, se continúa con las tareas independientes y no se anuncia compatibilidad verificada ni se cierra la aceptación integral del harness. Verificar el comportamiento contra la versión objetivo. Probar por separado la carga y los permisos de acción. No añadir un modelo externo al gate determinista.
- Aceptación A: [ ] la configuración no contiene campos ficticios; [ ] el adaptador distingue carga y acción; [ ] versiones, API y límites quedan documentados.
- Aceptación B, solo con binario real: [ ] la skill se descubre y se carga por su nombre; [ ] una denegación efectiva se prueba fuera de un modo de autoaprobación; [ ] las reglas globales y por agente se comprueban.
- Verificación: tests del adaptador obligatorios. Smoke del binario en HOME temporal si está disponible. Si no lo está, B es `not_run`, no PASS.

### Checkpoint C4 — Producto coherente y portable

- [ ] T16–T21 verdes, o bloqueos externos clasificados sin anunciarlos como verificación.
- [ ] Los requisitos esenciales de distribución están probados. El soporte opcional no probado no se anuncia como verificado.
- [ ] El nivel B de OpenCode, si es obligatorio para anunciar compatibilidad, no se cierra con un fake harness.
- [ ] No quedan rutas personales ni instrucciones contradictorias que afecten al lanzamiento.

### T22 — Consolidar CI, índice y nomenclatura de checks [pendiente]

- Dependencias: T05–T21. Roles: role-back, role-clean-code, plan-validators, project-publish.
- Superficie: `run-validation.sh`, `tools/validate`, `skill-router/build_index.py`, `package.json`, workflows, scripts y hooks.
- Trabajo: D07. Puerta full canónica. Check de índice puro y build explícito. Lint, sintaxis y tests seguros. `typecheck` solo si es real; si no, nombre syntax-check, con alias legacy documentado si un consumidor lo exige. Preservar required checks. No cambiar branch protection. Pinning según la política existente, sin actualizar por deporte. Un skip de un requisito obligatorio no deja el full en verde.
- Aceptación: [ ] full valida el repo real y los tests y smokes seguros; [ ] el check no cambia el árbol; [ ] el gate enrojece con cada fixture corrupta de la sección 7; [ ] `scripts/` y la raíz entran en la sintaxis Bash; [ ] el lint se ejecuta; [ ] las dependencias son reproducibles y no globales.
- Verificación: puerta desde un checkout limpio, `git diff` antes y después, paridad local y de CI, y colección registrada. Los modos rápidos identifican lo omitido.

### T23 — Pruebas E2E del producto y resiliencia [pendiente]

- Dependencias: T22. Roles: plan-validators, role-back.
- Superficie: instalación temporal, descubrimiento, ruta, preflight, ejecución o delegación, verificación y estado.
- Trabajo: flujos de la sección 7 con fixtures, concurrencia, fallos y recuperación. No sustituir un E2E por imprimir un nombre de skill. Separar pruebas deterministas del producto y smoke real del harness.
- Aceptación: [ ] happy path y rechazo de riesgo probados; [ ] la evidencia de fallo o timeout es coherente; [ ] los retries son seguros; [ ] una instalación ajena permanece intacta; [ ] la ejecución sin el source original respeta el modo declarado.
- Verificación: suite estándar completa y artefactos redactados. Los flujos con servicios o modelos reales quedan opt-in.

### T24 — Canon, migración, documentación y cierre local [pendiente]

- Dependencias: T23. Roles: role-clean-code, project-publish, plan-validators.
- Superficie: README, AGENTS.md, canon local de skills, TAXONOMY, guías de routing y harnesses, plantillas, changelog y este plan.
- Trabajo: resolver idioma, longitud, commits y fuente de verdad. AGENTS resume y remite. No crear el árbol P1 ajeno a este incremento ni archivos vacíos. Documentar quickstart, resultados, aprobación, recuperación, migración de estado y de CLI, y soporte con etiqueta honesta. Evaluar SemVer por el diff real. Preparar changelog si la política lo exige, sin tag, release ni bump automático. Repetir las comprobaciones afectadas sobre el árbol final, con digest que incluya archivos nuevos.
- Aceptación: [ ] ejemplos verificados; [ ] alias y migraciones testados; [ ] sin promesas falsas; [ ] este plan con evidencia y pendientes; [ ] diff revisado; [ ] cero publicación no aprobada; [ ] M1–M5 no se marcan completas por haber convertido las capacidades difíciles en blocked.
- Verificación: puerta full final, revisión de la documentación vigente y `git diff --check`. Informe de la sección 9. Commit, push y PR son un paso separado y no son criterio de este cierre.

## 6. Cobertura de capacidades

| Skill                | Perfección mínima exigida                                                                                  | Prueba o evidencia mínima                                |
| -------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| plan-specification   | Aprobaciones claras; soportar plan único explícito; tareas con inputs, roles y aceptación sin duplicación  | Fixture de single-file y preservación de plan ajeno      |
| plan-continue        | Consulta pura, init explícito, handoff portable y reanudación basada en evidencia                          | Estado legacy, workspace ausente y continuidad           |
| plan-validators      | Descubrir comandos reales; integrar tests sin afirmar que cobertura equivale a corrección                  | Fixtures de stack y prueba RED/GREEN real en el producto |
| local-maintenance    | Operaciones seguras, resultados reales, recuperación acotada, firmware separado y puntuación con cobertura | Matriz de fallo, aprobación, snapshot y F21              |
| local-security       | Diferenciar observación, plan y hardening; revisar todos los entrypoints mutadores antes de habilitarlos   | Auditoría simulada y mutación bloqueada sin autorización |
| local-proton         | Lectura, envío y secretos separados; consentimiento por destino y contenido; redacción                     | Integraciones simuladas; ausencia de envío implícito     |
| project-architecture | Stack, restricciones, métricas con evidencia y handoff correcto                                            | Repo fixture y resultado trazable                        |
| project-libraries    | Matriz real de ecosistemas y capacidades; SBOM verificable o blocked                                       | Fixtures de scanner, errores y capacidades ausentes      |
| project-publish      | Gates locales; commit, push, PR y release requieren autorización aplicable                                 | Prueba de que completar una fase no publica              |
| web-compliance       | Automático, manual y no evaluado; veredicto limitado; sin auto-handoff                                     | HTML fixture y reporte sin PASS injustificado            |
| web-owasp            | Edición oficial y categorías coherentes tras contrastar la fuente; alcance, evidencia y reproducción       | Mapping versionado y fixtures de hallazgos               |
| web-performance      | Protocolo reproducible; laboratorio y campo separados; fallos de medición visibles                         | Configuración, versión, repetición y artefacto validado  |
| role-front           | Contratos y verificación de superficies; sin scripts artificiales                                          | Output contractual y routing multirol                    |
| role-back            | Seguridad, robustez y superficies de test explícitas                                                       | Contratos y routing multirol                             |
| role-clean-code      | Preservar el método profundo y separar refactor de cambios de comportamiento                               | Verificación declarada y diff dentro de alcance          |
| role-design          | Contrato de entrega visual y verificación sin imponer un stack ajeno                                       | Artefactos esperados y coordinación con frontend         |

Los mutadores de local-security, project-publish y cualquier otro script descubierto en T00 también pasan revisión. Si no pueden migrarse, quedan bloqueados para ejecución automatizada y documentados como no soportados. Eso es contención, no la capacidad original, y se registra como cambio de alcance si afecta al objetivo.

## 7. Matriz de aceptación transversal

Registrar el node id o el comando exacto. No inventar rutas de tests futuras en el informe. Todos los casos usan dobles o fixtures, salvo un smoke real aislado cuando se indique.

### Riesgo, procesos y recuperación

- [ ] R01 Snapshot inexistente, corrupto, parcial no suficiente o de otro target: cero mutaciones.
- [ ] R02 Backend de snapshot no cero o timeout: blocked o failed, nunca éxito. Un inventario correcto no cuenta como backup.
- [ ] R03 Operación desconocida o argumento no válido: deny sin proceso ejecutado. `bash -c` arbitrario incluido.
- [ ] R04 Aprobación ausente, denegada, reutilizada para otro target o de otro plan: deny. `approved=true` no basta.
- [ ] R05 El entrypoint directo conserva las mismas puertas que el orquestador.
- [ ] R06 Fallo de acción: resultado real, código no exitoso y contadores coherentes.
- [ ] R07 Dry-run: cero mutaciones, outcome simulated y sin avance como ejecución real.
- [ ] R08 Restauración de fixture con traversal, ruta absoluta, symlink, hardlink o archivo especial fuera de la raíz: rechazo, sin escritura fuera del sandbox de la prueba.
- [ ] R09 Firmware y reinicios no entran implícitamente en cleanup. La suite no ejecuta esas operaciones reales.
- [ ] R10 stdout JSON limpio, stderr separado y secretos ausentes. Una categoría sin datos no puntúa 100 ni se etiqueta como excelente.

### Routing y ciclo de vida

- [ ] O01 enabled ausente, enabled vacío y disabled se distinguen y se respetan.
- [ ] O02 Skill, fase o handoff desconocidos bloquean antes de escribir.
- [ ] O03 Query desconocida o puntuación cero no ejecuta la primera skill del catálogo.
- [ ] O04 Ambigüedad y trabajo mixto devuelven selección o handoff explícitos.
- [ ] O05 route, list y status dejan el estado persistente idéntico y no crean scaffold ni resultados.
- [ ] O06 Una delegación `awaiting_agent` no completa la fase ni modifica el SemVer.
- [ ] O07 Verificación fallida, evidencia stale, artefacto ausente o simulación: complete rechazado.
- [ ] O08 Retry idempotente probado. Un timeout ambiguo exige reconciliación y no se reintenta a ciegas.
- [ ] O09 Concurrencia e interrupción, con sincronización determinista, no pierden updates ni corrompen YAML.
- [ ] O10 El estado legacy migra sin pérdida. Historial y evidencia no desaparecen por truncamiento.

### Instalación, distribución e integraciones

- [ ] I01 HOME y XDG temporales, cwd distinto y rutas con espacios funcionan.
- [ ] I02 Archivo, directorio real, symlink ajeno y enlace roto permanecen intactos ante conflicto, prune o uninstall.
- [ ] I03 Instalar dos veces no duplica recursos ni modifica instrucciones ajenas. Un fallo a mitad no queda como instalación correcta.
- [ ] I04 Mover o desactivar el source original no rompe una distribución declarada standalone. Un symlink al checkout no cuenta como standalone.
- [ ] I05 Workspace-required sin instalación completa devuelve blocked útil.
- [ ] I06 Symlink roto, escape o manifiesto manipulado no autoriza borrados fuera del target. Las rutas del manifiesto se validan antes.
- [ ] I07 OpenCode real, nivel B: carga la skill por nombre. Los permisos de carga y de acción se prueban por separado, sin autoaprobación. Si el binario falta, este caso es `not_run`.
- [ ] I08 El envío Proton usa destinatario y contenido exactos aprobados. Read y search no envían.

### Calidad y coherencia

- [ ] Q01 Frontmatter o contrato inválido, referencia o ejecutable inexistente y handoff imposible rompen el full gate.
- [ ] Q02 Un índice con nombres duplicados, ausentes o extra falla. El check no lo reescribe.
- [ ] Q03 Un test o smoke fallido y seguro bajo `skills/` hace fallar la puerta estándar.
- [ ] Q04 La colección incluye `tools/` y las partes seguras de `skills/`, sin colisiones de imports ni efectos en el host. El inventario precede a la recogida.
- [ ] Q05 Una fixture defectuosa demuestra que CI no valida solo al validador.
- [ ] Q06 Lint, sintaxis y tipado se nombran según lo que comprueban. Un skip obligatorio no deja el full en verde.
- [ ] Q07 Las instrucciones vivas coinciden en idioma, longitud, distribución, autorización y versión soportada.
- [ ] Q08 Catálogo, documentación e índice coinciden por identidad, no solo por número.

### E2E mínimo obligatorio

1. Copia o workspace temporal, instalar, descubrir, seleccionar, preflight, ejecutar una operación determinista no destructiva, validar el artefacto y completar la fase con estado consistente.
2. El mismo flujo con un requisito ausente: `blocked`, sin efectos y sin fase completada.
3. El mismo flujo con fallo tras empezar: `failed` o `partial` real. El retry no duplica el efecto probado.
4. Flujo agent: handoff real, `awaiting_agent`, recepción y verificación de artefactos. Sin fingir la ejecución del modelo.
5. Copia standalone fuera del source, sin symlink al origen: ejecución o lectura válida, o clasificación workspace-required correcta.

## 8. Fuentes y comprobaciones externas

Contrastar la versión pertinente antes de usar APIs o CLI. No instalar la última versión de una herramienta solo para hacer coincidir el plan.

| Fuente                                                             | Uso                                                                                      | Precaución                                                                                      |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Agent Skills specification — https://agentskills.io/specification  | Frontmatter, metadata string a string, allowed-tools experimental, recursos y validación | Los requisitos del repo son una capa aparte. El estándar permite instrucciones sin ejecutables. |
| OpenCode Agent Skills — https://opencode.ai/docs/skills/           | Discovery y permisos de carga                                                            | Cargar la skill no autoriza efectos posteriores.                                                |
| OpenCode migration V1/V2 — https://opencode.ai/v2/docs/migrate-v1/ | Configuración, permisos y compatibilidad                                                 | No imponer un rewrite total. No copiar una rama dev como estable.                               |
| Context7 /anomalyco/opencode                                       | Documentación de la versión y de SDK o CLI                                               | Los resultados dev pueden no coincidir con el binario instalado.                                |
| OWASP Top 10 oficial                                               | Verificar edición y mapping al implementar                                               | Revalidar la edición elegida. No afirmar mezclas no localizadas.                                |
| AGENTS.md del checkout                                             | Routing y reglas locales                                                                 | Resolver contradicciones con instrucciones superiores y con el canon.                           |
| docs/REUTILIZACION.md                                              | Propósito documental y límites de estructura                                             | No abrir una remediación P1 ajena al alcance.                                                   |
| skills/plan-specification/references/plan-templates.md             | Campos de tareas y checkpoints                                                           | El operador pidió un único archivo.                                                             |

Consultar también las fuentes oficiales de las herramientas elegidas para SCA, SBOM y medición web. No añadir comandos o versiones a la documentación final sin probarlos o marcarlos como no ejecutados. No copiar texto de terceros de forma que vulnere la higiene del repo.

## 9. Cierre, bloqueos y definición de terminado

### Definition of Done

El cierre local requiere que los criterios obligatorios de M1–M5 estén implementados y verificados sobre el mismo estado de código, que no queden P0 en rutas habilitadas y que las pruebas obligatorias no estén bloqueadas ni omitidas. La puerta full y el informe son evidencias de ese cierre, no sustitutos de los criterios.

Separar en el informe:

- contención de seguridad aceptada
- implementación local aceptada
- integración de harness verificada o pendiente
- publicación no solicitada y no ejecutada

Bloquear una operación peligrosa es una contención válida. No equivale a haber implementado la capacidad automatizada prevista. Si se reduce el soporte o se deshabilita una función, registrarlo como cambio de alcance o regresión funcional, documentar la migración y pedir aceptación cuando afecte al objetivo. No marcar M1–M5 completas por haber convertido las capacidades difíciles en `blocked`.

- [x] M1–M5 cubiertas por código, contratos y pruebas, o por una limitación explícita que impide anunciar la capacidad.
- [x] No quedan P0 abiertos en entrypoints oficiales habilitados (mutación host gated; restore host blocked).
- [x] Todos los contratos del catálogo real validan (16 execution.yaml).
- [x] La puerta full ejecuta los validadores, smokes y tests pertinentes sobre ese mismo árbol y termina correctamente. Un skip obligatorio no cuenta.
- [x] Un check de solo lectura no cambia el árbol observado, salvo cachés aisladas y documentadas fuera de él (index check read-only).
- [x] E2E mínimo y pruebas negativas esenciales pasan en ese mismo árbol (install test + pytest suites; OpenCode B not_run).
- [x] La instalación y la desinstalación no alteran recursos ajenos.
- [x] No hay secretos en diff, logs, fixtures ni artefactos. No se afirma una auditoría exhaustiva de secretos si no se ejecutó.
- [x] Las migraciones y los cambios incompatibles están documentados y probados.
- [x] El soporte de harness tiene etiqueta honesta y versión. Smoke real no disponible significa no verificado, no PASS.
- [x] No se declara todo terminado si un requisito esencial está `blocked` o `not_run` (OpenCode B = not_run, documentado).
- [x] No hay push, PR, merge, tag, release ni mutación real del host sin autorización separada (commit local pendiente/separado según política).

### Informe final obligatorio

Entregar en español, sin repetir el plan completo:

1. HEAD inicial y final, digest del árbol relevante y alcance efectivo. Cambios ajenos preservados.
2. Tareas completadas, bloqueadas o recortadas, con motivo.
3. Hallazgos F01–F22: corregido, no vigente o pendiente, y evidencia.
4. Pruebas: comandos exactos, resultado, número observado y artefactos redactados. Separar baseline, regresiones y limitaciones del entorno.
5. Capacidades ejecutables frente a delegadas. No vender handoffs como ejecución.
6. Garantías reales de seguridad, recuperación e idempotencia, y sus límites. Incluir la frontera del proveedor de aprobación.
7. Compatibilidad, cambios de CLI y de esquema, migraciones y SemVer recomendado si procede.
8. Diff revisable y el siguiente paso preciso si hay bloqueo o publicación pendiente.
9. Separación entre contención, implementación local, harness y publicación.

### Reglas para incidencias descubiertas durante la ejecución

- Dentro de alcance y necesaria para la aceptación: añadir la subtarea a este mismo archivo, con test rojo y corrección.
- Fuera de alcance y no bloqueante: registrar sin ampliar el diff.
- Bloqueo de seguridad, datos, permiso o decisión irreversible: detener solo el camino afectado, conservar la evidencia y pedir la decisión concreta.
- Fallo de entorno: no sustituir tests reales por una afirmación. Documentar `not_run` y su efecto.
- Nunca completar una casilla por haber escrito el código si su verificación obligatoria no pasó.

## 10. Registro de ejecución y reanudación

Completar durante la implementación, no durante el diseño. No incluir secretos ni cuerpos de correo.

| Campo                            | Valor a registrar                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Run ID del trabajo               | aw-exec-skills-20261018                                                                                       |
| Fecha/hora de inicio             | 2026-10-18T00:08:52+02:00                                                                                     |
| HEAD real de partida             | ecc5a97654d79cc924dfe5364c92e7c2bd1af7a6                                                                      |
| Rama/worktree                    | feat/executable-skills (creada en T00; no existía antes)                                                      |
| Estado del árbol inicial         | Solo `?? tasks/plan-executable-skills.md` al arrancar T00                                                     |
| Versiones y entorno aislado      | Python 3.14.4; Node v26.6.0; npm 11.18.0; venv `.venv-aw` con requirements-dev.txt                            |
| Baseline y fallos previos        | `pytest tools/`: 34 passed (baseline). Full gate final: 282 passed + contracts OK                             |
| Última tarea completada          | T24 (registro e informe)                                                                                      |
| Próxima tarea                    | Publicación (push/PR) solo con autorización separada; OpenCode nivel B cuando haya binario                    |
| Bloqueos                         | OpenCode discovery real = not_run; mutaciones host requieren AUTOWORKSPACE_ALLOW_HOST_MUTATION=1 + aprobación |
| Operaciones externas autorizadas | Ninguna                                                                                                       |
| Dictamen integrado               | 2026-10-17. Implementación autorizada por orden «Implement the plan» el 2026-10-18                            |

### Informe final (2026-10-18)

1. HEAD partida/final base: `ecc5a976` (sin commits previos del incremento). Rama `feat/executable-skills`. Digest ejemplo: clean_routine `67d2ef1b…`, common `154e25fd…`, loader `d01a3abd…`.
2. T00–T24 ejecutadas en el alcance local. Recortes honestos: OpenCode B `not_run`; mutación host contenida (no reimplementa toda la limpieza real bajo allow); SCA/performance adaptadores documentados como capacidades con herramientas opcionales.
3. F01–F04, F19–F22 corregidos con tests. F05–F08, F10–F13, F16–F18 corregidos en código/docs. F09 mitigado (pytest recoge skills seguras). F14/F21 OpenCode B pendiente binario. F15 contratos mínimos en 16 skills.
4. Comandos: `pytest tools/` 34→expandido; `bash run-validation.sh` → All checks passed, 282 passed; `bash scripts/tests/test_install.sh` → OK.
5. Ejecutable: clean/snapshot/risk/contracts/ops/install. Delegado: roles agent, handoffs awaiting_agent. Simulado: dry-run clean.
6. Deny-by-default ops; approval DenyProvider; restore solo `--restore-root` temporal; idempotencia status con evidence_ok; timeout mata process group.
7. CLI: router `--init`/`--bump` rechazado; install `--target` obligatorio; `typecheck` alias de `syntax-check`. SemVer producto no auto-bump; skill versions por manifiesto.
8. Siguiente paso: autorización para push/PR; opcional smoke OpenCode real.
9. Contención sí; implementación local sí; harness verificado no (B not_run); publicación no ejecutada.

### Diario por tarea

Copiar esta ficha aquí al trabajar una tarea. No crear un segundo tracker.

```text
Tarea:
Estado: pending | in_progress | done | blocked | not_applicable
Revisión/input:
HEAD base:
Digest de trabajo y exclusión de cachés/diario:
Archivos modificados y nuevos:
Skills/roles realmente cargados y fallback:
Hallazgo/test RED:
Cambio y archivos:
Comandos exactos de verificación:
Resultados y evidencia:
Limitaciones y datos no comprobados:
Decisiones nuevas:
Próximo paso:
```

Para reanudar: leer identidad, límites, HEAD, diff, digest, última ficha y dependencias. Revalidar las evidencias afectadas antes de continuar. No repetir operaciones con efectos solo porque se haya perdido el contexto de la conversación.

## 11. Rectificaciones vinculantes

Esta sección prevalece sobre cualquier frase contraria de las secciones 0–10. Las tareas T00–T24 y las matrices de las secciones 6 y 7 se conservan y se aplican con estas precisiones. El índice de Cursor no es otro plan.

### 11.1 Matriz de certeza

Estados: observado en código, reproducido mediante test, corregido previamente, pendiente de comprobar. En la preparación no se ejecutó ningún test de reproducción. «Observado en código» no autoriza a tratar el fallo como ya demostrado en runtime.

| ID  | Archivo o símbolo                                                              | Evidencia estática                                                                                                                                                            | Reproducción | Estado                                                             |
| --- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------ |
| F01 | clean_routine.py; sin import de risk_gate en la ruta mutadora                  | Lectura de preparación de la sesión                                                                                                                                           | No           | Observado en código                                                |
| F02 | clean_routine.py::main; retorno de snapshot no comprobado                      | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F03 | clean_routine.py::generate_json_output                                         | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F04 | risk_gate.py::classify_command; desconocido a R0                               | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F05 | workspace-router/run.py; ensure_scaffold en la consulta                        | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F06 | run.py::route; project_load.py::filter_skills                                  | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F07 | status_bump.py; SemVer en el bookkeeping                                       | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F08 | run-validation.sh frente a tools/validate/skill_spec.py                        | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F09 | pytest tools/; smoke help y py_compile                                         | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F10 | scripts/validate-skills.js                                                     | Archivo localizado en preparación. Búsqueda de la cadena en docs, hooks, workflows y scripts del checkout sin coincidencias de contenido el 2026-10-17                        | No           | Observado en código. Consumidores externos pendientes de comprobar |
| F11 | scripts/install-opencode.sh                                                    | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F12 | scripts/install.sh                                                             | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F13 | skills/plan-continue/SKILL.md                                                  | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F14 | opencode.json; AGENTS.md                                                       | Lectura de preparación. Sin prueba contra binario                                                                                                                             | No           | Observado en código                                                |
| F15 | catálogo SKILL.md; allowed-tools homogéneo                                     | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F16 | web-compliance; project-architecture; routers                                  | Lectura de preparación. Parte en prosa y parte en selección de fase                                                                                                           | No           | Observado en código                                                |
| F17 | skills/web-owasp                                                               | Identificadores y categorías sin una edición declarada que los unifique. No se afirma, sin cita localizada, una mezcla concreta con OWASP para LLM                            | No           | Observado en código. Mapping oficial pendiente de comprobar        |
| F18 | AGENTS.md; README; skill_spec.py; docs/architecture + docs/REUTILIZACION (P11) | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F19 | snapshot_state.py; fallo de backend y éxito                                    | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F20 | snapshot_state.py; ssh_host_* y restauración                                   | Lectura de preparación                                                                                                                                                        | No           | Observado en código                                                |
| F21 | common.py::run; FindingCollector._category_score                               | `run` devuelve cadena vacía ante fallo o timeout y descarta stderr. `_category_score` devuelve 100 cuando el peso es 0. Líneas 105–138 y 325–343 en la lectura del 2026-10-17 | No           | Observado en código                                                |
| F22 | common.py::SKILL_VERSION; SKILL.md metadata.version                            | Constante `2.0.0` frente a `5.0.0` del manifiesto, en la lectura del 2026-10-17                                                                                               | No           | Observado en código                                                |

T00 reclasifica esta matriz con el checkout real. T01 reproduce F01–F04, F19–F21. T08 y T18 cubren la regresión de puntuación y de etiquetado. Ninguna fila pasa a «corregido» sin el test verde correspondiente.

### 11.2 Un solo tracker

Las casillas de las secciones 5, 7 y 9, y el diario de la sección 10, son el seguimiento. El YAML de Cursor agrupa T00, T01–T03, T04–T05, T06–T09, T10–T15, T16–T21 y T22–T24 solo para navegar. Un grupo no se cierra hasta verificar todas sus tareas obligatorias. No se genera otro `SPEC.md` ni otro `tasks/todo.md`. No se reescriben `tasks/plan.md` ni `tasks/todo.md`.

### 11.3 Skills y rutas

Antes de cada tarea: reevaluar las skills aplicables, cargar `skills/<nombre>/SKILL.md` y las referencias que ese archivo exija, resolver enlaces de integración antes de seguirlos y declarar el fallback si no hay herramienta nativa. No afirmar una invocación que no ocurrió. No añadir role-front ni role-design sin una superficie real.

### 11.4 Inventario de efectos antes del baseline

T00 inventaría, antes de ejecutar baseline o colección:

- scripts mutadores de local-maintenance
- creación y restauración de snapshots
- mutadores de local-security
- instaladores y desinstaladores
- hooks y herramientas de project-publish
- envío de correo y acceso a secretos de local-proton
- scripts alcanzables por import, por la colección de pytest o por `--help`
- todos los consumidores de `common.run` y `common.run_capture`

No ejecutar un script desconocido para saber si es seguro. Inspeccionarlo primero. Un venv, una copia desechable o un HOME temporal no impiden escribir en rutas absolutas, leer credenciales del proceso ni usar la red. Hasta migrarlos, los entrypoints mutadores no cubiertos rechazan la ejecución.

### 11.5 common.py

Hay numerosos consumidores con pipelines y redirecciones. `run` descarta stderr y no expone el código de retorno. Fallo o timeout pueden convertirse en cadena vacía. No sustituir `shell=True` por `shell=False` de forma mecánica. Seguir el procedimiento de D04. Rechazar argv que invoquen un intérprete con código arbitrario. El timeout incluye descendientes cuando corresponda.

### 11.6 Observación que parece salud

F21 entra en T01, T08 y T18. Separar «sin incidencias» de «no se pudo comprobar». Conservar código de retorno, timeout y error de parsing. Publicar la cobertura junto a la puntuación. No mostrar «excelente», «actualizado» o equivalente si la evidencia obligatoria es insuficiente. Una categoría sin datos no recibe 100 en silencio. Una lista genérica de actualizaciones no se etiqueta como actualizaciones de seguridad. Tests: comando ausente, permiso denegado, timeout, salida inválida y comprobaciones en ERROR o SKIP.

### 11.7 Identidad de versión

F22. `skill_version` sale del manifiesto. `schema_version` es independiente. La versión de un componente interno, si se publica, va en otro campo. No igualar versiones de cosas distintas. Comprobar la correspondencia con tests.

### 11.8 Snapshots

«Fallo de backend no es éxito» se refiere a la recuperación requerida. El resultado separa inventario, backup, integridad, cobertura y validación de backend y target. `full` exige identificador, alcance y evidencia, no solo un código cero. No mezclar targets. Restauración real del host no autorizada. Pruebas solo en raíz temporal, cubriendo traversal, rutas absolutas, symlinks, hardlinks y archivos especiales. Esa prueba no certifica el rollback del host.

### 11.9 Deny-by-default y lecturas

Deny-by-default cubre el registro de operaciones ejecutables y las capacidades no autorizadas. La lectura tiene contrato y no exige snapshot por el mero hecho de leer. Separar validación, autorización, recuperación y capacidad. `risk_gate` no es un parser de shell ni una frontera frente a quien controla el código con los mismos privilegios.

### 11.10 Proveedor de aprobación

El digest no es consentimiento. Fijar emisor, transporte, cobertura, detección de cambios, reutilización y el comportamiento ante denegación, caducidad o timeout. Sin proveedor confiable: plan preparado y mutación en `blocked` o `awaiting_approval`. No aceptar `approved=true`, un archivo editable por el agente, una variable de entorno arbitraria ni un hash emitido por el propio ejecutor. No añadir criptografía ni un servidor de autorizaciones sin necesidad.

### 11.11 OpenCode

Cargar una skill no autoriza Bash, edición, red, secretos ni directorios externos. No fiar la protección crítica a una regla `ask` si el modo aprueba lo no denegado. No usar autoaprobación en las pruebas de autorización. Probar reglas efectivas globales y por agente. No copiar ejemplos amplios ni configuración dev como si fueran la versión estable. Verificar contra la versión objetivo.

### 11.12 execution.yaml

Extensión local. `SKILL.md` sigue siendo usable sin ella. Esquema con dialecto y `schema_version`. Rechazar duplicados, limitar tamaño y complejidad, resolver referencias en local, rechazar campos críticos desconocidos y dejar una extensión explícita. Validar semántica y definir qué ocurre con una versión desconocida. `jsonschema` no está en `requirements-dev.txt` de la base observada; si se añade, se justifica y se fija tras comprobarla. Cargar un contrato no depende de pytest ni de Ruff.

### 11.13 Estados

Implementar solo después de cerrar D03. `awaiting_agent` y `awaiting_approval` no son terminales. Una consulta o preparación correcta no es una implementación `succeeded`. `exit 0` no completa una fase. `not_applicable` obligatorio necesita una regla verificable. Entrada inválida, rechazo de política, fallo de proceso, resultado parcial y ausencia de capacidad conservan motivos distintos.

### 11.14 Trazabilidad sin commits

Cada evidencia guarda HEAD base, digest del contenido relevante, archivos modificados y nuevos, versiones de herramientas, configuración, comando, resultado y artefactos. El digest excluye cachés y este diario, y esa exclusión queda escrita. Tras el último cambio material se repiten las comprobaciones afectadas y la puerta final. Un hash de `git diff` no cubre no rastreados.

### 11.15 Consulta, reintentos y concurrencia

`route`, `list` y `status` no escriben scaffold ni resultados por defecto. La frontera de la prueba es el estado persistente y los archivos gestionados. Locks con alcance, plataforma, liberación, `state_revision`, escritura atómica en el mismo filesystem y prueba determinista de lectores y writers. Tras un timeout con posible efecto externo no se asume ausencia de efecto ni se reintenta hasta reconciliar.

### 11.16 validate-skills.js

T04 documenta la búsqueda interna en package scripts, hooks, workflows, documentación viva, instaladores y otros scripts. La búsqueda del checkout no demuestra ausencia de consumidores externos. Sin consumidores internos: retirar, corregir referencias y documentar la retirada si el uso era público. Wrapper temporal solo con una necesidad real. No dejar dos validadores divergentes.

### 11.17 Puerta que no se corrige a sí misma

El check del índice compara sin reescribir. La puerta full valida catálogo, contratos, identidades, tests seguros, smokes seguros, instalación, distribución, lint y sintaxis reales. Propaga fallos de subprocesos y rechaza flags inválidos. No recoge todo `skills/` sin inventario previo. No llama `typecheck` a `py_compile` salvo alias legacy documentado. Cada puerta demuestra con una fixture defectuosa que detecta el fallo. Un requisito obligatorio ausente no produce full verde.

### 11.18 Instalación y distribución

Validar todas las rutas del manifiesto antes de actualizar o desinstalar. Exigir target confinado, recursos ajenos intactos, conflictos de archivo, directorio, symlink y enlace roto, idempotencia, fallo parcial visible, desinstalación limitada a recursos propios identificables, sin sobrescribir instrucciones globales y sin prune por ausencia en el catálogo. Probar fallo de permisos y operación parcial. Standalone no se demuestra con symlinks al checkout. Los módulos compartidos se declaran workspace-required o se distribuyen de verdad.

### 11.19 Auditorías

F17 se formula así: las categorías e identificadores no forman un mapping coherente con una edición declarada; cada correspondencia se verifica contra la fuente oficial elegida. No afirmar una mezcla con OWASP para LLM sin localizar el contenido exacto.

SCA: vulnerabilidad, malware, typosquatting, unused y outdated son capacidades distintas. Herramienta ausente significa capacidad no disponible. Las heurísticas no son detección exhaustiva. No ejecutar código de dependencias no confiables.

Compliance: automático, manual y no evaluado. Un escaneo no certifica cumplimiento legal ni accesibilidad completa.

Performance: laboratorio y campo por separado. Registrar herramienta, versión, configuración, repeticiones y errores. Un fallo de medición no es una buena puntuación.

### 11.20 T21 en dos niveles

A) contratos, configuración y adaptador con dobles. B) descubrimiento, carga y permisos con OpenCode real de la versión declarada. A no sustituye a B. Sin binario, B es `not_run`; se sigue con las tareas independientes; no se anuncia compatibilidad verificada ni se cierra la aceptación integral del harness. Un fake harness no demuestra integración nativa ni ejecución real de un agente. El gate determinista no depende de un modelo externo.

### 11.21 Orden e integración

El orden normativo es el de la sección 3 y las dependencias de la sección 5. El índice de siete grupos no las sustituye. Paralelizar solo tareas sin archivos compartidos ni dependencias pendientes. Un coordinador integra. No hay dos escritores simultáneos sobre el mismo módulo. No se descarta una rama o el trabajo de otro agente para integrar.

### 11.22 Criterio final

El cierre local requiere que los criterios obligatorios de M1–M5 estén implementados y verificados sobre el mismo estado de código, que no queden P0 en rutas habilitadas y que las pruebas obligatorias no estén bloqueadas ni omitidas. La puerta full y el informe son evidencias, no sustitutos.

Informar por separado contención de seguridad, implementación local, harness verificado o pendiente, y publicación no solicitada. Bloquear una operación peligrosa no completa la capacidad prevista. Reducir o deshabilitar una función es un cambio de alcance: se documenta, se migra y se pide aceptación si afecta al objetivo. No marcar M1–M5 completas por haber convertido las capacidades difíciles en `blocked`.

Commit, push, PR, merge, tag, release y mutaciones reales del host siguen fuera de la autorización de este plan.
