"""
Day 4 — Flask backend.
Looks up a scored applicant in BigQuery and returns a plain-language explanation.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from google.cloud import bigquery
from explainer import explain_decision   # the function we built in Part 2

PROJECT_ID = "credit-risk-explainable-ai"
SCORED_TABLE = "credit_analytics.scored_applications"

app = Flask(__name__)
CORS(app)                                  # allow the React frontend to call this
client = bigquery.Client(project=PROJECT_ID)


@app.route("/explain/<int:applicant_id>")
def explain(applicant_id):
    """Look up one applicant's score + reasons, then return a Claude explanation."""
    # Parameterized query — NEVER format user input straight into SQL (injection risk).
    query = f"""
        SELECT decision, default_probability, top_reason_1, top_reason_2, top_reason_3
        FROM `{PROJECT_ID}.{SCORED_TABLE}`
        WHERE applicant_id = @applicant_id
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("applicant_id", "INT64", applicant_id)
        ]
    )
    rows = list(client.query(query, job_config=job_config).result())

    if not rows:
        return jsonify({"error": f"Applicant {applicant_id} not found"}), 404

    row = rows[0]
    reason_codes = [row.top_reason_1, row.top_reason_2, row.top_reason_3]

    explanation = explain_decision(
        decision=row.decision,
        probability=row.default_probability,
        reason_codes=reason_codes,
    )

    return jsonify({
        "applicant_id": applicant_id,
        "decision": row.decision,
        "default_probability": row.default_probability,
        "explanation": explanation,
    })


if __name__ == "__main__":
    # Port 5001, not 5000 — macOS uses 5000 for AirPlay and it'll conflict.
    app.run(port=5001, debug=True)