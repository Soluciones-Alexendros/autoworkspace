# Generators — catalog and artifact verification

Catalog from the official docs (https://linkml.io/linkml/generators/). Check
the feature dashboard and the installed version before relying on any
generator; coverage differs per feature and per version.

## Unified CLI (LinkML 1.12)

```bash
linkml generate <generator> [OPTIONS] YAMLFILE
# example: linkml generate json-schema --top-class Catalog schema.yaml
```

Project generator (all default artifacts, selectable):

```bash
gen-project -d out -I python -I jsonschema schema.yaml
gen-project -X shex -d out schema.yaml
gen-project -A 'jsonschema: {top_class: Catalog}' -d out schema.yaml
gen-project --config config.yaml schema.yaml   # --mergeimports default on
```

## Catalog (documented generators)

| Group | Generators |
| ----- | ---------- |
| Data shapes | JSON Schema, ShEx, SHACL, YARRRML, Pandera |
| Linked data / RDF | JSON-LD, JSON-LD Contexts, RDF, OWL, SPARQL |
| Code | Python (dataclasses), Pydantic, Java, Go, TypeScript, Rust |
| Data interchange | ProtoBuf, GraphQL, OpenAPI |
| Storage | SQL DDL, SQLAlchemy, SQL Validation, BigQuery DDL, TypeDB/TypeQL |
| Docs and diagrams | Markdown documentation, ER diagrams, PlantUML |
| Tabular | CSV, Excel Spreadsheet, Yaml |
| Misc | Project Generator, Prefix Generator, SSSOM, TerminusDB |

## Conversion between data formats

```bash
linkml-convert -s schema.yaml data.json -o data.ttl     # JSON/YAML ↔ RDF/Turtle
linkml-convert -s schema.yaml -t ttl data.yaml
```

Loaders/dumpers: JSON, YAML, RDF (Turtle), TSV/CSV. When converting to or
from RDF, a schema path is required. Validation happens optionally between
load and dump.

## Verifying generated artifacts

1. Generate only what the case needs. A generated artifact is not proof of
   semantic equivalence: check coverage per feature (dashboard).
2. Test the output artifact: for JSON Schema, run a compatible validator over
   valid and invalid instances and compare constraints (required, enums,
   cardinality, top class).
3. For SQL DDL: check keys, cardinality and type mapping; the DDL is not a
   migration nor a deployed database.
4. For Python/Pydantic: import the module, load the demo instance, dump and
   reload (round trip when required).
5. For RDF/JSON-LD: verify the conversion preserves identity and values on the
   demo data.
6. Record generator version, command and coverage for each artifact.
