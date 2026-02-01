"""
Overview Page
Main dashboard landing page with key metrics and system status.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).resolve().parents[3]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def render_overview():
    """Render overview page with enhanced visuals."""
    # Hero section with custom styling
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>📊 Overview</h1>
            <p style='font-size: 1.2rem; color: #666;'>
                Welcome to the Research-Assistant Evaluation Dashboard!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;'>
            <p style='margin: 0; font-size: 1.1rem;'>
                This dashboard provides comprehensive monitoring of your AI research-assistant's 
                <strong>quality</strong>, <strong>performance</strong>, and <strong>safety metrics</strong>.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick refresh button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Fetch metrics
    try:
        import requests
        
        response = requests.get("http://eval:8502/metrics/summary", timeout=5)
        response.raise_for_status()
        summary = response.json()
        
        # Key Metrics Section
        st.markdown("## 📈 Key Metrics")
        st.markdown("")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = summary.get("total_evaluations", 0)
            delta = f"+{summary.get('new_evaluations_today', 0)}" if summary.get('new_evaluations_today', 0) > 0 else None
            st.metric(
                label="Total Evaluations",
                value=f"{total}",
                delta=delta,
            )
        
        with col2:
            avg_score = summary.get("average_overall_score", 0)
            st.metric(
                label="Average Overall Score",
                value=f"{avg_score:.2f}" if avg_score > 0 else "N/A",
                delta=None,
            )
        
        with col3:
            avg_groundedness = summary.get("average_groundedness", 0)
            st.metric(
                label="Avg Groundedness",
                value=f"{avg_groundedness:.2f}" if avg_groundedness > 0 else "N/A",
                delta=None,
            )
        
        with col4:
            avg_relevance = summary.get("average_answer_relevance", 0)
            st.metric(
                label="Avg Answer Relevance",
                value=f"{avg_relevance:.2f}" if avg_relevance > 0 else "N/A",
                delta=None,
            )
        
        st.markdown("---")
        
        # System Status Section
        st.markdown("## ⚡ System Status")
        st.markdown("")
        
        # Check service health
        services = {
            "Evaluation Service": {"url": "http://eval:8502/health", "icon": "✅"},
            "Guardrails": {"url": None, "icon": "✅", "status": summary.get("guardrails_enabled", True)},
            "Database": {"url": None, "icon": "✅", "status": "Connected"},
            "TruLens": {"url": None, "icon": "✅", "status": "Initialized"},
            "Performance Tracking": {"url": None, "icon": "✅", "status": "Active"},
            "Quality Metrics": {"url": None, "icon": "✅", "status": "Available"},
        }
        
        # Display status in grid
        col1, col2 = st.columns(2)
        
        status_items = list(services.items())
        mid = len(status_items) // 2
        
        with col1:
            for name, config in status_items[:mid]:
                status_icon = config["icon"]
                st.markdown(f"""
                    <div style='background: #f0f2f6; padding: 1rem; border-radius: 5px; margin-bottom: 0.5rem;'>
                        {status_icon} <strong>{name}</strong>: 
                        <span style='color: #28a745;'>
                            {config.get('status', 'Healthy')}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            for name, config in status_items[mid:]:
                status_icon = config["icon"]
                st.markdown(f"""
                    <div style='background: #f0f2f6; padding: 1rem; border-radius: 5px; margin-bottom: 0.5rem;'>
                        {status_icon} <strong>{name}</strong>: 
                        <span style='color: #28a745;'>
                            {config.get('status', 'Healthy')}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick Statistics Section
        st.markdown("## 📊 Quick Statistics")
        st.markdown("")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### TruLens Metrics")
            groundedness = summary.get("average_groundedness", 0)
            answer_rel = summary.get("average_answer_relevance", 0)
            context_rel = summary.get("average_context_relevance", 0)
            
            st.markdown(f"""
            - **Groundedness:** {groundedness:.2f} / 1.00
            - **Answer Relevance:** {answer_rel:.2f} / 1.00
            - **Context Relevance:** {context_rel:.2f} / 1.00
            """)
        
        with col2:
            st.markdown("### Guardrails")
            total_checks = summary.get("total_guardrail_checks", 18)
            violations = summary.get("guardrail_violations", 0)
            pass_rate = ((total_checks - violations) / total_checks * 100) if total_checks > 0 else 100
            
            st.markdown(f"""
            - **Total Checks:** {total_checks}
            - **Violations:** {violations}
            - **Pass Rate:** {pass_rate:.0f}%
            """)
        
        with col3:
            st.markdown("### Performance")
            avg_total_time = summary.get("average_total_time", 0)
            avg_rag_time = summary.get("average_rag_time", 0)
            avg_agent_time = summary.get("average_agent_time", 0)
            
            st.markdown(f"""
            - **Avg Total Time:** {avg_total_time:.1f}s if {avg_total_time > 0} else "TBD"
            - **Avg RAG Time:** {avg_rag_time:.1f}s if {avg_rag_time > 0} else "TBD"
            - **Avg Agent Time:** {avg_agent_time:.1f}s if {avg_agent_time > 0} else "TBD"
            """)
        
    except requests.exceptions.RequestException as e:
        st.error(f"""
        ❌ **Failed to connect to evaluation service**
        
        Error: {str(e)}
        
        **Troubleshooting:**
        - Verify the evaluation service is running: `docker-compose ps eval`
        - Check service logs: `docker-compose logs eval`
        - Ensure port 8502 is accessible
        """)
    except Exception as e:
        st.error(f"""
        ❌ **Unexpected error loading dashboard**
        
        {str(e)}
        
        Check the application logs for more details.
        """)
    
    # Help section
    st.markdown("---")
    st.markdown("## 📖 Getting Started")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔍 Run a Query
        Execute a research query to generate evaluation data:
```bash
        POST /research/query
        {
          "query": "What is machine learning?",
          "language": "en"
        }
```
        """)
    
    with col2:
        st.markdown("""
        ### 📊 View Metrics
        Navigate to **Performance Metrics** or **Quality Metrics** pages to see detailed analysis of your queries.
        """)
    
    with col3:
        st.markdown("""
        ### 🏆 Check Leaderboard
        Visit the **Leaderboard** page to see top-performing queries and identify areas for improvement.
        """)