# Diagramas de arquitectura

Los diagramas de este directorio se generan con [Archify](https://github.com/tt-a1i/archify)
(Apache-2.0), fijado por SHA en [`catalog.json`](./catalog.json).

## Qué se versiona y qué no

| Ruta                      | Se versiona | Por qué                                                           |
| ------------------------- | ----------- | ----------------------------------------------------------------- |
| `catalog.json`            | Sí          | Declara el renderer y la lista cerrada de diagramas               |
| `sources/D0n.<tipo>.json` | Sí          | Es la fuente de verdad; se revisa como cualquier otro texto       |
| `rendered/D0n.html`       | No          | Es un artefacto de CI: se regenera y se sube como adjunto del run |
| `.cache/`                 | No          | Clon temporal del renderer                                        |

Versionar el HTML produce diffs gigantes e ilegibles en cada regeneración
—la lección del PR #188 de archmaker— y acopla la revisión a la salida del
renderer en vez de a la fuente. El job `diagrams` de `ci.yml` publica
`rendered/` como artefacto con 14 días de retención.

## Regenerar en local

```bash
make diagrams
```

El objetivo clona `tt-a1i/archify` en `.cache/archify` al SHA del catálogo (si
no está o no coincide), ejecuta `validate` y `deliver` por cada entrada y
falla si una fuente no está en el catálogo o una entrada no tiene fichero.
`ARCHIFY_DIR` permite reutilizar un clon ya existente.

## Editar un diagrama

Se edita la fuente JSON, nunca el HTML. Cada tipo tiene su esquema en el SHA
fijado (`<clon>/archify/schemas/`) y `validate` es la puerta: un cambio que no
valida no entra.

Las fuentes se escriben a mano. Opcionalmente, y siempre fuera del repo, puede
instalarse la skill de Archify (`npx skills add tt-a1i/archify`) para que un
agente las edite; el repositorio no depende de esa instalación.

## Catálogo

| Id  | Tipo           | Título                  | ADR      |
| --- | -------------- | ----------------------- | -------- |
| D01 | `architecture` | Capas de autoworkspace  | ADR-0016 |
| D02 | `workflow`     | Flujo en dos fases      | ADR-0013 |
| D03 | `sequence`     | Agregación de `ci-gate` | ADR-0013 |
| D04 | `lifecycle`    | Ciclo de vida de un ADR | ADR-0002 |

## Actualizar el pin

Renovate abre el PR por el `customManager` de `.github/renovate.json`, que lee
el SHA de `catalog.json` y el `ref` del job `diagrams` de `ci.yml` con
`datasource: git-refs`. La regla lleva `automerge: false` y la etiqueta `hold`:
subir el renderer cambia el HTML de los cuatro diagramas y se revisa a mano.

El test `tools/validate/tests/test_diagram_pin.py` comprueba que el `ref` del
job y el SHA del catálogo son el mismo.
