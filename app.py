"""
app.py — Unified Deployment Entry Point for Streamlit Community Cloud
URL: https://ai-human-scarcity-study.streamlit.app/

Routes seamlessly between:
1. Participant Experiment Interface (default) — human_interface/app.py
2. Researcher Hub & Model Analysis — dashboard/app.py (accessed via ?mode=researcher or sidebar switch)
"""

from __future__ import annotations

import os
import runpy
import sys
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Force clean module cache on every reload so deployed updates take effect immediately
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("dashboard") or mod_name.startswith("human_interface"):
        sys.modules.pop(mod_name, None)

# Check query parameter for mode selection (?mode=researcher or ?mode=study)
query_mode = st.query_params.get("mode", "").lower()

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

# Sidebar mode switcher (collapsible for participants)
with st.sidebar:
    if query_mode == "researcher":
        app_mode = "Researcher Hub & Analysis"
    else:
        app_mode = st.radio(
            "Navigation",
            ["Participant Study", "Researcher Hub & Analysis"],
            index=0,
            label_visibility="collapsed",
        )

if app_mode == "Researcher Hub & Analysis" or query_mode == "researcher":
    target_path = os.path.join(PROJECT_ROOT, "dashboard", "app.py")
else:
    target_path = os.path.join(PROJECT_ROOT, "human_interface", "app.py")

# Execute target script in __main__ namespace for full Streamlit reactivity
runpy.run_path(target_path, run_name="__main__")
