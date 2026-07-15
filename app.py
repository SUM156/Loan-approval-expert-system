"""
app.py
-------
Streamlit front-end for the Loan Approval Expert System.

All AI logic lives in rules.py (forward-chaining inference engine).
This file is only responsible for:
  - collecting/validating user input           (Problem Setup Module)
  - calling into rules.py                       (Core Logic Module)
  - drawing charts, tables, and controls        (Visual UI Module)
  - showing which rules fired and why           (Explainability Module)
  - showing accuracy/precision/recall/compare    (Evaluation Module)
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from rules import (
    RULE_SETS,
    preprocess_applicant,
    run_forward_chaining,
    evaluate_rule_set,
)

st.set_page_config(page_title="Loan Approval Expert System", layout="wide")

DATA_PATH = "data/applicants.csv"


# ---------------------------------------------------------------------------
# load_data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# UI HEADER
# ---------------------------------------------------------------------------
st.title("🏦 Loan Approval Expert System")
st.caption(
    "A rule-based AI system (forward-chaining inference over facts and rules) "
    "that decides whether to approve a loan applicant, and explains exactly why."
)

with st.sidebar:
    st.header("⚙️ Settings")
    policy_name = st.selectbox("Active rule set (policy)", list(RULE_SETS.keys()))
    st.markdown("---")
    st.markdown(
        "**How it works**\n\n"
        "1. You enter applicant facts\n"
        "2. The inference engine fires IF-THEN rules until no new facts appear\n"
        "3. You get a decision + the exact chain of rules that produced it"
    )
    st.markdown("---")
    st.caption("AI approach: Rule-based expert system (facts + rules + forward-chaining inference).")

tab_decide, tab_explain, tab_eval = st.tabs(
    ["📝 Applicant & Decision", "🔍 Explainability", "📊 Evaluation & Comparison"]
)

# ---------------------------------------------------------------------------
# TAB 1: Problem Setup + Core Logic + Visual UI (decision)
# ---------------------------------------------------------------------------
with tab_decide:
    st.subheader("Applicant Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        credit_score = st.slider("Credit score", 300, 850, 680)
        age = st.number_input("Age", min_value=18, max_value=100, value=32)

    with col2:
        annual_income = st.number_input("Annual income ($)", min_value=0, value=55000, step=1000)
        employment_years = st.slider("Years at current job", 0, 40, 3)

    with col3:
        monthly_debt = st.number_input("Monthly debt payments ($)", min_value=0, value=800, step=50)
        requested_amount = st.number_input("Requested loan amount ($)", min_value=0, value=15000, step=500)

    # --- input validation (Problem Setup Module requirement) ---
    errors = []
    if annual_income <= 0:
        errors.append("Annual income must be greater than 0.")
    if requested_amount <= 0:
        errors.append("Requested loan amount must be greater than 0.")
    if monthly_debt < 0:
        errors.append("Monthly debt cannot be negative.")

    run_clicked = st.button("🚀 Run Inference Engine", type="primary", disabled=bool(errors))

    if errors:
        for e in errors:
            st.error(e)

    if run_clicked and not errors:
        raw = {
            "credit_score": credit_score,
            "annual_income": annual_income,
            "employment_years": employment_years,
            "monthly_debt": monthly_debt,
            "age": age,
            "requested_amount": requested_amount,
        }
        facts = preprocess_applicant(raw)
        rules = RULE_SETS[policy_name]()
        result, trace = run_forward_chaining(facts, rules)

        # stash in session_state so the Explainability tab can use it
        st.session_state["last_result"] = result
        st.session_state["last_trace"] = trace
        st.session_state["last_facts"] = facts

        st.success("Inference complete — see the result panel below and the Explainability tab for details.")

    # --- Result panel ---
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        facts = st.session_state["last_facts"]
        decision = result["decision"]

        color = {"Approved": "🟢", "Rejected": "🔴", "Manual Review": "🟡"}.get(decision, "⚪")
        st.markdown("### Result")
        rcol1, rcol2 = st.columns([1, 2])
        with rcol1:
            st.metric("Decision", f"{color} {decision}")
            st.metric("Debt-to-income ratio", f"{facts['debt_to_income']:.2f}")
        with rcol2:
            st.info(f"**Why:** {result.get('reason', 'N/A')}")

        # Gauge-style visual of the key ratio driving the decision
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=facts["debt_to_income"] * 100,
            title={"text": "Debt-to-Income (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "steps": [
                    {"range": [0, 30], "color": "#c8f7c5"},
                    {"range": [30, 55], "color": "#fff3b0"},
                    {"range": [55, 100], "color": "#f7c5c5"},
                ],
                "bar": {"color": "#333333"},
            },
        ))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enter applicant details above and click **Run Inference Engine** to get a decision.")

# ---------------------------------------------------------------------------
# TAB 2: Explainability Module
# ---------------------------------------------------------------------------
with tab_explain:
    st.subheader("Why did the system decide this?")
    if "last_trace" not in st.session_state:
        st.info("Run the inference engine on the first tab to see an explanation here.")
    else:
        trace = st.session_state["last_trace"]
        result = st.session_state["last_result"]

        st.markdown(
            f"**Plain-language summary:** Based on the applicant's credit score, income, "
            f"employment history, and debt load, the `{policy_name}` policy reached "
            f"**{result['decision']}** because: *{result.get('reason')}*."
        )

        st.markdown("#### Rule firing sequence (forward-chaining trace)")
        if trace:
            trace_df = pd.DataFrame([
                {
                    "Step": t["iteration"],
                    "Rule Fired": t["rule"],
                    "Condition Satisfied": t["explanation"],
                    "New Fact(s)": ", ".join(f"{k}={v}" for k, v in t["concluded"].items()),
                }
                for t in trace
            ])
            st.dataframe(trace_df, use_container_width=True, hide_index=True)

            # Visual: step-by-step flow of the reasoning chain
            fig = px.timeline(
                pd.DataFrame([
                    {"Rule": t["rule"], "Start": t["iteration"], "Finish": t["iteration"] + 1}
                    for t in trace
                ]),
                x_start="Start", x_end="Finish", y="Rule", color="Rule",
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(showlegend=False, height=300, xaxis_title="Inference step",
                               margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No intermediate rules fired before the default decision was applied.")

        st.markdown("#### Key factors used in this decision")
        facts = st.session_state["last_facts"]
        factor_df = pd.DataFrame({
            "Factor": ["Credit score", "Annual income", "Employment years", "Debt-to-income"],
            "Value": [facts["credit_score"], facts["annual_income"], facts["employment_years"], facts["debt_to_income"]],
        })
        st.bar_chart(factor_df.set_index("Factor"))

# ---------------------------------------------------------------------------
# TAB 3: Evaluation Module (metrics + comparison of two rule sets)
# ---------------------------------------------------------------------------
with tab_eval:
    st.subheader("Evaluate the rule sets against sample data")

    try:
        df = load_data(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Could not find {DATA_PATH}. Run generate_data.py first.")
        st.stop()

    st.markdown(f"Sample dataset: **{len(df)} applicants** with known outcomes (`ground_truth`).")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    if st.button("📈 Run evaluation & compare both policies"):
        metrics = {}
        for name, builder in RULE_SETS.items():
            metrics[name] = evaluate_rule_set(df, builder)

        st.markdown("#### Performance indicators")
        metric_df = pd.DataFrame({
            name: {
                "Accuracy": m["accuracy"],
                "Precision": m["precision"],
                "Recall": m["recall"],
                "Approval Rate": m["approval_rate"],
            }
            for name, m in metrics.items()
        }).T
        st.dataframe(metric_df.style.format("{:.2%}"), use_container_width=True)

        fig = go.Figure()
        for metric_name in ["Accuracy", "Precision", "Recall", "Approval Rate"]:
            fig.add_trace(go.Bar(name=metric_name, x=list(metrics.keys()),
                                  y=[metric_df.loc[p, metric_name] for p in metrics.keys()]))
        fig.update_layout(barmode="group", yaxis_tickformat=".0%",
                           title="Standard Policy vs Strict Policy", height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Confusion counts")
        for name, m in metrics.items():
            st.write(
                f"**{name}** — True Positives: {m['tp']}, False Positives: {m['fp']}, "
                f"True Negatives: {m['tn']}, False Negatives: {m['fn']}"
            )

        better = max(metrics, key=lambda n: metrics[n]["accuracy"])
        st.success(f"On this sample dataset, **{better}** achieves the higher accuracy.")
