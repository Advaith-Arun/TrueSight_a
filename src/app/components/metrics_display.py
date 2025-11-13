import streamlit as st

# Define colors locally (no import from streamlit_app to avoid circular import)
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"

def render_processing_metrics(result, verdict_color):
    """
    Displays processing metrics in a clean card format.
    
    Args:
        result: Dictionary with job results from backend
        verdict_color: Color to use for styling (red or green)
    """
    st.markdown(f"<h3 style='color:{verdict_color}; font-family: Orbitron;'>Processing Metrics</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Filename",
            value=result.get('filename', 'N/A')
        )
    
    with col2:
        st.metric(
            label="File Size",
            value=f"{result.get('file_size_mb', 0):.2f} MB"
        )
    
    with col3:
        st.metric(
            label="Processing Time",
            value=f"{result.get('processing_time_seconds', 0):.2f}s"
        )
    
    # Additional details
    st.markdown(f"""
    <div style='background-color: #080808; padding: 15px; border-radius: 10px; border-left: 3px solid {verdict_color};'>
        <p style='color: {COLOR_TEXT_BODY}; margin: 5px 0;'>
            <strong>Job ID:</strong> {result.get('job_id', 'N/A')[:16]}...
        </p>
        <p style='color: {COLOR_TEXT_BODY}; margin: 5px 0;'>
            <strong>Upload Time:</strong> {result.get('upload_timestamp', 'N/A')}
        </p>
        <p style='color: {COLOR_TEXT_BODY}; margin: 5px 0;'>
            <strong>Completion Time:</strong> {result.get('completion_timestamp', 'N/A')}
        </p>
        <p style='color: {COLOR_TEXT_BODY}; margin: 5px 0;'>
            <strong>Raw Probability:</strong> {result.get('probability', 0):.4f}
        </p>
    </div>
    """, unsafe_allow_html=True)
