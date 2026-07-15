# Loan Approval Expert System

A rule-based AI application that decides whether to approve a loan
applicant and explains exactly which rules led to that decision. Built
for the AI Lab Project (UI + AI Integration).

- **AI approach:** Rule-based expert system — facts + IF-THEN rules +
  forward-chaining inference (Option 1 in the project brief).
- **UI:** Streamlit web app with sliders, a decision gauge, a rule-firing
  trace table, and a policy comparison dashboard.

  <img width="1600" height="668" alt="WhatsApp Image 2026-07-15 at 10 23 00 AM" src="https://github.com/user-attachments/assets/b5decb09-e6fc-43c2-b946-413f9455eaa4" />
<img width="1329" height="784" alt="WhatsApp Image 2026-07-15 at 10 22 57 AM" src="https://github.com/user-attachments/assets/77e0567b-ec49-49c4-91a0-613066dc6def" />
<img width="1424" height="752" alt="WhatsApp Image 2026-07-15 at 10 22 53 AM" src="https://github.com/user-attachments/assets/672be9e8-8855-4991-a0de-cb7d4ea7682b" />


## 1. Project Structure

```
LoanExpertSystem_Project/
├── app.py                 # Streamlit UI (render_ui equivalent)
├── rules.py                # Inference engine (core AI logic, no UI code)
├── generate_data.py        # Script that created the sample dataset
├── requirements.txt
├── README.md
├── report.md                # Short report: problem, method, AI used, results
├── data/
│   └── applicants.csv       # Sample dataset (40 synthetic applicants)
└── screenshots/              # Put your own screenshots here (see step 4 below)
```

## 2. Setup

```bash
cd LoanExpertSystem_Project
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## 4. Taking screenshots (required deliverable)

Once the app is running in your browser:
1. **Applicant & Decision tab** — enter an applicant, click "Run Inference
   Engine", screenshot the result panel + gauge.
2. **Explainability tab** — screenshot the rule-firing trace table and chart.
3. **Evaluation tab** — click "Run evaluation & compare both policies" and
   screenshot the metrics table + bar chart.

Save the images into `screenshots/`.

## 5. How the app is organized (maps to the required modules)

| Module | Where it lives |
|---|---|
| Problem Setup (input + validation) | `app.py`, tab "Applicant & Decision" |
| Core Logic (forward-chaining engine) | `rules.py` |
| Visual UI (gauge, tables, bar charts) | `app.py`, all three tabs |
| Explainability (rule trace, plain-language reason) | `app.py`, tab "Explainability" |
| Evaluation (accuracy/precision/recall, comparison) | `app.py`, tab "Evaluation & Comparison"; metrics computed in `rules.py:evaluate_rule_set` |

## 6. Regenerating the sample dataset

The dataset in `data/applicants.csv` was produced with:

```bash
python3 generate_data.py
```

It creates 40 synthetic applicants with a noisy "ground truth" approval
label, used only to score the rule sets in the Evaluation tab.

## 7. Two policies, for comparison

- **Standard Policy** — moderate thresholds (credit score ≥ 650, income
  ≥ $40k, debt-to-income < 0.40).
- **Strict Policy** — tighter thresholds (credit score ≥ 700, income
  ≥ $60k, debt-to-income < 0.30).

Switch between them from the sidebar dropdown; the Evaluation tab scores
both against the sample dataset side-by-side.
