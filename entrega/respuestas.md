# Respuestas conceptuales

## 1. ¿Por qué usar `_loaded_at` y no `fecha_venta` para este control?

Porque lo que quería saber era si la carga se retrasó, y eso solo lo dice `_loaded_at`. `fecha_venta` es la fecha del negocio, es decir, cuándo ocurrió la venta, mientras que `_loaded_at` es el instante en que la fila llegó a `raw`. Son cosas independientes: una venta vieja se puede cargar hoy, y una carga atrasada puede traer ventas recientes.

En mi ejercicio se ve claro. Las ventas son siempre del 10, 11 y 12 de enero de 2026 en los tres escenarios. Si hubiera usado `fecha_venta`, la fuente habría salido "desactualizada" por unos diez meses en todos los casos, incluso cuando la carga había sido hace 2 horas, y el DAG nunca habría construido el resumen. Con `_loaded_at`, en cambio, el resultado depende solo de cuándo llegaron los datos: con la carga de hace 2 h pasó (`max_loaded_at_time_ago_in_s` = 7 237 s en la ejecución `manual__2026-11-12T11:33:47+00:00`), con la de hace 18 h dio advertencia (64 815 s) y con la de hace 30 h falló (108 013 s, más que las 24 h de `error_after`) en `manual__2026-11-12T11:43:52+00:00`. Los datos de negocio eran idénticos en los tres casos y lo único que cambié fue `_loaded_at`, que es justo lo que el control debe medir.

## 2. ¿Por qué las pruebas de integridad no garantizan actualidad?

Porque revisan cómo son los datos, no cuándo llegaron. `unique`, `not_null` y la prueba de valores válidos comprueban que no haya identificadores repetidos, campos vacíos, cantidades no positivas ni precios negativos. Una tabla con datos de hace un mes puede cumplir todo eso perfectamente, y ninguna de esas pruebas compara `_loaded_at` con la hora actual.

En el escenario desactualizado mis seis registros eran válidos: con esos mismos datos `dbt build` había pasado las 19 pruebas en el escenario actualizado. Si el DAG hubiera ido directo al build, habría terminado en verde reconstruyendo el resumen con una carga de hace 30 horas, que es justo el problema que describe el enunciado: un proceso sin errores técnicos pero con información vieja. Por eso freshness es una comprobación aparte, que además `dbt build` no ejecuta por sí solo, y la puse antes del build. En `manual__2026-11-12T11:43:52+00:00` falló, el build quedó en `upstream_failed` sin ejecutarse y el resumen conservó las filas anteriores.
