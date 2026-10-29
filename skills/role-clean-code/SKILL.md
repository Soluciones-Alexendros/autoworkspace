---
name: role-clean-code
description: "Implements Clean Code principles to write expressive, maintainable software and refactor existing code safely in any language. Use when the operator asks for 'clean code', 'código limpio', refactoring, meaningful names, smaller functions, fewer code smells, or cleanup of duplicated logic. Not for architecture-only assessments (→ project-architecture), test-suite audits (→ plan-validators), or security reviews (→ web-owasp). Uses Bash/Write for mutative refactoring."
license: MIT
metadata:
  author: Soluciones-Alexendros
  version: "7.0.0"
  domain: role
  type: atomic
  language: en
  keywords: "role-clean-code, clean code, código limpio, refactor, refactoring, refactorización, code smells, meaningful names, nombres significativos, small functions, funciones pequeñas, duplicated code, código duplicado"
  execution: role-clean-code
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob, Bash, Write"
---

# Role Clean Code

## Overview

Apply the fundamentals of Robert C. Martin's _Clean Code_ as an executable
engineering method. Produce readable, focused, idiomatic code and improve
existing code through small, verified transformations. Cleanliness is a means
to safer change and easier comprehension, not a line-count target or a license
to redesign.

## When to Use

- Writing new application logic that should be clear and maintainable
- Refactoring existing code without changing its observable behavior
- Improving names, function responsibilities, comments, error handling or duplication
- Applying a focused "boy scout rule" cleanup to code already in scope

**When NOT to use:** architecture-only analysis (→ project-architecture);
test strategy or suite assessment (→ plan-validators); security review
(→ web-owasp). For new behavior or bug fixes, lead with → plan-validators and
separate the behavioral change from subsequent cleanup. Use → role-front or
→ role-back when framework-specific implementation is the primary task.

## Operating Principles

- Project conventions and current language idioms override generic heuristics.
- Optimize for the reader, but preserve public contracts and observable behavior.
- Prefer small functions and classes by responsibility and cohesion, not by size alone.
- Remove duplication of knowledge; do not force superficially similar code together.
- Make intent explicit in code. Reserve comments for why, constraints and intent
  that cannot be expressed directly; delete stale or commented-out code safely.
- Handle errors deliberately and keep third-party boundaries understandable.
- Avoid speculative abstractions, mass rewrites and unrelated drive-by changes.
- A green formatter is not evidence of correctness; only relevant verification is.

## Process

### 1. Discover the project and bound the change

Read repository instructions, manifests, formatter/linter settings, test commands
and nearby implementations. Identify the language and framework versions, public
APIs, serialization or persistence contracts, generated code and performance- or
concurrency-sensitive paths. State the files in scope and the invariants to preserve.

### 2. Establish the safety net

Run the relevant baseline before editing. For existing code, read
[refactoring-protocol.md](references/refactoring-protocol.md) and choose the
verification path. If coverage is inadequate for the intended transformation,
characterize the current behavior through → plan-validators, narrow the change,
or ask before accepting risk. Never claim behavior was preserved when the checks
needed to support that claim were not run.

For new behavior or bug fixes, use → plan-validators first: reproduce or specify
the behavior with a failing test, implement the smallest change, then clean up
with tests green.

### 3. Select transformations by value

Inspect the target for misleading names, mixed abstraction levels, hidden side
effects, duplicated decisions, stale comments, swallowed errors and accidental
coupling. Use [core-principles.md](references/core-principles.md) for the
relevant practice and [smells-and-heuristics.md](references/smells-and-heuristics.md)
when a broader smell review is requested.

Read [systems-emergence-concurrency.md](references/systems-emergence-concurrency.md)
only when the scope includes system design, dependency composition, emergent
design, concurrency or successive refinement of a larger implementation.

Rank work by correctness risk and reader benefit. Leave unrelated or unverifiable
smells documented rather than expanding the diff without authorization.

### 4. Apply one understandable step at a time

Keep each transformation easy to review: rename with all references updated,
extract a cohesive responsibility, inline an indirection that hides intent,
introduce guard clauses, or isolate an external dependency. Run the focused check
after every meaningful step. Keep structural edits separate from behavior changes
whenever possible.

Do not introduce dependencies, concurrency, a new architecture or unfamiliar
language features merely to satisfy a heuristic. Consult current official
language/framework documentation when an idiom or semantic is uncertain.

### 5. Review and verify

Inspect the complete diff for accidental API, data, ordering, error and side-effect
changes. Update comments and documentation that describe the old structure. Run
the formatter/linter, focused tests and the full relevant suite using the project's
own commands. Repeat the safety-net checks after the final edit.

## Validation

A change is complete only when:

- The diff stays within the agreed scope and follows local style.
- Names and structure make intent easier to understand than before.
- No stale comments, dead code or duplicated decisions remain in the touched scope.
- Public behavior and contracts are preserved, or intentional changes are explicit
  and test-covered.
- Every available relevant check passes; anything not run is reported plainly.

## Output Format

Report concisely:

1. **Changes** — files and the Clean Code principle applied to each.
2. **Verification** — exact commands with pass/fail/not-run status.
3. **Contracts** — behavior/API changes, or "none intended" with evidence.
4. **Remaining** — out-of-scope smells, risks and follow-up recommendations.

## References

- [core-principles.md](references/core-principles.md) — names, functions, comments,
  formatting, objects/data, errors, boundaries, tests and classes.
- [systems-emergence-concurrency.md](references/systems-emergence-concurrency.md) —
  system composition, emergent design, concurrency and successive refinement.
- [refactoring-protocol.md](references/refactoring-protocol.md) — safety gates,
  characterization and behavior-preserving transformation workflow.
- [smells-and-heuristics.md](references/smells-and-heuristics.md) — prioritized,
  language-neutral inspection checklist.

## Related

- TDD, behavior changes and test-suite assessment → plan-validators
- Architecture analysis → project-architecture
- Frontend/backend implementation → role-front / role-back
- Security review → web-owasp
