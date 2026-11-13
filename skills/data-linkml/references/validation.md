# Validation — layered strategy, CLI options, coverage limits

Command surface verified against official docs (https://linkml.io/linkml/cli/validate.html,
https://linkml.io/linkml/cli/lint.html) and the installed version's `--help`.
Never assert a flag exists without checking one of the two.

## Layers, in strict order

| Layer | Question | Command (LinkML 1.12) |
| ----- | -------- | --------------------- |
| 1. Syntax | Does the document parse as YAML? | YAML parser (any), no duplicate keys, no implicit conversions |
| 2. Metamodel | Is the schema a valid LinkML schema? | `linkml validate schema.yaml` (no `-s`: positional args are schemas) |
| 3. Lint | Quality rules (naming, recommended fields, canonical prefixes, root) | `linkml lint schema.yaml` |
| 4. Instance | Do data satisfy declared constraints? | `linkml validate -s schema.yaml -C TargetClass data.yaml` |
| 5. Dataset/domain | Coherence across records and sources | custom checks — not covered by the official validator |
| 6. Artifact | Does the projection preserve what is needed? | test the generated artifact; compare constraints on shared examples |
| 7. Evidence | Is the assertion substantiated? | primary source, date, location, human review |

## Verified options

```text
linkml validate [OPTIONS] [DATA_SOURCES]...
  -s, --schema <schema>        schema to validate data against
  -C, --target-class <class>   class within the schema to validate against
  --config <config>            validation configuration YAML file
  --exit-on-first-failure
  --fix                        normalize before validating (types coerced,
                               collection forms restructured); unfixable
                               issues are reported. Replaces deprecated
                               linkml-normalize.

linkml lint [OPTIONS] SCHEMA
  -a, --all                    process files starting with '.'
  -c, --config <config>        custom linter configuration file
  -f, --format <format>        terminal | markdown | json | tsv
  -o, --output <output>        report file name
  --ignore-warnings            exit 0 when only warnings
  --max-warnings <n>           exit 0 up to n warnings and no errors
  --fix, --no-fix
  (--validate, --validate-only: deprecated, no effect — metamodel validation
   always runs; use 'linkml validate' for structural-only checks)
```

The default lint configuration file is `.linkmllint.yaml` (rule keys: consult
the official linter docs for the installed version; do not invent them).

## Known coverage limits of the official validator

- **Global uniqueness** of identifiers within a class: not enforced.
- **Referential integrity**: a reference must point to an existing target,
  including nested levels: not enforced. A matching string is not integrity.
- **Orphan records, cross-record business rules, provenance completeness**:
  not enforced.

Pattern: keep the official layers 1–4, then add explicit custom checks (the
reference case in `references/project-integration.md` uses validators
V08–V25: uniqueness, referential integrity, orphans, provenance, domain rules,
artifact parity and freshness).

## Discipline

- A YAML parse is not "LinkML validation". Say exactly what ran and what did not.
- Record tool, version, command, files, result and limits for every cycle.
- Test the positive and the negative: missing required field, wrong type or
  enum, cardinality, duplicate id, dangling reference — only what the domain
  really demands.
- Do not call a self-made lint output proof that the official lint passed.
- Do not use `--fix` or destructive normalization without reviewing scope and
  getting authorization.
