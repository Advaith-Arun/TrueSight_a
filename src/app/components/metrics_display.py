import streamlit as st

# Define colors locally (no import from streamlit_app to avoid circular import)
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"

# src/app/components/metrics_display.py

def render_processing_metrics(result, verdict_color):
    """Render processing metrics with safe None handling."""
    
    # Safe get with defaults
    processing_time = result.get('processing_time_seconds')
    probability = result.get('probability')
    threshold = result.get('threshold', 0.5)
    
    # Format processing time
    if processing_time is None or processing_time == 0:
        time_str = 'N/A'
    else:
        time_str = f"{processing_time:.2f}s"
    
    # Format probability
    if probability is None:
        prob_str = 'N/A'
    elif probability == 0:
        prob_str = '< 0.01%'  # Show as "less than" instead of 0
    else:
        prob_str = f"{probability * 100:.2f}%"
    
    st.markdown(f"""
    <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; margin-top: 20px;'>
        <h3 style='color: {verdict_color}; font-family: Orbitron;'>Processing Metrics</h3>
        <p style='color: #E0E0E0;'>
            <strong>Processing Time:</strong> {time_str}<br>
            <strong>Raw Probability:</strong> {prob_str}<br>
            <strong>Decision Threshold:</strong> {threshold * 100:.0f}%
        </p>
    </div>
    """, unsafe_allow_html=True)

