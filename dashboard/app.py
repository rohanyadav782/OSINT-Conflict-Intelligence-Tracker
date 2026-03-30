"""Main Streamlit dashboard app with multi-page navigation."""
from __future__ import annotations

import sys, os
import importlib

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

import streamlit as st
from pipeline.db import init_db

# Ensure DB and tables exist (critical for cold-start on Streamlit Cloud)
init_db()

st.set_page_config(
    page_title="OSINT Conflict Tracker",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_page(module_name: str):
    """Dynamically import and call a page module's show() function."""
    pages_dir = os.path.join(os.path.dirname(__file__), "pages")
    spec = importlib.util.spec_from_file_location(
        module_name, os.path.join(pages_dir, f"{module_name}.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.show()


def main():
    # Hide sidebar completely
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
            section[data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    # Top navigation tabs
    tabs = st.tabs([
        "Executive Summary",
        "Event Feed",
        "Trends",
        "Map View",
        "Source Analysis",
        "Drill-Down",
    ])

    page_modules = [
        "01_executive_summary",
        "02_event_feed",
        "03_trends",
        "04_map_view",
        "05_source_analysis",
        "06_drill_down",
    ]

    for tab, module_name in zip(tabs, page_modules):
        with tab:
            load_page(module_name)


if __name__ == "__main__":
    main()
