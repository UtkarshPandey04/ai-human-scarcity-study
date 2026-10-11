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

try:
    st.set_page_config(
        page_title="AI-Human Scarcity Study",
        page_icon="🏝️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

# Hide Streamlit top-right menu and toolbar while keeping the sidebar toggle button accessible and prominent
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbarActions"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    .viewerBadge_link__qRIco {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    button[title="View app source"] {display: none !important;}
    a[href*="github.com"] {display: none !important;}

    /* Make sure the toolbar holding the expand button is always visible */
    [data-testid="stToolbar"] {
        visibility: visible !important;
        display: flex !important;
        background: transparent !important;
    }

    /* Ensure the sidebar open toggle button is prominent and always accessible */
    [data-testid="stExpandSidebarButton"],
    button[data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 9999999 !important;
        background: #0284c7 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.6) !important;
        cursor: pointer !important;
    }
    [data-testid="stExpandSidebarButton"]:hover,
    button[data-testid="stExpandSidebarButton"]:hover {
        transform: scale(1.08) !important;
        background: #0369a1 !important;
    }
    [data-testid="stExpandSidebarButton"] svg,
    button[data-testid="stExpandSidebarButton"] svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
        width: 24px !important;
        height: 24px !important;
    }
    </style>
    <img src="data:image/svg+xml;utf8,<svg></svg>" onerror="
        try {
            for (var i = 0; i < localStorage.length; i++) {
                var k = localStorage.key(i);
                if (k && k.indexOf('stSidebarCollapsed') !== -1) {
                    localStorage.setItem(k, 'false');
                }
            }
            function triggerSidebarOpen() {
                var sidebar = document.querySelector('section[data-testid=\\'stSidebar\\']');
                var isClosed = !sidebar || sidebar.getAttribute('aria-expanded') === 'false';
                if (isClosed) {
                    var btn = document.querySelector('[data-testid=\\'stExpandSidebarButton\\']') ||
                              document.querySelector('button[data-testid=\\'stExpandSidebarButton\\']') ||
                              document.querySelector('[data-testid=\\'collapsedControl\\'] button') ||
                              document.querySelector('[data-testid=\\'stSidebarCollapsedControl\\'] button') ||
                              document.querySelector('button[aria-label=\\'Expand sidebar\\']');
                    if (btn) btn.click();
                }
            }
            setTimeout(triggerSidebarOpen, 50);
            setTimeout(triggerSidebarOpen, 300);
            setTimeout(triggerSidebarOpen, 800);
        } catch(e) {}
    " style="display:none;" />
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
