"""
Evaluation Dashboard
Streamlit app for monitoring evaluation metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# CRITICAL FIX: Add src directory to Python path for absolute imports
# This is necessary because Streamlit runs files directly, not as modules
src_path = Path(__file__).resolve().parents[2]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now use absolute imports instead of relative imports
try:
    from eval.dashboard.pages.overview import render_overview
    from eval.dashboard.pages.performance import render_performance
    from eval.dashboard.pages.quality import render_quality
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure you're running this from the project root: streamlit run src/eval/dashboard/app.py")
    st.stop()


def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="ResearchAssistant Evaluation Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Select Page")
    
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Performance Metrics", "Quality Metrics", "Leaderboard"],
        label_visibility="collapsed"
    )

    # About section
    st.sidebar.markdown("---")
    st.sidebar.markdown("## About")
    st.sidebar.info(
        "This dashboard monitors the quality and performance of the "
        "ResearchAssistant AI system."
    )
    
    st.sidebar.markdown("### Metrics tracked:")
    st.sidebar.markdown("- TruLens (groundedness, relevance)")
    st.sidebar.markdown("- Guardrails (safety, citations)")
    st.sidebar.markdown("- Performance (timing, resources)")
    st.sidebar.markdown("- Quality (ROUGE, BLEU)")

    # Render selected page
    if page == "Overview":
        render_overview()
    elif page == "Performance Metrics":
        render_performance()
    elif page == "Quality Metrics":
        render_quality()
    elif page == "Leaderboard":
        st.title("📋 Evaluation Leaderboard")
        st.info("Leaderboard coming soon - shows top-performing queries")


if __name__ == "__main__":
    main()