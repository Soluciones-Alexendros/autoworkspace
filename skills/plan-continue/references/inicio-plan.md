# I — Inicio de plan (repo starting)

Punto de partida de cada tarea: un tablero canónico del repo **antes** de escribir el plan. Es el espejo de `project-publish` G (cierre de trabajo). `repo-starting` es el alias histórico; el procedimiento vive aquí.

Leer este fichero cuando el operador pida repo starting, inicio de plan, modo plan, «por dónde empiezo», o al abrir `/design` / `enter_plan_mode` sobre un repositorio.

## Autorización

Pedir este inicio autoriza, en el repo de la tarea:

1. `git fetch --prune` (sin merge si el árbol está sucio o divergente).
2. El escáner de `audit-repo.sh` y `inicio_plan.py` (solo lectura del árbol).
3. Escribir `inicio.json`, `ESTADO.md` y `ESTADO.html` **fuera** del repo, o copiar `ESTADO.md` al directorio de un plan nuevo (`.planning/<id>/`) si se inicia planificación persistente.

No autoriza: commits, PRs, tags, borrar ramas, `git clean`, ni implementar el trabajo. Eso espera al sí del plan y, al final, al modo G.

## Precondiciones

- Hay un directorio de trabajo. Si no es git, el tablero lo dice y el semáforo queda amarillo.
- `gh auth status` mejora el camino del producto (issues, PRs, runs); sin `gh` esas filas son `n/d`.
- Repo no archivado. Si lo es: parar y preguntar.
- Canon: [structure.md](../../../docs/REUTILIZACION.md).

## Secuencia

Ejecutar en orden. Un P0 de secreto o `.env` versionado detiene el diseño.

### 1. Sincronizar (Fase 0a)

Precondition: remoto `github.com` o anotar que es solo local. Action: `git fetch --prune origin`. Expected: fetch OK. Error: parar (clon posiblemente viejo). Recovery: sin `origin`, seguir en local.

Árbol sucio o divergente → preguntar. Solo detrás y limpio → `git pull --ff-only`.

### 2. Tablero (`scripts/inicio_plan.py`)

```bash
OUT=<directorio fuera del repo>
python3 "$SKILL_ROOT/scripts/inicio_plan.py" <repo> --profile <P0|P1|P2> --out "$OUT"
```

Action: el script corre `scan_repo`, `check-product-structure`, git y (si hay) `gh`. Expected: tres ficheros en `$OUT`. Error: exit 2 ruta inválida; exit 1 semáforo rojo. Recovery: leer `ESTADO.md` igual; no fingir verde.

### 3. Mostrar el estado

Presentar en el chat, en una pantalla:

- Semáforo y rama/SHA.
- Tabla **Estado del repo**.
- **Camino del producto** (ROADMAP, changelog sin publicar, issues/PRs, planes `.planning`).
- **Errores y fallos** (P0–P3). Si no hay, decir «Sin hallazgos».
- Ruta al HTML (`ESTADO.html`) para verlo en el navegador.

El informe largo de Fase 7 (`plantilla-informe.md`) queda para una auditoría completa, no para este arranque.

### 4. Abrir el plan

Con el tablero a la vista:

1. Si hay `task_plan.md` o `.planning/` activo: leerlo (`planificacion-archivos`) y reanudar.
2. Si no: crear el plan (`init-session` o `/design`). Copiar `ESTADO.md` al directorio del plan.
3. `enter_plan_mode` / `/design` **después** del tablero, no antes.
4. El plan nombra los fallos P0/P1 que hay que resolver o aceptar antes de implementar.

### 5. Handoff

- Implementar el plan → `execute-plan` / `codigo`.
- Terminar el trabajo → `project-publish` G (`cierre-trabajo.md`).
- Auditoría profunda del repo → seguir Fases 1–7 de `SKILL.md`.

## Entregable

```markdown
## Inicio de plan

| Campo      | Valor                                 |
| ---------- | ------------------------------------- |
| Semáforo   | verde / amarillo / rojo               |
| Rama       | `feat/…` @ `abc1234`                  |
| Estructura | OK / FALLO P1                         |
| Fallos P0  | 0                                     |
| Tablero    | `$OUT/ESTADO.md` · `$OUT/ESTADO.html` |
```
