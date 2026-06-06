# Start from the exact Airflow image your stack is already running.
FROM apache/airflow:3.2.2

# Switch to root to install a system library.
# xgboost needs libgomp1 (the GNU OpenMP runtime) to run on Linux —
# it's the Linux equivalent of the `libomp` you installed via brew on your Mac.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Airflow requires pip installs to run as the 'airflow' user, not root.
USER airflow

# Install your pipeline's Python dependencies into the image.
# Note: NO anthropic here — the batch pipeline (ingest -> dbt -> score -> check)
# never calls Claude, so the containers don't need your API key.
# xgboost is pinned <3 to stay compatible with SHAP's TreeExplainer (the bug you hit on Day 3).
RUN pip install --no-cache-dir \
    pandas \
    google-cloud-bigquery \
    dbt-bigquery \
    scikit-learn \
    "xgboost<3" \
    shap