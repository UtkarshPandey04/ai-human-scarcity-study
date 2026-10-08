"""
dashboard/app.py — Interactive Researcher & Model Training Dashboard (Authenticated)
"""

from __future__ import annotations

import os
import sys
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(
    page_title="Scarcity Study — Researcher Dashboard & Model Hub",
    page_icon="🔬",
    layout="wide",
)

import importlib
import dashboard.researcher_hub
importlib.reload(dashboard.researcher_hub)
from dashboard.researcher_hub import render_researcher_hub

render_researcher_hub(embedded=False)
