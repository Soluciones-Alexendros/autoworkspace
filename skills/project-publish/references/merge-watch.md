# Fase F — Remediación y merge-watch (escuchar, no vigilar)

Cuando la auditoría deja `BLOCK` remediables o el usuario pide aplicar correcciones de `/project-publish`, esta fase es **parte del workflow**, no un favor opcional.

## Cuándo aplica

- El usuario dice sí a remediación de pipeline / labels / docs de cierre.
- El usuario pide mergear / auto-merge tras abrir PRs de remediación o de cierre BUILD.
- Modo **cierre con publicación**: tras el PR de changelog/version bump.

No aplica en modo **auditoría pura** (solo informe).

## Autorización

Un sí a «aplica remediación», «abre el PR» o cierre BUILD autoriza:

1. Commits en rama de trabajo (`chore/project-publish-*`, `cursor/*`, etc.).
2. Push + PR (draft si el plan lo pide) a `main`.
3. **Auto-merge con squash** + suscripción a eventos (ver abajo).

Sigue exigiendo sí aparte: borrar labels legacy, tags, `gh release create`, rulesets, rotar secretos.

## Política de merge (normativa de flota)

| Permitido                                         | Prohibido                                      |
| ------------------------------------------------- | ---------------------------------------------- |
| `gh pr merge <n> --auto --squash --delete-branch` | `--merge`, `--rebase`                          |
| Esperar checks required vía auto-merge            | `--admin` / bypass de protección o merge queue |

Canon: [ADR-0012](../../../docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md),
`templates/product/AGENTS.md` §5, `AGENTS.md` del host. Si el ruleset del
repo no admite squash, documentarlo en el informe y **parar** (no inventar
`--merge`).

## Flujo: publicar y escuchar

Tras abrir el PR (y `gh pr ready` si deja de ser draft):

1. Activar auto-merge:

```bash
gh pr merge <n> --auto --squash --delete-branch
```

2. Suscribir la conversación del agente (Cursor):

- `subscribe_github_ci` → `repo: owner/name`, `branch: <head-del-PR>`
- `subscribe_github_pr` → `scope: pr`, mismo repo + `pullNumber` (o `prUrl`)

3. Declarar en una frase qué se espera (CI terminal o PR merged) y **terminar el turno**.
   No hacer `gh pr checks --watch` ni bucles de polling: el aviso llega como notificación.

   En Cursor (usuario): `~/.cursor/hooks.json` → `beforeShellExecution`
   (`shell_gate.py`, `failClosed`) cubre mutación de host y red; **no** impone
   el método de merge de `gh pr merge`. La norma de squash vive en esta skill,
   en el canon de flota y en la regla de usuario «Flota GitHub: auto-squash».
   Si se añade un hook de política de PR, debe exigir `--squash` y denegar
   `--merge` / `--rebase` / `--admin` (no al revés). El aviso de fallo/éxito
   lo emiten `subscribe_github_ci` / `subscribe_github_pr`.

4. Cuando llegue el evento:

- **CI failure** → corregir en alcance del PR, push (`--force-with-lease` solo si rebase local lo exige; nunca `--force`), reactivar `--auto --squash` si hace falta, volver a suscribir si la suscripción se cerró, terminar turno otra vez.
- **PR merged** → limpieza de ramas/worktrees (`cierre-trabajo.md` paso 6); actualizar informe.
- **PR closed without merge** → informar bloqueo; no reabrir sin instrucción.

## Grok / otros harnesses

Si no hay `subscribe_github_*`, equivalente: webhook/notificación del forge, o un único `gh pr checks --watch` no bloqueante en background que avise al completar — nunca revisión manual periódica en el chat.

## Multi-repo

Un PR por repo; una suscripción CI + PR por cada uno. Informe final: tabla repo · PR · MERGED/blocked · SHA.

## Entregable

```markdown
## Merge-watch

| Repo       | PR  | Estado | SHA / bloqueo |
| ---------- | --- | ------ | ------------- |
| owner/repo | #N  | MERGED | abc1234       |
```

Actualiza el readiness: los `BLOCK` remediados pasan a `OK` o `WARN` justificado.
