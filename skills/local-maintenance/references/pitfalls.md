# Pitfalls y falsos positivos conocidos — audit_full.py

Leer SIEMPRE antes de remediar un hallazgo. Verificar el estado real a mano primero.

## Falsos positivos corregidos (2026-09-23)

| Check | Bug | Fix aplicado |
|-------|-----|--------------|
| FS-05/FS-06 | La caché de bun vive ahora en `$XDG_DATA_HOME/bun/` (o el redirect XDG del host); la exclusión `*/.bun/*` ya no la cubre → cientos de archivos 0666 del install-cache | Añadida exclusión `*/share/bun/*` |
| FS-05/FS-06/FS-07 | Las capas de imágenes de contenedores (podman/docker) en `share/containers/storage/overlay/*/diff/` contienen paths world-writable y UID sin mapear (`/home/runner`, `/opt/hostedtoolcache` de imágenes de CI). Son contenido de imagen, no riesgo del host; también infla la papelera histórica (`$XDG_DATA_HOME/…/papelera-xdg/…`) que los contiene | Añadida exclusión `*/share/containers/storage/*` |
| FS-05 | La config de Proton Mail/Pass vive ahora en `$XDG_CONFIG_HOME/Proton*/` (o el redirect XDG del host); la exclusión `*/.config/Proton Mail/*` ya no la cubre (mismo comportamiento 0666 documentado en 2026-08-10) | Añadidas exclusiones `*/config/Proton Mail/*` y `*/config/Proton Pass/*` |
| FS-05 | Los `.lock` de uv (gestor de paquetes Python) se crean 0666 por diseño (`share/uv/*`, `cache/uv/*`, y `venv*/.lock` en cada proyecto). Misma clase que la caché de bun | Añadidas exclusiones `*/share/uv/*`, `*/cache/uv/*` y `*/venv*/.lock` |
| FS-05/FS-06/FS-07 | La papelera histórica de XDG (`$XDG_DATA_HOME/…/papelera-xdg/` (papelera histórica local)) es una copia congelada (dirs renombrados `config-puerta`, `cache-puerta`…) que replica todo el ruido anterior hasta que se elimine. **Pendiente: purga de la papelera (decisión del usuario)** | Añadida exclusión `*/papelera-xdg/*` |

## Falsos positivos corregidos (2026-08-10)

| Check | Bug | Fix aplicado |
|-------|-----|--------------|
| CR-01 | El regex esperaba `RSA-SHA2-*`, pero `ssh-keygen -lf` de OpenSSH imprime `(RSA)` → todo RSA marcado como débil | Regex ampliado a `ED25519\|\(RSA\)` |
| SSH-03/04/05/06 | `sshd -T` requiere root y, bajo sudo, ruta absoluta (re-exec) → salida vacía → WARN falsos | Helper `sshd_effective` (exportado con `export -f` para que sobreviva al `bash -c` de `run_check`); fallback a parsear `sshd_config` + `sshd_config.d/*.conf` |
| FW-02 | `grep 'Default:'` sobre `ufw status verbose`, pero con locale español la salida es `Predeterminado:` → FAIL falso. Ojo: `LC_ALL=C` a través de sudo **no es fiable** (depende de `env_keep`) | Grep bilingüe `Default:\|Predeterminado:` y `deny.*(incoming\|entrantes)` |
| FS-05/FS-06 | Cientos de archivos world-writable en `node_modules/.bun` y `~/.bun/install/cache` (bun instala 0666) → ruido, no riesgo | Excluidos `*/node_modules/*` y `*/.bun/*` |
| FS-05 | Proton Mail reescribe `~/.config/Proton Mail/*.json` a 0666 cada vez que arranca → FAIL recurrente tras cada reinicio | Excluido `*/.config/Proton Mail/*` (equipo monousuario; riesgo aceptado y documentado) |
| AU-01 | `auditctl -l` sin root devuelve vacío → "auditd sin reglas" falso | `sudo -n auditctl -l` (auditctl está en NOPASSWD) |

## Trampas al editar los scripts

- `run_check` ejecuta `timeout N bash -c "$cmd"`: las funciones **no** se heredan salvo `export -f`.
- `bash -n` no detecta comandos inexistentes dentro de strings; probar cada check aislado tras editarlo.
- Al usar `sed` con anclas tipo `^}$` se pueden insertar líneas duplicadas tras cada función; revisar con `grep -c`.

## Hallazgos reales recurrentes (aceptados, no perseguir)

- **NET-04 / NET-05** — SSH y servicios en 0.0.0.0: excepción documentada (LAN local con DHCP; política local de mantenimiento prohíbe restringir ListenAddress).
- **FS-09** — `/usr/share/doc/copyq-doc/CHANGES.md.gz` → `changelog.gz` inexistente: bug de empaquetado upstream de `copyq-doc`. No borrar (pertenece a dpkg).
- **FW-03** — ~150 "puertos abiertos": el check cuenta sockets UDP/ICMP sin estado y dockers; inflado.
- **FS-08** — 30 SUID/SGID: binarios estándar del sistema.
- **PKG-06** — paquetes "manuales": informativo.
- **LOG-06 / LOG-08** — errores de journal dominados por crashes del firmware WiFi RTL8852CE (mitigados vía modprobe.d; tras el reinicio del 2026-08-10: 12 errores/boot) y fallos puntuales de auth sudo. Revisar composición antes de actuar: `journalctl -p err -b | awk '{print $5}' | sort | uniq -c | sort -rn | head`.
- **SRV-01** — cups, avahi-daemon, bluetooth: en uso por el usuario.
- **Proton Mail** (`~/.config/Proton Mail/*.json`) — la app reescribe sus configs 0666 al arrancar; excluida de FS-05/FS-06 (riesgo aceptado, equipo monousuario).

## KR-27: fs.suid_dumpable vuelve a 2 tras reinicio (RESUELTO 2026-08-10)

`apport.service` escribe `fs.suid_dumpable=2` al arrancar (`/usr/share/apport/apport:691`), después de `sysctl --system`. Si KR-27 vuelve a fallar tras un reinicio, comprobar primero `systemctl is-enabled apport`. Resuelto deshabilitando apport (`systemctl disable --now apport`); revertir con `enable --now`.

## Procedimiento ante un FAIL nuevo

1. Reproducir el comando del check a mano y mirar la salida cruda.
2. Si el estado real es correcto → es bug del check: corregir en `audit_full.py` y anotar aquí.
3. Si el estado real es incorrecto → fix real + re-auditoría + CHANGELOG.
