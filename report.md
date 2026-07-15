# Short Report: Loan Approval Expert System

## 1. Problem

Loan officers must repeatedly decide whether to approve an applicant
based on a fairly consistent set of criteria (credit score, income,
employment stability, existing debt). This project automates that
decision with a transparent, rule-based AI system, and — critically —
shows *why* each decision was made, not just the final answer.

- **Input:** applicant facts (credit score, annual income, employment
  years, monthly debt, age, requested amount).
- **Output:** Approved / Rejected / Manual Review, with a plain-language
  reason and the full chain of rules that fired.
- **Constraints:** decisions must be explainable and consistent (same
  inputs always produce the same decision).

## 2. Method

The system is a **rule-based expert system** using **forward-chaining
inference**:

1. Raw applicant inputs are turned into a working-memory of "facts"
   (including a derived fact, debt-to-income ratio).
2. A fixed list of IF-THEN rules is repeatedly scanned. Any rule whose
   condition is satisfied by the current facts "fires", adding new
   facts (e.g. `credit_income_ok = True`).
3. This repeats until no new facts are produced (a fixed point) or a
   `decision` fact has been derived.
4. Every firing is logged with the rule name, the condition it
   satisfied, and the fact(s) it added — this trace is what powers the
   Explainability tab.

Two rule sets (policies) were implemented — a **Standard Policy** and a
tighter **Strict Policy** — so the app can compare underwriting
strategies directly, satisfying the "compare at least two settings"
evaluation requirement.

## 3. AI Technique Used

Rule-based AI (Option 1 from the assignment): explicit facts, explicit
IF-THEN production rules, and a forward-chaining inference engine. No
external AI API or model training is used — this keeps the entire
decision process auditable, which is important for a domain like loan
underwriting where explainability matters.

## 4. Results

Both policies were evaluated on a 40-applicant synthetic dataset with
"ground truth" outcomes (see `generate_data.py`):

| Policy | Accuracy | Precision | Recall | Approval Rate |
|---|---|---|---|---|
| Standard Policy | ~62.5% | ~100% | ~44% | ~30% |
| Strict Policy | ~47.5% | ~100% | ~22% | ~15% |

(Exact figures are re-computed live in the Evaluation tab and may shift
slightly if `generate_data.py` is re-run, since it uses randomness.)

**Interpretation:** Both policies have perfect precision — when the
system does approve someone, that approval reliably matches the
ground-truth "Approved" label. The Standard Policy has noticeably
higher recall and accuracy because the Strict Policy's tighter
thresholds push many otherwise-good applicants into "Manual Review",
which is scored conservatively (as a non-approval) in this evaluation.
This is a realistic trade-off: tighter policies reduce risk of bad
approvals but reject/defer more good applicants.

## 5. Limitations & Future Improvements

- The rule thresholds are hand-picked, not learned from real data — a
  natural extension is Option 3 (train a classifier on labeled
  historical loan outcomes and compare it against these hand-written
  rules).
- "Manual Review" cases are currently scored as non-approvals during
  evaluation, which understates recall for a policy that defers rather
  than rejects; a fairer 3-class evaluation could be added.
- The rule engine currently only reasons over 4 input facts; a real
  system would also weigh collateral, loan term, and existing customer
  history.
