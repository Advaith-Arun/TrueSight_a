"""
Upload Page - Video Upload with Auto-Status Polling
Styled with Orbitron font and custom cyberpunk aesthetic
"""

import streamlit as st
import requests
import time

# Color constants (matching main app)
COLOR_RED = "#E60000"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"
COLOR_CARD_BG = "#080808"

def render_upload(backend_url):
    """
    Renders the upload page with file uploader and auto-status polling.
    Integrates with backend POST /upload and GET /status endpoints.
    """
    
    # --- PAGE HEADER ---
    st.markdown("""
        <div style='text-align: center; padding: 30px 0;'>
            <h2 style='font-family: Orbitron, sans-serif; color: #E60000; 
                 text-shadow: 0 0 15px #E6000080; font-size: 2.5rem;'>
                📤 New Analysis Request
            </h2>
            <p style='color: #888; font-size: 1.1rem; margin-top: 10px;'>
                Upload a video file to detect deepfake manipulation using our AI ensemble
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- FILE UPLOADER SECTION ---
    st.markdown("""
        <div style='background: #080808; padding: 20px; border-radius: 10px; 
             border: 1px solid #E6000040; margin-bottom: 20px;'>
            <h3 style='font-family: Orbitron; color: #E60000; margin-bottom: 10px;'>
                Upload Video (MP4, AVI, MOV)
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "avi", "mov"],
        help="Maximum file size: 500MB",
        key="upload_file_input",
        label_visibility="collapsed"
    )
    
    # --- FILE INFO DISPLAY ---
    if uploaded_file:
        # Store file in session state
        st.session_state.uploaded_file = uploaded_file
        
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.session_state.file_size_mb = file_size_mb
        st.session_state.filename = uploaded_file.name
        
        # Display file details in styled card
        st.markdown(f"""
            <div style='background: {COLOR_CARD_BG}; padding: 15px; border-radius: 8px; 
                 border-left: 4px solid {COLOR_GREEN}; margin: 20px 0;'>
                <p style='margin: 0; color: {COLOR_TEXT_BODY};'>
                    <strong>File:</strong> {uploaded_file.name}<br>
                    <strong>Size:</strong> {file_size_mb:.2f} MB
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Video preview (optional expandable)
        with st.expander("🎬 Preview Video", expanded=False):
            st.video(uploaded_file)
        
        st.markdown("---")
        
        # --- UPLOAD BUTTON ---
        if st.button(
            "🚀 Initiate Analysis (POST /upload)",
            type="primary",
            use_container_width=True,
            key="upload_submit_btn"
        ):
            # --- UPLOAD PROCESS ---
            with st.spinner("📤 Uploading video to backend..."):
                try:
                    # Prepare file for upload (backend expects 'video' key)
                    files = {
                        'video': (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }
                    
                    # POST to /upload endpoint
                    response = requests.post(
                        f"{backend_url}/upload",
                        files=files,
                        timeout=60
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Extract job_id
                    job_id = result.get('job_id')
                    
                    if not job_id:
                        st.error("❌ Upload failed: No job ID received from backend")
                        st.stop()
                    
                    # Store job_id in session state
                    st.session_state.current_job_id = job_id
                    st.session_state.job_status = 'processing'
                    
                    st.success(f"✅ Upload successful! **Job ID:** `{job_id}`")
                    
                except requests.exceptions.Timeout:
                    st.error("❌ Upload timeout: Backend did not respond in time")
                    st.stop()
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Upload failed: {str(e)}")
                    st.info("💡 Ensure backend is running at: " + backend_url)
                    st.stop()
            
            # --- AUTO-POLLING STATUS ---
            st.markdown("---")
            st.markdown("""
                <h3 style='font-family: Orbitron; color: #E60000; text-shadow: 0 0 10px #E6000080;'>
                    🔄 Processing Status (Auto-Polling)
                </h3>
            """, unsafe_allow_html=True)
            
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            max_retries = 120  # 4 minutes max (2 sec intervals)
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # GET /status/{job_id}
                    status_response = requests.get(
                        f"{backend_url}/status/{st.session_state.current_job_id}",
                        timeout=10
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    job_status = status_data.get('status', 'unknown')
                    
                    if job_status == 'processing':
                        status_placeholder.info(
                            f"⏳ **Processing...** ({retry_count * 2}s elapsed)"
                        )
                        progress_bar.progress(min(retry_count / max_retries, 0.9))
                        st.session_state.job_status = 'processing'
                        
                    elif job_status == 'completed':
                        status_placeholder.success("✅ **Analysis completed!**")
                        progress_bar.progress(1.0)
                        st.session_state.job_status = 'completed'
                        
                        # ✅ FIX: Navigate to Results page
                        time.sleep(1)
                        st.balloons()
                        st.query_params["page"] = "Results / Dashboard"
                        st.rerun()
                        
                    elif job_status == 'failed':
                        error_msg = status_data.get('error', 'Unknown error')
                        status_placeholder.error(f"❌ **Processing failed:** {error_msg}")
                        st.session_state.job_status = 'failed'
                        break
                    
                    else:
                        status_placeholder.warning(f"⚠️ **Unknown status:** {job_status}")
                    
                    time.sleep(2)
                    retry_count += 1
                    
                except requests.exceptions.RequestException as e:
                    status_placeholder.error(f"❌ **Status check failed:** {str(e)}")
                    break
            
            # Timeout warning
            if retry_count >= max_retries:
                status_placeholder.warning(
                    "⚠️ Processing is taking longer than expected. "
                    "Check **Results / Dashboard** page manually."
                )
    
    else:
        # No file uploaded
        st.info("ℹ️ **Please upload a video file to begin analysis.**")
    
    # --- INSTRUCTIONS SECTION ---
    st.markdown("---")
    st.markdown("""
        <div style='background: #080808; padding: 20px; border-radius: 10px; 
             border: 1px solid #E6000040;'>
            <h3 style='font-family: Orbitron; color: #E60000;'>📖 Instructions</h3>
            <ol style='color: #E0E0E0; line-height: 1.8;'>
                <li><strong>Upload</strong> a video file (MP4, AVI, or MOV format)</li>
                <li><strong>Click</strong> "Initiate Analysis" to start processing</li>
                <li><strong>Wait</strong> for auto-polling to complete (~10-30 seconds)</li>
                <li><strong>View</strong> results automatically when processing finishes</li>
            </ol>
            <p style='color: #888; margin-top: 15px;'>
                <strong>Note:</strong> Maximum file size is 500 MB. 
                Processing time varies based on video length and complexity.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- BACKEND INTEGRATION INFO (DEBUG) ---
    with st.expander("🔧 Backend Integration Details", expanded=False):
        st.code(f"""
Endpoint: POST {backend_url}/upload
Expected Response: {{"job_id": "...", "status": "processing", "message": "..."}}

Status Polling: GET {backend_url}/status/<job_id>
Expected Response: {{"job_id": "...", "status": "processing|completed|failed", "verdict": "..."}}

File Key: 'video' (not 'file')
Max File Size: 500 MB
Allowed Extensions: .mp4, .avi, .mov
        """)
