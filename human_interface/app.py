"""
app.py — Group 1 (Sujal & Utkarsh)

Streamlit interface for the human side of the AI-Human Scarcity Study.
Flow: consent -> instructions -> game (multiple rounds with focal-player substitution) -> debrief

Architecture:
- Matched-protocol design: 5 players on the island (1 focal human participant + 4 co-players
  running deterministic policies from agents/coplayers.py).
- Shared logistic pool (agents/environment.ScarcityEnv): real commons depletion and tragedy dynamics.
- Slotted communication: machine-verifiable deception arithmetic.
- Full trial logging compliant with LOGGING_SCHEMA.md and common/schema.py.
- Novelties: Decision latency logging, Scarcity severity sweep, Behavioral Turing Test debrief module.

Run locally with:  streamlit run human_interface/app.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
import streamlit as st

# Ensure project root is on sys.path so common and agent modules can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.actions import Action, ActionType, Message, MessageKind
from common.config import (
    DROUGHT_ROUND,
    MATCHED_SEEDS,
    NUM_PLAYERS,
    SCENARIOS,
    START_WATER,
    SURVIVAL_COST,
    TOTAL_ROUNDS,
    gather_yield,
    is_alive,
    is_drought,
)
from agents.coplayers import get_policy
from agents.environment import ScarcityEnv
from human_interface.logging_utils import (
    LOG_DIR,
    log_round_records,
    load_trial_log,
    validate_trial_log,
)
from human_interface.session_analysis import (
    action_rates,
    calculate_deception,
    calculate_gini,
    calculate_latency_stats,
    count_actions,
    get_drought_action,
    resource_change,
)

# ---------- CONSTANTS & CO-PLAYERS CONFIG ----------
COPLAYER_IDS = [f"A{i}" for i in range(2, NUM_PLAYERS + 1)]
COPLAYER_POLICIES = ["cooperator", "free_rider", "tit_for_tat", "random"]
ACTIONS = [
    ActionType.GATHER.value,
    ActionType.SHARE.value,
    ActionType.HOARD.value,
    ActionType.SKIP.value,
    ActionType.COMMUNICATE.value,
]
MESSAGE_KINDS = [m.value for m in MessageKind]

st.set_page_config(
    page_title="AI-Human Scarcity Study",
    page_icon="🏝️",
    layout="centered",
)

# Hide Streamlit top-right menu, toolbar, and GitHub repo badge from participants
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    .viewerBadge_link__qRIco {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    button[title="View app source"] {display: none !important;}
    a[href*="github.com"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- RESEARCHER CONTROLS & QUERY PARAMS ----------
query_params = st.query_params
default_scenario = query_params.get("scenario", "drought")
if default_scenario not in SCENARIOS:
    default_scenario = "drought"

try:
    default_seed = int(query_params.get("seed", 0))
    if default_seed not in MATCHED_SEEDS:
        default_seed = 0
except (ValueError, TypeError):
    default_seed = 0

# ---------- SESSION STATE INIT ----------
if "stage" not in st.session_state:
    st.session_state.stage = "consent"

if "scenario" not in st.session_state:
    st.session_state.scenario = default_scenario

if "seed" not in st.session_state:
    st.session_state.seed = default_seed

if "severity" not in st.session_state:
    st.session_state.severity = 0.7 if st.session_state.scenario == "drought" else 0.0

if "participant_id" not in st.session_state:
    st.session_state.participant_id = f"P{uuid.uuid4().hex[:4].upper()}"

if "demographics" not in st.session_state:
    st.session_state.demographics = {}

if "trial_synced_to_db" not in st.session_state:
    st.session_state.trial_synced_to_db = False

if "trial_id" not in st.session_state:
    st.session_state.trial_id = f"{st.session_state.scenario}_human_{st.session_state.seed:03d}_{uuid.uuid4().hex[:6]}"

if "coplayer_mode" not in st.session_state:
    st.session_state.coplayer_mode = "Standard"

if "action_log" not in st.session_state:
    st.session_state.action_log = []

if "all_trial_rows" not in st.session_state:
    st.session_state.all_trial_rows = []

if "round_start_time" not in st.session_state:
    st.session_state.round_start_time = time.time()

if "round_transition_active" not in st.session_state:
    st.session_state.round_transition_active = False

if "round_transition_data" not in st.session_state:
    st.session_state.round_transition_data = {}

if "last_round_events" not in st.session_state:
    st.session_state.last_round_events = []

if "turing_guess" not in st.session_state:
    st.session_state.turing_guess = None

if "turing_submitted" not in st.session_state:
    st.session_state.turing_submitted = False


def get_active_coplayer_policies() -> list[str]:
    if st.session_state.get("coplayer_mode") == "Deceptive (Strategic Deceiver)":
        return ["cooperator", "free_rider", "tit_for_tat", "deceiver"]
    if st.session_state.get("coplayer_mode") == "Live LLM Ecology (Groq + Gemini)":
        return ["llm_groq", "llm_gemini", "tit_for_tat", "llm_auto"]
    return COPLAYER_POLICIES


def reset_environment():
    """Instantiate ScarcityEnv with focal-player substitution and co-players."""
    focal_id = st.session_state.participant_id
    player_ids = [focal_id] + COPLAYER_IDS
    env = ScarcityEnv(
        scenario=st.session_state.scenario,
        seed=st.session_state.seed,
        player_ids=player_ids,
    )
    # Instantiate co-player policies with matched deterministic seeds
    active_policies = get_active_coplayer_policies()
    coplayers = {
        pid: get_policy(active_policies[i], seed=st.session_state.seed + i + 1)
        for i, pid in enumerate(COPLAYER_IDS)
    }
    obs = env.reset()
    st.session_state.env = env
    st.session_state.coplayers = coplayers
    st.session_state.current_obs = obs
    st.session_state.action_log = []
    st.session_state.all_trial_rows = []
    st.session_state.last_round_events = []
    st.session_state.round_transition_active = False
    st.session_state.round_transition_data = {}
    st.session_state.round_start_time = time.time()
    st.session_state.trial_synced_to_db = False


def go_to(stage: str):
    st.session_state.stage = stage
    st.rerun()


# ---------- SIDEBAR: STUDY CONFIG (Editable prior to game start) ----------
with st.sidebar:
    st.header("⚙️ Island Setup")
    if st.session_state.stage in ("consent", "instructions"):
        selected_scenario = st.selectbox(
            "Game Scenario",
            options=list(SCENARIOS),
            index=list(SCENARIOS).index(st.session_state.scenario),
            format_func=lambda s: {
                "calm": "☀️ Normal Island (10 Rounds - Stable Rain)",
                "drought": "⚠️ Drought Crisis (10 Rounds - Heatwave in Round 6)",
                "repeated_trust": "🤝 Extended Society (30 Rounds - Long-Term Trust)",
            }.get(s, s),
            help="Choose the island condition: normal weather, severe drought heatwave, or long-term 30-round community.",
        )
        selected_seed = st.selectbox(
            "Island Map # (Layout)",
            options=list(MATCHED_SEEDS),
            index=st.session_state.seed,
            help="Preset island scenario map (0-29). Matched directly against AI computer runs.",
        )
        severity_val = st.slider(
            "Drought Hardship Level",
            min_value=0.0,
            max_value=1.0,
            value=0.7 if selected_scenario == "drought" else 0.0,
            step=0.1,
            help="Sets how severe the water scarcity gets during drought (0.0 = Mild, 1.0 = Extreme Scarcity).",
        )
        ecology_opts = ["Standard", "Deceptive (Strategic Deceiver)", "Live LLM Ecology (Groq + Gemini)"]
        default_eco_idx = ecology_opts.index(st.session_state.coplayer_mode) if st.session_state.coplayer_mode in ecology_opts else 0
        coplayer_opt = st.selectbox(
            "Teammate Personalities",
            options=ecology_opts,
            index=default_eco_idx,
            format_func=lambda e: {
                "Standard": "Standard Teammates (Cooperative, Selfish & Fair bots)",
                "Deceptive (Strategic Deceiver)": "Challenging Island (Includes Sneaky/Secretive bot)",
                "Live LLM Ecology (Groq + Gemini)": "Smart AI Island (Live AI bots with Groq & Gemini)",
            }.get(e, e),
            help="Standard: Balanced mix of bots. Deceptive: Adds a secretive player. Live LLM: Smart bots powered by live AI reasoning.",
        )
        if (
            selected_scenario != st.session_state.scenario
            or selected_seed != st.session_state.seed
            or severity_val != st.session_state.severity
            or coplayer_opt != st.session_state.coplayer_mode
        ):
            st.session_state.scenario = selected_scenario
            st.session_state.seed = selected_seed
            st.session_state.severity = severity_val
            st.session_state.coplayer_mode = coplayer_opt
            st.session_state.trial_id = f"{selected_scenario}_human_{selected_seed:03d}_{uuid.uuid4().hex[:6]}"
            st.rerun()
    else:
        scenario_labels = {
            "calm": "☀️ Normal Island (10 Rounds)",
            "drought": "⚠️ Drought Crisis (10 Rounds)",
            "repeated_trust": "🤝 Extended Society (30 Rounds)",
        }
        st.write(f"**Scenario:** {scenario_labels.get(st.session_state.scenario, st.session_state.scenario)}")
        st.write(f"**Island Map #:** `{st.session_state.seed}`")
        st.write(f"**Drought Hardship:** `{st.session_state.severity}`")
        st.write(f"**Teammate Mix:** `{st.session_state.coplayer_mode}`")

    st.divider()
    st.markdown(f"👤 **Participant ID:** `{st.session_state.participant_id}`")
    st.caption(f"Trial ID: `{st.session_state.trial_id}`")

    with st.expander("📥 Researcher Data Export", expanded=False):
        from common.database import DEFAULT_DB_PATH, export_combined_dataset, export_sft_dataset, get_db_summary, sync_all_logs_to_db
        try:
            db_summary = get_db_summary()
            st.caption(f"💾 Total Trials: **{db_summary['total_trials']}** ({db_summary['human_trials']} Human)")
            st.caption(f"📊 Action Steps: **{db_summary['total_actions']}**")
        except Exception:
            pass

        if st.button("🔄 Sync & Refresh Database", use_container_width=True):
            with st.spinner("Syncing latest logs..."):
                sync_all_logs_to_db()
                export_combined_dataset()
                export_sft_dataset()
                st.success("Synced!")
                st.rerun()

        csv_path = os.path.join(PROJECT_ROOT, "data", "combined_scarcity_dataset.csv")

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="Download Combined CSV",
                    data=f.read(),
                    file_name="combined_scarcity_dataset.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        if os.path.exists(DEFAULT_DB_PATH):
            with open(DEFAULT_DB_PATH, "rb") as f:
                st.download_button(
                    label="Download SQLite DB",
                    data=f.read(),
                    file_name="scarcity_study.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                )

    with st.expander("🤖 AI & LLM Training Center", expanded=False):
        st.markdown("**Model Training & LLM Steering**")
        st.caption("Train ML models and update LLM exemplars directly using banked human data.")
        if st.button("⚡ Train / Retrain Models", use_container_width=True):
            with st.spinner("Training models on all human and AI trials..."):
                try:
                    from analysis.train_models import train_all_models_summary
                    results = train_all_models_summary()
                    st.success("✅ Models retrained successfully!")
                    cls_res = results.get("classifier", {})
                    pol_res = results.get("policy", {})
                    if "accuracy" in cls_res:
                        st.metric("Classifier CV Accuracy", f"{cls_res['accuracy'] * 100:.1f}%")
                    if "test_accuracy" in pol_res:
                        st.metric("Human Clone Policy Acc", f"{pol_res['test_accuracy'] * 100:.1f}%")
                    st.info("💡 LLM agents automatically incorporate these updated trajectories as few-shot exemplars.")
                except Exception as e:
                    st.error(f"Training error: {e}")

    st.divider()
    if st.button("🔐 Researcher & Admin Portal", use_container_width=True):
        st.session_state.portal_active = True
        st.rerun()



# ---------- SCREEN 1: CONSENT ----------
def consent_screen():
    # Top Hero Bar: Institutional Header + Researcher Portal Access
    tcol_left, tcol_right = st.columns([3, 1])
    with tcol_left:
        st.caption("🏛️ Behavioral AI & Human Scarcity Study | KIET Deemed to be University")
    with tcol_right:
        if st.button("🔐 Researcher Portal", key="hero_researcher_btn", help="Restricted access for investigators & faculty", use_container_width=True):
            st.session_state.portal_active = True
            st.rerun()

    st.title("🏝️ Island Survival Study: Water Decisions Under Scarcity")
    st.write(
        """
        Welcome! You are invited to take part in a short, interactive study (10–15 minutes) examining how people
        manage shared survival resources when nature gets tough.

        **What you will do:**
        - **Survive on an Island:** You and 4 automated computer teammates are stranded on an island.
        - **Share a Freshwater Lake:** All players share one central freshwater lake to stay alive.
        - **Manage Your Canteen:** Each round, your body naturally drinks **2 units of water**. You decide each round whether to **collect lake water**, **share water with teammates**, **ration your supply to save the lake**, or **send messages**.
        
        **Important Information:**
        - **Teammates:** Your 4 companions on the island are automated computer bots. You are playing solo with computer companions.
        - **Anonymity:** No personal identifying information is collected. Your decisions are recorded under an anonymous Player ID.
        - **Voluntary:** You can withdraw at any time by closing this tab. All data is reported in scientific aggregate.
        """
    )

    agree = st.checkbox("I have read the information above and agree to participate in this study.")

    st.subheader("Background (Optional)")
    st.caption("Used solely for statistical subgroup analysis in our research paper.")
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        age_group = st.selectbox(
            "Age Group",
            ["18-24", "25-34", "35-44", "45-54", "55+", "Prefer not to say"],
        )
        gender = st.selectbox(
            "Gender",
            ["Female", "Male", "Non-binary", "Other", "Prefer not to say"],
        )
    with dcol2:
        ai_fam = st.selectbox(
            "AI / Tech Familiarity",
            ["Beginner (casual user)", "Intermediate (regular user)", "Advanced (developer / researcher)"],
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agree & Continue ➡️", disabled=not agree, type="primary"):
            st.session_state.demographics = {
                "age_group": age_group,
                "gender": gender,
                "ai_familiarity": ai_fam,
            }
            go_to("instructions")
    with col2:
        if st.button("Decline"):
            st.warning("Thank you for your consideration. You may close this window.")
            st.stop()

    st.divider()
    bcol_left, bcol_right = st.columns([3, 1])
    with bcol_left:
        st.caption("Dept. of Computer Science & Engineering (AI & ML) | **Mentor:** Ms. Laxmi")
        st.caption("👥 **Researchers:** Utkarsh Pandey, Sujal Kumar, Saksham Singh, Yashash Tyagi")
    with bcol_right:
        if st.button("🔑 Admin Login", key="footer_admin_btn", use_container_width=True):
            st.session_state.portal_active = True
            st.rerun()



# ---------- SCREEN 2: INSTRUCTIONS ----------
def instructions_screen():
    st.title("📖 How the Game Works")

    rounds_total = (
        TOTAL_ROUNDS * 3
        if st.session_state.scenario == "repeated_trust"
        else TOTAL_ROUNDS
    )

    st.markdown(
        f"""
        ### 🏝️ Survival Rules at a Glance
        You are one of **{NUM_PLAYERS} islanders** (You + computer teammates A2, A3, A4, A5) surviving for **{rounds_total} rounds**.

        | Rule / Action | What It Does | Why It Matters |
        | :--- | :--- | :--- |
        | 💧 **Your Thirst** | You automatically consume **{SURVIVAL_COST} units of water** every round. | If your personal water falls below 0, you dehydrate and are eliminated! |
        | 🌊 **Shared Lake** | All 5 players share the island's central lake. | The lake naturally replenishes each round—but if everyone over-harvests, it dries to 0! |
        | 💧 **Collect Water** | Scoop water from the lake (**+3 units** normal, **+1 unit** in drought). | Refills your water canteen, but drains water from the shared lake. |
        | 🛡️ **Ration / Rest** | Drink from your own canteen without touching the lake! Consumes {SURVIVAL_COST} units. | **Saves the lake!** Gives the lake time to naturally refill and recover. |
        | 🤝 **Share Water** | Gift 1 or more units from your canteen to another player. | Saves a struggling teammate's life and builds mutual trust. |
        | 💬 **Send Message** | Send announcements, water reports, or requests for help. | Helps coordinate team action across the island. |
        | ⏳ **Wait / Skip** | Take no action this turn (you still drink {SURVIVAL_COST} units). | Rest turn. |

        *(🎒 **Private Canteen:** Teammates can see what action you took, but they cannot see how much water is inside your canteen unless you choose to tell them!)*
        """
    )

    if st.session_state.scenario == "drought":
        st.warning(
            f"⚠️ **Drought Alert:** In Round {DROUGHT_ROUND}, an extreme heatwave strikes! Water collection drops to **only 1 unit**, and the lake stops refilling quickly. Build a water cushion of 3-4 units beforehand!"
        )

    if st.button("Start Island Simulation 🚀", type="primary"):
        reset_environment()
        go_to("game")


# ---------- POST-ROUND TRANSITION & NEXT ROUND BRIEFING ----------
def render_round_transition_screen():
    """Renders a dedicated status briefing after each round stating parameters and conditions for the next round."""
    env: ScarcityEnv = st.session_state.get("env")
    data = st.session_state.get("round_transition_data", {})
    completed_round = data.get("completed_round", 1)
    next_round = data.get("next_round", completed_round + 1)
    total_rounds = data.get("total_rounds", TOTAL_ROUNDS)
    scenario = data.get("scenario", "drought")
    done = data.get("done", False)
    focal_id = data.get("focal_id", st.session_state.participant_id)
    focal_alive = data.get("focal_alive", True)
    focal_res_before = data.get("focal_res_before", 0.0)
    focal_res_after = data.get("focal_res_after", 0.0)
    pool_before = data.get("pool_before", 0.0)
    pool_after = data.get("pool_after", 0.0)
    pool_capacity = data.get("pool_capacity", 20.0)
    events = data.get("events_this_round", [])
    coplayer_summaries = data.get("coplayer_summaries", [])
    focal_summary = data.get("focal_summary", {})

    p_name_val = st.session_state.get("participant_name", "").strip()
    p_display = f"Player: **{p_name_val}** (`{focal_id}`)" if p_name_val else f"Player: `{focal_id}`"

    # CASE 1: Focal player died this round
    if not focal_alive:
        st.error(f"💀 **Game Over — Round {completed_round} Fatal Depletion**")
        st.markdown(
            f"Your personal water reserve fell to **{focal_res_after:.1f} units** (below 0) "
            f"after survival consumption at the end of Round {completed_round}. You could not survive on the island."
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("Your Final Water", f"{focal_res_after:.1f}", f"{focal_res_after - focal_res_before:+.1f}")
        col2.metric("Survival Cost", f"-{SURVIVAL_COST:.1f}")
        col3.metric("Lake Commons Stock", f"{pool_after:.1f} / {pool_capacity:.0f}")

        if events:
            with st.expander("📢 Round Events Feed", expanded=True):
                for ev in events:
                    st.write(ev)

        st.divider()
        if st.button("Proceed to Debrief & Study Results ➡️", type="primary", use_container_width=True):
            st.session_state.round_transition_active = False
            go_to("debrief")
        return

    # CASE 2: All rounds finished (Final round concluded)
    if done:
        st.success(f"🏆 **Study Complete — Final Round {completed_round} of {total_rounds} Concluded!**")
        st.markdown(
            f"Congratulations! You survived all **{total_rounds} rounds** of the **{scenario.upper()}** condition. "
            f"Your final personal water reserve is **{focal_res_after:.1f} units**."
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Water", f"{focal_res_after:.1f}", f"{focal_res_after - focal_res_before:+.1f}")
        col2.metric("Your Status", "Alive ✅")
        col3.metric("Ending Lake Stock", f"{pool_after:.1f} / {pool_capacity:.0f}")
        alive_total = sum(1 for p in env.players.values() if p.alive) if env else 1
        col4.metric("Island Survivors", f"{alive_total} / {NUM_PLAYERS}")

        if events:
            with st.expander("📢 Final Round Events Feed", expanded=True):
                for ev in events:
                    st.write(ev)

        st.divider()
        if st.button("Proceed to Behavioral Turing Test & Debrief 🎓", type="primary", use_container_width=True):
            st.session_state.round_transition_active = False
            go_to("debrief")
        return

    # CASE 3: Active Simulation Between Rounds — State Status for Next Round!
    st.title(f"Round {completed_round} Complete ➔ Briefing for Round {next_round}")
    progress_val = min(1.0, max(0.0, completed_round / total_rounds))
    st.progress(progress_val)
    st.caption(
        f"{p_display} | Progress: Round {completed_round} of {total_rounds} finished "
        f"({int(progress_val * 100)}%) | Scenario: **{scenario.upper()}**"
    )

    # --- PART A: RECAP OF COMPLETED ROUND ---
    st.markdown(f"### 📋 Round {completed_round} Outcomes")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)

    act_type = focal_summary.get("action_type", "skip")
    action_labels = {
        "gather": "💧 Collected Water",
        "share": "🤝 Shared Water",
        "hoard": "🛡️ Rationed / Rested (Saved Lake)",
        "skip": "⏳ Skipped Turn",
        "communicate": "💬 Sent Message",
    }
    act_display = action_labels.get(act_type, act_type.capitalize())
    if act_type == "share" and focal_summary.get("target_agent"):
        act_display = f"🤝 Shared {focal_summary.get('share_amount', 1)} ➔ {focal_summary.get('target_agent')}"

    mcol1.metric("Your Action", act_display)
    mcol2.metric(
        "Your Water",
        f"{focal_res_after:.1f}",
        f"{focal_res_after - focal_res_before:+.1f} units",
    )
    if pool_after > 15.0:
        pool_status_str = "🟢 Lake Healthy"
    elif pool_after >= 6.0:
        pool_status_str = "🟡 Lake Stressed"
    else:
        pool_status_str = "🔴 Lake Low"
    mcol3.metric(
        "Shared Lake Level",
        f"{pool_after:.1f} / {pool_capacity:.0f}",
        f"{pool_after - pool_before:+.1f} ({pool_status_str})",
    )
    alive_count = sum(1 for p in env.players.values() if p.alive) if env else 5
    mcol4.metric("Island Survivors", f"{alive_count} / {NUM_PLAYERS} Alive")

    # Co-player activity recap
    with st.expander(f"👥 Teammate Actions in Round {completed_round}", expanded=True):
        if events:
            for ev in events:
                st.write(ev)
        if coplayer_summaries:
            c_cols = st.columns(len(coplayer_summaries))
            for idx, cinfo in enumerate(coplayer_summaries):
                with c_cols[idx]:
                    c_status = "🟢" if cinfo.get("alive") else "💀"
                    st.markdown(f"**{c_status} {cinfo['agent_id']}**")
                    c_act = cinfo.get("action_type", "skip")
                    friendly_c_act = action_labels.get(c_act, c_act)
                    st.caption(f"Action: {friendly_c_act}")
                    if c_act == "share" and cinfo.get("target_agent"):
                        st.caption(f"Target: `{cinfo['target_agent']}`")
                    if cinfo.get("message_sent"):
                        st.caption(f"*\"{cinfo['message_sent'][:25]}\"*")

    st.divider()

    # --- PART B: STATING FOR NEXT ROUND ---
    st.markdown(f"### 🎯 Next Round Briefing: Island Status for Round {next_round}")

    drought_next = is_drought(next_round, scenario)
    drought_in_two = is_drought(next_round + 1, scenario) if (next_round + 1 <= total_rounds) else False

    # Weather & Environmental Alert for Next Round
    if drought_next:
        st.error(
            f"🚨 **CRITICAL WEATHER WARNING: DROUGHT ROUND {next_round}!**\n\n"
            f"• **Yield Collapse:** Collecting water drops sharply from 3 units to **1 unit**.\n"
            f"• **Natural Replenishment Throttled:** The lake regenerates at a fraction of normal rate.\n"
            f"• **Mandatory Consumption:** You will still consume **{SURVIVAL_COST} units** of water at the end of Round {next_round}.\n"
            f"• **Risk:** If players over-gather, the lake may permanently collapse to 0!"
        )
    elif drought_in_two:
        st.warning(
            f"⚠️ **WEATHER WATCH: Approaching Drought in Round {next_round + 1}!**\n\n"
            f"Round {next_round} is your **last normal round** before severe scarcity begins. "
            f"Ensure you build a safety cushion of at least 3 to 4 water units before the drought strikes."
        )
    else:
        st.info(
            f"☀️ **Environmental Forecast: Calm & Stable Island Conditions**\n\n"
            f"• **Gather Yield:** Standard **+{gather_yield(next_round, scenario)} units** from the lake.\n"
            f"• **Lake Commons:** Natural rainwater refilling is active.\n"
            f"• **Survival Cost:** Standard **-{SURVIVAL_COST} units** will be deducted at the end of Round {next_round}."
        )

    # Readiness & Survival Math for Round {next_round}
    bcol1, bcol2, bcol3 = st.columns(3)
    bcol1.metric("Your Starting Water", f"{focal_res_after:.1f} units")
    bcol2.metric("Survival Cost (Round End)", f"-{SURVIVAL_COST:.1f} units")
    projected_balance = focal_res_after - SURVIVAL_COST
    bcol3.metric(
        "Projected Water (Without Collecting)",
        f"{projected_balance:.1f} units",
        "Safe" if projected_balance > 0 else "Danger",
        delta_color="normal" if projected_balance > 0 else "inverse",
    )

    if focal_res_after <= SURVIVAL_COST:
        st.error(
            f"⚠️ **URGENT WATER DEFICIT FOR ROUND {next_round}:** "
            f"You have only **{focal_res_after:.1f} units** remaining! "
            f"If you do not **Collect water** or receive a **Share from a teammate** in Round {next_round}, "
            f"you will run out of water and die at the end of the round."
        )
    elif focal_res_after <= 4.0:
        st.warning(
            f"🔔 **Rationing Advisory:** You have **{focal_res_after:.1f} units** — sufficient for 1-2 rounds. "
            f"Monitor lake health and teammate actions carefully."
        )
    else:
        st.success(
            f"🛡️ **Reserves Healthy:** You have **{focal_res_after:.1f} units** in reserve, providing a solid safety cushion."
        )

    # Teammates entering next round
    alive_coplayers = [pid for pid in COPLAYER_IDS if env.players[pid].alive] if env else COPLAYER_IDS
    st.caption(
        f"🏝️ **Island Status Entering Round {next_round}:** "
        f"Lake commons at **{pool_after:.1f} / {pool_capacity:.0f} units** ({pool_status_str}) | "
        f"Active co-players: **{', '.join(alive_coplayers) if alive_coplayers else 'None (all deceased)'}**"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- PART C: PROCEED BUTTON ---
    if st.button(
        f"👉 Proceed to Round {next_round} ➡️",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.round_transition_active = False
        st.session_state.round_start_time = time.time()
        st.rerun()


# ---------- SCREEN 3: GAME ----------
def game_screen():
    if "env" not in st.session_state or st.session_state.env is None:
        reset_environment()

    # Interstitial transition screen between rounds stating for next round
    if st.session_state.get("round_transition_active", False):
        render_round_transition_screen()
        return

    env: ScarcityEnv = st.session_state.env
    focal_id = st.session_state.participant_id
    focal_player = env.players[focal_id]
    r = env.round
    total_r = env.total_rounds

    drought_now = is_drought(r, env.scenario)
    round_label = "⚠️ Drought Round — Severe Scarcity!" if drought_now else "Normal Round"

    p_name_val = st.session_state.get("participant_name", "").strip()
    p_display = f"Player: **{p_name_val}** (`{focal_id}`)" if p_name_val else f"Player: `{focal_id}`"

    st.title(f"Round {r} of {total_r}")
    st.caption(f"{p_display} | Scenario: **{env.scenario.upper()}** | {round_label}")

    if focal_player.alive and focal_player.resource <= 2.0:
        st.warning(
            f"⚠️ **Low Water Critical Warning:** You have **{focal_player.resource:.1f} units** remaining! "
            f"You will consume **{SURVIVAL_COST} units** at the end of this round. "
            "Consider **Gathering** water or requesting a **Share** from teammates to survive!"
        )

    # Top Status Bar
    col1, col2, col3 = st.columns(3)
    col1.metric("🎒 Your Water Canteen", f"{focal_player.resource:.1f} units")
    col2.metric("Your Status", "Alive ✅" if focal_player.alive else "Deceased ❌")
    pool_pct = max(0.0, min(100.0, (env.pool.stock / env.pool.capacity) * 100))
    if env.pool.stock > 15.0:
        pool_status = "🟢 Lake Healthy"
    elif env.pool.stock >= 6.0:
        pool_status = "🟡 Lake Stressed (Needs Rest)"
    else:
        pool_status = "🔴 Lake Dangerously Low"
    col3.metric("🌊 Shared Lake Level", f"{env.pool.stock:.1f} / {env.pool.capacity:.0f} units", pool_status)

    st.progress(pool_pct / 100.0)

    # If focal player died
    if not focal_player.alive:
        st.error("💀 **Game Over:** You ran out of water and could not survive on the island.")
        # Ensure trial is validated and synced to SQLite database and CSV right now!
        if not st.session_state.get("trial_synced_to_db") and st.session_state.all_trial_rows:
            try:
                from common.database import export_combined_dataset, export_sft_dataset, sync_trial_log_to_db
                validate_trial_log(st.session_state.trial_id)
                sync_trial_log_to_db(st.session_state.all_trial_rows)
                export_combined_dataset()
                export_sft_dataset()
                st.session_state.trial_synced_to_db = True
            except Exception:
                pass
        if st.button("Proceed to Debrief", type="primary"):
            go_to("debrief")
        return

    # Previous round event feed
    if st.session_state.last_round_events:
        with st.expander("📢 What happened last round", expanded=True):
            for ev in st.session_state.last_round_events:
                st.write(ev)

    st.divider()

    # Public Co-Players Information
    st.subheader("👥 Other Teammates on the Island")
    coplayer_cols = st.columns(len(COPLAYER_IDS))
    for i, pid in enumerate(COPLAYER_IDS):
        pstate = env.players[pid]
        with coplayer_cols[i]:
            status_emoji = "🟢" if pstate.alive else "💀"
            st.markdown(f"**{status_emoji} {pid}**")
            st.caption(f"Status: {'Alive' if pstate.alive else 'Dehydrated'}")
            if pstate.last_action:
                friendly_last = {
                    "gather": "💧 Collected water",
                    "share": "🤝 Shared water",
                    "hoard": "🛡️ Rationed / Rested",
                    "communicate": "💬 Sent message",
                    "skip": "⏳ Skipped turn",
                }.get(pstate.last_action.value, pstate.last_action.value)
                st.caption(f"Last: {friendly_last}")

    st.divider()

    # Action Selection Form
    st.subheader("Choose Your Action for This Round")
    action_type_str = st.radio(
        "Action",
        ACTIONS,
        horizontal=True,
        format_func=lambda a: {
            "gather": "💧 Collect Water (Take from Lake)",
            "share": "🤝 Share Water (Gift to Teammate)",
            "hoard": "🛡️ Ration / Rest (Protect the Lake)",
            "communicate": "💬 Send Message to Team",
            "skip": "⏳ Wait / Skip Turn",
        }.get(a, a),
    )

    action_helpers = {
        "gather": f"💧 **Collect Water:** Scoop water from the shared lake (**+{1 if drought_now else 3} units** this round). Your body drinks **-{SURVIVAL_COST} units** at the end of the round.",
        "share": "🤝 **Share Water:** Gift water from your canteen to another player to keep them alive and foster trust.",
        "hoard": f"🛡️ **Ration / Rest:** Rest and drink from your canteen without touching the lake! Consumes your normal **-{SURVIVAL_COST} units**, but allows the shared lake to naturally replenish.",
        "communicate": "💬 **Send Message:** Broadcast a message, update the team on your water level, or ask for help without transferring water.",
        "skip": f"⏳ **Wait / Skip:** Take no action this round (still consumes normal **-{SURVIVAL_COST} units**).",
    }
    st.info(action_helpers.get(action_type_str, ""))

    target_agent = None
    share_amount = 1
    claim_kind = "none"
    claim_value = None
    message_text = ""

    alive_coplayers = [pid for pid in COPLAYER_IDS if env.players[pid].alive]

    if action_type_str == "share":
        scol1, scol2 = st.columns(2)
        with scol1:
            if alive_coplayers:
                target_agent = st.selectbox("Recipient Teammate", alive_coplayers)
            else:
                st.warning("No teammates are alive to receive water.")
        with scol2:
            max_share = max(1, int(focal_player.resource))
            share_amount = st.number_input(
                "Water amount to give",
                min_value=1,
                max_value=max(1, max_share),
                value=1,
                step=1,
            )

    if action_type_str in ("share", "communicate"):
        st.markdown("**Team Message (Optional Broadcast / Claim):**")
        if action_type_str == "communicate":
            target_agent = st.selectbox(
                "Send Message To",
                ["all"] + alive_coplayers,
                format_func=lambda t: "Everyone (Public Broadcast)" if t == "all" else f"Teammate {t}",
                help="Send to all players or a specific player",
            )

        ccol1, ccol2 = st.columns(2)
        with ccol1:
            claim_kind = st.selectbox(
                "Message Type",
                MESSAGE_KINDS,
                format_func=lambda k: {
                    "none": "💬 Friendly Note / General Chat",
                    "claim_stock": "📢 Report my current water level",
                    "promise_share": "🤝 Promise to share water soon",
                    "request": "🆘 Ask a teammate for water",
                    "accuse": "⚠️ Warn team about over-gathering",
                }.get(k, k),
            )
        with ccol2:
            if claim_kind != "none":
                claim_value = st.number_input(
                    "Reported Water Amount (e.g. your stated water or promised gift):",
                    min_value=0,
                    step=1,
                    value=int(focal_player.resource) if claim_kind == "claim_stock" else 1,
                )

        message_text = st.text_input("Message wording (Optional)", "")

    # Submit Button
    if st.button("Submit Action", type="primary", disabled=(action_type_str == "share" and not alive_coplayers)):
        latency_ms = max(0, int((time.time() - st.session_state.round_start_time) * 1000))

        # 1. Build focal human Action object
        claim_meta = None
        structured_msg = None
        if claim_kind != "none" or message_text:
            structured_msg = Message(
                kind=MessageKind(claim_kind),
                value=int(claim_value) if claim_value is not None else None,
                target=target_agent,
                surface=message_text or None,
            )
            claim_meta = {
                "kind": claim_kind,
                "value": int(claim_value) if claim_value is not None else None,
                "target": target_agent,
                "surface": message_text or None,
            }

        if action_type_str == "gather":
            human_action = Action(type=ActionType.GATHER)
        elif action_type_str == "share":
            human_action = Action(
                type=ActionType.SHARE,
                target=target_agent,
                amount=int(share_amount),
                message=structured_msg,
            )
        elif action_type_str == "hoard":
            human_action = Action(type=ActionType.HOARD)
        elif action_type_str == "skip":
            human_action = Action(type=ActionType.SKIP)
        elif action_type_str == "communicate":
            human_action = Action(
                type=ActionType.COMMUNICATE,
                target=target_agent,
                message=structured_msg or Message(kind=MessageKind.NONE, surface="hello"),
            )
        else:
            human_action = Action(type=ActionType.SKIP)

        # 2. Query co-player policies for actions
        actions: dict[str, Action] = {focal_id: human_action}
        for pid in COPLAYER_IDS:
            if env.players[pid].alive:
                obs_pid = st.session_state.current_obs[pid]
                policy = st.session_state.coplayers[pid]
                actions[pid] = policy.act(obs_pid)

        # 3. Step ScarcityEnv
        completed_round = env.round
        pool_before = env.pool.stock
        focal_res_before = focal_player.resource

        next_obs, done, raw_log_rows = env.step(actions)
        st.session_state.current_obs = next_obs
        pool_after = env.pool.stock
        focal_res_after = focal_player.resource
        focal_alive_after = focal_player.alive

        # 4. Enrich and log rows to data/human_logs/
        timestamp = datetime.now(timezone.utc).isoformat()
        enriched_rows = []
        events_this_round = []

        for row in raw_log_rows:
            agent_id = row["agent_id"]
            row["trial_id"] = st.session_state.trial_id
            row["timestamp"] = timestamp

            if agent_id == focal_id:
                row["source"] = "human"
                row["meta"] = {
                    "arm": "human",
                    "seed": st.session_state.seed,
                    "severity": st.session_state.severity,
                    "decision_latency_ms": latency_ms,
                    "claim": claim_meta,
                    "demographics": st.session_state.get("demographics"),
                }
                st.session_state.action_log.append(row)
            else:
                row["source"] = "ai"
                active_policies = get_active_coplayer_policies()
                pol_name = active_policies[COPLAYER_IDS.index(agent_id)]
                row["meta"] = {
                    "arm": "human",
                    "seed": st.session_state.seed,
                    "policy": pol_name,
                    "severity": st.session_state.severity,
                }
                # Track if a co-player shared water with human or sent a message
                if row["action_type"] == "share" and row.get("target_agent") == focal_id:
                    events_this_round.append(f"💧 **{agent_id}** shared water with **YOU**!")
                elif row["action_type"] == "communicate":
                    msg_txt = row.get("message_sent") or "(structured notice)"
                    events_this_round.append(f"💬 **{agent_id}** broadcast: *\"{msg_txt}\"*")

            enriched_rows.append(row)
            st.session_state.all_trial_rows.append(row)

        log_round_records(st.session_state.trial_id, enriched_rows)

        # Summary event for pool
        events_this_round.append(f"🌊 Pool level at end of round: **{env.pool.stock:.1f} units**")
        st.session_state.last_round_events = events_this_round

        # 5. Extract round summaries for transition briefing
        coplayer_summaries = []
        for row in enriched_rows:
            if row["agent_id"] != focal_id:
                coplayer_summaries.append({
                    "agent_id": row["agent_id"],
                    "action_type": row["action_type"],
                    "target_agent": row.get("target_agent"),
                    "message_sent": row.get("message_sent"),
                    "resource_before": row.get("resource_before"),
                    "resource_after": row.get("resource_after"),
                    "alive": row.get("alive"),
                })

        focal_summary = {
            "action_type": action_type_str,
            "target_agent": target_agent,
            "share_amount": share_amount if action_type_str == "share" else None,
            "claim_kind": claim_kind,
            "claim_value": claim_value,
            "message_text": message_text,
            "resource_before": focal_res_before,
            "resource_after": focal_res_after,
            "alive": focal_alive_after,
        }

        # 6. Store transition briefing data & activate transition UI
        st.session_state.round_transition_data = {
            "completed_round": completed_round,
            "next_round": env.round,
            "total_rounds": env.total_rounds,
            "scenario": env.scenario,
            "done": done,
            "focal_id": focal_id,
            "focal_alive": focal_alive_after,
            "focal_res_before": focal_res_before,
            "focal_res_after": focal_res_after,
            "pool_before": pool_before,
            "pool_after": pool_after,
            "pool_capacity": env.pool.capacity,
            "events_this_round": events_this_round,
            "coplayer_summaries": coplayer_summaries,
            "focal_summary": focal_summary,
        }
        st.session_state.round_transition_active = True

        # Sync to DB if simulation finished or focal player died
        if done or not focal_alive_after:
            validate_trial_log(st.session_state.trial_id)
            try:
                from common.database import export_combined_dataset, export_sft_dataset, sync_trial_log_to_db
                sync_trial_log_to_db(st.session_state.all_trial_rows)
                export_combined_dataset()
                export_sft_dataset()
                st.session_state.trial_synced_to_db = True
            except Exception:
                pass

        st.rerun()

# ---------- SCREEN 4: DEBRIEF & BEHAVIORAL TURING TEST ----------

def debrief_screen():
    # Guarantee that trial is synced to SQLite database and CSV export right upon landing!
    if not st.session_state.get("trial_synced_to_db") and st.session_state.all_trial_rows:
        try:
            from common.database import export_combined_dataset, export_sft_dataset, sync_trial_log_to_db
            validate_trial_log(st.session_state.trial_id)
            sync_trial_log_to_db(st.session_state.all_trial_rows)
            export_combined_dataset()
            export_sft_dataset()
            st.session_state.trial_synced_to_db = True
        except Exception:
            pass

    p_name = st.session_state.get("participant_name", "").strip()
    p_display = f"{p_name} ({st.session_state.participant_id})" if p_name else st.session_state.participant_id
    st.title(f"Study Completed — Thank You, {p_name or st.session_state.participant_id}!")
    st.write(
        f"Your trial has finished and your decision log has been securely saved into the research database "
        f"under participant **{p_display}**."
    )

    action_log = st.session_state.action_log
    all_rows = st.session_state.all_trial_rows
    env: ScarcityEnv | None = st.session_state.get("env")

    # ---------- SECTION A: OUTCOME SUMMARY ----------
    st.subheader("📊 Session Overview")
    col1, col2, col3, col4 = st.columns(4)

    focal_id = st.session_state.participant_id
    focal_alive = env.players[focal_id].alive if env else False
    focal_res = env.players[focal_id].resource if env else 0.0

    alive_total = sum(1 for p in env.players.values() if p.alive) if env else 0
    all_resources = [p.resource for p in env.players.values()] if env else [focal_res]

    col1.metric("Your Survival", "Survived ✅" if focal_alive else "Died ❌")
    col2.metric("Final Water", f"{focal_res:.1f} units")
    col3.metric("Island Survivors", f"{alive_total} / {NUM_PLAYERS}")
    gini = calculate_gini(all_resources)
    col4.metric("Water Equality (Gini)", f"{gini:.2f}", help="0.00 = Perfect equality across players, 1.00 = Extreme inequality")

    st.divider()

    # ---------- SECTION B: BEHAVIORAL PROFILE ----------
    st.subheader("🧠 Your Playing Style & Decision Metrics")

    counts = count_actions(action_log)
    rates = action_rates(action_log)
    deception_stats = calculate_deception(action_log)
    latency_stats = calculate_latency_stats(action_log)

    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    bcol1.metric("Sharing Rate", f"{rates.get('share', 0.0):.1f}%")
    bcol2.metric("Rationing Rate", f"{rates.get('hoard', 0.0):.1f}%")
    bcol3.metric("Misleading Reports", f"{deception_stats['deception_rate']:.1f}%")
    bcol4.metric("Decision Speed", f"{latency_stats['mean_ms']:.0f} ms")

    st.bar_chart(counts)

    if deception_stats["total_claims"] > 0:
        st.info(
            f"🔍 **Water Reporting Accuracy:** You shared your water count {deception_stats['total_claims']} times; "
            f"{deception_stats['deceptive_claims']} times your reported number differed from your true canteen reserve."
        )

    st.divider()

    # ---------- SECTION C: NOVELTY N8 - BEHAVIORAL TURING TEST ----------
    st.subheader("🤖 Challenge: Can You Spot the Real Human Player?")
    st.write(
        """
        Can you tell the difference between how a human plays versus how an AI computer bot plays under scarcity?
        Below are two real 6-round action histories from this island simulation. One is an AI bot, the other is a real human participant:
        """
    )

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.markdown("**Player Trajectory A:**")
        st.code("R1: Collect water\nR2: Collect water\nR3: Share water (1 unit to A2)\nR4: Ration / Rest\nR5: Collect water\nR6: Send message (Ask for water)")
    with tcol2:
        st.markdown("**Player Trajectory B:**")
        st.code("R1: Collect water\nR2: Collect water\nR3: Collect water\nR4: Collect water\nR5: Ration / Rest\nR6: Ration / Rest")

    if not st.session_state.turing_submitted:
        choice = st.radio(
            "Which trajectory was played by the REAL HUMAN participant?",
            ["Player A is Human, Player B is AI Bot", "Player B is Human, Player A is AI Bot"],
        )
        if st.button("Submit Your Guess 🎯", type="primary"):
            st.session_state.turing_guess = choice
            st.session_state.turing_submitted = True
            is_correct_val = "Player A is Human" in choice
            # Log judgment to JSONL and SQLite DB
            turing_log_path = os.path.join(LOG_DIR, "turing_judgments.jsonl")
            with open(turing_log_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "participant_id": st.session_state.participant_id,
                            "guess": choice,
                            "correct": is_correct_val,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    + "\n"
                )
            try:
                from common.database import export_combined_dataset, save_turing_judgment, sync_trial_log_to_db
                save_turing_judgment(st.session_state.participant_id, choice, is_correct_val)
                sync_trial_log_to_db(st.session_state.all_trial_rows)
                export_combined_dataset()
            except Exception:
                pass
            st.rerun()
    else:
        guess = st.session_state.turing_guess
        is_correct = "Player A is Human" in (guess or "")
        if is_correct:
            st.success("🎉 **Correct!** Player A was the real human! Notice the social sharing and team communication, whereas the AI bot (Player B) rigidly collected water and rested purely for its own survival.")
        else:
            st.warning("❌ **Incorrect.** Player A was actually the real human! Humans actively engage in reciprocal sharing and signaling, whereas standard AI bot policies follow rigid harvesting rules.")
        st.caption("Your guess has been recorded into our scientific Turing-distinguishability dataset.")

    st.divider()

    # ---------- SECTION D: ACTION LOG DATA ----------
    st.subheader(f"📄 Recorded Trial Log for {p_display}")
    if action_log:
        st.dataframe(action_log, width="stretch")
        jsonl_str = "\n".join([json.dumps(r) for r in all_rows])
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.download_button(
                label="📥 Download Complete Trial JSONL",
                data=jsonl_str,
                file_name=f"{st.session_state.trial_id}.jsonl",
                mime="application/jsonlines",
                use_container_width=True,
            )
        with dcol2:
            from common.database import export_combined_dataset
            csv_path = export_combined_dataset()
            if os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Download Combined CSV (With Your Trial)",
                        data=f.read(),
                        file_name="combined_scarcity_dataset.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

    # ---------- SECTION E: AI & LLM MODEL TRAINING CENTER ----------
    st.divider()
    st.subheader("🤖 How Your Decisions Directly Power Our AI Models")
    st.write(
        """
        Your trial was automatically banked into the research database! Here is how your choices help train each AI model:
        - **1. Spotting Humans vs Bots (Classifier):** Helps the system distinguish human empathy and communication from simple computer scripts.
        - **2. Learning Human Survival Instincts (Imitation Model):** Teaches bots how real people balance self-preservation with helping teammates.
        - **3. Teaching Advanced AI (Groq & Gemini LLMs):** Co-player AI agents learn from your decisions as real examples of teamwork and crisis management.
        - **4. Fine-Tuning Open Source AI:** Your gameplay steps are formatted into training sets (`data/llm_sft_dataset.jsonl`) to train models on social coordination.
        """
    )

    mcol1, mcol2 = st.columns([2, 1])
    with mcol1:
        from common.database import get_db_summary
        summary = get_db_summary()
        st.metric(
            "Total Trials in Database",
            f"{summary['total_trials']} trials",
            f"{summary['human_trials']} human sessions",
        )
        st.caption(f"Banked Action Steps: **{summary['total_actions']}**")
    with mcol2:
        if st.button("⚡ Retrain AI Models with My Data Now", type="primary", use_container_width=True):
            with st.spinner("Retraining Classifier & Human Clone Policy on all data..."):
                try:
                    from analysis.train_models import train_all_models_summary
                    results = train_all_models_summary()
                    st.session_state.latest_training_results = results
                    st.balloons()
                    st.success("🎉 Models successfully updated with your gameplay!")
                except Exception as e:
                    st.error(f"Training error: {e}")

    if st.session_state.get("latest_training_results"):
        res = st.session_state.latest_training_results
        cls_res = res.get("classifier", {})
        pol_res = res.get("policy", {})
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.markdown("🎯 **Model A: Distinguishability Classifier**")
            st.write(f"- 5-Fold Cross-Val Accuracy: **{cls_res.get('accuracy', 0.0) * 100:.1f}%**")
            st.write(f"- ROC-AUC Score: **{cls_res.get('auc', 0.0):.3f}**")
            st.caption("Checkpoint: `models/distinguishability_classifier.json`")
        with rcol2:
            st.markdown("🧬 **Model B: Human Clone Policy**")
            st.write(f"- Test Set Accuracy: **{pol_res.get('test_accuracy', 0.0) * 100:.1f}%**")
            st.write(f"- Trained Steps: **{pol_res.get('n_samples', 0)}**")
            st.caption("Checkpoint: `models/human_clone_policy.json`")


# ---------- ROUTER ----------
if query_params.get("mode") == "researcher" or st.session_state.get("portal_active", False):
    import importlib
    import dashboard.researcher_hub
    importlib.reload(dashboard.researcher_hub)
    from dashboard.researcher_hub import render_researcher_hub
    render_researcher_hub(embedded=True)
else:
    stage = st.session_state.stage
    if stage == "consent":
        consent_screen()
    elif stage == "instructions":
        instructions_screen()
    elif stage == "game":
        game_screen()
    elif stage == "debrief":
        debrief_screen()
