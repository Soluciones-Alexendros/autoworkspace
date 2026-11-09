# Upgrade and migration

- Prefer immutable tags (`vX.Y.Z`); pinned refs do not move on `pi update`
- Bootstrap: checksum + attestation before extract (`scripts/bootstrap.sh`)
- Doctor after install; failure triggers owned-resource rollback or explicit FAIL
- Schema/registry changes require coherent version bumps (ADR-0010)
- Rollback: reinstall previous tag; do not leave partial PASS states
- Foreign skills/resources outside owned manifests must be preserved on uninstall
