#!/usr/bin/env bash
# Valida que el árbol canónico P0+P1 de ESTE repo existe.
# En repos de producto, o bien no copies este script, o bien cambia REQUIRED_FILES.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

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

echo "check-structure: validando canon P0+P1 en $root"

# P0
require_file "README.md"
require_file "LICENSE"
require_file "CHANGELOG.md"
require_file "SECURITY.md"
require_file "CONTRIBUTING.md"
require_file ".github/workflows/ci.yml"
require_file ".github/CODEOWNERS"

# P1 + piezas de este canon
require_file "AGENTS.md"
require_file "ARCHITECTURE.md"
require_file "CODE_OF_CONDUCT.md"
require_file "Makefile"
require_file ".env.example"
require_file "docs/README.md"
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
require_file "docs/guides/local-setup.md"
require_file "docs/guides/coding-standards.md"
require_file "docs/guides/testing.md"
require_file "docs/runbooks/deploy.md"
require_file "docs/runbooks/rollback.md"
require_file "docs/runbooks/rotate-secrets.md"
require_file "scripts/smoke.sh"
require_file "scripts/check-structure.sh"
require_file "stacks/typescript/README.md"
require_file "stacks/typescript/ci.quality.snippet.yml"
require_file "stacks/typescript/ci.smoke.snippet.yml"
require_file "stacks/rust/README.md"
require_file "stacks/rust/ci.quality.snippet.yml"
require_file "stacks/infra/README.md"
require_file "stacks/infra/ci.quality.snippet.yml"
require_file ".github/renovate.json"
require_file ".github/PULL_REQUEST_TEMPLATE.md"
require_file ".github/ISSUE_TEMPLATE/bug.yml"
require_file ".github/ISSUE_TEMPLATE/feature.yml"
require_file ".github/ISSUE_TEMPLATE/config.yml"
require_file ".github/workflows/security.yml"

require_dir "docs"
require_dir "docs/architecture"
require_dir "docs/architecture/decisions"
require_dir "docs/guides"
require_dir "docs/runbooks"
require_dir "stacks"
require_dir ".github/workflows"
require_dir ".github/ISSUE_TEMPLATE"

# Jobs canónicos en ci.yml (este canon no declara `build`: no hay artefacto)
ci=".github/workflows/ci.yml"
for job in quality test smoke; do
  if ! grep -Eq "^[[:space:]]*${job}:" "$ci"; then
    echo "FALTA job '${job}' en $ci"
    errors=$((errors + 1))
  fi
done

# Meta-sección contractual (excepto CHANGELOG: Keep a Changelog)
purpose_heading="### Propósito de este documento"
purpose_files=(
  "README.md"
  "AGENTS.md"
  "ARCHITECTURE.md"
  "SECURITY.md"
  "CONTRIBUTING.md"
  "CODE_OF_CONDUCT.md"
  "docs/README.md"
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
  "docs/guides/local-setup.md"
  "docs/guides/coding-standards.md"
  "docs/guides/testing.md"
  "docs/runbooks/deploy.md"
  "docs/runbooks/rollback.md"
  "docs/runbooks/rotate-secrets.md"
  "stacks/typescript/README.md"
  "stacks/rust/README.md"
  "stacks/infra/README.md"
  ".github/PULL_REQUEST_TEMPLATE.md"
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

if [[ ! -s ".github/renovate.json" ]]; then
  echo "FALTA o vacío: .github/renovate.json"
  errors=$((errors + 1))
fi

if [[ $missing -gt 0 || $errors -gt 0 ]]; then
  echo "check-structure: FALLO (archivos_faltantes=${missing} errores=${errors})"
  exit 1
fi

echo "check-structure: OK"
exit 0
