# Schema authoring — modeling rules and syntax patterns

Core syntax verified against the official docs (tutorials 01–09,
https://linkml.io/linkml/schemas/models.html). Everything here is LinkML 1.12
compatible; verify against the installed version when in doubt.

## Minimum skeleton

```yaml
id: https://example.org/lab/cards        # provisional example URI — never present as published
name: lab_cards
prefixes:
  linkml: https://w3id.org/linkml/
  demo: https://example.org/lab/cards/
default_prefix: demo
default_range: string
imports:
  - linkml:types
classes:
  Catalog:
    tree_root: true
    attributes:
      sources:
        range: Source
        multivalued: true
        inlined_as_list: true
      words:
        range: Word
        multivalued: true
        inlined_as_list: true
  Source:
    attributes:
      source_code:
        required: true
      source_name:
        required: true
  Word:
    attributes:
      term:
        required: true
      source_ref:
        required: true
      definition:
        required: true
```

## Rules

- **Identity.** Decide the scope, stability and policy of identifiers. A
  readable label is not necessarily a stable identifier. Use `identifier:
  true` on real identity slots; a string coincidence is not referential
  integrity.
- **Composition vs reference.** Inline what is managed together
  (`inlined_as_list`, `inlined`); reference shared entities by id. Verify
  separately that targets exist and ids are unique.
- **Cardinality and required.** `multivalued: true`, `required: true`,
  `minimum_value` / `maximum_value` where the domain demands; test positive and
  negative cases per critical rule.
- **Ranges and types.** `string`, `integer`, `boolean`, `date`, `datetime`,
  `uri`, enums via `enum_range` or an `enum` class with permissible values.
- **Closed vocabularies.** Declare enums only when the value set is known and
  accepted; document each value. Do not claim semantic equivalence by name
  coincidence with external vocabularies.
- **Slots and inheritance.** Reuse slots when they share real meaning and
  constraints; check the effects of inheritance and redefinition (tutorial 07).
- **Root.** One `tree_root: true` container when the working format needs it;
  otherwise select target classes explicitly with `-C` and check behavior on
  the installed version.
- **Missing values.** Decide whether absent, `null`, zero and empty list mean
  different things in the domain; test how the chosen validation engine
  behaves.
- **URIs and mappings.** Keep example URIs explicitly provisional; declare
  `id_prefixes`, `see_also` and mappings only when the target exists.
- **Provenance.** For attributed content (definitions, etymologies, normative
  uses): text, assertion type, concrete source, fragment/locator, date,
  review state. Do not mix opinion, transcription and inference.

## Authoring discipline

Write one valid and one invalid instance per critical rule. Keep demo data
separate from real data and label unverified sources. Validate order: YAML
parse → metamodel → lint → instances (see `references/validation.md`).
