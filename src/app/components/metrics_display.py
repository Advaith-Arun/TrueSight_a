import streamlit as st
from streamlit_app import COLOR_RED, COLOR_GREEN, COLOR_TEXT_BODY

def render_processing_metrics(result, verdict_color):
    """
    Renders key metrics from the job result object (e.g., time, size, raw probability).
    """
    st.markdown(f"### Processing Metrics", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Processing Time
    with col1:
        st.markdown(f"<p style='color:{COLOR_TEXT_BODY}; font-family:Roboto;'>Processing Time</p>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:{verdict_color}; font-family:Orbitron; font-size:24px;'>{result['processing_time_seconds']:.2f}s</div>",
            unsafe_allow_html=True
        )

    # File Size
    with col2:
        st.markdown(f"<p style='color:{COLOR_TEXT_BODY}; font-family:Roboto;'>File Size</p>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:{COLOR_TEXT_BODY}; font-family:Orbitron; font-size:24px;'>{result['file_size_mb']:.2f}MB</div>",
            unsafe_allow_html=True
        )
        
    # Raw Probability (Hidden/Minor display)
    with col3:
        st.markdown(f"<p style='color:{COLOR_TEXT_BODY}; font-family:Roboto;'>Raw Probability</p>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:{COLOR_TEXT_BODY}; font-family:Orbitron; font-size:24px;'>{result['probability']:.4f}</div>",
            unsafe_allow_html=True
        )