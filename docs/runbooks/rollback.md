# Runbook — rollback

## Canon (este repo)

El «rollback» es revertir el contrato:

1. Identifica el merge o tag que rompió a los consumidores (CHANGELOG + SHA).
2. `git revert` del squash (o PR que restaure el árbol anterior). No force-push a `main`.
3. CI verde en el revert. Comunica en el PR qué repos de la flota deben pausar la alineación.
4. Si un ADR Accepted quedó mal: ábrelo como Superseded y escribe el que lo corrige.

## Producto (plantilla)

1. **Hosting inmutable (Vercel / contenedor):** redespliega el deployment/tag anterior. No «arreglar» en caliente en prod.
2. **Migraciones de datos:** no hagas rollback de schema a ciegas; usa el runbook de migraciones del producto.
3. **DNS / dominio:** revertir el registro (snapshot de zona si Hostinger/DNS). Confirma TTL.
4. **Feature flags:** apaga el flag antes de revertir código si el flag evita downtime.
5. Tras estabilizar: issue post-mortem breve + test que reproduzca el fallo.

## Contacto

Incidentes de seguridad: [SECURITY.md](../../SECURITY.md), no un issue público.
