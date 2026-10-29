# Proton Mail 2024-26: Bridge 3.x, SDK y MCP

Novedades del ecosistema Proton 2024-26 relevantes para esta skill. El canon operativo vive en [protonsuite-tools @ v1.5.0](https://github.com/Soluciones-Alexendros/protonsuite-tools/tree/v1.5.0) (AGPL-3.0: solo enlazar); aquí solo criterio de decisión.

## Matriz de decisión: MCP → CLI → legacy

| Vía | Cuándo | Latencia / coste |
|---|---|---|
| **MCP tools** (`docs/mcp-tools/mail.md`) | Entorno con servidor MCP (defecto en agentes) | Baja; una llamada = una operación |
| **CLI protonsuite-tools** | Sin MCP, con Bridge corriendo | Media; subproceso por operación |
| **Legacy `scripts/proton_bridge.py`** | Sin MCP ni protonsuite-tools instalados | Media; solo IMAP/SMTP básico, sin features nuevas |

## Bridge 3.x

Bridge 3.x mantiene el contrato que usa esta skill (IMAP `127.0.0.1:1143` / SMTP `127.0.0.1:1025` con STARTTLS y contraseña generada por Bridge). Cambios a tener en cuenta:

- **Modo de direcciones**: combinado vs. separado (split) sigue existiendo; en split, `PROTON_USER` debe ser la dirección concreta (ver `references/setup.md`).
- **Certificado autofirmado local**: se mantiene `ssl.CERT_NONE` en cliente local; nunca exponer los puertos a red (túnel SSH si el agente corre remoto).
- **Cuentas gratuitas**: Bridge sigue requiriendo plan de pago; con plan Free, informar al usuario antes de seguir.

Si protonsuite-tools v1.5.0 documenta flags nuevos de Bridge 3.x, el canon del tag prevalece sobre `references/setup.md` (legacy).

## proton-python-sdk: evaluación

[proton-python-sdk](https://github.com/ProtonMail/proton-python-sdk) (componentes `proton-core`, clientes por producto) es la vía programática oficial frente al IMAP del Bridge:

| Criterio | proton-python-sdk | Bridge IMAP (esta skill) |
|---|---|---|
| Autenticación | Sesión SRP de cuenta Proton | Contraseña de Bridge ( IMAP/SMTP local) |
| Cobertura Mail | Envío/lectura según madurez del componente | Completa (IMAP+SMTP estándar) |
| Operativa agente | Requiere gestión de sesión y dependencias del SDK | Un proceso Bridge + credenciales env |
| Recomendación | Evaluar para integraciones sin Bridge (headless) | **Defecto**: simple, testeado, con script legacy funcional |

Regla: mientras el SDK no cubra el flujo del agente con menos piezas móviles que Bridge+IMAP, el Bridge sigue siendo la vía por defecto. Reevaluar cuando protonsuite-tools lo adopte en su canon.

## MCP tools de Mail (resumen)

Detalle completo en `docs/mcp-tools/mail.md` del tag pineado. Los 14 tools cubren: listar, buscar (remitente/asunto/texto/fecha/no-leídos), fetch con cabeceras, envío, marcado leído/no-leído y carpetas. El agente debe preferirlos al IMAP manual: devuelven estructurado y no requieren gestionar conexiones.
