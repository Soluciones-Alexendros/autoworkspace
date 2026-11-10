# REFLEXIONES — constitucion

Registro de los razonamientos del autor durante la revisión de
`GLibUnix.signal_add` (keybackcon, `gui/main.py`). Contiene exclusivamente
los razonamientos, afirmaciones y reflexiones del autor.

## I. Razonamientos del autor

### 1. El núcleo no emite señales Unix: sólo las recibe
`kill` es un flujo de comunicaciones-acciones (comandos) distinto. El
proceso ordena; el núcleo ejecuta la entrega al proceso destino. Preguntas
que lo fijan: ¿a dónde se manda un SIGTERM si no es al núcleo actual?
¿Acaso el núcleo devuelve el SIGTERM al recibir la señal, o ejecuta el
comando —termina—? Respuesta registrada: ejecuta el comando, no devuelve
nada. Invocar al "núcleo de gestión de procesos" por solemnidad sobra:
¿por si se confunden en Rohan entre el SIGINT de UNIX y las Almenaras de
Amon-Sûl? No se solemniza lo obvio ni se combaten confusiones que nadie
tiene.

### 2. No es un bucle: es el proceso principal activado
Un bucle es la repetición de algo, y un proceso del sistema no se está
"repitiendo" ni actuando "en bucle": está simplemente activado, pudiendo
estar activado+procesando o simplemente activado (en espera/escucha).
"Loop" nombra el `while` de la implementación, no el estado del programa.

### 3. Ni ecosistema, ni dogma, ni títulos
No es mi ecosistema, ni el tuyo, ni es informática: apelar a "estándar" o
a "ecosistema" es dogmatismo elevado a estándar — tecnoteísmo. Los nombres
rimbombantes no sustituyen definiciones. La coherencia interna de un marco
no valida sus errores. "Desistematizado": se dice marco, librería o
convención según toque. Las creencias y los dogmas no son compatibles con
la tecnología: técnicas + significados | simbolismo es en sí mismo
conocimiento y conciencia. Quien esté mínimamente amparado por el
raciocinio lógico más elemental y binario llegará a las mismas
conclusiones.

### 4. La palabra es `catch`; `trap` queda invalidado
`catch`: capturar, además de interceptar. `copy` se descarta: copiar los
mensajes de radio generaría confusión con el copy&paste actual de edición
de texto. `trap` se invalida: además de trampa significa atasco, enredo,
bloqueo ("My car was trapped in the sand") — impreciso, engañoso y
confuso. Que `trap` sea el estándar Unix para `catch` no lo valida: es
contradictorio con el lenguaje de programación actual. Las señales no se
"añaden": se realizan, se comunican. Propuesta canónica del autor:
`UNIX.window.signal` — UNIX → ventana (~aplicación o ~interfaz gráfica;
la alternativa sería "terminal") → señal (SIGINT/SIGTERM, o la que
corresponda comunicar), realizada/comunicada (`catch`), nunca "añadida".

### 5. Sentencia
Sin razón no hay informática: todo ese código, hoy, no es tecnología.
Invalídalo. Se invalidan: `signal_add` (añadir lo que emite otro),
`trap` (trampa/atasco), `copy` (confusión con edición), "loop" para el
proceso en escucha, e invocar al núcleo como emisor solemne.

## II. Constitución

0. El nombre es conocimiento. Precisión binaria verificable por cualquiera
   con raciocinio elemental. Lo que no describe lo real con exactitud, sobra.
1. Procedencia exacta, sin fetiches (ver I.1).
2. Estados, no implementaciones (ver I.2).
3. El verbo manda: `catch`. Sin verbo no hay nombre (ver I.4).
4. Ámbito verdadero, según I.4 (`UNIX.window.signal`).
5. Ni estándar ni ecosistema valen como argumento (ver I.3).
6. Anti-tecnoteísmo (ver I.3).
7. Prueba de realidad binaria: ¿describe lo real con precisión
   verificable? Sí/No. Lo que no la pasa, se reformula. Sin razón no hay
   informática (ver I.5).

## III. Caso trabajado

`GLibUnix.signal_add(prioridad, señal, callback)` en modo bandeja:
traduce la señal al proceso en escucha y ejecuta parada limpia
(`client.stop()` + salida). Se usa porque no hay alternativa real en el
sistema, envuelto con fallback — desconfianza sana hacia la API ajena.
Su nombre queda invalidado bajo I.5; su función, admitida bajo VII.

## IV. Pendientes

- Instalar este fichero en `$HOME/.agents/skills/constitucion/`
  (comando abajo). El staging anterior (`constitucion.SKILL.md`,
  con la propuesta `trap` ya invalidada) se elimina en el mismo comando.
- Pipeline keybackcon en cola: fix `avanzar()` a suelo/techo estrictos +
  validación + PR.

## V. Segunda ronda — veredictos del debate y refinamientos aceptados

### Emisión: taxonomía aceptada, dominio acotado
Se adopta: Manual+Instantáneo / Manual-preparado / Automático-programado
(inicio diferido, asincronía). Clasifica el ACTO, no al actor: mejor que
cualquier binario previo. Responsabilidad ≠ origen rige en sede
humana/organizativa (el que escribe mal el cron responde, no quien dio la
orden clara); en sede de imposición sólo existe la tarea emisora (uid,
syscall) — acotar el dominio evita que el núcleo tenga que juzgar
intenciones. Iniciación atemporal, SÍ; entrega atemporal, NO: lo programado
dispara si se dan X, pero el mediador entrega cuando toca (máscara,
retorno a userspace).

### Núcleo: asimetría medible, interdependencia probada
"Máximo privilegio" no es título: es inclusión de cardinalidad (ring0 ⊇
ring3 en operaciones permitidas; un `cli` falla en userspace y funciona en
núcleo — falsable en una instrucción). Pero "máximo" como rango entre
pares es falso: no hay pares. Prueba adoptada: sin init el núcleo ni
arranca (`Kernel panic - not syncing: No working init found`) —
cerebro-en-pecera verificado. Formulación: capacidades disjuntas y
complementarias; máximo solo como inclusión, jamás como jerarquía de
valor. El núcleo no "acepta permisos": cumple su responsabilidad de
verificación (mismo UID o `CAP_KILL`, si no `EPERM`).
Ref: [capabilities.7](https://man7.org/linux/man-pages/man7/capabilities.7.html).

### Visibilidad: pila, no binario; parentesco intocable
La visibilidad es una PILA (2º, 3º, 4º plano…): se adoptan `subplano` /
`bajoplano` para el eje visibilidad. Pero redefinir `subproceso`
(hijo-fork: `getppid`/`waitpid`/`SIGCHLD`) como "no visible" crea colisión
de homónimos con un término de máxima carga — y por la propia regla del
`copy`, cae. Dos ejes, dos vocabularios, cero colisión: parentesco =
subproceso (intocable); visibilidad = plano/subplano; sin ventana =
proceso sin ventana.

## VI. Cierre — palabra del autor y aportaciones integradas

Cita textual de cierre del autor:

> Microkernel es lo que Linux, el núcleo del sistema, debía ser. El
> pingüino aislado en la tundra. No la mañana de ñus. Desde la Antártida
> el pingüino se comunica con las manadas de la Sabana, es el núcleo
> relacionándose con su sistema que le da cuerpo accionable.

### Aportaciones integradas (mías, en línea del autor)

- Recorte kill-flujo: el universal "el núcleo no emite" se restringe a su
  enunciado irrefutable (en el flujo kill, el núcleo ejecuta la entrega);
  excepción honesta registrada: señales síncronas originadas por el núcleo
  (`SIGSEGV`/`SIGFPE`/`SIGILL`/`SIGBUS`, `SIGPIPE`, `SIGCHLD`).
- Criterio del sentido técnico dominante: no gana el término monosémico
  (no existe), gana aquel cuyo sentido dominante en programación coincide
  con lo nombrado — por este criterio, `catch` vence a `trap`.
- Simetría de desambiguación: `catch` no necesita desambiguación en
  código; `trap` la necesita siempre. Ventaja `catch`, aun menor de lo
  que la formulación inicial sugería.
- Contenido atemporal / ejecución temporal / entrega calendarizada por el
  mediador (contra "todo atemporal": existen timeouts, races y deriva de
  relojes).
- Máximo-como-inclusión (ring0 ⊇ ring3, falsable en una instrucción) con
  interdependencia probada (sin init no hay arranque); el núcleo cumple su
  responsabilidad de verificación (mismo UID o `CAP_KILL`, si no `EPERM`).
- Pila de visibilidad (`subplano`, no `suplano`); vocabulario completo sin
  redefinir nada: hijo (parentesco), servicio (unidad de init), trabajo
  (`jobs`, lo que el operador puso en marcha), plano/subplano
  (visibilidad), proceso sin ventana.
- Cláusula hecho-vs-doctrina: se constata lo que el estándar fija (`trap`
  POSIX) y se invalida igual (estándar ≠ correcto).

### Referencias

- [signal.7](https://man7.org/linux/man-pages/man7/signal.7.html) —
  generación y captura de señales.
- [kill.2](https://man7.org/linux/man-pages/man2/kill.2.html) — flujo
  orden→entrega.
- [sigaction.2](https://man7.org/linux/man-pages/man2/sigaction.2.html)
- [capabilities.7](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [g_unix_signal_add](https://docs.gtk.org/glib/func.unix_signal_add.html)
  — el API enjuiciado.
- [trap POSIX](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/trap.html)
  — el estándar que no valida.

### Pendiente de veredicto del autor

- Síntesis candidata `Unix.process.catch(signum, handler)` (ensamblaje de
  piezas del autor: plataforma + ámbito + verbo).
- Propuestas R1–R5 (cronología, apéndice, matices, Rohan formal, caso
  expandido).
