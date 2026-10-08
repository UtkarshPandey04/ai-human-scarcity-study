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
import numpy as np
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
tab_overview, tab_joint, tab_train, tab_explore, tab_inference = st.tabs([
    "📊 Study Overview",
    "📈 Joint Analysis (Phase 3)",
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
# TAB 2: JOINT ANALYSIS (PHASE 3 RESULTS)
# -------------------------------------------------------------
with tab_joint:
    st.subheader("🔬 Phase 3: Joint Analysis & Behavioral Divergence Findings")
    st.caption("Empirical statistical hypothesis testing, Scarcity Dose-Response Elasticity, and Distinguishability Modeling.")

    # Action button to trigger pipeline
    ja_col1, ja_col2 = st.columns([1, 3])
    with ja_col1:
        if st.button("⚡ Re-run Full Joint Analysis", type="primary", use_container_width=True):
            with st.spinner("Executing Feature Extraction, Mann-Whitney U, Classifier, and Figures..."):
                import subprocess
                subprocess.call([sys.executable, "tasks.py", "joint_analysis"])
                st.success("Joint Analysis completed and figures updated!")
                st.rerun()

    stats_json_path = os.path.join(PROJECT_ROOT, "data", "stats_summary.json")
    classifier_json_path = os.path.join(PROJECT_ROOT, "models", "distinguishability_classifier.json")
    qual_json_path = os.path.join(PROJECT_ROOT, "data", "qualitative_excerpts.json")

    # 1. Statistical Hypothesis Testing Sub-Section
    st.markdown("### 📊 1. Non-Parametric Hypothesis Testing (Mann-Whitney U)")
    if os.path.exists(stats_json_path):
        with open(stats_json_path, "r", encoding="utf-8") as f:
            stats_data = json.load(f)

        subsets = stats_data.get("subsets", {})
        subset_keys = list(subsets.keys())
        selected_subset = st.selectbox("Select Scenario Subset:", subset_keys, index=0)

        if selected_subset in subsets:
            rows = subsets[selected_subset]
            table_rows = []
            for r in rows:
                table_rows.append({
                    "Metric": r["metric_label"],
                    "Human Mean (SD)": f"{r['human_mean']:.3f} (±{r['human_std']:.2f})",
                    "AI Mean (SD)": f"{r['ai_mean']:.3f} (±{r['ai_std']:.2f})",
                    "Mann-Whitney U": f"{r['u_stat']:.1f}",
                    "p-value": f"{r['p_value']:.4f} {r['stars']}",
                    "Cliff's Delta": f"{r['cliffs_delta']:+.3f}",
                    "Effect Size": r["effect_magnitude"],
                    "Cohen's d": f"{r['cohens_d']:+.2f}",
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
            st.caption("Significance flags: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.")

        # Dose Response summary
        dr_data = stats_data.get("dose_response", {})
        slopes = dr_data.get("slopes", {})
        st.markdown("#### 📈 Novelty N1: Scarcity Dose-Response Elasticity")
        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
        dcol1.metric("Human d(Share)/d(Sev)", f"{slopes.get('human_dShare_dSeverity', 0):+.4f}")
        dcol2.metric("AI d(Share)/d(Sev)", f"{slopes.get('ai_dShare_dSeverity', 0):+.4f}")
        dcol3.metric("Human d(Hoard)/d(Sev)", f"{slopes.get('human_dHoard_dSeverity', 0):+.4f}")
        dcol4.metric("AI d(Hoard)/d(Sev)", f"{slopes.get('ai_dHoard_dSeverity', 0):+.4f}")
    else:
        st.info("Run `python tasks.py stats` or click the button above to generate statistical findings.")

    st.divider()

    # 2. Classifier & Novelty N3 Sub-Section
    st.markdown("### 🏆 2. Distinguishability Classifier & Novelty N3 Findings")
    if os.path.exists(classifier_json_path):
        with open(classifier_json_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)

        ccol1, ccol2 = st.columns(2)
        with ccol1:
            lr_res = c_data.get("overall_logistic", {})
            st.markdown("**Logistic Regression (L2 Regularized):**")
            st.metric("5-Fold CV Accuracy", f"{lr_res.get('accuracy', 0)*100:.1f}%")
            st.metric("ROC-AUC Score", f"{lr_res.get('roc_auc', 0):.3f}")
            st.metric("F1-Score", f"{lr_res.get('f1_score', 0):.3f}")

        with ccol2:
            rf_res = c_data.get("overall_rf", {})
            st.markdown("**Random Forest Classifier (Ensemble):**")
            st.metric("5-Fold CV Accuracy", f"{rf_res.get('accuracy', 0)*100:.1f}%")
            st.metric("ROC-AUC Score", f"{rf_res.get('roc_auc', 0):.3f}")
            st.metric("F1-Score", f"{rf_res.get('f1_score', 0):.3f}")

        # Distinguishability Across Scarcity
        st.markdown("#### 🔬 Distinguishability Across Scarcity Conditions (Novelty N3):")
        sc_dose = c_data.get("scarcity_dose_response", {})
        sc_table = []
        for s_name, s_res in sc_dose.items():
            sc_table.append({
                "Condition": s_name,
                "Logistic Regression AUC": f"{s_res['logistic_regression'].get('roc_auc', 0):.3f}",
                "Logistic Accuracy": f"{s_res['logistic_regression'].get('accuracy', 0)*100:.1f}%",
                "Random Forest AUC": f"{s_res['random_forest'].get('roc_auc', 0):.3f}",
                "Random Forest Accuracy": f"{s_res['random_forest'].get('accuracy', 0)*100:.1f}%",
            })
        st.dataframe(pd.DataFrame(sc_table), use_container_width=True)

    st.divider()

    # 3. Publication Figures Showcase
    st.markdown("### 🖼️ 3. Camera-Ready Academic Figures (300 DPI)")
    fig_col1, fig_col2 = st.columns(2)

    fig1_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig1_behavioral_comparison.png")
    fig2_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig2_dose_response.png")
    fig3_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig3_distinguishability_roc.png")
    fig4_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig4_feature_importance.png")

    with fig_col1:
        if os.path.exists(fig1_path):
            st.image(fig1_path, caption="Figure 1: Behavioral Metric Distributions (AI vs. Human across Scenarios)")
        if os.path.exists(fig3_path):
            st.image(fig3_path, caption="Figure 3: Distinguishability ROC-AUC across Scarcity Levels (Novelty N3)")

    with fig_col2:
        if os.path.exists(fig2_path):
            st.image(fig2_path, caption="Figure 2: Scarcity Dose-Response Elasticity Curves (Novelty N1)")
        if os.path.exists(fig4_path):
            st.image(fig4_path, caption="Figure 4: Feature Importance & Driver Attribution")

    st.divider()

    # 4. Qualitative Behavioral Excerpts Viewer
    st.markdown("### 📝 4. Qualitative Excerpt Explorer")
    st.caption("Inspect verifiable arithmetic deception cases, moral appeals, and altruistic sacrifice.")
    if os.path.exists(qual_json_path):
        with open(qual_json_path, "r", encoding="utf-8") as f:
            excerpts_list = json.load(f)

        for idx, ex in enumerate(excerpts_list[:6], 1):
            with st.expander(f"Excerpt {idx}: {ex['category']} — {ex['trial_id']} (Round {ex['round']})"):
                st.write(f"**Agent:** `{ex['agent_id']}` ({ex['source'].upper()}) | **Action:** `{ex['action_type'].upper()}`")
                if ex.get("latency_ms") and ex["latency_ms"] > 0:
                    st.write(f"**Decision Latency:** `{ex['latency_ms']:,} ms`")
                if ex.get("claimed_value") is not None:
                    st.error(f"🚨 Arithmetic Deception: Claimed Stock = {ex['claimed_value']} vs. True Resource = {ex['true_resource_before']:.1f}")
                st.info(f"💡 Commentary: {ex['commentary']}")

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
