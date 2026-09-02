"""
app.py — Group 1 (Sujal & Utkarsh)

Streamlit interface for the human side of the scarcity study.
Flow: consent -> instructions -> game (multiple rounds) -> debrief

Run locally with:  streamlit run human_interface/app.py
"""

import streamlit as st
import uuid
from logging_utils import log_action

# ---------- CONFIG (keep in sync with agents/environment.py in Group 2) ----------
GRID_SIZE = 5
TOTAL_ROUNDS = 10
DROUGHT_ROUND = 6
NUM_AGENTS_ON_ISLAND = 5  # includes the human participant
SCENARIO = "drought"
ACTIONS = ["gather", "share", "hoard", "move", "skip"]

st.set_page_config(page_title="Scarcity Study", layout="centered")

# ---------- SESSION STATE INIT ----------
if "stage" not in st.session_state:
    st.session_state.stage = "consent"
if "trial_id" not in st.session_state:
    st.session_state.trial_id = f"{SCENARIO}_human_{uuid.uuid4().hex[:6]}"
if "participant_id" not in st.session_state:
    st.session_state.participant_id = f"P{uuid.uuid4().hex[:4].upper()}"
if "round" not in st.session_state:
    st.session_state.round = 1
if "resource" not in st.session_state:
    st.session_state.resource = 5
if "alive" not in st.session_state:
    st.session_state.alive = True
if "action_log" not in st.session_state:
    st.session_state.action_log = []


def go_to(stage):
    st.session_state.stage = stage
    st.rerun()


# ---------- SCREEN 1: CONSENT ----------
def consent_screen():
    st.title("Research Study: Resource Decisions Under Scarcity")
    st.write(
        """
        You are invited to take part in a short research study (10-15 minutes)
        about how people make decisions when resources are limited.

        **What you'll do:** play a short round-based game where you manage a
        resource (e.g. water) shared with a few other players, and decide
        whether to gather, share, hoard, or communicate with others.

        **What we record:** your in-game actions and any messages you send
        to other players during the game. No personally identifying
        information is collected — you are assigned an anonymous ID.

        **Voluntary participation:** you may stop at any time without
        penalty. Your data will be used only for academic research purposes
        and reported in aggregate.
        """
    )
    agree = st.checkbox("I have read the above and agree to participate.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Agree & Continue", disabled=not agree, type="primary"):
            go_to("instructions")
    with col2:
        if st.button("Decline"):
            st.warning("Thank you for your time. You may close this window.")
            st.stop()


# ---------- SCREEN 2: INSTRUCTIONS ----------
def instructions_screen():
    st.title("How the Game Works")
    st.write(
        f"""
        - You are one of **{NUM_AGENTS_ON_ISLAND} players** on a small island.
        - The game lasts **{TOTAL_ROUNDS} rounds**. Each round you need
          **2 units of water** to survive.
        - Available actions each round:
            - **Gather** — collect water from the shared source
            - **Share** — give some of your water to another player
            - **Hoard** — keep all your water, take no other action
            - **Move** — reposition on the island (may reveal new resources)
            - **Skip** — take no action this round
        - You may also send a short message to another player when you
          share or communicate.
        - Water availability changes over time — pay attention each round.

        There are no right or wrong answers. Please play naturally, as you
        actually would in this situation.
        """
    )
    if st.button("Start Game", type="primary"):
        go_to("game")


# ---------- SCREEN 3: GAME ----------
def game_screen():
    r = st.session_state.round
    is_drought = r == DROUGHT_ROUND
    scenario_label = "⚠️ Drought — water is scarce this round" if is_drought else "Normal round"

    st.title(f"Round {r} / {TOTAL_ROUNDS}")
    st.caption(scenario_label)

    col1, col2 = st.columns(2)
    col1.metric("Your water", st.session_state.resource)
    col2.metric("Status", "Alive" if st.session_state.alive else "Not surviving")

    if not st.session_state.alive:
        st.error("You ran out of water and could not continue.")
        if st.button("Continue to Debrief"):
            go_to("debrief")
        return

    st.divider()
    st.subheader("Choose your action")

    action = st.radio("Action", ACTIONS, horizontal=True, label_visibility="collapsed")

    target = None
    message = None
    if action == "share":
        target = st.selectbox(
            "Share with which player?",
            [f"A{i}" for i in range(1, NUM_AGENTS_ON_ISLAND) if f"A{i}" != st.session_state.participant_id],
        )
        message = st.text_input("Optional message to them")

    if st.button("Submit Action", type="primary"):
        resource_before = st.session_state.resource

        # --- simplified resource logic (mirror agents/environment.py rules) ---
        if action == "gather":
            gained = 1 if is_drought else 3
            st.session_state.resource += gained
        elif action == "share":
            st.session_state.resource -= 1
        elif action == "hoard":
            pass
        elif action == "move":
            pass
        elif action == "skip":
            pass

        st.session_state.resource -= 2  # survival cost per round
        st.session_state.alive = st.session_state.resource >= 0

        record = log_action(
            trial_id=st.session_state.trial_id,
            agent_id=st.session_state.participant_id,
            round_num=r,
            scenario=SCENARIO,
            action_type=action,
            resource_before=resource_before,
            resource_after=st.session_state.resource,
            alive=st.session_state.alive,
            target_agent=target,
            message_sent=message,
        )
        st.session_state.action_log.append(record)

        if r >= TOTAL_ROUNDS or not st.session_state.alive:
            go_to("debrief")
        else:
            st.session_state.round += 1
            st.rerun()


# ---------- SCREEN 4: DEBRIEF ----------
def debrief_screen():
    st.title("Thank You")
    st.write(
        """
        That's the end of the study. Thank you for participating.

        **About this study:** we're comparing how AI agents and human
        participants behave when facing the same resource-scarcity
        situations, to understand where AI decision-making diverges from
        human decision-making. Your anonymized actions help us measure
        this.

        If you have questions about this research, please contact the
        research team via your guide/instructor.
        """
    )
    st.subheader("Your session summary")
    st.write(f"Participant ID: `{st.session_state.participant_id}`")
    st.write(f"Rounds completed: {st.session_state.round}")
    st.write(f"Final water level: {st.session_state.resource}")
    st.dataframe(st.session_state.action_log)


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
