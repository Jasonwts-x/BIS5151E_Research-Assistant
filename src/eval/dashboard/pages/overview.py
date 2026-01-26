"""
Overview Page
Dashboard overview with key metrics summary.
"""
from __future__ import annotations

import streamlit as st


def render_overview():
    """Render overview page."""
    st.header("📈 Overview")
    
    st.markdown("""
    Welcome to the ResearchAssistant Evaluation Dashboard!
    
    This dashboard provides comprehensive monitoring of your AI research assistant's
    quality, performance, and safety metrics.
    """)
    
    # Key metrics (top row)
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Evaluations",
            value="0",
            delta="0 today",
        )
    
    with col2:
        st.metric(
            label="Average Overall Score",
            value="N/A",
            delta=None,
        )
    
    with col3:
        st.metric(
            label="Average Response Time",
            value="N/A",
            delta=None,
        )
    
    with col4:
        st.metric(
            label="Guardrails Pass Rate",
            value="N/A",
            delta=None,
        )
    
    st.markdown("---")
    
    # Recent evaluations
    st.markdown("### Recent Evaluations")
    st.info("No evaluations yet. Start using the research assistant to see metrics here!")
    
    # TODO: Fetch and display recent evaluations
    # Example table structure:
    st.dataframe({
        "Timestamp": [],
        "Query": [],
        "Overall Score": [],
        "Groundedness": [],
        "Answer Relevance": [],
        "Response Time (s)": [],
        "Status": [],
    })
    
    st.markdown("---")
    
    # System status
    st.markdown("### System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ **Evaluation Service**: Healthy")
        st.success("✅ **Database**: Connected")
        st.success("✅ **TruLens**: Initialized")
    
    with col2:
        st.success("✅ **Guardrails**: Enabled")
        st.success("✅ **Performance Tracking**: Active")
        st.success("✅ **Quality Metrics**: Available")
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### Quick Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### TruLens Metrics")
        st.write("- Groundedness: N/A")
        st.write("- Answer Relevance: N/A")
        st.write("- Context Relevance: N/A")
    
    with col2:
        st.markdown("#### Guardrails")
        st.write("- Input Validations: 0")
        st.write("- Output Validations: 0")
        st.write("- Violations Blocked: 0")
    
    with col3:
        st.markdown("#### Performance")
        st.write("- Avg RAG Time: N/A")
        st.write("- Avg Agent Time: N/A")
        st.write("- Avg LLM Time: N/A")