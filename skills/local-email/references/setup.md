# Instalación y configuración de Proton Mail Bridge

> LEGACY: el canon vive en protonsuite-tools @ v1.5.0 (`docs/bridge-core/setup.md`). Este fichero se conserva como fallback local.

## Requisitos

- Cuenta Proton Mail de pago (Bridge no está disponible en el plan
  gratuito). Si el usuario tiene plan Free, decírselo antes de seguir.
- Proton Mail Bridge instalado en la máquina del usuario:
  https://proton.me/mail/bridge (Windows, macOS, Linux — .deb/.rpm).

## Puesta en marcha

1. Instalar Bridge e iniciar sesión con la cuenta Proton.
2. En la app Bridge: seleccionar la cuenta → **Mailbox details**
   (o «Detalles del buzón»). Ahí aparecen:
   - Servidor IMAP: `127.0.0.1`, puerto `1143` (STARTTLS)
   - Servidor SMTP: `127.0.0.1`, puerto `1025` (STARTTLS)
   - Usuario: la dirección de correo completa
   - **Contraseña generada por Bridge** (larga, aleatoria): es la que
     va en `PROTON_PASS`. NO es la contraseña de la cuenta Proton.
3. Mantener Bridge en ejecución (bandeja del sistema). Si se cierra,
   todo da `Connection refused`.

## Modo de direcciones

Si la cuenta tiene varias direcciones/alias, Bridge puede estar en modo
«combined» (una sola bandeja) o «split» (una por dirección). El script
funciona con ambos; en modo split hay que usar como `PROTON_USER` la
dirección concreta que se quiere revisar.

## Acceso remoto (opcional, solo si el agente corre fuera de la máquina)

Lo seguro es un túnel SSH desde la máquina donde corre el agente:

```bash
ssh -N -L 1143:127.0.0.1:1143 -L 1025:127.0.0.1:1025 usuario@maquina-del-usuario
```

y luego usar los valores por defecto (`127.0.0.1`). No abrir los puertos
del Bridge a la red directamente: la contraseña viajaría protegida por
STARTTLS pero el certificado es autofirmado y el servicio no está
pensado para exposición pública.

## Variables de entorno

```bash
export PROTON_USER="${PROTON_USER:-user@example.com}"  # ver .env.example
export PROTON_PASS="contraseña-generada-por-bridge"
# Opcionales (solo si cambian host/puertos):
# export PROTON_IMAP_HOST / PROTON_IMAP_PORT / PROTON_SMTP_HOST / PROTON_SMTP_PORT
```
