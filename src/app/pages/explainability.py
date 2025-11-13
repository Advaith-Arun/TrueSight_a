import streamlit as st
import numpy as np
import cv2

# Define colors locally
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"

def render_explainability(backend_url):
    """
    Renders the explainability page with Grad-CAM visualization.
    Only shown when verdict is 'Fake' (placeholder for now).
    """
    st.markdown(f"<h2 style='font-family: Orbitron; color: {COLOR_RED};'>Forensic Visualization</h2>", unsafe_allow_html=True)
    
    if st.session_state.get('verdict') == 'Real':
        st.success("✅ **Authenticity Verified**")
        st.info("This video passed all forensic checks. No manipulation artifacts detected.")
        st.markdown("---")
        st.markdown("""
        ### Why No Visualization?
        Real (authentic) videos do not exhibit the telltale patterns that deepfake models look for.
        Grad-CAM heatmaps are only generated for videos classified as **Fake**, where we can
        highlight suspicious regions (e.g., around the mouth, eyes, or facial boundaries).
        """)
        return
    
    elif st.session_state.get('verdict') != 'Fake':
        st.warning("⚠️ No analysis results available yet. Please upload and analyze a video first.")
        return
    
    # FAKE verdict - Show explainability
    st.markdown(f"""
    <p style='color: {COLOR_RED}; font-family: Orbitron;'>
    ⚠️ MANIPULATION DETECTED | Displaying forensic heatmap overlay
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown("### Frame-by-Frame Analysis")
    st.info("🔬 **Note**: Grad-CAM visualization is currently using placeholder data. Full implementation pending model finalization.")
    
    # Generate placeholder Grad-CAM data (8 frames)
    grad_cam_frames = []
    for i in range(8):
        heatmap = np.random.rand(224, 224)
        grad_cam_frames.append(heatmap)
    
    # Simple frame scrubber
    frame_idx = st.slider("Select Frame", min_value=0, max_value=7, value=0, key="frame_scrubber")
    
    # Display heatmap
    heatmap_data = grad_cam_frames[frame_idx]
    heatmap_rgb = cv2.applyColorMap((heatmap_data * 255).astype(np.uint8), cv2.COLORMAP_JET)
    
    st.image(heatmap_rgb, caption=f"Frame {frame_idx + 1}/8 - Grad-CAM Heatmap", use_column_width=True)
    
    # Explainability controls
    st.markdown("---")
    st.markdown("### Analysis Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        opacity = st.slider("Heatmap Opacity", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        st.info(f"Current opacity: {opacity}")
    
    with col2:
        show_grid = st.checkbox("Show Grid Overlay", value=False)
        if show_grid:
            st.success("Grid overlay enabled")
    
    # Export options
    st.markdown("---")
    st.markdown("### Export Options")
    
    if st.button("📸 Export Current Frame (PNG)", key="export_png"):
        st.info("Screenshot export functionality coming soon!")
    
    if st.button("📊 Generate Analysis Report (PDF)", key="export_pdf"):
        st.info("PDF report generation coming soon!")
