# Verificación rigurosa inspirada en seL4

seL4 demostró que un sistema complejo puede garantizarse funcionalmente mediante una cadena **especificación → invariantes → prueba exhaustiva**. Aquí no se pide verificación formal completa, sino trasladar su disciplina a tests convencionales: toda funcionalidad crítica debe tener (1) invariantes explícitos, (2) propiedades verificadas sobre entradas generadas, no solo ejemplos elegidos a mano, y (3) evidencia de que los tests realmente cazan fallos (mutation testing), cuando la herramienta está disponible.

## Contenido

- [Método en 5 pasos](#metodo-en-5-pasos)
- [Pirámide y cobertura](#piramide-y-cobertura)
- [Property-based testing](#property-based-testing)
- [Fuzzing](#fuzzing)
- [Mutation testing](#mutation-testing)
- [Contratos e invariantes](#contratos-e-invariantes)
- [Herramientas por lenguaje](#herramientas-por-lenguaje)
- [Criterios de aceptación](#criterios-de-aceptacion)

## Método en 5 pasos

1. **Extraer la especificación implícita**: para cada módulo crítico, escribir en una frase qué debe cumplir (su contrato). Si nadie puede enunciarlo, eso ya es un hallazgo (P2: código sin especificación).
2. **Listar invariantes**: condiciones que siempre se cumplen (ej.: "el saldo nunca es negativo", "toda salida está escapada", "el parser nunca lanza excepción no controlada", "serialize∘parse = identidad"). Fuente: docstrings, tests existentes, sentido común del dominio.
3. **Convertir invariantes en propiedades ejecutables**: property-based tests que generen cientos/miles de casos, incluidos los extremos.
4. **Demostrar que los tests muerden**: mutation testing sobre los módulos críticos cuando la herramienta existe. Un mutante superviviente = un comportamiento no garantizado; un score bajo invalida la cobertura nominal. Objetivo ≥75 % mutantes eliminados; no bloquea la entrega si no se puede medir.
5. **Blindar los bordes**: fuzzing en todo punto donde entran datos externos (parsers, uploads, deserialización, APIs), con presupuesto de tiempo acotado.

## Pirámide y cobertura

- **Unitarios** (base): rápidos, aislados, uno por comportamiento. Nombres que describen el comportamiento esperado.
- **Integración** (media): contratos entre módulos, BD real en contenedor, APIs.
- **E2E** (cima): pocos, sobre flujos críticos de usuario (Playwright/Cypress en web).
- Cobertura orientativa: ≥80 % líneas en módulos críticos, 100 % en rutas de dinero/datos/seguridad. La cobertura es condición necesaria, nunca suficiente: medir también mutation score cuando sea posible.
- Tests deterministas: sin relojes ni aleatoriedad sin semilla fija, sin dependencia de red, sin orden implícito entre tests.

## Property-based testing

Patrón: en lugar de `f(3) == 5`, afirmar `∀x ∈ dominio: propiedad(f, x)`.

Propiedades canónicas reutilizables:

- **Round-trip**: `decode(encode(x)) == x` (serializadores, codecs, parsers).
- **Idempotencia**: `f(f(x)) == f(x)` (normalizadores, sanitizadores, migraciones).
- **Invariante de dominio**: predicados que se mantienen tras cualquier operación (saldos, tamaños, cotas).
- **Oráculo diferencial**: nueva implementación vs. antigua/referencia sobre el mismo input.
- **Metamórficas**: relación entre salidas de inputs relacionados (útil sin oráculo: `sum(x)+sum(y) == sum(x+y)`).
- **Never crashes**: ningún input generado produce excepción no controlada (mínimo absoluto en parsers).

Ejemplo (hypothesis):

```python
from collections import Counter
from hypothesis import given, strategies as st


@given(st.lists(st.integers()))
def test_ordenar_es_idempotente_y_conserva_multiconjunto(xs):
    ordenado = sorted(xs)
    assert sorted(ordenado) == ordenado
    assert Counter(ordenado) == Counter(xs)
```

## Fuzzing

- Dirigido por cobertura cuando sea posible: libFuzzer/AFL++ (C/C++), `go test -fuzz` (Go), cargo-fuzz (Rust), Jazzer (Java), Atheris (Python).
- Sembrar con corpus de entradas reales + casos límite conocidos; ejecutar en CI con presupuesto de tiempo.
- Todo crash encontrado se convierte en test de regresión permanente.

## Mutation testing

Herramientas: Stryker (JS/TS/.NET), mutmut/cosmic-ray (Python), pitest (Java), cargo-mutants (Rust), infection (PHP), go-mutesting (Go).

- Aplicar solo a módulos críticos (coste alto). Score objetivo: ≥75 % mutantes eliminados.
- Cada mutante superviviente se analiza: ¿comportamiento irrelevante (equivalente) o hueco real de tests? Lo segundo genera un test nuevo.
- Si la herramienta no está instalada o el presupuesto de tiempo no alcanza: anotar "No ejecutado" en el informe y continuar.

## Contratos e invariantes

- Aserciones en código para invariantes internos (`assert`/pre-postcondiciones), activas en desarrollo y tests.
- Tipos que hacen ilegibles los estados inválidos: TypeScript estricto, newtypes en Rust, tipos con nombre (type aliases + validación) en Go, value objects. La verificación más barata es la que el compilador hace gratis.
- En APIs: tests de contrato contra el schema (OpenAPI/JSON Schema); en BD: tests de migración arriba/abajo.

## Herramientas por lenguaje

| Lenguaje | Runner | Property-based | Fuzzing | Mutation | Cobertura |
|---|---|---|---|---|---|
| Python | pytest | hypothesis | Atheris | mutmut, cosmic-ray | coverage.py |
| JS/TS | vitest/jest | fast-check | jsfuzz | stryker | c8/istanbul |
| Go | go test | testing/quick, gopter | go test -fuzz | go-mutesting | go test -cover |
| Rust | cargo test | proptest | cargo-fuzz | cargo-mutants | tarpaulin/llvm-cov |
| Java | JUnit 5 | jqwik | Jazzer | pitest | JaCoCo |
| C# | xUnit | FsCheck | SharpFuzz | Stryker.NET | coverlet |
| Ruby | RSpec | rantly | — | mutant | simplecov |
| PHP | PHPUnit | eris | — | infection | phpunit --coverage |

## Criterios de aceptación

### Nivel obligatorio (siempre)

1. Build y suite completa en verde en CI (o localmente si no hay CI).
2. Todo fallo corregido en la auditoría tiene un test de regresión que falla sin la corrección (red → green demostrado).
3. Se reportan: cobertura por módulo (si se midió) y la lista honesta de lo que NO queda garantizado.

### Nivel riguroso (módulos críticos, si la herramienta existe)

4. Los módulos críticos tienen invariantes documentados y property-based tests que los ejercitan.
5. Los puntos de entrada de datos externos tienen al menos el test "never crashes" con generación.
6. Mutation score de módulos críticos medido (objetivo ≥75 %) o marcado "No ejecutado" con motivo.

La entrega del informe **no** se bloquea si falta el nivel riguroso: se documenta lo no ejecutado.
