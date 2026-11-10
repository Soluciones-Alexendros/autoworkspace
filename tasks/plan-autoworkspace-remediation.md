# Remediación verificable de autoworkspace 7.1.0

Plan ID: `autoworkspace-remediation-v1`  
Base auditada: `68c1dc90f8d5edfe4ca011f585de95dce95e6e32` (`v7.1.0`)  
Estado: **T20 GO pre-release (candidato 7.1.1 local); publicación pendiente de autorización**  
Fuente de verdad: este documento. La especificación, el plan técnico, las tareas y la evidencia de este incremento se añadirán aquí. No se crearán `SPEC.md`, `tasks/todo.md` ni trackers paralelos.

## Objetivo del incremento

Corregir las desviaciones detectadas tras integrar el PR #63 y publicar `v7.1.0`, de modo que el cierre del sistema se apoye en evidencia real y no en la sola presencia de código, archivos o fixtures.

El incremento debe demostrar, sobre una misma identidad final:

1. Aislamiento y mínimo privilegio efectivos en subagentes Pi y Cursor.
2. Orquestación con integración acumulativa, verificación independiente y evidencia válida para todo tipo de tarea.
3. Descubrimiento y políticas nativas de Cursor comprobados mediante el propio harness.
4. Recorridos reales Pi y Cursor con modelo, sin convertir `blocked` o `not_run` en PASS.
5. Una release nueva con assets, checksums, atestación y smoke público satisfactorio.
6. Canon, índice, estado y evidencia final coherentes con la implementación publicada.

## Alcance y no objetivos

### Dentro del alcance

- Corrección de los hallazgos P0/P1/P2 de la auditoría posterior al PR #63.
- Contratos, implementación, pruebas, validadores y documentación viva afectados.
- Recorridos nativos con modelo sobre fixtures y worktrees temporales.
- Preparación y, solo tras autorización separada, publicación de una release patch posterior a `v7.1.0`.
- Actualización final del plan y del estado declarativo del repositorio.

### Fuera del alcance

- Nuevas familias de skills, nuevos dominios o un daemon/servidor de agentes.
- Nuevos frameworks de orquestación, bases de datos o dependencias no justificadas.
- Reescritura de planes históricos o de la release/tag `v7.1.0`.
- Publicación, commits, pushes, PRs, merges, tags o releases autorizados por este documento.
- Mantenimiento real del host, acceso a secretos o mutación de configuración global para ejecutar pruebas.

## Mapa de capacidades aprobado

| Module id                 | Responsabilidad y entrega principal                                                                                                                                                                                                       | Depends on                                       |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `execution-isolation`     | Hacer efectivo el mínimo privilegio: entorno filtrado, herramientas y efectos permitidos, confinamiento de escrituras, prohibición de autoaprobación y reconciliación tras timeout/cancelación. Contratos comunes para ambos adaptadores. | —                                                |
| `orchestration-integrity` | Mantener un staging compartido por run, aplicar patches en orden topológico, cerrar tareas read-only con evidencia real, ejecutar verificadores de aceptación y hacer que `--plan` tenga una semántica explícita.                         | `execution-isolation`                            |
| `cursor-native-proof`     | Sustituir las comprobaciones estáticas presentadas como B/C por descubrimiento y políticas ejecutados mediante Cursor; completar el recorrido headless real sin `--force` para obtener PASS.                                              | `execution-isolation`, `orchestration-integrity` |
| `pi-native-proof`         | Completar el recorrido real Pi con modelo, restricciones efectivas, escritura aislada, integración, verificación, evidencia y ausencia de procesos residuales; validar el paquete pineado.                                                | `execution-isolation`, `orchestration-integrity` |
| `release-recovery`        | Incorporar las puertas nativas al circuito controlado de cierre, diagnosticar la ausencia de assets de `v7.1.0`, producir una release patch con tarball/checksum/atestación y ejecutar smoke público de bootstrap y paquete Pi.           | `cursor-native-proof`, `pi-native-proof`         |
| `canon-reconciliation`    | Alinear catálogo 17, documentación, diagramas, estado declarativo y registro final de evidencia; realizar la revisión independiente y emitir GO/NO-GO sin requisitos ocultos.                                                             | `release-recovery`                               |

## Dirección de dependencias y orden de construcción

```text
Capa 0: execution-isolation
                  │
                  ▼
Capa 1: orchestration-integrity
                  │
                  ├──────────────────────┐
                  ▼                      ▼
Capa 2: cursor-native-proof        pi-native-proof
                  │                      │
                  └──────────┬───────────┘
                             ▼
Capa 3:               release-recovery
                             │
                             ▼
Capa 4:             canon-reconciliation
```

`cursor-native-proof` y `pi-native-proof` pueden trabajarse en paralelo después de estabilizar el núcleo, siempre que no compartan superficies de escritura. Las pruebas con modelo, credenciales o coste conservan una puerta de autorización independiente.

## Contratos entre capacidades

1. `execution-isolation` define las políticas comunes; ningún adaptador puede ampliarlas mediante prompts, flags o variables implícitas.
2. `orchestration-integrity` posee staging, integración y agregación; los adaptadores solo ejecutan un task packet y devuelven resultados normalizados.
3. Los módulos `*-native-proof` deben consumir el núcleo compartido y demostrar capacidades observadas en el harness correspondiente.
4. Un verde estático, una fixture o una simulación no sustituye una prueba nativa obligatoria.
5. `release-recovery` no publica por completar las pruebas: prepara evidencia y separa la autorización externa.
6. `canon-reconciliation` documenta únicamente capacidades demostradas sobre la identidad final.

## Supuestos aprobados

1. El núcleo continuará en Python; Bash quedará limitado a wrappers y TypeScript a la extensión Pi.
2. No se añadirán dependencias salvo justificación y aprobación específicas.
3. La corrección se publicará, cuando se autorice, como una release patch nueva; `v7.1.0` permanecerá inmutable aunque su distribución quedó incompleta.
4. Cursor CLI `2026.11.05-86047df` está disponible localmente, pero sus flags y capacidades se revalidarán contra documentación vigente antes de cambiar el adaptador.
5. Las ejecuciones con modelo utilizarán fixtures desechables y configuración explícita; este mapa no autoriza credenciales, coste ni instalación de binarios.
6. Los cambios de CI, esquemas públicos o contratos incompatibles requerirán la puerta correspondiente antes de implementarse.

## Límites globales

### Always

- Mantener este documento como única fuente de verdad del incremento.
- Reproducir primero cada defecto y añadir una regresión que falle por la causa esperada.
- Conservar trabajo ajeno, recursos ajenos, tags y planes históricos.
- Ejecutar las puertas deterministas y nativas afectadas después del último cambio material.
- Registrar identidad, comandos, artefactos, resultados y limitaciones de cada tarea.

### Ask first

- Implementar este mapa o cualquier especificación derivada.
- Ejecutar modelos, usar credenciales, asumir coste o acceder a servicios externos no públicos.
- Añadir dependencias, cambiar esquemas públicos o modificar CI.
- Crear commits, ramas, pushes, PRs, merges, tags o releases.
- Instalar/actualizar harnesses o modificar el host fuera de entornos aislados.

### Never

- Usar `--force`, `--yolo` o equivalentes para convertir una prueba de permisos en PASS.
- Presentar archivos presentes, hooks invocados directamente o fixtures como evidencia nativa de Cursor.
- Crear resultados `OpResult` manuales en E2E para afirmar que ocurrió una operación distinta.
- Mover o reutilizar `v7.1.0`, usar refs flotantes o omitir checksum/atestación.
- Convertir `skip`, `blocked`, `not_run` o dependencias ausentes en PASS.
- Aplicar automáticamente el staging al checkout del operador.

## Criterios de aceptación de la Fase 0

- [x] El operador aprueba los seis módulos y sus responsabilidades.
- [x] El operador aprueba la dirección de dependencias y el orden por capas.
- [x] El operador confirma que el alcance es remediar `v7.1.0` sin añadir capacidades ajenas.
- [x] El operador acepta los supuestos y límites globales.

# Fase 1 — Especificaciones

## Especificación transversal

### Objective

Remediar las brechas de `v7.1.0` sin ampliar el producto: que una tarea delegada solo pueda usar los privilegios concedidos, que el DAG produzca una integración acumulativa verificable y que Pi, Cursor, bootstrap y release demuestren sus capacidades en el entorno que afirman soportar.

El resultado no se medirá por archivos añadidos ni checkboxes. Cada capacidad deberá producir evidencia enlazada a plan, tarea, run, revisión, artefactos y verificaciones. El cierre será GO únicamente cuando todos los requisitos obligatorios estén verdes sobre la misma identidad final.

### Tech Stack

- Python 3.12 para contratos, scheduler, worktrees, adaptadores, doctor y pruebas.
- YAML/JSON Schema ya versionados; `yaml.StrictLoader` equivalente y validación local estricta.
- Bash únicamente para wrappers y scripts de prueba; `set -euo pipefail` y procesos sin shell libre.
- TypeScript estricto solo para `extensions/autoworkspace/`.
- Pi con paquete Git pineado, RPC sin modelo y subproceso JSON para delegación.
- Cursor CLI/IDE con versión observada y documentación vigente; ningún flag se presupone sin comprobarlo.
- Git worktrees, patches binarios, manifests SHA-256 y staging temporal.
- GitHub Actions, Releases, `gh release` y `gh attestation` para distribución.
- Sin nuevas dependencias, daemon, base de datos ni framework de orquestación.

### Commands

Puertas deterministas existentes:

```bash
make validate
make test
make smoke
npm run typecheck
npm run lint
uv run --project tools --frozen python tools/harness/doctor.py --harness all --json
uv run --project tools --frozen python tools/workspace-router/run.py --status --repo . --json
```

Puertas focales y nativas:

```bash
bash scripts/tests/test_orchestration_core.sh
bash scripts/tests/test_pi_native.sh
bash scripts/tests/test_cursor_native.sh
bash scripts/tests/test_bootstrap.sh
make validate-harnesses
make e2e-orchestration
```

Smoke público posterior a una release autorizada:

```bash
AW_PI_GIT_SMOKE=1 \
AW_PI_GIT_FROM_TAG=v7.1.0 \
AW_PI_GIT_TO_TAG=v7.1.1 \
bash scripts/tests/test_pi_native.sh
```

El tag de destino es una previsión patch, no una autorización ni una instrucción para crearlo. Si cambia el alcance SemVer se actualizarán el documento, los comandos y la documentación viva antes de implementar.

### Project Structure

```text
tools/execution/             → registry, ejecución, aprobación y evidencia
tools/contracts/             → contratos y schemas existentes
tools/harness/               → política común, adaptadores y doctor Pi/Cursor
tools/orchestrator/          → DAG, scheduler, staging, verificadores y agregación
scripts/tests/               → fixtures y recorridos nativos/adversarios
scripts/bootstrap.sh         → descarga, verificación, instalación y doctor
.github/workflows/           → release y puertas controladas
skills/project-autoworkspace/ → auditoría y protocolo de autocambio
tasks/plan-autoworkspace-remediation.md → único SDD y registro del incremento
.autoworkspace/              → plan activo, estado, runs y evidencia
```

Como diseño interno candidato, `tools/harness/policy.py` podrá concentrar la política de procesos y `tools/orchestrator/verifiers.py` la resolución de verificadores. No se crearán si duplican contratos existentes; los nombres definitivos se fijarán en el plan técnico sin alterar las responsabilidades aprobadas.

### Code Style

- Código e identificadores en inglés; documentación operativa del incremento en español y documentación de skills según `docs/GLOSARIO.md`.
- Dataclasses/tipos explícitos, funciones pequeñas, inyección de dependencias y errores con causa conservada.
- Una política se calcula desde registry + task + context; nunca desde texto libre del modelo.
- `shell=False`, grupos de procesos cancelables, timeouts, salida acotada y redacción de secretos.
- Escrituras atómicas, locks de alcance mínimo y confinamiento componente a componente.
- Adaptadores sin DAG, aprobaciones, integración ni publicación propias.
- Verificadores independientes, deterministas y resueltos desde identificadores permitidos; ningún comando arbitrario embebido en el plan.
- Stdout reservado a JSON cuando se solicite `--json`; diagnósticos en stderr.
- Limpieza de recursos temporales en `finally`, sin borrar recursos ajenos.

### Testing Strategy

1. **Reproducción RED:** una prueba por defecto auditado, fallando por la causa documentada antes de modificar el producto.
2. **Unitarias:** política de entorno/herramientas, scopes, DAG, receipts, manifests, resolución de verificadores, agregación y códigos de salida.
3. **Integración:** varias tareas dependientes sobre staging compartido, lectores sin write scope, escritores disjuntos, rollback de integración y reanudación.
4. **Nativas sin modelo:** paquete Pi/RPC, versión Cursor y descubrimiento estático A claramente separado de B/C.
5. **Nativas con modelo:** Pi y Cursor ejecutan el mismo fixture con escritura, integración, verificación y evidencia; Cursor B/C usa el harness real.
6. **Adversarias:** entorno con secretos no autorizados, herramienta denegada, scope escapado, patch vacío, contenido incorrecto, verificador desconocido, evidencia stale, timeout, cancelación, proceso residual, release sin assets, checksum/attestation inválidos y tar hostil.
7. **Regresión de validadores:** defectos sembrados deben romper la puerta esperada; un skip o una dependencia ausente nunca se cuenta como PASS.
8. **Cobertura:** no reducir la puerta CI existente (`77`) ni sustituir tests de comportamiento por snapshots.

Los dobles se limitan a unitarias/integración de procesos y servicios peligrosos. Las pruebas nativas obligatorias deben usar los binarios y modelos reales en entornos desechables.

### Boundaries

#### Always

- Mantener compatibilidad o documentar una migración explícita antes de cambiar un contrato público.
- Resolver verificadores y políticas antes de ejecutar efectos.
- Registrar versión del harness, modo, identidad, artefactos y resultado observado.
- Repetir todas las puertas afectadas tras el último cambio material.
- Separar validación local, aceptación nativa, release readiness y publicación.

#### Ask first

- Implementar cualquier módulo de esta especificación.
- Modificar CI, schemas públicos, contratos de CLI o política de aprobación.
- Añadir dependencias o instalar/actualizar binarios.
- Ejecutar modelos, usar credenciales o asumir coste.
- Crear commits, ramas, pushes, PRs, merges, tags, releases o reruns externos.

#### Never

- Relajar permisos, quitar tests o bajar cobertura para obtener verde.
- Usar `--force`, `--yolo`, autoaprobación o un prompt como sustituto de una política efectiva.
- Ejecutar mantenimiento real, acceder a secretos no autorizados o modificar el host.
- Aplicar staging al checkout del operador ni crear publicaciones desde el scheduler.
- Reescribir `v7.1.0`, planes históricos o evidencia para ocultar un fallo.

### Success Criteria

1. Los seis módulos cumplen sus criterios sobre una misma revisión final.
2. Ningún subagente recibe secretos, herramientas o efectos no autorizados por su política.
3. Cursor B/C y los recorridos Pi/Cursor con modelo son reales y reproducibles, o el cierre permanece NO-GO.
4. Un DAG con dependencias produce un staging acumulativo y un manifest final coherente.
5. Lectores y escritores cierran únicamente con evidencia y aceptación verificadas.
6. Contenido vacío/incorrecto, scopes violados, resultados inválidos y verificadores omitidos impiden el cierre.
7. La release patch contiene tarball y checksum, su atestación verifica y ambos smokes públicos pasan.
8. `make validate`, `make test`, `make smoke`, typecheck y lint están verdes.
9. `make validate-harnesses` y `make e2e-orchestration` están verdes sin requisitos `not_run`.
10. Catálogo 17, documentación, diagramas, estado y evidencia no presentan contradicciones.
11. No hay publicación, mutación de host ni operación externa sin autorización específica.

### Open Questions

Ninguna arquitectónica. La disponibilidad de credenciales/modelos, la modificación de CI y la publicación son puertas operativas, no decisiones abiertas ni motivos para relajar la aceptación.

## SPEC: `execution-isolation`

### Objective

Convertir el mínimo privilegio en una propiedad ejecutable del proceso hijo, no en una instrucción del prompt. Ambos adaptadores deben compartir la misma política de entorno, herramientas, efectos, cancelación y evidencia.

### Interfaces and Structure

- Una política inmutable derivada de `OpSpec`, task packet y `RunContext`, calculada antes de lanzar el proceso.
- Entorno deny-by-default: solo variables no sensibles necesarias y credenciales nombradas por una ejecución nativa expresamente autorizada.
- La política nunca registra valores de credenciales; cualquier digest se calcula sobre nombres y configuración no secreta.
- Herramientas de lectura para tareas sin escritura; `write`/`edit` solo dentro de `write_scope` para escritores.
- Shell arbitrario deshabilitado en subagentes por defecto. Los comandos de verificación se ejecutan fuera del worker mediante operaciones registradas.
- Cursor no usará `--force`, `--yolo` ni equivalentes. Si el modo headless soportado no puede escribir sin autoaprobación, la capacidad queda `blocked`.
- Pi y Cursor conservan grupo de procesos, timeout, cancelación, límites de salida, redacción y reconciliación.
- Un artefacto de política por tarea registra harness, versión, herramientas, scopes, flags y digest sin valores sensibles.

### Commands

```bash
uv run --project tools --frozen pytest tools/harness/tests tools/orchestrator/tests -q
npm run typecheck
make validate
```

### Code Style

Política común y funciones puras; adaptadores delgados; listas ordenadas para salida determinista; ninguna mutación global de `os.environ`; flags nativos comprobados contra documentación vigente antes de usarse.

### Testing Strategy

- Variables sensibles presentes en el padre no llegan al hijo sin autorización.
- Credenciales explícitamente permitidas llegan sin aparecer en logs, prompts, artefactos ni evidencia.
- Lectores no reciben escritura; escritores no reciben shell arbitrario.
- Intentos fuera de scope no producen evidencia válida ni modifican staging.
- Deny/ask no ejecutan efectos; timeout/cancelación matan el grupo y exigen reconciliación.
- Los flags prohibidos no aparecen en ningún argv de aceptación.

### Boundaries

No se instalarán binarios ni se accederá al almacén real de credenciales sin autorización. No se afirmará sandbox de seguridad si solo existe aislamiento de archivos; las limitaciones se reportarán explícitamente.

### Success Criteria

- La política efectiva es idéntica en intención para Pi y Cursor y observable en evidencia.
- Ningún test de aceptación necesita elevar permisos para pasar.
- Un worker no puede convertir una tarea read-only en escritora ni ampliar scopes.
- Toda terminación deja estado y procesos reconciliables.

### Open Questions

Ninguna. Si un harness no soporta la restricción requerida, el resultado es `blocked`.

## SPEC: `orchestration-integrity`

### Objective

Hacer que un run produzca una integración acumulativa verificada y que todas las tareas —incluidas las read-only— cierren por evidencia real, sin confundir éxito del worker con aceptación del plan.

### Interfaces and Structure

- Un workspace de run posee una raíz temporal, writers por tarea y **un único staging** creado desde `base_revision`.
- El scheduler sigue siendo neutral; el workspace compartido se inyecta en el wrapper de worktrees y su ciclo de vida queda acotado al run.
- Cada writer genera patch binario y manifest; la integración aplica el patch al staging compartido bajo lock cuando sus dependencias ya cerraron.
- La integración conserva orden topológico, impide solapes y serializa apply + verificación para evitar lecturas concurrentes de staging.
- Tras un fallo, el staging debe restaurar el digest previo antes de continuar tareas independientes; los dependientes quedan bloqueados.
- Cada tarea conserva patch, manifest, política, verificaciones y receipt. Al final se escribe un manifest integrado con archivos, hashes, orden aplicado y digest del staging.
- El `output_digest` del checkout sigue protegiendo contra cambios del workspace real; el digest de staging se almacena en la verificación/manifest y queda cubierto por hashes de artefactos.
- Las tareas read-only atraviesan `verify_and_store` con un artefacto derivado del resultado real del adaptador y un verificador resuelto; nunca se fabrica otro resultado para simular ejecución.
- Los identificadores de `verification` se resuelven contra un catálogo permitido. Un ID desconocido o una verificación ausente falla antes de ejecutar la tarea.
- El verificador por defecto comprueba aceptación y contenido esperado; la mera existencia de una ruta no es suficiente.
- `--plan PATH` carga y valida exactamente ese plan. En dry-run no escribe; en ejecución exige que el plan activo coincida o lo activa explícitamente, rechazando conflictos con otro plan activo.

### Commands

```bash
bash scripts/tests/test_orchestration_core.sh
uv run --project tools --frozen pytest tools/orchestrator/tests tools/execution/tests tools/workspace-router/tests -q
uv run --project tools --frozen python tools/orchestrator/run.py --repo . --plan tasks/plan-autoworkspace-remediation.md --adapter pi --dry-run --json
```

### Code Style

Inyección explícita del workspace, locks estrechos, manifests ordenados y funciones sin efectos ocultos. El adaptador conoce procesos; el wrapper conoce integración; el scheduler conoce DAG; la evidencia conoce persistencia.

### Testing Strategy

- Tarea dependiente lee el artefacto integrado por su dependencia.
- Dos writers independientes y disjuntos aparecen juntos en el staging final.
- Solape, patch vacío, contenido incorrecto o verificador desconocido impiden el cierre.
- Un fallo de verificación restaura staging y bloquea dependientes.
- Read-only completa con evidencia; un resultado sin evidencia no completa.
- Resume no repite succeeded y reconstruye staging desde manifests/patches verificados.
- Cambio de plan, patch, base o digest invalida la evidencia afectada.
- Dry-run no cambia bytes; `--plan` nunca es ignorado.

### Boundaries

Sin commits, pushes, merges, publicación ni aplicación al checkout real. No se ejecutarán comandos arbitrarios desde campos Markdown/YAML. Los comandos de test permitidos pertenecen a operaciones registradas.

### Success Criteria

- El manifest final representa todos y solo los patches aceptados.
- El resultado integrado supera verificación final, no solo verificaciones aisladas por tarea.
- Ninguna tarea dependiente observa un estado anterior a sus dependencias.
- Reanudación y replay conservan idempotencia y evidencia.

### Open Questions

Ninguna.

## SPEC: `cursor-native-proof`

### Objective

Demostrar Cursor B/C y el recorrido headless con el comportamiento real de Cursor, separándolo de la instalación estática y sin autoaprobación.

### Interfaces and Structure

- Nivel A conserva manifiestos, rutas, links y versiones; no contribuye por sí solo a B/C.
- Nivel B usa una interfaz nativa documentada o un recorrido Cursor controlado que demuestre carga/efecto de skills, reglas, agents y hooks.
- Las pruebas B deben fallar si un componente está ausente, corrupto o no cargado aunque su ruta siga existiendo.
- Nivel C hace que Cursor intente acciones benignas allow/deny/ask y observa efectos y hooks. El test no invoca `shell_gate.py` directamente ni escribe él mismo los sentinels.
- Allow crea únicamente el sentinel permitido; deny no actúa; ask permanece sin efecto hasta decisión o timeout.
- El recorrido de orquestación usa `CursorSubagentAdapter`, worktree, staging compartido, verificador independiente y evidencia, sin `--force`/`--yolo`.
- El informe registra versión, binario, modo headless/IDE, comandos redactados, checks A/B/C y causas `blocked/not_run`.

### Commands

```bash
agent --version
bash scripts/tests/test_cursor_native.sh
bash scripts/tests/test_cursor_orchestration.sh
make validate-harnesses
make e2e-orchestration
```

### Code Style

Sondas pequeñas con una capacidad por check; ninguna afirmación nativa derivada de filesystem estático; timeouts y salida JSON redactada; documentación oficial consultada antes de fijar flags.

### Testing Strategy

- Descubrimiento positivo y negativo con recursos ausentes/corruptos.
- Allow/deny/ask con sentinels independientes y comprobación posterior.
- Worker escribe el fixture exacto; verifier no implementa ni publica.
- Tool denegada, autenticación ausente, salida inválida, timeout y cancelación no producen PASS.
- IDE asistido y headless se reportan como capacidades distintas.

### Boundaries

Sin instalación de Cursor, credenciales, modelo o coste sin autorización. Si no existe una interfaz nativa capaz de demostrar B/C o escritura sin autoaprobación, el cierre queda bloqueado.

### Success Criteria

- B y C proceden de observaciones nativas y sus defectos sembrados rompen el check.
- Cursor completa el mismo recorrido que Pi sin elevar permisos.
- La evidencia demuestra artefacto integrado, política, versión y ausencia de procesos residuales.

### Open Questions

Ninguna arquitectónica; la mecánica nativa concreta se selecciona tras consultar documentación vigente.

## SPEC: `pi-native-proof`

### Objective

Cerrar el recorrido Pi real sobre el núcleo remediado y mantener la distribución Git pineada, sin confundir RPC sin modelo con aceptación de subagentes.

### Interfaces and Structure

- `PiSubagentAdapter` consume la política común, contexto aislado y herramientas mínimas.
- RPC `get_commands` demuestra paquete y extensión cargados; no cuenta como prueba con modelo.
- El recorrido real escribe en writer, integra en staging compartido, verifica contenido y persiste evidencia.
- La ejecución registra paquete, tag/ref, versión Pi, modelo seleccionado sin secretos, run, tarea, herramientas y artefactos.
- La autenticación se comprueba antes del run; ausencia de binario/modelo produce `not_run` o `blocked` según el contrato del doctor.

### Commands

```bash
bash scripts/tests/test_pi_native.sh
bash scripts/tests/test_pi_orchestration.sh
make e2e-orchestration
```

### Code Style

JSONL estricto, proceso sin shell, salida acotada, selección explícita de skill/modelo y prompts temporales privados con limpieza garantizada.

### Testing Strategy

- Recorrido real con contenido exacto y verificación independiente.
- Herramienta denegada, modelo con error, JSON inválido/truncado, timeout y cancelación.
- Ningún proceso hijo residual y ningún archivo aplicado al checkout de origen.
- Install/reinstall/uninstall local preserva recursos ajenos.
- Smoke entre tags queda enlazado a `release-recovery`, no se marca antes de ejecutarlo.

### Boundaries

Sin modelo/coste/credenciales sin autorización; sin refs flotantes ni escritura en settings reales durante pruebas.

### Success Criteria

- Pi completa el recorrido real mediante el núcleo compartido.
- Las restricciones y la evidencia son efectivas, no solo texto del prompt.
- La ausencia de cualquier requisito mantiene el cierre bloqueado.

### Open Questions

Ninguna.

## SPEC: `release-recovery`

### Objective

Restaurar una distribución pública verificable mediante una release patch nueva y hacer que la ausencia de assets o de smoke impida el cierre.

### Interfaces and Structure

- Revisar mediante MCP GitHub los logs del run de `v7.1.0` y registrar la causa de `assets: []`; cualquier rerun externo requiere autorización.
- Mantener `v7.1.0` inmutable y preparar `v7.1.1` como PATCH por corregir comportamiento ya prometido, conforme a ADR-0010.
- El workflow produce archivo → checksum → atestación → upload y falla si falta cualquier entregable.
- Una puerta post-release descarga los assets exactos, verifica checksum y atestación, instala en destinos temporales y ejecuta doctor.
- El smoke Pi instala desde `v7.1.0` y actualiza explícitamente al nuevo tag, comprobando el catálogo y la extensión.
- El smoke Cursor usa bootstrap con plugin/componentes completos y doctor, sin afirmar B/C si no ejecuta esas sondas.
- Release readiness y publicación permanecen separadas; un release creado sin smoke no es cierre GO.
- CI pública conserva PRs sin secretos. Las pruebas con modelo se documentan/ejecutan en un entorno controlado y su ausencia bloquea release readiness.

### Commands

```bash
bash scripts/tests/test_bootstrap.sh
uv run --project tools --frozen python tools/validate/release_coherence.py --release-gate
uv run --project tools --frozen pytest tools/validate/tests/test_release_assets.py tools/harness/tests/test_bootstrap.py -q
make validate-harnesses
make e2e-orchestration
```

Tras publicación autorizada, los comandos concretos de descarga/verificación se registrarán con el tag real y la identidad observada; no se inventará evidencia anticipada.

### Code Style

Acciones pineadas, permisos mínimos, temporales privados, assets sin `--clobber`, extracción confinada y diagnósticos accionables. Cambios de workflows condicionados a aprobación previa.

### Testing Strategy

- Release fixture sin tarball/checksum/attestation falla readiness.
- Digest distinto, tag incorrecto, tar hostil, doctor negativo y fallo de upload impiden PASS.
- Smoke público demuestra los assets reales y la actualización pineada.
- Se conserva evidencia de la release fallida actual sin reescribirla.

### Boundaries

Ningún tag, release, rerun, push o upload se ejecuta por esta especificación. Nunca se mueve `v7.1.0` ni se usan credenciales de modelo en PRs públicos.

### Success Criteria

- La nueva release contiene los assets esperados y su atestación verifica contra tag/commit correctos.
- Bootstrap Pi/Cursor y actualización Git Pi pasan contra URLs públicas.
- Toda puerta nativa previa está verde sobre la misma identidad de release.
- La documentación distingue instalación, soporte nativo y publicación verificada.

### Open Questions

Ninguna. La causa del fallo histórico es evidencia pendiente de leer, no una cuestión que cambie el diseño.

## SPEC: `canon-reconciliation`

### Objective

Cerrar la deriva entre implementación, documentación y estado sin reescribir la historia ni elevar afirmaciones por encima de la evidencia.

### Interfaces and Structure

- `AGENTS.md`, `docs/TAXONOMY.md` y el diagrama D01 reflejan 17 skills; el índice y snapshot se generan desde el catálogo.
- `README.md` y `docs/harness-setup.md` enlazan la release real y describen únicamente capacidades verificadas.
- `.autoworkspace/status.yaml` activa este plan por ruta/digest durante IMPLEMENT y conserva tasks, receipts e historial; no infiere planes históricos.
- `.autoworkspace/SPEC.md` y otros documentos antiguos se tratan como historia, no como fuente del incremento; cualquier migración/archivo preservará el contenido histórico.
- Este documento recibe un registro final por módulo: fuente, implementación, comando, identidad, estado y desviación.
- `project-autoworkspace` mantiene routing y handoffs sin publicación automática; sus fixtures de deriva deben romper los checks esperados.
- La revisión independiente es read-only y contrasta DoD, evidencia, assets y ausencia de requisitos `not_run`.

### Commands

```bash
make validate
make smoke
uv run --project tools --frozen python tools/skill-index/generate.py --check --root .
uv run --project tools --frozen python tools/workspace-router/run.py --status --repo . --json
uv run --project tools --frozen python tools/harness/doctor.py --harness all --json
npm run lint
```

### Code Style

Enlaces a fuentes canónicas en lugar de copias, español/inglés según `docs/GLOSARIO.md`, tablas de evidencia completas y cambios documentales mínimos.

### Testing Strategy

- Una skill ausente/extra rompe índice/snapshot.
- Texto 16 en superficies vivas se detecta y corrige sin alterar changelog/historial.
- Routing positivo/negativo de `project-autoworkspace` no invoca publicación.
- Estado con digest cambiado o plan histórico no reanuda trabajo.
- Revisión final detecta cualquier criterio sin evidencia o con identidad distinta.

### Boundaries

No se reescriben planes, releases ni evidencia histórica. La revisión no autoriza implementación, commits ni publicación. La limpieza de ramas remotas permanece como operación separada.

### Success Criteria

- Todas las superficies vivas describen el mismo catálogo y la misma versión publicada.
- El estado declarativo permite auditar plan, tareas y receipts sin contradicciones.
- El informe final registra alcance, limitaciones y siguiente acción externa.
- GO solo si no queda ningún criterio obligatorio `fail`, `blocked` o `not_run`.

### Open Questions

Ninguna.

## Criterios globales de aceptación de las especificaciones

- [x] El operador aprueba la especificación transversal y los seis módulos.
- [x] El operador acepta que las pruebas nativas y la publicación conserven autorizaciones separadas.
- [x] El operador acepta la estrategia de staging compartido, verificadores permitidos y evidencia read-only.
- [x] El operador acepta una release patch nueva sin modificar `v7.1.0`.
- [x] El operador confirma que no quedan preguntas arquitectónicas abiertas.

# Fase 2 — Plan técnico

## Overview

La remediación se ejecutará como cortes verticales sobre el sistema existente. Primero se fijarán las pruebas que reproducen los falsos PASS y las pérdidas de integración; después se compartirá una política de procesos y un workspace de run. Los adaptadores nativos se conectarán únicamente cuando el núcleo demuestre aislamiento, integración acumulativa, evidencia read-only y reanudación.

La publicación será el último eslabón y permanecerá fuera del scheduler. Las pruebas nativas tendrán opt-in explícito, mientras `make validate` conservará un carril determinista sin credenciales. Ninguna tarea cerrará por una simulación cuando el criterio exija un harness real.

## Architecture Decisions

### AD-01 — Política de ejecución común y deny-by-default

Un módulo interno de `tools/harness/` producirá una política inmutable a partir de `OpSpec`, tarea y contexto. La política resolverá entorno, herramientas, flags prohibidos, cwd, timeout y scopes antes de crear el proceso.

El entorno hijo se construirá desde cero con variables operativas no sensibles. Las credenciales solo se transmitirán cuando una ejecución nativa autorizada declare sus nombres; sus valores nunca formarán parte de prompts, manifests, logs ni digests. Los workers no recibirán shell arbitrario por defecto.

### AD-02 — Workspace compartido por run, no por tarea

`WorktreeManager` evolucionará internamente hacia un workspace de run con un staging único y writers independientes. El wrapper de worktrees recibirá ese workspace por inyección; el scheduler seguirá sin conocer Git ni APIs de harness.

Un lock acotado cubrirá apply + verificación + actualización del manifest. Las dependencias se completan antes de integrar dependientes; los independientes pueden ejecutarse en paralelo, pero la integración será serializada y topológica.

### AD-03 — Integración transaccional y reanudable

Antes de cada apply se registrará el digest del staging. Un fallo de apply o verificación impedirá el cierre; para continuar independientes será obligatorio restaurar y comprobar el digest previo. No se usará `reset --hard` ni se tocará el checkout real.

Los patches/manifests aceptados vivirán bajo `.autoworkspace/runs/<run_id>/`. Al reanudar, el staging se reconstruirá desde la base aplicando únicamente artefactos válidos en el orden registrado. El manifest final incluirá orden, archivos, hashes y digest agregado.

### AD-04 — Evidencia común para lectores y escritores

Todo resultado real del adaptador pasará por `verify_and_store`. Para tareas read-only, el coordinador guardará un resultado normalizado y redactado como artefacto; no creará un `OpResult` sustituto ni omitirá el verificador.

El `output_digest` seguirá ligando el checkout real. El digest del staging viajará en verificaciones y manifests protegidos por hash, evitando un cambio incompatible de los schemas actuales. La evidencia legacy seguirá siendo legible, pero no válida para este plan nuevo.

### AD-05 — Verificadores permitidos, no comandos del plan

Los IDs de `verification` se resolverán contra un catálogo interno. Cada verificador recibirá el resultado real y el staging, y devolverá los `kind` exigidos por `OpSpec` junto con evidencia de aceptación.

No habrá un fallback de «la ruta existe». Unknown IDs, lista vacía, contenido incorrecto o ausencia de verificación fallarán antes de delegar. Los comandos de tests se ejecutarán mediante operaciones registradas, nunca como shell libre proporcionado por Markdown/YAML.

### AD-06 — Aceptación nativa con opt-in explícito

`make validate` no invocará modelos. Los recorridos con modelo exigirán una variable de opt-in y la configuración mínima documentada; sin ella terminarán `not_run`/exit 3 antes de crear worktrees o procesos de modelo.

Cursor B/C deberá observar acciones del propio CLI. Filesystem estático y llamadas directas a hooks se reclasificarán como nivel A/unitario. No se utilizará `--force`, `--yolo` ni autoaprobación. Si Cursor no ofrece un carril compatible, la evidencia será `blocked` y no habrá release GO.

### AD-07 — Release patch y smoke post-release obligatorio

La ausencia de assets de `v7.1.0` se diagnosticará mediante MCP GitHub sin reescribir la release. La corrección preparará `v7.1.1` por restaurar contratos existentes, conforme a ADR-0010.

El workflow conservará permisos mínimos y añadirá una puerta post-release sin modelos para descargar, verificar e instalar los assets reales. La readiness local agregará las puertas nativas; la publicación externa seguirá requiriendo autorización específica.

### AD-08 — Canon generado y cierre independiente

El índice y snapshot seguirán generándose desde `skills/`. Los textos vivos se corregirán a 17 sin tocar historial. El estado activará este plan por ruta/digest y conservará receipts.

El informe final será una tabla por capacidad con comando, identidad, estado y desviación. La revisión independiente read-only no podrá convertir ausencia de evidencia en PASS ni ejecutar publicación.

## Componentes y cambios por módulo

| Module id                 | Componentes principales                                                                          | Pruebas y evidencia                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `execution-isolation`     | Política común; builders de entorno/argv; adaptadores Pi/Cursor; artefacto de política           | Unitarias de política, procesos fixture, adversarias de secretos/tools/flags |
| `orchestration-integrity` | Workspace de run; staging único; lock; manifests; verificadores; read-only; resume; CLI `--plan` | Integración DAG, rollback, reconstrucción, manifest final y E2E público      |
| `cursor-native-proof`     | Sondas B/C; hooks observados; adaptador headless; script nativo                                  | Cursor real, sentinels nativos, defectos sembrados y recorrido con modelo    |
| `pi-native-proof`         | Adaptador Pi; JSONL; auth preflight; script de orquestación                                      | Pi real, paquete/RPC, escritura/integración/evidencia y limpieza             |
| `release-recovery`        | Release workflow; readiness; bootstrap; runbook/smoke público                                    | Fixtures adversarias, assets/attestation reales y actualización entre tags   |
| `canon-reconciliation`    | AGENTS/taxonomía/diagrama/docs; plan activo; registro final; autoauditoría                       | Gates de canon, routing, estado, revisión independiente y DoD                |

## Secuencia de implementación

### Wave 0 — Baseline, reproducción y viabilidad

1. Registrar identidad `68c1dc9`, árbol, versiones y gates heredados sin convertirlos en evidencia final.
2. Añadir reproducciones RED para entorno heredado, flags prohibidos, staging no acumulativo, read-only sin evidencia, verificador por existencia y Cursor B/C estático.
3. Consultar documentación Cursor/Pi vigente y revisar por MCP GitHub el fallo de assets de `v7.1.0`.
4. Activar el plan únicamente cuando el bloque `aw-plan` esté aprobado; no inferir actividad desde documentos antiguos.

Si Cursor no ofrece el boundary requerido, se conservarán los carriles independientes, pero el cierre integral quedará bloqueado antes de invertir en una falsa integración.

### Wave 1 — Política y aislamiento

1. Implementar la política común y los tests de entorno/herramientas.
2. Aplicarla a Pi y Cursor, retirando autoaprobación y shell arbitrario.
3. Verificar cancelación, timeout, redacción, artefacto de política y ausencia de procesos residuales.

El checkpoint exige que los defectos sembrados rompan las puertas y que los tests deterministas existentes sigan verdes.

### Wave 2 — Integridad del orquestador

1. Introducir workspace/staging de run e integración transaccional.
2. Añadir verificadores permitidos y evidencia read-only.
3. Implementar manifest final, reconstrucción en resume y semántica real de `--plan`.
4. Demostrar un recorrido con dependencias, writers disjuntos, lector, fallo/rollback y reanudación.

Los cambios de `runner.py`, `worktrees.py`, `scheduler.py` y `run.py` se secuencian por un único integrador para evitar contratos divergentes.

### Wave 3 — Pruebas nativas Pi y Cursor

1. Completar Pi con modelo sobre el núcleo común.
2. Sustituir Cursor B/C por sondas reales y completar su recorrido sin elevar permisos.
3. Registrar versiones, modelos redactados, políticas, artefactos y procesos.

Estos carriles pueden solaparse solo con archivos separados y autorización de modelos/coste. Un `not_run` de cualquiera impide pasar a release GO, aunque permite preparar fixtures de distribución no publicables.

### Wave 4 — Distribución y release readiness

1. Corregir la cadena archive/checksum/attestation/upload según la causa observada.
2. Añadir readiness agregada y smoke post-release sin modelos.
3. Ejecutar fixtures adversarias, gates deterministas y nativas sobre la identidad candidata.
4. Preparar changelog/manifests/documentación para `v7.1.1` sin crear tag ni release.

### Wave 5 — Canon y revisión final

1. Corregir textos vivos, diagrama, estado y referencias de instalación.
2. Actualizar el registro de ejecución y evidencia por módulo sobre el HEAD final.
3. Realizar revisión independiente y emitir GO/NO-GO con IDs concretos.
4. Entregar cualquier acción de publicación como paso separado y expresamente autorizado.

## Paralelismo y propiedad de archivos

| Superficie                           | Propiedad/coordinación                                                      |
| ------------------------------------ | --------------------------------------------------------------------------- |
| Política y adaptadores Pi/Cursor     | Un escritor por harness; contrato común cerrado antes de paralelizar        |
| `tools/orchestrator/`                | Un integrador secuencial durante Wave 2                                     |
| Scripts Pi/Cursor                    | Paralelizable tras estabilizar adaptadores; ningún writer comparte worktree |
| Workflows/release                    | Secuencial y sujeto a aprobación de CI                                      |
| Plan, status, README y documentación | Un único escritor para evitar divergencia de canon                          |
| Pruebas nativas                      | Secuenciales si comparten credenciales, modelo, HOME o recursos temporales  |

La delegación no concede permisos adicionales. Antes de cada tarea se reevaluarán `role-back`, `role-clean-code` y `plan-validators`; no se invocarán `role-front` ni `role-design` porque no existe superficie UI/visual.

## Migraciones y compatibilidad

1. **Schemas:** se conservan las versiones actuales. Nuevos datos viajan en artefactos/manifests/verificaciones existentes; si hace falta un cambio incompatible se detiene la tarea y se replantea SemVer.
2. **Estado:** se usa schema 2 y `activate_plan`; no se infiere ni reescribe un plan histórico. El cambio de digest exige revalidación.
3. **Evidencia:** documentos antiguos permanecen disponibles, pero no completan tareas del nuevo `plan_id`.
4. **CLI:** `--plan` pasa de ignorado a validado/aplicado; es una corrección del comportamiento documentado. Dry-run sigue sin escrituras.
5. **Adaptadores:** la política más restrictiva puede exigir configuración explícita de credenciales para pruebas autorizadas; se documentará sin persistir secretos.
6. **Recursos ajenos:** instaladores, uninstall y worktrees preservan cualquier recurso fuera de manifests propios.
7. **Release:** `v7.1.0` queda inmutable y marcado como distribución incompleta en la evidencia; no se mueve su tag.
8. **Historial:** `CHANGELOG.md`, planes anteriores y snapshots históricos no se reescriben para ocultar el fallo.

## Verification Checkpoints

### CP0 — Baseline y viabilidad

- [ ] Identidad, árbol y gates iniciales registrados.
- [ ] Cada defecto auditado tiene una reproducción RED por la causa esperada.
- [ ] Cursor/Pi y release failure tienen evidencia de viabilidad/causa sin falsos PASS.

### CP1 — Execution isolation

- [ ] Entorno, herramientas, scopes y flags efectivos están probados.
- [ ] Ningún recorrido contiene autoaprobación ni secretos no autorizados.
- [ ] Timeout/cancelación no dejan procesos ni cierres falsos.

### CP2 — Orchestration integrity

- [ ] Staging acumulativo, rollback, read-only y verificadores pasan integración.
- [ ] Resume reconstruye el mismo manifest sin repetir tareas exitosas.
- [ ] `--plan` y dry-run cumplen su contrato sin escrituras indebidas.

### CP3 — Native acceptance

- [ ] Pi completa el recorrido real y limpio.
- [ ] Cursor B/C y orquestación pasan mediante Cursor real, sin `--force`.
- [ ] Toda evidencia corresponde a la misma revisión y no contiene `not_run` obligatorio.

### CP4 — Release readiness

- [ ] `make validate`, `make test`, `make smoke`, typecheck y lint están verdes.
- [ ] `make validate-harnesses` y `make e2e-orchestration` están verdes.
- [ ] Fixtures de release/bootstrap y validadores sembrados detectan los fallos esperados.
- [ ] Versión, changelog y documentación candidata son coherentes sin publicar.

### CP5 — Public distribution

- [ ] Tras autorización, la release patch contiene assets y atestación válidos.
- [ ] Bootstrap Pi/Cursor y actualización Git Pi pasan contra la release pública.
- [ ] La evidencia pública corresponde al mismo commit/tag candidato.

### CP6 — Canon and independent closure

- [ ] Catálogo 17, documentación, diagramas y estado están alineados.
- [ ] Todos los módulos y criterios tienen evidencia final trazable.
- [ ] Revisión independiente emite GO solo sin fail/blocked/not_run obligatorio.
- [ ] Publicación y cualquier operación posterior permanecen separadas del scheduler.

## Risks and Mitigations

| Risk                                                             | Impact               | Mitigation                                                                       |
| ---------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------- |
| Cursor no permite escritura headless sin autoaprobación          | Alto; bloquea cierre | Spike temprano, documentación vigente, `blocked` explícito; nunca `--force`      |
| Sondas nativas vuelven a medir archivos en vez de comportamiento | Alto                 | Defectos sembrados por componente y observación de acciones reales               |
| Writers paralelos corrompen staging                              | Alto                 | Staging único, lock apply+verify, scopes disjuntos y digest previo/posterior     |
| Resume acepta patches stale                                      | Alto                 | Bindings base/plan/task/run, hashes y reconstrucción solo desde evidencia válida |
| Read-only o verificadores genéricos producen falsos cierres      | Alto                 | Evidencia común, catálogo permitido y rechazo de existencia como criterio único  |
| Credenciales se filtran a logs/manifests                         | Alto                 | Entorno deny-by-default, nombres sin valores, redacción y escaneo de fixtures    |
| Tests nativos tienen coste o efectos inesperados                 | Alto                 | Opt-in, fixtures, timeout, procesos confinados y autorización separada           |
| Release vuelve a crearse sin assets                              | Alto                 | Puerta post-release, smoke obligatorio y NO-GO hasta evidencia pública           |
| Cambios de schema/CI rompen compatibilidad                       | Medio                | Reutilizar contratos; aprobación y migración antes de cualquier cambio           |
| Documentación declara capacidades no demostradas                 | Medio                | Revisión independiente y tabla por identidad/comando/estado                      |

## Open Questions

Ninguna. Las limitaciones nativas se resolverán como evidencia de viabilidad; no se rebajará el criterio para eliminar un bloqueo.

## Criterios de aceptación del plan técnico

- [x] El operador aprueba las ocho decisiones de arquitectura y los componentes.
- [x] El operador aprueba waves, checkpoints, paralelismo y propiedad de archivos.
- [x] El operador acepta las migraciones y la conservación de schemas actuales.
- [x] El operador acepta los riesgos y la estrategia de mitigación.

# Fase 3 — Desglose de tareas

## Contrato estructurado `aw-plan`

El siguiente bloque es la única entrada estructurada de tareas. La narrativa posterior define su detalle y evidencia exigida; no existen otros trackers.

```yaml aw-plan
schema_version: 1
plan_id: autoworkspace-remediation-v1
base_revision: "68c1dc90f8d5edfe4ca011f585de95dce95e6e32"
tasks:
  - id: baseline-identity
    phase: DEFINE
    operation: specify
    roles: [role-clean-code]
    depends_on: []
    read_scope: [README.md, tasks/plan-autoworkspace-remediation.md]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [baseline-report]
    acceptance: [baseline-recorded]
    verification: [document-review]
    on_failure: stop
  - id: red-execution-isolation
    phase: SCHEMAS
    operation: schema_write
    roles: [role-back]
    depends_on: [baseline-identity]
    read_scope: [tools/harness/pi.py, tools/harness/cursor.py]
    write_scope: [tools/harness/tests/]
    artifacts: [isolation-red-tests]
    acceptance: [isolation-defects-reproduced]
    verification: [pytest-harness-policy]
    on_failure: stop
  - id: red-orchestration-integrity
    phase: SCHEMAS
    operation: schema_write
    roles: [role-back]
    depends_on: [baseline-identity]
    read_scope: [tools/orchestrator/]
    write_scope: [tools/orchestrator/tests/]
    artifacts: [orchestration-red-tests]
    acceptance: [orchestration-defects-reproduced]
    verification: [pytest-orchestrator]
    on_failure: stop
  - id: native-release-feasibility
    phase: DEFINE
    operation: specify
    roles: [role-back]
    depends_on: [baseline-identity]
    read_scope: [tools/harness/, .github/workflows/release.yml]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [feasibility-report]
    acceptance: [native-and-release-causes-recorded]
    verification: [document-review]
    on_failure: stop
  - id: execution-policy
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back, role-clean-code]
    depends_on: [red-execution-isolation]
    read_scope:
      [
        tools/execution/registry.yaml,
        tools/execution/ops.py,
        tools/orchestrator/model.py,
      ]
    write_scope: [tools/harness/policy.py, tools/harness/tests/test_policy.py]
    artifacts: [execution-policy]
    acceptance: [deny-by-default-policy]
    verification: [pytest-harness-policy]
    on_failure: stop
  - id: pi-isolation
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [execution-policy]
    read_scope: [tools/harness/policy.py, tools/harness/pi.py]
    write_scope: [tools/harness/pi.py, tools/harness/tests/test_pi_subagent.py]
    artifacts: [pi-policy-adapter]
    acceptance: [pi-policy-enforced]
    verification: [pytest-harness-policy]
    on_failure: stop
  - id: cursor-isolation
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [execution-policy]
    read_scope: [tools/harness/policy.py, tools/harness/cursor.py]
    write_scope:
      [tools/harness/cursor.py, tools/harness/tests/test_cursor_native.py]
    artifacts: [cursor-policy-adapter]
    acceptance: [cursor-policy-enforced]
    verification: [pytest-harness-policy]
    on_failure: stop
  - id: run-staging
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back, role-clean-code]
    depends_on: [red-orchestration-integrity, execution-policy]
    read_scope: [tools/orchestrator/worktrees.py, tools/orchestrator/runner.py]
    write_scope:
      [
        tools/orchestrator/worktrees.py,
        tools/orchestrator/runner.py,
        tools/orchestrator/tests/test_worktrees.py,
        tools/orchestrator/tests/test_full_flow.py,
      ]
    artifacts: [shared-staging]
    acceptance: [cumulative-transactional-staging]
    verification: [pytest-orchestrator]
    on_failure: stop
  - id: verifier-evidence
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [run-staging]
    read_scope:
      [
        tools/orchestrator/runner.py,
        tools/orchestrator/run.py,
        tools/execution/ops.py,
      ]
    write_scope:
      [
        tools/orchestrator/verifiers.py,
        tools/orchestrator/runner.py,
        tools/orchestrator/run.py,
        tools/orchestrator/tests/test_full_flow.py,
      ]
    artifacts: [verifier-catalog, readonly-evidence]
    acceptance: [explicit-verification-and-readonly-evidence]
    verification: [pytest-orchestrator]
    on_failure: stop
  - id: resume-manifest
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [verifier-evidence]
    read_scope: [tools/orchestrator/, tools/execution/evidence.py]
    write_scope:
      [
        tools/orchestrator/worktrees.py,
        tools/orchestrator/runner.py,
        tools/orchestrator/tests/test_scheduler.py,
        tools/orchestrator/tests/test_full_flow.py,
      ]
    artifacts: [resume-manifest]
    acceptance: [reconstructible-final-manifest]
    verification: [pytest-orchestrator]
    on_failure: stop
  - id: plan-cli-core-e2e
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [resume-manifest]
    read_scope: [tools/orchestrator/run.py, tools/orchestrator/scheduler.py]
    write_scope:
      [
        tools/orchestrator/run.py,
        tools/orchestrator/scheduler.py,
        scripts/tests/test_orchestration_core.sh,
      ]
    artifacts: [plan-cli-core-e2e]
    acceptance: [plan-and-dry-run-contract]
    verification: [pytest-orchestrator]
    on_failure: stop
  - id: native-opt-in
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [pi-isolation, cursor-isolation]
    read_scope:
      [
        Makefile,
        scripts/tests/test_pi_orchestration.sh,
        scripts/tests/test_cursor_orchestration.sh,
      ]
    write_scope:
      [
        Makefile,
        scripts/tests/test_pi_orchestration.sh,
        scripts/tests/test_cursor_orchestration.sh,
      ]
    artifacts: [native-opt-in]
    acceptance: [native-runs-require-explicit-opt-in]
    verification: [native-gate-contract]
    on_failure: stop
  - id: cursor-native-bc
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [native-release-feasibility, cursor-isolation, native-opt-in]
    read_scope: [tools/harness/cursor.py, .cursor/hooks/]
    write_scope:
      [
        tools/harness/cursor.py,
        tools/harness/tests/test_cursor_native.py,
        scripts/tests/test_cursor_native.sh,
      ]
    artifacts: [cursor-native-bc]
    acceptance: [native-discovery-and-policy]
    verification: [native-cursor-bc]
    on_failure: stop
  - id: cursor-native-e2e
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [plan-cli-core-e2e, cursor-native-bc]
    read_scope: [tools/harness/cursor.py, tools/orchestrator/]
    write_scope:
      [
        scripts/tests/test_cursor_orchestration.sh,
        tasks/plan-autoworkspace-remediation.md,
      ]
    artifacts: [cursor-native-evidence]
    acceptance: [cursor-real-flow-without-force]
    verification: [native-cursor-e2e]
    on_failure: stop
  - id: pi-native-e2e
    phase: VALIDATE
    operation: red_green
    roles: [role-back]
    depends_on: [plan-cli-core-e2e, native-opt-in]
    read_scope: [tools/harness/pi.py, tools/orchestrator/]
    write_scope:
      [
        scripts/tests/test_pi_orchestration.sh,
        tasks/plan-autoworkspace-remediation.md,
      ]
    artifacts: [pi-native-evidence]
    acceptance: [pi-real-flow-with-least-privilege]
    verification: [native-pi-e2e]
    on_failure: stop
  - id: release-assets-fix
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [native-release-feasibility, cursor-native-e2e, pi-native-e2e]
    read_scope:
      [.github/workflows/release.yml, tools/validate/release_coherence.py]
    write_scope:
      [
        .github/workflows/release.yml,
        tools/validate/release_coherence.py,
        tools/validate/tests/test_release_assets.py,
      ]
    artifacts: [release-assets-fix]
    acceptance: [release-assets-cannot-be-omitted]
    verification: [release-fixture-gate]
    on_failure: stop
  - id: release-readiness-smoke
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: [release-assets-fix]
    read_scope: [.github/workflows/release.yml, Makefile, scripts/bootstrap.sh]
    write_scope:
      [
        .github/workflows/release.yml,
        Makefile,
        scripts/tests/test_bootstrap.sh,
        docs/harness-setup.md,
      ]
    artifacts: [release-readiness-smoke]
    acceptance: [post-release-smoke-gate]
    verification: [release-fixture-gate]
    on_failure: stop
  - id: full-local-validation
    phase: VALIDATE
    operation: local_gates
    roles: [role-back]
    depends_on: [release-readiness-smoke]
    read_scope:
      [Makefile, package.json, tasks/plan-autoworkspace-remediation.md]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [full-local-gates]
    acceptance: [all-local-gates-same-identity]
    verification: [canonical-local-gates]
    on_failure: stop
  - id: patch-version-changelog
    phase: INTEGRATE
    operation: integrate
    roles: [role-back]
    depends_on: [full-local-validation]
    read_scope: [package.json, tools/pyproject.toml, CHANGELOG.md]
    write_scope:
      [
        package.json,
        package-lock.json,
        tools/pyproject.toml,
        tools/uv.lock,
        CHANGELOG.md,
      ]
    artifacts: [patch-version-changelog]
    acceptance: [patch-version-coherent]
    verification: [release-fixture-gate]
    on_failure: stop
  - id: canon-docs-alignment
    phase: IMPLEMENT
    operation: refactor
    roles: [role-clean-code]
    depends_on: [full-local-validation]
    read_scope: [AGENTS.md, docs/TAXONOMY.md, docs/harness-setup.md]
    write_scope:
      [
        AGENTS.md,
        docs/TAXONOMY.md,
        docs/architecture/diagrams/sources/D01.architecture.json,
        README.md,
        docs/harness-setup.md,
      ]
    artifacts: [canon-docs-17]
    acceptance: [living-canon-consistent]
    verification: [canon-gates]
    on_failure: stop
  - id: prerelease-review
    phase: VALIDATE
    operation: local_gates
    roles: []
    depends_on: [patch-version-changelog, canon-docs-alignment]
    read_scope: [tasks/plan-autoworkspace-remediation.md, .autoworkspace/]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [prerelease-review]
    acceptance: [independent-prerelease-review]
    verification: [independent-plan-review]
    on_failure: stop
  - id: authorized-release-evidence
    phase: INTEGRATE
    operation: integrate
    roles: [role-back]
    depends_on: [prerelease-review]
    read_scope: [tasks/plan-autoworkspace-remediation.md, CHANGELOG.md]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [public-release-record]
    acceptance: [authorized-release-observed]
    verification: [release-public-evidence]
    on_failure: stop
  - id: public-release-smoke
    phase: VALIDATE
    operation: local_gates
    roles: [role-back]
    depends_on: [authorized-release-evidence]
    read_scope: [scripts/tests/, docs/harness-setup.md]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [public-smoke-evidence]
    acceptance: [public-bootstrap-and-pi-upgrade-pass]
    verification: [release-public-smoke]
    on_failure: stop
  - id: final-status-evidence
    phase: STATUS
    operation: status
    roles: [role-back]
    depends_on: [public-release-smoke]
    read_scope:
      [.autoworkspace/status.yaml, tasks/plan-autoworkspace-remediation.md]
    write_scope:
      [.autoworkspace/status.yaml, tasks/plan-autoworkspace-remediation.md]
    artifacts: [final-status-evidence]
    acceptance: [status-and-evidence-reconciled]
    verification: [canon-gates]
    on_failure: stop
  - id: independent-closure
    phase: STATUS
    operation: status
    roles: []
    depends_on: [final-status-evidence]
    read_scope: [tasks/plan-autoworkspace-remediation.md, .autoworkspace/]
    write_scope: [tasks/plan-autoworkspace-remediation.md]
    artifacts: [independent-closure-report]
    acceptance: [independent-go-or-no-go]
    verification: [independent-plan-review]
    on_failure: stop
```

## Reglas de ejecución de las tareas

- T00–T24 se ejecutan por dependencias; cada tarea termina en una sesión focalizada y deja el sistema en un estado verificable.
- Antes de cada acción se reevalúan los roles declarados y `plan-validators`. No hay superficie para `role-front` o `role-design`.
- T01/T02 son tareas RED deliberadas: sus pruebas se incorporan sin relajarlas y pasan tras la corrección correspondiente.
- Las tareas con modelos, credenciales o coste no se ejecutan sin opt-in y autorización específica. Ausencia significa `blocked/not_run`, nunca done.
- Los cambios de workflows en T15/T16 requieren aprobación previa de CI. Ningún schema público se cambia sin replanificar.
- La publicación no es una tarea del scheduler. Después de T20, el operador podrá autorizar `project-publish`; T21 solo registra y valida una release ya existente.
- T21/T22 permanecen bloqueados si no existe una release autorizada con la identidad candidata. El scheduler no puede crearla ni simularla.
- Cada tarea añade al registro final: HEAD/contenido, roles, RED/GREEN, comandos, artefactos, limitaciones y evidencia.
- Ninguna casilla se marca antes de disponer de evidencia sobre la identidad afectada.

## Tasks — Wave 0

### Task T00: Baseline e identidad

**Description:** Registrar revisión base, árbol, versiones y resultados heredados sin presentarlos como evidencia final.

**Acceptance criteria:**

- [x] HEAD `68c1dc9`, rama, árbol y versiones quedan registrados.
- [x] El documento es el único plan activo candidato y no reescribe historial.

**Dependencies:** None.  
**Implementation roles:** `role-clean-code`.  
**Test surfaces:** Identidad Git, estado y estructura documental.  
**Files likely touched:** `tasks/plan-autoworkspace-remediation.md`.  
**Verification:** `git status`, `git rev-parse HEAD`, `make validate`.  
**Estimated scope:** S.

### Task T01: Reproducir fallos de aislamiento

**Description:** Añadir tests RED para entorno heredado, shell arbitrario, scopes y flags de autoaprobación.

**Acceptance criteria:**

- [x] Cada test falla por el defecto esperado, no por setup.
- [x] Secretos fixture y flags prohibidos quedan cubiertos sin valores reales.

**Dependencies:** T00.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Política Pi/Cursor, argv, entorno y cancelación.  
**Files likely touched:** `tools/harness/tests/`.  
**Verification:** pytest focal RED y colección válida.  
**Estimated scope:** M.

### Task T02: Reproducir fallos de orquestación

**Description:** Añadir RED para staging no acumulativo, read-only sin evidencia, verificador por existencia y resume stale.

**Acceptance criteria:**

- [x] Una dependencia demuestra que no recibe el artefacto previo en el código base.
- [x] Read-only, contenido vacío y digest stale tienen regresiones independientes.

**Dependencies:** T00.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Worktrees, runner, scheduler, evidencia y CLI.  
**Files likely touched:** `tools/orchestrator/tests/`.  
**Verification:** pytest focal RED y defectos sembrados identificados.  
**Estimated scope:** M.

### Task T03: Viabilidad nativa y causa de release

**Description:** Consultar documentación vigente de Cursor/Pi y revisar por MCP GitHub los logs de la release sin assets.

**Acceptance criteria:**

- [x] Capacidades/flags soportados y limitaciones quedan citados con versión observada.
- [x] La causa del run `v7.1.0` queda registrada o clasificada `blocked` con motivo.

**Dependencies:** T00.  
**Implementation roles:** `role-back`.  
**Test surfaces:** Cursor B/C, Pi JSON/RPC y release workflow.  
**Files likely touched:** `tasks/plan-autoworkspace-remediation.md`.  
**Verification:** revisión documental y enlaces/comandos de evidencia.  
**Estimated scope:** S.

#### Checkpoint CP0

- [x] Baseline verde y RED reproducidos.
- [x] Viabilidad nativa y causa de release registradas sin falsos PASS.

## Tasks — Wave 1

### Task T04: Política común de ejecución

**Description:** Implementar política inmutable deny-by-default para entorno, herramientas, scopes, flags y timeouts.

**Acceptance criteria:**

- [x] Entorno y herramientas se derivan antes de ejecutar y no desde prompts.
- [x] Credenciales no autorizadas y flags prohibidos se rechazan de forma demostrada.

**Dependencies:** T01.  
**Implementation roles:** `role-back`, `role-clean-code`, `plan-validators`.  
**Test surfaces:** Builder de política, digest, redacción y errores.  
**Files likely touched:** `tools/harness/policy.py`, `tools/harness/tests/test_policy.py`.  
**Verification:** `pytest tools/harness/tests -q`, typecheck y `make validate`.  
**Estimated scope:** M.

### Task T05: Aplicar aislamiento a Pi

**Description:** Conectar el adaptador Pi a la política común sin shell arbitrario ni entorno implícito.

**Acceptance criteria:**

- [x] Lectores/escritores reciben solo herramientas permitidas y entorno filtrado.
- [x] Timeout/cancelación limpian el grupo y producen reconciliación.

**Dependencies:** T04.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** `PiSubagentAdapter`, JSONL y procesos fixture.  
**Files likely touched:** `tools/harness/pi.py`, `tools/harness/tests/test_pi_subagent.py`.  
**Verification:** pytest Pi/harness y typecheck.  
**Estimated scope:** S.

### Task T06: Aplicar aislamiento a Cursor

**Description:** Conectar Cursor a la política común y retirar `--force`/`--yolo` de todo recorrido de aceptación.

**Acceptance criteria:**

- [x] Ningún argv de escritura contiene autoaprobación.
- [x] Ausencia de un modo compatible queda `blocked` antes de efectos.

**Dependencies:** T04.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** `CursorSubagentAdapter`, argv, entorno y permisos.  
**Files likely touched:** `tools/harness/cursor.py`, `tools/harness/tests/test_cursor_native.py`.  
**Verification:** pytest Cursor/harness, búsqueda de flags prohibidos y typecheck.  
**Estimated scope:** S.

#### Checkpoint CP1

- [x] Política común y ambos adaptadores pasan unitarias/adversarias.
- [x] Ningún secreto, shell o autoaprobación queda implícito.

## Tasks — Wave 2

### Task T07: Staging único y transaccional

**Description:** Introducir workspace de run, staging compartido, writers aislados y lock de integración.

**Acceptance criteria:**

- [x] Dependientes e independientes aparecen correctamente en el mismo staging.
- [x] Fallo de apply/verificación impide cierre y restaura el digest previo.

**Dependencies:** T02, T04.  
**Implementation roles:** `role-back`, `role-clean-code`, `plan-validators`.  
**Test surfaces:** Worktrees, patches, scopes, locks y rollback.  
**Files likely touched:** `worktrees.py`, `runner.py`, `test_worktrees.py`, `test_full_flow.py`.  
**Verification:** `test_orchestration_core.sh` y pytest orchestrator.  
**Estimated scope:** M.

### Task T08: Verificadores y evidencia read-only

**Description:** Resolver IDs permitidos y hacer que todo resultado real pase por verificación/evidencia.

**Acceptance criteria:**

- [x] Unknown ID, lista vacía o existencia sin contenido no producen cierre.
- [x] Read-only completa con artefacto real redactado y evidencia válida.

**Dependencies:** T07.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Verifier registry, `verify_and_store`, artefactos y receipts.  
**Files likely touched:** `verifiers.py`, `runner.py`, `run.py`, `test_full_flow.py`.  
**Verification:** pytest orchestrator/execution y negativos de evidencia.  
**Estimated scope:** M.

#### Checkpoint CP2a

- [x] Staging acumulativo y evidencia read-only pasan.
- [x] Ningún verificador desconocido u omitido llega a delegar.

### Task T09: Resume y manifest final

**Description:** Reconstruir staging desde artefactos válidos y escribir el manifest integrado del run.

**Acceptance criteria:**

- [x] Resume no repite succeeded y reproduce el digest esperado.
- [x] Cambio de base/plan/patch invalida la reconstrucción afectada.

**Dependencies:** T08.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Scheduler, resume, manifests, hashes y replay.  
**Files likely touched:** `worktrees.py`, `runner.py`, `test_scheduler.py`, `test_full_flow.py`.  
**Verification:** pytest orchestrator y comparación de manifests.  
**Estimated scope:** M.

### Task T10: CLI `--plan` y E2E del núcleo

**Description:** Implementar la semántica de `--plan` y completar el E2E con dependencias, lector, writers y validación final.

**Acceptance criteria:**

- [x] `--plan` nunca se ignora; dry-run no cambia bytes.
- [x] El E2E demuestra manifest final y ningún cambio en el checkout real.

**Dependencies:** T09.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** CLI, activación, scheduler y E2E público.  
**Files likely touched:** `run.py`, `scheduler.py`, `test_orchestration_core.sh`.  
**Verification:** dry-run, E2E núcleo y `make validate`.  
**Estimated scope:** M.

#### Checkpoint CP2b

- [x] Resume, manifest final, `--plan` y dry-run están verdes.
- [x] El núcleo completo pasa antes de conectar modelos.

## Tasks — Wave 3

### Task T11: Opt-in y agregación nativa

**Description:** Exigir opt-in antes de auth/modelos y agregar los resultados sin convertir ausencia en PASS.

**Acceptance criteria:**

- [x] Sin opt-in no se crean procesos/worktrees y la salida es `not_run`/exit 3.
- [x] `validate-harnesses`/`e2e-orchestration` agregan ambos harnesses con causas útiles.

**Dependencies:** T05, T06.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Makefile, preflight auth, códigos y agregación.  
**Files likely touched:** `Makefile`, `test_pi_orchestration.sh`, `test_cursor_orchestration.sh`.  
**Verification:** carriles sin opt-in y fixtures de salida.  
**Estimated scope:** M.

### Task T12: Cursor B/C real

**Description:** Sustituir filesystem/hook directo por descubrimiento y políticas observados mediante Cursor.

**Acceptance criteria:**

- [x] Recursos ausentes/corruptos rompen B aunque sus rutas existan. (B nativo via `sessionStart` + defecto sembrado)
- [x] Cursor genera allow/deny/ask; el test no escribe sentinels ni invoca el hook directamente.

**Dependencies:** T03, T06, T11.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Cursor CLI, skills/rules/agents/hooks y sentinels.  
**Files likely touched:** `cursor.py`, `test_cursor_native.py`, `test_cursor_native.sh`.  
**Verification:** `test_cursor_native.sh` autorizado y defectos sembrados.  
**Estimated scope:** M.

### Task T13: Recorrido real Cursor

**Description:** Ejecutar el fixture completo con Cursor sin autoaprobación sobre el núcleo remediado.

**Acceptance criteria:**

- [x] Cursor escribe, integra y verifica el artefacto con evidencia completa.
- [x] No hay flags prohibidos, procesos residuales ni cambios en el checkout origen.

**Dependencies:** T10, T12.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Cursor adapter, staging, verifier y evidencia.  
**Files likely touched:** `test_cursor_orchestration.sh`, plan/evidencia.  
**Verification:** `test_cursor_orchestration.sh` con modelo autorizado.  
**Estimated scope:** S.

### Task T14: Recorrido real Pi

**Description:** Ejecutar el mismo fixture con Pi, política común y evidencia comparable.

**Acceptance criteria:**

- [x] Pi escribe, integra y verifica el artefacto sin herramientas extra.
- [x] Versión/modelo/run/artefactos quedan registrados sin secretos ni procesos residuales.

**Dependencies:** T10, T11.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Pi adapter, staging, verifier, evidencia y paquete.  
**Files likely touched:** `test_pi_orchestration.sh`, plan/evidencia.  
**Verification:** `test_pi_orchestration.sh` con modelo autorizado.  
**Estimated scope:** S.

#### Checkpoint CP3

- [ ] Cursor B/C y ambos recorridos reales pasan sobre la misma revisión.
- [ ] Ningún requisito nativo obligatorio está `not_run`.

## Tasks — Wave 4

### Task T15: Corregir assets de release

**Description:** Aplicar la causa diagnosticada y reforzar readiness para impedir releases sin entregables.

**Acceptance criteria:**

- [x] Archive/checksum/attestation/upload quedan ligados al mismo tag/commit.
- [x] Assets ausentes o digest distinto rompen la puerta.

**Dependencies:** T03, T13, T14.  
**Implementation roles:** `role-back`, `plan-validators`; aprobación CI previa.  
**Test surfaces:** Release workflow y validador de assets.  
**Files likely touched:** `release.yml`, `release_coherence.py`, `test_release_assets.py`.  
**Verification:** fixtures, actionlint/zizmor y release coherence.  
**Estimated scope:** M.

### Task T16: Readiness y smoke post-release

**Description:** Agregar readiness completa y una puerta pública de descarga/verificación/instalación sin modelos.

**Acceptance criteria:**

- [x] Readiness incluye todas las puertas nativas previas.
- [x] Post-release falla si faltan assets, atestación, doctor o actualización Pi.

**Dependencies:** T15.  
**Implementation roles:** `role-back`, `plan-validators`; aprobación CI previa.  
**Test surfaces:** Makefile, workflow, bootstrap y runbook.  
**Files likely touched:** `release.yml`, `Makefile`, `test_bootstrap.sh`, `harness-setup.md`.  
**Verification:** bootstrap adversario y gates de workflow.  
**Estimated scope:** M.

#### Checkpoint CP4a

- [ ] La cadena de assets y la puerta post-release detectan omisiones.
- [ ] No se ha creado tag, release ni rerun externo.

### Task T17: Validación local integral

**Description:** Ejecutar todas las puertas sobre una única identidad candidata y registrar resultados.

**Acceptance criteria:**

- [x] Deterministas, typecheck/lint, nativas y E2E están verdes.
- [x] No hay requisito obligatorio omitido ni evidencia de otro HEAD.

**Dependencies:** T16.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Suite completa y harnesses.  
**Files likely touched:** plan/evidencia.  
**Verification:** comandos de Success Criteria transversal.  
**Estimated scope:** S.

### Task T18: Versión patch y changelog

**Description:** Preparar `v7.1.1`, locks y notas como corrección compatible, sin publicar.

**Acceptance criteria:**

- [x] Manifiestos/locks/changelog son coherentes y justifican PATCH.
- [x] Readiness pasa sin crear tag ni release.

**Dependencies:** T17.  
**Implementation roles:** `role-back`; `project-publish` solo para readiness.  
**Test surfaces:** Versiones, release coherence y changelog.  
**Files likely touched:** package manifests/locks, `tools/pyproject.toml`, `tools/uv.lock`, `CHANGELOG.md`.  
**Verification:** `cut_tag.py --dry-run` y release gate.  
**Estimated scope:** M.

### Task T19: Alinear canon y documentación viva

**Description:** Corregir 17 skills, diagrama, quickstarts y afirmaciones de soporte sin tocar historial.

**Acceptance criteria:**

- [x] AGENTS/taxonomía/D01/README/setup describen el mismo catálogo y release candidata.
- [x] Índice, snapshot, enlaces, terminología y formato pasan.

**Dependencies:** T17.  
**Implementation roles:** `role-clean-code`, `plan-validators`.  
**Test surfaces:** Canon, índice, enlaces y documentación de instalación.  
**Files likely touched:** `AGENTS.md`, `TAXONOMY.md`, D01, `README.md`, `harness-setup.md`.  
**Verification:** `make validate`, smoke y lint.  
**Estimated scope:** M.

### Task T20: Revisión independiente pre-release

**Description:** Contrastar módulos, evidencia e identidad antes de solicitar cualquier publicación.

**Acceptance criteria:**

- [x] T00–T19 y CP0–CP4a tienen evidencia o NO-GO concreto.
- [x] No hay omisiones, evidencia stale ni publicación no autorizada.

**Dependencies:** T18, T19.  
**Implementation roles:** revisor read-only/`aw-verifier`.  
**Test surfaces:** Plan versus código, gates y evidencia.  
**Files likely touched:** plan/evidencia.  
**Verification:** revisión read-only y digest final.  
**Estimated scope:** S.

#### Checkpoint CP4b

- [ ] Release candidate completamente validada y documentada.
- [ ] Publicación sigue pendiente de autorización específica.

## Tasks — Distribución pública y cierre

### Task T21: Registrar release autorizada existente

**Description:** Tras una publicación separada autorizada por el operador, registrar tag/commit/assets observados; nunca crearla desde el scheduler.

**Acceptance criteria:**

- [ ] Existe autorización y la release observada corresponde a la identidad revisada.
- [ ] Tarball/checksum/attestation se registran sin modificar `v7.1.0`.

**Dependencies:** T20 + publicación externa autorizada.  
**Implementation roles:** `role-back`; publicación externa mediante `project-publish`.  
**Test surfaces:** GitHub Release, tag, assets y atestación.  
**Files likely touched:** plan/evidencia.  
**Verification:** MCP GitHub y verificación pública read-only.  
**Estimated scope:** S.

### Task T22: Smoke público

**Description:** Ejecutar bootstrap Pi/Cursor y actualización Pi desde `v7.1.0` al nuevo tag en entornos temporales.

**Acceptance criteria:**

- [ ] Ambos bootstrap descargan, verifican, instalan y pasan doctor.
- [ ] La actualización Pi entre tags carga el catálogo/extensión esperados y preserva recursos ajenos.

**Dependencies:** T21.  
**Implementation roles:** `role-back`, `plan-validators`.  
**Test surfaces:** Release pública, bootstrap, Pi Git y desinstalación.  
**Files likely touched:** plan/evidencia.  
**Verification:** `AW_PI_GIT_SMOKE=1` y smoke post-release.  
**Estimated scope:** M.

#### Checkpoint CP5

- [ ] Assets y atestación pública verificados.
- [ ] Bootstrap y actualización entre tags pasan sin efectos ajenos.

### Task T23: Estado y evidencia final

**Description:** Reconciliar plan activo, tasks, receipts, documentación y tabla final por capacidad.

**Acceptance criteria:**

- [ ] Estado y digest corresponden al plan/código final.
- [ ] Cada capacidad registra fuente, comando, identidad, estado y desviación.

**Dependencies:** T22.  
**Implementation roles:** `role-back`, `role-clean-code`, `plan-validators`.  
**Test surfaces:** Status, receipts, canon y evidencia.  
**Files likely touched:** `.autoworkspace/status.yaml`, plan/evidencia.  
**Verification:** router status, doctor, `make validate`.  
**Estimated scope:** S.

### Task T24: Revisión independiente de cierre

**Description:** Emitir GO/NO-GO final sin ejecutar publicación ni modificar implementación.

**Acceptance criteria:**

- [ ] T00–T23, CP0–CP6 y DoD tienen evidencia completa o NO-GO por IDs.
- [ ] GO solo si no queda fail/blocked/not_run obligatorio y toda identidad coincide.

**Dependencies:** T23.  
**Implementation roles:** revisor independiente read-only/`aw-verifier`.  
**Test surfaces:** Todas las capacidades y evidencia final.  
**Files likely touched:** plan/evidencia.  
**Verification:** revisión read-only y comandos de cierre.  
**Estimated scope:** S.

#### Checkpoint CP6

- [ ] Revisión independiente registra veredicto y limitaciones.
- [ ] Cualquier operación posterior permanece fuera del scheduler.

## Definition of Done del incremento

- [ ] T00–T24 completados por dependencias con evidencia registrada.
- [ ] Los seis módulos cumplen sus especificaciones.
- [ ] Política efectiva sin secretos/herramientas/autoaprobación no autorizados.
- [ ] Staging acumulativo, read-only, verificación, resume y manifest final demostrados.
- [ ] Cursor B/C y recorridos reales Pi/Cursor pasan sobre la misma identidad.
- [ ] Release patch pública con assets, atestación y smokes verificados.
- [ ] Canon 17, documentación, estado y evidencia reconciliados.
- [ ] Todas las puertas verdes sin fail/blocked/not_run obligatorio.
- [ ] Ninguna publicación, host o recurso externo mutado sin autorización específica.

## Registro de ejecución

Durante IMPLEMENT cada tarea añade aquí estado, identidad, roles, RED/GREEN, comandos, artefactos, limitaciones y evidencia. Las ausencias se clasifican como `blocked`, `not_run` o `not_applicable` solo con regla verificable; nunca como PASS.

### T00 baseline-identity — 2026-11-10

| Campo                        | Valor                                                                      |
| ---------------------------- | -------------------------------------------------------------------------- |
| Estado                       | done                                                                       |
| Roles                        | role-clean-code                                                            |
| HEAD                         | `68c1dc90f8d5edfe4ca011f585de95dce95e6e32`                                 |
| Rama                         | `main` (tracks `origin/main`)                                              |
| Worktrees                    | 1 (`/home/alexendros/Work/autoworkspace`)                                  |
| Árbol                        | limpio salvo `?? tasks/plan-autoworkspace-remediation.md`                  |
| aw-plan digest               | `8eb29d52bf6ddf5131ad0a83ba16fbfb0437c00f22534236f23751870b388c99` (match) |
| Catálogo                     | 17 skills (PREFLIGHT dry-run)                                              |
| Python / Node / npm / uv     | 3.14.8 / v26.13.0 / 11.20.0 / 0.13.7                                       |
| agent / pi                   | `2026.11.05-86047df` / `1.5.0`                                             |
| `.autoworkspace/status.yaml` | schema 1 en disco; router migra a schema 2 en memoria; `active_plan: null` |
| Comandos                     | `git rev-parse HEAD`, `git status`, `make validate` → exit 0               |
| Limitación                   | `make validate` heredado **no** es evidencia final del incremento          |
| Evidencia                    | este registro; no se reescribió historial ni `.autoworkspace/SPEC.md`      |

### T01 red-execution-isolation — 2026-11-10

| Campo          | Valor                                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Estado         | RED confirmed (tests committed as failing contract)                                                                                           |
| Roles          | role-back, plan-validators                                                                                                                    |
| Comando        | `pytest tools/harness/tests/test_isolation_red.py -q` → 3 failed                                                                              |
| Causas         | (1) writer tools incluyen `bash`; (2) hijo hereda `AW_FIXTURE_SECRET`/`GITHUB_TOKEN`; (3) `CursorSubagentAdapter(force=True)` añade `--force` |
| Artefacto      | `tools/harness/tests/test_isolation_red.py`                                                                                                   |
| HEAD contenido | working tree sobre `68c1dc9` + SDD/tests                                                                                                      |

### T02 red-orchestration-integrity — 2026-11-10

| Campo     | Valor                                                                                                                                                            |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estado    | RED confirmed                                                                                                                                                    |
| Roles     | role-back, plan-validators                                                                                                                                       |
| Comando   | `pytest tools/orchestrator/tests/test_orchestration_red.py -q` → 4 failed                                                                                        |
| Causas    | (1) dependiente no ve artefacto integrado; (2) read-only sin evidence store; (3) falta `orchestrator.verifiers`; (4) falta `RunWorkspace` / rechazo digest stale |
| Artefacto | `tools/orchestrator/tests/test_orchestration_red.py`                                                                                                             |

### T03 native-release-feasibility — 2026-11-10

| Campo                           | Valor                                                                                                                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estado                          | done (feasibility recorded; no PASS for native B/C yet)                                                                                                                                           |
| Roles                           | role-back                                                                                                                                                                                         |
| Cursor CLI                      | `agent` `2026.11.05-86047df`; help: `--print` claims write+shell access; `--mode` only `plan`/`ask` (read-only); `-f/--force` and `--yolo` auto-approve; `--sandbox enabled\|disabled`; `--trust` |
| Cursor write sin autoaprobación | **unproven** — no documented headless write mode without `--force`/`--yolo`; acceptance must not use those flags; if spike fails → `blocked`                                                      |
| Pi                              | `1.5.0`; `--mode text\|json\|rpc`; `--tools` allowlist; `--print/-p`; help via disposable HOME                                                                                                    |
| Release `v7.1.0`                | `assets: []`; run `42718075116` failed at **Upload attested release assets** with `release not found`                                                                                             |
| Causa raíz                      | en push a `main`, el step Upload no recibe `needs.publish.outputs.version`; `VERSION="${VERSION:-${GITHUB_REF_NAME#v}}"` resuelve a `main` → `gh release upload vmain`                            |
| Limitación                      | sin rerun externo; `v7.1.0` permanece inmutable                                                                                                                                                   |

### T04 execution-policy — done

| Campo      | Valor                                                                                                      |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| Estado     | done                                                                                                       |
| Roles      | role-back, role-clean-code, plan-validators                                                                |
| Artefactos | `tools/harness/policy.py`, `tools/harness/tests/test_policy.py`                                            |
| GREEN      | deny-by-default env; writer tools without bash; forbidden flags; digest without secret values              |
| Comandos   | `pytest tools/harness/tests -q` → 45 passed; `npm run typecheck` → ok; `make validate` → All checks passed |

### T05 pi-isolation — done

| Campo      | Valor                                                                      |
| ---------- | -------------------------------------------------------------------------- |
| Estado     | done                                                                       |
| Roles      | role-back, plan-validators                                                 |
| Artefactos | `tools/harness/pi.py` uses `build_policy` + filtered env; no bash in tools |
| Evidencia  | isolation_red Pi cases GREEN; existing timeout/cancel tests still pass     |

### T06 cursor-isolation — done

| Campo      | Valor                                                                                                                                    |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Estado     | done                                                                                                                                     |
| Roles      | role-back, plan-validators                                                                                                               |
| Artefactos | `tools/harness/cursor.py` rejects `force=True`; no `--force`/`--yolo` in argv; `--sandbox enabled`; `run.py` rejects `AW_CURSOR_FORCE=1` |
| Limitación | headless write without auto-approval remains **unproven** (T03); T12 may be `blocked`                                                    |

### CP0 / CP1 — recorded

CP0 and CP1 checkboxes marked with evidence above.

### T07 run-staging — done

| Campo      | Valor                                                                                    |
| ---------- | ---------------------------------------------------------------------------------------- |
| Estado     | done                                                                                     |
| Roles      | role-back, role-clean-code, plan-validators                                              |
| Artefactos | `RunWorkspace` shared staging; writers receive prior patches; integrate+rollback digests |
| GREEN      | `test_dependent_receives_prior_artifact_in_shared_staging` pass                          |

### T08 verifier-evidence — done

| Campo      | Valor                                                                                     |
| ---------- | ----------------------------------------------------------------------------------------- |
| Estado     | done                                                                                      |
| Artefactos | `tools/orchestrator/verifiers.py`; read-only → `verify_and_store`; empty content rejected |
| GREEN      | readonly evidence + default verifier empty-file reject                                    |

### T09 resume-manifest — done

| Campo      | Valor                                                                                   |
| ---------- | --------------------------------------------------------------------------------------- |
| Estado     | done                                                                                    |
| Artefactos | `validate_patch_manifest`, `rebuild_staging_from_artifacts`, `integrated.manifest.json` |
| GREEN      | stale patch digest rejected                                                             |

### T10 plan-cli-core-e2e — done (CP2)

| Campo      | Valor                                                                                                                                     |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Estado     | done                                                                                                                                      |
| Artefactos | `--plan` validates/activates; dry-run simulates without status writes                                                                     |
| Comandos   | `bash scripts/tests/test_orchestration_core.sh` pass; `--plan … --dry-run --json` → digest `8eb29d52…`; `make validate` All checks passed |
| Evidencia  | status.yaml unchanged (schema 1 DEFINE, no active_plan) after dry-run                                                                     |

### T11 native-opt-in — done

| Campo      | Valor                                                                                               |
| ---------- | --------------------------------------------------------------------------------------------------- |
| Estado     | done                                                                                                |
| Artefactos | `AW_NATIVE_OPT_IN=1` gate in Pi/Cursor orchestration scripts; Makefile aggregates exit 3 as not_run |
| Evidencia  | without opt-in: both scripts exit 3; `make e2e-orchestration` reports not_run (core still green)    |

### T12 cursor-native-bc — done (B/C pass)

| Campo       | Valor                                                                                                           |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| Estado      | done                                                                                                            |
| Evidencia B | `sessionStart` observado vía Cursor; `hooks.json` ausente rompe discovery                                       |
| Evidencia C | `beforeShellExecution` allow/deny/ask vía Cursor headless **sin** `--force`/`--yolo`; efectos deny/ask ausentes |
| Comando     | `bash scripts/tests/test_cursor_native.sh` → exit 0 (`outcome=pass`, receipt `policy-receipt.json`)             |
| Spike       | confirmado 2026-11-10; probe invocado por Cursor; harness no escribe sentinels ni llama al hook directamente    |

### T13 cursor-native-e2e — done

| Campo    | Valor                                                                                                                     |
| -------- | ------------------------------------------------------------------------------------------------------------------------- |
| Estado   | done                                                                                                                      |
| Roles    | role-back, plan-validators                                                                                                |
| Comando  | `AW_NATIVE_OPT_IN=1 bash scripts/tests/test_cursor_orchestration.sh` → PASS                                               |
| Artefact | agent `2026.11.05-86047df`; `CursorSubagentAdapter(force=False)`; digest artefacto `573123b2aef1`; sin `--force`/`--yolo` |
| HEAD     | working tree sobre `68c1dc9`; aw-plan digest canónico `8eb29d52…`                                                         |

### T14 pi-native-e2e — done

| Campo    | Valor                                                                                                     |
| -------- | --------------------------------------------------------------------------------------------------------- |
| Estado   | done                                                                                                      |
| Roles    | role-back, plan-validators                                                                                |
| Comando  | `AW_NATIVE_OPT_IN=1 AW_PI_MODEL=opencode-go/beam-free bash scripts/tests/test_pi_orchestration.sh` → PASS |
| Artefact | model `opencode-go/beam-free` (único disponible; resto en cooldown); digest `44d22db65687`                |

### T15 release-assets-fix — done (local CI edit; no publish)

| Campo    | Valor                                                                                                                                                      |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estado   | done (workflow + guards; sin tag/release)                                                                                                                  |
| Artefact | `.github/workflows/release.yml`: resolve `needs.publish.outputs.version` / `v*` tag; reject `main`; `gh release view` before upload; asset presence checks |
| Guards   | `release_coherence.release_asset_errors` + `test_release_assets.py` (incl. histórico `vmain` fallback) → 25 passed                                         |

### T16 release-readiness-smoke — done (local; no publish)

| Campo     | Valor                                                                                                                                 |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Estado    | done                                                                                                                                  |
| Artefact  | job `post-release-smoke` (download → sha256 → attestation → bootstrap Pi/Cursor sin modelos); `make readiness`; docs/harness-setup.md |
| Bootstrap | `bash scripts/tests/test_bootstrap.sh` → PASS (contra assets públicos `v7.1.0`)                                                       |

### T17 full-local-validation — done

| Campo     | Valor                                                                                 |
| --------- | ------------------------------------------------------------------------------------- |
| Estado    | done                                                                                  |
| Comando   | `AW_NATIVE_OPT_IN=1 AW_PI_MODEL=opencode-go/beam-free make readiness` → exit 0        |
| Verde     | validate, test, smoke, typecheck, lint, validate-harnesses (A/B/C), e2e-orchestration |
| Identidad | HEAD `68c1dc9…` + WT; aw-plan digest `8eb29d52…`                                      |
| Extra     | digest de evidencia por artefactos (paralelo seguro); flake scheduler resuelto        |

### T18 patch-version-changelog — done (sin publicar)

| Campo    | Valor                                                                                             |
| -------- | ------------------------------------------------------------------------------------------------- |
| Estado   | done (manifiestos locales; sin tag/release)                                                       |
| Versión  | `package.json` / locks / README / CHANGELOG → **7.1.1**                                           |
| Gates    | `release_coherence.py --release-gate` OK; `cut_tag.py --dry-run` would tag `v7.1.1`; readiness OK |
| No hecho | `cut_tag --apply`, push, GitHub Release                                                           |

### T19 canon-docs-alignment — done

| Campo  | Valor                                                               |
| ------ | ------------------------------------------------------------------- |
| Estado | done                                                                |
| Fix    | AGENTS/TAXONOMY/D01 → 17 skills; harness-setup readiness vs publish |

### T20 prerelease-review — GO (publicación pendiente de autorización)

| Campo     | Valor                                                        |
| --------- | ------------------------------------------------------------ |
| Estado    | **GO** pre-release                                           |
| Evidencia | T00–T19 con PASS local; CP3/CP4a satisfechos en working tree |
| Pendiente | autorización explícita `project-publish` para T21–T24        |
| No hecho  | commit/push/PR/tag/release                                   |

## Tabla capability → prueba → identidad → estado → desviación

| Capability              | Prueba                               | Identidad          | Estado     | Desviación              |
| ----------------------- | ------------------------------------ | ------------------ | ---------- | ----------------------- |
| execution-isolation     | pytest harness isolation/policy      | WT sobre `68c1dc9` | pass       | —                       |
| orchestration-integrity | `test_orchestration_core.sh`         | idem               | pass       | —                       |
| cursor-native B         | `test_cursor_native.sh` sessionStart | idem               | pass       | —                       |
| cursor-native C         | same (beforeShellExecution)          | idem               | pass       | sin --force/--yolo      |
| pi model e2e            | `test_pi_orchestration.sh`           | idem + opt-in      | pass       | `opencode-go/beam-free` |
| cursor model e2e        | `test_cursor_orchestration.sh`       | idem + opt-in      | pass       | —                       |
| release-recovery        | workflow + coherence + bootstrap     | idem               | pass local | sin publish             |
| release readiness       | `make readiness`                     | idem               | pass       | —                       |
| canon docs              | TAXONOMY/AGENTS/D01/setup            | idem               | pass       | —                       |
| version 7.1.1           | cut_tag --dry-run / release-gate     | idem               | pass local | sin tag                 |

**Veredicto T20 (pre-release): GO** — candidato `7.1.1` validado en local. Publicación (T21–T24) requiere orden explícita `/project-publish`.

## Siguiente puerta — STOP (publicación)

1. Revisar diff y autorizar commit/PR si se desea aterrizar el WT.
2. Tras merge a `main`, autorizar `project-publish` (tag `v7.1.1` + smoke público T21–T24).
3. Sin commit/push/tag/release en este turno salvo nueva orden.

Sin commits, pushes, PRs, merges, tags ni releases.
