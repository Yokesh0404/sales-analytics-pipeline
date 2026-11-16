"""
### Olist daily pipeline

Runs the whole pipeline once a day, in order:

1. **ingest_raw**: load the Olist CSVs into the `raw` schema
2. **quality_checks**: check the raw data; stop if anything is broken
3. **dbt_run**: build the `staging` and `analytics` (star schema) tables
4. **dbt_test**: test the built tables

If a step fails, the steps after it don't run.
"""
from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# Where docker-compose mounts the project inside the container.
PROJECT_DIR = "/opt/project"
# The separate Python environment with pandas, SQLAlchemy and dbt (see airflow/Dockerfile).
PYTHON = "/opt/airflow/pipeline-venv/bin/python"

# Settings applied to every task in this DAG.
default_args = {
    "owner": "yokesh",
    "retries": 2,                          # try a failed task up to 2 more times...
    "retry_delay": timedelta(minutes=2),   # ...waiting 2 minutes between tries
    "execution_timeout": timedelta(minutes=30),  # kill a task that hangs
}

with DAG(
    dag_id="olist_pipeline",
    description="Ingest Olist CSVs -> quality checks -> dbt run -> dbt test",
    schedule="@daily",                     # once a day at midnight UTC (05:30 in India)
    # Note: in Airflow 3, "@daily" runs at the START of each day. So switching the DAG
    # on runs today's run straight away instead of waiting until tomorrow.
    start_date=pendulum.datetime(2026, 11, 16, tz="UTC"),
    catchup=False,                         # don't "back-fill" runs for past days
    max_active_runs=1,                     # never run two copies of the pipeline at once
    default_args=default_args,
    doc_md=__doc__,                        # shows the docstring above in the Airflow UI
    tags=["olist"],
) as dag:

    # A BashOperator runs a shell command. If the command exits with a
    # non-zero code, the task FAILS (our scripts call sys.exit(1) on errors).

    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} src/ingest.py",
        doc_md="""
        Loads every CSV in `data/raw/` into the `raw` schema (full refresh, safe to re-run).
        Fails if any file can't be loaded. Log: `logs/ingestion.log`.
        """,
    )

    quality_checks = BashOperator(
        task_id="quality_checks",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} src/quality_checks.py",
        doc_md="""
        Runs 50 data quality checks on the `raw` schema and saves results to
        `quality.check_results`. Fails only on FAIL-level issues (broken keys);
        WARN-level issues are logged. Log: `logs/quality.log`.
        """,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} src/run_dbt.py run",
        doc_md="""
        Builds all dbt models: 9 staging tables and the star schema in `analytics`
        (fct_orders, fct_order_items, dim_customers, dim_products, dim_sellers, dim_date).
        """,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} src/run_dbt.py test",
        doc_md="""
        Runs the dbt tests: unique/not_null keys, relationships between facts and
        dimensions, accepted values. Fails if any test fails.
        """,
    )

    # ">>" sets the order: each task runs only after the previous one succeeds.
    ingest_raw >> quality_checks >> dbt_run >> dbt_test
