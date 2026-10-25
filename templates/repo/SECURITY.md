# Política de seguridad

### Propósito de este documento

- **Objetivos:** Canal privado de vulnerabilidades, ventanas de respuesta y versiones soportadas. En producto, las mismas secciones con _tus_ versiones y contacto.
- **Estructura:** Esta meta-sección → Reportar → Ventanas → Versiones soportadas → Alcance.
- **Contenido a integrar según contexto:** Cambia la URL de advisories y el correo si el producto tiene canal propio. Rellena la tabla de versiones de _aplicación_. No publiques exploits ni secretos. No desactives Dependabot Alerts ni secret scanning ([ADR-0004](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0004-renovate-org-y-dependabot.md), [ADR-0005](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0005-secret-scanning-org.md)).

## Reportar vulnerabilidades

Si descubres una vulnerabilidad, **no abras un issue público**.

1. Usa [GitHub Security Advisories](https://github.com/Soluciones-Alexendros/<tu-repo>/security/advisories/new) (privado; sustituye `<tu-repo>`), o
2. Escribe a **operaciones@alexendros.dev** con descripción, impacto, reproducción y commit/versión.

## Ventanas de respuesta

| Paso                                | Objetivo                                                                      |
| ----------------------------------- | ----------------------------------------------------------------------------- |
| Acuse de recibo                     | ≤ 48 horas laborables (Europe/Madrid)                                         |
| Evaluación inicial                  | ≤ 5 días laborables                                                           |
| Coordinación de parche / disclosure | Según severidad; no publicar detalles explotables hasta que exista mitigación |

## Versiones soportadas

Este repositorio es el **canon de plataforma** (documentación, esqueleto CI y convenciones), no un runtime de producto.

| Canal                                  | Soporte                                          |
| -------------------------------------- | ------------------------------------------------ |
| Rama `main`                            | Sí — contrato vigente                            |
| Tags SemVer                            | Sí, mientras no estén deprecados en el CHANGELOG |
| Forks / copias locales desactualizadas | No — alinea con `main`                           |

En repos de producto que hereden este estándar, documenta aquí las versiones de aplicación que sí reciben parches.

## Alcance de este canon

- Contratos de docs, CI (`quality` → `test` → `build` → `smoke`), Renovate y protección de `main`.
- Prerrequisitos org de flota: App Renovate; secret scanning + push protection ON ([ADR-0005](https://github.com/Soluciones-Alexendros/autoworkspace/blob/main/docs/architecture/decisions/ADR-0005-secret-scanning-org.md)).
- No cubre secretos reales, credenciales ni infraestructura de producción.

Si el hallazgo afecta a un producto de la flota (SaaS, web, CLI, infra), reporta en **ese** repositorio o al mismo canal si no tienes claro el destino.
