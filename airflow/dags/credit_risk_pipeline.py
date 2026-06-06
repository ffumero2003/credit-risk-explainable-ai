"""
Project 2 — Credit Risk Scoring + Explainable AI
Day 6: Orchestration with Apache Airflow

This DAG runs the full batch pipeline in order:
    load_raw  ->  dbt_build  ->  train_model  ->  quality_check

Each step is a stage you already built by hand; Airflow just runs them in
sequence, stops if one fails, and gives you logs + a visual run history.

Note: this batch pipeline does NOT call Claude. The Claude layer (explainer.py
+ app.py) is the live, on-demand part of the project; orchestration is about
the scheduled data pipeline that produces the scored table.
"""

from datetime import datetime

from airflow.sdk import DAG                                      # Airflow 3 DAG object
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator


# Project constant, reused by the quality check below.
PROJECT_ID = "credit-risk-explainable-ai"


def check_scored_rows():
    """Quality gate: fail the pipeline if scored_applications came out empty.

    Runs inside the Airflow worker, which has google-cloud-bigquery installed
    and the mounted credentials in its environment (same as our scripts).
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)
    query = (
        f"SELECT COUNT(*) AS n "
        f"FROM `{PROJECT_ID}.credit_analytics.scored_applications`"
    )
    row_count = list(client.query(query).result())[0].n
    print(f"scored_applications row count: {row_count:,}")

    # If the upstream steps silently produced nothing, this raise marks the
    # task (and the run) as failed — exactly what a real data-quality gate does.
    if row_count == 0:
        raise ValueError("Quality check FAILED: scored_applications is empty.")
    print("Quality check PASSED.")


# default_args apply to every task in the DAG unless overridden per-task.
default_args = {
    "owner": "felipe",
    # First bring-up uses fail-fast (no retries) so any error surfaces
    # immediately instead of being hidden behind a retry delay. In production
    # you'd set this to 1-2 — our tasks are idempotent (WRITE_TRUNCATE), so
    # retrying them is always safe.
    "retries": 0,
}

with DAG(
    dag_id="credit_risk_pipeline",
    description="Ingest -> dbt -> score -> quality check (Credit Risk + Explainable AI)",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),   # a fixed past date; required by Airflow
    schedule=None,                     # manual trigger only (no surprise auto-runs)
    catchup=False,                     # don't backfill past dates
    tags=["credit-risk", "portfolio"],
) as dag:

    # Step 1 — ingest the raw CSVs into BigQuery.
    # We cd into the project first so relative imports/paths behave the same as
    # when you run it by hand. DATA_DIR=/opt/data is already in the worker's env.
    load_raw = BashOperator(
        task_id="load_raw",
        bash_command="cd /opt/project && python load_raw.py",
    )

    # Step 2 — run dbt. `dbt build` runs models AND tests together, so if a data
    # test fails, this task fails too. DBT_PROFILES_DIR=/opt/dbt-profiles is in env.
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/project/credit_risk && dbt build",
    )

    # Step 3 — train the models, run SHAP, write scored_applications back.
    train_model = BashOperator(
        task_id="train_model",
        bash_command="cd /opt/project && python train_model.py",
    )

    # Step 4 — the data-quality gate (Python so it can query + raise).
    quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=check_scored_rows,
    )

    # The dependency chain — this is the "directed" part of the DAG.
    # Each task only starts if the one before it succeeded.
    load_raw >> dbt_build >> train_model >> quality_check