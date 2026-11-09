# Autoworkspace plan template

Keep the narrative specification and this single structured block in the same
canonical document. Replace the fixture IDs and scopes before activation.

```yaml aw-plan
schema_version: 1
plan_id: my-plan-v1
base_revision: "0000000000000000000000000000000000000000"
tasks:
  - id: first-task
    phase: IMPLEMENT
    operation: implement_api
    roles: [role-back]
    depends_on: []
    read_scope: [README.md]
    write_scope: [src/]
    artifacts: [task-patch]
    acceptance: [observable-outcome]
    verification: [project-test-command]
    on_failure: stop
```
