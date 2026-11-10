# Postura defensiva — inventario y lectura de estado

Qué comprobar, con qué comando y cómo interpretarlo. Todo R0 (solo lectura).

## 1. Control de acceso mandatorio (AppArmor)

```bash
cat /sys/module/apparmor/parameters/enabled            # Y
sysctl kernel.apparmor_restrict_unprivileged_userns    # 1 = endurecido; 0 = puerta abierta (revisar por qué)
systemctl is-active apparmor
aa-status                                              # conteos enforce/complain/unconfined
aa-unconfined --paranoid                               # procesos sin confinar (el riesgo real)
```

Lectura: perfiles en complain de fábrica (`force-complain/`) no son hallazgo; complain inesperados sí. `aa-unconfined` lista intérpretes (node, python3) por diseño — se confinan servicios, no intérpretes.

## 2. Auditoría y detección

```bash
systemctl is-active auditd
auditctl -l                                            # reglas cargadas (vigilancias -w, claves -k)
grep -c . /var/log/audit/audit.log 2>/dev/null
ausearch -m avc -ts today | grep -c 'apparmor="DENIED"'
systemctl list-timers --all | grep -iE 'aide|clam'     # integridad/AV programados
systemctl --user is-active apparmor-notify             # canal de alertas de escritorio
ls -la /var/log/apparmor/denials.log 2>/dev/null       # recolector de denegaciones
```

Nota: con auditd activo, AppArmor habla por audit.log, no por journal.

## 3. Superficie de ataque

```bash
ufw status verbose
ss -tulpn | head -30                                   # qué escucha y quién lo abre
systemctl --failed
find / -xdev -perm -4000 -type f 2>/dev/null           # setuid: comparar contra baseline conocido
grep -E '^[^:]*:[^:]*:[0-9]{1,2}:' /etc/passwd         # cuentas con UID < 100 inesperadas
```

## 4. SSH

```bash
sshd -T | grep -iE 'permitrootlogin|passwordauthentication|pubkey|port|allowusers|maxauth'
```
Baseline sano: rootlogin no, MaxAuthTries ≤ 4, sin password si hay claves. En esta máquina hay excepción documentada: SSH en 0.0.0.0:22 en WiFi doméstica — no "corregir" ListenAddress.

## 5. Integridad de binarios y canon

- `~/Aplicaciones/Terminal` (canon CLI): su **raíz + binarios + `Scripts/`** deben ser `root:root`, 0755, `chattr +i` (`lsattr -d`), regla auditd `terminal_canon` (`auditctl -l | grep terminal_canon`) y presentes en AIDE (`zgrep -c Terminal /var/lib/aide/aide.db`).
- **Excluidos de la vigilancia** (estado mutable del usuario): `~/Aplicaciones/Terminal/Shell` y `~/Aplicaciones/Terminal/Agentes` — deben ser del usuario y **sin** `chattr +i`.
- Cualquier binario de usuario editable por procesos sin confinar que toque secretos (gh, sops, gestores de claves) es un hallazgo P2: vía de troyanización.
- Canon del home y notación de referencia: `../../disenar-constitucion/references/DirectoriosEsenciales.md` (`·Aplicaciones` = raíz de aplicaciones, estrato 1; `··Terminal` = canon CLI, estrato 2; `·Audiovisual` = medios).

## 6. Parches de seguridad

```bash
apt list --upgradable 2>/dev/null | grep -ci secur
snap refresh --list
```
