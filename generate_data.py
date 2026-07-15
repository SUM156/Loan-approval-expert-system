"""
generate_data.py
Creates a synthetic sample dataset of loan applicants for the
Loan Approval Expert System project (data/applicants.csv).

Ground truth labels are generated from a slightly noisy version of a
'true' underwriting rule so the evaluation module has something
meaningful to score the rule-based system against.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

N = 40

credit_score = np.random.randint(480, 830, size=N)
annual_income = np.random.randint(18000, 130000, size=N)
employment_years = np.random.randint(0, 15, size=N)
monthly_income = (annual_income / 12).round(2)
monthly_debt = np.random.randint(100, 3500, size=N)
age = np.random.randint(21, 60, size=N)
requested_amount = np.random.randint(5000, 60000, size=N)

debt_to_income = (monthly_debt / monthly_income).round(3)

df = pd.DataFrame({
    "applicant_id": [f"A{100+i}" for i in range(N)],
    "credit_score": credit_score,
    "annual_income": annual_income,
    "employment_years": employment_years,
    "monthly_income": monthly_income,
    "monthly_debt": monthly_debt,
    "debt_to_income": debt_to_income,
    "age": age,
    "requested_amount": requested_amount,
})

# "True" underwriting logic used only to create ground-truth labels
# for evaluation (simulates a real-world outcome, with a little noise).
def true_label(row):
    score = 0
    score += (row.credit_score - 480) / (830 - 480)
    score += (row.annual_income - 18000) / (130000 - 18000)
    score += min(row.employment_years / 10, 1)
    score -= min(row.debt_to_income, 1)
    noise = np.random.normal(0, 0.08)
    return "Approved" if (score / 3 + noise) > 0.42 else "Rejected"

df["ground_truth"] = df.apply(true_label, axis=1)

df.to_csv("/home/claude/LoanExpertSystem_Project/data/applicants.csv", index=False)
print(df.head(10))
print("\nLabel balance:\n", df.ground_truth.value_counts())
