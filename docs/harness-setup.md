# Harness setup — Cursor and Pi

`skills/` is the only catalog that is committed. Installers create symlinks; they do not copy skill bodies.

## Cursor

| Destination              | Command                                                    |
| ------------------------ | ---------------------------------------------------------- |
| Project `.cursor/skills` | `bash scripts/install-cursor.sh --target .cursor/skills`   |
| User `~/.cursor/skills`  | `bash scripts/install-cursor.sh --user`                    |
| Any directory            | `bash scripts/install-cursor.sh --target /tmp/test-cursor` |

## Pi

Pi loads project skills from `.pi/skills/` and user skills from `~/.pi/agent/skills/` ([documentation](https://pi.dev/docs/latest/skills)).

| Destination               | Command                                            |
| ------------------------- | -------------------------------------------------- |
| Project `.pi/skills`      | `bash scripts/install-pi.sh --target .pi/skills`   |
| User `~/.pi/agent/skills` | `bash scripts/install-pi.sh --user`                |
| Any directory             | `bash scripts/install-pi.sh --target /tmp/test-pi` |

`--target` never writes `$HOME`. `--dry-run` performs no filesystem writes. `--uninstall` removes only symlinks recorded in the manifest and still owned by this checkout.
