---
name: Corrección final y cierre de producto autoworkspace
overview: Corregir los hallazgos pendientes sobre 86a3ab47 y aceptar el producto mediante veinte criterios de cierre congelados, pruebas públicas, evidencia de contenido y compatibilidad real. Un único plan; sin publicación ni efectos reales sobre el host del operador.
todos:
  - id: f0-baseline
    content: "F0 · T00: preservar trabajo, fijar alcance y reproducir los defectos"
    status: pending
  - id: f1-evidence
    content: "F1 · T01–T03: evidencia estricta, aceptación semántica y content manifest completo"
    status: pending
  - id: f2-execution
    content: "F2 · T04–T07: consentimiento real, handlers verificables, recuperación y resultados"
    status: pending
  - id: f3-state
    content: "F3 · T08–T09: finalización transaccional, reanudación e idempotencia"
    status: pending
  - id: f4-distribution
    content: "F4 · T10–T12: journal previo a efectos, rollback real, standalone y tar seguro"
    status: pending
  - id: f5-acceptance
    content: "F5 · T13–T15: harness real, E2E público y cierre funcional del catálogo"
    status: pending
  - id: f6-close
    content: "F6 · T16–T17: release readiness, pruebas independientes y dictamen final"
    status: pending
isProject: false
---

# Corrección final y criterios de cierre completo de autoworkspace

### Propósito de este documento

- Corregir todos los hallazgos vigentes de la última revisión y las garantías anteriores que aún no quedaron acreditadas.
- Fijar AHORA qué significa producto completo, con criterios estables, pruebas y evidencias que no se sustituyen por resúmenes de un agente.
- Reutilizar la implementación actual; no abrir otra reorganización, taxonomía o plataforma.
- Un único archivo de especificación, tareas, aceptación y seguimiento. No crear SPEC.md, todo.md o tracker canónico adicional.
- Estado inicial: PLAN DISEÑADO; correcciones y pruebas de este incremento NO EJECUTADAS.

## 0. Identidad, base y mandato

| Campo                  | Valor                                                                                                           |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| Plan ID                | autoworkspace-product-closure-final-v1                                                                          |
| Fecha                  | 2026-10-18                                                                                                      |
| Repositorio            | Soluciones-Alexendros/autoworkspace                                                                             |
| Base remota comprobada | 86a3ab473a0b276f3ef0cf67ffee0356bf573921                                                                        |
| Incrementos revisados  | PR #16 y PR #17, integradas                                                                                     |
| Versión declarada      | 5.1.0; no constituye una release publicada por sí misma                                                         |
| Destino sugerido       | tasks/plan-product-closure-final.md                                                                             |
| Scope de aceptación    | Cadena de ejecución/evidencia/estado, instalación, distribución, catálogo declarado y OpenCode objetivo 1.18.34 |
| Publicación            | Fuera de autorización de este plan; readiness sí se verifica                                                    |

### Orden para lanzar en Cursor

> Implementa este archivo como único plan canónico. Empieza por T00, respeta dependencias y usa las skills aplicables. Reproduce cada defecto antes de corregirlo y verifica las rutas públicas reales, no copias de la implementación en tests. Registra aquí los comandos y resultados observados. No uses cuentas, secretos, correo ni mutaciones reales del host del operador. No hagas commit, push, PR, merge, tag o release sin autorización específica. No declares producto cerrado si falla o no se ha ejecutado algún criterio C01–C20.

Revisar/adjuntar este archivo no autoriza implementación. La orden expresa de implementarlo autoriza trabajo local en código y pruebas seguras. No autoriza actuaciones externas, costes de modelos, privilegios ni publicación.

### Límites y preservación

- No sudo, cambios en /etc, paquetes/servicios del host, firmware, restauración del host, SMTP real ni lectura de secretos reales.
- No reset --hard, clean -fd, force-push ni descarte de trabajo ajeno.
- No asumir que venv, HOME temporal o copia del repo aíslan rutas absolutas, red o credenciales. Inspeccionar hooks, imports, collection de pytest y scripts antes de ejecutar.
- Usar temporales, dobles de binarios/transportes y runners controlados que fallen ante operaciones reales no previstas. VM desechable o servicio externo solo con permiso específico y capacidad disponible.
- No implementar criptografía ficticia ni otro framework. El adversario con control del código y mismos privilegios queda fuera de una garantía de aislamiento OS; los entrypoints oficiales sí deben ser seguros según su contrato.
- No bloquear todas las funciones y llamar a eso producto terminado. Contención de seguridad y funcionalidad aceptada son resultados distintos.
- Conservar planes históricos. Este documento reemplaza únicamente el contrato de aceptación del nuevo incremento, no reescribe resultados anteriores.
- Si el destino existe con otro trabajo incompleto, resolver antes de escribir. Los todos de Cursor reflejan este archivo y nunca son otra fuente de verdad.

## 1. Criterios de cierre congelados

Estos criterios quedan fijados por este plan. No se suavizan durante implementación para que pase CI. Una modificación exige decisión explícita del operador y registro de versión, motivo e impacto. Un fallo nuevo dentro de estas garantías es una corrección pendiente, no excusa para mover el objetivo.

Estados por criterio: pending, running, PASS, FAIL, BLOCKED, NOT_RUN. FAIL/BLOCKED/NOT_RUN nunca equivalen a PASS. N/A solo cabe para una subprueba realmente fuera del alcance congelado, con regla verificable; no para un criterio C completo.

| ID  | Criterio obligatorio             | Condición binaria de PASS                                                                                                                                                                                                  |
| --- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C01 | Alcance e identidad              | Matriz de capacidades del catálogo congelada en T00; código, configuración, artefactos y pruebas ligados a la identidad final; cero regresiones funcionales no aceptadas                                                   |
| C02 | Evidencia estructural estricta   | Store y loader rechazan ausencia, vacío, tipo incorrecto o inconsistencia de campos obligatorios; no fail-open por faltar digest, fase, skill, target u operación                                                          |
| C03 | Aceptación semántica             | Cada fase exige sus artefactos y verificaciones; local_gates o validate_snapshot no sustituyen especificación/implementación; coincidencias exactas, no prefijos permisivos                                                |
| C04 | Contenido y artefactos completos | Bytes, tipos, symlinks de archivos/directorios y configuración relevante representados; lectura fallida invalida; contenido cambiado o fuera de raíz rechazado                                                             |
| C05 | Consentimiento efectivo          | Ninguna variable, flag, hash o JSON controlado por el solicitante se acepta como prueba independiente de aprobación; denegación impide backend/handler                                                                     |
| C06 | Plan efectivo y handler          | Inputs completos y validados, target, handler y configuración quedan ligados al plan aprobado; cambios entre revisión/ejecución se rechazan                                                                                |
| C07 | Resultados y tiempos reales      | Fallo, None, herramienta ausente, parcial y timeout se propagan; no éxito del wrapper; cancelación no deja una mutación oculta activa                                                                                      |
| C08 | Recuperación y salud honestas    | Snapshot comprobado y suficiente por operación; hashes finales válidos; sin promesa de reversibilidad inexistente ni PASS por error/salida vacía                                                                           |
| C09 | API única y política             | Ejecución libre cerrada; todas las CLIs mutadoras habilitadas usan política; contrato y registro coinciden; campos reservados/desconocidos rechazados                                                                      |
| C10 | Estado transaccional             | Read→validate→update→write bajo lock/revisión; ningún lost update; fallo/interrupción conserva estado válido                                                                                                               |
| C11 | Reanudación y transiciones       | Grafo explícito, allowlist/fases respetadas, awaiting_agent puede resolverse mediante evidencia válida sin edición manual ni bloqueo perpetuo                                                                              |
| C12 | Idempotencia y reconciliación    | Replay no duplica efectos/finalización; no vence silenciosamente por recortar 200 IDs; timeout ambiguo bloquea retry hasta reconciliar                                                                                     |
| C13 | Instalación recuperable          | Journal durable antes de cada efecto; fallo real durante apply/finalize restaura estado anterior y conserva recursos ajenos                                                                                                |
| C14 | Portabilidad ejecutada           | Paquete standalone ejecuta capacidad declarada sin source/PYTHONPATH del checkout; workspace-required declara y verifica dependencia; quickstart real funciona                                                             |
| C15 | Restore confinado                | Tar inspeccionado/extraído en una apertura controlada y staging nuevo privado; escapes/links/especiales/sobrecuotas rechazados; contenido y limpieza comprobados                                                           |
| C16 | OpenCode nativo                  | Versión objetivo, discovery y carga reales; allow/deny de skill y acción independientes; ask observado donde forma parte del soporte; ningún --help/--version sustituye permiso                                            |
| C17 | E2E y calidad                    | Camino positivo público completo más rechazos/stale/concurrencia/retry; tests ejercitan producto y no lógica copiada; suite/gate detectan defectos sembrados                                                               |
| C18 | Catálogo funcional y coherente   | Las 16 skills tienen contrato operativo y entrega verificable según modo agent/script/orchestrator; capacidades anunciadas están implementadas o reducción aprobada antes del cierre                                       |
| C19 | Documentación y migración        | Instrucciones/README/contratos/versiones/soporte/ejemplos coinciden; legacy inválido se migra/rechaza expresamente; ningún claim excede evidencia                                                                          |
| C20 | Release readiness y cierre       | Validación estricta de release preparada en repo desechable; skip/not_ready distinto de published; informe final por identidad y todos C01–C19 PASS; publicación externa pendiente no se confunde con defecto del producto |

### Definición exacta de GO

PRODUCTO COMPLETO = C01 ∧ C02 ∧ … ∧ C20 = PASS, sobre el mismo estado final verificado, sin bloqueantes de seguridad ni regresiones no aceptadas.

No hay un estado “GO local completo” que permita omitir C05, C07, C14, C16 o C17. Puede existir GATE_DETERMINISTA_PASS con aceptación integral pendiente. El informe debe usar esos nombres sin ambigüedad.

PUBLICADO es un estado adicional y externo: requiere autorización, tag/release reales y su verificación. No es necesario publicar para aceptar readiness; tampoco basta readiness para afirmar publicación.

## 2. Alcance funcional sin ampliaciones silenciosas

T00 transcribe en este archivo la matriz actual de operaciones de README, SKILL.md, execution.yaml y registro. Para cada fila: skill, operación, modo, efectos, entrada pública, soporte/entorno, handler o procedimiento agent, requisitos, salida y verificador. El alcance se congela antes de implementar.

Reglas ya fijadas:

- Se conservan 16 skills y 5 dominios. No añadir familias ni roles artificiales.
- Las skills agent no necesitan un script vacío: necesitan un procedimiento que un agente pueda ejecutar y una entrega comprobable. No confundir skill cargada con trabajo terminado.
- OpenCode es el harness principal obligatorio de aceptación, objetivo 1.18.34. Otra versión exige migración explícita, no pruebas mezcladas. Cursor es el entorno de implementación; no se proclama compatibilidad certificada con todos los harnesses por copiar carpetas.
- Standalone se acepta por ejecución fuera del source, no por existencia de vendor/execution. Si se reduce a workspace-required, registrar cambio de alcance y no declarar cumplida autonomía sin aceptación del operador.
- Host mutation: pruebas del producto con ejecutores controlados/temporales. Sin pruebas de backend real, no certificar compatibilidad de mutación con todos los sistemas anunciados. Para familias de SO publicitadas, exigir evidencia de adaptador/protocolo y especificar qué integración de backend quedó probada; una incompatibilidad esencial mantiene C18 pendiente hasta corregirla o aprobar una reducción concreta.
- AppArmor/SELinux, firmware, pass-cli, proveedores de red y escáneres no se habilitan ficticiamente. Enumerar soporte real, no un “blocked” genérico vendido como funcionalidad.
- Auditorías OWASP, legales, accesibilidad y salud entregan evidencia y límites; no certificación exhaustiva ni veredicto perfecto por ausencia de datos.
- SCA separa vulnerabilidades, malware, typosquatting, unused, outdated y SBOM; cada capacidad anunciada necesita herramienta/procedimiento/limitación verificable por ecosistema. No es obligatorio añadir un scanner nuevo si el procedimiento agent ya puede cumplir de manera honesta; sí es obligatorio demostrar la entrega anunciada.
- No autorizar costes o servicios/modelos externos implícitamente. Si una aceptación esencial requiere capacidad no disponible, declarar BLOCKED; no relajar el criterio.

## 3. Registro completo de hallazgos

Observaciones de partida; revalidar contra checkout real. Las reproducciones anteriores fueron focales, no una ejecución integral. Estado inicial de todos: POR REVALIDAR.

| ID  | Hallazgo                                                                                                                | Evidencia principal                           | Criterios | Tareas  |
| --- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | --------- | ------- |
| H01 | Loader acepta succeeded sin bindings/digest/esquema obligatorios                                                        | evidence.py::load_evidence                    | C02       | T01     |
| H02 | Gates genéricos/prefijos y verificaciones vacías pueden cerrar fases ajenas                                             | PHASE_EVIDENCE_OPS, store_result, complete    | C03       | T02     |
| H03 | Symlink de artefacto se comprueba después de resolve; raíces/store con componentes enlazados requieren confinamiento    | _artifact_record/evidence_dir                 | C04       | T03     |
| H04 | Manifest omite symlinks de directorio, ignora lecturas fallidas y no garantiza snapshot estable                         | content_manifest                              | C04       | T03     |
| H05 | AUTOWORKSPACE_EXECUTION_APPROVED=1 vuelve a actuar como consentimiento en CLI                                           | snapshot_state.py; clean_routine.py           | C05       | T04     |
| H06 | Params/globales, identidad **name** y objetos mutables no atan todo efecto al plan                                      | ops.py/registry/clean_routine/approval        | C06,C09   | T05     |
| H07 | Wrapper convierte None a 0; procesos/probes no propagan fallos; timeout Python no aplicado                              | _wrap, cleaners, common.py, ops               | C07,C08   | T06     |
| H08 | Snapshot válido solo por metadata incompleta; integridad puede cambiar al reescribir metadata tras hashes               | validate_snapshot, snapshot_state             | C08       | T07     |
| H09 | Journal escrito después de efectos; rollback probado con copia de lógica y no fallo del instalador                      | install.sh; test_install.sh                   | C13       | T10     |
| H10 | Instalador OpenCode sin transacción completa y con posibles efectos sobre enlaces no planificados                       | install-opencode.sh                           | C13       | T10     |
| H11 | Vendor/directorio existe pero autonomía funcional/imports/dependencias no probados                                      | package-standalone-skill.sh, preflight, tests | C14       | T11     |
| H12 | E2E fabrica OpResult/artefacto, no recorre selección→ejecución→verificación pública                                     | test_execution_e2e.sh                         | C17       | T14     |
| H13 | Help con permissions/versión puede terminar en E2E OK pese a B/C parcial                                                | test_execution_e2e.sh; docs harness           | C16,C19   | T13     |
| H14 | awaiting_agent puede impedir complete sin ruta de resolución; replay almacenado con horizonte limitado                  | status_bump.py/run.py                         | C11,C12   | T08,T09 |
| H15 | Release omitida diferenciada por tagged=false, pero faltan readiness estricto/motivos/tests de ausente-vacío-YANKED     | cut_tag.py, release.yml                       | C20       | T16     |
| H16 | Plan pendiente/implementado y GO local conviven; mapping parcial no demuestra A01–A48 completos                         | plan-verifiable-closure.md                    | C19,C20   | T17     |
| H17 | Salud puede interpretar error como limpio; cobertura y categorías no equivalen a verificación completa                  | common.py/probes/reportes                     | C08,C18   | T06,T15 |
| H18 | Promesas del catálogo superan en algunos casos procedimientos/adaptadores/deliverables verificados                      | README, SKILL.md, execution.yaml              | C01,C18   | T00,T15 |
| H19 | Retry de efectos y de finalización no son iguales; evidencia validada antes de lock puede quedar stale antes del commit | ops/evidence/status                           | C10,C12   | T08,T09 |
| H20 | Claims de registro único siguen sujetos a entrypoints, requisitos y contratos divergentes                               | CLIs habilitadas y registry                   | C09       | T05,T14 |

No reabrir defectos ya corregidos sin regresión: ejecución libre read está cerrada, UUID añadido, lock desde lectura mejorado, SHA-256 de bytes, tar de una apertura y staging propio, red dura bloqueada, versión README alineada. Probarlos para conservarlos, no volver a diseñarlos.

## 4. Reglas técnicas de implementación

### 4.1 Evidencia de esquema estricto y semántica

- Esquema versionado único aplicado al escribir Y al leer. Campos para complete: schema_version, run_id, operation_id, skill/versión, fase/tarea, target normalizado, plan_digest, input/output identity, outcome, resultados de acciones, verificaciones obligatorias y artefactos exigidos por la fase.
- Ausencia/vacío/tipo erróneo rechazan, no desactivan validaciones. Legacy no recibe defaults que lo conviertan en éxito.
- Match exacto y de catálogo; eliminar prefijos permisivos de aceptación. local_gates es prueba de gate, no implementación universal.
- Especificación/plan/implementación/validación/integración/estado tienen verificadores definidos por sus entregables. Un artefacto con “ok” no representa una spec funcional.
- OpResult sin ejecución real no se considera prueba E2E; fixtures de resultado solo para tests unitarios del store.
- Input digest antes de operación y output digest después de verificación; no fingir que ambos son idénticos porque no se capturó input. Si falta evidencia requerida, incomplete/blocked.
- Los hashes no autentican al actor que puede editar todo. No inventar firma como seguridad; sí validar origen/protocolo en los componentes de confianza declarados.

### 4.2 Contenido, rutas y carreras

- Hash de bytes determinista e identidad de tipo. Procesar dirnames symlink sin seguir escapes; política explícita por enlaces internos/externos.
- No resolver primero y luego preguntar si el path original era symlink. Validar componentes/raíz mediante lstat/no-follow o mecanismo equivalente adecuado.
- Archivo relevante ilegible o cambiado durante hash → error y reverificación, nunca continue silencioso.
- Exclusiones solo administrativas y justificadas; tests prueban que un archivo relevante no queda fuera por prefijo accidental.
- Store de evidencia y artefactos confinados, UUID validado, creación exclusiva/no-overwrite, temporales seguros. Ficheros y directorios intermedios no deben escapar por enlaces.
- Snapshot de contenido o verificación de estabilidad hasta el punto de aceptación. Un lock del YAML no bloquea ediciones del repo: revalidar identidad al aceptar y documentar la frontera sin exagerarla.

### 4.3 Consentimiento y ejecución

- CLI pública snapshot llama a política/proveedor real o rechaza la operación; backend interno no se habilita mediante env/flag.
- Reutilizar funciones internas sin CLI privilegiada alternativa; no pasar el problema a un token que el mismo agente genera.
- Normalizar todos los parámetros antes de aprobación y rechazar campos desconocidos. Handler recibe un objeto efectivo completo; no lee globals o entorno no incluidos para cambiar el efecto.
- Resolver callable/ejecutable antes de aprobación y fijarlo hasta ejecutar. No usar **name** como identidad suficiente (wrappers homónimos). Identidad de componente/código y callable congelado según diseño, sin convertirlo en sandbox ficticio.
- Proveedor muestra target, efectos y params completos relevantes, con redacción cuando hay secretos. No truncar silenciosamente lo que el usuario debe revisar.
- Handler devuelve resultado explícito. None no es éxito ni se convierte en 0. Procesos fallidos, ausentes y acciones omitidas mantienen su estado.
- Política de dependencias: un fallo o deny detiene dependientes. Independientes solo continúan de forma explícita.
- Timeout sobre subprocess y handlers con control efectivo; no un thread aún activo presentado como cancelado. Si se necesita worker, usar la solución mínima compatible con handlers/transportes y probar limpieza de descendientes.
- Mutadores reales del host siguen fuera de pruebas del operador. Usar transportes/ejecutores falsos y entornos desechables autorizados; no usar tests como excusa para tocar paquetes.

### 4.4 Recuperación, transacción e idempotencia

- Snapshot por target/host, backend, alcance e integridad; no aceptar metadata insuficiente. Revisar hashes antes/después de actualizar metadata; evitar autorreferencia accidental.
- Separar inventario, backup y recuperación. Logs eliminados/firmware no reversibles por tar de /etc. Sin rollback suficiente, política y advertencia específica; no garantía genérica.
- Estado bajo lock de lectura→validación→write con revision/CAS; evidencia válida hasta aceptación. Mantener código mejorado de PR16 y probar fallo/interrupción reales.
- Awaiting_agent debe resolverse mediante un evento/API público que verifica evidencia y permite complete; no editar YAML manualmente.
- Dedupe durable de finalización sin perder protección al recortar historial a 200. Guardar receipt por identidad/fase/tarea; un reset explícito no autoriza replay ajeno.
- Idempotency key de efectos distinta de run_id. SMTP sin exactamente-una-vez: timeout ambiguo requiere reconciliación; no prometer ni repetir automáticamente.

### 4.5 Journal, paquetes, tar y release

- Journal write-ahead: registrar y persistir estado previo/intención ANTES de alterar cada recurso, luego registrar aplicación. Errores y caída deben poder recuperar lo ya aplicado.
- No invocar rollback con un journal de otra ejecución. Validar/confinar sus paths y tipos. Lock de instalación o política de exclusión para concurrencia.
- Rollback y tests usan implementación real compartida, no algoritmo espejo en el test. Fault injection en puntos reales de apply/finalize; no || true para encubrir fallo que se pretende verificar.
- OpenCode installer toca solo names planificados; recursos ajenos no colisionantes intactos. Inventario y rollback para ambos destinos.
- Empaquetado standalone a destino explícito nuevo, sin mutar source para probar y sin rsync --delete sobre destino no validado. Validar nombre de skill y confinamiento; transitive deps, imports y herramientas documentadas.
- Ejecutar paquete movido en proceso limpio, sin repo/tools ni PYTHONPATH heredado; probar operación positiva segura y default deny.
- Restore: staging nuevo privado, una apertura controlada, rechazo de links/absolutos/traversal/especiales, cuotas antes de materializar todo lo que pueda agotar recursos, contenido comprobado y política de cleanup.
- Release en push ordinario puede ser skipped/not_ready; comando de readiness/release explícito debe fallar si faltan notas/validaciones. YANKED explícito es rechazo de publicar, no publicación exitosa. No publicar realmente en estas pruebas.

## 5. Tareas, dependencias y checkpoints

Convención: inspección → test RED significativo sobre código real → corrección mínima → GREEN → refactor → evidencia. Un test que solo comprueba helpers o no llega al control no satisface aceptación pública. Roles base: plan-validators, role-back y role-clean-code; plan-continue para arranque, project-publish para gates/readiness inspeccionados. Reevaluar por tarea; sin role-front/design si no hay UI.

### T00 — Preservación, alcance y baseline

- Depends: none
- Cubre: H18; C01.
- Trabajo: HEAD/rama/estado/untracked; preservar trabajo; inspeccionar scripts/hooks antes de baseline; completar matriz de capacidades sección 2 aquí; añadir reproducción de hallazgos no reproducidos.
- Archivos: este plan, lectura de AGENTS/README/skills/contratos/workflows.
- Aceptación: [ ] matriz congelada; [ ] entornos/requisitos/versiones registrados; [ ] baseline seguro separado de regresiones; [ ] ningún plan ajeno sobrescrito.
- Verificación: git rev-parse HEAD, git status --short --untracked-files=all, git diff --check; comandos de gate solo tras inspección.

### T01 — Esquema obligatorio de evidencia

- Depends: T00
- Cubre: H01; C02.
- Trabajo: esquema y loader/store comunes; rechazar campos ausentes/vacíos/tipos/versión/UUID incorrectos; migración explícita de legacy.
- Archivos: evidence.py, contracts/result.py y schemas/tests pertinentes.
- Aceptación: [ ] succeeded solo no pasa; [ ] falta de digest/binding rechaza; [ ] caso válido sí pasa; [ ] fallo no altera estado.
- Verificación: V01–V04.

### T02 — Verificación de fase y entregables

- Depends: T01
- Cubre: H02; C03.
- Trabajo: requisitos por fase/tarea y verificadores de artefacto; coincidencias exactas; no gate genérico ni prefijos como sustituto; verifications completas y coherentes.
- Archivos: evidence.py, run.py, status y verificadores nuevos mínimos si son necesarios.
- Aceptación: [ ] local_gates/validate_snapshot no completan DEFINE/IMPLEMENT por sí solos; [ ] spec/implementación positiva auténtica de fixture permite el avance correspondiente.
- Verificación: V05–V07; sin fabricar solo un resultado para el E2E.

### T03 — Manifest y confinamiento completos

- Depends: T01
- Cubre: H03–H04; C04.
- Trabajo: dir symlinks, errores de lectura, tipos, carreras, roots de artefactos/store y exclusiones; reutilizar SHA-256 actual.
- Archivos: evidence.py y tests con filesystem temporal.
- Aceptación: [ ] todas las modificaciones relevantes cambian identidad; [ ] touch no; [ ] lectura fallida no omite; [ ] links no evaden política.
- Verificación: V08–V12.

### Checkpoint F1

- [ ] T01–T03 PASS; [ ] pruebas negativas Y positivas; [ ] no evidence accepted por dato obligatorio ausente.

### T04 — Quitar consentimiento mediante env en snapshot

- Depends: T00
- Cubre: H05; C05.
- Trabajo: una entrada pública y backend interno; proveedor antes de efectos. Eliminar AUTOWORKSPACE_EXECUTION_APPROVED como habilitación, no renombrarla.
- Archivos: snapshot_state.py, clean_routine.py, registry/approval según diseño.
- Aceptación: [ ] flags/env/hash no autorizan; [ ] deny no llama backend; [ ] proveedor de test permite snapshot controlado sin host real.
- Verificación: V13–V15.

### T05 — Plan efectivo y consistencia del registro

- Depends: T04
- Cubre: H06,H20; C06,C09.
- Trabajo: entradas tipadas completas, callable fijo/identidad válida, contrato-registro coherentes, inventario de todas las CLIs habilitadas. Evitar inyección shell desde journal_time/snapshot_id u otros strings; procesos argv y validación de dominio.
- Archivos: ops.py, registry.py, approval.py, handlers/contratos.
- Aceptación: [ ] params desconocidos/reservados rechazados; [ ] cambio efectivo invalida consentimiento; [ ] entradas reales no leen globals ajenos al plan; [ ] sin bypass oficial.
- Verificación: V16–V19.

### T06 — Resultados, timeout y salud

- Depends: T05
- Cubre: H07,H17; C07,C08.
- Trabajo: sustituir wrapper None→0, migrar comandos con error oculto; ausencias/skip; dependencias y timeout efectivo; probes/reportes distinguen error de limpio.
- Archivos: clean_routine.py, common.py, ops.py, reportes/tests.
- Aceptación: [ ] fallo interno y timeout visibles; [ ] recursos/procesos terminados; [ ] ausencia no succeeded; [ ] sin puntuación plena por controles no realizados.
- Verificación: V20–V23.

### T07 — Snapshot e integridad final

- Depends: T04,T06
- Cubre: H08; C08.
- Trabajo: validar target/backend/coverage, integridad real y orden de escritura/hash; no vender reversibilidad imposible.
- Archivos: snapshot_state.py, validate_snapshot y tests.
- Aceptación: [ ] corrupto/ajeno/parcial insuficiente bloquea; [ ] snapshot final pasa su verificador; [ ] resultado separa inventario/backup/recuperación.
- Verificación: V24–V25; fixtures, no snapshots reales.

### Checkpoint F2

- [ ] T04–T07 PASS; [ ] toda ruta habilitada respeta política; [ ] éxito significa handler completado correctamente, no wrapper silencioso.

### T08 — Estado, bindings y resolución awaiting

- Depends: T02,T03
- Cubre: H14,H19; C10,C11.
- Trabajo: conservar lock completo; revalidación coherente de evidencia hasta aceptar; resolve awaiting público; allowlist/fases/transiciones homogéneas y esperado revision.
- Archivos: status_bump.py, run.py, evidence y tests multiproceso.
- Aceptación: [ ] sin lost update; [ ] stale no se acepta en ventana de lock; [ ] pending puede resolverse sin editar YAML; [ ] retroceso no autorizado rechazado.
- Verificación: V26–V28 con barreras y fallo/interrupción inyectados.

### T09 — Receipts e idempotencia durable

- Depends: T08,T05
- Cubre: H14,H19; C12.
- Trabajo: separar run/completion/operation idempotency; no perder garantía tras >200 completions; retry ambiguo de SMTP simulado requiere reconciliar.
- Archivos: status, evidence/receipts y ejecución.
- Aceptación: [ ] replay no duplica incluso tras compactación; [ ] writers concurrentes no duplican; [ ] timeout después de posible efecto no reenvía.
- Verificación: V29–V30; no claims exactamente-una-vez injustificados.

### Checkpoint F3

- [ ] T08–T09 PASS; [ ] reanudación positiva y retries negativos demostrados por API pública.

### T10 — Journal write-ahead y rollback de ambos instaladores

- Depends: T00
- Cubre: H09–H10; C13.
- Trabajo: persistencia previa a efectos y recuperación real; journal por run confinado; lock/conflictos; preserve/restore archivos, links y manifiesto anteriores.
- Archivos: install.sh, install-opencode.sh, tests públicos.
- Aceptación: [ ] falla segunda operación y recupera primera; [ ] finalize fail recupera previo; [ ] instalación anterior válida no se borra; [ ] dry-run idéntico; [ ] ningún test espeja el algoritmo.
- Verificación: V31–V33; comprobar bytes/tipos/targets/manifiesto antes y después.

### T11 — Paquete standalone real

- Depends: T05,T10
- Cubre: H11; C14.
- Trabajo: empaquetado a destino validado, bootstrap/imports y requisitos transitivos; preflight sobre la misma distribución; revisar Proton y mantenimiento y quickstart.
- Archivos: package-standalone-skill.sh, preflight.py, contratos/guías y tests.
- Aceptación: [ ] capacidad positiva segura en proceso nuevo sin source; [ ] default deny también en paquete; [ ] shared deps y binarios reales comprobados; [ ] skill path no escapa destino.
- Verificación: V34–V35, no directorio vendor vacío como sustituto.

### T12 — Restore seguro y cleanup

- Depends: T07
- Cubre: garantías de extracción aún no acreditadas; C15.
- Trabajo: conservar single-open/staging, cuotas/cleanup/retención y verificación efectiva de payload; evitar descompresión/metadata exhaustivas antes de comprobar cuota cuando sea relevante.
- Archivos: snapshot_state.py y tests tar adversarios.
- Aceptación: [ ] nada fuera de staging; [ ] contenido esperado; [ ] límites efectivos; [ ] no temporales sensibles huérfanos en fallo.
- Verificación: V36–V37.

### Checkpoint F4

- [ ] T10–T12 PASS; [ ] instalación/paquetes/restauración ejercitados realmente, sin lógica espejo.

### T13 — OpenCode B/C completo, no superficies help

- Depends: T05,T11
- Cubre: H13; C16.
- Trabajo: validar comandos disponibles contra 1.18.34, HOME/config temporal y sin --auto; discovery, carga de skill, acción permitida/denegada y ask por canal real cuando se ofrece; sentinel benigno.
- Archivos: scripts/tests/test_execution_e2e.sh, pruebas de harness y docs.
- Aceptación: [ ] cargar skill no salta permiso de acción; [ ] deny cero sentinel; [ ] allow crea sentinel; [ ] ask no actúa antes de decisión y rechazo no actúa; [ ] versión/help nunca PASS de permiso.
- Verificación: V38–V39. Si no se puede ejecutar, C16 NOT_RUN/BLOCKED y NO-GO integral. API debug que omite prompt solo prueba deny, no ask.

### T14 — E2E público y sensibilidad de la puerta

- Depends: T01–T13
- Cubre: H12,H20; C09,C17.
- Trabajo: recorridos sección 7 usando CLIs/servicios públicos, handler real de operación segura, verificador real y evidencia derivada; tests de mutación de fixtures para demostrar detección. No construir OpResult de éxito como sustituto de ejecutar.
- Archivos: tests E2E, run-validation.sh, integraciones.
- Aceptación: [ ] positivo completo; [ ] deny/stale/failure/retry reales; [ ] controles sembrados rompen gate; [ ] mismos módulos producción, mocks solo en bordes peligrosos.
- Verificación: V40–V42 y E1–E6.

### T15 — Aceptación funcional del catálogo congelado

- Depends: T00,T14
- Cubre: H17–H18; C18.
- Trabajo: ejecutar/probar procedimientos y entregas de las 16 skills según sección 6 y matriz T00; capacidades anunciadas sin soporte quedan pendientes o requieren reducción aprobada, no cierre por cambio de etiqueta.
- Archivos: skills/contratos, docs y tests según defectos reales.
- Aceptación: [ ] todas las filas del catálogo tienen ejecución/deliverable/verificador; [ ] límites y revisiones manuales explícitas; [ ] ningún binario ausente se convierte en informe sin hallazgos.
- Verificación: V43 y matriz por skill; no inventar certificación legal/seguridad universal.

### Checkpoint F5

- [ ] T13–T15 PASS; [ ] producto funciona de punta a punta y harness obligatorio probado.

### T16 — Release readiness explícito y estados de publicación

- Depends: T14
- Cubre: H15; C20 (readiness).
- Trabajo: separar push ordinario skipped/not_ready de release explícita estricta. Rechazar YANKED/errores; outputs reason/status; probar tag/notes en repo temporal y remoto local, sin GitHub.
- Archivos: cut_tag.py, release.yml, tests versionado y guías.
- Aceptación: [ ] notas ausentes/vacías no se publican; [ ] readiness falla mientras no están preparadas; [ ] ruta preparada crea tag correcto solo en fixture; [ ] omitido nunca published; [ ] filesystem/Git error no skip exitoso.
- Verificación: V44–V45.

### T17 — Revisión independiente y cierre único

- Depends: T15,T16
- Cubre: H16 y consolidación; C01–C20.
- Trabajo: revisar diff contra criterios, reconciliar estados del plan y mapping exacto; migraciones/versiones solo por cambios reales; full gate, lint/sintaxis/pruebas finales y smoke sobre distribución final. Segundo pase crítico separado del autor cuando haya recurso, sin tratar otra opinión LLM como prueba técnica.
- Archivos: este plan, README/AGENTS/guías/changelog y fixes necesarios dentro de alcance.
- Aceptación: [ ] 20/20 C PASS; [ ] evidencias por identidad final; [ ] sin residual esencial/skip; [ ] publicación no ejecutada; [ ] informe de sección 9.
- Verificación: V46–V48; todo cambio material invalida comprobaciones afectadas y obliga a repetir antes del GO.

### Checkpoint F6 — Cierre final

- [ ] T00–T17 y C01–C20 PASS.
- [ ] E1–E6 y V01–V48 con evidencia real.
- [ ] Cero bloqueantes de seguridad/corrección/operación; deuda no bloqueante explícita, aceptada y fuera del alcance congelado.
- [ ] Veredicto único PRODUCTO_COMPLETO_GO o NO_GO con IDs pendientes; no “GO dentro de límites” que esconda un criterio fallido.

## 6. Matriz mínima de aceptación del catálogo

Cada fila se desglosa con las operaciones existentes, sin añadir familias. Tests con fixtures y un agente real para procedimientos agent cuando esa sea la modalidad, no un script que siempre devuelva PASS.

| Skill                | Evidencia funcional exigida                                                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| plan-specification   | Spec aprobable, tareas con criterios y contratos; archivo único respetado cuando el operador lo pide; no sobreescritura de plan ajeno                                |
| plan-continue        | Selección/reanudación real desde status; consulta pura; init explícito; resolución de pending y handoffs con evidencia                                               |
| plan-validators      | Descubre comandos del fixture; reproduce bug/test RED; GREEN de cambio y suite pertinente; nunca cobertura=corrección automática                                     |
| local-maintenance    | Auditoría con errores visibles, cleanup controlado con resultados reales, snapshot por target y autonomía según paquete; sin efectos del host del operador           |
| local-security       | Postura/forense/plan con límites y outputs; mutación registrada o soporte reducido aceptado; sin shell injection de perfil y sin fingir enforce por imprimir comando |
| local-proton         | Read/search/mark/send separados; SMTP/secret stores de test; consentimiento por destino/contenido; timeout ambiguo no reenvía                                        |
| project-architecture | Repo fixture, mapeo/evidencia de dependencias y hallazgos trazables; herramientas/versiones y N/A fundamentados                                                      |
| project-libraries    | Matriz por ecosistema/capacidad, outputs de scanners y errores; SBOM estructuralmente válido si se anuncia; no prometer detección exhaustiva                         |
| project-publish      | Gates inspeccionados con efectos declarados; readiness de release; sin publicación no autorizada; skip distinto de fallo/publicado                                   |
| web-compliance       | Checks auto/manual/no evaluado, scoring verificable y remediación; no PASS integral por scan parcial                                                                 |
| web-owasp            | Edición oficial declarada y mapping coherente; hallazgos con path/evidencia y límites; no checklist vacío como auditoría completa                                    |
| web-performance      | Medición/config/versión/entorno y repeticiones; lab/campo distintos; error de herramienta visible; artefacto válido                                                  |
| role-front           | Implementación de UI en fixture únicamente si se prueba esta skill, contratos y verificación de superficies; no invocarla para desarrollar este backend sin UI       |
| role-back            | Implementación segura de API/datos fixture, tests y contratos; integración con plan-validators y entrega verificable                                                 |
| role-clean-code      | Refactor de fixture preservando comportamiento y contratos; pruebas/diff y límites de alcance                                                                        |
| role-design          | Entrega visual/tokens de fixture con verificación pertinente y coordinación; no script artificial ni evaluación visual afirmada sin revisar                          |

La matriz no obliga a construir una aplicación web nueva. Usar fixtures pequeños/reutilizables. Para skills agent, demostrar que el procedimiento produce una entrega útil y comprobable; no exigir que todo sea determinista ni confundir una instrucción con garantía ya ejecutada.

## 7. Pruebas obligatorias

Los IDs son aceptación fijada, no resultados. Asociar test node ID/comando, input, expected, observed y digest de artefactos. PASS solo con ejecución y aserciones del motivo correcto.

| ID  | Caso y resultado obligatorio                                                                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------- |
| V01 | JSON solo succeeded, aun con filename UUID → rechazo                                                                      |
| V02 | Omitir/vaciar individualmente cada binding/digest/campo obligatorio → rechazo                                             |
| V03 | Tipos/schema/UUID inconsistentes y legacy incompleto → rechazo o migración que no crea éxito                              |
| V04 | Evidencia estructural y semánticamente válida → aceptada                                                                  |
| V05 | local_gates/validate_snapshot para spec/implementación sin deliverable → rechazo                                          |
| V06 | Operación por prefijo, fase/target/skill/plan diferente → rechazo                                                         |
| V07 | Verificación requerida ausente/fallida o artefacto semánticamente inválido → rechazo                                      |
| V08 | Bytes distintos mismo tamaño/mtime → digest distinto; touch bytes iguales → estable                                       |
| V09 | Cambio de target de symlink de archivo/directorio → detectado o rechazado                                                 |
| V10 | Symlink de artefacto/ancestor/store fuera de política → rechazo, no normalización que lo oculta                           |
| V11 | Archivo relevante ilegible/cambio durante lectura → error explícito; no omisión                                           |
| V12 | Estado/evidencia administrativa cambia sin código → digest estable; nuevo archivo relevante cambia digest                 |
| V13 | CLI snapshot con env/flag/hash de autoaprobación → backend no invocado                                                    |
| V14 | Proveedor denegado/default deny → cero efectos previos ni posteriores                                                     |
| V15 | Proveedor de test aprueba operación segura exacta → backend controlado correcto                                           |
| V16 | Param desconocido/reservado/inválido/inyección en strings → rechazo antes de proceso                                      |
| V17 | Cambiar parámetro efectivo, target, config, executable/handler tras aprobación → rechazo                                  |
| V18 | Wrappers distintos con mismo **name** y mutación de params → no sustituyen plan aprobado                                  |
| V19 | Inventario de todas las CLIs mutadoras habilitadas → cada ruta atraviesa la política                                      |
| V20 | Handler None y wrapper que intenta convertirlo → no succeeded                                                             |
| V21 | Fallo interno de paquete/journal/temp/cache/SMTP y binario ausente → resultado exacto; no éxito silencioso                |
| V22 | Timeout/descendientes/handler → sin operación viva presentada como cancelada segura; reconciliación si efecto incierto    |
| V23 | Probes vacíos por error/permiso/timeout → no limpio/PASS/excelente; cobertura real publicada                              |
| V24 | Snapshot ajeno/corrupto/metadata insuficiente/recovery_scope insuficiente → bloqueo antes de efecto                       |
| V25 | Snapshot final autoverificado tras todas sus escrituras → hashes válidos y alcance de recuperación honesto                |
| V26 | Dos procesos con barrera sobre misma revisión → sin lost update ni duplicación                                            |
| V27 | Interrupción/error antes/después de replace → estado válido, error/recuperación trazables                                 |
| V28 | Awaiting_agent → evidencia válida → resolve/complete por API pública; sin edición manual ni deadlock                      |
| V29 | Replay inmediato y tras más de 200 completions/compactación → cero avance duplicado                                       |
| V30 | Efecto externo simulado seguido de timeout → sin retry ciego; reconciliación explícita                                    |
| V31 | Fallo REAL al segundo enlace del instalador → primer efecto restaurado gracias a journal previo                           |
| V32 | Fallo REAL de finalize/manifest → instalación anterior y recursos ajenos restaurados/preservados                          |
| V33 | Dry-run inexistente, conflicto/foreign/broken symlink, uninstall recurso sustituido y journal ajeno → sin daño externo    |
| V34 | Paquete movido, source original inaccesible, proceso limpio → operación positiva segura y deny funcionan                  |
| V35 | Nombre/target de empaquetado con escape, dependencia dura ausente o red no permitida → rechazo                            |
| V36 | Tar link/hardlink/absoluto/traversal/especial/sobrecuota → nada fuera de staging                                          |
| V37 | Tar válido → payload y hash correctos en staging nuevo; fallo limpia/retiene según política sin secretos huérfanos        |
| V38 | OpenCode discovery/carga real y acción deny → skill puede cargar pero sentinel no aparece                                 |
| V39 | OpenCode acción allow crea sentinel y ask espera decisión; rechazo no actúa; sin autoaprobación                           |
| V40 | E2E positivo público → preflight→plan→consentimiento→handler→artefacto→verificador→evidence→complete                      |
| V41 | Mismo E2E con deny/fallo/stale/retry → sin éxito ni finalización indebida                                                 |
| V42 | Defectos sembrados de auth/evidence/journal causan fallo del gate por el control evaluado, no import/entorno ajeno        |
| V43 | Matriz catálogo completa → cada claim tiene entrega, verificación y limitaciones; ausentes no PASS                        |
| V44 | Release sin notas/vacías/YANKED → no publicación; readiness estricto falla con motivo correcto                            |
| V45 | Release preparada en repo/remoto temporal → tag/notes/version correctos; fallo Git/FS es error, no skip                   |
| V46 | Plan, docs y contratos del contenido final coinciden con outputs observados; no tasks pending + completed contradictorios |
| V47 | Full gate local y misma implementación en CI; ningún requisito esencial oculto por skips/if/                              |     | true |
| V48 | Revisor comprueba C01–C20 y trazabilidad contra identidad final; cambio material posterior invalida acceptance afectada   |

### Recorridos de producto E1–E6

- E1 positivo: distribución temporal → discovery → entrada pública → preflight → autorización controlada → handler real de operación segura → verificación de contenido → evidencia → complete correcto.
- E2 rechazo: mismo flujo con deny/default → sin backend, sin artifact de éxito ni fase completada.
- E3 obsoleto: verificar, cambiar bytes/artefacto/binding y conservar tamaño/mtime → complete rechazado; reverificar permite el positivo.
- E4 concurrencia/reanudación: procesos coordinados y pending real → resolución, idempotencia durable y evidencia correcta; no editar YAML para arreglar el test.
- E5 distribución/recuperación: paquete fuera de source + fallo real de instalación/update + tar de fixture; conservación/restauración exacta, sin copiar algoritmos en tests.
- E6 harness: OpenCode objetivo real, skill loading y permisos independientes, allow/deny/ask; help/versión se guardan como diagnóstico, nunca como sustituto.

## 8. Fuentes, versiones y estrategia de ejecución

- GitHub confirma base 86a3ab473a0b276f3ef0cf67ffee0356bf573921 al preparar este plan. El agente repetirá la comprobación; no hay garantía sobre cambios locales no vistos.
- Context7 /anomalyco/opencode ayuda a localizar documentación, pero puede devolver dev y V1/V2 mezcladas. Verificar versión objetivo y --help antes de elegir comandos. No inventar flags ni APIs.
- https://opencode.ai/docs/skills/ y https://opencode.ai/docs/permissions/ respaldan separación entre cargar una skill y autorizar herramientas. Un debug que solo aplica deny no demuestra interacción ask.
- El estándar Agent Skills permite procedimientos sin scripts; execution.yaml sigue siendo una extensión propia del repo.
- Conservar nombres de required checks; no cambiar branch protection. Gate de desarrollo y aceptación de producto/harness/release readiness son estados separados y visibles.
- No afirmar compatibilidad, rendimiento, seguridad, legalidad o recuperación absoluta. El GO certifica los criterios definidos y el soporte expresamente probado, no ausencia universal de defectos.

## 9. Registro único y salida final

| Campo                       | Estado inicial                                                        |
| --------------------------- | --------------------------------------------------------------------- |
| Implementación autorizada   | Sí — orden expresa del operador (Cursor plan approved)                |
| HEAD/árbol de ejecución     | baseline 86a3ab473a0b; árbol con cambios locales del incremento       |
| Cambios ajenos preservados  | Pendiente de inspección                                               |
| Matriz de alcance congelada | Congelada en sección T00 (32 operaciones / 16 skills)                 |
| T00–T17                     | T00–T16 PASS (implementación+pruebas); T17 dictamen registrado        |
| C01–C20                     | ver informe final § cierre; C16 ask=NOT_RUN ⇒ no 20/20                |
| V01–V48 y E1–E6             | Ejecutados en pytest/shell; ver registro; E6 ask=NOT_RUN              |
| OpenCode real               | 1.18.34 version+deny observados; ask=NOT_RUN                          |
| Release readiness           | --check-readiness / --strict-readiness PASS en fixtures; sin publicar |
| Publicación                 | No autorizada/no ejecutada                                            |
| Próximo paso                | Decisión operador: canal ask OpenCode o aceptar NO_GO / reducción C16 |

Ficha por tarea (en ESTE archivo):

```text
Task ID / estado:
HEAD y content identity:
Skills/roles realmente cargados:
Hallazgo reproducido / RED / causa:
Cambio y archivos:
Comandos exactos y test node IDs:
Expected / observed / resultado:
Criterios C y casos V cubiertos:
Artefactos redactados y sus hashes:
Bloqueos, soporte y límites:
Siguiente paso:
```

### Informe final obligatorio

1. HEAD inicial/final y content manifest final (incluye código nuevo/config/distribución), versiones de herramientas y cambios ajenos preservados.
2. H01–H20: corregido/no vigente/pendiente, archivo/test y evidencia.
3. T00–T17, C01–C20 y V01–V48: mapping exacto, resultado y comando/test real. No números inventados ni porcentajes sin denominador.
4. Capacidad real por cada fila del catálogo y modo de distribución; compatibilidad probada y límites.
5. OpenCode discovery, load, action allow/deny y ask: resultados separados y evidencia, no palabra permissions de help.
6. Instalación/restore/idempotencia: escenarios reales de fallo y recuperación, no copia de lógica.
7. Readiness de release y estado de publicación por separado.
8. Dictamen único: PRODUCTO_COMPLETO_GO solo con 20/20 C PASS; de lo contrario NO_GO y lista concreta de criterios pendientes, sin rebautizar el alcance como éxito.

### Reanudación y nuevos hallazgos

Releer estado/HEAD/diff y evidencia antes de continuar. No repetir efectos por pérdida de contexto. Un defecto nuevo dentro de C01–C20 se añade como subtask en este archivo y se prueba. Una mejora opcional ajena se registra sin ampliar el incremento. Si falta permiso, capacidad o decisión de alcance, conservar trabajo y pedir la decisión precisa; no elegir por el operador ni suavizar el criterio.

## T00 · Matriz de capacidades congelada (2026-10-18)

- HEAD: `86a3ab473a0b276f3ef0cf67ffee0356bf573921`
- Árbol: limpio al baseline; OpenCode 1.18.34 disponible.
- Planes históricos conservados: plan.md, plan-verifiable-closure.md, plan-execution-closure.md, plan-executable-skills.md.

| Skill                | Op               | Kind         | Dist               | Effect               | Approval | Recovery | Dry-run |
| -------------------- | ---------------- | ------------ | ------------------ | -------------------- | -------- | -------- | ------- |
| local-maintenance    | health_check     | script       | standalone         | read                 | False    | False    | yes     |
| local-maintenance    | clean_routine    | script       | standalone         | mutate-host          | True     | True     | yes     |
| local-maintenance    | create_snapshot  | script       | standalone         | write-workspace      | True     | False    | yes     |
| local-maintenance    | restore_snapshot | script       | standalone         | mutate-host          | True     | True     | yes     |
| local-proton         | read_mail        | script       | standalone         | communicate-external | False    | False    | yes     |
| local-proton         | search_mail      | script       | standalone         | communicate-external | False    | False    | yes     |
| local-proton         | send_mail        | script       | standalone         | communicate-external | True     | False    | no      |
| local-proton         | access_secret    | script       | standalone         | access-secret        | True     | False    | no      |
| local-security       | posture_audit    | script       | standalone         | read                 | False    | False    | yes     |
| local-security       | harden_plan      | script       | standalone         | read                 | False    | False    | yes     |
| local-security       | apply_hardening  | script       | standalone         | mutate-host          | True     | True     | yes     |
| plan-continue        | route            | orchestrator | workspace-required | read                 | False    | False    | yes     |
| plan-continue        | init             | orchestrator | workspace-required | write-workspace      | False    | False    | yes     |
| plan-continue        | status           | orchestrator | workspace-required | read                 | False    | False    | yes     |
| plan-specification   | specify          | orchestrator | standalone         | write-workspace      | False    | False    | yes     |
| plan-specification   | plan             | orchestrator | standalone         | write-workspace      | False    | False    | yes     |
| plan-specification   | tasks            | orchestrator | standalone         | write-workspace      | False    | False    | yes     |
| plan-validators      | discover_stack   | agent        | standalone         | read                 | False    | False    | yes     |
| plan-validators      | red_green        | agent        | standalone         | write-workspace      | False    | False    | yes     |
| project-architecture | analyze          | agent        | standalone         | read                 | False    | False    | yes     |
| project-libraries    | sca_scan         | agent        | standalone         | read                 | False    | False    | yes     |
| project-libraries    | sbom             | agent        | standalone         | write-workspace      | False    | False    | yes     |
| project-publish      | local_gates      | script       | workspace-required | write-workspace      | False    | False    | yes     |
| project-publish      | publish          | script       | workspace-required | communicate-external | True     | False    | no      |
| role-back            | implement_api    | agent        | standalone         | write-workspace      | False    | False    | yes     |
| role-clean-code      | refactor         | agent        | standalone         | write-workspace      | False    | False    | yes     |
| role-design          | deliver_visual   | agent        | standalone         | write-workspace      | False    | False    | yes     |
| role-front           | implement_ui     | agent        | standalone         | write-workspace      | False    | False    | yes     |
| web-compliance       | auto_checks      | script       | standalone         | read                 | False    | False    | yes     |
| web-compliance       | manual_review    | script       | standalone         | read                 | False    | False    | unknown |
| web-owasp            | review           | agent        | standalone         | read                 | False    | False    | yes     |
| web-performance      | measure          | agent        | standalone         | read                 | False    | False    | yes     |

### Reproducción focal H01–H20 (estado al baseline)

- H01/H02: `load_evidence` acepta succeeded sin bindings; PHASE_EVIDENCE_OPS incluye local_gates + prefijos.
- H03/H04: resolve antes de is_symlink; content_manifest omite dir-symlinks y OSError.
- H05: AUTOWORKSPACE_EXECUTION_APPROVED=1 habilita create en snapshot_state CLI.
- H07: clean_routine._wrap convierte None→0.
- H09: install.sh escribe journal después de symlinks.
- H12/H13: E2E fabrica OpResult; help como permiso parcial.
- H14/H19: awaiting sin resolve público; completed_run_ids[-200].

### Registro de ejecución

```text
Task ID / estado: T00 PASS
HEAD y content identity: 86a3ab473a0b276f3ef0cf67ffee0356bf573921 (pre-implementación)
Skills/roles: plan-continue, plan-validators, role-back
Hallazgo reproducido: matriz y H01–H20 revalidados en checkout
Cambio y archivos: tasks/plan-product-closure-final.md (copia + matriz)
Siguiente paso: T01
```

## Informe final T17 (2026-10-18)

1. **HEAD**: baseline `86a3ab473a0b276f3ef0cf67ffee0356bf573921`; cambios locales del incremento pendientes de commit (sin push/PR/release — fuera de autorización de este plan).
2. **H01–H20**: corregidos en código + tests (evidencia estricta, fases exactas, manifest, CLI sin env-consent, handler identity, None≠éxito, snapshot metadata/hash, journal write-ahead, receipts durables, standalone `--dest`, readiness estricto, E2E público).
3. **T00–T17**: implementación local cerrada. Gate: `bash run-validation.sh --pytest-only --smoke-only` → **325 passed**.
4. **Catálogo**: 16 skills / 32 operaciones congeladas; `execution.yaml` por skill.
5. **OpenCode**: 1.18.34 version OK; deny-default observado; **ask = NOT_RUN** (sin canal interactivo). Help/version no se usan como PASS de permiso.
6. **Install/restore/idempotencia**: V31 fault-injection real + rollback compartido; `completion_receipts` sobreviven compactación; `resolve_awaiting_agent` público.
7. **Release readiness**: skip ordinario ≠ published; `cut_tag.py --check-readiness` / `--strict-readiness` fallan con motivo; **publicación no ejecutada**.
8. **Dictamen único: NO_GO** — C16 no es PASS mientras ask=NOT_RUN. Criterios restantes implementados y verificados en local; no se rebautiza el alcance como éxito.

```text
Task ID / estado: T17 PASS (dictamen NO_GO)
HEAD: 86a3ab473a0b276f3ef0cf67ffee0356bf573921 (+ working tree)
Skills/roles: plan-validators, role-back, role-clean-code
Gate: 325 pytest + smoke OK
C16 ask: NOT_RUN
Publicación: no autorizada / no ejecutada
Pendiente operador: cablear ask OpenCode o reducir C16 con aceptación explícita
```
