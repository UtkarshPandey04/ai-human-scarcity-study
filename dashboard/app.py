"""
dashboard/app.py — Interactive Researcher & Model Training Dashboard

Provides researchers with a visual control center to:
1. Explore the SQLite trial database (trials, actions, behavioral features)
2. Train Machine Learning models (Distinguishability Classifier + Human Behavioral Policy) with one click
3. Inspect model weights, accuracy curves, and feature importance
4. Test interactive model inference: simulate what action the trained human model predicts for any game state
5. Monitor human participant data collection and Turing test accuracy

Run locally with:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import os
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.database import DEFAULT_DB_PATH, get_connection, get_db_summary, init_db, sync_all_logs_to_db
from analysis.train_models import (
    MODELS_DIR,
    train_distinguishability_classifier,
    train_human_behavior_policy,
)

st.set_page_config(
    page_title="Scarcity Study — Researcher Dashboard & Model Hub",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Scarcity Study: Researcher Hub & Model Training")
st.caption("Manage trials database, train behavioral models, and inspect AI-vs-human divergence.")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Database Controls")
    if st.button("🔄 Sync Logs to Database", use_container_width=True):
        synced, total = sync_all_logs_to_db()
        st.success(f"Synced {synced}/{total} trial logs!")

    db_stats = get_db_summary()
    st.metric("Total Trials", db_stats["total_trials"])
    col_a, col_b = st.columns(2)
    col_a.metric("Human Trials", db_stats["human_trials"])
    col_b.metric("AI Trials", db_stats["ai_trials"])
    st.metric("Total Action Events", f"{db_stats['total_actions']:,}")
    if db_stats["total_judgments"] > 0:
        st.metric("Turing Test Accuracy", f"{db_stats['turing_accuracy']:.1f}%")

    st.divider()
    st.caption(f"Database Path:\n`{DEFAULT_DB_PATH}`")

# Tabs
tab_overview, tab_train, tab_explore, tab_inference = st.tabs([
    "📊 Study Overview",
    "🧠 Model Training Center",
    "🗄️ Database Explorer",
    "🔮 Model Inference & Testing",
])

# -------------------------------------------------------------
# TAB 1: OVERVIEW
# -------------------------------------------------------------
with tab_overview:
    st.subheader("Data Collection & Scenario Distribution")
    ov_col1, ov_col2 = st.columns([1, 1])

    with ov_col1:
        st.markdown("**Trials by Scenario:**")
        sc_df = pd.DataFrame(
            list(db_stats["scenario_counts"].items()),
            columns=["Scenario", "Count"],
        )
        st.bar_chart(sc_df.set_index("Scenario"))

    with ov_col2:
        st.markdown("**Key Behavioral Summary:**")
        with get_connection() as conn:
            query = """
            SELECT source, scenario,
                   COUNT(*) as n_trials,
                   ROUND(AVG(survived) * 100, 1) as survival_rate,
                   ROUND(AVG(gather_rate) * 100, 1) as avg_gather_pct,
                   ROUND(AVG(share_rate) * 100, 1) as avg_share_pct,
                   ROUND(AVG(hoard_rate) * 100, 1) as avg_hoard_pct,
                   ROUND(AVG(deception_rate) * 100, 1) as avg_deception_pct,
                   ROUND(AVG(society_gini), 2) as avg_gini
            FROM trial_features
            GROUP BY source, scenario
            """
            summary_df = pd.read_sql_query(query, conn)
        st.dataframe(summary_df, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: MODEL TRAINING CENTER
# -------------------------------------------------------------
with tab_train:
    st.subheader("Train Machine Learning Models on Collected Data")
    st.write(
        """
        Train your models directly on the active SQLite database. Every time you collect new
        human sessions, re-run training here to update your model checkpoints.
        """
    )

    tcol1, tcol2 = st.columns(2)

    with tcol1:
        st.markdown("### 🏆 Model 1: Distinguishability Classifier (Novelty N3)")
        st.caption("Predicts Human (1) vs. AI (0) using trial-level behavioral signatures.")

        if st.button("🚀 Train Distinguishability Classifier", type="primary", use_container_width=True):
            with st.spinner("Training cross-validated classifier..."):
                res = train_distinguishability_classifier()
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("Trained successfully!")
                    st.metric("Cross-Validation Accuracy", f"{res['accuracy'] * 100:.1f}%")
                    st.metric("ROC-AUC Score", f"{res['auc']:.3f}")

                    st.markdown("**Learned Behavioral Signatures:**")
                    weights_df = pd.DataFrame(
                        list(res["feature_weights"].items()),
                        columns=["Feature", "Weight"],
                    ).sort_values(by="Weight", ascending=False)
                    st.dataframe(weights_df, use_container_width=True)
                    st.caption(f"Saved checkpoint: `{res['checkpoint_path']}`")

    with tcol2:
        st.markdown("### 🤖 Model 2: Human Behavioral Policy (Imitation Learning)")
        st.caption("Learns p(action | state) from raw human action choices.")

        if st.button("🚀 Train Human Behavioral Policy", type="primary", use_container_width=True):
            with st.spinner("Training multi-class behavioral policy..."):
                res = train_human_behavior_policy()
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success("Trained successfully!")
                    st.metric("Action Prediction Accuracy", f"{res['test_accuracy'] * 100:.1f}%")
                    st.metric("Total Human Decisions", res["n_samples"])

                    st.markdown("**Action Prior Distribution:**")
                    acts_df = pd.DataFrame(
                        list(res["action_counts"].items()),
                        columns=["Action", "Count"],
                    )
                    st.bar_chart(acts_df.set_index("Action"))
                    st.caption(f"Saved checkpoint: `{res['checkpoint_path']}`")

# -------------------------------------------------------------
# TAB 3: DATABASE EXPLORER
# -------------------------------------------------------------
with tab_explore:
    st.subheader("Query Trials and Action Events")
    with get_connection() as conn:
        trials_df = pd.read_sql_query("SELECT * FROM trials ORDER BY created_at DESC", conn)
        st.markdown(f"**Trials Table ({len(trials_df)} rows):**")
        st.dataframe(trials_df, use_container_width=True)

        if not trials_df.empty:
            selected_trial = st.selectbox("Select a trial to view its round-by-round events:", trials_df["trial_id"].tolist())
            if selected_trial:
                actions_df = pd.read_sql_query(
                    "SELECT round, agent_id, source, action_type, target_agent, message_kind, message_value, resource_before, resource_after, alive, decision_latency_ms FROM actions WHERE trial_id = ? ORDER BY round, agent_id",
                    conn,
                    params=(selected_trial,),
                )
                st.dataframe(actions_df, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: INTERACTIVE INFERENCE
# -------------------------------------------------------------
with tab_inference:
    st.subheader("🔮 Interactive Policy Inference")
    st.write("Simulate what the trained **Human Clone Model** would do in a given state:")

    policy_chk = os.path.join(MODELS_DIR, "human_clone_policy.json")
    if os.path.exists(policy_chk):
        with open(policy_chk, "r", encoding="utf-8") as f:
            chk_data = json.load(f)

        icol1, icol2, icol3, icol4 = st.columns(4)
        sim_round = icol1.slider("Round", 1, 10, 6)
        sim_res = icol2.slider("Current Water", 0, 15, 3)
        sim_drought = icol3.checkbox("Is Drought Round?", value=(sim_round == 6))
        sim_sev = icol4.slider("Scarcity Severity", 0.0, 1.0, 0.7 if sim_drought else 0.0)

        # Compute softmax
        from analysis.train_models import softmax
        x_vec = np.array([1.0, float(sim_round) / 10.0, float(sim_res) / 10.0, 1.0 if sim_drought else 0.0, sim_sev])
        w_mat = np.array(chk_data["weights"])
        probs = softmax(np.dot(x_vec, w_mat))

        st.markdown("**Action Probabilities Predicted by Human Model:**")
        prob_dict = {action: float(probs[idx]) for action, idx in chk_data["action_map"].items()}
        st.bar_chart(pd.DataFrame(list(prob_dict.items()), columns=["Action", "Probability"]).set_index("Action"))

        top_act = max(prob_dict.items(), key=lambda k: k[1])
        st.success(f"🎯 **Predicted Action:** `{top_act[0].upper()}` ({top_act[1] * 100:.1f}% confidence)")
    else:
        st.info("Train the Human Behavioral Policy in the 'Model Training Center' tab first.")
