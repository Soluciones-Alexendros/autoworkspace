---
name: plan-validators
description: "Drive implementation and QA with integrated tests: red-green-refactor, bug reproduction, test strategy, quality metrics and behavior coverage for routes, functions and jobs. Use when implementing or changing behavior, writing or reviewing tests, or planning coverage. Not for pure configuration, documentation or static content changes, nor production host debugging (→ local-maintenance). Uses Write/Bash for red/green project test suites."
license: MIT
metadata:
  author: "addyosmani (adapted)"
  version: "7.0.0-alpha.1"
  domain: plan
  type: atomic
  language: en
  keywords: "plan-validators, tdd, test coverage, qa"
  execution: plan-validators
compatibility: "cursor, pi"
allowed-tools: "Read, Grep, Glob, Bash, Write"
---

# Plan Validators

## Overview

Write a failing test before writing the code that makes it pass, reproduce bugs
before fixing them, and verify observable behavior through the repository's own
test suite. Test strategy, quality and coverage are part of the same workflow:
"seems right" is not done, and a coverage number without meaningful assertions
is not proof.

## When to Use

- Implementing any new logic or behavior
- Fixing any bug (the Prove-It pattern)
- Modifying existing functionality or adding edge case handling
- Planning, writing or reviewing unit, integration and end-to-end tests
- Assessing test quality, suite maintenance, metrics or coverage gaps

When NOT to use: pure configuration changes, documentation updates, static
content changes, or production host debugging (→ local-maintenance).

## Process

### 1. Discover the stack

The TDD cycle is universal; the commands are not. Before the first test,
learn how this repository tests: the language and build file (`package.json`,
`pom.xml`/`build.gradle`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`,
`Makefile`), checked-in wrappers (`./gradlew`, `./mvnw`, `make test`), the test
framework and its focused-test vs full-suite commands, test locations and
naming conventions, and documented commands in README, CONTRIBUTING, and CI
workflows. Never assume a default like `npm test`.

### 2. Inventory observable behavior

Before implementation, map every route, function and job introduced or changed
to the tests that prove its expected behavior:

- **HTTP and client routes:** methods, success responses, errors, authn/authz,
  navigation and sibling-route effects.
- **Functions and public units:** normal behavior, boundaries, invalid input and
  failure paths; test public outcomes rather than private implementation details.
- **Jobs, queues and scheduled work:** triggering, success, failure, retries,
  idempotency and observable side effects.
- **Critical cross-layer flows:** end-to-end proof through the real user or API path.

Record the inventory → test-case mapping in the spec, task or test names. Mark an
item N/A only with a reason. Add the cases to the repository's standard suite and
commands so they run with the rest of the project, not as disconnected ad hoc scripts.

### 3. RED — write a failing test

Write the test first. It must fail. A test that passes immediately proves
nothing — run it and confirm the failure.

### 4. GREEN — make it pass

Write the minimum code to make the test pass. Do not over-engineer.

### 5. REFACTOR — clean up

With tests green, improve naming, extract shared logic, and remove duplication
without changing behavior. Run tests after every refactor step.

### 6. Prove-It pattern for bug fixes

Do not start by fixing. Write a reproduction test first, confirm it fails
(bug confirmed), implement the fix, confirm it passes, then run the full
suite to check for regressions.

## Test Strategy and Quality

- Use the test pyramid: fast unit tests for logic, integration tests for API,
  database and filesystem boundaries, and a small number of E2E tests for critical flows.
- Shift tests left into each implementation task; keep the suite deterministic,
  isolated and maintained as production behavior evolves.
- Run focused tests during the loop and the complete suite before finishing.
  Track coverage when the repo supports it and do not decrease it without justification.
- Coverage is a gap-detection signal, not a target that justifies meaningless
  assertions or tests of third-party internals. Every changed behavior still needs proof.

## Tools

- Run the focused-test command during the loop; run the full-suite command
  before finishing.
- For code that runs in a browser, add runtime verification with Chrome
  DevTools MCP: DOM inspection, console logs, network requests, performance
  traces, and screenshots.
- For complex bugs, spawn a subagent to write the reproduction test without
  knowledge of the fix, then verify it fails before implementing the fix.

## References

- [test-pyramid-and-sizes.md](references/test-pyramid-and-sizes.md) — pyramid, test sizes, decision guide.
- [writing-good-tests.md](references/writing-good-tests.md) — state-based tests, DAMP, doubles, AAA, naming, anti-patterns.
- [rationalizations-and-flags.md](references/rationalizations-and-flags.md) — rationalizations, red flags, verification checklist.

## Examples

TDD cycle:

```text
// RED: fails because createTask does not exist yet
const task = await taskService.createTask({ title: 'Buy groceries' });
expect(task.status).toBe('pending');

// GREEN: minimal implementation
export async function createTask(input) {
  const task = {
    id: generateId(),
    title: input.title,
    status: 'pending',
    createdAt: new Date(),
  };
  await db.tasks.insert(task);
  return task;
}
// REFACTOR: clean up with tests green; re-run after each step.
```

Bug fix (Prove-It):

```text
// 1. Reproduction test — must FAIL before the fix
it('sets completedAt when task is completed', async () => {
  const task = await taskService.createTask({ title: 'Test' });
  const completed = await taskService.completeTask(task.id);
  expect(completed.completedAt).toBeInstanceOf(Date);
});
// 2. Fix: set completedAt in completeTask. Test passes; run full suite.
```
