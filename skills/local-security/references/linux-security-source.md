---
name: linux-security
description: "Verifica endurecimiento del host Linux: MAC activo (SELinux/AppArmor), hardening sysctl, SSH endurecido (sin root login ni password auth), auditd, fail2ban. Read-only, nunca aplica cambios. Dispara con: auditar seguridad, hardening del host, bastionado, revisar postura de seguridad, CIS benchmark."
license: MIT
compatibility: cursor, pi
metadata:
  author: alexendros
  version: "1.0.0"
  source: convertido desde XEK_linux-seguridad v0.7.0
allowed-tools: Bash(sysctl:*) Bash(systemctl:*) Bash(grep:*) Bash(sshd:*) Read
---

> Nota de absorción: fuente `linux-security` fusionada aquí. El ejecutable citado abajo (`scripts/linux-security.sh`) no existe en esta skill — el fingerprint activo es `scripts/postura_seguridad.sh` (ver SKILL.md «Herramientas»). (Deduplicado 2026-09-26: 5 bloques x30 líneas fusionados en una copia canónica; se conservó un bloque completo con tabla `## Uso` íntegra.)

# linux-security

## Objetivo

Verificar el endurecimiento del host Linux: control de acceso obligatorio
(SELinux/AppArmor) activo, parámetros `sysctl` de hardening, `sshd` endurecido
(sin root login ni autenticación por contraseña), `auditd` y `fail2ban`. Emite
informe sin aplicar cambios (read-only).

## Cuándo activar

| Si... | Entonces... |
|-------|-------------|
| Bastionado de un nuevo host | Ejecutar todos los checks y comparar contra CIS |
| Tras actualización del sistema | Confirmar que el hardening sobrevive |
| Auditoría de cumplimiento | Revisar MAC, sysctl, SSH, auditd, fail2ban |

## Uso

| `sshd -T` / `auditctl -s` requieren sudo | Checks privilegiados se marcan como `skipped` sin `--sudo` |
| MAC en modo permisivo no es hardening real | Check hard-002 exige `enforcing` o `--enabled` |
| `sshd_config.d/` puede sobrescribir config | Check hard-004 lee también el directorio drop-in |
| fail2ban innecesario en host sin SSH expuesto | Severidad medium; propuesta contextualiza por exposición |

## Implementación

La fuente ejecutable es `scripts/linux-security.sh`. Emite findings en JSON con
`id`, `severity`, `message` y `remediation`. Los checks que requieren privilegios
se saltan automáticamente si no se pasa `--sudo`.
