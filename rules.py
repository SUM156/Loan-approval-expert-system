"""
rules.py
---------
Core AI logic for the Loan Approval Expert System.

This module is intentionally UI-free. It implements a small forward-
chaining inference engine over a working memory of "facts", driven by
a list of IF-THEN production rules. This is the classic rule-based /
expert-system approach to AI (facts + rules + inference), in the
style of early systems like MYCIN, applied here to loan underwriting.

Two rule sets are provided (STANDARD_RULES and STRICT_RULES) so the
evaluation module can compare two different policies on the same data.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any


@dataclass
class Rule:
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    conclusion: Dict[str, Any]
    explanation: str


def _standard_rules() -> List[Rule]:
    return [
        Rule(
            name="R1_credit_income_ok",
            condition=lambda f: f["credit_score"] >= 650 and f["annual_income"] >= 40000,
            conclusion={"credit_income_ok": True},
            explanation="Credit score >= 650 and annual income >= $40,000",
        ),
        Rule(
            name="R2_stable_employment",
            condition=lambda f: f["employment_years"] >= 2 and f["debt_to_income"] < 0.40,
            conclusion={"stable_profile": True},
            explanation="At least 2 years employment and debt-to-income < 0.40",
        ),
        Rule(
            name="R3_low_credit_reject",
            condition=lambda f: f["credit_score"] < 550,
            conclusion={"decision": "Rejected", "reason": "Credit score below 550 (high risk)"},
            explanation="Credit score below 550 is an automatic decline",
        ),
        Rule(
            name="R4_high_debt_reject",
            condition=lambda f: f["debt_to_income"] >= 0.55,
            conclusion={"decision": "Rejected", "reason": "Debt-to-income ratio of 0.55 or higher"},
            explanation="Debt-to-income >= 0.55 is considered unaffordable",
        ),
        Rule(
            name="R5_approve",
            condition=lambda f: f.get("credit_income_ok") and f.get("stable_profile") and "decision" not in f,
            conclusion={"decision": "Approved", "reason": "Strong credit/income and a stable financial profile"},
            explanation="credit_income_ok AND stable_profile AND no prior rejection",
        ),
        Rule(
            name="R6_manual_review",
            condition=lambda f: "decision" not in f and f.get("_no_new_facts"),
            conclusion={"decision": "Manual Review", "reason": "Profile does not clearly meet or fail the criteria"},
            explanation="No rule confidently approved or rejected the applicant",
        ),
    ]


def _strict_rules() -> List[Rule]:
    return [
        Rule(
            name="R1_credit_income_ok_strict",
            condition=lambda f: f["credit_score"] >= 700 and f["annual_income"] >= 60000,
            conclusion={"credit_income_ok": True},
            explanation="Credit score >= 700 and annual income >= $60,000 (stricter)",
        ),
        Rule(
            name="R2_stable_employment_strict",
            condition=lambda f: f["employment_years"] >= 4 and f["debt_to_income"] < 0.30,
            conclusion={"stable_profile": True},
            explanation="At least 4 years employment and debt-to-income < 0.30 (stricter)",
        ),
        Rule(
            name="R3_low_credit_reject",
            condition=lambda f: f["credit_score"] < 600,
            conclusion={"decision": "Rejected", "reason": "Credit score below 600 (high risk, strict policy)"},
            explanation="Credit score below 600 is an automatic decline under the strict policy",
        ),
        Rule(
            name="R4_high_debt_reject_strict",
            condition=lambda f: f["debt_to_income"] >= 0.40,
            conclusion={"decision": "Rejected", "reason": "Debt-to-income ratio of 0.40 or higher"},
            explanation="Debt-to-income >= 0.40 is considered unaffordable under the strict policy",
        ),
        Rule(
            name="R5_approve",
            condition=lambda f: f.get("credit_income_ok") and f.get("stable_profile") and "decision" not in f,
            conclusion={"decision": "Approved", "reason": "Meets the strict credit, income and stability bar"},
            explanation="credit_income_ok AND stable_profile AND no prior rejection",
        ),
        Rule(
            name="R6_manual_review",
            condition=lambda f: "decision" not in f and f.get("_no_new_facts"),
            conclusion={"decision": "Manual Review", "reason": "Profile does not clearly meet or fail the strict criteria"},
            explanation="No rule confidently approved or rejected the applicant",
        ),
    ]


RULE_SETS = {
    "Standard Policy": _standard_rules,
    "Strict Policy": _strict_rules,
}


def preprocess_applicant(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Derive computed facts (e.g. debt_to_income) from raw input fields."""
    facts = dict(raw)
    monthly_income = raw["annual_income"] / 12
    facts["monthly_income"] = round(monthly_income, 2)
    facts["debt_to_income"] = round(raw["monthly_debt"] / monthly_income, 3) if monthly_income > 0 else 1.0
    return facts


def run_forward_chaining(facts: Dict[str, Any], rules: List[Rule], max_iterations: int = 10):
    """
    Runs forward-chaining inference to a fixed point.

    Returns:
        final_facts: dict of all derived + input facts
        fired_trace: ordered list of dicts describing each rule firing
                     (used for the explainability module)
    """
    working_memory = dict(facts)
    fired_trace = []

    for iteration in range(max_iterations):
        new_fact_added = False
        for rule in rules:
            try:
                condition_met = rule.condition(working_memory)
            except KeyError:
                condition_met = False

            if condition_met:
                # Skip if this exact conclusion is already known (avoid re-firing forever)
                already_known = all(working_memory.get(k) == v for k, v in rule.conclusion.items())
                if not already_known:
                    working_memory.update(rule.conclusion)
                    fired_trace.append({
                        "iteration": iteration + 1,
                        "rule": rule.name,
                        "explanation": rule.explanation,
                        "concluded": rule.conclusion,
                    })
                    new_fact_added = True

        if not new_fact_added:
            # Give the "no new facts" rules (manual review) one more chance to fire
            working_memory["_no_new_facts"] = True
            still_new = False
            for rule in rules:
                if rule.condition(working_memory):
                    already_known = all(working_memory.get(k) == v for k, v in rule.conclusion.items())
                    if not already_known:
                        working_memory.update(rule.conclusion)
                        fired_trace.append({
                            "iteration": iteration + 1,
                            "rule": rule.name,
                            "explanation": rule.explanation,
                            "concluded": rule.conclusion,
                        })
                        still_new = True
            if not still_new:
                break

    working_memory.setdefault("decision", "Manual Review")
    working_memory.setdefault("reason", "No rule reached a firm conclusion")
    return working_memory, fired_trace


def evaluate_rule_set(df, rule_builder_fn):
    """
    Runs the given rule set over every row of a DataFrame (which must
    contain a 'ground_truth' column of 'Approved'/'Rejected') and
    computes accuracy, precision, and recall for the 'Approved' class.
    Rows the engine sends to Manual Review are scored as a miss
    against ground truth (a conservative but simple evaluation choice).
    """
    rules = rule_builder_fn()
    tp = fp = tn = fn = 0
    predictions = []

    for _, row in df.iterrows():
        raw = row.to_dict()
        facts = preprocess_applicant(raw)
        result, _ = run_forward_chaining(facts, rules)
        pred = result["decision"]
        predictions.append(pred)

        truth = row["ground_truth"]
        pred_positive = (pred == "Approved")
        truth_positive = (truth == "Approved")

        if pred_positive and truth_positive:
            tp += 1
        elif pred_positive and not truth_positive:
            fp += 1
        elif not pred_positive and not truth_positive:
            tn += 1
        else:
            fn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    approval_rate = predictions.count("Approved") / len(predictions) if predictions else 0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "approval_rate": approval_rate,
        "predictions": predictions,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }
