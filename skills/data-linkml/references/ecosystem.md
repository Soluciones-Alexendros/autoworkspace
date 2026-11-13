# Ecosystem — tool decision map and maturity limits

Source: official docs (https://linkml.io/linkml/ecosystem.html) plus the
operator's internal LinkML inventory. Install only what the case requires:
start with the core and add components when a real need appears. Every
candidate must record: problem solved, owner, license, install path, version,
maintenance, dependencies, limits, security, simpler alternative.

| Need | Tool or technology | Role and limit |
| ---- | ----------------- | -------------- |
| Define a model | LinkML + YAML | Declarative schema of classes, slots, ranges, rules, vocabularies |
| Develop and generate | `linkml` package | Core toolchain: validation, utilities, generators |
| Use generated Python models | `linkml-runtime` | Runtime support, `SchemaView`; check per-generator deps |
| Consult the language | `linkml-model` | Metamodel and specification |
| Validate instances | `linkml validate` / `linkml-validate` | Engine-dependent strategy; the JSON Schema path does not cover every LinkML expression |
| Validate outside Python | JSON Schema + compatible validator | Generate from LinkML, test concrete rules, document coverage |
| Work with data in Python | Generated classes, Pydantic, runtime serializers | Objects, load/dump; do not confuse schema generators with instance serializers |
| Publish specifications | Documentation and diagram generators | Review fidelity and format of output |
| Linked data and graphs | JSON-LD, RDF, OWL, SHACL, ShEx, SPARQL | Related standards, not start requirements; separate conversion, shape generation and validation |
| Relational database | SQL DDL and SQLAlchemy generators; SQLite/PostgreSQL | Review identity, cardinality, type mapping; generated DDL is not a migration nor a deployed database |
| Transform between models | LinkML-Map | Declarative mappings; the project itself warns its model still evolves |
| Storage access | LinkML-Store | Layer over several backends; early-stage project per its authors |
| Model from spreadsheets | Schemasheets | Compiles sheets to LinkML; compare result with the canonical schema |
| Bootstrap from existing formats | schema-automator | Inferred schemas are hypotheses requiring human review |
| Start a project | linkml-project-copier | Template and lifecycle; check prerequisites and version |
| Data transformation | Koza; linkml-transformer | Related tools; verify scope, maintenance and compatibility |
| Ontologies and vocabularies | linkml-owl, OAK, SSSOM-py | Generation, vocabulary access, mapping management; label coincidence is not semantic identity |
| Assisted extraction | OntoGPT; OCR and external parsers | Candidate data from text; requires source, traceability, privacy review and validation |
| Interfaces and editing | DataHarmonizer; Valve/Nanobot | Curation/editing tools; coverage per product and version |
| Search and rendering | linkml-solr, linkml-renderer, plugin-link | Optional components |

## Rules for keeping the inventory honest

1. Consult the official catalog and repos at the start of any task that
   depends on concrete tools; this inventory is a starting selection, not a
   closed list.
2. Never assert that a version, CLI option, backend or integration exists or
   works without verifying it against the corresponding version.
3. When several output formats exist, check the generator feature dashboard
   and design specific tests: conversion may lose constraints or semantics.
4. Do not move sensitive content to external services without authorization.
