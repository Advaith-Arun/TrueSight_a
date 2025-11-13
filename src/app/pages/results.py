import streamlit as st
import pandas as pd
import requests
from streamlit_app import BACKEND_URL, COLOR_RED, COLOR_GREEN, COLOR_TEXT_BODY
from components.metrics_display import render_processing_metrics

def render_results(backend_url):
    """
    Renders the Analysis Results (if available) and the Job History Dashboard.
    """
    st.markdown(f"## Final Analysis Report & Dashboard", unsafe_allow_html=True)

    # --- 1. ANALYSIS RESULTS SECTION ---
    if st.session_state.job_result:
        result = st.session_state.job_result
        verdict_color = COLOR_GREEN if result['verdict'] == 'Real' else COLOR_RED
        
        st.markdown("---")
        
        # Verdict Card (TYPE_VERDICT - 64px)
        col1, col2 = st.columns([1, 2])
        with col1:
             st.markdown(
                 f"<div class='verdict-readout' style='color:{verdict_color}'>{result['verdict'].upper()}</div>",
                 unsafe_allow_html=True
             )
             st.markdown(f"<p style='color:{COLOR_TEXT_BODY}'>Confidence</p>", unsafe_allow_html=True)
             
        with col2:
             st.markdown(
                 f"<div class='verdict-readout' style='font-size:48px; color:{verdict_color}'>{result['confidence']:.2f}%</div>",
                 unsafe_allow_html=True
             )
             
             # Critical Threshold Display
             st.markdown(
                 f"<p style='color:{COLOR_RED}; font-family:Orbitron; font-size:14px; text-shadow:none;'>CRITICAL: Threshold {result['threshold']} Applied</p>",
                 unsafe_allow_html=True
             )

        # Processing Metrics Display
        render_processing_metrics(result, verdict_color)
        
        # Link to Explainability
        if st.button("View Forensic Visualization", key="view_viz_btn"):
             st.query_params["page"] = "Explainability"
             st.rerun()

        st.markdown("---")
        
    elif st.session_state.current_job_id:
        st.warning(f"Analysis for Job {st.session_state.current_job_id[:8]}... not yet completed or failed to retrieve.")
    
    # --- 2. GLOBAL DASHBOARD SECTION (GET /stats, GET /jobs) ---
    st.markdown(f"## System History & Statistics", unsafe_allow_html=True)
    
    try:
        # Fetch stats
        stats_response = requests.get(f"{backend_url}/stats", timeout=5)
        stats = stats_response.json()
        
        # Display key stats (using Orbitron/Red)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(f"Total Jobs", f"{stats['total_jobs']}")
        with col2: st.metric(f"Completed Jobs", f"{stats['completed_jobs']}")
        with col3: st.metric(f"Real Verdicts", f"{stats['real_videos']}", delta_color="normal", delta_func=lambda x: f"+{x}" if x > 0 else f"{x}")
        with col4: st.metric(f"Fake Verdicts", f"{stats['fake_videos']}", delta_color="inverse", delta_func=lambda x: f"+{x}" if x > 0 else f"{x}")

        # Fetch job history list
        limit = st.selectbox("Jobs per page", [10, 25, 50], index=2)
        status_filter = st.selectbox("Filter by Status", ["all", "completed", "failed", "processing", "queued"], index=0)

        params = {"limit": limit}
        if status_filter != "all":
             params["status"] = status_filter
             
        jobs_response = requests.get(f"{backend_url}/jobs", params=params, timeout=5)
        jobs_data = jobs_response.json()
        
        if jobs_data.get('jobs'):
             df = pd.DataFrame(jobs_data['jobs'])
             # Format for display
             df['job_id'] = df['job_id'].apply(lambda x: x[:8] + '...')
             df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else 'N/A')
             df['processing_time_seconds'] = df['processing_time_seconds'].apply(lambda x: f"{x:.2f}s" if pd.notna(x) else 'N/A')
             
             st.dataframe(df, use_container_width=True)
        else:
             st.info("No jobs found matching the filter.")
             
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to Dashboard API for history/stats.")
    except Exception as e:
        st.error(f"An error occurred loading dashboard data: {e}")