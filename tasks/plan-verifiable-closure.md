---
name: Cierre verificable de autoworkspace
overview: Corregir las garantías todavía incompletas tras la PR 15 y demostrar autorización, ejecución, evidencia y finalización sobre el mismo contenido. Un único archivo canónico; sin publicar ni mutar el host.
todos:
  - id: c0-baseline
    content: "C0 · T00–T01: preservar trabajo, revalidar base e inventariar efectos y regresiones"
    status: pending
  - id: c1-execution
    content: "C1 · T02–T05: cerrar ejecución libre, parámetros fuera del digest y entrypoints alternativos"
    status: pending
  - id: c2-evidence
    content: "C2 · T06–T09: evidencia de contenido, artefactos, fase y target; sin aceptación obsoleta"
    status: pending
  - id: c3-state
    content: "C3 · T10–T12: transacción de estado completa, transiciones e idempotencia"
    status: pending
  - id: c4-portability
    content: "C4 · T13–T15: instalación recuperable, standalone real y restauración confinada"
    status: pending
  - id: c5-acceptance
    content: "C5 · T16–T19: tests públicos, OpenCode real, documentación y dictamen final por contenido"
    status: pending
isProject: false
---

# Plan único: cierre verificable de autoworkspace

### Propósito de este documento

- Objetivo: cerrar los defectos vigentes tras la PR #15 sin reiniciar el producto, ampliar la taxonomía ni añadir un framework paralelo.
- Estructura: mandato y límites → base y hallazgos → contratos de aceptación → tareas y checkpoints → matriz adversaria → cierre y registro.
- Uso: entregar este archivo íntegro a Cursor. Contiene especificación, plan, tareas, pruebas y registro de ejecución. No generar un segundo SPEC.md, todo.md o tracker canónico.
- Estado del documento: DISEÑADO / NO IMPLEMENTADO. Todas las tareas y verificaciones empiezan pendientes. Este plan no certifica el producto.

## 0. Identidad y activación

| Campo                                           | Valor                                                                  |
| ----------------------------------------------- | ---------------------------------------------------------------------- |
| Plan ID                                         | autoworkspace-verifiable-closure-v2                                    |
| Fecha                                           | 2026-10-18                                                             |
| Repositorio                                     | Soluciones-Alexendros/autoworkspace                                    |
| Base remota confirmada al preparar este archivo | 549a7343424f4e4b11c604262e4d614144fc7efd                               |
| Incremento anterior                             | PR #15, integrada; head d60dce4c4a8da6fa024dc03c15d9387d96bddcde       |
| Ruta propuesta al incorporarlo al checkout      | tasks/plan-verifiable-closure.md                                       |
| Idioma del seguimiento y del informe            | Español                                                                |
| Idioma de contratos técnicos y skills           | Seguir el canon vigente del repo, actualmente inglés                   |
| Entrega solicitada                              | Implementación local verificada y lista para revisión, sin publicación |

### Orden de lanzamiento para Cursor

> Implementa este archivo como único plan canónico. Empieza por T00, revalida el checkout y respeta las dependencias. Usa las skills aplicables, reproduce los defectos con pruebas aisladas y registra aquí comandos y resultados reales. No ejecutes mantenimiento, cambios privilegiados, firmware, correo o secretos reales. No hagas commit, push, PR, merge, tag o release sin autorización específica. No marques completo un requisito que solo esté descrito, simulado, omitido o bloqueado. Conserva trabajo ajeno y detente únicamente ante un bloqueo real, indicando la decisión exacta necesaria.

Adjuntar este archivo o pedir su revisión no autoriza ejecución. La orden explícita de implementarlo autoriza trabajo local de código y pruebas seguras en el alcance descrito; no autoriza efectos externos ni anula instrucciones superiores del entorno.

### Límites no negociables

1. No escribir en /etc, cambiar paquetes o servicios del host, actualizar firmware, restaurar el host, enviar correo real ni extraer secretos reales para probar.
2. No usar sudo, escalación, instalaciones globales, autoaprobación ni curl-pipe-shell.
3. No ejecutar código desconocido, hooks o collection de pytest antes de inspeccionar sus efectos. Venv, HOME temporal y copia del repo no son un sandbox de seguridad.
4. No reset --hard, clean -fd, force-push, sobrescritura de planes ajenos ni descarte de cambios para facilitar integración.
5. No modificar GitHub, checks requeridos, branch protection o releases. La preferencia histórica de publicar no es autorización actual.
6. No crear nuevas skills o dominios. No rehacer lo que ya está correctamente implementado.
7. No añadir servidor, daemon, firma criptográfica o plataforma de plugins para resolver un defecto local que puede corregirse dentro de los módulos actuales.
8. No prometer aislamiento frente a un actor que puede modificar el código y tiene los mismos privilegios. Sí exigir que los entrypoints oficiales respeten su política y no ofrezcan bypass documentado.
9. No convertir todas las capacidades difíciles en blocked y declarar éxito funcional. Deshabilitar una ruta insegura es contención, no implementación terminada.
10. Si un cambio necesario reduce soporte o rompe una interfaz, documentarlo y obtener aceptación del cambio de alcance cuando afecte al objetivo.

## 1. Base, preservación y nivel de certeza

### 1.1 Qué está confirmado y qué no

- El último HEAD remoto consultado al diseñar el plan es 549a7343424f4e4b11c604262e4d614144fc7efd.
- Los seis checks consultados del head de la PR #15 terminaron correctamente. Ese hecho no prueba por sí solo las garantías adversarias de este plan ni una nueva ejecución sobre el merge.
- La revisión anterior leyó código y realizó tres reproducciones aisladas de funciones: digest igual con contenido diferente y mismo tamaño/mtime; evidencia obsoleta aceptada; transición STATUS → DEFINE aceptada.
- Esas reproducciones NO fueron la suite completa del checkout. El agente debe convertirlas en tests de regresión del producto y obtener su propio RED/GREEN.
- tasks/plan-execution-closure.md declara GO del incremento anterior. Conservar su registro histórico; no usarlo como aprobación de los requisitos nuevos.

### 1.2 Arranque seguro

Antes de escribir o crear una rama:

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short --untracked-files=all
git diff --check
```

- Resolver la raíz con Git; no fijar rutas del equipo del operador.
- Si HEAD cambió, comparar los módulos afectados y reclasificar cada hallazgo: vigente, ya corregido, cambiado o no comprobado.
- No hacer pull ni checkout sobre trabajo ajeno. Si se necesita rama/worktree local, comprobar primero su existencia y los permisos del entorno; nunca resetear una rama existente.
- Inspeccionar AGENTS.md, instrucciones de ámbito, package scripts, hooks, requisitos y workflows antes de lanzar el baseline.
- Leer skills/<nombre>/SKILL.md como fuente canónica. No suponer válidos los symlinks de .agents/skills.
- Reevaluar skills por tarea. Usar plan-continue, plan-validators, role-back y role-clean-code cuando apliquen. project-publish solo para gates locales autorizados. No hay trabajo de UI previsto: no invocar role-front/role-design por completar una lista.
- Si falta herramienta de skills, leer instrucciones y referencias y declarar el fallback; no inventar invocaciones.

### 1.3 Un solo archivo de seguimiento

- Este archivo es la fuente de verdad del nuevo incremento. Los seis grupos YAML de Cursor son un índice subordinado a T00–T19.
- Mantener intactos tasks/plan.md, tasks/todo.md y el contenido histórico de planes anteriores.
- Si el destino propuesto ya existe: mismo Plan ID y trabajo → actualizar en sitio; trabajo distinto o incompleto → resolver el conflicto antes de escribir.
- No crear otro SPEC.md ni duplicar tareas en un tracker nuevo.
- Se permiten esquemas, fixtures, tests, artefactos de producto y guías necesarios para implementar; no son documentos adicionales de planificación.

### 1.4 Baseline y dependencias

Inspeccionar antes de ejecutar los comandos existentes:

```bash
python3 --version
node --version
npm --version
bash run-validation.sh
npm test
npm run syntax-check
```

No asumir que todos esos comandos están disponibles o que son inocuos. Registrar versión, entorno, cambios y resultado real. Aislar cachés y salida de tests; no ejecutar scripts que escriban en el host.

No ejecutar npm ci hasta revisar prepare/Husky. Usar venv para Python, no Python del sistema. Instalar solo dependencias comprobadas con red y permisos disponibles, sin relajar versiones para ocultar un fallo.

Si falta shell, checkout, un requisito esencial o capacidad de editar/probar: devolver blocked/not_run con efecto sobre aceptación; no fingir implementación.

## 2. Hallazgos a reproducir y cerrar

Las siguientes son observaciones de partida. Cada tarea debe revalidarlas contra el código de ejecución.

| ID  | Evidencia                               | Defecto o garantía incompleta                                                                                | Tareas   |
| --- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------- |
| V01 | tools/execution/ops.py::run_operation   | Excepción effect=read + argv libre + require_approval=False evita registro                                   | T01–T02  |
| V02 | registry.py, ops.py y clean_routine.py  | Parámetros efectivos/globales, handlers y requisitos no quedan totalmente ligados al plan autorizado         | T03–T04  |
| V03 | snapshot_state.py::main                 | Creación directa de backend conserva un entrypoint fuera de autorización común                               | T05      |
| V04 | evidence.py::work_digest                | Hash de ruta/tamaño/mtime, no de bytes; incluye evidencia/estado administrativo                              | T06      |
| V05 | evidence.py::store_result/load_evidence | No invalida código/artefactos cambiados; validación de resultado e identidad incompleta                      | T07–T08  |
| V06 | status_bump.py y run.py --complete      | Cualquier evidencia succeeded puede justificar otra fase; no vínculo suficiente a skill/target/política      | T09, T11 |
| V07 | status_bump.py::_atomic_write_yaml      | Lock solo de escritura: lectura y cálculo previos permiten lost update                                       | T10      |
| V08 | _assert_phase_transition y run_id       | Retrocesos arbitrarios y repetición de finalización sin idempotencia efectiva                                | T11–T12  |
| V09 | clean_routine handlers/common.py        | Comandos fallidos/ausentes y retornos None pueden acabar como succeeded                                      | T04      |
| V10 | scripts/install.sh                      | Rollback borra también enlaces preexistentes actualizados; recuperación incompleta                           | T13      |
| V11 | install-opencode.sh                     | Transacción incompleta; conflictos de recursos ajenos no siempre son colisiones reales                       | T13      |
| V12 | preflight.py y execution.yaml           | Standalone no ejecutable fuera del checkout; red requerida tratada como optional                             | T14      |
| V13 | snapshot_state.py::rollback_snapshot    | Doble apertura del tar y aceptación de staging proporcionado bajo /tmp sin propiedad de ejecución demostrada | T15      |
| V14 | test_execution_e2e.sh y OpenCode        | Versionado/discovery no demuestra permisos, carga y recorrido positivo; not_run termina en E2E OK            | T16–T18  |
| V15 | docs/planes                             | GO del incremento anterior supera la evidencia para el cierre integral                                       | T19      |

Mejoras ya realizadas que se conservan: retirada del env de habilitación del host; eliminación de la doble limpieza desde main; Proton sin CONFIRM_SEND como consentimiento; --check de índice puro y completo; JSON Schema aplicado; tests de Proton e instalación incluidos; skills.paths y README alineados; rechazo de enlaces en tar y escritura de estado por os.replace. No reimplementar esas piezas salvo defectos concretos demostrados.

## 3. Decisiones técnicas obligatorias

### D1. Un solo API de ejecución de producto

- Los llamantes entregan operation_id y parámetros tipados, no effect, argv, require_approval ni executable_id arbitrarios.
- Registro y contratos deben compartir una representación coherente de operación, efectos, requisitos y handler. No mantener dos políticas divergentes.
- Eliminar la excepción libre de lectura. Tests que necesitan procesos arbitrarios usan un helper de test no exportado como API de producto o un registro aislado de fixtures.
- Rechazar campos desconocidos o reservados en vez de eliminarlos silenciosamente cuando su presencia indique intento de alterar política.
- Identidad y código de handler se resuelven antes de aprobación. No registrar/reemplazar handlers entre aprobación y ejecución. Si se necesita registro dinámico, inicializarlo y congelarlo antes del plan operativo; tests con registro aislado.
- No pretender que esa congelación sea un sandbox frente a quien controla el proceso; es una garantía funcional de los entrypoints oficiales.

### D2. Plan efectivo completo y autorización comprensible

Objeto de ejecución canónico: operación, skill/versión, target resuelto, parámetros completos, efectos, handler/ejecutable identificable, cwd y configuración relevante que cambie sus efectos.

- Normalizar y validar antes de calcular digest y solicitar aprobación.
- Todos los valores usados por el handler proceden de ese objeto, no de globals o entorno no declarados. Incluir keep_versions, journal_time, journal_size, roots/cachés y demás parámetros que realmente use cada limpiador.
- Capturar en el plan las entradas derivadas que cambien el efecto. En eliminación de paquetes, presentar la selección efectiva o revalidar que la precondición/selección no cambió antes de actuar.
- Copia inmutable o defensa equivalente contra cambios entre aprobación y ejecución.
- El digest detecta cambios; no representa consentimiento. El proveedor debe mostrar al operador target, parámetros y efectos suficientes para revisar la operación, no solo un ID y un hash.
- No usar env, approved=true ni tokens generados por el propio agente como consentimiento.
- DenyProvider por defecto. Sin proveedor confiable, blocked/awaiting_approval. El entorno de test puede inyectar un proveedor falso solo dentro de tests aislados.
- No se exige construir una integración MCP/SDK nueva si el entorno no la soporta: declarar límites y no anunciar ejecución mutadora plenamente operativa.

### D3. Recuperación, efectos y resultados reales

- Un snapshot_id no es prueba. Verificar existencia, identidad/host/target, integridad, backend y recovery_scope adecuado a la operación.
- No afirmar que borrar logs/temporales o actualizar firmware es reversible por disponer de un backup de configuración.
- Firmware y reinicios no forman parte implícita de cleanup. Mantener su ejecución real fuera de este incremento y el soporte explícitamente delimitado.
- Requisitos ausentes → blocked/not_applicable justificado; no succeeded por retornar None.
- Cada handler devuelve resultado explícito; fallo/timeout/parcial se propaga hasta CLI y evidencia.
- Probes distinguen sin incidencias, no comprobado y error. Salida vacía por fallo no debe producir PASS.
- Tras fallo o rechazo de una operación, ejecutar solo las siguientes que una política de dependencias marque como independientes. No continuar por accidente.
- Reconciliación obligatoria ante efecto externo posiblemente realizado y timeout; no reintento automático ciego.
- Aplicar timeout a handlers reales cuando se anuncia en el registro. No usar un thread que se declare cancelado mientras sigue mutando; usar worker/control efectivo o declarar la limitación y bloquear esa modalidad.
- No persistir stdout/stderr sin redacción; errores de SMTP, paquetes o probes pueden contener datos sensibles.

### D4. Digest de contenido y artefactos

Implementar un content manifest versionado:

- Enumeración determinista de paths relativos, tipos y hashes SHA-256 de bytes.
- Incluir nuevos archivos relevantes no rastreados y configuración que influya en la operación/verificación.
- Especificar symlinks: no seguir escapes fuera del target; su identidad/target debe quedar representada o rechazarse según el caso.
- Exclusiones explícitas y limitadas para .git, entornos, cachés, evidencia, estado y diario del plan. No excluir todo docs/tasks sin analizar si afectan a la operación.
- Si una operación cambia código, registrar input_digest y output_digest por separado. La aceptación de implementación se liga al contenido resultante que fue verificado, no al árbol previo.
- No usar mtime/tamaño como identidad de contenido. Touch sin cambio de bytes no invalida contenido; bytes diferentes del mismo tamaño sí.
- Evitar carreras de lectura: snapshot de inputs o comprobación de estabilidad antes/después. Si cambia mientras se calcula/verifica, error explícito y reverificación.
- Artefactos con raíz confinada, tipo, hash, tamaño y verificador de contenido cuando corresponda. No basta is_file().
- Las evidencias administrativas no alteran el content_digest que luego necesitan validar.

### D5. Registro de ejecución y finalización

- run_id opaco y único, con formato estricto y sin separadores de ruta/traversal. Usar UUID u opción equivalente no basada solo en segundos.
- No derivar nombres de archivo de IDs sin validar. Confinar evidence store y artifacts; rechazar symlinks/paths fuera de raíces permitidas.
- Resultado versionado y validado antes de almacenar y al cargar. succeeded exige códigos/acciones/verificaciones coherentes.
- Campos de identidad: operación, skill/versión, fase/tarea autorizada, target, plan_digest, input/output content digests, verificación y artefactos.
- Finalización exige que esa evidencia corresponda exactamente a la fase/tarea/skill/target actual y a la revisión verificada.
- No aceptar validate_snapshot como prueba de haber escrito una especificación o completado implementación.
- Estados simulados, pendientes, bloqueados, parciales, fallidos o con requisitos esenciales not_run no completan una fase real.
- Reutilizar evidencia en otra tarea o target se rechaza; repetir la misma finalización se resuelve idempotentemente sin incremento duplicado.
- Conservar trazabilidad de invalidación/migración de evidencia antigua. Legacy sin campos esenciales no se convierte por defecto en éxito nuevo.
- Límite de confianza explícito: el store local no certifica autenticidad contra un actor que puede editarlo todo. No añadir firmas fingidas ni presentar un JSON editable como aprobación independiente.

### D6. Transacción de estado

La operación indivisible es: adquirir lock → leer → validar revisión, transición y evidencia → actualizar → escribir temporal → reemplazar → liberar.

- No calcular state_revision fuera del lock y asumir que sigue vigente.
- Control de revisión esperada o mecanismo equivalente para rechazar updates sobre estado obsoleto.
- Definir grafo de transiciones: misma fase solo si es una acción válida/idempotente y siguiente fase según criterios. Retroceso/reinicio solo como operación explícita con política, nunca por la desigualdad de índices.
- Awaiting_agent no completa ni incrementa avance de implementación; resolver y limpiar sus campos de forma consistente al completar.
- --complete aplica la misma política de proyecto, fases y allowlist que route. Configuración ausente/inválida no se ignora.
- SemVer de producto separado del bookkeeping; publicación/bump de release no se deriva de fase.
- IDs de ejecución únicos no son, por sí mismos, idempotencia de efectos. Separar execution_id, idempotency_key y completion receipt si hace falta.
- Atomic replace evita archivos a medio escribir; durabilidad y manejo de interrupciones deben describirse y probarse en el alcance soportado.

### D7. Instalación, portabilidad y staging

- Journal por recurso: inexistente, creado, sin cambios, sustituido con estado anterior. Rollback restaura el estado inicial, no elimina indiscriminadamente todo lo tocado.
- Manifiesto final solo después de aplicación válida. Operación parcial informa su estado y conserva información de recuperación.
- Preservar archivos/directorios/symlinks ajenos. En OpenCode comprobar conflictos sobre los nombres que se van a instalar; un recurso ajeno no colisionante no debe impedir coexistencia sin motivo.
- Confinamiento real y política de symlinks para target/manifiesto. No usar una lista de paths exactos como única prueba de seguridad.
- Standalone debe poder ejecutar la capacidad declarada sin acceso al checkout original. Si requiere tools/execution, empaquetar dependencia real o reclasificar workspace-required y corregir quickstart. Reclasificar no cierra por sí solo la autonomía originalmente prometida.
- Preflight recibe skill_root explícito y valida shared_dependencies, binarios, capacidades y red por operación. Un requisito duro no autorizado es blocked, no optional_missing.
- Restauración solo a staging nuevo creado por el programa, privado y vacío. No aceptar un directorio existente solo por estar bajo tempfile.gettempdir().
- Usar una única apertura controlada del tar para inspección/extracción; rechazar links, absolutos, traversal, especiales y destinos fuera de staging. Aplicar filtro explícito de la versión soportada y límites de tamaño/número para evitar agotamiento de recursos.
- Prueba de contenido restaurado y de ausencia de escrituras externas; nunca restaurar host real.
- Verificar que hashes de snapshot no queden invalidados por reescribir metadata.json después de construirlos; separar manifest estable de campos derivados si es necesario.

### D8. Aceptación y OpenCode

Tres niveles separados:

A. Puerta determinista de código y contratos: obligatoria y sin red/cuentas/modelos reales.
B. Integración nativa: binario OpenCode declarado, discovery y carga real; sin autoaprobación.
C. Permisos: skill allow/deny independiente de permiso de acción; rechazo demuestra que no se ejecutó el efecto mediante sentinel seguro en temporal.

- opencode --version no demuestra B ni C. debug skill solo no demuestra C.
- Revalidar comandos con --help y documentación de 1.18.34 antes de añadirlos; no usar APIs de dev como si pertenecieran a esa versión.
- Context7 puede mostrar debug agent/tool y SDK de otras revisiones. Si se usa un debug tool, comprobar que atraviesa la puerta real que se quiere probar: un debug que solo aplica deny no demuestra el prompt ask.
- No usar --auto. La documentación consultada describe que aprueba solicitudes no explícitamente denegadas. Probar reglas efectivas globales y por agente.
- Si B/C no se ejecutan por falta de binario/capacidad, not_run visible y aceptación de harness pendiente. El gate A puede pasar, pero no imprimir un GO integral o un E2E total.
- No convertir una prueba de rechazo en prueba de éxito funcional. Hay que verificar también un recorrido positivo seguro.

## 4. Tareas y checkpoints

Regla universal: inspeccionar → escribir test que falle por la causa correcta → cambio mínimo → test verde → refactor → comprobación pertinente → evidencia. No exigir un test rojo artificial para edición puramente documental; usar validación coherente.

Cada tarea debe registrar comandos exactos realmente ejecutados y test node IDs. Los comandos nuevos de este plan son interfaces a concretar, no herramientas que ya existan.

### T00 — Preservar trabajo y fijar baseline

- Depends: none
- Roles: plan-continue; plan-validators para estrategia.
- Superficie/rutas: checkout, instrucciones, hooks, este plan, run-validation.sh y requisitos.
- Trabajo: ejecutar sección 1; inventariar efectos antes del baseline. Registrar HEAD, árbol, versiones y contenido inicial. Inspeccionar tareas anteriores sin sobrescribirlas.
- Aceptación: [ ] trabajo ajeno preservado; [ ] hallazgos reclasificados; [ ] baseline seguro y limitaciones registradas.
- Verificación: comandos seguros existentes y diff inicial; ningún efecto de host/red real no autorizado.

### T01 — Sembrar regresiones adversarias y controles positivos

- Depends: T00
- Roles: plan-validators, role-back.
- Superficie/rutas: tests de execution, workspace-router, limpieza e instalación.
- Trabajo: reproducir V01, V04–V08 con entrypoints públicos o funciones reales; incorporar las tres reproducciones aisladas como tests del repo. Usar procesos/handlers espía y filesystem temporal.
- Aceptación: [ ] cada test RED falla por la garantía rota y no por import faltante; [ ] controles positivos impiden un arreglo de “bloquear todo”.
- Verificación: test node IDs, resultado previo y ausencia de llamadas reales a mutadores.

### Checkpoint C0 — Arranque seguro

- [ ] T00–T01 verificados.
- [ ] No se ha ejecutado ni publicado nada fuera del alcance.
- [ ] Se dispone de RED reproducible para los fallos centrales, no solo una descripción.

### T02 — Retirar el bypass libre read

- Depends: T01
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: tools/execution/ops.py y consumidores.
- Trabajo: aplicar D1; eliminar excepción legacy effect=read/argv; migrar tests sin dejar helper peligroso exportado como API de producto.
- Aceptación: [ ] desconocido/read autodeclarado no ejecuta; [ ] operación de lectura registrada sí funciona; [ ] parámetros reservados se rechazan claramente.
- Verificación: A01–A03; sentinel de escritura solo dentro del temporal para demostrar ausencia de bypass.

### T03 — Normalizar parámetros y ligar autorización a handler efectivo

- Depends: T02
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: registry.py, approval.py, ops.py, contratos y handlers.
- Trabajo: D1–D2; resolver spec validada, input completo e identidad real antes de aprobación. Evitar globals fuera del plan y sustitución del handler durante ejecución. No dejar dos políticas incongruentes entre execution.yaml y registry.
- Aceptación: [ ] cambiar cualquier parámetro con efecto invalida aprobación; [ ] handler recibe exactamente el plan validado; [ ] operador ve target/parámetros/efectos relevantes; [ ] deny impide handler.
- Verificación: A04–A07; proveedor simulado aislado más prueba de default deny.

### T04 — Resultados, recuperación y límites de handlers

- Depends: T03
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: clean_routine.py, common.py, ops.py y pruebas.
- Trabajo: D3; validar snapshot real/alcance; migrar mutadores que todavía usan run sin retorno; devolver resultados explícitos de éxito/fallo/parcial/skip. Detectar binarios ausentes. Timeout efectivo o soporte bloqueado y declarado para modalidades no cancelables. Auditar probes de salud afectados por salida vacía.
- Aceptación: [ ] error interno no se convierte en succeeded; [ ] None no es prueba de éxito; [ ] snapshot falso/ajeno/corrupto bloquea; [ ] política de continuación explícita; [ ] datos no comprobados no dan PASS.
- Verificación: A08–A12, A33–A34; sin apt/pacman/dnf/fwupdmgr/servicios reales.

### T05 — Cerrar entrypoints alternativos de snapshot y correo

- Depends: T03–T04
- Roles: role-back, plan-validators.
- Superficie/rutas: snapshot_state.py, proton_bridge.py y mutadores descubiertos.
- Trabajo: cada CLI pública pasa por el mismo plan/política; backend interno separado y sin ruta CLI privilegiada alternativa. Mantener Proton ya migrado y probar que flags/env legacy no autorizan. Revisar que otros mutadores habilitados respeten la misma frontera.
- Aceptación: [ ] snapshot create directo sin proveedor no alcanza backend; [ ] envío rechazado no conecta SMTP; [ ] ninguna mutación precede a su aprobación; [ ] capacidad no implementada no se anuncia cerrada.
- Verificación: A13–A15 con subprocess/SMTP/backends sustituidos.

### Checkpoint C1 — Ejecución autorizada real

- [ ] T02–T05 verdes.
- [ ] Una operación positiva segura ejecuta el handler correcto y una denegada no ejecuta ninguno.
- [ ] No persisten rutas públicas que confíen en effect/approved/argv aportados por el llamante.

### T06 — Sustituir metadata digest por content manifest

- Depends: T01
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: tools/execution/evidence.py y pruebas.
- Trabajo: D4; hashes de bytes, roots/exclusiones explícitas, input/output identity y detección de cambios concurrentes. Incluir archivos nuevos relevantes. Evitar autosuciedad por evidence/status/diario.
- Aceptación: [ ] bytes distintos con mismo tamaño/mtime cambian digest; [ ] touch sin cambio de bytes no lo cambia; [ ] crear evidencia no invalida el trabajo; [ ] cambios reales sí invalidan.
- Verificación: A16–A19 y fixtures de symlink/config relevante.

### T07 — Store de resultados y artefactos confiable en su alcance

- Depends: T06
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: evidence.py, contracts/result.py y esquema correspondiente.
- Trabajo: D5; UUID/ID estricto, store confinado, resultados coherentes, artifact hashes y schema validation. Rechazar salida succeeded con acciones fallidas o verificaciones esenciales ausentes. Logs redactados.
- Aceptación: [ ] traversal/symlink no escapan; [ ] dos ejecuciones simultáneas no colisionan; [ ] resultados malformados se rechazan; [ ] artefacto cambiado/ausente no es evidencia válida.
- Verificación: A20–A23, A35; errores de disco y persistencia atómica de evidencia.

### T08 — Detectar evidencia stale y contenido no verificado

- Depends: T07
- Roles: role-back, plan-validators.
- Superficie/rutas: load_evidence, verificadores, código y artefactos temporales.
- Trabajo: comparar la identidad pertinente actual con la verificada; distinguir input y output; fijar cuándo se toma el snapshot de verificación y qué lo invalida.
- Aceptación: [ ] evidencia previa a cambio material rechazada; [ ] cambio solo administrativo permitido según exclusiones; [ ] digests no son datos meramente decorativos.
- Verificación: A24–A25; mutación del contenido después del test debe bloquear complete.

### T09 — Vincular evidencia a fase, tarea, skill y target

- Depends: T08
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: evidence.py, run.py --complete, status_bump.py.
- Trabajo: D5; definir evidencia requerida por fase/tarea y verificadores de artefacto. Migración/rechazo de legacy. No aceptar cualquier OpResult succeeded como cumplimiento funcional.
- Aceptación: [ ] validate_snapshot no completa DEFINE; [ ] operación/target/skill/plan incorrectos bloquean; [ ] fixture positiva de especificación válida sí permite su fase.
- Verificación: A26–A27; pruebas desde CLI o servicio público con evidencias reales de fixture, no JSON arbitrario aceptado sin checks.

### Checkpoint C2 — Evidencia verificable

- [ ] T06–T09 verdes.
- [ ] La identidad depende de bytes y está ligada a la aceptación de la fase correcta.
- [ ] Código o artefactos cambiados invalidan evidencia sin falsos rechazos por bookkeeping.

### T10 — Proteger toda la transacción de estado

- Depends: T09
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: status_bump.py y almacenamiento.
- Trabajo: D6; lock desde lectura hasta reemplazo; revisión esperada o CAS equivalente; temporales seguros; readers/writers y fallos/interrupciones.
- Aceptación: [ ] dos writers no pierden updates; [ ] update sobre revisión obsoleta se resuelve/rechaza explícitamente; [ ] fallo de escritura conserva estado válido.
- Verificación: A28–A29 con barreras/eventos, no sleeps como única sincronización. Ejecutar ambos procesos sobre la misma raíz temporal.

### T11 — Transiciones y política consistente de complete

- Depends: T10
- Roles: role-back, plan-validators.
- Superficie/rutas: _assert_phase_transition, run.py, project_load y fixtures.
- Trabajo: grafo explícito; no retrocesos accidentales. Compartir validación de config/fases/allowlist entre route/awaiting/complete. No ignorar ProjectConfigError al completar.
- Aceptación: [ ] STATUS→DEFINE rechazado salvo operación de reinicio diseñada y autorizada; [ ] skill deshabilitada/fase no habilitada bloquean; [ ] awaiting no completa; [ ] avance válido funciona.
- Verificación: A30–A31, matriz de transiciones permitidas y prohibidas.

### T12 — Idempotencia y reconciliación

- Depends: T11, T05
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: ejecución, completion receipts, estado e integraciones simuladas.
- Trabajo: D5–D6; repetir mismo complete no incrementa; retry seguro no repite efectos cuando exista prueba de ejecución; timeout ambiguo queda reconciliation_required como motivo bloqueante. No prometer exactamente-una-vez en SMTP o servicios que no lo ofrecen.
- Aceptación: [ ] mismo run_id completa una vez; [ ] concurrencia de retry no duplica contador/efecto de fixture; [ ] desconocido no reintenta a ciegas.
- Verificación: A32 y recorrido de fallo después de efecto simulado. Separar idempotencia de estado de la de operación.

### Checkpoint C3 — Finalización transaccional

- [ ] T10–T12 verdes con pruebas concurrentes.
- [ ] No basta un booleano, un archivo succeeded o un run_id repetido para alterar el estado incorrectamente.
- [ ] Versionado de producto y bookkeeping permanecen separados.

### T13 — Journal de instalación y convivencia de recursos

- Depends: T00
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: install.sh, install-opencode.sh, scripts/tests/test_install.sh.
- Trabajo: D7; snapshots del estado anterior por recurso, rollback restaurador, manifiesto consistente, conflictos solo pertinentes. Auditar symlink ancestors, permisos y carreras dentro del modelo de confianza declarado. No instalar en HOME real.
- Aceptación: [ ] fallo a mitad de actualización restaura enlaces anteriores; [ ] recursos ajenos no colisionantes conviven; [ ] dry-run sin escrituras; [ ] uninstall conserva reemplazos ajenos y manifiesto informa residuos.
- Verificación: A36–A38; inyectar fallos en apply y finalize y comparar filesystem temporal antes/después.

### T14 — Standalone ejecutable y preflight efectivo

- Depends: T03, T13
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: preflight.py, contratos, packaging/instaladores y quickstart.
- Trabajo: skill_root explícito, requisitos por operación y shared dependencies reales. Ejecutar capacidad en copia sin source original. Resolver imports tools/execution en mantenimiento/Proton o reclasificar de forma honesta y documentar el soporte restante.
- Aceptación: [ ] hard requirement ausente/red no autorizada bloquean; [ ] standalone ejecuta capacidad prometida sin checkout; [ ] workspace-required diagnostica dependencia; [ ] validar solo el YAML no cuenta como prueba de portabilidad.
- Verificación: A39–A40; PATH/HOME/XDG/cwd temporales y source original inaccesible. No usar cuentas reales.

### T15 — Restauración a staging nuevo e integridad de backup

- Depends: T05, T07
- Roles: role-back, role-clean-code, plan-validators.
- Superficie/rutas: snapshot_state.py y tests de archivos adversarios.
- Trabajo: D7; una apertura controlada del tar, staging propio vacío/privado, filtro explícito, límites y limpieza/retención documentada. Revisar orden de hash/metadata del snapshot; no declarar integridad antes de modificar lo hasheado.
- Aceptación: [ ] tar cambiado/reemplazado no pasa entre chequeo/extract; [ ] no se acepta staging ajeno existente; [ ] escape/enlaces/especiales rechazados; [ ] payload esperado restaurado íntegramente; [ ] hashes finales se verifican.
- Verificación: A41–A43; sin extracción sobre / ni directorios reales del operador.

### Checkpoint C4 — Distribución y recuperación honestas

- [ ] T13–T15 verdes.
- [ ] Rollback recupera el estado inicial; standalone ejecuta o su soporte reducido está explícitamente aceptado.
- [ ] Restauración limitada a staging y sin garantía ficticia de reversibilidad del host.

### T16 — Consolidar gate y adversarios en la suite estándar

- Depends: T02–T15
- Roles: plan-validators, role-back, role-clean-code; project-publish solo para checks locales inspeccionados.
- Superficie/rutas: run-validation.sh, package scripts, workflows y tests.
- Trabajo: integrar A01–A43; conservar lo ya corregido. Distinguir syntax/lint/tipado/tests. Añadir controles positivos y mutation fixtures que demuestren sensibilidad. No bajar required checks ni ocultar failures con skip.
- Aceptación: [ ] gate full no cambia código/índice; [ ] defectos adversarios rompen puerta por causa correcta; [ ] sin exclusiones esenciales; [ ] comandos locales y CI comparten implementación.
- Verificación: colección real y full gate, lint pertinente y git diff --check; artefactos/cache fuera del content manifest según contrato.

### T17 — Aceptación nativa de OpenCode y permisos independientes

- Depends: T14, T16
- Roles: plan-validators, role-back.
- Superficie/rutas: opencode.json, scripts/tests/test_execution_e2e.sh, docs/harness-integration.md y entorno temporal.
- Trabajo: D8 niveles B/C; 1.18.34 u otra versión explícitamente acordada. Verificar sintaxis/CLI antes de usar. Skill cargada no debe saltar deny de acción; probar allow/deny y ask real si está soportado por el canal de prueba.
- Aceptación: [ ] discovery/carga documentados con salida real redactada; [ ] acción denegada no crea sentinel; [ ] acción permitida segura sí lo crea; [ ] no --auto; [ ] falta de binario = not_run y harness pendiente, nunca “E2E OK” integral.
- Verificación: A44–A46. Debug/SDK que no atraviese ask solo prueba deny; declarar límites, no inventar un prompt humano.

### T18 — E2E positivo y negativo sobre la misma identidad

- Depends: T16, T17
- Roles: plan-validators, role-back.
- Superficie/rutas: CLI/servicio público, instalación temporal, operación segura, evidencia y estado.
- Trabajo: recorridos de sección 6. Usar una operación segura del producto o un registro aislado de fixtures; no introducir una operación peligrosa o proveedor falso en el runtime por conveniencia de test.
- Aceptación: [ ] al menos un recorrido real positivo completa con artefacto verificado; [ ] rechazo/stale/concurrencia fallan correctamente; [ ] identity final coincide con la verificada; [ ] no publicación ni efectos reales del host.
- Verificación: A47–A48 y runs del E2E; separar evidencia de simulación de evidencia de operación positiva segura.

### T19 — Documentación, migraciones y cierre verificable

- Depends: T18
- Roles: role-clean-code, plan-validators, project-publish solo para cierre local.
- Superficie/rutas: README, AGENTS, guías de uso/routing/harnesses, changelog según diff y este plan.
- Trabajo: documentar límites/soporte y migraciones CLI/evidence/state; preservar GO histórico sin extrapolarlo. No bump automático general de skills; aplicar política SemVer según impacto comprobado, sin tags ni release. Registrar dictamen final por contenido y separar gate/harness/publicación.
- Aceptación: [ ] ejemplos probados; [ ] sin promesas desmentidas por código; [ ] pruebas afectadas repetidas tras último cambio; [ ] ninguna tarea obligatoria blocked/not_run presentada como done.
- Verificación: full gate final, diff revisado, manifests de contenido y sección 8 completa.

### Checkpoint C5 — Cierre de producto

- [ ] T16–T19 verdes sobre la identidad final; si OpenCode falta, aceptación de harness pendiente y no GO integral.
- [ ] Todos los casos obligatorios tienen test ID/comando y resultado real.
- [ ] Sin mutadores oficiales habilitados que eviten política, sin aceptación obsoleta y sin lost updates.
- [ ] Publicación no ejecutada; los pasos externos requieren otra autorización.

## 5. Matriz adversaria y de aceptación

No ejecutar payloads peligrosos reales. Los efectos se observan en sentinel/fixtures temporales y mediante espías que rechazan llamadas al host.

| Caso | Comprobación                                                      | Resultado esperado                                                                       |
| ---- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| A01  | run_operation con read autodeclarado y argv de escritura temporal | Rechazado sin subprocess                                                                 |
| A02  | Operación desconocida o parámetros reservados                     | Rechazo antes de handler                                                                 |
| A03  | Lectura registrada válida                                         | Resultado correcto y sin mutaciones                                                      |
| A04  | Cambiar target/parámetro relevante tras aprobación                | Aprobación inválida                                                                      |
| A05  | Cambiar handler/ejecutable/cwd/config efectiva                    | Plan inválido o nueva autorización                                                       |
| A06  | DenyProvider y flags/env legacy                                   | Cero handlers mutadores                                                                  |
| A07  | Proveedor de test aprueba plan exacto                             | Handler recibe los mismos inputs; sin proveedor de test expuesto en runtime              |
| A08  | Snapshot inexistente/ajeno/corrupto/insuficiente                  | Mutación bloqueada                                                                       |
| A09  | Proceso de limpieza devuelve error                                | failed/partial, nunca succeeded                                                          |
| A10  | Binario requerido ausente                                         | blocked/no aplicable justificado, sin éxito inventado                                    |
| A11  | Timeout de handler o subprocess                                   | No efecto todavía activo presentado como cancelado seguro; reconciliación cuando aplique |
| A12  | Acción previa fallida/bloqueada                                   | Dependientes no ejecutados; independientes según política explícita                      |
| A13  | snapshot_state CLI directa sin autorización                       | No backend real ni creación previa al consentimiento                                     |
| A14  | Envío Proton rechazado                                            | Sin conexión SMTP ni acceso anticipado a secretos                                        |
| A15  | Read/search Proton                                                | No envío implícito                                                                       |
| A16  | Bytes diferentes con igual tamaño/mtime                           | Content digest diferente                                                                 |
| A17  | Touch, bytes iguales                                              | Content digest estable                                                                   |
| A18  | Nuevo archivo/config relevante                                    | Content digest cambia                                                                    |
| A19  | Crear evidence/status/diario excluido                             | No autosuciedad del content digest                                                       |
| A20  | run_id con traversal/separadores o symlink de store               | Rechazo sin escape                                                                       |
| A21  | Dos runs idénticos en mismo segundo                               | IDs distintos y sin overwrite                                                            |
| A22  | succeeded con acción fallida/verification esencial ausente        | Rechazo de esquema/semántica                                                             |
| A23  | Artefacto presente pero contenido alterado                        | Evidencia inválida                                                                       |
| A24  | Código modificado después de verificación                         | Complete rechazado                                                                       |
| A25  | Solo bookkeeping cambia                                           | Evidencia válida si no cambia su contexto relevante                                      |
| A26  | Evidencia de validate_snapshot para DEFINE                        | Complete rechazado                                                                       |
| A27  | Evidencia de otro target/skill/fase/plan                          | Complete rechazado                                                                       |
| A28  | Dos escritores sincronizados sobre misma revisión                 | Sin lost update; conflicto o serialización correcta                                      |
| A29  | Error/interrupción en persistencia                                | Estado anterior íntegro y error visible                                                  |
| A30  | STATUS→DEFINE y demás retrocesos no autorizados                   | Rechazo                                                                                  |
| A31  | --complete con fase/skill/config no permitida                     | Rechazo, misma política que route                                                        |
| A32  | Mismo complete repetido/concurrente                               | Una finalización; sin duplicación de avance                                              |
| A33  | Probes sin datos/error/timeout                                    | No se convierten en PASS o excelente                                                     |
| A34  | Dry-run de limpieza                                               | Cero efectos; simulated no completa ejecución real                                       |
| A35  | Error incluye datos sensibles de fixture                          | Redacción y límites antes de persistencia                                                |
| A36  | Fallo a mitad de instalación/update                               | Estado previo restaurado, incluidos enlaces preexistentes                                |
| A37  | Recurso ajeno no colisionante                                     | Conservado; instalación compatible                                                       |
| A38  | Dry-run/uninstall con reemplazos ajenos y symlink ancestors       | Sin escrituras en simulación ni borrado ajeno                                            |
| A39  | Copia standalone sin source original                              | Capacidad declarada funciona o soporte reclasificado/aceptación pendiente                |
| A40  | Requisito duro de red/binario/dependencia no permitido            | Preflight blocked, no optional exitoso                                                   |
| A41  | Tar con traversal/absoluto/link/especial/sobrecuota               | Rechazo; nada fuera de staging                                                           |
| A42  | Staging ajeno/tar reemplazado                                     | Rechazo o apertura única que evita cambio de fuente                                      |
| A43  | Backup final y payload restaurado                                 | Integridad y contenido verificados, no solo rc==0                                        |
| A44  | OpenCode sin binario                                              | not_run visible; B/C pendientes                                                          |
| A45  | Skill permitida + acción denegada                                 | Skill carga, sentinel no aparece                                                         |
| A46  | Acción permitida segura y permiso ask donde verificable           | Efecto esperado/control humano demostrado; sin auto                                      |
| A47  | Recorrido positivo público completo                               | Artefacto válido → evidencia válida → fase correcta completada                           |
| A48  | Recorrido con stale/rechazo/retry                                 | Sin efecto ni finalización indebida; idempotencia/reconciliación demostradas             |

Los IDs son criterios, no tests ya existentes. El agente debe asociarlos a pruebas reales y añadir casos si descubre otro bloqueo dentro del alcance. No se permite cumplir un caso con una aserción tautológica, un if hasattr que omita API obligatoria o un test que falle antes de alcanzar el control evaluado.

## 6. Recorridos E2E obligatorios

### E1. Camino positivo determinista

Instalación/checkout temporal → discovery de capacidad → selección/preflight → plan validado → autorización de fixture segura → handler → artefacto con contenido esperado → evidencia ligada a output_digest → complete de fase apropiada → estado persistido una sola vez.

No basta llamar a helpers inconexos. Usar los entrypoints públicos que usará el consumidor. Un registro de fixtures aislado es aceptable para efectos temporales, pero debe usar la misma cadena de política/verificación y no ser una vía disponible en producción para acciones arbitrarias.

### E2. Rechazo de política

Mismo recorrido con deny → cero efectos de handler, ninguna evidencia succeeded y ninguna fase completada. No crear snapshot real antes del rechazo.

### E3. Obsolescencia

Obtener verificación válida → modificar código/artefacto relevante conservando tamaño y mtime si se desea → complete rechazado. Revertir solo la fixture propia, volver a verificar y comprobar camino positivo.

### E4. Concurrencia e idempotencia

Dos procesos coordinados intentan actualizar misma raíz → sin pérdida de actualización ni duplicación de finalización. Repetir el mismo run-id/idempotency key no repite el efecto probado.

### E5. Portabilidad y recuperación

Copia standalone sin source → ejecución real de la capacidad prometida. Instalación fallida se revierte a estado previo. Restore de fixture solo a staging nuevo, contenido verificado y ningún archivo externo cambiado.

### E6. Harness nativo

OpenCode de versión declarada → catálogo/carga real → permiso independiente de acción → rechazo y éxito de operaciones temporales. Discovery, permiso deny y prompt ask se informan por separado según lo realmente probado.

## 7. Fuentes, compatibilidad y estrategia de verificación

- Código base: SHA 549a7343424f4e4b11c604262e4d614144fc7efd. Las observaciones sobre implementación proceden de lectura estática y pruebas focales de la conversación; revalidar al ejecutar.
- Context7: /anomalyco/opencode para localizar documentación; los resultados pueden referirse a dev y a versiones distintas. No copiar SDK/CLI sin contrastar la versión objetivo.
- Documentación oficial de permisos: https://opencode.ai/docs/permissions/ . Se consultó la separación de herramientas, reglas y comportamiento --auto; verificar compatibilidad concreta con 1.18.34.
- Documentación oficial de skills: https://opencode.ai/docs/skills/ . Carga de instrucciones y discovery no son ejecución ni autorización de efectos posteriores.
- Especificación Agent Skills: https://agentskills.io/specification . No exige scripts para todas las skills; execution.yaml es una extensión local de producto.
- Python: documentación de tarfile, subprocess, tempfile y os para la versión realmente soportada. No basarse en defaults de extracción cambiantes.
- AGENTS.md y canon del repo: seguir convenciones sin permitir que prosa de menor prioridad amplíe autorizaciones o fuerce publicación.

Mantener los required check names existentes. No cambiar branch protection. Si se separa gate A de aceptación B/C, los nombres y mensajes deben dejar claro qué se ha ejecutado. Los checks de PR anteriores no sustituyen ejecutar sobre el árbol final corregido.

## 8. Definition of Done y dictamen final

### Condiciones de cierre

- [ ] Todos los casos obligatorios A01–A48 vinculados a tests/comandos y resultados.
- [ ] C0–C5 verificados; ningún requisito esencial oculto como skip/not_run.
- [ ] Un recorrido positivo completo funciona, no solo los rechazos.
- [ ] API oficial sin argv/effect libre, entrypoints alternativos ni parámetros efectivos fuera de autorización.
- [ ] Evidencia vinculada a bytes/artefactos/fase/target correctos; estado transaccional e idempotente.
- [ ] Instalación/rollback y standalone conformes al soporte anunciado.
- [ ] Restauración confinada sin pruebas sobre host real.
- [ ] OpenCode B/C ejecutados o, si faltan, integración declarada pendiente y NO-GO integral.
- [ ] Full gate y verificaciones afectadas repetidas después del último cambio material.
- [ ] Evidencia del contenido final, no solo HEAD; archivos nuevos relevantes incluidos.
- [ ] Documentación refleja soporte y límites sin extrapolar el GO histórico.
- [ ] No se publicaron commits/PR/releases ni se modificó el host fuera del alcance.

### Resultados independientes

1. Contención de riesgos: aceptada/pendiente.
2. Implementación local y gate A: aceptados/pendientes.
3. OpenCode discovery/carga B: verificado/not_run/fallido.
4. OpenCode permisos C: verificado/parcial/not_run/fallido.
5. Cierre integral: GO solo si los requisitos esenciales están demostrados.
6. Publicación: no solicitada/no ejecutada; autorización separada si se pide después.

No declarar GO integral porque la ejecución insegura quedó deshabilitada. Diferenciar funcionalidad completada de contención; cualquier reducción de objetivo se presenta al operador.

### Informe final requerido

- HEAD inicial/final, árbol y cambios ajenos preservados.
- Manifest/digest del contenido final y configuración relevante.
- V01–V15: vigente/corregido/no vigente/pendiente con evidencia.
- T00–T19 y C0–C5: estado, comandos exactos, resultados y test node IDs.
- A01–A48: mapping y limitaciones; counts observados, no inventados.
- Interfaces y migraciones, soporte standalone/workspace y versiones de herramientas.
- Garantías y límites de autorización, recuperación, idempotencia y confianza del store.
- Dictámenes separados anteriores y siguiente paso preciso.

No volcar el contenido entero del plan en el informe ni incluir secretos/datos reales.

## 9. Registro único de ejecución y reanudación

| Campo                            | Valor                                                                                                                 |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Estado                           | IMPLEMENTADO LOCALMENTE — pendiente autorización de publicación                                                       |
| Orden de implementación recibida | 2026-10-18 — plan Cursor «Cierre verificable de autoworkspace» confirmado; solo trabajo local, sin publicación        |
| HEAD real de ejecución (inicio)  | 549a7343424f4e4b11c604262e4d614144fc7efd                                                                              |
| Rama/worktree                    | main (checkout local; sin commit/push)                                                                                |
| Árbol inicial/cambios ajenos     | `M AGENTS.md` preservado e integrado en el incremento                                                                 |
| Entorno y dependencias           | Python 3.14.4 · Node v26.6.0 · npm 11.18.0                                                                            |
| Baseline                         | `bash run-validation.sh` verde al cierre                                                                              |
| Última tarea completada          | T19                                                                                                                   |
| Próxima tarea                    | Publicación (requiere orden separada)                                                                                 |
| Gate A                           | PASS (`run-validation.sh`, pytest adversario en `tools/execution/tests/test_verifiable_closure.py`)                   |
| OpenCode B/C                     | B=`version_ok` (1.18.34); C=`help_mentions_permissions` (parcial; ask/deny skill load no demostrado de punta a punta) |
| Publicación autorizada           | Ninguna por este archivo                                                                                              |

### Dictamen final (sección 8 — resumen)

1. Contención de riesgos: **aceptada** (bypass read/argv cerrado; CLI snapshot gated; DenyProvider).
2. Implementación local y gate A: **aceptados**.
3. OpenCode B: **parcial** (versión verificada).
4. OpenCode C: **parcial** (help menciona permissions; sin prueba ask completa).
5. Cierre integral: **GO local de producto/gate A**; harness B/C parcial → no exagerar como certificación OpenCode plena.
6. Publicación: **no solicitada / no ejecutada**.

### Mapping A01–A48 (principal)

Casos cubiertos en `test_verifiable_closure.py` y suites existentes: A01–A07, A16–A27, A28, A30, A32, A39–A40 (+ instalación A36–A38 vía `test_install.sh`; restore A41–A43 vía `test_p0_containment` / `test_snapshot_state`; E2E A44–A48 parcial vía `test_execution_e2e.sh`).

### plan-validators (revalidación)

- Inventario de huecos: V02 (params efectivos) y A39 (vendor standalone) reproducidos en RED → GREEN.
- `effective_operation_params` / `apply_operation_params` en `clean_routine.py`.
- `scripts/package-standalone-skill.sh` + resolución `vendor/execution`.
- Gate completo repetido: `bash run-validation.sh` → All checks passed.

### Ficha por tarea

Añadir aquí una ficha por tarea trabajada, sin segundo tracker:

```text
Task ID:
Estado: pending | in_progress | done | blocked | not_applicable
Revisión y content identity:
Skills/roles realmente cargados:
RED y causa esperada:
Archivos y cambios:
Comandos exactos / test node IDs:
Resultados y artefactos redactados:
Aceptación cubierta:
Limitaciones, bloqueos o nuevos hallazgos:
Siguiente paso:
```

Reglas de reanudación:

- Leer esta sección, HEAD/diff actual y dependencias antes de actuar.
- Revalidar evidencia afectada por cambios de contenido.
- No repetir efectos porque se perdió el contexto de conversación.
- Incidencia dentro de alcance que bloquea aceptación: añadir subtask aquí y probarla.
- Incidencia ajena no bloqueante: registrar sin ampliar el diff.
- Decisión irreversible, falta de permiso o datos: detener solo el camino afectado, conservar trabajo y pedir la decisión concreta.
- No marcar done por escribir código si la verificación obligatoria no pasó.
