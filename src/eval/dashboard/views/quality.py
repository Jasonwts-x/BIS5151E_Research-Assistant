"""
Quality Metrics Page
Quality and accuracy analysis dashboard.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).resolve().parents[3]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def render_quality():
    """Render quality metrics page."""
    st.header("✨ Quality Metrics")
    
    st.markdown("""
    Monitor TruLens evaluation scores and quality metrics.
    """)
    
    # Time period selector
    col1, col2 = st.columns([3, 1])
    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        )
    with col2:
        if st.button("Refresh Data"):
            st.rerun()
    
    st.markdown("---")
    
    # Fetch quality data
    try:
        import requests
        
        response = requests.get("http://eval:8502/metrics/summary", timeout=5)
        response.raise_for_status()
        summary = response.json()
        
        # Quality summary
        st.markdown("### TruLens Scores")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_ground = summary.get("average_groundedness", 0)
            st.metric(
                label="Avg Groundedness",
                value=f"{avg_ground:.2f}" if avg_ground > 0 else "N/A",
                delta=None,
            )
        
        with col2:
            avg_ans_rel = summary.get("average_answer_relevance", 0)
            st.metric(
                label="Avg Answer Relevance",
                value=f"{avg_ans_rel:.2f}" if avg_ans_rel > 0 else "N/A",
                delta=None,
            )
        
        with col3:
            avg_ctx_rel = summary.get("average_context_relevance", 0)
            st.metric(
                label="Avg Context Relevance",
                value=f"{avg_ctx_rel:.2f}" if avg_ctx_rel > 0 else "N/A",
                delta=None,
            )
        
        with col4:
            avg_overall = summary.get("average_overall_score", 0)
            st.metric(
                label="Avg Overall Score",
                value=f"{avg_overall:.2f}" if avg_overall > 0 else "N/A",
                delta=None,
            )
        
        st.markdown("---")
        
        # Get leaderboard for detailed data
        response = requests.get("http://eval:8502/metrics/leaderboard?limit=100", timeout=5)
        response.raise_for_status()
        leaderboard = response.json()
        
        entries = leaderboard.get("entries", [])
        
        if entries:
            # Quality trends chart
            st.markdown("### Quality Trends")
            
            import pandas as pd
            import plotly.graph_objects as go
            
            df = pd.DataFrame(entries)
            
            if "timestamp" in df.columns and "overall_score" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")
                
                fig = go.Figure()
                
                if "groundedness" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["timestamp"],
                        y=df["groundedness"],
                        mode="lines+markers",
                        name="Groundedness",
                    ))
                
                if "answer_relevance" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["timestamp"],
                        y=df["answer_relevance"],
                        mode="lines+markers",
                        name="Answer Relevance",
                    ))
                
                if "context_relevance" in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["timestamp"],
                        y=df["context_relevance"],
                        mode="lines+markers",
                        name="Context Relevance",
                    ))
                
                fig.update_layout(
                    title="TruLens Scores Over Time",
                    xaxis_title="Time",
                    yaxis_title="Score (0-1)",
                    yaxis_range=[0, 1],
                    height=400,
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Score distribution
            st.markdown("### Score Distribution")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "overall_score" in df.columns:
                    import plotly.express as px
                    
                    fig_dist = px.histogram(
                        df,
                        x="overall_score",
                        nbins=20,
                        title="Overall Score Distribution",
                        labels={"overall_score": "Overall Score"},
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
            
            with col2:
                if "groundedness" in df.columns:
                    fig_ground = px.histogram(
                        df,
                        x="groundedness",
                        nbins=20,
                        title="Groundedness Distribution",
                        labels={"groundedness": "Groundedness Score"},
                    )
                    st.plotly_chart(fig_ground, use_container_width=True)
            
            st.markdown("---")
            
            # Recent evaluations
            st.markdown("### Recent Evaluations")
            
            qual_df = pd.DataFrame([
                {
                    "Query": entry.get("query", "")[:50] + "...",
                    "Overall Score": f"{entry.get('overall_score', 0):.2f}",
                    "Groundedness": f"{entry.get('groundedness', 0):.2f}",
                    "Answer Relevance": f"{entry.get('answer_relevance', 0):.2f}",
                    "Context Relevance": f"{entry.get('context_relevance', 0):.2f}",
                    "Timestamp": entry.get("timestamp", ""),
                }
                for entry in entries[:20]
            ])
            
            st.dataframe(qual_df, use_container_width=True)
            
            st.markdown("---")
            
            # Top/Bottom performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Top Performing Queries")
                top_df = pd.DataFrame([
                    {
                        "Query": entry.get("query", "")[:40] + "...",
                        "Score": f"{entry.get('overall_score', 0):.2f}",
                    }
                    for entry in entries[:10]
                ])
                st.dataframe(top_df, use_container_width=True)
            
            with col2:
                st.markdown("#### Lowest Scoring Queries")
                sorted_entries = sorted(entries, key=lambda x: x.get("overall_score", 0))
                bottom_df = pd.DataFrame([
                    {
                        "Query": entry.get("query", "")[:40] + "...",
                        "Score": f"{entry.get('overall_score', 0):.2f}",
                    }
                    for entry in sorted_entries[:10]
                ])
                st.dataframe(bottom_df, use_container_width=True)
        else:
            st.info("No quality data available yet. Run some queries to see metrics here!")
    
    except Exception as e:
        st.error(f"Failed to load quality data: {e}")
        st.info("Make sure the evaluation service is running on port 8502")