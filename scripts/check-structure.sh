#!/usr/bin/env bash
# Valida el esqueleto P0+P1 en templates/repo/ (parámetro de raíz) y el
# árbol del canon (ADRs, stacks, reusables) en la raíz del host.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

template_root="${1:-templates/repo}"
if [[ ! -d "$template_root" ]]; then
  echo "FALTA directorio de plantilla: $template_root"
  exit 1
fi

missing=0
errors=0

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "FALTA archivo: $path"
    missing=$((missing + 1))
  fi
}

require_dir() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "FALTA directorio: $path"
    missing=$((missing + 1))
  fi
}

echo "check-structure: validando plantilla P0+P1 en $template_root"
echo "check-structure: validando canon en $repo_root"

# --- Plantilla de producto (templates/repo) ---
require_file "$template_root/README.md"
require_file "$template_root/LICENSE"
require_file "$template_root/CHANGELOG.md"
require_file "$template_root/SECURITY.md"
require_file "$template_root/CONTRIBUTING.md"
require_file "$template_root/.github/CODEOWNERS"
require_file "$template_root/AGENTS.md"
require_file "$template_root/ARCHITECTURE.md"
require_file "$template_root/CODE_OF_CONDUCT.md"
require_file "$template_root/Makefile"
require_file "$template_root/.env.example"
require_file "$template_root/docs/README.md"
require_file "$template_root/.github/renovate.json"
require_file "$template_root/.github/PULL_REQUEST_TEMPLATE.md"
require_file "$template_root/.github/ISSUE_TEMPLATE/bug.yml"
require_file "$template_root/.github/ISSUE_TEMPLATE/feature.yml"
require_file "$template_root/.github/ISSUE_TEMPLATE/config.yml"
require_dir "$template_root/.github/ISSUE_TEMPLATE"

# --- Canon en la raíz del host ---
require_file ".github/workflows/ci.yml"
require_file "docs/REUTILIZACION.md"
require_file "docs/architecture/overview.md"
require_file "docs/architecture/decisions/README.md"
require_file "docs/architecture/decisions/template.md"
require_file "docs/architecture/decisions/ADR-0001-canon-repo-standard.md"
require_file "docs/architecture/decisions/ADR-0002-proteccion-metadatos-como-codigo.md"
require_file "docs/architecture/decisions/ADR-0003-job-build-y-required-checks.md"
require_file "docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md"
require_file "docs/architecture/decisions/ADR-0005-secret-scanning-org.md"
require_file "docs/architecture/decisions/ADR-0006-reviews-por-perfil.md"
require_file "docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md"
require_file "docs/architecture/decisions/ADR-0008-snippets-reales-post-oleada.md"
require_file "docs/architecture/decisions/ADR-0009-scorecard-cumplimiento-p0.md"
require_file "docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md"
require_file "docs/architecture/decisions/ADR-0011-bootstrap-desde-plantilla.md"
require_file "docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md"
require_file "docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md"
require_file "docs/architecture/decisions/ADR-0014-release-please-y-packaging-por-stack.md"
require_file "docs/guides/local-setup.md"
require_file "docs/guides/coding-standards.md"
require_file "docs/guides/testing.md"
require_file "docs/runbooks/deploy.md"
require_file "docs/runbooks/rollback.md"
require_file "docs/runbooks/rotate-secrets.md"
require_file "scripts/smoke.sh"
require_file "scripts/check-structure.sh"
require_file "stacks/typescript/README.md"
require_file "stacks/typescript/ci.yml"
require_file "stacks/rust/README.md"
require_file "stacks/rust/ci.yml"
require_file "stacks/infra/README.md"
require_file "stacks/infra/ci.yml"
require_file "stacks/python/README.md"
require_file "stacks/python/ci.yml"
require_file ".github/workflows/security.yml"
require_file ".github/workflows/reusable-node.yml"
require_file ".github/workflows/reusable-rust.yml"
require_file ".github/workflows/reusable-python.yml"
require_file ".github/workflows/reusable-static.yml"

require_dir "docs"
require_dir "docs/architecture"
require_dir "docs/architecture/decisions"
require_dir "docs/guides"
require_dir "docs/runbooks"
require_dir "stacks"
require_dir ".github/workflows"

# Caller canónico (P11): pipeline-python (+ pipeline-node si hay JS), canon, ci-gate
ci=".github/workflows/ci.yml"
for job in pipeline-python canon ci-gate; do
  if ! grep -Eq "^[[:space:]]*${job}:" "$ci"; then
    echo "FALTA job '${job}' en $ci"
    errors=$((errors + 1))
  fi
done
if ! grep -Eq "name:[[:space:]]*ci-gate" "$ci"; then
  echo "FALTA name: ci-gate en $ci (el check required debe llamarse exactamente ci-gate)"
  errors=$((errors + 1))
fi

# Meta-sección contractual (excepto CHANGELOG: Keep a Changelog)
purpose_heading="### Propósito de este documento"
purpose_files=(
  "$template_root/README.md"
  "$template_root/AGENTS.md"
  "$template_root/ARCHITECTURE.md"
  "$template_root/SECURITY.md"
  "$template_root/CONTRIBUTING.md"
  "$template_root/CODE_OF_CONDUCT.md"
  "$template_root/docs/README.md"
  "docs/REUTILIZACION.md"
  "docs/architecture/overview.md"
  "docs/architecture/decisions/README.md"
  "docs/architecture/decisions/template.md"
  "docs/architecture/decisions/ADR-0001-canon-repo-standard.md"
  "docs/architecture/decisions/ADR-0002-proteccion-metadatos-como-codigo.md"
  "docs/architecture/decisions/ADR-0003-job-build-y-required-checks.md"
  "docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md"
  "docs/architecture/decisions/ADR-0005-secret-scanning-org.md"
  "docs/architecture/decisions/ADR-0006-reviews-por-perfil.md"
  "docs/architecture/decisions/ADR-0007-coverage-gate-opcional.md"
  "docs/architecture/decisions/ADR-0008-snippets-reales-post-oleada.md"
  "docs/architecture/decisions/ADR-0009-scorecard-cumplimiento-p0.md"
  "docs/architecture/decisions/ADR-0010-semver-contrato-estandar.md"
  "docs/architecture/decisions/ADR-0011-bootstrap-desde-plantilla.md"
  "docs/architecture/decisions/ADR-0012-solo-dev-automerge-sin-revision.md"
  "docs/architecture/decisions/ADR-0013-check-unico-ci-gate.md"
  "docs/architecture/decisions/ADR-0014-release-please-y-packaging-por-stack.md"
  "docs/guides/local-setup.md"
  "docs/guides/coding-standards.md"
  "docs/guides/testing.md"
  "docs/runbooks/deploy.md"
  "docs/runbooks/rollback.md"
  "docs/runbooks/rotate-secrets.md"
  "stacks/typescript/README.md"
  "stacks/rust/README.md"
  "stacks/infra/README.md"
  "stacks/python/README.md"
  "$template_root/.github/PULL_REQUEST_TEMPLATE.md"
)
for path in "${purpose_files[@]}"; do
  if [[ -f "$path" ]] && ! grep -Fq "$purpose_heading" "$path"; then
    echo "FALTA meta-sección '${purpose_heading}' en $path"
    errors=$((errors + 1))
  fi
done

# Renovate único: no version-updates de Dependabot
if [[ -f ".github/dependabot.yml" ]] || [[ -f "dependabot.yml" ]]; then
  echo "PROHIBIDO: dependabot.yml de version-updates. El bot de la flota es Renovate."
  errors=$((errors + 1))
fi

if [[ ! -s "$template_root/.github/renovate.json" ]]; then
  echo "FALTA o vacío: $template_root/.github/renovate.json"
  errors=$((errors + 1))
fi

if [[ $missing -gt 0 || $errors -gt 0 ]]; then
  echo "check-structure: FALLO (archivos_faltantes=${missing} errores=${errors})"
  exit 1
fi

echo "check-structure: OK"
exit 0
