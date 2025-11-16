import streamlit as st
from pathlib import Path
from PIL import Image
import requests
import os

# Define colors locally
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"

BACKEND_URL = os.environ.get("TRUESIGHT_BACKEND_URL", "http://localhost:5000")


def render_explainability(backend_url):
    """
    Renders the explainability page with Grad-CAM visualization.
    Loads real Grad-CAM data from the most recent completed job.
    """
    
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0 40px 0; 
             background: linear-gradient(135deg, {COLOR_RED} 0%, #8B0000 100%);
             border-radius: 10px; margin-bottom: 30px;">
            <h1 style="color: white; font-size: 2.5rem; margin: 0;">
                ⚠️ MANIPULATION DETECTED
            </h1>
            <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-top: 10px;">
                Displaying forensic heatmap overlay
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get latest completed job with Grad-CAM
    try:
        response = requests.get(f"{backend_url}/jobs")
        response.raise_for_status()
        jobs_data = response.json()
        
        # Find most recent completed job with Grad-CAM
        completed_jobs = [
            job for job in jobs_data.get('jobs', [])
            if job.get('status') == 'completed' and job.get('gradcam_enabled')
        ]
        
        if not completed_jobs:
            st.warning("⚠️ No completed jobs with Grad-CAM available.")
            st.info("💡 Upload a video and wait for analysis to complete.")
            return
        
        # Get the most recent job
        latest_job = completed_jobs[0]
        job_id = latest_job['job_id']
        
        # Fetch full results
        response = requests.get(f"{backend_url}/results/{job_id}")
        response.raise_for_status()
        result = response.json()
        
    except requests.RequestException as e:
        st.error(f"❌ Failed to fetch data: {e}")
        return
    
    # Display job info
    st.markdown(f"**Analyzing Job:** `{job_id}`")
    st.markdown(f"**File:** {result.get('filename', 'Unknown')}")
    st.markdown(f"**Verdict:** {result.get('verdict', 'Unknown')} ({result.get('confidence', 0):.2f}% confidence)")
    
    st.markdown("---")
    
    # Get Grad-CAM directory
    gradcam_dir = Path(result.get('gradcam_dir', ''))
    
    if not gradcam_dir.exists():
        st.error("❌ Grad-CAM visualizations not found.")
        return
    
    # What is Grad-CAM section
    with st.expander("🔬 **What is Grad-CAM?**", expanded=True):
        st.markdown("""
        **Grad-CAM (Gradient-weighted Class Activation Mapping)** is a visualization 
        technique that shows which parts of the video the AI model focused on when 
        making its prediction.
        
        ### How to Read the Heatmaps:
        
        - 🔴 **Red/Orange regions**: Areas the model considered most important
        - 🟡 **Yellow regions**: Moderately important areas
        - 🔵 **Blue/Purple regions**: Less important areas
        - ⚫ **Dark regions**: Background or ignored areas
        
        ### What This Tells Us:
        
        **For Fake Videos:**
        - Model typically focuses on mouth, eyes, and facial edges
        - Strong activations indicate detected manipulation artifacts
        - Concentrated hotspots show specific problem areas
        
        **For Real Videos:**
        - Activations are weaker and more distributed
        - No concentrated hotspots on specific features
        - Model found no suspicious patterns
        
        This transparency helps you understand and trust the AI's decision-making process!
        """)
    
    # Average Heatmap
    avg_heatmap_path = Path(result.get('gradcam_avg_heatmap', ''))
    if avg_heatmap_path.exists():
        st.markdown("### 📊 **Overall Attention Map**")
        st.markdown("*Shows the combined attention across all analyzed frames*")
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            try:
                avg_img = Image.open(avg_heatmap_path)
                st.image(avg_img, caption="Average Grad-CAM Heatmap")
            except Exception as e:
                st.error(f"Error loading average heatmap: {e}")
    
    # Frame-by-frame analysis
    st.markdown("---")
    st.markdown("### 🎞️ **Frame-by-Frame Analysis**")
    
    overlays_dir = gradcam_dir / 'overlays'
    if overlays_dir.exists():
        overlay_files = sorted(list(overlays_dir.glob('frame_*_overlay.jpg')))
        
        if overlay_files:
            st.markdown(f"*Analyzing {len(overlay_files)} frames*")
            
            # Frame scrubber (slider)
            frame_idx = st.slider(
                "Select Frame",
                min_value=0,
                max_value=len(overlay_files) - 1,
                value=0,
                key="frame_scrubber"
            )
            
            # Display selected frame
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                try:
                    frame_img = Image.open(overlay_files[frame_idx])
                    st.image(
                        frame_img,
                        caption=f"Frame {frame_idx} - Grad-CAM Heatmap Overlay"
                    )
                except Exception as e:
                    st.error(f"Error loading frame: {e}")
            
            # Frame info
            st.markdown(f"""
            **Frame {frame_idx} Analysis:**
            - Heatmap overlay shows regions examined by the model
            - Red areas indicate high attention/importance
            - Blue/dark areas indicate low attention
            """)
            
            # Grid view option
            st.markdown("---")
            if st.checkbox("Show all frames in grid", value=False):
                st.markdown("#### All Frames Grid View")
                cols_per_row = 4
                for i in range(0, len(overlay_files), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < len(overlay_files):
                            with col:
                                try:
                                    frame_img = Image.open(overlay_files[idx])
                                    st.image(frame_img, caption=f"Frame {idx}")
                                except Exception as e:
                                    st.error(f"Error: Frame {idx}")
        else:
            st.warning("No overlay images found.")
    else:
        st.error("Overlays directory not found.")
