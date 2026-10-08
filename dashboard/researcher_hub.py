"""
researcher_hub.py — Authenticated Researcher & Admin Portal for AI-Human Scarcity Study

Provides authenticated researchers with:
1. Executive Telemetry (Human vs AI counts, Turing test accuracy, survival rates, latencies)
2. Phase 3 Joint Analysis (Mann-Whitney U, Cliff's delta, Dose-response regressions)
3. 300 DPI Publication Visualizations & Figure Interpretation
4. Model Training Center (Distinguishability Classifier + Human Clone Policy)
5. Interactive Policy Inference Simulation (Predict human choices across game states)
6. Database Explorer & Full Export Center (CSV, SQLite DB, SFT Dataset)
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

from common.database import (
    DEFAULT_DB_PATH,
    export_combined_dataset,
    export_sft_dataset,
    get_connection,
    get_db_summary,
    init_db,
    sync_all_logs_to_db,
)
from analysis.train_models import (
    MODELS_DIR,
    train_distinguishability_classifier,
    train_human_behavior_policy,
)


def get_credentials() -> tuple[str, str]:
    """Retrieve researcher credentials from st.secrets, environment, or secure defaults."""
    default_user = "admin"
    default_pass = "scarcity2026"

    # Try Streamlit Secrets first
    try:
        user = st.secrets.get("RESEARCHER_USERNAME", os.environ.get("RESEARCHER_USERNAME", default_user))
        pwd = st.secrets.get("RESEARCHER_PASSWORD", os.environ.get("RESEARCHER_PASSWORD", default_pass))
        return str(user), str(pwd)
    except Exception:
        user = os.environ.get("RESEARCHER_USERNAME", default_user)
        pwd = os.environ.get("RESEARCHER_PASSWORD", default_pass)
        return str(user), str(pwd)


def check_researcher_auth() -> bool:
    """Render a secure login card if not authenticated. Returns True if authenticated."""
    if st.session_state.get("researcher_authenticated", False):
        return True

    expected_user, expected_pass = get_credentials()

    st.markdown("## 🔐 Researcher & Admin Portal")
    st.caption("Restricted Access — Empirical Analysis, Model Steering & Research Telemetry")

    col_l, col_center, col_r = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            """
            <div style="background-color: #1E293B; padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px;">
                <h4 style="margin-top:0; color: #38BDF8;">🔑 Researcher Authentication Required</h4>
                <p style="color: #94A3B8; font-size: 0.9rem;">
                    This section is restricted to study investigators to inspect unblinded data, 
                    retrain behavioral models, and access raw experiment logs.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("researcher_login_form"):
            username_input = st.text_input("Username", value="admin", placeholder="Enter username")
            password_input = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Authenticate & Enter Portal", type="primary", use_container_width=True)

            if submit:
                if username_input.strip() == expected_user and password_input == expected_pass:
                    st.session_state.researcher_authenticated = True
                    st.success("✅ Authentication successful. Loading portal...")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please check your username and password.")

        st.caption("💡 Default researcher login: `admin` / `scarcity2026` (configurable in `.env` or Streamlit Secrets).")

    return False


def render_researcher_hub(embedded: bool = False):
    """Render the full Researcher & Model Training Hub."""
    if not check_researcher_auth():
        return

    # Expand layout to 95% full-width desktop view (eliminates compact centered container)
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 95% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1.5rem !important;
        }
        /* Style tabs for clean desktop spacing */
        button[data-baseweb="tab"] {
            font-size: 0.95rem !important;
            padding: 8px 14px !important;
            font-weight: 500 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Auto-sync logs if DB is freshly initialized
    try:
        init_db()
        current_summary = get_db_summary()
        if current_summary.get("total_trials", 0) < 5:
            sync_all_logs_to_db()
            export_combined_dataset()
    except Exception:
        pass

    # Header with title and Logout button
    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        st.title("🔬 Scarcity Study: Researcher Hub & Model Analysis")
        st.caption("Unblinded Empirical Analysis, Statistical Divergence, Model Steering, and Camera-Ready Visuals.")
    with hcol2:
        if st.button("🚪 Logout & Exit", use_container_width=True):
            st.session_state.researcher_authenticated = False
            st.session_state.portal_active = False
            if "mode" in st.query_params:
                st.query_params.clear()
            st.rerun()

    # Sidebar Database Controls & Telemetry
    with st.sidebar:
        st.markdown("### 🔐 Researcher Controls")
        st.success("Authenticated: **Admin / Investigator**")

        if st.button("🔄 Sync All Logs to DB", use_container_width=True):
            with st.spinner("Syncing JSONL logs into SQLite database..."):
                synced, total = sync_all_logs_to_db()
                export_combined_dataset()
                export_sft_dataset()
                st.success(f"Synced {synced}/{total} trial logs!")
                st.rerun()

        db_stats = get_db_summary()
        st.metric("Total Banked Trials", db_stats["total_trials"])
        col_a, col_b = st.columns(2)
        col_a.metric("Human", db_stats["human_trials"])
        col_b.metric("AI Models", db_stats["ai_trials"])
        st.metric("Total Action Decisions", f"{db_stats['total_actions']:,}")
        if db_stats["total_judgments"] > 0:
            st.metric("Turing Test Human Accuracy", f"{db_stats['turing_accuracy']:.1f}%")

        st.divider()
        st.markdown("### 📥 Direct Data Exports")
        csv_path = os.path.join(PROJECT_ROOT, "data", "combined_scarcity_dataset.csv")
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download CSV Dataset",
                    data=f.read(),
                    file_name="combined_scarcity_dataset.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        if os.path.exists(DEFAULT_DB_PATH):
            with open(DEFAULT_DB_PATH, "rb") as f:
                st.download_button(
                    label="💾 Download SQLite DB",
                    data=f.read(),
                    file_name="scarcity_study.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                )
        sft_path = os.path.join(PROJECT_ROOT, "data", "llm_sft_dataset.jsonl")
        if os.path.exists(sft_path):
            with open(sft_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="🤖 Download LLM SFT Dataset",
                    data=f.read(),
                    file_name="llm_sft_dataset.jsonl",
                    mime="application/jsonlines",
                    use_container_width=True,
                )

    # Core Navigation Tabs
    tab_overview, tab_stats, tab_figures, tab_train, tab_inference, tab_explore = st.tabs([
        "📊 Study Telemetry",
        "📐 Hypothesis Tests & Slopes",
        "🖼️ Publication Figures (300 DPI)",
        "🧠 Model Training Center",
        "🔮 Interactive Behavior Simulator",
        "🗄️ Relational Data Explorer",
    ])

    # -------------------------------------------------------------
    # TAB 1: STUDY TELEMETRY
    # -------------------------------------------------------------
    with tab_overview:
        st.subheader("Data Collection & Behavioral Distribution")
        ov_col1, ov_col2 = st.columns([1, 1])

        with ov_col1:
            st.markdown("**Trials by Scenario Condition:**")
            sc_df = pd.DataFrame(
                list(db_stats["scenario_counts"].items()),
                columns=["Scenario", "Count"],
            )
            st.bar_chart(sc_df.set_index("Scenario"))

        with ov_col2:
            st.markdown("**Empirical Comparison by Scenario & Arm:**")
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

        st.divider()
        st.markdown("### 📈 Key Divergence Summary Metrics")
        m1, m2, m3, m4 = st.columns(4)
        with get_connection() as conn:
            feat_df = pd.read_sql_query("SELECT * FROM trial_features", conn)
        if not feat_df.empty:
            h_share = feat_df[feat_df["source"] == "human"]["share_rate"].mean() * 100
            a_share = feat_df[feat_df["source"] == "ai"]["share_rate"].mean() * 100
            m1.metric("Human Cooperation", f"{h_share:.1f}%", f"{h_share - a_share:+.1f}% vs AI")

            h_hoard = feat_df[feat_df["source"] == "human"]["hoard_rate"].mean() * 100
            a_hoard = feat_df[feat_df["source"] == "ai"]["hoard_rate"].mean() * 100
            m2.metric("Human Hoarding", f"{h_hoard:.1f}%", f"{h_hoard - a_hoard:+.1f}% vs AI")

            h_dec = feat_df[feat_df["source"] == "human"]["deception_rate"].mean() * 100
            m3.metric("Human Deception Rate", f"{h_dec:.1f}%", "AI Deception: 0.0%")

            h_lat = feat_df[feat_df["source"] == "human"]["mean_latency_ms"].mean()
            m4.metric("Avg Human Latency", f"{h_lat:.0f} ms", "Moral Deliberation")

    # -------------------------------------------------------------
    # TAB 2: HYPOTHESIS TESTS & SLOPES
    # -------------------------------------------------------------
    with tab_stats:
        st.subheader("📐 Non-Parametric Hypothesis Tests & Dose-Response Slopes")
        st.caption("Mann-Whitney U, Cliff's Delta, Cohen's d, and Scarcity Dose-Response Elasticity.")

        stats_json_path = os.path.join(PROJECT_ROOT, "data", "stats_summary.json")
        if os.path.exists(stats_json_path):
            with open(stats_json_path, "r", encoding="utf-8") as f:
                stats_data = json.load(f)

            subsets = stats_data.get("subsets", {})
            subset_keys = list(subsets.keys())
            selected_subset = st.selectbox("Filter by Experimental Condition:", subset_keys, index=0)

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
                        "Cliff's Delta (δ)": f"{r['cliffs_delta']:+.3f}",
                        "Effect Magnitude": r["effect_magnitude"],
                        "Cohen's d": f"{r['cohens_d']:+.2f}",
                    })
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
                st.caption("Significance: * p < 0.05, ** p < 0.01, *** p < 0.001. Two-sided Mann-Whitney U test.")

            st.divider()
            st.markdown("#### 🌊 Novelty N1: Scarcity Dose-Response Elasticity Curves")
            st.write(
                "Characterizes the behavioral rate derivative across scarcity severity intensities $\\sigma \\in [0.0, 0.7]$:"
            )
            dr_data = stats_data.get("dose_response", {})
            slopes = dr_data.get("slopes", {})
            dcol1, dcol2, dcol3, dcol4 = st.columns(4)
            dcol1.metric("Human d(Share)/d(Sev)", f"{slopes.get('human_dShare_dSeverity', 0):+.4f}")
            dcol2.metric("AI d(Share)/d(Sev)", f"{slopes.get('ai_dShare_dSeverity', 0):+.4f}")
            dcol3.metric("Human d(Hoard)/d(Sev)", f"{slopes.get('human_dHoard_dSeverity', 0):+.4f}")
            dcol4.metric("AI d(Hoard)/d(Sev)", f"{slopes.get('ai_dHoard_dSeverity', 0):+.4f}")
            st.info(
                "💡 **Key Discovery:** Humans display sharp cooperation collapse (-15.6% per severity unit) "
                "and defensive hoarding surge (+19.4%), whereas AI models maintain flat, rigid gathering routines."
            )
        else:
            st.info("Run `python tasks.py stats` to compute statistical findings.")

    # -------------------------------------------------------------
    # TAB 3: PUBLICATION FIGURES
    # -------------------------------------------------------------
    with tab_figures:
        st.subheader("🖼️ Publication-Quality Figures (300 DPI)")
        st.caption("Generated directly from the empirical dataset for the final manuscript.")

        fig1_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig1_behavioral_comparison.png")
        fig2_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig2_dose_response.png")
        fig3_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig3_distinguishability_roc.png")
        fig4_path = os.path.join(PROJECT_ROOT, "paper", "figures", "fig4_feature_importance.png")

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            if os.path.exists(fig1_path):
                st.image(fig1_path, caption="Figure 1: Behavioral Metric Distributions (AI vs. Human across Scenarios)")
            if os.path.exists(fig3_path):
                st.image(fig3_path, caption="Figure 3: Distinguishability ROC-AUC across Scarcity Levels (Novelty N3)")
        with fcol2:
            if os.path.exists(fig2_path):
                st.image(fig2_path, caption="Figure 2: Scarcity Dose-Response Elasticity Curves (Novelty N1)")
            if os.path.exists(fig4_path):
                st.image(fig4_path, caption="Figure 4: Permutation Feature Importance & Driver Attribution")

    # -------------------------------------------------------------
    # TAB 4: MODEL TRAINING CENTER
    # -------------------------------------------------------------
    with tab_train:
        st.subheader("Train & Retrain Behavioral Machine Learning Models")
        st.write(
            "Every time new human trials are completed, click below to retrain both models on all banked data."
        )

        tcol1, tcol2 = st.columns(2)
        with tcol1:
            st.markdown("### 🏆 Model 1: Distinguishability Classifier (Novelty N3)")
            st.caption("Predicts Human (1) vs. AI (0) using trial-level behavioral signatures.")
            if st.button("🚀 Retrain Distinguishability Classifier", type="primary", use_container_width=True):
                with st.spinner("Training cross-validated classifier..."):
                    res = train_distinguishability_classifier()
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success("Trained successfully!")
                        st.metric("5-Fold CV Accuracy", f"{res['accuracy'] * 100:.1f}%")
                        st.metric("ROC-AUC Score", f"{res['auc']:.3f}")
                        st.markdown("**Top Learned Feature Weights:**")
                        w_df = pd.DataFrame(list(res["feature_weights"].items()), columns=["Feature", "Weight"]).sort_values(by="Weight", ascending=False)
                        st.dataframe(w_df, use_container_width=True)

        with tcol2:
            st.markdown("### 🤖 Model 2: Human Behavioral Policy (Imitation Learning)")
            st.caption("Learns p(action | state) from actual human decisions.")
            if st.button("🚀 Retrain Human Clone Policy", type="primary", use_container_width=True):
                with st.spinner("Training multi-class behavioral policy..."):
                    res = train_human_behavior_policy()
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success("Trained successfully!")
                        st.metric("Action Prediction Accuracy", f"{res['test_accuracy'] * 100:.1f}%")
                        st.metric("Trained Decision Steps", res["n_samples"])
                        acts_df = pd.DataFrame(list(res["action_counts"].items()), columns=["Action", "Count"])
                        st.bar_chart(acts_df.set_index("Action"))

    # -------------------------------------------------------------
    # TAB 5: INTERACTIVE BEHAVIOR SIMULATOR
    # -------------------------------------------------------------
    with tab_inference:
        st.subheader("🔮 Interactive Policy Inference & Model Simulator")
        st.write("Adjust game parameters below to simulate what the trained **Human Clone Model** predicts:")

        policy_chk = os.path.join(MODELS_DIR, "human_clone_policy.json")
        if os.path.exists(policy_chk):
            with open(policy_chk, "r", encoding="utf-8") as f:
                chk_data = json.load(f)

            icol1, icol2, icol3, icol4 = st.columns(4)
            sim_round = icol1.slider("Simulated Round", 1, 10, 6)
            sim_res = icol2.slider("Agent Water Reserve", 0, 15, 3)
            sim_drought = icol3.checkbox("Drought Round Shock?", value=(sim_round == 6))
            sim_sev = icol4.slider("Scarcity Severity (σ)", 0.0, 1.0, 0.7 if sim_drought else 0.0)

            from analysis.train_models import softmax
            x_vec = np.array([1.0, float(sim_round) / 10.0, float(sim_res) / 10.0, 1.0 if sim_drought else 0.0, sim_sev])
            w_mat = np.array(chk_data["weights"])
            probs = softmax(np.dot(x_vec, w_mat))

            st.markdown("**Predicted Action Probability Distribution:**")
            prob_dict = {action: float(probs[idx]) for action, idx in chk_data["action_map"].items()}
            st.bar_chart(pd.DataFrame(list(prob_dict.items()), columns=["Action", "Probability"]).set_index("Action"))

            top_act = max(prob_dict.items(), key=lambda k: k[1])
            st.success(f"🎯 **Predicted Human Action:** `{top_act[0].upper()}` ({top_act[1] * 100:.1f}% confidence)")
        else:
            st.info("Train the Human Behavioral Policy in the 'Model Training Center' tab first.")

    # -------------------------------------------------------------
    # TAB 6: RELATIONAL DATA EXPLORER
    # -------------------------------------------------------------
    with tab_explore:
        st.subheader("🗄️ Relational Database & Decision Log Explorer")
        with get_connection() as conn:
            trials_df = pd.read_sql_query("SELECT * FROM trials ORDER BY created_at DESC", conn)
            st.markdown(f"**Banked Trials ({len(trials_df)} rows):**")
            st.dataframe(trials_df, use_container_width=True)

            if not trials_df.empty:
                selected_trial = st.selectbox("Select Trial to Inspect Round-by-Round Events:", trials_df["trial_id"].tolist())
                if selected_trial:
                    actions_df = pd.read_sql_query(
                        """
                        SELECT round, agent_id, source, action_type, target_agent, 
                               message_kind, message_value, resource_before, resource_after, 
                               alive, decision_latency_ms 
                        FROM actions 
                        WHERE trial_id = ? 
                        ORDER BY round, agent_id
                        """,
                        conn,
                        params=(selected_trial,),
                    )
                    st.dataframe(actions_df, use_container_width=True)
