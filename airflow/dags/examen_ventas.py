from datetime import datetime, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from runtime import run_dbt

with DAG(
    dag_id="examen_ventas",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"retries": 0},
    tags=["examen"],
) as dag:
    # Comprueba la actualidad de raw.ventas (max(_loaded_at)) con los umbrales de
    # sources.yml. Una advertencia termina con salida 0 y la tarea queda en success;
    # un error hace que run_dbt lance CalledProcessError y la tarea queda en failed.
    verificar_freshness = PythonOperator(
        task_id="verificar_freshness",
        python_callable=run_dbt,
        op_args=[["source", "freshness"]],
    )

    construir_resumen = PythonOperator(
        task_id="construir_resumen",
        python_callable=run_dbt,
        op_args=[["build"]],
    )

    # Con la regla predeterminada all_success, si freshness falla el build queda
    # en upstream_failed y el resumen anterior se conserva.
    verificar_freshness >> construir_resumen
