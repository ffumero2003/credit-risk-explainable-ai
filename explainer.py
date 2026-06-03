"""
Day 4 — turns a credit decision + SHAP reason codes into a plain-language,
FCRA-style adverse-action explanation using Claude.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()                      # reads ANTHROPIC_API_KEY from .env

MODEL = "claude-haiku-4-5-20251001"       # cheap, fast — right-sized for short text

# Map cryptic feature codes -> clear, consumer-friendly descriptions.
REASON_LABELS = {
    "ext_source_1": "limited external credit history (bureau score 1)",
    "ext_source_2": "limited external credit history (bureau score 2)",
    "ext_source_3": "limited external credit history (bureau score 3)",
    "num_prior_loans": "number of prior loans on record",
    "num_active_loans": "multiple currently active loans",
    "num_overdue_loans": "history of overdue loan payments",
    "max_days_overdue": "severity of past payment delinquency",
    "total_credit_amount": "total amount of existing credit",
    "total_current_debt": "high level of current outstanding debt",
    "annual_income": "reported annual income",
    "loan_amount": "size of the requested loan",
    "loan_annuity": "size of the loan's annual payment",
    "years_employed": "length of employment history",
    "num_children": "number of dependents",
    "owns_car_Y": "vehicle ownership",
    "owns_realty_Y": "property ownership",
    "education_type_Higher education": "education level",
}

# Protected attributes under fair-lending rules (ECOA) — never surface these as
# reasons in a credit decision, even if the model flagged them.
PROTECTED_PREFIXES = ("age_years", "gender_", "family_status_")

def _is_protected(code):
    return code.startswith(PROTECTED_PREFIXES)

def _to_label(code):
    # use a friendly label if we have one; otherwise tidy the raw code
    return REASON_LABELS.get(code, code.replace("_", " "))

def explain_decision(decision, probability, reason_codes):
    """Build a plain-language adverse-action explanation from a decision and its
    top reason codes. Protected attributes are filtered out before calling Claude."""
    # drop protected attributes, then convert the rest to human-readable labels
    reasons = [_to_label(c) for c in reason_codes if not _is_protected(c)]

    system_prompt = (
        "You write clear, professional credit-decision explanations for consumers, "
        "in the style of an FCRA adverse-action notice. Rules: use ONLY the reasons "
        "provided — never invent or infer others; never mention age, gender, marital "
        "status, or any protected characteristic; be factual and neutral, not preachy; "
        "keep it to 2-4 short sentences."
    )

    user_prompt = (
        f"Decision: {decision}\n"
        f"Model-estimated probability of default: {probability:.0%}\n"
        f"Principal factors (most influential first): {', '.join(reasons)}\n\n"
        f"Write the explanation the applicant would receive."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


# quick standalone test
if __name__ == "__main__":
    sample = explain_decision(
        decision="DECLINE",
        probability=0.78,
        reason_codes=["num_active_loans", "ext_source_3", "total_current_debt"],
    )
    print(sample)