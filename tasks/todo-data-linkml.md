# Tareas: skill `data-linkml` (ramo `data`)

- [x] T1: Ampliar validador para el dominio `data`
  - Acceptance: `skill_spec.py` acepta `metadata.domain: data` y prefijos `data-` en tokens y flechas; las 17 skills actuales siguen pasando
  - Implementation roles: role-clean-code (cambio quirúrgico de constantes)
  - Test surfaces: `python3 tools/validate/skill_spec.py`
  - Verify: `uv sync --frozen --project tools && uv run --project tools python tools/validate/skill_spec.py` → exit 0
  - Files: tools/validate/skill_spec.py

- [x] T2: SKILL.md de data-linkml
  - Acceptance: frontmatter conforme (name=data-linkml, domain=data, type=orchestrator, descripción con Use when/Not for y flechas válidas), cuerpo ≤500 líneas/≤5000 tokens, H2 Overview/When to Use/Tools presentes, sin H2 prohibidos
  - Implementation roles: role-clean-code
  - Test surfaces: skill_spec.py + skill_links.py
  - Verify: `make validate`
  - Files: skills/data-linkml/SKILL.md

- [x] T3: references/ (7 archivos planos)
  - Acceptance: installation, ecosystem, schema-authoring, validation, generators, official-sources, project-integration; enlaces solo a URLs oficiales verificadas (F1–F16) o archivos propios; sin subdirectorios
  - Implementation roles: role-clean-code
  - Test surfaces: skill_links.py (resolución de enlaces)
  - Verify: `make validate`
  - Files: skills/data-linkml/references/*.md

- [x] T4: assets/ (requirements + laboratorio mínimo)
  - Acceptance: requirements-linkml.txt con pin exacto linkml==1.12.1; schema-template.yaml válido contra metamodelo; instancia válida e inválida coherentes con el template
  - Implementation roles: role-clean-code
  - Test surfaces: laboratorio T8 (linkml validate/lint reales)
  - Verify: T8; pre-check YAML con parseador
  - Files: skills/data-linkml/assets/*

- [x] T5: scripts + smoke
  - Acceptance: bootstrap_arch.sh (dry-run por defecto, --apply, --venv-dir, --skip-pacman, --verify; exit codes canónicos; pip solo en venv), linkml_env.py (exit 3 si falta dependencia), validate_cycle.py (capas 1–4, positivo/negativo, informe MD/JSON); smoke_sh.sh cubre --help, py_compile y dry-run del bootstrap
  - Implementation roles: role-clean-code, plan-validators (RED: smoke falla antes de scripts)
  - Test surfaces: scripts/tests/smoke_sh.sh
  - Verify: `bash skills/data-linkml/scripts/tests/smoke_sh.sh` → exit 0
  - Files: skills/data-linkml/scripts/*

- [x] T6: Router intents
  - Acceptance: 4 intents (modelado, validación, generación, instalación) apuntando a data-linkml con patrones ES/EN
  - Implementation roles: role-clean-code
  - Test surfaces: route.py con prompts de prueba
  - Verify: `python3 tools/skill-router/route.py --interactive`
  - Files: tools/skill-router/intent-map.yaml

- [x] T7: Catálogo, taxonomía y changelog
  - Acceptance: TAXONOMY.md con dominio `data` en closed sets y 18 skills en 6 dominios; README.md «18 skills en 6 dominios»; bloques SKILL-INDEX regenerados; CHANGELOG.md con entrada
  - Implementation roles: role-clean-code
  - Test surfaces: check_catalog (paridad de bloques)
  - Verify: `make validate`
  - Files: docs/TAXONOMY.md, README.md, CHANGELOG.md (+ skill-index.json regenerado)

- [x] T8: Verificación integral con LinkML real
  - Acceptance: make validate verde; smoke verde; bootstrap dry-run correcto; bootstrap --apply con venv temporal instala linkml==1.12.1 y pasa linkml --version; laboratorio: metamodelo OK, lint limpio, instancia válida aceptada e inválida rechazada; segunda pasada idempotente; venv temporal borrado; route.py top-3
  - Implementation roles: plan-validators (evidencia), project-machineroom (cierre de cambio aprobado)
  - Test surfaces: run-validation.sh completo + laboratorio funcional
  - Verify: comandos del checkpoint T8 con salida registrada
  - Files: ninguno (solo ejecución y evidencia)
  - Result: PASS — evidencia en tasks/evidence-data-linkml.md. Pendiente único: borrado de /tmp/linkml-verify-venv bloqueado por path-guard (requiere autorización del operador; no se reintentó).
