import streamlit as st
from streamlit_app import COLOR_RED, COLOR_GREEN, COLOR_TEXT_BODY
from components.video_player import render_video_player
import numpy as np

# --- PLACEHOLDERS FOR MISSING BACKEND DATA (CRITICAL GAP) ---
# Backend does not yet expose frame images or Grad-CAM heatmaps.
def get_fake_grad_cam_data():
    """Generates placeholder data for the 8 missing Grad-CAM images."""
    if st.session_state.verdict == 'Fake':
        # Create 8 unique placeholder arrays (simulate 224x224 grayscale images)
        return [np.random.rand(224, 224) for _ in range(8)]
    return None

def render_explainability():
    """
    Renders the conditional Explainability (Grad-CAM) visualization page.
    Explainability is ONLY active for FAKE verdicts.
    """
    verdict = st.session_state.verdict
    
    st.markdown(f"## Forensic Visualization & Explainability", unsafe_allow_html=True)
    st.markdown("---")

    if not verdict:
         st.warning("Please run an analysis first on the Upload page.")
         return

    # --- 1. REAL VERDICT (Disabled Explainability) ---
    if verdict == 'Real':
        st.markdown(
            f"<h3 style='color:{COLOR_GREEN}; font-family:Orbitron'>Authenticity Verified</h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='border: 2px solid {COLOR_GREEN}; padding: 30px; border-radius: 10px; text-align: center;'>"+
            f"<p style='color:{COLOR_TEXT_BODY}; font-size:18px;'>No explainability visualizations are required — this video is verified as **Real**.</p>"+
            f"<p style='color:{COLOR_GREEN}; font-family:Roboto;'>The Green theme confirms the system's high confidence in authenticity.</p></div>",
            unsafe_allow_html=True
        )
        # Placeholder for system charts (not visualization)
        # render_metrics_charts() 
        return

    # --- 2. FAKE VERDICT (Active Explainability) ---
    elif verdict == 'Fake':
        st.markdown(
            f"<h3 style='color:{COLOR_RED}; font-family:Orbitron'>Deepfake Artifact Tracing (Grad-CAM)</h3>",
            unsafe_allow_html=True
        )
        
        # Placeholder: Assume Grad-CAM data is retrieved
        grad_cam_data = get_fake_grad_cam_data() 
        if not grad_cam_data:
            st.error("⚠️ CRITICAL: Grad-CAM data not available for this job ID. Backend did not return heatmaps.")
            return

        # Visualization Controls (Red/Black theme)
        col_ctrl, col_viz = st.columns([1, 2])
        
        with col_ctrl:
            st.markdown(f"**Visualization Controls**", unsafe_allow_html=True)
            
            # Overlay Opacity Slider
            overlay_opacity = st.slider(
                "Heatmap Opacity", 0.0, 1.0, 0.7, 0.05,
                help="Adjust the transparency of the Grad-CAM heatmap overlay."
            )
            
            # Frame Scrubber (Simulated for 8 frames)
            frame_index = st.slider(
                "Frame Scrubber (8 Analyzed Frames)", 0, 7, 0, 1,
                help="The model analyzed 8 frames. Scrub to see frame-level artifacts."
            )
            
            # Export Controls
            if st.button("Export Keyframe (PNG)", key="export_frame_btn"):
                 st.info("Exporting keyframe... (Client-side screenshot initiated)")
            
            st.markdown("---")
            st.markdown(f"**Interpretation:** Red areas indicate high model focus/suspicion on fake artifacts (e.g., blending seams, texture inconsistencies).", unsafe_allow_html=True)
        
        # Side-by-Side View (Requires Video Player)
        with col_viz:
            st.markdown(f"**Frame {frame_index + 1} / 8**", unsafe_allow_html=True)
            
            # Placeholder: Video Player is used to show the frame and overlay
            render_video_player(
                video_source=st.session_state.job_result['filename'],
                verdict=verdict,
                current_frame_index=frame_index,
                grad_cam_frames=grad_cam_data,
                opacity=overlay_opacity,
                is_real_source=False # Tells player to display the fake visualization
            )
            
            # Simple Side-by-Side Text
            st.markdown("<p style='text-align:center;'>Side-by-Side View: Processed Crop vs. Heatmap Overlay</p>", unsafe_allow_html=True)