# Fixture plan

Not an active workspace plan. Used only by parser and scheduler tests.

```yaml aw-plan
schema_version: 1
plan_id: fixture-plan-v1
base_revision: "0000000000000000000000000000000000000000"
tasks:
  - id: fixture-read
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: []
    read_scope: [README.md]
    write_scope: []
    artifacts: [fixture-report]
    acceptance: [fixture-read-observed]
    verification: [fixture-check]
    on_failure: stop
```
