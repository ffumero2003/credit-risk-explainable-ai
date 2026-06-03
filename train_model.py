"""
Project 2 — Credit Risk Scoring + Explainable AI
Day 3: Modeling
Part 2 load · Part 3 prepare · Part 4 train+evaluate · Part 5 SHAP · Part 6 score+write back.
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
import shap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, roc_curve
from xgboost import XGBClassifier

# ----------------- CONFIG -----------------
PROJECT_ID = "credit-risk-explainable-ai"
FEATURE_TABLE = "credit_analytics.mart_credit_features"
SCORED_TABLE = "credit_analytics.scored_applications"
DECISION_THRESHOLD = 0.5   # decline if predicted risk >= this (a tunable business choice)

# ----------------- LOAD -----------------
client = bigquery.Client(project=PROJECT_ID)
query = f"SELECT * FROM `{PROJECT_ID}.{FEATURE_TABLE}`"
df = client.query(query).to_dataframe()
print(f"Loaded {df.shape[0]:,} rows, {df.shape[1]} columns")

# ----------------- PREPARE FEATURES -----------------
applicant_ids = df["applicant_id"]
y = df["target_default"].astype("int64")
# Drop the id, the label, AND gender — a protected attribute under ECOA, so
# using it in a credit decision is a fair-lending violation.
X = df.drop(columns=["applicant_id", "target_default", "gender"])
X = pd.get_dummies(X, drop_first=True)
X = X.astype("float64")
X = X.fillna(X.median())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {X_train.shape[0]:,} | Test: {X_test.shape[0]:,} | Features: {X_train.shape[1]}")

# ----------------- TRAIN MODELS -----------------
pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

logreg = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
logreg.fit(X_train, y_train)

xgb = XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.1,
    scale_pos_weight=pos_weight, eval_metric="auc", random_state=42,
)
xgb.fit(X_train, y_train)

# ----------------- EVALUATE -----------------
def evaluate(name, y_true, probs):
    auc = roc_auc_score(y_true, probs)
    gini = 2 * auc - 1
    fpr, tpr, _ = roc_curve(y_true, probs)
    ks = max(tpr - fpr)
    print(f"\n{name}")
    print(f"  AUC:  {auc:.3f}")
    print(f"  Gini: {gini:.3f}")
    print(f"  KS:   {ks:.3f}")

evaluate("Logistic Regression", y_test, logreg.predict_proba(X_test)[:, 1])
evaluate("XGBoost",             y_test, xgb.predict_proba(X_test)[:, 1])

# ----------------- SHAP EXPLAINABILITY -----------------
explainer = shap.TreeExplainer(xgb)
shap_values = explainer.shap_values(X_test)
if isinstance(shap_values, list):
    shap_values = shap_values[1]

probs = xgb.predict_proba(X_test)[:, 1]
i = int(np.argmax(probs))
print(f"\n--- Explaining one applicant ---")
print(f"Predicted default probability: {probs[i]:.2f}")
person = sorted(zip(X_test.columns, shap_values[i]), key=lambda kv: abs(kv[1]), reverse=True)
print("Top factors (+ raises risk, - lowers risk):")
for feature, val in person[:5]:
    sign = "+" if val > 0 else "-"
    print(f"  {sign} {feature}  (SHAP {val:+.3f})")

mean_abs = np.abs(shap_values).mean(axis=0)
overall = sorted(zip(X_test.columns, mean_abs), key=lambda kv: kv[1], reverse=True)
print("\n--- Most important features overall ---")
for feature, imp in overall[:10]:
    print(f"  {feature}: {imp:.3f}")

# ----------------- SCORE & WRITE BACK TO BIGQUERY -----------------
feature_names = X_test.columns.to_numpy()

# For each applicant, the 3 features with the largest POSITIVE SHAP values are
# the factors that raised their risk most — their adverse-action reasons.
top_idx = np.argsort(-shap_values, axis=1)[:, :3]

scored = pd.DataFrame({
    "applicant_id": applicant_ids.loc[X_test.index].astype("int64").to_numpy(),
    "default_probability": probs.round(4),
    "decision": np.where(probs >= DECISION_THRESHOLD, "DECLINE", "APPROVE"),
    "top_reason_1": feature_names[top_idx[:, 0]],
    "top_reason_2": feature_names[top_idx[:, 1]],
    "top_reason_3": feature_names[top_idx[:, 2]],
})

# Write the scored table back to BigQuery (WRITE_TRUNCATE = replace on re-run).
client.load_table_from_dataframe(
    scored,
    f"{PROJECT_ID}.{SCORED_TABLE}",
    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
).result()

print(f"\nWrote {len(scored):,} scored applicants to {SCORED_TABLE}")
print(scored.head())