---
name: data-linkml
description: "Model, validate, generate and evolve data schemas and instances with LinkML: schema authoring in YAML, metamodel validation, lint, instance validation, artifact generation (JSON Schema, Python/Pydantic, SQL, JSON-LD, SHACL, docs) and data conversion, with layered verification and provenance records. Arch Linux one-shot bootstrap (pacman + venv + pinned linkml==1.12.1). Use when the operator asks to model data, create or fix a LinkML schema, validate data or generate artifacts. Not for dependency audits (→ project-libraries) nor backend application logic (→ role-back). Uses Bash/Write for the local venv and generated artifacts."
license: MIT
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob, Bash, Write"
metadata:
  author: Soluciones-Alexendros
  version: "0.1.0"
  domain: data
  type: orchestrator
  language: en
  keywords: "data-linkml, linkml, schema, modelado de datos, validar datos, yaml schema, gen-project, pydantic, json schema, json-ld"
---

# Data LinkML

## Overview

Model data with LinkML and keep model, data and generated artifacts
verifiable. This skill covers the full cycle: domain design, schema authoring
in YAML, layered validation (syntax → metamodel → lint → instance → domain →
artifact), artifact generation, data conversion, and versioned evolution of
schemas. It provides a one-shot Arch Linux bootstrap that prepares a virtual
environment with pinned `linkml==1.12.1`, plus deterministic helpers that
record tool, version, command and result for every check.

Guiding discipline: a YAML parse is not LinkML validation; a generated artifact
is not semantically equivalent until checked; the official validator does not
cover global uniqueness, referential integrity or provenance — those need
explicit checks; and no command, flag or generator may be asserted without
verifying it against the installed version, the official docs or context7.

## When to Use

- Learning LinkML or bootstrapping a LinkML environment on Arch Linux
- Modeling entities, files, sources, records or compound objects as a schema
- Creating or fixing LinkML schemas (classes, slots, ranges, enums, URIs)
- Validating schemas and instance data, or debugging why validation fails
- Generating artifacts: JSON Schema, Python/Pydantic, SQL, JSON-LD, SHACL, docs
- Converting data between JSON, YAML, RDF/Turtle, TSV/CSV
- Evolving a schema with migrations, compatibility and rollback decisions

## Not for:

- Dependency audits, SCA or CVE scanning (→ project-libraries)
- Backend application logic, APIs or persistence (→ role-back)

## Workflow

1. **Frame.** Fix the operational question, consumer, boundaries, real example
   data, target formats and sensitivity. Distinguish conceptual model → LinkML
   schema → instances → generated artifacts. Ask only what changes the decision.
2. **Design the domain.** Entities with identity, attributes, relations and
   cardinality; lifecycle; inline vs reference by id; absence vs unknown vs
   not-applicable; units, currency, periods; closed vocabularies only when
   known. Separate entity / resource / concrete source / version / record, and
   attributed text from transcription and inference.
3. **Write the schema.** YAML with `id`, `name`, `prefixes`, `imports`
   (`linkml:types`), `classes`, `slots`; types, `required`, cardinality, ranges,
   enums; reuse slots by real meaning; one `tree_root` when the working format
   needs it; at least one valid and one invalid instance per critical rule.
4. **Verify and generate.** Strict order: YAML well-formed → `linkml validate`
   (metamodel) → `linkml lint` → `linkml validate -s -C` (instance, positive
   and negative cases) → domain checks LinkML does not cover (uniqueness,
   referential integrity, provenance). Generate only needed artifacts and test
   the output; do not assume equivalence between generators.
5. **Integrate and evolve.** Versioned canonical schema and projections;
   compatible vs breaking changes, migration, rollback and regression checks
   before touching shared contracts; treat Notion/SQL exports as projections
   with evaluated mapping loss; minimize sensitive data exposure.

Delivery format: summary (goal, recommendation, verification state), model,
artifacts with paths, tests (command, valid and invalid inputs, real result or
"not executed", uncovered rules), pending decisions. Answer in Spanish unless
asked otherwise. Record every run: environment and versions, inputs with hash,
exact operation, output and exit code, coverage, next step.

## Tools

| Script                      | Purpose                                                                              | Mode                        |
| --------------------------- | ------------------------------------------------------------------------------------ | --------------------------- |
| `scripts/bootstrap_arch.sh` | One-shot Arch setup: pacman → venv (`~/Projects/linkml/venvs/linkml`) → pip → verify | mutating (dry-run default)  |
| `scripts/linkml_env.py`     | Pre-flight: Python and LinkML presence/version                                       | read-only                   |
| `scripts/validate_cycle.py` | Layered validation 1–4 with report                                                   | read-only (runs linkml CLI) |

Exit codes: `0` OK, `1` error or negative verdict, `2` invalid input,
`3` missing dependency, `4` permission denied.

## Validation Strategy

Layers, in order (see `references/validation.md` for full detail):

| Layer          | Question                                     | Tool                                                  |
| -------------- | -------------------------------------------- | ----------------------------------------------------- |
| Syntax         | Does the document parse?                     | YAML parser                                           |
| Metamodel      | Is it a valid LinkML schema?                 | `linkml validate schema.yaml`                         |
| Lint           | Quality rules (naming, prefixes, root)       | `linkml lint schema.yaml`                             |
| Instance       | Do data satisfy declared constraints?        | `linkml validate -s schema.yaml -C Class data.yaml`   |
| Dataset/domain | Coherence across records and sources         | custom checks (not covered by the official validator) |
| Artifact       | Does the projection preserve what is needed? | test the generated output                             |
| Evidence       | Is the assertion substantiated?              | source, date, location, human review                  |

A valid schema does not certify truth. Stop on the first blocking error; never
promote `not_run` to PASS.

## References

- `references/installation.md` — Arch Linux bootstrap, venv, troubleshooting
- `references/ecosystem.md` — tool decision map and maturity limits
- `references/schema-authoring.md` — modeling rules and syntax patterns
- `references/validation.md` — layered validation, CLI options, coverage limits
- `references/generators.md` — generator catalog and artifact verification
- `references/official-sources.md` — canonical sources F1–F16 and verification policy
- `references/project-integration.md` — projections (JSON-LD, SQL, Notion) and a worked reference case

## Examples

> "Crea un esquema LinkML para estas fichas de fuentes y palabras, valídalo y dame JSON Schema"
> "No me valida este modelo: reproduce el fallo y dime la capa exacta"
> "Prepara el entorno LinkML en este equipo (Arch) y ejecuta el laboratorio"
> "Genera la proyección SQL del esquema y comprueba claves y cardinalidades"
