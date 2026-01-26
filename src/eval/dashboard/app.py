"""
Main Dashboard Application
Streamlit app for evaluation monitoring.
"""
from __future__ import annotations

import logging

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ResearchAssistant Evaluation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("📊 ResearchAssistant Evaluation Dashboard")
st.markdown("---")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Overview", "Performance Metrics", "Quality Metrics", "Leaderboard"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This dashboard monitors the quality and performance 
    of the ResearchAssistant AI system.
    
    **Metrics tracked:**
    - TruLens (groundedness, relevance)
    - Guardrails (safety, citations)
    - Performance (timing, resources)
    - Quality (ROUGE, BLEU)
    """
)

# Page routing
if page == "Overview":
    from .pages.overview import render_overview
    render_overview()

elif page == "Performance Metrics":
    from .pages.performance import render_performance
    render_performance()

elif page == "Quality Metrics":
    from .pages.quality import render_quality
    render_quality()

elif page == "Leaderboard":
    st.header("🏆 Evaluation Leaderboard")
    st.info("Coming soon: Leaderboard of top-performing queries")
    
    # TODO: Implement leaderboard
    st.markdown("### Top 10 Queries by Overall Score")
    st.dataframe({
        "Rank": [],
        "Query": [],
        "Overall Score": [],
        "Groundedness": [],
        "Relevance": [],
        "Total Time (s)": [],
    })