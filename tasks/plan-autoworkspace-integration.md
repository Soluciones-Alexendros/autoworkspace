# Integración agéntica, distribución y automejora de autoworkspace

Plan ID: `autoworkspace-integration-v1`  
Base analizada: `0811c9a3b6582c47692dbc80eb34b8cee8f95c80`  
Estado: **NO-GO — gates locales verificados; Cursor nativo, modelos y release nueva pendientes**  
Fuente de verdad: este documento. Las futuras especificaciones, el plan técnico, las tareas y la evidencia de este incremento se añadirán aquí, sin trackers paralelos.

## Objetivo del incremento

Convertir el catálogo, los routers, la ejecución y el estado existentes en un sistema integrado que pueda:

1. Ejecutar y verificar operaciones mediante una cadena pública coherente.
2. Reanudar un plan activo y programar sus tareas como un DAG.
3. Delegar tareas en subagentes con adaptadores nativos para Pi y Cursor.
4. Descargar, instalar, actualizar, verificar y desinstalar el sistema de forma reproducible.
5. Auditar y mejorar autoworkspace mediante una skill especializada que conozca el canon y la operativa sin duplicar sus fuentes normativas.

## Supuestos que deben corregirse antes de continuar

1. El núcleo seguirá usando Python; Bash queda limitado a wrappers finos. La integración Pi podrá usar TypeScript porque es el runtime nativo de sus extensiones.
2. No se introducirá un daemon, un servidor de agentes, una plataforma genérica de plugins ni una nueva familia de skills.
3. `tools/execution/registry.yaml` seguirá siendo la fuente de verdad declarativa de operaciones y efectos; el runtime y la evidencia deberán derivar de contratos coherentes con ella.
4. `run_registered` y las aprobaciones seguirán gobernando las operaciones reguladas. Delegar en un subagente no concede permisos adicionales.
5. Pi se distribuirá preferentemente como paquete nativo desde Git con un tag pineado. Los symlinks quedarán como flujo de desarrollo del checkout.
6. Cursor distribuirá el paquete completo —skills, rules, agents y hooks— mediante su plugin; cualquier instalador por proyecto deberá cubrir los mismos componentes o declarar explícitamente una instalación parcial.
7. La automatización nativa de Cursor no se dará por verificada mediante fixtures. Si el binario o el entorno necesario no están disponibles, el resultado será `not_run` o `blocked`, nunca PASS.
8. Se añadirá `project-autoworkspace` como skill 17 dentro del dominio `project`, sin crear dominios nuevos.
9. La publicación, los commits, los tags, las releases y las mutaciones externas quedan fuera de la autorización de diseño y requerirán su autorización específica.

## Mapa de capacidades

Los identificadores son estables durante el incremento. Las dependencias indican qué contrato debe existir antes de diseñar e implementar el módulo dependiente.

| Module id             | Responsabilidad y entrega principal                                                                                                                                                                                                                                            | Depends on                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `execution-contract`  | Unificar los identificadores de operaciones entre registry, runtime, evidencia y cierre; ofrecer una cadena pública ejecutar → verificar → registrar → completar; sustituir el E2E que construye manualmente el resultado de DEFINE por un recorrido real.                     | —                                                                                                                  |
| `harness-doctor`      | Definir un informe común de instalación y soporte: versión, fuente, componentes esperados/cargados, diagnósticos, capacidades y estados `pass`, `fail`, `blocked`, `not_run`; validar coherencia de versiones en todas las superficies de distribución.                        | —                                                                                                                  |
| `plan-runtime`        | Declarar el plan activo, su identidad y revisión; modelar tareas, dependencias, roles, artefactos y estados; conservar receipts e idempotencia por tarea; resolver todos los roles aplicables sin reducirlos al handoff único de fase.                                         | `execution-contract`                                                                                               |
| `pi-distribution`     | Empaquetar autoworkspace como paquete Pi pineado; documentar la instalación en una línea; validar descubrimiento nativo mediante RPC `get_commands`; cubrir instalación, repetición idempotente, actualización, desinstalación y ausencia del binario.                         | `harness-doctor`                                                                                                   |
| `cursor-distribution` | Hacer del plugin la distribución completa de Cursor; verificar manifiesto, skills, rules, agents y hooks; mantener la instalación de solo skills como modo explícitamente parcial; separar pruebas estáticas, headless e IDE.                                                  | `harness-doctor`                                                                                                   |
| `orchestration-core`  | Compilar el plan a un DAG validado; calcular tareas listas; aplicar límites de concurrencia, superficies de escritura, cancelación, fallo de dependencias y reanudación; agregar resultados sin confundir delegación con finalización.                                         | `execution-contract`, `plan-runtime`                                                                               |
| `pi-subagents`        | Implementar el adaptador Pi para delegación aislada, herramientas restringidas, salida estructurada, cancelación y concurrencia; enlazar cada resultado con plan, tarea, revisión y evidencia.                                                                                 | `orchestration-core`, `pi-distribution`                                                                            |
| `cursor-subagents`    | Implementar el adaptador Cursor con subagentes focalizados y verificador independiente; distinguir la delegación guiada por el modelo en el IDE de una ejecución headless determinista; capturar resultados verificables sin atribuir garantías inexistentes.                  | `orchestration-core`, `cursor-distribution`                                                                        |
| `secure-bootstrap`    | Publicar y descargar artefactos de release verificables; incorporar checksums y atestación; ofrecer un bootstrap de una línea sin `curl \| bash`, con tag inmutable, destino explícito, verificación posterior y recuperación ante instalación parcial.                        | `pi-distribution`, `cursor-distribution`                                                                           |
| `autoworkspace-skill` | Crear la skill `project-autoworkspace` para auditoría y mejora del propio sistema; incluir el mapa integral del canon, control plane, harnesses, migraciones y protocolo de autocambio; derivar arquitectura, planificación, validación y publicación a las skills existentes. | `execution-contract`, `plan-runtime`, `orchestration-core`, `pi-subagents`, `cursor-subagents`, `secure-bootstrap` |

## Orden de diseño y construcción por capas

```text
Capa 0: execution-contract · harness-doctor
             │                    │
             ▼                    ├──────────────┬──────────────────┐
Capa 1: plan-runtime              │              │                  │
             │                    ▼              ▼                  │
             │             pi-distribution  cursor-distribution    │
             ▼                    │              │                  │
Capa 2: orchestration-core        │              │                  │
             ├────────────────────┤              │                  │
             ▼                    ▼              ▼                  │
Capa 3: pi-subagents        cursor-subagents     │                  │
             │                    │              ▼                  │
             │                    │       secure-bootstrap          │
             └────────────────────┴──────────────┬──────────────────┘
                                                  ▼
Capa 4:                                 autoworkspace-skill
```

`secure-bootstrap` puede especificarse después de las dos distribuciones sin esperar a los adaptadores de subagentes. `autoworkspace-skill` se cierra al final para documentar el sistema realmente integrado, no una arquitectura aspiracional.

## Contratos entre módulos que deben preservarse

1. `execution-contract` es proveedor de identidad de operación, resultado y evidencia; ningún adaptador podrá inventar `OpResult` para simular trabajo.
2. `plan-runtime` es proveedor de identidad de plan/tarea y transiciones; el scheduler no editará libremente `status.yaml`.
3. `orchestration-core` no conocerá APIs concretas de Pi o Cursor: consumirá puertos de delegación y resultados normalizados.
4. Los adaptadores no decidirán políticas de aprobación ni criterios de aceptación; delegarán esas decisiones en el núcleo y en las puertas existentes.
5. `harness-doctor` reportará capacidades observadas. Una ausencia o una comprobación omitida no se convertirá en éxito.
6. `autoworkspace-skill` enlazará las fuentes canónicas y no mantendrá copias divergentes de ADRs, glosario, taxonomía o contratos.
7. Ningún módulo publicará automáticamente al completar otro módulo o fase.

## Límites globales

### Always

- Mantener una única fuente de verdad por contrato y un único documento canónico para este incremento.
- Validar entradas, rutas, identidades, dependencias y resultados antes de ejecutar efectos.
- Probar primero los fallos y después el comportamiento corregido mediante la suite del repositorio.
- Repetir `make validate` y las pruebas nativas afectadas después del último cambio material.
- Conservar trabajo ajeno, recursos ajenos y planes históricos.

### Ask first

- Añadir dependencias, cambiar esquemas públicos, modificar CI o introducir una skill adicional.
- Instalar o actualizar binarios de harness fuera de entornos aislados.
- Ejecutar pruebas con coste, credenciales, red no pública o servicios externos.
- Autorizar escritores paralelos que compartan worktree o superficie de archivos.
- Cualquier commit, push, PR, merge, tag, release o cambio de configuración global.

### Never

- Ejecutar mantenimiento real, enviar correo, acceder a secretos o modificar el host para probar estos componentes.
- Usar `curl | bash`, tags flotantes o una descarga sin verificar como bootstrap seguro.
- Presentar `skip`, dependencia ausente, simulación o `not_run` como PASS.
- Permitir que un subagente amplíe por sí mismo permisos, alcance, dependencias o publicación.
- Crear un segundo registry, otro plan canónico o documentación copiada que pueda divergir del canon.

## Criterios de aceptación de la Fase 0

- [x] El operador aprueba los diez módulos y sus responsabilidades.
- [x] El operador aprueba la dirección de dependencias y el orden por capas.
- [x] El operador confirma la creación de `project-autoworkspace` como skill 17.
- [x] El operador confirma Pi como paquete nativo y Cursor como plugin completo.
- [x] Los supuestos y límites globales quedan aceptados.

## Decisiones aprobadas

1. Se crea `project-autoworkspace` como skill 17, dominio `project`.
2. Pi se distribuye inicialmente solo desde Git con tag pineado; npm queda fuera.
3. La validación nativa de Cursor es obligatoria para el cierre integral.
4. El primer recorrido será completo: delegación, escritura, integración, verificación, evidencia y cierre. Se ejecutará sobre proyectos fixture y worktrees temporales, no sobre el host ni una publicación real.
5. El bootstrap mediante artefactos con checksum y atestación de provenance forma parte obligatoria del incremento.

# Fase 1 — Especificaciones

## Especificación transversal

### Objetivo

Entregar una arquitectura modular en la que el catálogo, la ejecución, el estado, los harnesses y la distribución compartan contratos explícitos. El sistema debe poder completar un recorrido real con escritura y verificación sin otorgar autonomía de publicación ni permisos sobre el host.

### Tech Stack

- Python 3.12 o superior para contratos, scheduler, estado, doctor y pruebas.
- YAML/JSON Schema para documentos declarativos; parsers seguros, rechazo de claves duplicadas y esquemas locales.
- Bash únicamente para wrappers y compatibilidad de instaladores existentes.
- TypeScript solo en extensiones Pi, usando los paquetes proporcionados por el host como `peerDependencies`.
- Pi con paquetes Git pineados, modo JSON/RPC y procesos aislados.
- Cursor con plugin, custom subagents y CLI headless; la versión exacta aceptada quedará registrada en la evidencia.
- Git worktrees y patches para aislar e integrar escrituras sin exigir commits durante la ejecución.

No se añadirá otro framework de orquestación ni una base de datos. Cualquier dependencia nueva exigirá justificación y actualización de lockfiles en el plan técnico.

### Commands

Comandos existentes que deben seguir funcionando:

```bash
make validate
make test
make smoke
npm run typecheck
```

Interfaces nuevas propuestas; su implementación no está autorizada por esta especificación:

```bash
uv run --project tools --frozen python tools/harness/doctor.py --harness all --json
uv run --project tools --frozen python tools/orchestrator/run.py --repo . --plan tasks/plan-example.md --adapter pi --json
uv run --project tools --frozen python tools/orchestrator/run.py --repo . --plan tasks/plan-example.md --adapter cursor --json
make validate-harnesses
make e2e-orchestration
```

`make validate` conservará las puertas deterministas y nativas sin credenciales. `make validate-harnesses` incluirá Cursor headless y el recorrido nativo completo; su ausencia o fallo impedirá el cierre integral. Los comandos concretos de instalación nativa se documentan en sus módulos.

### Project Structure

```text
tools/contracts/       → esquemas y loaders de operaciones, planes y resultados
tools/execution/       → registry, ejecución, aprobación y evidencia
tools/orchestrator/    → DAG, scheduler, worktrees, puertos y agregación
tools/harness/         → doctor y clientes nativos Pi/Cursor
extensions/            → extensión empaquetada de Pi
.cursor/agents/        → subagentes Cursor focalizados
.cursor-plugin/        → manifiesto del plugin completo
scripts/               → wrappers e instalación/bootstrap
skills/                → catálogo Agent Skills, incluida project-autoworkspace
.autoworkspace/        → plan activo, estado y evidencia; nunca código ejecutable descargado
```

Las rutas nuevas son propuestas de diseño; el plan técnico podrá ajustar nombres de archivos internos sin cambiar los contratos aprobados.

### Code Style

- Identificadores y código en inglés; documentación operativa para el operador en español.
- Funciones pequeñas, tipos explícitos, resultados estructurados y errores sin pérdida de causa.
- `shell=False` para procesos modelados; rechazo de intérpretes con código libre y de parámetros desconocidos.
- Stdout reservado a JSON cuando se solicite `--json`; diagnósticos redactados en stderr.
- Escrituras atómicas, locks con alcance documentado, timeouts y cancelación de descendientes.
- Un mismo resultado no se serializará de forma distinta por harness: los adaptadores normalizan hacia los contratos comunes.

### Testing Strategy

1. **Unitarias:** parsers, validación, DAG, transiciones, selección de roles, redacción y resultados.
2. **Integración:** registry → ejecución → verificación → evidencia → estado; instalación → doctor; plan → scheduler → adaptador simulado.
3. **Nativas sin modelo:** Pi RPC `get_commands`, manifiestos y comandos disponibles.
4. **Nativas con modelo:** recorrido completo Pi y Cursor sobre fixture, con escritura en worktree, integración en staging, verificador y cierre.
5. **Adversarias:** dependencia cíclica, solape de escritura, resultado inválido, evidencia stale, timeout, cancelación, denegación, reintento, instalación parcial, checksum incorrecto y atestación inválida.
6. **Regresión:** `make validate`, cobertura no inferior a la puerta existente y pruebas de defectos sembrados para demostrar que las nuevas puertas fallan.

Los dobles solo sustituyen procesos, modelos o servicios peligrosos en tests unitarios/integración. No sustituyen la aceptación nativa obligatoria. En tests unitarios del store podrán existir fixtures de resultados; en los E2E públicos queda prohibido construir manualmente un resultado que no proceda de la ejecución.

### Cierre integral

El incremento solo será completo cuando todos los módulos cumplan sus criterios sobre la misma identidad final, el recorrido completo pase en Pi y Cursor, la instalación pineada y el bootstrap verificado funcionen, y `make validate` y `make validate-harnesses` estén verdes. La publicación real es un estado posterior separado.

## SPEC: `execution-contract`

### Objetivo

Hacer que registry, runtime, evidencia y cierre hablen de las mismas operaciones y que toda evidencia de éxito proceda de una ejecución pública verificada.

### Interfaces y estructura

- `tools/execution/registry.yaml`: único catálogo declarativo de `operation_id`, skill, efecto, aprobación, recuperación, timeout y distribución.
- `tools/execution/registry.py`: carga y valida especificaciones; el mapa mutable solo registrará handlers, sin redefinir políticas ni IDs.
- `tools/contracts/schemas/result.schema.json`: sobre común con `run_id`, `operation_id`, `plan_id`, `task_id`, `skill`, `target`, `input_digest`, `output_digest`, `outcome`, artefactos y verificaciones.
- API pública `run_verified(...)`: captura entrada, ejecuta mediante `run_registered`, invoca el verificador declarado, registra el resultado y devuelve el sobre. No avanza planes por sí misma.
- `tools/execution/evidence.py`: acepta únicamente operaciones canónicas del registry y exige los bindings y verificadores de la fase/tarea correspondiente.
- Los IDs históricos que solo aparecen en allowlists de evidencia se migran a IDs reales del registry. Evidencia legacy incompatible se rechaza con diagnóstico o se migra explícitamente; no se acepta mediante alias silenciosos.

### Commands

```bash
uv run --project tools --frozen python -m execution.registry --check --root .
uv run --project tools --frozen pytest tools/execution/tests tools/contracts/tests -q
bash scripts/tests/test_execution_e2e.sh
```

### Estilo

Dataclass/tipos inmutables para especificaciones; handlers registrados por ID canónico; ninguna política duplicada en Python; ningún éxito inferido de `returncode=0` sin verificación de entregable.

### Testing Strategy

- Fixtures que demuestren que toda operación de runtime existe en YAML y toda operación de cierre es resoluble.
- RED actual: IDs divergentes y E2E con resultado manual; GREEN mediante la API pública.
- Captura de input antes del efecto y output después de verificar; modificación intermedia invalida evidencia.
- Denegación, handler ausente, `None`, fallo, timeout, verificación negativa y artefacto cambiado no producen cierre.
- El E2E positivo usa un handler real o un doble registrado en el boundary de ejecución, pero atraviesa `run_verified` y el store de producción sin instanciar `OpResult` manualmente.

### Boundaries

No se relajarán las aprobaciones ni se añadirán operaciones ficticias de producto para facilitar tests. Cambios incompatibles de API se tratarán según SemVer del contrato.

### Success Criteria

- Cero IDs divergentes entre registry, runtime y evidencia.
- Un recorrido positivo real completa DEFINE con una especificación fixture válida.
- Ningún resultado fabricado, simulado o no verificado puede completar una fase.
- Los nueve tipos de cierre actuales quedan migrados, sustituidos o eliminados explícitamente según su operación real.

### Open Questions

Ninguna. El impacto SemVer se calculará en el plan según la compatibilidad final, sin presumir que sea minor.

## SPEC: `harness-doctor`

### Objetivo

Proporcionar un diagnóstico uniforme y accionable de instalación, descubrimiento y capacidades de cada harness.

### Interfaces y estructura

- `tools/harness/doctor.py --harness pi|cursor|all --target DIR --expected-version X.Y.Z --json`.
- `tools/harness/base.py`: contrato de comprobación y resultado.
- `tools/harness/pi.py` y `cursor.py`: sondas específicas sin lógica de aceptación propia.
- `tools/contracts/schemas/harness-report.schema.json`.
- Informe con `harness`, `harness_version`, `package_version`, `source`, `ref`, `target`, `components`, `checks`, `capabilities`, `outcome` y `reasons`.
- Niveles: A = recursos/instalación; B = descubrimiento/carga nativa; C = acción y política nativa. Cada nivel conserva su propio estado.
- Códigos: 0 PASS; 1 FAIL o requisito obligatorio `not_run`; 2 entrada inválida; 3 capacidad bloqueada/ausente.

### Commands

```bash
uv run --project tools --frozen python tools/harness/doctor.py --harness all --target . --json
uv run --project tools --frozen pytest tools/harness/tests -q
```

### Estilo

Checks pequeños e independientes, salida JSON sin logs, rutas resueltas, versiones observadas y ningún valor inventado cuando una sonda no pueda ejecutarse.

### Testing Strategy

HOME/XDG/PATH temporales, targets con espacios, binario ausente, versión incorrecta, skill rota, componente parcial, recurso ajeno y diagnóstico nativo malformado. Una fixture defectuosa por tipo de check debe hacer fallar el doctor.

### Boundaries

El doctor no repara, instala, actualiza ni concede confianza. No lee valores secretos ni persiste prompts o credenciales.

### Success Criteria

- Detecta instalación válida, parcial, ajena, desactualizada y corrupta.
- Distingue A/B/C y nunca agrega un PASS global si falta una capacidad obligatoria.
- Las versiones de repo, paquete Pi, plugin Cursor e instaladores son coherentes o la deriva queda explícitamente rechazada.

### Open Questions

Ninguna.

## SPEC: `plan-runtime`

### Objetivo

Convertir un documento canónico en un plan activo direccionable, con tareas verificables, dependencias y reanudación segura.

### Interfaces y estructura

- El plan canónico seguirá siendo Markdown e incluirá un bloque YAML `aw-plan` con `schema_version`, `plan_id`, `base_revision` y `tasks`.
- `tools/contracts/schemas/plan.schema.json` y loader seguro; no habrá un segundo archivo de tareas.
- Cada tarea declara `id`, `phase`, `operation`, `roles`, `depends_on`, `read_scope`, `write_scope`, `artifacts`, `acceptance`, `verification` y política de fallo.
- `.autoworkspace/status.yaml` añade `active_plan`, `plan_digest`, `state_revision`, `tasks` y receipts; el campo `version` de producto permanece independiente.
- API de transición por tarea: `start_task`, `await_task`, `complete_task`, `fail_task`, `retry_task`; solo `complete_task` acepta evidencia válida.
- La fase activa se deriva de las tareas pendientes; al completar una fase se activa la siguiente disponible sin exigir otra selección manual.
- La selección de roles valida el conjunto declarado contra allowlist y superficie. El handoff de fase queda como fallback de descubrimiento, nunca como sustituto de los roles de la tarea.

### Commands

```bash
uv run --project tools --frozen python tools/workspace-router/run.py --status --repo . --json
uv run --project tools --frozen pytest tools/workspace-router/tests tools/contracts/tests -q
```

### Estilo

IDs kebab-case, dependencias acíclicas, transiciones explícitas, actualizaciones bajo lock, escritura atómica y compatibilidad de lectura migrada para estados anteriores.

### Testing Strategy

Planes vacíos, ciclos, dependencias ausentes, IDs duplicados, roles no permitidos, paths que escapan, dos escritores concurrentes, replay, estado stale, interrupción antes/después de escritura y reanudación con cambio de digest. El plan histórico no activo no puede reanudarse por mera existencia.

### Boundaries

El runtime no ejecuta tareas ni publica. No reescribe planes históricos ni cambia SemVer por bookkeeping. Toda modificación del plan aprobado invalida las tareas afectadas y exige revalidación.

### Success Criteria

- Existe un único plan activo y cada resultado queda ligado a `plan_id` + `task_id` + digest.
- Un DAG válido deriva correctamente tareas listas y fase activa.
- Reintentos idempotentes no duplican cierres ni efectos.
- Todos los roles declarados llegan al contrato de ejecución de la tarea.

### Open Questions

Ninguna.

## SPEC: `pi-distribution`

### Objetivo

Instalar el catálogo y la futura extensión como un único paquete Pi desde Git, con verificación nativa automatizable.

### Interfaces y estructura

- `package.json` declara `keywords: ["pi-package"]` y `pi.skills`; cuando exista, `pi.extensions` apuntará a la extensión.
- Instalación personal:

  ```bash
  pi install git:github.com/Soluciones-Alexendros/autoworkspace@vX.Y.Z
  ```

- Instalación de proyecto mediante la variante `--local`, sujeta a la confianza nativa del proyecto.
- `pi list` para declaración; RPC `get_commands` para skills/comandos cargados, `sourceInfo.origin=package` y `baseDir` esperado.
- `scripts/install-pi.sh` queda documentado para desarrollo con symlinks, no como distribución de release.
- Actualizar significa seleccionar explícitamente otro tag; no se espera que `pi update` mueva una referencia pineada.

### Commands

```bash
pi install git:github.com/Soluciones-Alexendros/autoworkspace@vX.Y.Z
pi list
pi --mode rpc --no-session
uv run --project tools --frozen python tools/harness/doctor.py --harness pi --expected-version X.Y.Z --json
```

### Estilo

Recursos convencionales, dependencias de host como peers, ningún código de instalación global personalizado y ninguna escritura en settings del operador durante tests.

### Testing Strategy

HOME temporal y proyecto vacío; instalación desde path y desde un repositorio Git fixture con tag; RPC sin modelo; 17 skills tras añadir la nueva; repetición idempotente; cambio explícito de tag; desinstalación; paquete roto y binario ausente. Smoke posterior a release contra la URL pública pineada, separado del gate de PR.

### Boundaries

Sin npm, refs flotantes, autoaprobación de proyectos ni instalación real durante las pruebas del checkout. La carga de una skill no prueba permisos de acción.

### Success Criteria

- Una línea instala una versión inmutable y el doctor demuestra su descubrimiento nativo.
- La actualización entre dos tags carga exactamente los recursos de la nueva versión.
- La desinstalación no afecta paquetes o skills ajenos.
- La ausencia de Pi o una carga incompleta bloquea el PASS nativo.

### Open Questions

Ninguna; npm queda expresamente fuera.

## SPEC: `cursor-distribution`

### Objetivo

Distribuir y validar el sistema completo de Cursor, manteniendo explícita la diferencia entre plugin completo e instalación parcial de skills.

### Interfaces y estructura

- `.cursor-plugin/plugin.json`: versión coherente con el repo y rutas a skills, rules, agents y hooks.
- `.cursor-plugin/marketplace.json`: entrada nativa de distribución.
- `.cursor/rules/`, `.cursor/agents/`, `.cursor/hooks.json` y `.cursor/hooks/`: componentes versionados.
- `scripts/install.sh --harness cursor --components skills|full`: compatibilidad explícita; `skills` se reporta como parcial y `full` exige journal para todos los recursos.
- Doctor A: manifiesto/rutas/symlinks. Doctor B: skills, reglas y subagentes descubiertos. Doctor C: acción permitida/denegada y comportamiento de hooks.
- La aceptación nativa registrará versión de Cursor CLI/IDE y modalidad headless o IDE.

### Commands

```bash
agent --version
uv run --project tools --frozen python tools/harness/doctor.py --harness cursor --target . --json
bash scripts/tests/test_install.sh
make validate-harnesses
```

Los flags de ejecución/permiso de `agent` se fijarán en el plan únicamente tras comprobar la documentación de la versión instalada.

### Estilo

Manifest declarativo, hooks con working directory portable, subagentes focalizados y componentes ajenos preservados. Ningún hook dependerá de rutas personales.

### Testing Strategy

Validación estática de todas las rutas; fixtures de plugin incompleto; hooks con payloads reales documentados; nivel B de descubrimiento; nivel C con sentinel benigno para deny/ask/allow; recorrido headless obligatorio. Si `agent` o credenciales faltan, el chequeo es `not_run` y el cierre integral permanece bloqueado.

### Boundaries

No se instalará Cursor ni se escribirá configuración real sin autorización. Las pruebas de PR no requerirán secretos; la puerta nativa usará un entorno dedicado y redactará su salida.

### Success Criteria

- El plugin carga los cuatro tipos de componentes en la versión aceptada.
- La instalación parcial nunca se anuncia como sistema completo.
- Native B y C están verificados, incluidos deny/ask sin efectos antes de decisión.
- La versión observada y los resultados quedan almacenados como evidencia de cierre.

### Open Questions

Ninguna. La ausencia actual del CLI es una limitación de ejecución, no una exención de aceptación.

## SPEC: `orchestration-core`

### Objetivo

Ejecutar el DAG de un plan con delegación, aislamiento de escritura, integración, verificación y reanudación, sin conocer detalles de Pi o Cursor.

### Interfaces y estructura

- `tools/orchestrator/model.py`: `Task`, `Plan`, `TaskState`, `RunContext`.
- `tools/orchestrator/ports.py`: `SubagentAdapter.execute(task, context) -> AdapterResult`; el adaptador no decide autorización ni aceptación.
- `tools/orchestrator/scheduler.py`: ready set, dependencias, concurrencia y fail-fast.
- `tools/orchestrator/worktrees.py`: worktree temporal por escritor, patch binario, staging de integración y limpieza preservando evidencia.
- `tools/orchestrator/runner.py`: ejecución, verificación independiente, evidencia y transición mediante APIs públicas.
- CLI `run.py --plan PATH --adapter pi|cursor --max-parallel 4 --dry-run --resume --json`.
- Resultados bajo `.autoworkspace/runs/<run_id>/`; cada tarea guarda resultado, artefactos, patch, digest, diagnósticos redactados y receipt.
- Escritores nunca comparten worktree. Lectores solo comparten workspace si no hay escritor concurrente. La integración aplica patches en orden topológico al staging y ejecuta verificadores.
- El operador checkout no se modifica por aplicación automática: aplicar el resultado integrado fuera del staging es una operación posterior explícita.

### Commands

```bash
uv run --project tools --frozen python tools/orchestrator/run.py --plan PATH --adapter pi --dry-run --json
uv run --project tools --frozen python tools/orchestrator/run.py --plan PATH --adapter pi --resume --json
make e2e-orchestration
```

### Estilo

Scheduler síncrono/orquestado con límites explícitos, sin daemon; dependencias deterministas; procesos en grupos cancelables; recuperación de estado antes de reintentar.

### Testing Strategy

- Recorrido completo fixture: especificar → implementar un archivo → integrar patch → verificar contenido/tests → evidencia → cierre.
- Dos lectores independientes, dos escritores disjuntos, solape rechazado, dependencia fallida, fail-fast, cancelación y timeout.
- Resume tras terminar el coordinador entre tareas; replay de receipt; cambio de plan o patch invalida evidencia.
- Un verificador que no se ejecuta o falla impide completar aunque el worker devuelva éxito.

### Boundaries

Sin commits, pushes, merges o publicación. Sin ejecución fuera de worktrees/staging autorizados. Un timeout con efecto incierto exige reconciliación antes de retry.

### Success Criteria

- El recorrido completo produce un cambio integrado y verificado en staging, no solo texto de subagentes.
- El orden y la concurrencia respetan el DAG y las superficies declaradas.
- La reanudación conserva trabajo y no repite tareas exitosas.
- Pi y Cursor consumen el mismo núcleo sin ramificaciones de política.

### Open Questions

Ninguna; se aprueba expresamente el recorrido con escritura en fixtures.

## SPEC: `pi-subagents`

### Objetivo

Proveer un adaptador Pi de contexto aislado que ejecute paquetes de tarea y devuelva resultados normalizados al núcleo.

### Interfaces y estructura

- `extensions/autoworkspace/index.ts`: registra `aw_subagent` y comandos de diagnóstico mínimos.
- `extensions/autoworkspace/subagent.ts`: proceso Pi hijo con `--mode json -p --no-session`, selección explícita de skill/rol, tools restringidas y modelo heredado salvo configuración de tarea.
- `extensions/autoworkspace/agents/`: prompts focalizados cargados por la propia extensión; no se asume que Pi descubra `agents/` como recurso de paquete.
- Entrada: sobre de tarea serializado. Salida: eventos JSON, texto final, herramientas usadas, stop reason, uso, exit code y artefactos declarados.
- Una llamada ejecuta una tarea; la concurrencia pertenece al scheduler para evitar un segundo orquestador.
- Los prompts temporales tienen permisos privados y limpieza garantizada; logs no incluyen contenido sensible.

### Commands

```bash
pi install git:github.com/Soluciones-Alexendros/autoworkspace@vX.Y.Z
pi --mode rpc --no-session
make validate-harnesses
make e2e-orchestration
```

### Estilo

TypeScript estricto, `spawn` sin shell, límites de salida, propagación de abort, grupo de procesos y ningún paquete Pi host duplicado en dependencies.

### Testing Strategy

Unitarias de parsing/descubrimiento con proceso doble; integración con un ejecutable fixture; nativa Pi real con tarea de escritura benigna; skill incorrecta, tools denegadas, salida truncada, modelo con error, abort y timeout. El recorrido nativo debe usar el paquete instalado, no importar el ejemplo de Pi.

### Boundaries

El hijo no hereda aprobación externa ni acceso a secretos por defecto. Proyectos no confiables no cargan recursos de proyecto. No se ofrece un modo paralelo independiente del núcleo.

### Success Criteria

- Pi ejecuta una tarea real con contexto aislado y entrega verificable.
- Las herramientas efectivas respetan la restricción declarada.
- Cancelación y timeout no dejan procesos activos ni cierres falsos.
- El adaptador devuelve evidencia suficiente para `plan-runtime` y `execution-contract`.

### Open Questions

Ninguna.

## SPEC: `cursor-subagents`

### Objetivo

Integrar los subagentes Cursor con el mismo scheduler, distinguiendo la delegación del IDE de la ejecución headless reproducible.

### Interfaces y estructura

- `.cursor/agents/aw-verifier.md`: verificador read-only existente, reforzado con el sobre de resultado.
- Definiciones focalizadas para planificación/exploración y roles de implementación que remitan a las skills canónicas, sin duplicar sus procedimientos.
- `tools/harness/cursor.py`: cliente headless y normalizador de salida para el puerto `SubagentAdapter`.
- Hooks de finalización de subagente podrán capturar metadatos cuando la API documentada lo permita; nunca sustituirán artefactos ni verificación.
- En IDE, la descripción podrá favorecer delegación automática. En headless, el coordinador invocará cada tarea explícitamente y no dependerá de que el modelo decida delegar.
- Cada ejecución recibe plan, tarea, rol, worktree, herramientas permitidas y criterios de entrega.

### Commands

```bash
agent --version
make validate-harnesses
make e2e-orchestration
```

### Estilo

Prompts concisos, responsabilidades únicas, modelos heredados por defecto y políticas externas al prompt. La configuración exacta se valida contra la versión instalada.

### Testing Strategy

Descubrimiento de subagentes; invocación de cada rol; escritura en fixture; verifier independiente; deny/ask/allow; resultado vacío o incompleto; cancelación; reintento y cambio de worktree. Comparación del resultado headless con el contrato común usado en Pi.

### Boundaries

No se afirmará scheduling determinista en el IDE por usar frases como «use proactively». No se habilitará autoaprobación para obtener PASS. La validación nativa es obligatoria.

### Success Criteria

- Cursor completa el mismo recorrido fixture que Pi mediante el núcleo compartido.
- El verificador no implementa ni publica y rechaza entregas sin evidencia.
- Los resultados incluyen versión, herramientas, artefactos y estado observable.
- IDE asistido y headless quedan reportados como capacidades distintas.

### Open Questions

Ninguna.

## SPEC: `secure-bootstrap`

### Objetivo

Ofrecer descarga e instalación en una línea con artefactos identificables, verificación previa a ejecutar y validación posterior.

### Interfaces y estructura

- Release publica `autoworkspace-X.Y.Z.tar.gz`, `SHA256SUMS` y atestación de provenance vinculada al commit/tag.
- `.github/workflows/release.yml` sube los artefactos a la Release; la atestación por sí sola no cuenta como distribución.
- `scripts/bootstrap.sh --version X.Y.Z --harness pi|cursor --target DIR --dry-run --json`.
- El bootstrap resuelve un directorio temporal privado, descarga con `gh release download`, comprueba checksum y ejecuta `gh attestation verify` antes de extraer o instalar.
- Extracción confinada, sin traversal/links/especiales; instalación mediante el instalador nativo correspondiente; doctor obligatorio al final.
- La línea pública documentada combinará descarga, verificación y ejecución con `&&`; no descargará código directo a un intérprete.
- La instalación Pi preferente sigue siendo `pi install git:...@vX.Y.Z`; el bootstrap cubre el paquete completo y Cursor.

### Commands

```bash
bash scripts/bootstrap.sh --version X.Y.Z --harness cursor --target DIR --dry-run --json
gh attestation verify autoworkspace-X.Y.Z.tar.gz -R Soluciones-Alexendros/autoworkspace
uv run --project tools --frozen python tools/harness/doctor.py --harness all --target DIR --json
```

### Estilo

Bash fino y `set -euo pipefail`, temporales privados, paths con espacios, sin shell remoto, salida JSON y códigos del estándar.

### Testing Strategy

Release fixture local, checksum alterado, atestación ausente/inválida, tag incorrecto, archivo con traversal, destino con conflicto, fallo a mitad, rollback y doctor negativo. Smoke post-release real obligatorio para declarar la distribución publicada, con autorización de publicación separada.

### Boundaries

Nunca `curl | bash`, tag `main`, descarga sin verificar, escritura antes de validar el artefacto ni borrado de recursos ajenos. La release real no forma parte de las pruebas de implementación.

### Success Criteria

- Los assets aparecen en la Release y su digest/atestación corresponden al tag.
- Una línea documentada descarga, verifica, instala y ejecuta el doctor.
- Cualquier fallo de autenticidad, integridad o descubrimiento impide la instalación o la revierte.
- Pi y Cursor producen un informe de versión y componentes coherentes.

### Open Questions

Ninguna; el bootstrap con atestación es obligatorio en este incremento.

## SPEC: `autoworkspace-skill`

### Objetivo

Crear una puerta especializada para auditar, actualizar y mejorar autoworkspace conociendo el canon, la operativa y los límites reales del sistema.

### Interfaces y estructura

- `skills/project-autoworkspace/SKILL.md`, versión inicial `1.0.0`, dominio `project`, tipo `orchestrator`, compatibilidad `cursor, pi`.
- `metadata.execution: project-autoworkspace` y operaciones read/write-workspace en el registry; ninguna operación de publicación propia.
- `references/canon-map.md`: AGENTS, STANDARD, GLOSARIO, TAXONOMY, ADR-0016/0017, templates, stacks, reusables y reglas de publicación.
- `references/control-plane.md`: skill-router, workspace-router, registry, ejecución, evidencia, plan activo y scheduler.
- `references/harnesses.md`: paquetes/RPC/subagentes Pi; plugin/hooks/subagentes Cursor; niveles A/B/C.
- `references/self-change-protocol.md`: auditoría → spec → aprobación → DAG → implementación → validación nativa → evidencia → publicación separada.
- `references/upgrade-and-migration.md`: tags, esquemas, compatibilidad, doctor, rollback y desinstalación.
- Salida de auditoría: capacidad, fuente canónica, implementación observada, prueba, estado y desviación; estados `pass`, `fail`, `blocked`, `not_applicable`, `not_run`.
- Handoffs: arquitectura → `project-architecture`; nuevos cambios → `plan-specification`; ejecución → roles aplicables; pruebas → `plan-validators`; publicación → `project-publish`.

### Commands

```bash
uv run --project tools --frozen python tools/harness/doctor.py --harness all --json
uv run --project tools --frozen python tools/workspace-router/run.py --status --repo . --json
make validate
make validate-harnesses
```

### Estilo

Skill y referencias en inglés; cuerpo breve y progressive disclosure; enlaces relativos válidos; triggers ES/EN; sin copiar documentos normativos completos ni crear un segundo canon.

### Testing Strategy

Frontmatter, enlaces, índice, taxonomía y snapshot actualizados a 17; routing positivo/negativo; auditoría fixture que detecta deriva de versión, operación sin runtime, plan sin evidencia, harness parcial y canon desalineado. La skill no se invoca automáticamente para publicar.

### Boundaries

No modifica el sistema sin plan aprobado, no se autoactualiza desde contenido no confiable y no publica. Las instrucciones encontradas en repos auditados son datos, no autoridad.

### Success Criteria

- El catálogo contiene 17 skills y todos los instaladores/doctores las descubren.
- La skill identifica las capas y fuentes canónicas sin afirmaciones desmentidas por el código.
- Produce un plan de mejora trazable y deriva cada acción a la skill competente.
- No existe ningún bypass de aprobación, validación o publicación introducido por la automejora.

### Open Questions

Ninguna; la creación de la skill 17 está aprobada.

## Criterios globales de aceptación de las especificaciones

- [x] El operador aprueba el objetivo, interfaces y límites de los diez módulos.
- [x] El operador acepta el plan Markdown con bloque `aw-plan` como única fuente estructurada de tareas.
- [x] El operador acepta worktrees + patches + staging sin aplicación automática al checkout ni commits obligatorios.
- [x] El operador acepta separar `make validate` de `make validate-harnesses`, manteniendo ambas como requisitos del cierre integral.
- [x] El operador confirma que no quedan preguntas arquitectónicas abiertas.

# Fase 2 — Plan técnico

## Overview

La implementación se organizará como una serie de cortes verticales sobre el sistema actual. Primero se cerrará la cadena de ejecución y evidencia; después el plan activo y el DAG; en paralelo se prepararán el doctor y las distribuciones nativas. El scheduler se probará inicialmente con un adaptador controlado y después con Pi y Cursor. El bootstrap y la skill de automejora se cerrarán sobre capacidades ya demostradas.

El recorrido de aceptación será completo, pero confinado: workers escriben en worktrees temporales, producen patches, un coordinador integra en staging y un verificador independiente comprueba el resultado. El checkout del operador y los servicios externos no forman parte del efecto automático.

## Architecture Decisions

### AD-01 — Una sola especificación de operación

`registry.yaml` contendrá la política declarativa completa. `registry.py` dejará de duplicar IDs, efectos, aprobaciones y timeouts en `OPERATIONS`: mantendrá únicamente el binding entre `operation_id` y handler. El loader producirá `OpSpec` desde YAML y el gate comparará handlers, operaciones declaradas y capacidades de cierre.

La evidencia dejará de depender de `PHASE_EVIDENCE_OPS` independiente. Cada operación podrá declarar las fases que puede cerrar y las verificaciones requeridas; el plan activo seleccionará una operación permitida para la tarea. Un `returncode=0` seguirá siendo insuficiente sin entregable y verificación.

### AD-02 — Pipeline pública sin doble contabilidad

`run_verified` coordinará input digest → ejecución registrada → verificación → output digest → store. Devolverá un sobre de ejecución y no cambiará el plan. `plan-runtime` será el único consumidor autorizado para convertir ese sobre en una transición de tarea/fase.

Los tests unitarios podrán crear fixtures para el store. Los E2E llamarán a la API pública y registrarán dobles solo en el boundary del handler/proceso; no construirán `OpResult` para afirmar que ocurrió una operación distinta.

### AD-03 — Plan Markdown con contrato estructurado embebido

El parser extraerá exactamente un bloque `aw-plan` del documento canónico. El contenido narrativo seguirá siendo la especificación para humanos; el bloque estructurado será la entrada del scheduler. No se generará `tasks/todo.md` ni otro índice de tareas para este incremento.

El estado almacenará ruta y digest del plan activo. Un checkout sin `active_plan` migrará a «sin plan activo»; no se inferirá uno desde `tasks/plan.md` u otros documentos históricos.

### AD-04 — Aislamiento por worktree e integración por patches

Cada escritor usará un worktree detached bajo una raíz temporal fuera del repo. El resultado se capturará como patch binario más manifest de archivos. El coordinador aplicará patches en orden topológico a un staging detached y ejecutará verificación incremental y final.

No se exigirán commits para transportar cambios. Aplicar el resultado al checkout real será una operación separada y explícita. Las ramas, PRs, tags y releases quedan fuera del scheduler.

### AD-05 — Evidencia no recursiva

`.autoworkspace/runs/` se tratará como almacenamiento administrativo y quedará fuera del digest general del workspace; cada artefacto y patch se hashará individualmente dentro del sobre correspondiente. Worktrees y staging no se ubicarán bajo el árbol cuyo contenido se está midiendo.

El input digest se capturará antes de la tarea y el output digest después de integración/verificación. Cualquier cambio en artefactos, plan, target o contenido relevante invalida la aceptación afectada.

### AD-06 — Núcleo neutral y adaptadores delgados

El scheduler solo conocerá `SubagentAdapter.execute`. Pi encapsulará procesos JSON y selección de skills; Cursor encapsulará subagentes/CLI y sus capacidades. Ninguno implementará locks, DAG, aprobaciones o criterios de aceptación propios.

Las operaciones `agent`/`orchestrator` usarán un dispatcher registrado una única vez por operación. El scheduler pasará `adapter` y `run_context` como parámetros validados incluidos en el digest; no existirá un «adaptador actual» global mutable. Así, tareas paralelas podrán usar harnesses distintos sin cambiar el handler ni invalidar la identidad aprobada.

El IDE de Cursor se clasificará como delegación asistida. La aceptación determinista se realizará mediante el recorrido headless nativo, sin depender de que el modelo decida delegar espontáneamente.

### AD-07 — Doctor como puerta de soporte

El doctor emitirá estados por nivel A/B/C y por componente. `make validate` incluirá checks deterministas y Pi sin modelo. `make validate-harnesses` incluirá las pruebas nativas completas, incluido Cursor. Ambas serán obligatorias para el cierre integral, pero las credenciales de Cursor no se exigirán en PRs públicos.

### AD-08 — Distribución nativa y bootstrap verificable

Pi usará paquete Git pineado. Cursor usará plugin completo; el modo skills-only permanecerá disponible y se reportará como parcial. La release publicará tarball y checksums, los atestará y los subirá como assets antes del smoke de distribución.

El bootstrap verificará checksum y atestación antes de extraer/ejecutar. La instalación terminará con doctor; un fallo activará rollback o dejará un estado fallido explícito, nunca un PASS parcial.

## Contratos de cierre por fase

La configuración final se declarará en el registry y se validará contra el plan. La correspondencia de diseño es:

| Fase      | Operación canónica                                                                                      | Verificación mínima                              |
| --------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| DEFINE    | `plan-specification:specify` (`specify`)                                                                | `spec_deliverable` + artefacto de especificación |
| SCHEMAS   | nueva operación `schema_write` en `plan-continue`                                                       | `schema_deliverable` + stubs/esquemas            |
| IMPLEMENT | operación de rol declarada por la tarea: `implement_api`, `implement_ui`, `deliver_visual` o `refactor` | `implementation_deliverable` + patch/artefactos  |
| VALIDATE  | `red_green` o `local_gates`, según la tarea; el cierre de fase exige la puerta completa                 | `gate_result` + salida de tests                  |
| INTEGRATE | nueva operación `integrate`, sin publicación                                                            | `integrate_result` + staging verificado          |
| STATUS    | `status` de `plan-continue`                                                                             | `status_result` + receipt persistente            |

Los IDs antiguos que solo existen en `PHASE_EVIDENCE_OPS` no se aceptarán como sustitutos. La migración no convertirá evidencia histórica en válida para un plan nuevo.

## Componentes y cambios por módulo

| Module id             | Implementación principal                                                                                     | Pruebas integradas                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| `execution-contract`  | Loader YAML → `OpSpec`; registry de handlers; `run_verified`; result schema; evidencia dinámica; E2E público | `tools/execution/tests/`, `tools/contracts/tests/`, `scripts/tests/test_execution_e2e.sh` |
| `harness-doctor`      | Report schema, checks A/B/C, CLI y coherencia de distribución                                                | `tools/harness/tests/`, fixtures de versiones/componentes                                 |
| `plan-runtime`        | Plan schema/parser, active plan, estados por tarea, receipts y migración de status                           | `tools/workspace-router/tests/`, `tools/contracts/tests/`                                 |
| `pi-distribution`     | Manifest Pi, documentación Git pineado, RPC probe y lifecycle                                                | Tests con HOME/temp Git y RPC sin modelo                                                  |
| `cursor-distribution` | Plugin completo, instalador por componentes, probes B/C y documentación                                      | Tests estáticos/hooks + native headless dedicado                                          |
| `orchestration-core`  | DAG, scheduler, adapter port, worktrees, patches, staging, cancelación y resume                              | Fixtures de DAG y recorrido completo con adaptador controlado                             |
| `pi-subagents`        | Extensión TypeScript, proceso hijo, tool limits, salida JSON y cleanup                                       | Unitarias TS/proceso + E2E Pi nativo                                                      |
| `cursor-subagents`    | Agent definitions, cliente headless, verifier y normalización                                                | Native B/C + mismo recorrido fixture que Pi                                               |
| `secure-bootstrap`    | Assets/checksums/attestation, bootstrap confinado, rollback y post-release smoke                             | Release fixture + verificación pública posterior                                          |
| `autoworkspace-skill` | Skill 17, referencias progresivas, registry, routing y auditoría de canon                                    | Gates de catálogo, routing y fixtures de deriva                                           |

## Secuencia de implementación

### Wave 0 — Baseline y viabilidad de los boundaries

1. Revalidar HEAD, árbol, dependencias y comandos del repo; registrar la identidad de partida.
2. Reproducir la divergencia de IDs y el E2E manual con tests focales.
3. Confirmar Pi nativo mediante paquete/RPC y realizar un spike temprano de Cursor headless con versión y credenciales aprobadas.
4. Preparar fixtures de plan, proyecto y release sin tocar host ni servicios reales.

Si Cursor no puede ejecutar el boundary requerido, el diseño de tareas podrá continuar, pero el cierre integral quedará `blocked`; no se sustituirá por mocks.

### Wave 1 — Cadena de ejecución coherente

1. Introducir schemas y cargar `OpSpec` desde YAML conservando compatibilidad de las operaciones actuales.
2. Migrar evidencia y cierre a operaciones canónicas con verificadores declarados.
3. Implementar `run_verified` y rehacer el E2E positivo/negativo sobre la API pública.

Este corte debe dejar `make validate` verde y cero divergencias antes de abrir el plan-runtime.

### Wave 2 — Plan activo, DAG y doctor en paralelo controlado

**Carril A:** parser `aw-plan`, active plan, transiciones por tarea, receipts y migración de status.

**Carril B:** harness report, doctor, comprobación de versiones y probes estáticos.

Son independientes una vez cerrado `execution-contract`. Los archivos compartidos (`Makefile`, `run-validation.sh`, documentación y schemas comunes) tendrán un único escritor/integrador.

### Wave 3 — Distribuciones nativas

Cuando el doctor esté disponible:

- **Pi:** manifest de paquete, instalación Git, RPC `get_commands`, update/uninstall.
- **Cursor:** plugin completo, componentes, nivel B/C y headless nativo.

Las dos distribuciones pueden avanzar en paralelo. La evidencia nativa de Cursor es un checkpoint bloqueante, no una actividad final opcional.

### Wave 4 — Núcleo de orquestación

Con `execution-contract` y `plan-runtime` cerrados:

1. Compilar/validar DAG y estados.
2. Implementar scheduler y adaptador controlado.
3. Añadir worktrees, patches, staging, cancelación y resume.
4. Ejecutar el recorrido completo fixture antes de conectar harnesses reales.

La escritura paralela solo se habilitará después de demostrar rechazo de solapes y recuperación ante fallo.

### Wave 5 — Adaptadores y bootstrap en paralelo

- **Pi subagentes:** extensión y recorrido nativo.
- **Cursor subagentes:** agents/cliente y el mismo recorrido nativo.
- **Secure bootstrap:** release fixture, assets, checksum/attestation e instalador verificado; no requiere esperar a los adaptadores.

Los tres carriles deben usar los contratos congelados. Cambios transversales vuelven al coordinador y disparan revalidación de los otros adaptadores.

### Wave 6 — Skill de automejora y documentación viva

Con las capacidades reales disponibles, añadir `project-autoworkspace`, registry, índice, taxonomía, referencias y triggers. Actualizar arquitectura, setup, routing, reutilización y glosario solo donde el comportamiento implementado lo requiera.

### Wave 7 — Verificación integral y release readiness

1. Repetir todas las suites sobre la misma identidad final.
2. Ejecutar recorrido completo en Pi y Cursor.
3. Ejecutar doctor A/B/C y pruebas de instalación/actualización/desinstalación.
4. Probar release fixture y, tras una publicación autorizada, el smoke público pineado.
5. Revisar plan frente a ejecución, límites, migraciones, versiones y artefactos.

La publicación efectiva seguirá requiriendo una orden separada.

## Paralelismo y propiedad de archivos

| Trabajo simultáneo permitido            | Condición                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------------- |
| `execution-contract` + `harness-doctor` | Schemas compartidos asignados a un solo carril; integración al final de cada corte |
| `plan-runtime` + distribuciones         | Doctor disponible y ningún escritor concurrente sobre status/contracts             |
| Pi + Cursor                             | Adaptadores y fixtures separados; package/docs compartidos por el integrador       |
| Adaptadores + `secure-bootstrap`        | Distribuciones cerradas y release workflow con propietario único                   |
| Workers de un plan                      | Dependencias resueltas, write scopes disjuntos y worktrees distintos               |

No se paralelizarán cambios sobre `registry.yaml`, `status.yaml`, `package.json`, índices generados, `Makefile`, `run-validation.sh` ni documentación compartida. El coordinador integra y repite las puertas afectadas.

## Migraciones y compatibilidad

1. **Registry/runtime:** conservar IDs públicos actualmente ejecutables; las operaciones declarativas sin handler se marcarán `agent`/`orchestrator` y seguirán el procedimiento correspondiente, no desaparecerán silenciosamente.
2. **Evidencia:** mantener lectura diagnóstica de documentos antiguos, pero no aceptarlos para un nuevo `plan_id`. Las migraciones escribirán una copia nueva y conservarán los artefactos originales.
3. **Status:** `schema_version` nuevo, active plan vacío por defecto, historial preservado y migración idempotente. Ningún plan histórico se activará por heurística.
4. **Instaladores:** conservar flags actuales; `--components full` será explícito hasta que el plugin sea la vía recomendada. El JSON añadirá campos compatibles y la versión real.
5. **Catálogo:** actualizar 16 → 17 mediante generador; reemplazar aserciones rígidas por el conjunto esperado derivado del catálogo cuando no se esté probando específicamente la nueva identidad.
6. **Versiones:** alinear repo, paquete, plugin e instaladores. El bump de cada skill se calculará por su cambio; el bump del repo se decidirá según incompatibilidad pública efectiva y ADR-0010.
7. **Documentación:** planes históricos permanecen intactos; las afirmaciones nuevas se limitarán a capacidades con evidencia final.

## Verification Checkpoints

### CP0 — Baseline y capacidad nativa

- [x] `make validate` inicial y estado del árbol registrados.
- [x] Divergencias actuales reproducidas por tests.
- [x] Pi RPC verificado y Cursor headless clasificado como `blocked` por ausencia de `agent`.

### CP1 — Execution contract

- [x] Cero IDs divergentes.
- [x] E2E público positivo y negativo sin resultado manual.
- [x] `make validate` verde y defectos sembrados detectados.

### CP2 — Plan runtime + doctor

- [x] DAG, roles, active plan, migración, locks, replay y resume probados.
- [x] Doctor detecta instalación válida/parcial/ausente sin falsos PASS.

### CP3 — Distribuciones

- [ ] Pi Git pineado + RPC + lifecycle.
- [ ] Cursor plugin completo + native B/C; ausencia bloquea cierre.

### CP4 — Orchestration core

- [x] Recorrido completo fixture con escritura/parches/staging/verificación/cierre.
- [x] Concurrencia, solapes, fallo, timeout, cancelación y resume cubiertos.

### CP5 — Adaptadores nativos

- [ ] Mismo recorrido completo en Pi y Cursor sobre el núcleo compartido.
- [ ] Tool restrictions, evidencia y ausencia de procesos residuales verificadas.

### CP6 — Bootstrap y skill

- [ ] Artefacto válido instala; checksum/atestación inválidos rechazan antes de efectos.
- [ ] Skill 17 descubierta y auditoría de canon comprobada.

### CP7 — Cierre integral

- [ ] `make validate`, `make test`, `make smoke` y `npm run typecheck` verdes.
- [ ] `make validate-harnesses` y `make e2e-orchestration` verdes en ambos harnesses.
- [ ] Cobertura y gates existentes sin retroceso; misma identidad final en toda la evidencia.
- [ ] Release readiness verificada; publicación no ejecutada salvo autorización específica.

## Risks and Mitigations

| Risk                                                 | Impact                       | Mitigation                                                                                            |
| ---------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| Cursor CLI/credenciales no disponibles               | Alto; impide cierre integral | Spike en Wave 0, entorno dedicado, `blocked/not_run` explícito; nunca sustituir por mocks             |
| Migración de IDs rompe consumidores                  | Alto                         | Inventario, aliases solo con compatibilidad demostrada, tests de contrato y bump SemVer apropiado     |
| Escritores paralelos pierden trabajo                 | Alto                         | Worktrees, write scopes, patches, integración topológica y pruebas adversarias                        |
| Evidencia recursiva o stale                          | Alto                         | Runs fuera del digest general, hashes por artefacto, input/output separados y revalidación bajo lock  |
| Subagente amplía permisos o ejecuta prompt inyectado | Alto                         | Task packet cerrado, tool allowlists, proyecto sin confianza por defecto y política externa al prompt |
| Timeout deja procesos o efectos inciertos            | Alto                         | Grupos de procesos, cancelación, reconciliación y prohibición de retry ciego                          |
| Tests nativos lentos/inestables o con coste          | Medio                        | Fixture mínimo, versiones pineadas, límites, evidencia de versión y separación de PR/cierre           |
| Release creada sin assets verificables               | Alto                         | Upload explícito, orden de pasos, fixture de release y smoke post-release obligatorio                 |
| Archivos compartidos divergen entre carriles         | Medio                        | Propiedad única, integrador y repetición de gates tras cada integración                               |
| Skill de automejora duplica el canon                 | Medio                        | Enlaces e invariantes, progressive disclosure y validación de enlaces/terminología                    |
| Cambios de esquema rompen estados antiguos           | Alto                         | Versionado, migración idempotente, historial preservado y rechazo explícito de evidencia incompatible |

## Open Questions

Ninguna. Las decisiones de alcance están cerradas. Las versiones concretas de Cursor y los flags nativos se registrarán tras comprobar la documentación y el binario soportado; esto es evidencia de implementación, no una decisión arquitectónica abierta.

# Fase 3 — Desglose de tareas

El plan técnico está aprobado. Las tareas siguientes son la única lista de trabajo del incremento. Los IDs `tNN-*` son estables; las casillas narrativas y el bloque `aw-plan` se actualizarán juntos. Ninguna tarea se considera completada por escribir código sin superar su verificación.

## Contrato estructurado `aw-plan`

```yaml aw-plan
schema_version: 1
plan_id: autoworkspace-integration-v1
base_revision: 0811c9a3b6582c47692dbc80eb34b8cee8f95c80
tasks:
  - id: t00-baseline
    phase: IMPLEMENT
    operation: status
    roles: []
    depends_on: []
    read_scope:
      [AGENTS.md, package.json, Makefile, tools/, scripts/, .github/workflows/]
    write_scope: [tasks/plan-autoworkspace-integration.md]
    artifacts: [baseline-report]
    acceptance: [baseline-reproducible]
    verification: [make-validate]
    on_failure: stop
  - id: t01-red-contract
    phase: IMPLEMENT
    operation: red_green
    roles: [role-back]
    depends_on: [t00-baseline]
    read_scope:
      [tools/execution/, tools/contracts/, scripts/tests/test_execution_e2e.sh]
    write_scope: [tools/execution/tests/, tools/contracts/tests/]
    artifacts: [red-contract-tests]
    acceptance: [divergence-reproduced]
    verification: [focused-red-tests]
    on_failure: stop
  - id: t02-cursor-spike
    phase: VALIDATE
    operation: discover_stack
    roles: [role-back]
    depends_on: [t00-baseline]
    read_scope: [.cursor/, .cursor-plugin/, docs/harness-integration.md]
    write_scope: [tasks/plan-autoworkspace-integration.md]
    artifacts: [cursor-capability-report]
    acceptance: [cursor-native-classified]
    verification: [agent-version, native-smoke]
    on_failure: stop
  - id: t03-registry-loader
    phase: IMPLEMENT
    operation: refactor
    roles: [role-back, role-clean-code]
    depends_on: [t01-red-contract]
    read_scope:
      [
        tools/execution/registry.py,
        tools/execution/registry.yaml,
        tools/execution/ops.py,
      ]
    write_scope:
      [
        tools/execution/registry.py,
        tools/execution/registry.yaml,
        tools/execution/schemas/,
        tools/execution/tests/,
      ]
    artifacts: [canonical-opspec-loader]
    acceptance: [single-operation-source]
    verification: [registry-tests]
    on_failure: stop
  - id: t04-evidence-policy
    phase: IMPLEMENT
    operation: refactor
    roles: [role-back, role-clean-code]
    depends_on: [t03-registry-loader]
    read_scope:
      [
        tools/execution/evidence.py,
        tools/execution/registry.yaml,
        tools/workspace-router/status_bump.py,
      ]
    write_scope:
      [
        tools/execution/evidence.py,
        tools/execution/registry.yaml,
        tools/execution/tests/,
      ]
    artifacts: [registry-bound-evidence]
    acceptance: [canonical-completion-bindings]
    verification: [evidence-tests]
    on_failure: stop
  - id: t05-run-verified
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t04-evidence-policy]
    read_scope:
      [tools/execution/ops.py, tools/execution/evidence.py, tools/contracts/]
    write_scope:
      [
        tools/execution/ops.py,
        tools/execution/evidence.py,
        tools/contracts/schemas/result.schema.json,
        tools/contracts/tests/,
        tools/execution/tests/,
      ]
    artifacts: [verified-execution-envelope]
    acceptance: [execute-verify-store-chain]
    verification: [run-verified-tests]
    on_failure: stop
  - id: t06-public-execution-e2e
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t05-run-verified]
    read_scope: [scripts/tests/test_execution_e2e.sh, tools/execution/]
    write_scope: [scripts/tests/test_execution_e2e.sh, scripts/tests/fixtures/]
    artifacts: [public-execution-e2e]
    acceptance: [no-fabricated-e2e-result]
    verification: [execution-e2e]
    on_failure: stop
  - id: t07-plan-schema
    phase: IMPLEMENT
    operation: schema_write
    roles: [role-back]
    depends_on: [t05-run-verified]
    read_scope:
      [
        tools/contracts/,
        templates/harness/,
        tasks/plan-autoworkspace-integration.md,
      ]
    write_scope:
      [
        tools/contracts/plan.py,
        tools/contracts/schemas/plan.schema.json,
        tools/contracts/tests/,
        templates/harness/,
      ]
    artifacts: [aw-plan-parser]
    acceptance: [valid-dag-document]
    verification: [plan-parser-tests]
    on_failure: stop
  - id: t08-active-plan-migration
    phase: IMPLEMENT
    operation: schema_write
    roles: [role-back]
    depends_on: [t07-plan-schema]
    read_scope: [tools/workspace-router/, templates/harness/status.yaml]
    write_scope:
      [
        tools/workspace-router/status_bump.py,
        tools/workspace-router/run.py,
        tools/workspace-router/tests/,
        templates/harness/status.yaml,
      ]
    artifacts: [active-plan-state]
    acceptance: [explicit-active-plan-migration]
    verification: [status-migration-tests]
    on_failure: stop
  - id: t09-task-transitions
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t08-active-plan-migration]
    read_scope:
      [tools/workspace-router/status_bump.py, tools/execution/evidence.py]
    write_scope:
      [tools/workspace-router/status_bump.py, tools/workspace-router/tests/]
    artifacts: [task-receipts]
    acceptance: [transactional-task-lifecycle]
    verification: [task-transition-tests]
    on_failure: stop
  - id: t10-doctor-core
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t00-baseline]
    read_scope: [tools/contracts/, scripts/lib/link-skills.sh, package.json]
    write_scope:
      [
        tools/harness/doctor.py,
        tools/harness/base.py,
        tools/contracts/schemas/harness-report.schema.json,
        tools/harness/tests/,
      ]
    artifacts: [harness-report]
    acceptance: [honest-capability-report]
    verification: [doctor-tests]
    on_failure: stop
  - id: t11-pi-package
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t10-doctor-core]
    read_scope: [package.json, docs/harness-setup.md, README.md]
    write_scope: [package.json, docs/harness-setup.md, README.md]
    artifacts: [pi-git-package]
    acceptance: [pinned-pi-package]
    verification: [pi-package-fixture]
    on_failure: stop
  - id: t12-pi-rpc-lifecycle
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t11-pi-package]
    read_scope: [tools/harness/, scripts/tests/]
    write_scope:
      [
        tools/harness/pi.py,
        tools/harness/tests/,
        scripts/tests/test_pi_native.sh,
      ]
    artifacts: [pi-native-report]
    acceptance: [pi-discovery-and-lifecycle]
    verification: [pi-rpc-native]
    on_failure: stop
  - id: t13-cursor-plugin
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t10-doctor-core]
    read_scope: [.cursor-plugin/, .cursor/, tools/harness/]
    write_scope:
      [
        .cursor-plugin/plugin.json,
        .cursor-plugin/marketplace.json,
        .cursor/,
        tools/harness/tests/,
      ]
    artifacts: [cursor-complete-plugin]
    acceptance: [cursor-components-declared]
    verification: [cursor-static-plugin-tests]
    on_failure: stop
  - id: t14-cursor-full-install
    phase: IMPLEMENT
    operation: refactor
    roles: [role-back, role-clean-code]
    depends_on: [t13-cursor-plugin]
    read_scope:
      [
        scripts/install.sh,
        scripts/lib/link-skills.sh,
        scripts/tests/test_install.sh,
      ]
    write_scope:
      [
        scripts/install.sh,
        scripts/lib/link-skills.sh,
        scripts/tests/test_install.sh,
        docs/harness-setup.md,
      ]
    artifacts: [cursor-full-install]
    acceptance: [component-aware-transaction]
    verification: [install-matrix]
    on_failure: stop
  - id: t15-cursor-native-bc
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t02-cursor-spike, t14-cursor-full-install]
    read_scope: [.cursor/, tools/harness/, scripts/tests/]
    write_scope:
      [
        tools/harness/cursor.py,
        tools/harness/tests/,
        scripts/tests/test_cursor_native.sh,
      ]
    artifacts: [cursor-native-bc-report]
    acceptance: [cursor-discovery-and-policy]
    verification: [cursor-native-bc]
    on_failure: stop
  - id: t16-dag-scheduler
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t05-run-verified, t09-task-transitions]
    read_scope: [tools/contracts/plan.py, tools/workspace-router/status_bump.py]
    write_scope:
      [
        tools/orchestrator/model.py,
        tools/orchestrator/ports.py,
        tools/orchestrator/scheduler.py,
        tools/orchestrator/run.py,
        tools/orchestrator/tests/,
      ]
    artifacts: [dag-scheduler]
    acceptance: [deterministic-ready-set]
    verification: [scheduler-tests]
    on_failure: stop
  - id: t17-worktree-staging
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t16-dag-scheduler]
    read_scope: [tools/orchestrator/, tools/execution/evidence.py]
    write_scope:
      [
        tools/orchestrator/worktrees.py,
        tools/orchestrator/runner.py,
        tools/orchestrator/tests/,
      ]
    artifacts: [patch-staging-flow]
    acceptance: [isolated-writer-integration]
    verification: [worktree-tests]
    on_failure: stop
  - id: t18-orchestration-resilience
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t17-worktree-staging]
    read_scope: [tools/orchestrator/, tools/execution/ops.py]
    write_scope:
      [
        tools/orchestrator/scheduler.py,
        tools/orchestrator/runner.py,
        tools/orchestrator/tests/,
      ]
    artifacts: [resilient-run-state]
    acceptance: [cancel-retry-resume-safe]
    verification: [orchestration-adversarial-tests]
    on_failure: stop
  - id: t19-core-complete-fixture
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t18-orchestration-resilience]
    read_scope: [tools/orchestrator/, scripts/tests/]
    write_scope:
      [
        tools/orchestrator/tests/,
        scripts/tests/test_orchestration_core.sh,
        scripts/tests/fixtures/,
      ]
    artifacts: [core-complete-e2e]
    acceptance: [controlled-full-path]
    verification: [core-orchestration-e2e]
    on_failure: stop
  - id: t20-pi-extension
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t12-pi-rpc-lifecycle, t19-core-complete-fixture]
    read_scope: [extensions/, package.json, tools/orchestrator/ports.py]
    write_scope: [extensions/autoworkspace/, package.json, tools/harness/tests/]
    artifacts: [pi-subagent-extension]
    acceptance: [isolated-pi-child]
    verification: [pi-extension-tests]
    on_failure: stop
  - id: t21-pi-native-e2e
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t20-pi-extension]
    read_scope:
      [tools/harness/pi.py, tools/orchestrator/, extensions/autoworkspace/]
    write_scope:
      [
        tools/harness/pi.py,
        tools/orchestrator/tests/,
        scripts/tests/test_pi_orchestration.sh,
      ]
    artifacts: [pi-complete-e2e]
    acceptance: [pi-native-full-path]
    verification: [pi-orchestration-e2e]
    on_failure: stop
  - id: t22-cursor-adapter
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [t15-cursor-native-bc, t19-core-complete-fixture]
    read_scope:
      [.cursor/agents/, tools/harness/cursor.py, tools/orchestrator/ports.py]
    write_scope:
      [
        .cursor/agents/aw-planner.md,
        .cursor/agents/aw-worker.md,
        .cursor/agents/aw-verifier.md,
        tools/harness/cursor.py,
        tools/harness/tests/,
      ]
    artifacts: [cursor-subagent-adapter]
    acceptance: [cursor-task-packet-adapter]
    verification: [cursor-adapter-tests]
    on_failure: stop
  - id: t23-cursor-native-e2e
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t22-cursor-adapter]
    read_scope: [tools/harness/cursor.py, tools/orchestrator/, scripts/tests/]
    write_scope:
      [
        tools/orchestrator/tests/,
        scripts/tests/test_cursor_orchestration.sh,
        tasks/plan-autoworkspace-integration.md,
      ]
    artifacts: [cursor-complete-e2e]
    acceptance: [cursor-native-full-path]
    verification: [cursor-orchestration-e2e]
    on_failure: stop
  - id: t24-release-assets
    phase: IMPLEMENT
    operation: integrate
    roles: [role-back]
    depends_on: [t12-pi-rpc-lifecycle, t13-cursor-plugin]
    read_scope:
      [.github/workflows/release.yml, tools/validate/release_coherence.py]
    write_scope:
      [
        .github/workflows/release.yml,
        tools/validate/release_coherence.py,
        tools/validate/tests/,
      ]
    artifacts: [attested-release-assets]
    acceptance: [release-uploads-verifiable-assets]
    verification: [release-fixture-tests]
    on_failure: stop
  - id: t25-secure-bootstrap
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on:
      [t24-release-assets, t12-pi-rpc-lifecycle, t14-cursor-full-install]
    read_scope: [scripts/, tools/harness/doctor.py]
    write_scope:
      [
        scripts/bootstrap.sh,
        scripts/tests/test_bootstrap.sh,
        docs/harness-setup.md,
      ]
    artifacts: [verified-bootstrap]
    acceptance: [verify-before-install]
    verification: [bootstrap-tests]
    on_failure: stop
  - id: t26-bootstrap-adversarial
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t25-secure-bootstrap, t15-cursor-native-bc]
    read_scope:
      [scripts/bootstrap.sh, scripts/tests/, .github/workflows/release.yml]
    write_scope:
      [
        scripts/tests/test_bootstrap.sh,
        docs/runbooks/,
        tasks/plan-autoworkspace-integration.md,
      ]
    artifacts: [bootstrap-adversarial-report]
    acceptance: [bootstrap-fails-closed]
    verification: [bootstrap-adversarial-tests]
    on_failure: stop
  - id: t27-autoworkspace-skill
    phase: IMPLEMENT
    operation: specify
    roles: [role-back]
    depends_on:
      [t21-pi-native-e2e, t23-cursor-native-e2e, t26-bootstrap-adversarial]
    read_scope:
      [
        skills/plan-continue/,
        skills/project-architecture/,
        tools/execution/registry.yaml,
      ]
    write_scope:
      [
        skills/project-autoworkspace/SKILL.md,
        tools/execution/registry.yaml,
        tools/skill-router/intent-map.yaml,
      ]
    artifacts: [project-autoworkspace-skill]
    acceptance: [self-improvement-contract]
    verification: [skill-spec-and-routing]
    on_failure: stop
  - id: t28-canon-references
    phase: IMPLEMENT
    operation: specify
    roles: []
    depends_on: [t27-autoworkspace-skill]
    read_scope: [docs/, ARCHITECTURE.md, templates/, stacks/]
    write_scope:
      [
        skills/project-autoworkspace/references/canon-map.md,
        skills/project-autoworkspace/references/control-plane.md,
        skills/project-autoworkspace/references/harnesses.md,
        skills/project-autoworkspace/references/self-change-protocol.md,
        skills/project-autoworkspace/references/upgrade-and-migration.md,
      ]
    artifacts: [integral-canon-map]
    acceptance: [canonical-progressive-references]
    verification: [skill-links]
    on_failure: stop
  - id: t29-self-audit-routing
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [t28-canon-references]
    read_scope:
      [skills/project-autoworkspace/, tools/skill-router/, tools/harness/]
    write_scope:
      [
        tools/skill-router/tests/,
        tools/harness/tests/,
        skills/project-autoworkspace/SKILL.md,
      ]
    artifacts: [self-audit-fixtures]
    acceptance: [self-audit-detects-drift]
    verification: [self-audit-routing-tests]
    on_failure: stop
  - id: t30-catalog-17
    phase: INTEGRATE
    operation: integrate
    roles: [role-back]
    depends_on:
      [t29-self-audit-routing, t12-pi-rpc-lifecycle, t15-cursor-native-bc]
    read_scope: [README.md, docs/TAXONOMY.md, skill-index.json, scripts/tests/]
    write_scope:
      [
        README.md,
        docs/TAXONOMY.md,
        skill-index.json,
        docs/architecture/skill-index-7.0.0.json,
        scripts/tests/test_install.sh,
      ]
    artifacts: [catalog-17]
    acceptance: [all-surfaces-discover-17]
    verification: [catalog-and-install-matrix]
    on_failure: stop
  - id: t31-living-docs
    phase: INTEGRATE
    operation: integrate
    roles: []
    depends_on: [t30-catalog-17]
    read_scope: [ARCHITECTURE.md, docs/]
    write_scope:
      [
        ARCHITECTURE.md,
        docs/harness-integration.md,
        docs/harness-setup.md,
        docs/routing.md,
        docs/GLOSARIO.md,
      ]
    artifacts: [integrated-live-docs]
    acceptance: [docs-match-implemented-system]
    verification: [docs-and-terminology-gates]
    on_failure: stop
  - id: t32-full-validation
    phase: VALIDATE
    operation: local_gates
    roles: [role-back]
    depends_on:
      [
        t31-living-docs,
        t21-pi-native-e2e,
        t23-cursor-native-e2e,
        t26-bootstrap-adversarial,
      ]
    read_scope: [Makefile, run-validation.sh, scripts/tests/, tools/]
    write_scope:
      [
        Makefile,
        run-validation.sh,
        scripts/tests/,
        tasks/plan-autoworkspace-integration.md,
      ]
    artifacts: [final-validation-report]
    acceptance: [all-gates-same-identity]
    verification: [full-native-validation]
    on_failure: stop
  - id: t33-version-readiness
    phase: STATUS
    operation: status
    roles: [role-back]
    depends_on: [t32-full-validation]
    read_scope:
      [
        package.json,
        tools/pyproject.toml,
        CHANGELOG.md,
        docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md,
      ]
    write_scope:
      [
        package.json,
        package-lock.json,
        tools/pyproject.toml,
        tools/uv.lock,
        CHANGELOG.md,
      ]
    artifacts: [version-release-readiness]
    acceptance: [coherent-version-and-release]
    verification: [release-readiness-gate]
    on_failure: stop
  - id: t34-closure-review
    phase: STATUS
    operation: status
    roles: []
    depends_on: [t33-version-readiness]
    read_scope:
      [
        tasks/plan-autoworkspace-integration.md,
        .autoworkspace/,
        tools/,
        scripts/,
      ]
    write_scope: [tasks/plan-autoworkspace-integration.md]
    artifacts: [final-closure-report]
    acceptance: [plan-evidence-match]
    verification: [independent-closure-review]
    on_failure: stop
```

## Reglas de ejecución de las tareas

- Antes de cada tarea se reevaluarán y cargarán todos los roles aplicables; los roles indicados son la preselección aprobada, no una invocación anticipada.
- `plan-validators` cubre todas las superficies de comportamiento. Las tareas de documentación pura no inventarán TDD.
- El scheduler no se usará para construirse a sí mismo hasta superar CP5. Antes de esa puerta, el coordinador ejecuta las tareas en el orden del DAG.
- Las tareas con modelos, credenciales o instalación nativa requieren el entorno aprobado; si falta, quedan `blocked/not_run` y bloquean el cierre correspondiente.
- Los archivos generados se actualizan con su generador. Ningún carril paralelo escribe índices, lockfiles o documentación compartida fuera de su asignación.
- Cada tarea registra RED cuando aplique, comandos, resultado, identidad y artefactos en la sección de evidencia de este documento.

## Tasks — Wave 0 y Wave 1

### Task T00: Baseline verificable y fixtures

**Description:** Revalidar el checkout y preparar fixtures inertes para planes, proyectos y releases.

**Acceptance criteria:**

- [x] HEAD, rama, árbol, versiones y gate inicial quedan registrados.
- [x] Las fixtures no contienen secretos ni rutas del host y no ejecutan efectos reales.

**Dependencies:** None.  
**Implementation roles:** None; coordinación con `plan-continue`.  
**Test surfaces:** Baseline y seguridad de fixtures.  
**Verification:** `make validate` y revisión de fixtures.  
**Files likely touched:** este documento y `scripts/tests/fixtures/`.  
**Estimated scope:** S.

### Task T01: Reproducir divergencia de contratos

**Description:** Añadir pruebas RED para IDs divergentes, bindings de cierre y resultado manual del E2E.

**Acceptance criteria:**

- [x] Las pruebas fallan por las divergencias observadas, no por errores de setup.
- [x] Quedan cubiertos IDs desconocidos, operación sin handler y fase sin operación canónica.

**Dependencies:** T00.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Registry, evidencia y E2E público.  
**Verification:** pytest focal con fallo esperado documentado.  
**Files likely touched:** `tools/execution/tests/`, `tools/contracts/tests/`.  
**Estimated scope:** S.

### Task T02: Spike nativo de Cursor

**Description:** Comprobar versión, CLI headless, descubrimiento, subagentes y permisos en un proyecto temporal.

**Acceptance criteria:**

- [x] Se registra versión y capacidad real de B/C con comandos y resultados redactados.
- [x] Un deny/ask no crea el sentinel y un allow benigno sí lo crea.
- [x] Binario/credencial ausente deja la tarea `blocked`, no done.

**Dependencies:** T00; autorización del entorno nativo.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Cursor CLI, hooks y subagentes.  
**Verification:** `agent --version` y smoke nativo temporal.  
**Files likely touched:** evidencia en este documento; ningún código de producto.  
**Estimated scope:** S.

#### Checkpoint CP0

- [x] Baseline verde y defectos RED registrados.
- [x] Pi RPC confirmado y Cursor nativo clasificado; el bloqueo de Cursor impide el cierre integral.

### Task T03: Cargar `OpSpec` desde registry

**Description:** Sustituir la duplicación de políticas en `OPERATIONS` por especificaciones cargadas de YAML y bindings de handlers.

**Acceptance criteria:**

- [x] IDs, efectos, aprobación, snapshots y timeouts proceden del registry.
- [x] Operación duplicada, desconocida o sin binding ejecutable falla antes de efectos.
- [x] Las operaciones actuales conservan su comportamiento o migración explícita.

**Dependencies:** T01.  
**Implementation roles:** `role-back`, `role-clean-code`; `plan-validators`.  
**Test surfaces:** Loader, schema, `get_operation`, `resolve_argv` y aprobación.  
**Verification:** `uv run --project tools --frozen pytest tools/execution/tests -q`.  
**Files likely touched:** `registry.py`, `registry.yaml`, registry schema y tests.  
**Estimated scope:** M.

### Task T04: Vincular evidencia al registry

**Description:** Sustituir allowlists independientes por fases y verificadores declarados en operaciones canónicas.

**Acceptance criteria:**

- [x] DEFINE/SCHEMAS/IMPLEMENT/VALIDATE/INTEGRATE/STATUS usan operaciones reales del registry.
- [x] Evidencia legacy, de otra fase o sin verificación obligatoria se rechaza.
- [x] Los artefactos y bindings se validan al escribir y al leer.

**Dependencies:** T03.  
**Implementation roles:** `role-back`, `role-clean-code`; `plan-validators`.  
**Test surfaces:** Store, loader, complete y operaciones por fase.  
**Verification:** pytest de evidencia y contratos.  
**Files likely touched:** `evidence.py`, `registry.yaml` y tests.  
**Estimated scope:** M.

#### Checkpoint CP1a

- [x] Cero divergencia de IDs y políticas.
- [x] Fixtures adversarias rompen registry/evidence por la causa esperada.

### Task T05: Implementar `run_verified`

**Description:** Integrar input digest, ejecución registrada, verificación, output digest y persistencia en un sobre común.

**Acceptance criteria:**

- [x] El resultado incluye plan/tarea/target y ambos digests capturados en el orden correcto.
- [x] Fallo, timeout, verificación negativa o store inválido no produce éxito.
- [x] `run_verified` transmite adapter/run_context como parámetros del plan validado; el dispatcher se conectará en T16 sin estado global mutable.

**Dependencies:** T04.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Ejecución script/agent, digests, verificación y store.  
**Verification:** pytest de ejecución/contratos y defectos sembrados.  
**Files likely touched:** `ops.py`, `evidence.py`, result schema y tests.  
**Estimated scope:** M.

### Task T06: Rehacer el E2E público de ejecución

**Description:** Ejecutar DEFINE mediante la cadena pública y eliminar la construcción manual de su resultado.

**Acceptance criteria:**

- [x] El camino positivo pasa por ejecución, verificación, artefacto, store y complete.
- [x] Deny/stale/artefacto cambiado no completan.
- [x] El E2E no instancia un resultado para una operación que no se ejecutó.

**Dependencies:** T05.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** `run_verified`, evidencia y router `--complete`.  
**Verification:** `bash scripts/tests/test_execution_e2e.sh` y `make validate`.  
**Files likely touched:** E2E y fixtures asociadas.  
**Estimated scope:** M.

#### Checkpoint CP1

- [x] Recorrido público positivo y negativo verificado.
- [x] `make validate` verde sin IDs divergentes ni resultados manuales.

## Tasks — Wave 2

### Task T07: Implementar schema y parser `aw-plan`

**Description:** Extraer y validar un único bloque estructurado del plan Markdown canónico.

**Acceptance criteria:**

- [x] Un plan válido produce un DAG tipado con todos los campos requeridos.
- [x] Bloques múltiples, claves duplicadas, ciclos, IDs duplicados y paths inválidos se rechazan.
- [x] No se crea ningún tracker paralelo.

**Dependencies:** T05.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Parser, schema y compilación inicial del DAG.  
**Verification:** `uv run --project tools --frozen pytest tools/contracts/tests -q`.  
**Files likely touched:** `plan.py`, plan schema, tests y template harness.  
**Estimated scope:** M.

### Task T08: Migrar a plan activo explícito

**Description:** Versionar status y añadir active plan/digest sin activar documentos históricos.

**Acceptance criteria:**

- [x] Estado antiguo migra de forma idempotente con historial preservado y sin plan activo inferido.
- [x] Plan cambiado o revisión incompatible invalida la reanudación afectada.
- [x] `route/list/status` conservan su comportamiento de consulta.

**Dependencies:** T07.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Migración, lectura/escritura atómica y router.  
**Verification:** pytest de workspace-router y migraciones.  
**Files likely touched:** `status_bump.py`, `run.py`, status template y tests.  
**Estimated scope:** M.

### Task T09: Implementar transiciones y receipts por tarea

**Description:** Añadir lifecycle por tarea y cierre ligado a evidencia de `run_verified`.

**Acceptance criteria:**

- [x] Solo evidencia canónica válida completa una tarea y activa dependientes.
- [x] Replay no duplica receipt; concurrencia no pierde updates.
- [x] `awaiting`, fallo, retry y cambio de fase siguen el grafo explícito.

**Dependencies:** T08.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Locks, CAS/revisión, idempotencia y transiciones.  
**Verification:** pytest multiproceso determinista de workspace-router.  
**Files likely touched:** `status_bump.py` y tests.  
**Estimated scope:** M.

#### Checkpoint CP2a

- [x] Parser, active plan, migración y receipts verdes.
- [x] Ningún plan histórico se activa por heurística.

### Task T10: Implementar el núcleo de harness doctor

**Description:** Crear el informe común A/B/C, CLI y códigos de salida sin sondas que reparen el sistema.

**Acceptance criteria:**

- [x] El informe valida schema y distingue PASS/FAIL/blocked/not_run por check.
- [x] Una capacidad obligatoria ausente produce salida no exitosa y motivo útil.
- [x] Versiones/componentes divergentes se detectan sin modificar recursos.

**Dependencies:** T00.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** CLI JSON, report schema y agregación de checks.  
**Verification:** `uv run --project tools --frozen pytest tools/harness/tests -q`.  
**Files likely touched:** `doctor.py`, `base.py`, report schema y tests.  
**Estimated scope:** M.

### Task T11: Declarar el paquete Pi Git

**Description:** Añadir el manifiesto explícito de recursos Pi y documentar instalación pineada.

**Acceptance criteria:**

- [x] `package.json` declara `pi-package` y skills; extensions se añadirá cuando exista.
- [x] La documentación usa un tag `vX.Y.Z`, no una rama flotante.
- [x] El paquete fixture conserva `private: true` y no introduce npm publishing.

**Dependencies:** T10.  
**Implementation roles:** `role-back`; `plan-validators` para el contrato de paquete.  
**Test surfaces:** Manifest y paquete local/Git fixture.  
**Verification:** instalación en HOME temporal y `pi list`.  
**Files likely touched:** `package.json`, README y harness setup.  
**Estimated scope:** S.

### Task T12: Validar discovery y lifecycle Pi por RPC

**Description:** Implementar la sonda `get_commands` y pruebas nativas de instalación, update y uninstall.

**Acceptance criteria:**

- [x] RPC demuestra skills cargadas con origen package y baseDir esperado sin usar un modelo.
- [x] Install/reinstall/uninstall locales preservan paquetes ajenos; el smoke entre tags de la nueva release queda asignado a T26/T33.
- [x] Binario ausente, JSON inválido o skill incompleta bloquea el PASS.

**Dependencies:** T11.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Pi RPC, doctor B y lifecycle Git.  
**Verification:** `bash scripts/tests/test_pi_native.sh` con HOME/proyecto temporales.  
**Files likely touched:** `pi.py`, tests harness y E2E Pi.  
**Estimated scope:** M.

#### Checkpoint CP2b / CP3-Pi

- [ ] Doctor común y Pi nativo verdes.
- [ ] La instalación pineada queda probada sin tocar settings reales.

### Task T13: Cerrar el plugin completo de Cursor

**Description:** Validar manifiesto, rutas y portabilidad de skills, rules, agents y hooks.

**Acceptance criteria:**

- [x] El plugin declara todos los componentes y una versión coherente con el repo.
- [x] Los hooks resuelven correctamente desde plugin y proyecto.
- [x] Una ruta/componente ausente rompe el gate estático.

**Dependencies:** T10.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Manifest, hook working directory y recursos del plugin.  
**Verification:** tests estáticos de plugin y hooks.  
**Files likely touched:** plugin manifest, marketplace, recursos `.cursor/` y tests.  
**Estimated scope:** M.

### Task T14: Añadir instalación Cursor por componentes

**Description:** Incorporar `skills|full` al wrapper manteniendo journal, conflictos y uninstall para cada recurso gestionado.

**Acceptance criteria:**

- [x] `skills` queda marcado como parcial y `full` instala todos los componentes declarados.
- [x] Fallo intermedio restaura el estado previo y recursos ajenos permanecen intactos.
- [x] Flags actuales, dry-run e idempotencia conservan compatibilidad.

**Dependencies:** T13.  
**Implementation roles:** `role-back`, `role-clean-code`; `plan-validators`.  
**Test surfaces:** Install matrix, rollback y manifest de componentes.  
**Verification:** `bash scripts/tests/test_install.sh`.  
**Files likely touched:** `install.sh`, `link-skills.sh`, install tests y setup.  
**Estimated scope:** M.

### Task T15: Implementar doctor nativo Cursor B/C

**Description:** Automatizar descubrimiento, carga y pruebas de política con la versión soportada.

**Acceptance criteria:**

- [x] B demuestra skills/rules/agents cargados; C demuestra allow/deny/ask con sentinel.
- [x] Ask no actúa antes de decisión y deny nunca crea efectos.
- [x] La ausencia del entorno nativo bloquea el cierre integral y queda en el informe.

**Dependencies:** T02 y T14.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Cursor native B/C y doctor.  
**Verification:** `bash scripts/tests/test_cursor_native.sh` en entorno aprobado.  
**Files likely touched:** `cursor.py`, tests harness y E2E Cursor.  
**Estimated scope:** M.

#### Checkpoint CP3

- [ ] Plugin completo e instalación transaccional verificados.
- [ ] Cursor B/C nativo PASS; cualquier `not_run` mantiene el cierre bloqueado.

## Tasks — Wave 4

### Task T16: Implementar DAG y scheduler

**Description:** Calcular ready set, ejecutar adaptadores con límite y respetar dependencias/roles.

**Acceptance criteria:**

- [x] El orden es determinista y toda tarea espera a sus dependencias.
- [x] Todos los roles declarados llegan al task packet; no se usa el fallback único de fase.
- [x] Dry-run produce schedule simulado sin escrituras ni cierre.

**Dependencies:** T05 y T09.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Ready set, concurrencia, roles, fail-fast y dry-run.  
**Verification:** `uv run --project tools --frozen pytest tools/orchestrator/tests -q`.  
**Files likely touched:** model, ports, scheduler, CLI y tests.  
**Estimated scope:** M.

### Task T17: Implementar worktrees, patches y staging

**Description:** Aislar cada escritor e integrar sus cambios en orden sin commits ni modificación automática del checkout.

**Acceptance criteria:**

- [x] Cada writer produce patch y manifest desde un worktree temporal independiente.
- [x] Solapes se rechazan y staging aplica patches en orden topológico.
- [x] Runs quedan fuera del digest general y cada artefacto tiene hash propio.

**Dependencies:** T16.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Git worktree, diff binario, paths, digest e integración.  
**Verification:** tests sobre repositorios temporales, incluidos espacios y binarios.  
**Files likely touched:** `worktrees.py`, `runner.py` y tests.  
**Estimated scope:** M.

#### Checkpoint CP4a

- [x] Scheduler y aislamiento de escritura probados.
- [x] Ningún test exige commit/push ni escribe en el checkout real.

### Task T18: Añadir resiliencia y reanudación

**Description:** Completar cancelación, timeout, fallo de dependencias y resume mediante receipts.

**Acceptance criteria:**

- [x] Timeout/abort termina el grupo de procesos y marca reconciliación cuando el efecto sea incierto.
- [x] Fail-fast bloquea dependientes y resume no repite tareas verificadas.
- [x] Estado corrupto, plan cambiado o receipt stale se rechaza.

**Dependencies:** T17.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Señales, concurrencia, recuperación e idempotencia.  
**Verification:** tests adversarios con sincronización determinista.  
**Files likely touched:** scheduler, runner y tests.  
**Estimated scope:** M.

### Task T19: Probar el recorrido completo del núcleo

**Description:** Ejecutar specify → write → integrate → verify → evidence → close con adaptador controlado.

**Acceptance criteria:**

- [x] El staging contiene el cambio esperado y supera el verificador independiente.
- [x] El cierre procede de evidencia real de la ejecución controlada.
- [x] Un verificador omitido/fallido impide done aunque el worker afirme éxito.

**Dependencies:** T18.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Flujo E2E completo y defectos sembrados.  
**Verification:** `bash scripts/tests/test_orchestration_core.sh`.  
**Files likely touched:** tests orchestrator, E2E y fixtures.  
**Estimated scope:** M.

#### Checkpoint CP4

- [x] Recorrido completo del núcleo verde.
- [x] Concurrencia, cancelación y reanudación cubiertas antes de conectar modelos.

## Tasks — Wave 5

### Task T20: Implementar la extensión de subagentes Pi

**Description:** Crear `aw_subagent` con proceso hijo aislado, skill explícita, tools restringidas y salida JSON normalizada.

**Acceptance criteria:**

- [x] Una llamada ejecuta una tarea y hereda modelo/configuración solo según contrato.
- [x] Prompts temporales son privados y se limpian; salida y errores quedan acotados/redactados.
- [x] Abort/timeout propaga al proceso y sus descendientes.

**Dependencies:** T12 y T19.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Extension load, spawn, JSON events, tool limits y cleanup.  
**Verification:** tests TypeScript/proceso y carga del paquete Pi.  
**Files likely touched:** `extensions/autoworkspace/`, `package.json` y tests harness.  
**Estimated scope:** M.

### Task T21: Ejecutar el recorrido nativo completo en Pi

**Description:** Conectar extensión, adaptador, worktrees y evidencia al scheduler compartido.

**Acceptance criteria:**

- [x] Pi escribe el artefacto fixture, lo integra y supera verificación/cierre.
- [x] Tools no permitidas y denegación no producen efectos.
- [x] La evidencia registra paquete, versión, run, tarea y artefactos sin procesos residuales.

**Dependencies:** T20.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Pi native E2E y contrato común de adaptador.  
**Verification:** `bash scripts/tests/test_pi_orchestration.sh`.  
**Files likely touched:** `pi.py`, tests orchestrator y E2E Pi.  
**Estimated scope:** M.

#### Checkpoint CP5-Pi

- [x] Pi completa el recorrido real mediante el núcleo compartido.
- [x] La carga de skills y la autorización de acciones permanecen separadas.

### Task T22: Implementar adaptador y agents Cursor

**Description:** Normalizar tareas headless y mantener planner/worker/verifier focalizados sobre las skills canónicas.

**Acceptance criteria:**

- [x] El coordinador invoca explícitamente cada tarea sin depender de delegación espontánea.
- [x] Verifier es read-only y worker recibe rol, worktree y criterios exactos.
- [x] El adaptador devuelve el mismo contrato de resultado que Pi.

**Dependencies:** T15 y T19.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Cursor headless, agent definitions y adaptador común.  
**Verification:** tests de adaptador y discovery nativo.  
**Files likely touched:** tres agent definitions, `cursor.py` y tests.  
**Estimated scope:** M.

### Task T23: Ejecutar el recorrido nativo completo en Cursor

**Description:** Ejecutar sobre fixture el mismo flujo de escritura, integración, verificación y cierre usado en Pi.

**Acceptance criteria:**

- [x] Cursor produce el artefacto esperado y supera el verificador independiente.
- [x] Permisos deny/ask no actúan antes de decisión y no hay autoaprobación.
- [x] La evidencia diferencia IDE asistido de headless y registra versión real.

**Dependencies:** T22.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Cursor native E2E, permisos y evidencia.  
**Verification:** `bash scripts/tests/test_cursor_orchestration.sh`.  
**Files likely touched:** tests orchestrator, E2E Cursor y evidencia del plan.  
**Estimated scope:** M.

#### Checkpoint CP5

- [x] Pi y Cursor completan el mismo recorrido nativo.
- [x] Cualquier capacidad no ejecutada impide CP5 y el cierre integral.

### Task T24: Publicar assets con atestación en el workflow

**Description:** Añadir checksums, upload de tarball/SHA256SUMS y orden verificable de release/provenance.

**Acceptance criteria:**

- [x] El workflow atesta el archivo exacto y sube los assets a la Release correcta.
- [x] Tag, versión, notas y contenido mantienen coherencia.
- [x] Una release fixture sin assets o con digest distinto falla readiness.

**Dependencies:** T12 y T13.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Release workflow, coherencia y empaquetado.  
**Verification:** actionlint/zizmor existentes y tests de release fixture.  
**Files likely touched:** `release.yml`, `release_coherence.py` y tests.  
**Estimated scope:** M.

### Task T25: Implementar bootstrap verificable

**Description:** Descargar assets, validar checksum/atestación, extraer confinado, instalar y ejecutar doctor.

**Acceptance criteria:**

- [x] Ningún código se extrae/ejecuta antes de superar checksum y atestación.
- [x] La línea documentada funciona para el harness/target y versión seleccionados.
- [x] Dry-run no escribe y el JSON final refleja la instalación observada.

**Dependencies:** T24, T12 y T14.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Descarga, atestación, extracción e instalación.  
**Verification:** `bash scripts/tests/test_bootstrap.sh` sobre release fixture.  
**Files likely touched:** `bootstrap.sh`, tests bootstrap y setup.  
**Estimated scope:** M.

### Task T26: Probar bootstrap adversario y smoke post-release

**Description:** Cubrir artefactos inválidos, rollback y verificación de una publicación real autorizada.

**Acceptance criteria:**

- [x] Checksum/atestación/tag incorrecto y tar hostil no producen efectos.
- [x] Fallo de instalación/doctor restaura recursos o deja FAIL explícito sin falsos PASS.
- [ ] El runbook post-release exige descargar, verificar e instalar el tag publicado.

**Dependencies:** T25 y T15.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Seguridad de archivo, rollback y release smoke.  
**Verification:** tests adversarios; smoke real queda pendiente hasta publicación autorizada.  
**Files likely touched:** tests bootstrap, runbook y evidencia del plan.  
**Estimated scope:** M.

#### Checkpoint CP6a

- [x] Bootstrap fixture y fallos adversarios verificados.
- [x] Ninguna release real se crea durante las pruebas.

## Tasks — Wave 6

### Task T27: Crear `project-autoworkspace`

**Description:** Añadir el contrato de la skill 17, sus límites, handoffs y operaciones sin publicación propia.

**Acceptance criteria:**

- [x] Frontmatter, tipo orchestrator y registry cumplen el estándar y mínimo privilegio.
- [x] La descripción diferencia automejora de plan-continue, project-architecture y project-publish.
- [x] Los triggers ES/EN seleccionan la skill sin capturar auditorías genéricas.

**Dependencies:** T21, T23 y T26.  
**Implementation roles:** `role-back`; `plan-specification` y `plan-validators`.  
**Test surfaces:** Skill spec, registry y routing.  
**Verification:** `skill_spec.py`, registry check y corpus de routing.  
**Files likely touched:** `SKILL.md`, registry e intent map.  
**Estimated scope:** M.

### Task T28: Escribir las referencias integrales del canon

**Description:** Añadir los cinco mapas progresivos enlazando fuentes normativas y operativa real.

**Acceptance criteria:**

- [x] Canon, control plane, harnesses, autocambio y migraciones tienen cobertura explícita.
- [x] Todos los enlaces resuelven y no se duplican ADRs/contratos completos.
- [x] Los límites de permisos y niveles A/B/C coinciden con la implementación.

**Dependencies:** T27.  
**Implementation roles:** None; documentación.  
**Test surfaces:** Links, terminología y cobertura del mapa canónico.  
**Verification:** `skill_links.py` y revisión contra las rutas canónicas.  
**Files likely touched:** cinco archivos bajo `skills/project-autoworkspace/references/`.  
**Estimated scope:** M.

### Task T29: Probar autoauditoría de deriva y routing

**Description:** Añadir fixtures donde la skill/doctor detecte contratos, versiones, planes o harnesses divergentes.

**Acceptance criteria:**

- [ ] Cada deriva obligatoria produce FAIL/blocked con causa y fuente.
- [ ] Un sistema válido produce PASS sin convertir checks omitidos en verde.
- [ ] Routing positivo/negativo y handoffs no invocan publicación automática.

**Dependencies:** T28.  
**Implementation roles:** `role-back`; `plan-validators` para fixtures de comportamiento.  
**Test surfaces:** Self-audit, router y doctor.  
**Verification:** pytest de router/harness y defectos sembrados.  
**Files likely touched:** tests router/harness y ajuste focal de `SKILL.md`.  
**Estimated scope:** M.

#### Checkpoint CP6b

- [ ] Skill 17 y canon progresivo válidos.
- [ ] Las fixtures de deriva rompen la puerta por el motivo esperado.

## Tasks — Wave 7 y cierre

### Task T30: Integrar el catálogo 17 en todas las superficies

**Description:** Regenerar índices y actualizar instaladores/doctores para el nuevo conjunto canónico.

**Acceptance criteria:**

- [x] README, taxonomía, índice y snapshot contienen exactamente el catálogo generado.
- [x] Pi, Cursor y los instaladores descubren las 17 skills sin romper recursos ajenos.
- [x] Las aserciones de catálogo fallan ante una skill ausente/extra cuando esa identidad se esté probando.

**Dependencies:** T29, T12 y T15.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Generador, paridad documental e install matrix.  
**Verification:** generador `--check`, `test_install.sh`, Pi RPC y Cursor B.  
**Files likely touched:** README, TAXONOMY, skill index, snapshot e install tests.  
**Estimated scope:** M.

### Task T31: Actualizar documentación viva

**Description:** Alinear arquitectura, harnesses, routing y glosario con las capacidades implementadas.

**Acceptance criteria:**

- [x] Los diagramas/textos distinguen route, execute, verify, evidence, complete y publish.
- [x] Quickstarts usan Git pineado/plugin/bootstrap reales y marcan skills-only como parcial.
- [x] No quedan claims de soporte superior a la evidencia nativa.

**Dependencies:** T30.  
**Implementation roles:** None; documentación.  
**Test surfaces:** Links, terminología, coherencia y ejemplos.  
**Verification:** gates de documentación y ejecución de los ejemplos en fixtures.  
**Files likely touched:** ARCHITECTURE, harness integration/setup, routing y GLOSARIO.  
**Estimated scope:** M.

#### Checkpoint CP6

- [ ] Catálogo 17 y documentación viva coherentes.
- [ ] Bootstrap, skill y harnesses tienen evidencia de sus propias puertas.

### Task T32: Ejecutar validación integral sobre una identidad final

**Description:** Integrar las nuevas puertas en Make/CI y ejecutar todas las comprobaciones después del último cambio.

**Acceptance criteria:**

- [ ] `make validate`, `make test`, `make smoke` y typecheck están verdes.
- [ ] `make validate-harnesses` y `make e2e-orchestration` pasan en Pi y Cursor.
- [ ] Toda la evidencia corresponde al mismo contenido final y no hay requisito obligatorio `not_run`.

**Dependencies:** T31, T21, T23 y T26.  
**Implementation roles:** `role-back`; `plan-validators`.  
**Test surfaces:** Todas las suites, gates y recorridos E2E.  
**Verification:** comandos completos registrados, defectos sembrados y digest final.  
**Files likely touched:** Makefile, run-validation, agregación de tests y evidencia del plan.  
**Estimated scope:** M.

### Task T33: Preparar versiones y release readiness

**Description:** Aplicar bumps por cambio real, alinear distribuciones y preparar notas sin publicar.

**Acceptance criteria:**

- [ ] Repo, locks, plugin e instalador declaran versiones coherentes y skills solo sus bumps propios.
- [ ] El bump del contrato se justifica según compatibilidad y ADR-0010.
- [ ] Release readiness pasa; tag/PR/merge/release permanecen sin ejecutar.

**Dependencies:** T32.  
**Implementation roles:** `role-back`; `project-publish` solo para readiness local.  
**Test surfaces:** Version coherence, changelog y release fixture.  
**Verification:** `release_coherence.py --release-gate` y readiness en copia temporal.  
**Files likely touched:** package manifest/lock, tools manifest/lock y CHANGELOG.  
**Estimated scope:** M.

### Task T34: Revisión independiente de cierre

**Description:** Contrastar cada módulo, tarea y checkpoint con su evidencia final y clasificar cualquier pendiente.

**Acceptance criteria:**

- [ ] T00–T33 y CP0–CP7 están PASS o el veredicto integral es NO-GO con IDs concretos.
- [ ] El revisor independiente no detecta omisiones, evidencia stale ni publicación no autorizada.
- [ ] El documento registra alcance entregado, limitaciones y siguiente acción externa separada.

**Dependencies:** T33.  
**Implementation roles:** None; verificador independiente/`aw-verifier`.  
**Test surfaces:** Revisión plan vs ejecución y evidencia final.  
**Verification:** `review-vs-plan.py`, digest final y revisión read-only.  
**Files likely touched:** únicamente este documento con el informe final.  
**Estimated scope:** S.

#### Checkpoint CP7

- [ ] Todas las puertas obligatorias verdes sobre la misma identidad.
- [ ] Release readiness y publicación permanecen diferenciadas.
- [ ] Veredicto integral GO solo si no queda ningún criterio blocked/not_run.

## Definition of Done del incremento

- [ ] T00–T34 completados en orden de dependencias con evidencia registrada.
- [ ] Los diez módulos cumplen sus criterios de especificación.
- [ ] Registry/runtime/evidence no tienen divergencias y el E2E no fabrica resultados.
- [ ] El recorrido completo pasa en Pi y Cursor con escritura aislada, verificación y cierre.
- [ ] Pi Git pineado, Cursor plugin completo y bootstrap con atestación están verificados.
- [ ] `project-autoworkspace` y el catálogo 17 funcionan en ambos harnesses.
- [ ] `make validate`, `make validate-harnesses` y `make e2e-orchestration` están verdes.
- [ ] No hay publicación, mutación de host ni cambio externo sin autorización específica.

## Registro de ejecución

Durante IMPLEMENT cada tarea añade aquí: estado, HEAD/contenido, roles realmente cargados, RED/GREEN cuando aplique, comandos, artefactos, limitaciones y evidencia vinculada. Las casillas no se marcan antes de esa evidencia.

### T00 — baseline

- Estado: **done** (documentación y fixtures; no requiere RED).
- Base: `0811c9a3b6582c47692dbc80eb34b8cee8f95c80`, rama `main`; el plan nuevo y las fixtures eran los únicos no rastreados.
- Roles/skills cargados: `plan-continue`, `plan-validators`; no había código de aplicación que implementar.
- Entorno: Python 3.14.8, Node 26.13.0, Pi 1.5.0; Cursor `agent` ausente.
- Verificación: `make validate` → 438 passed + All checks passed; `git diff --check` → PASS.
- Artefactos: fixtures inertes bajo `scripts/tests/fixtures/` para plan, proyecto y release.
- Límites: sin escrituras globales, red, credenciales, publicación ni mutación de host.
- Registrado: 2026-11-09T19:45:51Z.

### T01 — reproducción del contrato

- Estado: **done** como tarea RED; las pruebas permanecen en la suite y deben pasar tras T03–T06.
- Roles/skills cargados: `role-back`, `plan-validators`.
- Artefacto: `tools/execution/tests/test_integration_contract.py`.
- RED: `uv run --project tools --frozen pytest tools/execution/tests/test_integration_contract.py -q` → exit 1, **4 failed** por las divergencias previstas.
- Fallos probados: IDs runtime≠registry, política sin contrato, operaciones de cierre no resolubles y `OpResult` manual en E2E.
- Ningún host, red o servicio externo utilizado.

### T02 — spike Cursor

- Estado: **blocked**.
- Roles/skills cargados: `role-back`, `plan-validators` en el análisis de capacidad.
- Comprobación: `command -v agent` / `agent --version` → binario no encontrado.
- Resultado: native B/C = `not_run`; no se instalaron binarios ni se usaron credenciales sin autorización específica.
- Impacto: T15, T22, T23 y el cierre integral quedan bloqueados hasta disponer del entorno Cursor aprobado; los carriles independientes continúan.
- Revalidación 2026-11-09, sin marcar casillas: sonda read-only. `command -v agent` ausente; `type -a agent` → not found. `cursor-agent` es un enlace a `/usr/bin/mise` y no se ejecutó. `test -x` negativo en `/usr/bin/agent`, `/usr/local/bin/agent`, `~/.local/bin/agent`, `~/.local/bin/cursor-agent` y `~/.local/share/mise/installs/cursor-agent`. Ese directorio de instalaciones no contiene `cursor-agent`. `cursor` resuelve a `/usr/share/cursor/cursor`; `cursor --version` → `3.29.9`, `306d153d51d714882ab7b1bc49649cab624e8a30`, `x64`.
- Causa precisa de la sonda pedida: `agent` no está en PATH e instalar el CLI no está autorizado. El shim de mise no se ejecutó. Revisión posterior, solo lectura: existe un ejecutable fuera de PATH en `~/.config/Cursor/User/globalStorage/anysphere.cursor-agent-worker/agent-cli/.local/bin/cursor-agent` (`test -x` afirmativo; enlace a `versions/2026.11.05-86047df/cursor-agent`). No se invocó. El uso de ese binario y de credenciales de modelo no está autorizado por los pasos de esta sesión. Niveles B y C: `not_run`. No hubo sentinel.

### T03 — registry como fuente de OpSpec

- Estado: **done**.
- Roles/skills cargados: `role-back`, `role-clean-code`, `plan-validators`; leído `refactoring-protocol.md`.
- Cambios: eliminada la tabla Python duplicada; `OpSpec` se deriva de YAML; añadidas al registry las nueve operaciones runtime ausentes y metadatos de snapshot/timeout/argv.
- Compatibilidad: los handlers existentes se registran por los mismos IDs; operaciones declarativas sin handler siguen bloqueando.
- Tests: las dos pruebas de registry/policy de T01 pasan; suite focal → **67 passed, 2 failed**, ambos RED reservados a T04/T06.
- La histórica congelada de 25 operaciones no se reescribe; la identidad inicial del registry unificado pasó a 34 operaciones.

### T04 — evidencia ligada al registry

- Estado: **done**.
- Roles/skills cargados: `role-back`, `role-clean-code`, `plan-validators`.
- Cambios: fases de cierre y verificadores se derivan de `OpSpec`; añadidas `schema_write` e `integrate`; la skill de evidencia debe coincidir con la skill propietaria de la operación.
- Migración de tests: `plan_specification` → `specify`; SCHEMAS/INTEGRATE usan `plan-continue`. No se editaron planes históricos.
- Verificación: `uv run --project tools --frozen pytest tools/execution/tests tools/contracts/tests tools/workspace-router/tests -q` → **81 passed, 1 failed**; el único rojo es el E2E manual asignado a T06.
- Registry actual: 36 operaciones canónicas.

### T07 — schema y parser aw-plan

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: ausencia de `contracts.plan` confirmada antes de implementar.
- Cambios: schema estricto, parser de bloque único, StrictLoader, paths confinados, IDs/dependencias y digest canónico; template de plan.
- Verificación: 10/10 pruebas nuevas; el documento real de 35 tareas carga como DAG válido; suite focal **96 passed**.
- Corrección de contrato: revisiones hex de solo ceros se escriben entre comillas para evitar que YAML las convierta en entero.

### T08 — plan activo y migración

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: APIs `activate_plan/load_active_plan/migrate_status` ausentes.
- Cambios: status schema 2, migración explícita/perezosa en lectura, active plan con path/base/digest, tareas pending y CLI `--migrate-status`.
- Verificación: 5/5 pruebas nuevas; suite focal **101 passed**.
- Garantías: lectura legacy sin escrituras, migración idempotente, historial preservado, cambio de digest rechazado y ningún plan inferido.

### T05 — run_verified

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: `test_run_verified.py` falló en colección porque `run_verified` no existía.
- Cambios: API pública con preflight de verifier/artifacts/plan/task, input/output digests, verificación obligatoria, store de éxito/fallo y schema de resultado.
- Evidencia ampliable: `plan_id`/`task_id` persistidos; `.autoworkspace/runs/` excluido del digest general para evitar recursión.
- Verificación: 4/4 pruebas nuevas PASS; suite focal → **85 passed, 1 failed**, solo el RED de T06.
- Nota de diseño: el dispatcher completo de adaptadores se conectará en T16/T20/T22; T05 fija el contexto y la API sin estado mutable global.

### T06 — E2E público de ejecución

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- Cambios: el handler `specify` escribe el artefacto; `run_verified` comprueba contenido y almacena evidencia; `advance_status` completa/reproduce idempotentemente.
- Negativos: mutación sin aprobación bloqueada, free-form rechazado, ausencia de run ID, artefacto stale y verificación fallida rechazados.
- Verificación focal: E2E PASS + **86 passed** en execution/contracts/workspace-router.
- CP1: `make validate` → **446 passed**, registry/contracts 36 ops y **All checks passed**; `git diff --check` PASS.
- Dependencias de tests: el E2E se ejecuta con `uv run --project tools --frozen bash ...`; el Python del sistema no tiene jsonschema.

### T09 — ciclo de vida por tarea

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: APIs de lifecycle ausentes antes de implementar.
- Cambios: ready/start/await/complete/fail/retry por tarea; receipts `task_id:run_id`; bindings plan/task/fase/skill/target/operación; fase derivada del trabajo restante.
- Verificación: 4/4 pruebas nuevas; suite focal **105 passed**.
- Concurrencia: dos completions independientes serializan revisiones 4 y 5 sin lost update; los handlers fixture son idempotentes para aislar el test de invalidación de contenido.
- Diseño confirmado: la escritura real paralela queda para worktrees/staging en T17; compartir workspace entre writers invalida evidencia como debe.

### T10 — harness doctor core

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: paquete `harness` inexistente antes de implementar.
- Cambios: `Check`, report schema, agregación A/B/C, códigos 0/1/3, coherencia package/plugin/installer y validación de symlinks absolutos al catálogo.
- Verificación: 6/6 pruebas nuevas; suite focal **111 passed**.
- Límite actual: sondas nativas Pi/Cursor se conectan en T12/T15; no se presentan como ya implementadas.

### T11 — paquete Pi Git

- Estado: **done**.
- Roles/skills cargados: `role-back`; configuración/documentación sin TDD artificial.
- Cambios: `keywords: [pi-package]`, `pi.skills: [./skills]`, quickstart `pi install git:…@v7.0.3`, update explícito de tag y symlinks clasificados como desarrollo.
- Verificación: manifest JSON PASS; `pi install <checkout>` y `pi list` con HOME temporal PASS; Prettier PASS.
- Límites: npm/publicación no ejecutados; configuración real de Pi no modificada.

### T12 — discovery y lifecycle Pi

- Estado: **done** para paquete/lifecycle local; smoke público de la próxima release sigue pendiente y bloqueante para distribución final.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: módulo Pi ausente; después, smoke real `v7.0.2` falló porque `prepare: husky` se ejecuta con devDependencies omitidas.
- Cambios: RPC JSONL con timeout/process group, validación de origen package, doctor `--native`, E2E de install/reinstall/uninstall y preservación de skill ajena.
- Bugfix: `scripts/prepare.mjs` omite hooks cuando Husky no está instalado; instalación npm `--omit=dev` temporal PASS.
- Verificación: 10/10 pruebas harness; `test_pi_native.sh` PASS; producción npm PASS; Prettier PASS.
- Pendiente externo: `AW_PI_GIT_SMOKE=1` con `AW_PI_GIT_FROM_TAG` y `AW_PI_GIT_TO_TAG` tras publicar una versión corregida. El fallo de la release antigua no se presenta como PASS ni se reescribe.

### T13 — plugin Cursor completo

- Estado: **done** en alcance estático; nativo B/C sigue bloqueado por T02.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: plugin `6.1.1` frente a repo `7.0.3`; corregido a 7.0.3.
- Verificación: componentes skills/rules/agents/hooks existen; hooks portables; marketplace root correcto; **13 harness tests** PASS y Prettier PASS.
- Límite: no se afirma descubrimiento ni permiso nativo Cursor.

### T14 — instalación Cursor full

- Estado: **done**.
- Roles/skills cargados: `role-back`, `role-clean-code`, `plan-validators`; protocolo de refactor leído.
- Cambios: `--components skills|full`, proyecto/user targets, 21 recursos individuales, preflight, journal write-ahead, rollback, uninstall selectivo y doctor de versión alineado.
- RED: módulo full inexistente; después pruebas de conflicto, fault injection e idempotencia.
- Verificación: 5/5 tests full; 18 harness tests; install matrix PASS; Bash syntax y Prettier PASS.
- Bloque CP3: `make validate` → **483 passed + All checks passed**; tras corregir anotaciones nuevas, `npm run typecheck` → 97 archivos sin errores y suite focal **123 passed**.

### T15 — Cursor nativo B/C

- Estado: **blocked**, heredado de T02.
- Motivo: `agent` no instalado y no se autorizaron credenciales/coste ni instalación global.
- No se escribieron probes ficticios ni se marcaron criterios. T22/T23 permanecen bloqueados por dependencia.

### T16 — DAG y scheduler

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`; referencia de concurrencia leída.
- RED: paquete orchestrator ausente antes de implementar.
- Cambios: `RunContext`, puerto `SubagentAdapter`, `AdapterResult`, topological waves, scheduler con ThreadPoolExecutor, fail-fast y CLI inicial.
- Verificación: 5/5 pruebas nuevas; dry-run sin cambios de bytes; evidencia real completa tareas; max_active=2; revisiones sin lost update.
- Límite inicial: los writers reales se aislaron en T17; el CLI reportaba adaptadores nativos pendientes en lugar de simular ejecución.

### T17 — worktrees, patches y staging

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: `WorktreeManager` ausente antes de implementar.
- Cambios: worktrees detached bajo /tmp, write scopes, diff binario de tracked/untracked, manifests SHA-256, `git apply --check` y limpieza confinada.
- Verificación: 4/4 pruebas con texto, 256 bytes binarios, scope violation y cleanup; HEAD de origen inalterado.
- Seguridad de Git: sin commits, `reset --hard` ni `--force`; `worktree prune` solo tras eliminar raíces temporales controladas.

### T18 — resiliencia y reanudación

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: tarea running quedaba sin recuperación y `Scheduler.cancel` no existía.
- Cambios: cancel_event compartido, transiciones blocked/cancelled, recuperación de running/awaiting con reconciliación y retry explícito.
- Verificación: 8 scheduler tests y **12 orchestrator tests** PASS.
- Garantías: resume no repite succeeded, cancelled no es éxito, tareas pendientes no se lanzan tras cancelación y no hay retry ciego tras interrupción.

### T19 — recorrido completo del núcleo

- Estado: **done**.
- Roles/skills cargados: `role-back`, `role-clean-code`, `plan-validators`.
- Cambios: extraída `verify_and_store` para resultados reales ya ejecutados; `WorktreeAdapter` copia patch/manifest, aplica a staging, verifica y produce evidencia en el repo principal aislado.
- Recorrido: DEFINE + IMPLEMENT + VALIDATE, tres patches y cierres; archivos producidos no se aplican al checkout principal.
- Negativo: contenido incorrecto en VALIDATE deja la tarea failed y no cierra.
- Verificación: `test_orchestration_core.sh` PASS; **14 orchestrator tests**; `npm run typecheck` → 107 archivos sin errores.
- CP4 completo antes de conectar modelos.

### T20 — extensión y adaptador Pi

- Estado: **done**.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: adaptador ausente; native extension gate preparado antes de implementar.
- Cambios: paquete `pi.extensions`, `aw-status`, `aw_subagent`, worker acotado, JSONL buffered, salida limitada, allowlist de skills/cwd y proceso aislado.
- Adaptador Python: tools mínimas, task packet con digest, stopReason/exit codes, timeout/cancel con process group y reconciliación.
- Verificación: 6/6 pruebas nuevas; **24 harness tests**; native lifecycle + `aw-status` PASS; npm production PASS; typecheck 109 archivos sin errores.
- Límite: estas pruebas no invocan un modelo ni afirman todavía el recorrido nativo completo de T21.

### T21 — recorrido nativo completo Pi

- Estado: **blocked**.
- Motivo: requiere una ejecución real de modelo con coste/credenciales; la orden general de implementar no incluye la autorización específica exigida por el plan.
- No se ejecutó el modelo ni se marcaron criterios. CP5-Pi y el cierre integral permanecen bloqueados.

### T24 — release assets

- Estado: **done** en workflow y fixtures; release real no ejecutada.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: `release_asset_errors` ausente; después la secuencia actual carecía de checksum/upload.
- Cambios: archive → SHA256SUMS → attestation → `gh release upload`; `contents: write` limitado a provenance; sin `--clobber`; regla integrada en release coherence.
- Verificación: 3/3 pruebas nuevas, round-trip archive/checksum PASS, `release_coherence.py` RELEASE OK y Prettier PASS.
- Límite: la existencia/verificación pública de assets de una nueva release se prueba tras publicación autorizada.

### T25 — bootstrap verificable

- Estado: **done** sobre release fixture; smoke público pendiente tras publicación.
- Roles/skills cargados: `role-back`, `plan-validators`.
- RED: extractor ausente; después las fixtures detectaron symlinks de desarrollo y dependencia jsonschema no declarada en el comando.
- Cambios: `safe_extract` con una apertura, cuotas/confinamiento, doctor source/target, `bootstrap.sh` con checksum + attestation + instalación + doctor y rollback owned-resource.
- Verificación: 9/9 pruebas de extractor; E2E Pi y Cursor PASS; dry-run sin escrituras; checksum/attestation/tar hostil rechazados; 33 harness tests.
- Documentación: comando de una línea con clone pineado, sin `curl | bash`.
- Puerta: `npm run typecheck` → 112 archivos sin errores; `make validate` → **515 passed + All checks passed**.

### T26–T34 — bloqueados por dependencias externas

- **T26:** depende de T15 (Cursor nativo ausente); smoke público además requiere una release nueva autorizada.
- **T27–T29:** dependen de T21/T23/T26; no se crea la skill 17 sobre recorridos nativos no demostrados.
- **T30–T31:** dependen de T29; catálogo/documentación final no se marcan como integrados.
- **T32–T34:** dependen de las puertas nativas y de T31; cierre integral, versión final y revisión GO quedan pendientes.
- Ninguno de estos criterios se convierte en PASS por las pruebas locales existentes.

## Informe de revalidación — 2026-11-09

Skills cargadas: `plan-continue`, `plan-validators`. Ajustes locales de esta revalidación: intérprete de `test_pi_native.sh` y `commit.gpgsign=false` en el fixture de readiness (prueba, no producto). Sin `role-front`, `role-design` ni `project-publish`. No se marcaron casillas nuevas. No hay commit, push, PR, tag, release ni instalación de CLI.

### Identidad y árbol

- `git rev-parse HEAD` → `0811c9a3b6582c47692dbc80eb34b8cee8f95c80`
- `git branch --show-current` → `main`
- Árbol preservado: 23 modificados y 47 no rastreados al inicio de la revalidación. El diff toca contrato de ejecución, registry (36 ops), plan activo, doctor/harness, orquestador, plugin Cursor, instalador, bootstrap, release workflow y fixtures. Cambios añadidos en esta sesión: `scripts/tests/test_pi_native.sh` (intérprete del proyecto) y `tools/execution/tests/test_product_closure_state_release.py` (`commit.gpgsign false` en el repo fixture). No se aplicó `reset`, `clean` ni `--force`.
- `git diff --check` → exit 0, sin hallazgos, repetido al cierre de la revalidación (`2026-11-09T21:37:35Z`).

### aw-plan

`uv run --project tools --frozen python` cargó el bloque con `contracts.plan.load_plan`. Resultado: `plan_id=autoworkspace-integration-v1`, `base_revision` igual al HEAD, 35 IDs únicos, dependencias resolubles y DAG acíclico (`validate_plan`). Digest `c4027c59c60cd081fbdf0eb8436c27b12c22c7e82dee4e8fbc6bed0e8f1fadc6`.

### Gates deterministas

- Primera repetición de `make validate` en esta ejecución → **FAIL**: `test_v44_readiness_fails_missing_yanked` y `test_v45_readiness_ok_and_ordinary_skip` (2 failed, 513 passed). Causa: `_init_release_repo` hacía `git commit` heredando `commit.gpgsign=true` del host; GPG falló con `Input/output error` al firmar. Clasificación: flakiness del fixture por configuración del host, no un defecto de readiness ni de Cursor/Pi nativo. Fuera de ese entorno restringido las mismas dos pruebas pasaron; el FAIL quedó documentado y no se convirtió en PASS omitido.
- Corrección demostrada por ese FAIL: el fixture fija `git config commit.gpgsign false` en el repo temporal.
- Tras la corrección: `make validate` → **515 passed** y `=== All checks passed ===`. Incluye spec, enlaces, release coherence, hygiene, registry 11 tools / 36 ops, índice de 16 skills, smoke de routing, `scripts/tests/test_install.sh`, `scripts/tests/test_execution_e2e.sh` y `bash -n`.
- `npm run typecheck` → `Success: no issues found in 112 source files`.
- `npm run lint` → tras formatear este documento con Prettier, All matched files use Prettier code style.

Estos tres comandos no incluyen `test_pi_native.sh`, `test_orchestration_core.sh` ni `test_bootstrap.sh`.

### Scripts focales independientes

- Primera ejecución de `bash scripts/tests/test_pi_native.sh` → **FAIL**, exit 1, mensaje `jsonschema required: uv sync --frozen`. Causa: el script llamaba a `/usr/bin/python3` 3.14.8, que no tiene `jsonschema`. `pi install` en un HOME temporal sí llegó a `Installed` dos veces. Las aserciones RPC no se ejecutaron. No es un fallo de modelo ni de la release antigua.
- Corrección, demostrada por ese fallo: las invocaciones que importan el proyecto usan `uv run --project "$ROOT/tools" --frozen python`. El bloque `AW_PI_GIT_SMOKE` no se ejecutó.
- Repetición de `bash scripts/tests/test_pi_native.sh` → exit 0. Salida: `Pi native package discovery: 16 skills discovered natively`, `Pi packaged extension loaded: aw-status`, desinstalación con skill ajena preservada, `Pi native lifecycle OK`.
- `bash scripts/tests/test_orchestration_core.sh` → `2 passed`.
- `bash scripts/tests/test_bootstrap.sh` → `bootstrap Pi + native doctor: PASS`, `bootstrap Cursor full + doctor: PASS`, `bootstrap tests OK`. Cubre checksum, atestación denegada y un tar de traversal sobre fixture local. No descarga una release pública.

### Matriz de superficies

No hay un único «harness PASS».

| Superficie                            | Resultado | Dónde se observó                                                                                    |
| ------------------------------------- | --------- | --------------------------------------------------------------------------------------------------- |
| Cursor A estático/plugin e instalador | PASS      | `make validate` (pytest de plugin/instalador y `test_install.sh`) y doctor de bootstrap en temporal |
| Cursor B descubrimiento/carga nativa  | `not_run` | `agent` ausente del PATH; el binario fuera de PATH no se invocó                                     |
| Cursor C permisos nativos             | `not_run` | Sin ejecución; sin sentinel                                                                         |
| Pi A paquete/lifecycle                | PASS      | `test_pi_native.sh` tras el arreglo de intérprete                                                   |
| Pi B RPC `get_commands` y extensión   | PASS      | mismo script: 16 skills de paquete y `aw-status`                                                    |
| Pi recorrido con modelo               | `not_run` | T21 `blocked`; el modelo no está autorizado en esta sesión                                          |
| Smoke de una release nueva            | `not_run` | `AW_PI_GIT_SMOKE` no activado; no hay publicación autorizada                                        |

IDE Cursor observado, sin usarlo como CLI headless: versión `3.29.9`. Pi `1.5.0` en `/home/alexendros/.local/share/mise/installs/pi/1.5.0/pi/pi`. Node `v26.13.0`. Python de sistema `3.14.8`; el venv del proyecto es `tools/.venv`.

### Delta frente al informe heredado

- HEAD, rama y volumen del árbol coinciden con la base no publicada.
- `make validate` 515 passed y typecheck de 112 archivos se confirmaron de nuevo; ya no son cifras heredadas.
- El PASS histórico de `test_pi_native.sh` no se sostuvo con `/usr/bin/python3`. Tras usar el intérprete del proyecto, el script pasa. El registro antiguo de T12 no se reescribe.
- `agent` sigue ausente del PATH. Hay IDE Cursor `3.29.9` y un shim mise sin install dir. Además, fuera de PATH, `test -x` confirma `cursor-agent` `2026.11.05-86047df` bajo la configuración de Cursor. No se invocó.
- Siguen sin existir `tools/harness/cursor.py`, `scripts/tests/test_cursor_native.sh` y `skills/project-autoworkspace`.
- No hay commit nuevo.

### Tabla T00–T34

Las tareas `done` conservan su registro anterior. La evidencia de esta sesión es el gate agregado o el script focal indicado, no un comando nuevo por cada ID. Ninguna ausencia se clasifica como `not_applicable`.

| ID      | Estado  | Evidencia y comandos de esta sesión                                                         | Limitación                                                    |
| ------- | ------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| T00     | done    | Identidad git, `git diff --check` exit 0, fixtures presentes                                | No abre publicación                                           |
| T01     | done    | Cubierta por `make validate` / 515 passed                                                   | El RED histórico no se repitió como fallo esperado            |
| T02     | blocked | Sonda de PATH y `test -x` del binario fuera de PATH; no se invocó; B/C `not_run`            | Instalación no autorizada; el binario existente no se ejecutó |
| T03–T14 | done    | `make validate`: registry 36 ops, plugin, install matrix, 515 passed                        | T13/T14 no demuestran B/C nativo                              |
| T15     | blocked | No ejecutada; `cursor-native-discovery` sigue `not_run` en `doctor.py`                      | Depende de T02                                                |
| T16–T20 | done    | 515 passed; `test_orchestration_core.sh` → 2 passed                                         | El núcleo no sustituye el recorrido con modelo                |
| T21     | blocked | No ejecutada                                                                                | Modelo no autorizado en esta sesión; `not_run`                |
| T22     | blocked | No ejecutada; no hay adaptador en `cursor.py`                                               | Depende de T15 y T19; T15 no está resuelta                    |
| T23     | blocked | No ejecutada                                                                                | Depende de T22                                                |
| T24     | done    | 515 passed incluye `test_release_assets.py`; release real no creada                         | Assets públicos `not_run`                                     |
| T25     | done    | `test_bootstrap.sh` PASS sobre fixture                                                      | No es smoke de una release publicada                          |
| T26     | blocked | No ejecutada más allá de la cobertura fixture ya en T25                                     | Depende de T15; smoke público `not_run`                       |
| T27–T31 | blocked | No ejecutadas; el catálogo generado sigue en 16 skills                                      | Dependen de T21, T23, T26 o de la tarea anterior              |
| T32     | blocked | `make validate`, typecheck y lint verdes; faltan `validate-harnesses` y `e2e-orchestration` | Depende de T31, T21, T23 y T26                                |
| T33     | blocked | No ejecutada                                                                                | Depende de T32; sin tag ni release                            |
| T34     | blocked | Revisión independiente de esta sesión; no es cierre de T33                                  | Depende de T33; no queda `done`                               |

### Checkpoints

- CP0: el baseline determinista está verde y Cursor nativo sigue clasificado como bloqueado. No se añade ninguna casilla.
- CP3 no se cierra. Cursor B/C y el smoke público Pi siguen pendientes.
- CP5 no se cierra. CP5-Pi no se cierra.
- CP6a conserva el PASS ya registrado por la evidencia fixture de T24/T25, reforzada hoy por `test_bootstrap.sh`. No se marca nada nuevo.
- CP6, CP6b y CP7 no pasan.

### Veredicto

**NO-GO** por requisitos externos no satisfechos; los gates deterministas y las capacidades locales verificadas están en verde. No hay evidencia suficiente para cierre nativo integral ni publicación.

IDs pendientes: T02, T15, T21, T22, T23, T26, T27, T28, T29, T30, T31, T32, T33, T34.

La causa no es un fallo abierto de `make validate`, typecheck, lint, DAG, lifecycle Pi sin modelo, RPC `get_commands`, núcleo de orquestación ni bootstrap fixture. Los FAIL de `test_pi_native.sh` (intérprete del sistema) y de los fixtures de readiness (GPG heredado) quedaron clasificados y corregidos; las repeticiones pasan. El cierre integral falta porque no se ejecutó Cursor B/C, el recorrido con modelo no está autorizado y no hay una release nueva que someter a smoke.

Tras el aviso de `aw-verifier`, el desfase heredado de T07 quedó resuelto en la revisión posterior: sus tres criterios se marcaron solo después de repetir las pruebas del parser y validar el plan actual de 35 tareas. No era un PASS nuevo, sino alineación documental de una capacidad ya verificada.

`aw-verifier` (revisión read-only, sin reejecutar los gates) sostiene el NO-GO: no hay commit posterior al HEAD; los arreglos de `uv run` y `commit.gpgsign false` están en el árbol; no existen `cursor.py` ni `skills/project-autoworkspace`; B/C no se presentan como PASS.

### Reapertura, sin ejecutarla

1. Provisionar un entorno Cursor nativo aprobado.
2. Autorizar específicamente los recorridos con modelo/credenciales y su posible coste.
3. Reabrir T02, T15, T21, T22, T23 y sus dependientes.
4. Autorizar después una release nueva para el smoke público y la verificación de distribución.

## Siguiente puerta

Fin de TASKS. La revisión o aprobación de esta lista no autoriza por sí sola implementación ni publicación. Para iniciar T00 hace falta una orden explícita de implementar este plan; las operaciones externas, nativas con coste/credenciales, commits, pushes, PRs, merges, tags y releases conservan sus autorizaciones específicas.
