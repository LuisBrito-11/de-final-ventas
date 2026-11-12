# Entrega del punto 2: ventas diarias con control de actualidad

Examen final de Arquitecturas de Datos 2026-2 (Universidad EIA). Estudiante: Luis Miguel Brito Rincón.
Enunciado: el [`README.md`](../README.md) de este repositorio (copia de <https://github.com/smm-0216/DE-Final-Ventas>).

## Archivos modificados (solo los tres permitidos)

| Archivo | Cambio |
| --- | --- |
| [`dbt/models/ventas_diarias.sql`](../dbt/models/ventas_diarias.sql) | Una fila por `fecha_venta` desde `ref('stg_ventas')`: `count(*)` como `numero_ventas`, `sum(cantidad)` como `unidades_vendidas` y `sum(cantidad * precio_unitario)` como `ingreso_total`. El producto de `INTEGER` por `DECIMAL(12,2)` y su suma siguen siendo `DECIMAL` (la tabla queda con `DECIMAL(38,2)`), así que no se pierde precisión. |
| [`dbt/models/sources.yml`](../dbt/models/sources.yml) | En la tabla `ventas`, al mismo nivel que `columns` y fuera de `config` (sintaxis de dbt 1.9): `loaded_at_field: _loaded_at` y `freshness` con `warn_after: {count: 12, period: hour}` y `error_after: {count: 24, period: hour}`. |
| [`airflow/dags/examen_ventas.py`](../airflow/dags/examen_ventas.py) | Nueva tarea `verificar_freshness` (`PythonOperator` con `python_callable=run_dbt` y `op_args=[["source", "freshness"]]`) y la dependencia `verificar_freshness >> construir_resumen`. Se mantiene la regla `all_success` por defecto, sin `--warn-error`, y el error de dbt se propaga a Airflow. |

No se modificaron datos, pruebas, perfiles, `scripts/`, `compose.yaml` ni el `README.md` del profesor (`git diff origin/main --stat` solo muestra esos tres archivos más la carpeta nueva `entrega/`).

## Entorno

- Imagen `smendezm/examen-ventas:1.0` (Airflow 2.10.5, dbt-core 1.9.4, dbt-duckdb 1.9.2), preparada el día anterior con el ZIP del profesor. Se conservó el `.env` creado entonces por `scripts/preparar.sh` (no se versiona).
- En Windows se usó **Git Bash** en lugar de Ubuntu en WSL2. Los comandos son los mismos (`docker compose ...`, `bash scripts/examen.sh ...`) y el contenedor es idéntico.
- `docker compose up -d --wait airflow` y `bash scripts/examen.sh check` terminaron sin errores: [`entorno_check.txt`](entorno_check.txt) (incluye el DAG activo, sin errores de importación y el árbol de tareas `verificar_freshness → construir_resumen`).
- Para lanzar el DAG se usó `docker compose exec airflow airflow dags trigger examen_ventas`, que crea una ejecución **manual** igual que el botón **Trigger DAG** de la interfaz (`run_type = manual`, `external_trigger = True`, identificador `manual__<fecha>`).
- Horas en UTC (la interfaz de Airflow y el contenedor trabajan en UTC).

## Comprobación directa (antes de usar Airflow)

- `bash scripts/examen.sh scenario actualizada` y `bash scripts/examen.sh dbt build`: 19 de 19 nodos en `PASS`/`OK`.
- Consulta del resumen:

| fecha_venta | numero_ventas | unidades_vendidas | ingreso_total |
|---|---:|---:|---:|
| 2026-01-10 | 2 | 3 | 46.00 |
| 2026-01-11 | 3 | 6 | 51.25 |
| 2026-01-12 | 1 | 4 | 12.40 |

- `dbt source freshness` en cada escenario: `actualizada` → `PASS`, salida 0; `advertencia` → `WARN`, salida 0; `desactualizada` → `ERROR STALE`, salida 1.

## Dónde aparece la salida de dbt

`run_dbt` (en `scripts/runtime.py`, que no se puede modificar) lanza dbt con `subprocess.run` sin capturar su salida. Por eso el **log de la tarea en Airflow** muestra lo que imprime Python (`INICIO dbt`, `FIN dbt` o el `CalledProcessError` cuando dbt falla), mientras que las líneas propias de dbt (`PASS`/`WARN`/`ERROR STALE freshness of ventas_raw.ventas`) aparecen en el **log del contenedor** (`docker compose logs airflow`). Además, dbt deja el detalle de la comprobación en `sources.json` (`bash scripts/examen.sh artifacts`). En cada escenario se guardaron las tres fuentes.

## Escenario 1: fuente actualizada (obligatorio)

Ejecución **`manual__2026-11-12T11:33:47+00:00`**. Carga de raw: `max(_loaded_at) = 2026-11-12T09:33:24Z` (hace 2 h) ([`scenario.txt`](escenario1_actualizada/scenario.txt)).

| Tarea | Estado | Inicio → fin (UTC) |
| --- | --- | --- |
| `verificar_freshness` | `success` | 11:33:55 → 11:34:01 |
| `construir_resumen` | `success` | 11:34:06 → 11:34:12 |

| Evidencia | Contenido |
| --- | --- |
| [`capturas/01_grid_estados.png`](escenario1_actualizada/capturas/01_grid_estados.png) | Identificador de ejecución, estado `success` y las dos tareas en verde. |
| [`capturas/02_grafico.png`](escenario1_actualizada/capturas/02_grafico.png) | Gráfico: `verificar_freshness` → `construir_resumen`, ambas `success`. |
| [`capturas/03_log_verificar_freshness.png`](escenario1_actualizada/capturas/03_log_verificar_freshness.png) y [`log_verificar_freshness.txt`](escenario1_actualizada/log_verificar_freshness.txt) | `INICIO dbt ['source', 'freshness']` y `FIN dbt ['source', 'freshness']`. |
| [`capturas/04_log_construir_resumen.png`](escenario1_actualizada/capturas/04_log_construir_resumen.png) y [`log_construir_resumen.txt`](escenario1_actualizada/log_construir_resumen.txt) | `INICIO dbt ['build']` y `FIN dbt ['build']`. |
| [`estados_tareas.txt`](escenario1_actualizada/estados_tareas.txt), [`ejecuciones_dag.txt`](escenario1_actualizada/ejecuciones_dag.txt), [`trigger.txt`](escenario1_actualizada/trigger.txt) | Estados y horas de las tareas desde la CLI de Airflow y salida del `trigger`. |
| [`log_contenedor_airflow.txt`](escenario1_actualizada/log_contenedor_airflow.txt) | Salida de dbt: `PASS freshness of ventas_raw.ventas` y luego `Done. PASS=19 WARN=0 ERROR=0`. |
| [`artefactos_dbt_tras_ejecucion.txt`](escenario1_actualizada/artefactos_dbt_tras_ejecucion.txt) | `sources.json`: `status: pass`, `max_loaded_at_time_ago_in_s: 7236.8` (2,0 h). |
| [`../resumen_antes_del_bloqueo.txt`](resumen_antes_del_bloqueo.txt) | Consulta del resumen después de esta ejecución. |

## Escenario 2: fuente desactualizada (obligatorio)

Sin tareas en ejecución ([`ejecuciones_antes_de_preparar.txt`](escenario2_desactualizada/ejecuciones_antes_de_preparar.txt)), se preparó el escenario (`max(_loaded_at) = 2026-11-11T05:43:48Z`, hace 30 h) y enseguida se creó una ejecución **nueva**: **`manual__2026-11-12T11:43:52+00:00`**. No se limpió ni se reutilizó la ejecución anterior y no se ejecutó ningún `dbt build` manual entre la preparación y la captura de estas evidencias.

| Tarea | Estado | Detalle |
| --- | --- | --- |
| `verificar_freshness` | `failed` | 11:43:57 → 11:44:01, `try_number = 1` |
| `construir_resumen` | `upstream_failed` | `try_number = 0`, sin `pid` ni `job_id`: nunca se ejecutó |

| Evidencia | Contenido |
| --- | --- |
| [`capturas/01_grid_estados.png`](escenario2_desactualizada/capturas/01_grid_estados.png) | Identificador de ejecución y estado `failed`: freshness en rojo, build en naranja. |
| [`capturas/02_grafico.png`](escenario2_desactualizada/capturas/02_grafico.png) | Gráfico: `verificar_freshness` `failed` → `construir_resumen` `upstream_failed`. |
| [`capturas/03_log_verificar_freshness.png`](escenario2_desactualizada/capturas/03_log_verificar_freshness.png) y [`log_verificar_freshness.txt`](escenario2_desactualizada/log_verificar_freshness.txt) | `INICIO dbt ['source', 'freshness']`, `CalledProcessError: Command '['/opt/dbt/bin/dbt', 'source', 'freshness', ...]' returned non-zero exit status 1` y `Marking task as FAILED`. No aparece `FIN dbt`. |
| [`log_contenedor_airflow.txt`](escenario2_desactualizada/log_contenedor_airflow.txt) | Motivo según dbt: `ERROR STALE freshness of ventas_raw.ventas`. En esa ventana no hay ninguna ejecución de `build`. |
| [`artefactos_dbt_tras_ejecucion.txt`](escenario2_desactualizada/artefactos_dbt_tras_ejecucion.txt) | `sources.json` de esa comprobación: `status: error`, `max_loaded_at: 2026-11-11T05:43:48Z`, `snapshotted_at: 2026-11-12T11:44:01Z`, `max_loaded_at_time_ago_in_s: 108013` (**30,0 h, más que el umbral `error_after` de 24 h**). |
| [`capturas/04_construir_resumen_sin_intento.png`](escenario2_desactualizada/capturas/04_construir_resumen_sin_intento.png) | Log de `construir_resumen` en esa ejecución: vacío, sin intento. |
| [`verificacion_build_sin_intento.txt`](escenario2_desactualizada/verificacion_build_sin_intento.txt) | Solo existe el archivo de log de `verificar_freshness`; la carpeta de `construir_resumen` no existe; en la tabla `task_instance`, `construir_resumen` tiene `try_number = 0`, `duration = 0` y sin `pid`. Por lo tanto no hubo `INICIO dbt` de build en esta ejecución. |
| [`capturas/05_lista_ejecuciones.png`](escenario2_desactualizada/capturas/05_lista_ejecuciones.png) y [`ejecuciones_dag.txt`](escenario2_desactualizada/ejecuciones_dag.txt) | Las dos ejecuciones son distintas: la del escenario 1 sigue `success` y la nueva quedó `failed`. |
| [`../resumen_despues_del_bloqueo.txt`](resumen_despues_del_bloqueo.txt) | Consulta del resumen después del bloqueo. |

**Resumen antes y después del bloqueo:** [`resumen_antes_del_bloqueo.txt`](resumen_antes_del_bloqueo.txt) y [`resumen_despues_del_bloqueo.txt`](resumen_despues_del_bloqueo.txt) son idénticos byte a byte (`cmp` sin diferencias). Como los datos de negocio no cambian entre escenarios, la igualdad sola no prueba que build no corrió; eso lo prueban los estados de Airflow (`upstream_failed`, `try_number = 0`) y la ausencia de log de build.

## Escenario opcional: advertencia

Ejecución **`manual__2026-11-12T11:46:17+00:00`** con `max(_loaded_at)` de hace 18 h. Las dos tareas terminaron en `success`; dbt informó `WARN freshness of ventas_raw.ventas` ([`log_contenedor_airflow.txt`](escenario3_advertencia_opcional/log_contenedor_airflow.txt)) y `sources.json` registró `status: warn` con `max_loaded_at_time_ago_in_s: 64815` (18,0 h) ([`sources.json`](escenario3_advertencia_opcional/sources.json)). La advertencia no bloqueó el build ([`capturas/01_grafico.png`](escenario3_advertencia_opcional/capturas/01_grafico.png), [`estados_tareas.txt`](escenario3_advertencia_opcional/estados_tareas.txt)). Se ejecutó después de guardar las evidencias de los dos escenarios obligatorios.

## Respuestas conceptuales

En [`respuestas.md`](respuestas.md).
