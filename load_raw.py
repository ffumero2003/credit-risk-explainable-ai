"""
Project 2 — Credit Risk Scoring + Explainable AI
Day 1: Ingestion
Loads the raw Home Credit CSVs from local disk into a 'raw' dataset in BigQuery.
No transformation here — that's Day 2 (dbt). Re-running is safe (idempotent).
"""
import os
from google.cloud import bigquery  # official BigQuery client library

# ----------------- CONFIG (the only part you edit) -----------------
PROJECT_ID = "credit-risk-explainable-ai"               # your sandbox project ID
RAW_DATASET = "credit_raw"                              # dataset holding the raw tables
LOCATION = "US"                                         # keep this identical everywhere
# Where the CSVs live. Reads DATA_DIR from the environment if it's set, otherwise
# falls back to your Mac path. On your Mac DATA_DIR is unset, so it uses the local
# folder; inside the Airflow container DATA_DIR is set to /opt/data (via the env var
# we added to docker-compose), so the SAME script works in both places untouched.
DATA_DIR = os.getenv("DATA_DIR", "/Users/felipefumero/datasets/home-credit")


# Map each CSV file -> the raw table name it becomes.
FILES_TO_LOAD = {
    "application_train.csv": "raw_applications",
    "bureau.csv": "raw_bureau",
}

# ----------------- CLIENT -----------------
# Picks up your ADC credentials automatically — no key file needed.
client = bigquery.Client(project=PROJECT_ID, location=LOCATION)


def ensure_dataset_exists(dataset_id):
    """Create the dataset if it isn't there yet. Safe to run every time."""
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)  # no error if it already exists
    print(f"Dataset ready: {PROJECT_ID}.{dataset_id}")


def load_csv_to_bigquery(csv_filename, table_name):
    """Load one CSV file into a BigQuery table, replacing it if it exists."""
    csv_path = f"{DATA_DIR}/{csv_filename}"
    table_id = f"{PROJECT_ID}.{RAW_DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,                  # skip the header row
        autodetect=True,                      # let BigQuery infer column names/types
        write_disposition="WRITE_TRUNCATE",   # replace the table each run (idempotent)
        allow_quoted_newlines=True,           # safe handling of any quoted fields
    )

    # Stream the file straight to BigQuery (low memory, no pandas needed).
    with open(csv_path, "rb") as source_file:
        load_job = client.load_table_from_file(
            source_file, table_id, job_config=job_config
        )

    load_job.result()  # wait for the load to finish; raises an error if it fails

    # Read the row count back so we can confirm the load worked.
    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows:,} rows into {table_id}")


def main():
    """Run the full ingestion: create the dataset, then load each file."""
    ensure_dataset_exists(RAW_DATASET)
    for csv_filename, table_name in FILES_TO_LOAD.items():
        load_csv_to_bigquery(csv_filename, table_name)
    print("Day 1 ingestion complete.")


if __name__ == "__main__":
    main()