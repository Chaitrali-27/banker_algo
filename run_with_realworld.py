"""Launcher: runs the ORIGINAL app.py exactly as it is, and adds one extra
tab ("Real-World Use") at the far left. app.py is not modified.

Run with:  python -m streamlit run run_with_realworld.py
"""
import runpy
from pathlib import Path
import streamlit as st
from real_world import render_real_world_tab

_original_tabs = st.tabs


def _tabs_with_realworld(labels, *args, **kwargs):
    # Only touch the main tab bar of the dashboard (it starts with "Overview").
    if list(labels)[:1] != ["Overview"]:
        return _original_tabs(labels, *args, **kwargs)
    all_tabs = _original_tabs(["Real-World Use"] + list(labels), *args, **kwargs)
    with all_tabs[0]:
        render_real_world_tab()
    return all_tabs[1:]          # app.py receives exactly the tabs it expects


st.tabs = _tabs_with_realworld
runpy.run_path(str(Path(__file__).parent / "app.py"), run_name="__main__")
