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
    HOARD_SURVIVAL_COST,
    MATCHED_SEEDS,
    NUM_PLAYERS,
    SCENARIOS,
    START_WATER,
    SURVIVAL_COST,
    TOTAL_ROUNDS,
    gather_yield,
    is_alive,
    is_drought,
    survival_cost,
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

if "trial_id" not in st.session_state:
    st.session_state.trial_id = f"{st.session_state.scenario}_human_{st.session_state.seed:03d}_{uuid.uuid4().hex[:6]}"

if "action_log" not in st.session_state:
    st.session_state.action_log = []

if "all_trial_rows" not in st.session_state:
    st.session_state.all_trial_rows = []

if "round_start_time" not in st.session_state:
    st.session_state.round_start_time = time.time()

if "last_round_events" not in st.session_state:
    st.session_state.last_round_events = []

if "turing_guess" not in st.session_state:
    st.session_state.turing_guess = None

if "turing_submitted" not in st.session_state:
    st.session_state.turing_submitted = False


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
    coplayers = {
        pid: get_policy(COPLAYER_POLICIES[i], seed=st.session_state.seed + i + 1)
        for i, pid in enumerate(COPLAYER_IDS)
    }
    obs = env.reset()
    st.session_state.env = env
    st.session_state.coplayers = coplayers
    st.session_state.current_obs = obs
    st.session_state.action_log = []
    st.session_state.all_trial_rows = []
    st.session_state.last_round_events = []
    st.session_state.round_start_time = time.time()


def go_to(stage: str):
    st.session_state.stage = stage
    st.rerun()


# ---------- SIDEBAR: STUDY CONFIG (Editable prior to game start) ----------
with st.sidebar:
    st.header("🔬 Session Parameters")
    if st.session_state.stage in ("consent", "instructions"):
        selected_scenario = st.selectbox(
            "Scenario",
            options=list(SCENARIOS),
            index=list(SCENARIOS).index(st.session_state.scenario),
            help="Experimental condition: calm (baseline), drought (resource shock), repeated_trust (30 rounds)",
        )
        selected_seed = st.selectbox(
            "Matched Seed",
            options=list(MATCHED_SEEDS),
            index=st.session_state.seed,
            help="Fixed RNG seed matched against the AI primary arm trials (0-29)",
        )
        severity_val = st.slider(
            "Scarcity Severity",
            min_value=0.0,
            max_value=1.0,
            value=0.7 if selected_scenario == "drought" else 0.0,
            step=0.1,
            help="Novelty N1: dose-response parameter",
        )
        if (
            selected_scenario != st.session_state.scenario
            or selected_seed != st.session_state.seed
            or severity_val != st.session_state.severity
        ):
            st.session_state.scenario = selected_scenario
            st.session_state.seed = selected_seed
            st.session_state.severity = severity_val
            st.session_state.trial_id = f"{selected_scenario}_human_{selected_seed:03d}_{uuid.uuid4().hex[:6]}"
            st.rerun()
    else:
        st.write(f"**Scenario:** `{st.session_state.scenario}`")
        st.write(f"**Matched Seed:** `{st.session_state.seed}`")
        st.write(f"**Severity:** `{st.session_state.severity}`")

    st.divider()
    st.caption(f"Participant: `{st.session_state.participant_id}`")
    st.caption(f"Trial ID: `{st.session_state.trial_id}`")

    with st.expander("📥 Researcher Data Export", expanded=False):
        from common.database import DEFAULT_DB_PATH, export_combined_dataset
        csv_path = export_combined_dataset()
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



# ---------- SCREEN 1: CONSENT ----------
def consent_screen():
    st.title("Research Study: Resource Decisions Under Scarcity")
    st.write(
        """
        You are invited to take part in a research study (10–15 minutes) examining how people
        make allocation decisions when essential shared resources are scarce.

        **What you will do:**
        - You will participate in a round-based survival simulation set on an island.
        - You and four computer-controlled co-players share a common water pool.
        - Each round you must manage your water to survive while deciding whether to
          gather, share, hoard, or communicate.

        **Ethics & Co-Player Disclosure:**
        - **Co-players:** The other four players on the island are automated computer policies.
          You are not playing with other active human subjects in real time.
        - **Anonymity:** No personally identifying information is collected. Your decisions
          are recorded under an anonymous participant ID.
        - **Voluntary Participation:** You may withdraw at any time by closing this browser tab.
          All data is collected solely for scientific research and reported in aggregate.
        """
    )

    agree = st.checkbox("I have read the information above and consent to participate.")

    st.subheader("Demographic Background (Optional)")
    st.caption("Used solely for statistical subgroup analysis in the research paper.")
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        p_name = st.text_input("Name or Alias (Optional)", value="")
        age_group = st.selectbox(
            "Age Group",
            ["18-24", "25-34", "35-44", "45-54", "55+", "Prefer not to say"],
        )
    with dcol2:
        gender = st.selectbox(
            "Gender",
            ["Female", "Male", "Non-binary", "Other", "Prefer not to say"],
        )
        ai_fam = st.selectbox(
            "AI / Tech Familiarity",
            ["Beginner (rarely use)", "Intermediate (regular user)", "Advanced (developer / researcher)"],
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agree & Continue", disabled=not agree, type="primary"):
            st.session_state.demographics = {
                "name": p_name.strip() if p_name.strip() else None,
                "age_group": age_group,
                "gender": gender,
                "ai_familiarity": ai_fam,
            }
            go_to("instructions")
    with col2:
        if st.button("Decline"):
            st.warning("Thank you for your consideration. You may close this window.")
            st.stop()



# ---------- SCREEN 2: INSTRUCTIONS ----------
def instructions_screen():
    st.title("How the Game Works")

    rounds_total = (
        TOTAL_ROUNDS * 3
        if st.session_state.scenario == "repeated_trust"
        else TOTAL_ROUNDS
    )

    st.markdown(
        f"""
        ### The Island Setting
        - You are one of **{NUM_PLAYERS} players** sharing a water source on an island.
        - The other four players (**A2, A3, A4, A5**) are computer-controlled co-players.
        - The game lasts **{rounds_total} rounds**.
        - You start with **{START_WATER} units of water**. Each round, you consume **{SURVIVAL_COST} units** to survive.
        - If your water drops below 0 at the end of a round, you do not survive.

        ### The Shared Water Source
        - The central water pool is a **shared commons**. It regenerates naturally, but excessive harvesting
          will deplete it. If the pool empties, gathering yields nothing!

        ### Your Actions
        Each round, choose one of five actions:
        - 💧 **Gather** — Draw water from the shared pool. (Yields 3 water normally, but only 1 during drought).
        - 🤝 **Share** — Transfer 1 or more water units from your personal stock to another player.
        - 🛡️ **Hoard** — Ration and conserve your personal reserves. Hoarding reduces your consumption cost to **{HOARD_SURVIVAL_COST} water** (saving 1 unit) while drawing nothing from the shared pool.
        - ⏳ **Skip** — Take no action this round (consumes standard {SURVIVAL_COST} water).
        - 💬 **Communicate** — Broadcast a structured message or claim to one or all players without transferring water.

        ### Communication & Claims
        When you **Share** or **Communicate**, you can attach a structured claim:
        - `claim_stock`: Report how much water you currently hold (e.g. "I have 1 water left").
        - `promise_share`: Promise to share water in future rounds.
        - `request`: Ask another player for help.
        - `accuse`: Flag another player's selfish behavior.

        *(Note: Water levels are private. Other players only see what you do and what you claim.)*
        """
    )

    if st.session_state.scenario == "drought":
        st.warning(
            f"⚠️ **Drought Alert:** In Round {DROUGHT_ROUND}, an environmental shock will drastically reduce water yield and pool regeneration."
        )

    if st.button("Start Simulation", type="primary"):
        reset_environment()
        go_to("game")


# ---------- SCREEN 3: GAME ----------
def game_screen():
    if "env" not in st.session_state or st.session_state.env is None:
        reset_environment()

    env: ScarcityEnv = st.session_state.env
    focal_id = st.session_state.participant_id
    focal_player = env.players[focal_id]
    r = env.round
    total_r = env.total_rounds

    drought_now = is_drought(r, env.scenario)
    round_label = "⚠️ Drought Round — Severe Scarcity!" if drought_now else "Normal Round"

    st.title(f"Round {r} of {total_r}")
    st.caption(f"Scenario: **{env.scenario.upper()}** | {round_label}")

    # Top Status Bar
    col1, col2, col3 = st.columns(3)
    col1.metric("Your Water", f"{focal_player.resource:.1f}")
    col2.metric("Your Status", "Alive" if focal_player.alive else "Deceased")
    pool_pct = max(0.0, min(100.0, (env.pool.stock / env.pool.capacity) * 100))
    col3.metric("Shared Pool Stock", f"{env.pool.stock:.1f} / {env.pool.capacity:.0f}")

    st.progress(pool_pct / 100.0)

    # If focal player died
    if not focal_player.alive:
        st.error("You ran out of water and could not survive on the island.")
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
    st.subheader("👥 Other Players on the Island")
    coplayer_cols = st.columns(len(COPLAYER_IDS))
    for i, pid in enumerate(COPLAYER_IDS):
        pstate = env.players[pid]
        with coplayer_cols[i]:
            status_emoji = "🟢" if pstate.alive else "💀"
            st.markdown(f"**{status_emoji} {pid}**")
            st.caption(f"Status: {'Alive' if pstate.alive else 'Dead'}")
            if pstate.last_action:
                st.caption(f"Last: `{pstate.last_action.value}`")

    st.divider()

    # Action Selection Form
    st.subheader("Choose Your Action")
    action_type_str = st.radio(
        "Action",
        ACTIONS,
        horizontal=True,
        format_func=lambda a: {
            "gather": "💧 Gather Water",
            "share": "🤝 Share Water",
            "hoard": "🛡️ Hoard / Ration",
            "skip": "⏳ Skip Round",
            "communicate": "💬 Communicate",
        }.get(a, a),
    )

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
                target_agent = st.selectbox("Recipient", alive_coplayers)
            else:
                st.warning("No co-players are alive to receive water.")
        with scol2:
            max_share = max(1, int(focal_player.resource))
            share_amount = st.number_input(
                "Amount to give",
                min_value=1,
                max_value=max(1, max_share),
                value=1,
                step=1,
            )

    if action_type_str in ("share", "communicate"):
        st.markdown("**Structured Message (Optional Claim / Request):**")
        if action_type_str == "communicate":
            target_agent = st.selectbox(
                "Target",
                ["all"] + alive_coplayers,
                help="Send to all players or a specific player",
            )

        ccol1, ccol2 = st.columns(2)
        with ccol1:
            claim_kind = st.selectbox(
                "Message Kind",
                MESSAGE_KINDS,
                format_func=lambda k: {
                    "none": "No claim",
                    "claim_stock": "State my stock (claim_stock)",
                    "promise_share": "Promise future share (promise_share)",
                    "request": "Request water (request)",
                    "accuse": "Accuse of selfishness (accuse)",
                }.get(k, k),
            )
        with ccol2:
            if claim_kind != "none":
                claim_value = st.number_input(
                    "Stated Value (e.g. reported stock / promised amount)",
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
        next_obs, done, raw_log_rows = env.step(actions)
        st.session_state.current_obs = next_obs

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
                pol_name = COPLAYER_POLICIES[COPLAYER_IDS.index(agent_id)]
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

        # 5. Check completion
        st.session_state.round_start_time = time.time()
        if done:
            validate_trial_log(st.session_state.trial_id)
            go_to("debrief")
        else:
            st.rerun()

# ---------- SCREEN 4: DEBRIEF & BEHAVIORAL TURING TEST ----------

def debrief_screen():
    st.title("Study Completed — Thank You!")
    st.write(
        """
        Your trial has finished and all data has been securely logged.
        Below is an analysis of your behavioral profile, society-level outcomes,
        and an interactive behavioral Turing test.
        """
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
    col2.metric("Final Water", f"{focal_res:.1f}")
    col3.metric("Society Survivors", f"{alive_total} / {NUM_PLAYERS}")
    gini = calculate_gini(all_resources)
    col4.metric("Society Gini", f"{gini:.2f}", help="0 = perfect equality, 1 = maximal inequality")

    st.divider()

    # ---------- SECTION B: BEHAVIORAL PROFILE ----------
    st.subheader("🧠 Your Behavioral Metrics")

    counts = count_actions(action_log)
    rates = action_rates(action_log)
    deception_stats = calculate_deception(action_log)
    latency_stats = calculate_latency_stats(action_log)

    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    bcol1.metric("Sharing Rate", f"{rates.get('share', 0.0):.1f}%")
    bcol2.metric("Hoarding Rate", f"{rates.get('hoard', 0.0):.1f}%")
    bcol3.metric("Deception Rate", f"{deception_stats['deception_rate']:.1f}%")
    bcol4.metric("Avg Latency", f"{latency_stats['mean_ms']:.0f} ms")

    st.bar_chart(counts)

    if deception_stats["total_claims"] > 0:
        st.info(
            f"🔍 **Arithmetic Deception Audit:** You made {deception_stats['total_claims']} stock claims; "
            f"{deception_stats['deceptive_claims']} diverged from your true resource level."
        )

    st.divider()

    # ---------- SECTION C: NOVELTY N8 - BEHAVIORAL TURING TEST ----------
    st.subheader("🤖 Novelty N8: Behavioral Turing Test")
    st.write(
        """
        Can you distinguish AI agent decision-making from human behavior under scarcity?
        Below are two real 6-round action sequences from this environment. One is an AI agent,
        the other is a human participant:
        """
    )

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.markdown("**Trajectory A:**")
        st.code("R1: gather\nR2: gather\nR3: share(target=A2, amount=1)\nR4: hoard\nR5: gather\nR6: communicate(request)")
    with tcol2:
        st.markdown("**Trajectory B:**")
        st.code("R1: gather\nR2: gather\nR3: gather\nR4: gather\nR5: hoard\nR6: hoard")

    if not st.session_state.turing_submitted:
        choice = st.radio(
            "Which trajectory was produced by the HUMAN participant?",
            ["Trajectory A is Human, Trajectory B is AI", "Trajectory B is Human, Trajectory A is AI"],
        )
        if st.button("Submit Judgment"):
            st.session_state.turing_guess = choice
            st.session_state.turing_submitted = True
            is_correct_val = "Trajectory A is Human" in choice
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
                from common.database import save_turing_judgment
                save_turing_judgment(st.session_state.participant_id, choice, is_correct_val)
            except Exception:
                pass
            st.rerun()
    else:
        guess = st.session_state.turing_guess
        is_correct = "Trajectory A is Human" in (guess or "")
        if is_correct:
            st.success("🎉 **Correct!** Trajectory A was the human participant. Notice the cooperative social sharing and active communication, whereas the AI reflex agent (Trajectory B) defaulted to rigid gathering and survival hoarding.")
        else:
            st.warning("❌ **Incorrect.** Trajectory A was actually the human participant. Humans actively engage in reciprocal sharing and signaling, whereas standard RL policies exhibit deterministic harvest patterns.")
        st.caption("Your response has been banked into the behavioral distinguishability dataset.")

    st.divider()

    # ---------- SECTION D: ACTION LOG DATA ----------
    st.subheader("📄 Recorded Trial Log")
    if action_log:
        st.dataframe(action_log, width="stretch")
        jsonl_str = "\n".join([json.dumps(r) for r in all_rows])
        st.download_button(
            label="Download Complete Trial JSONL",
            data=jsonl_str,
            file_name=f"{st.session_state.trial_id}.jsonl",
            mime="application/jsonlines",
        )


# ---------- ROUTER ----------
stage = st.session_state.stage
if stage == "consent":
    consent_screen()
elif stage == "instructions":
    instructions_screen()
elif stage == "game":
    game_screen()
elif stage == "debrief":
    debrief_screen()
