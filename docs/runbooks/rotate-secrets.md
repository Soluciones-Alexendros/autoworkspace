# Runbook — rotar secretos

### Propósito de este documento

- **Objetivos:** Qué hacer si se filtra un token y cómo rotar secretos de producto. Prevención (scanning org).
- **Estructura:** Esta meta-sección → filtración GitHub/Renovate/Actions → tabla de secretos de producto → pasos genéricos → Prevención.
- **Contenido a integrar según contexto:** Rellena la tabla con *nombres* de variables del producto (sin valores). Indica dónde viven (Environment, 1Password). No pongas tokens de ejemplo realistas. Secret scanning + push protection son P0 de org ([ADR-0005](../architecture/decisions/ADR-0005-secret-scanning-org.md)).

Este canon no guarda secretos reales. El archivo `.env.example` solo tiene placeholders.

## Si se filtra un token de GitHub / Renovate / Actions

1. Revoca el token en GitHub (Settings → Developer settings / org secrets / Environments).
2. Emite uno nuevo. Actualiza **solo** GitHub Secrets o el almacén (1Password, `pass`, Environment `production`).
3. No commitees el valor. No lo pongas en logs de Actions.
4. Revisa audit log: PRs y workflow runs posteriores a la filtración.
5. Abre un advisory privado si el secreto daba acceso a repos o prod.

## Producto (plantilla para copiar)

| Secreto | Dónde vive | Rotación |
|---------|------------|----------|
| `DATABASE_URL` | Environment `production` | nuevo rol/password en el proveedor → actualizar secret → redeploy |
| API keys de terceros | Environment + `.env` local | revocar en el panel del proveedor primero |
| `AUTH_SECRET` / JWT | Environment | rotar implica invalidar sesiones; avisa |

Pasos genéricos:

1. Genera el valor nuevo **fuera** del repo.
2. Actualiza el Environment (reviewer en `production`).
3. Despliega o reinicia el runtime.
4. Revoca el valor viejo cuando el nuevo esté en uso.
5. Confirma smoke (`/api/health` o equivalente) y que el valor viejo falla.

## Prevención

- Secret scanning + push protection ON (org / repo).
- `gitleaks` o equivalente en pre-commit (P1).
- `.env` en `.gitignore`; `.env.example` sin valores reales.
