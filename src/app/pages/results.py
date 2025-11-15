import streamlit as st
import pandas as pd
import requests
import os
import sys
from pathlib import Path

# Add components directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "components"))

from metrics_display import render_processing_metrics

# Define constants locally
BACKEND_URL = os.environ.get("TRUESIGHT_BACKEND_URL", "http://localhost:5000")
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"

def render_results(backend_url):
    """Renders the Analysis Results and Job History Dashboard."""
    st.markdown(f"<h2 style='font-family: Orbitron;'>Final Analysis Report & Dashboard</h2>", unsafe_allow_html=True)
    
    # Analysis Results Section
    if st.session_state.get('job_result'):
        result = st.session_state.job_result
        
        # ✅ FIXED: Check if verdict exists (job completed successfully)
        if result.get('verdict'):
            verdict_color = COLOR_GREEN if result['verdict'] == 'Real' else COLOR_RED
            
            st.markdown("---")
            
            # Verdict Card
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(
                    f"<div style='font-family: Orbitron; font-size: 64px; color: {verdict_color}; text-shadow: 0 0 20px {verdict_color};'>{result['verdict']}</div>"
                    f"<p style='color:{COLOR_TEXT_BODY};'>Confidence: {result['confidence']}%</p>",
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f"<p style='color:{verdict_color}; font-family: Orbitron;'>✓ CRITICAL: Threshold {result.get('threshold', 0.5)} Applied</p>",
                    unsafe_allow_html=True
                )
            
            # Processing Metrics
            render_processing_metrics(result, verdict_color)
            
            # Link to Explainability
            if st.button("View Forensic Visualization", key="view_viz_btn"):
                st.query_params["page"] = "Explainability"
                st.rerun()
        
        else:
            # ✅ NEW: Handle failed jobs gracefully
            st.error("❌ Analysis Failed")
            
            error_msg = result.get('error_message', 'Unknown error occurred')
            st.markdown(f"""
            <div style='background-color: #2B0000; padding: 20px; border-radius: 10px; border-left: 4px solid {COLOR_RED};'>
                <h3 style='color: {COLOR_RED}; font-family: Orbitron;'>Error Details</h3>
                <p style='color: {COLOR_TEXT_BODY};'>{error_msg}</p>
                
                <h4 style='color: {COLOR_RED}; margin-top: 20px;'>Possible Causes:</h4>
                <ul style='color: {COLOR_TEXT_BODY};'>
                    <li>No faces detected in video</li>
                    <li>Video file corrupted or unreadable</li>
                    <li>Unsupported video format</li>
                    <li>Processing timeout</li>
                </ul>
                
                <p style='color: {COLOR_TEXT_BODY}; margin-top: 20px;'>
                    <strong>Suggestion:</strong> Try uploading a different video with clear, frontal face views.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Dashboard Section
    st.markdown(f"<h2 style='font-family: Orbitron;'>System History & Statistics</h2>", unsafe_allow_html=True)
    
    try:
        stats_response = requests.get(f"{backend_url}/stats", timeout=5)
        stats = stats_response.json()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Jobs", f"{stats['total_jobs']}")
        with col2:
            st.metric("Completed Jobs", f"{stats['completed_jobs']}")
        with col3:
            st.metric("Real Verdicts", f"{stats['real_videos']}")
        with col4:
            st.metric("Fake Verdicts", f"{stats['fake_videos']}")
        
        limit = st.selectbox("Jobs per page", [10, 25, 50], index=2)
        status_filter = st.selectbox("Filter by Status", ["all", "completed", "failed", "processing", "queued"], index=0)
        
        params = {"limit": limit}
        if status_filter != "all":
            params["status"] = status_filter
        
        jobs_response = requests.get(f"{backend_url}/jobs", params=params, timeout=5)
        jobs_data = jobs_response.json()
        
        if jobs_data.get('jobs'):
            df = pd.DataFrame(jobs_data['jobs'])
            df['job_id'] = df['job_id'].apply(lambda x: x[:8] + '...')
            
            # ✅ FIXED: Handle None values in confidence column
            df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and x is not None else 'N/A')
            df['processing_time_seconds'] = df['processing_time_seconds'].apply(lambda x: f"{x:.2f}s" if pd.notna(x) and x is not None else 'N/A')
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No jobs found matching the filter.")
    
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to Dashboard API for history/stats.")
