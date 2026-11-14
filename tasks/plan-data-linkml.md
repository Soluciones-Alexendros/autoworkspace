# Plan: Skill `data-linkml` (ramo `data`) — implementación

Spec validada: `tasks/SPEC-data-linkml.md`. Trabajo aprobado por el operador
(«Implementa»). Sin commits ni push (norma del operador); publicación y PR
quedan fuera de este plan.

## Componentes y dependencias

```text
T1 validador dominio data ──┐
T2 SKILL.md + T3 references + T4 assets ──┤
T5 scripts + smoke ───────────────────────┤
T6 router intents ────────────────────────┼──→ T7 catálogo/docs ──→ T8 verificación
```

- **T1** (XS) `tools/validate/skill_spec.py`: `DOMINIOS`, `SKILL_TOKEN_RE`,
  `ARROW_RE` aceptan `data`. Sin esto, `make validate` rechaza la skill.
- **T2–T5** (M) skill completa: `SKILL.md` (≤500 líneas/≤5000 tokens, H2
  canónicos), 7 `references/` planas, `assets/` (requirements pin, laboratorio
  mínimo válido/inválido), `scripts/` (bootstrap_arch.sh, linkml_env.py,
  validate_cycle.py) + `scripts/tests/smoke_sh.sh`.
- **T6** (S) `tools/skill-router/intent-map.yaml`: intents de modelado,
  validación, generación e instalación LinkML.
- **T7** (S) Catálogo: `generate.py --sync-docs` (README, TAXONOMY, índice),
  textos «17 skills en 5 dominios» → «18 en 6», dominio `data` en los closed
  sets de TAXONOMY.md, entrada en CHANGELOG.md.
- **T8** (M) Verificación completa: `make validate`, smoke, dry-run del
  bootstrap, bootstrap real con venv temporal + laboratorio LinkML real
  (instalación de `linkml==1.12.1` desde PyPI), idempotencia en segunda pasada,
  `route.py` con prompts típicos. Limpieza del venv temporal.

## Riesgos y mitigaciones

| Riesgo                                                                   | Mitigación                                                                                                                                        |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| El validador rechaza el dominio `data` en otras comprobaciones no vistas | T1 amplía las tres constantes conocidas; `make validate` completo en T8 confirma                                                                  |
| Formato del config de lint no verificado                                 | No se inventa: documentadas solo las opciones verificadas (`-c`, `-f`, `--ignore-warnings`, `--max-warnings`)                                     |
| Red/PyPI no disponible en T8                                             | El laboratorio real se intenta una vez; si falla por red, se registra `not_run` con evidencia y se reintenta; nunca se declara PASS sin ejecución |
| smoke del bootstrap requiere sudo                                        | El smoke ejecuta solo dry-run (sin sudo ni red); la prueba con sudo es manual en T8 con confirmación explícita                                    |

## Orden

Secuencial T1→T8 (cada pieza depende de la anterior). Sin trabajo paralelo:
es un solo implementador y las piezas comparten validación final.

## Checkpoints

- Tras T1: `make validate` sigue verde con las 17 skills actuales.
- Tras T5: `make validate` verde con la skill presente + smoke verde.
- Tras T8: todo verde + evidencia del laboratorio funcional.

## Verificación final (comandos)

```bash
uv sync --frozen --project tools
make validate
bash skills/data-linkml/scripts/tests/smoke_sh.sh
bash skills/data-linkml/scripts/bootstrap_arch.sh               # dry-run
bash skills/data-linkml/scripts/bootstrap_arch.sh --apply --verify --venv-dir /tmp/...
python3 tools/skill-router/route.py --interactive               # prompts de prueba
```
