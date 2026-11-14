# Project integration — projections and a worked reference case

## Projection rules

- A canonical, versioned schema plus projections is a decision, not a default:
  respect an existing canonical source; do not impose a new one without
  agreement.
- Notion and SQL exports are **projections**: they do not synchronize or
  validate data automatically. Design round trip, conflicts, permissions and
  recovery before integrating; test the projection before touching real data.
- Map explicitly and evaluate semantic loss. A label coincidence is not an
  identity; a projection may drop constraints the schema keeps.
- Conflicting edits: if the canon changed since the last capture, do not apply
  silently; open a review with both versions and record the decision.
- Provenance and freshness: every change generates a review record (author,
  date, reason) and can be reverted by version; new content hash on change.

## Reference case (read-only, Notion)

Project «Diagnosis y Actualización del Español-Castellano» (LinkML 1.12.1).
Useful patterns, not approved specifications:

- **6 layers**: input (target entries, manual source/entry cards) → acquisition
  (adapters by access type: documented API, linked vocabulary, wiki API,
  document without API, source without programmatic access) → normalization
  (assertion candidates with citation and locator; identity resolution; sense
  hierarchy and order; merge and deduplication) → canonical core (versioned
  schema, plain-text source of truth, queryable index, glossary) →
  verification (metamodel · lint · instance; integrity and provenance; domain
  coherence; extractor regression) → projections and return (editable view,
  SQL query, JSON-LD publication, change capture and conflict resolution) →
  governance (approval gate, licenses and access conditions, versioning and
  migration).
- **19 tables**: AGENTE, RECURSO, EDICION, CAPTURA, DOCUMENTO, SECCION,
  ATESTIGUACION, ASERCION, PALABRA, ACEPCION, USO, ORDEN, GLOSARIO,
  GLOSARIO_PALABRA, CORRESPONDENCIA, REVISION, TAREA, ENCABEZADO_CAMPO,
  REFERENCIA. Five exist as validated LinkML classes (Fichero, Fuente,
  Palabra, Acepcion, Uso); the rest are pending design.
- **Validators V01–V25** grouped in: schema contract (V01–V02, official
  `linkml validate`/`linkml lint`), shape and instance (V03–V07), identity and
  integrity (V08–V11, custom: the official validator does not cover them),
  provenance (V12–V15), domain (V16–V21), artifacts and freshness (V22–V25).
  Stop rule: the first blocker halts the flow; a cycle does not close if a
  verified validator stops being so.
- **Sources verified in the case**: BOE (public REST API for consolidated
  legislation and daily summary), Wikidata (SPARQL), Wikipedia/Wiktionary
  (MediaWiki API), RAE·DLE (no official API; reference-only use per
  robots/Content-Signal), CGPJ (no API). **No API does not authorize
  scraping**: usage terms and intellectual property are decided before writing
  an adapter and recorded in RECURSO.licencia and RECURSO.notas_acceso.

## Integration checklist

1. Identify the source of truth and the consumer of each projection.
2. Map entities and constraints; list what each projection drops.
3. Prototype the projection on demo data; verify round trip when required.
4. Define conflicts, permissions, recovery and audit trail before switching
   real data.
5. Record licenses and access conditions for every concrete source.
