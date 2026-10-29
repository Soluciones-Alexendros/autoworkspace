# Proton Pass — notas de seguridad

> LEGACY: el canon vive en protonsuite-tools @ v1.5.0 (`docs/bridge-core/security-notes.md`). Este fichero se conserva como referencia local.

Consideraciones de seguridad al operar con `pass-cli` y secretos en el agente.

## Manejo de sesión

- La sesión se almacena en `~/.local/share/proton-pass-cli/.session/` _(ruta local)_.
  No copiar, commitear ni compartir ese directorio.
- `pass-cli login` es idempotente y usa flujo web: nunca pedidas contraseñas por stdin.
- Ante sospecha de compromiso de la sesión → `pass-cli login` para rotar la credencial.
- Verificar sesión activa antes de cada operación: si falta, `pass-cli login` en lugar de
  sustituir por secretos hardcodeados o pedidos en texto plano.

## Inyección de variables de entorno

- Para que un consumidor (script CI, helper) acceda al secreto sin verlo en salida,
  exportarlo únicamente en el proceso destino _(ejemplo)_:
  `PASS=$(pass-cli show Personal/app.com --field password) ./deploy.sh`
- No escribir el secreto en `.env` commiteado, logs ni artefactos de build.
- Restringir permisos de cualquier fichero temporal que contenga el secreto (`chmod 600`)
  y borrarlo tras su uso.
- En CI, usar secretos del orquestador (GitHub Secrets, GitLab CI variables) inyectados en
  el entorno del job, nunca en texto plano en el YAML.

## Limpieza de portapapeles

- Si un secreto pasa por portapapeles (p. ej. `pass-cli show ... | xclip`), programar el
  borrado tras un tiempo acortado _(ejemplo: 45 s)_ para minimizar exposición.
- En headless/servidor no hay portapapeles: preferir inyección directa por variable de
  entorno y evitar cualquier paso por `xclip`/`wl-copy`/`pbcopy`.
- Nunca registrar el valor del secreto en transcripciones, issues ni informes.

## Reglas generales

1. El secreto viaja del agente al consumidor en memoria/variable de entorno, nunca en disco.
2. Ante duda entre pedir el secreto o hardcodear: pedir el secreto vía `pass-cli`.
3. Si un comando falla, reintentar el flujo de sesión; no degradar a alternativas inseguras.
