# Política de seguridad

## Reportar vulnerabilidades

Si descubres una vulnerabilidad, **no abras un issue público**.

1. Usa [GitHub Security Advisories](https://github.com/Iniciativas-Alexendros/repo-standard/security/advisories/new) (privado), o
2. Escribe a **operaciones@alexendros.dev** con descripción, impacto, reproducción y commit/versión.

## Ventanas de respuesta

| Paso | Objetivo |
|------|----------|
| Acuse de recibo | ≤ 48 horas laborables (Europe/Madrid) |
| Evaluación inicial | ≤ 5 días laborables |
| Coordinación de parche / disclosure | Según severidad; no publicar detalles explotables hasta que exista mitigación |

## Versiones soportadas

Este repositorio es el **canon de plataforma** (documentación, esqueleto CI y convenciones), no un runtime de producto.

| Canal | Soporte |
|-------|---------|
| Rama `main` | Sí — contrato vigente |
| Tags SemVer | Sí, mientras no estén deprecados en el CHANGELOG |
| Forks / copias locales desactualizadas | No — alinea con `main` |

En repos de producto que hereden este estándar, documenta aquí las versiones de aplicación que sí reciben parches.

## Alcance de este canon

- Contratos de docs, CI (`quality` → `test` → `build` → `smoke`), Renovate y protección de `main`.
- No cubre secretos reales, credenciales ni infraestructura de producción.

Si el hallazgo afecta a un producto de la flota (SaaS, web, CLI, infra), reporta en **ese** repositorio o al mismo canal si no tienes claro el destino.
