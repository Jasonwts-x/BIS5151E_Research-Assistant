"""
Evaluation Dashboard
Streamlit app for monitoring evaluation metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# CRITICAL FIX: Add src directory to Python path for absolute imports
src_path = Path(__file__).resolve().parents[2]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now use absolute imports
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
    
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Performance", "Quality", "Leaderboard"],
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
    elif page == "Performance":
        render_performance()
    elif page == "Quality":
        render_quality()
    elif page == "Leaderboard":
        st.title("📋 Evaluation Leaderboard")
        
        try:
            import requests
            import pandas as pd
            
            response = requests.get("http://eval:8502/metrics/leaderboard?limit=50", timeout=5)
            response.raise_for_status()
            leaderboard = response.json()
            
            entries = leaderboard.get("entries", [])
            
            if entries:
                df = pd.DataFrame([
                    {
                        "Rank": i + 1,
                        "Query": entry.get("query", "")[:60] + "...",
                        "Overall Score": f"{entry.get('overall_score', 0):.3f}",
                        "Groundedness": f"{entry.get('groundedness', 0):.3f}",
                        "Answer Relevance": f"{entry.get('answer_relevance', 0):.3f}",
                        "Context Relevance": f"{entry.get('context_relevance', 0):.3f}",
                        "Time (s)": f"{entry.get('total_time', 0):.2f}",
                        "Timestamp": entry.get("timestamp", ""),
                    }
                    for i, entry in enumerate(entries)
                ])
                
                st.dataframe(df, use_container_width=True, height=600)
            else:
                st.info("No evaluations yet. Run some queries to see the leaderboard!")
        
        except Exception as e:
            st.error(f"Failed to load leaderboard: {e}")
            st.info("Make sure the evaluation service is running on port 8502")


if __name__ == "__main__":
    main()