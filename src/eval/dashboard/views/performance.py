"""
Performance Metrics Page
Performance and timing analysis dashboard.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).resolve().parents[3]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def render_performance():
    """Render performance metrics page."""
    st.header("⚡ Performance Metrics")
    
    st.markdown("""
    Monitor system performance, timing, and resource usage.
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
    
    # Fetch performance data
    try:
        import requests
        
        response = requests.get("http://eval:8502/metrics/summary", timeout=5)
        response.raise_for_status()
        summary = response.json()
        
        # Performance summary
        st.markdown("### Performance Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_total = summary.get("average_total_time", 0)
            st.metric(
                label="Avg Total Time",
                value=f"{avg_total:.2f}s" if avg_total > 0 else "N/A",
                delta=None,
            )
        
        with col2:
            avg_rag = summary.get("average_rag_time", 0)
            st.metric(
                label="Avg RAG Time",
                value=f"{avg_rag:.2f}s" if avg_rag > 0 else "N/A",
                delta=None,
            )
        
        with col3:
            avg_agent = summary.get("average_agent_time", 0)
            st.metric(
                label="Avg Agent Time",
                value=f"{avg_agent:.2f}s" if avg_agent > 0 else "N/A",
                delta=None,
            )
        
        with col4:
            avg_llm = summary.get("average_llm_time", 0)
            st.metric(
                label="Avg LLM Time",
                value=f"{avg_llm:.2f}s" if avg_llm > 0 else "N/A",
                delta=None,
            )
        
        st.markdown("---")
        
        # Get leaderboard for detailed data
        response = requests.get("http://eval:8502/metrics/leaderboard?limit=50", timeout=5)
        response.raise_for_status()
        leaderboard = response.json()
        
        entries = leaderboard.get("entries", [])
        
        if entries:
            # Timing breakdown chart
            st.markdown("### Timing Breakdown")
            
            import pandas as pd
            import plotly.express as px
            
            df = pd.DataFrame(entries)
            if "total_time" in df.columns:
                fig_timing = px.bar(
                    df.head(10),
                    x="query",
                    y="total_time",
                    title="Query Execution Time (Top 10)",
                    labels={"total_time": "Time (seconds)", "query": "Query"},
                )
                st.plotly_chart(fig_timing, use_container_width=True)
            
            st.markdown("---")
            
            # Resource usage
            st.markdown("### Resource Usage")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_memory = summary.get("average_memory_mb", 0)
                st.metric(
                    label="Avg Memory (MB)",
                    value=f"{avg_memory:.0f}" if avg_memory > 0 else "N/A",
                    delta=None,
                )
            
            with col2:
                avg_tokens = summary.get("average_token_count", 0)
                st.metric(
                    label="Avg Token Count",
                    value=f"{avg_tokens:.0f}" if avg_tokens > 0 else "N/A",
                    delta=None,
                )
            
            with col3:
                total_evals = summary.get("total_evaluations", 0)
                st.metric(
                    label="Total Queries",
                    value=f"{total_evals}",
                    delta=None,
                )
            
            st.markdown("---")
            
            # Recent queries performance
            st.markdown("### Recent Queries Performance")
            
            perf_df = pd.DataFrame([
                {
                    "Query": entry.get("query", "")[:50] + "...",
                    "Total Time (s)": entry.get("total_time", 0),
                    "Timestamp": entry.get("timestamp", ""),
                }
                for entry in entries[:20]
            ])
            
            st.dataframe(perf_df, use_container_width=True)
            
            st.markdown("---")
            
            # Slowest queries
            st.markdown("### Slowest Queries (Top 10)")
            
            sorted_entries = sorted(entries, key=lambda x: x.get("total_time", 0), reverse=True)
            slow_df = pd.DataFrame([
                {
                    "Query": entry.get("query", "")[:50] + "...",
                    "Total Time (s)": entry.get("total_time", 0),
                    "Timestamp": entry.get("timestamp", ""),
                }
                for entry in sorted_entries[:10]
            ])
            
            st.dataframe(slow_df, use_container_width=True)
        else:
            st.info("No performance data available yet. Run some queries to see metrics here!")
    
    except Exception as e:
        st.error(f"Failed to load performance data: {e}")
        st.info("Make sure the evaluation service is running on port 8502")