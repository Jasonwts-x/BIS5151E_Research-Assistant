"""
Evaluation Dashboard
Streamlit app for monitoring evaluation metrics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add src directory to Python path for absolute imports
src_path = Path(__file__).resolve().parents[2]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import page render functions
try:
    from eval.dashboard.views.overview import render_overview
    from eval.dashboard.views.performance import render_performance
    from eval.dashboard.views.quality import render_quality
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure you're running from the project root")
    st.stop()


def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="Research Assistant - Evaluation Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Title
    st.sidebar.title("📊 Evaluation Dashboard")
    st.sidebar.markdown("**Research Assistant GPT**")
    st.sidebar.markdown("---")
    
    # Navigation
    st.sidebar.markdown("### Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Performance Metrics", "Quality Metrics", "Leaderboard"],
        label_visibility="collapsed",
    )

    # About section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This dashboard monitors the quality and performance of the "
        "Research-Assistant AI system."
    )
    
    st.sidebar.markdown("#### Metrics Tracked")
    st.sidebar.markdown("• **TruLens**: Groundedness, relevance, citations")
    st.sidebar.markdown("• **Guardrails**: Safety, policy compliance")
    st.sidebar.markdown("• **Performance**: Timing, resources")
    st.sidebar.markdown("• **Quality**: ROUGE, BLEU, similarity")
    
    # Quick stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    
    try:
        import requests
        response = requests.get("http://eval:8502/metrics/summary", timeout=3)
        if response.status_code == 200:
            summary = response.json()
            total = summary.get("total_evaluations", 0)
            avg_score = summary.get("average_overall_score", 0)
            
            st.sidebar.metric("Total Evaluations", f"{total}")
            st.sidebar.metric("Avg Score", f"{avg_score:.2f}" if avg_score > 0 else "N/A")
        else:
            st.sidebar.warning("⚠️ Cannot connect to eval service")
    except Exception:
        st.sidebar.warning("⚠️ Eval service offline")

    # Render selected page
    if page == "Overview":
        render_overview()
    elif page == "Performance Metrics":
        render_performance()
    elif page == "Quality Metrics":
        render_quality()
    elif page == "Leaderboard":
        render_leaderboard()


def render_leaderboard():
    """Render leaderboard page."""
    st.title("📋 Evaluation Leaderboard")
    st.markdown("Top-performing queries ranked by overall evaluation score.")
    
    # Controls
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.selectbox("Show top", [10, 25, 50, 100], index=1)
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.markdown("---")
    
    try:
        import requests
        import pandas as pd
        
        response = requests.get(
            f"http://eval:8502/metrics/leaderboard?limit={limit}",
            timeout=5
        )
        response.raise_for_status()
        leaderboard = response.json()
        
        entries = leaderboard.get("entries", [])
        
        if entries:
            # Create dataframe
            df = pd.DataFrame([
                {
                    "🏆 Rank": i + 1,
                    "Query": entry.get("query", "")[:80] + ("..." if len(entry.get("query", "")) > 80 else ""),
                    "Overall Score": f"{entry.get('overall_score', 0):.3f}",
                    "Groundedness": f"{entry.get('groundedness', 0):.3f}",
                    "Answer Rel.": f"{entry.get('answer_relevance', 0):.3f}",
                    "Context Rel.": f"{entry.get('context_relevance', 0):.3f}",
                    "Timestamp": pd.to_datetime(entry.get("timestamp", "")).strftime("%Y-%m-%d %H:%M"),
                }
                for i, entry in enumerate(entries)
            ])
            
            # Display with styling
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                hide_index=True,
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="evaluation_leaderboard.csv",
                mime="text/csv",
            )
            
        else:
            st.info("📭 No evaluations yet. Run some research queries to see the leaderboard!")
            st.markdown("""
            **To generate evaluations:**
            1. Run a research query: `POST /research/query`
            2. Wait for execution (~30-60 seconds)
            3. Refresh this page to see results
            """)
    
    except requests.RequestException as e:
        st.error(f"❌ Failed to load leaderboard: {e}")
        st.info("Make sure the evaluation service is running on port 8502")
    except Exception as e:
        st.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()