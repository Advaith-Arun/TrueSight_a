import streamlit as st
import requests
import time
import json
import os

# Define BACKEND_URL locally (no import from streamlit_app)
BACKEND_URL = os.environ.get("TRUESIGHT_BACKEND_URL", "http://localhost:5000")

def render_upload(backend_url):
    """Handles video file upload, initiates asynchronous processing, and manages polling."""
    st.markdown(f"<h2 style='font-family: Orbitron;'>New Analysis Request</h2>", unsafe_allow_html=True)
    
    # Reset result state when navigating to upload
    if 'verdict' in st.session_state and st.session_state.verdict is not None:
        st.session_state.verdict = None
        st.session_state.job_result = None

    uploaded_file = st.file_uploader(
        "Upload Video (MP4, AVI, MOV)",
        type=["mp4", "avi", "mov"],
        accept_multiple_files=False,
        help="Max size 500 MB. File will be deleted after analysis."
    )
    
    st.markdown("---")
    
    if st.session_state.get('current_job_id') and st.session_state.get('job_status') in ['queued', 'processing']:
        st.info(f"Job **{st.session_state.current_job_id[:8]}** is already running. Monitoring status...")
        poll_status_ui(backend_url)
        return  # Block new uploads while polling
    
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 500:
            st.error("❌ Error 413: File exceeds 500 MB limit.")
            return
        
        st.markdown(f"**File:** {uploaded_file.name} | **Size:** {file_size_mb:.2f} MB")
        
        if st.button("Initiate Analysis (POST /upload)", key="analyze_btn"):
            st.session_state.verdict = None
            st.session_state.job_result = None
            
            with st.spinner("Uploading video..."):
                try:
                    files = {'video': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{backend_url}/upload", files=files, timeout=30)
                    
                    if response.status_code == 202:
                        data = response.json()
                        st.session_state.current_job_id = data.get('job_id')
                        st.session_state.job_status = data.get('status')
                        st.session_state.filename = data.get('filename')
                        st.session_state.file_size_mb = data.get('file_size_mb')
                        st.success(f"✅ Upload successful. Job ID: **{data['job_id'][:8]}...**")
                        time.sleep(1)
                        st.rerun()
                    elif response.status_code == 400:
                        st.error(f"❌ Upload Failed (400): {response.json().get('message', 'Invalid file type.')}")
                    else:
                        st.error(f"❌ Upload Failed ({response.status_code}): Server error. Try again.")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Connection Error: Backend API not reachable at {backend_url}. Please ensure the server is running.")
                except Exception as e:
                    st.exception(f"An unexpected error occurred: {e}")

def poll_status_ui(backend_url):
    """Manages the polling loop and progress bar display."""
    job_id = st.session_state.current_job_id
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    max_wait_time = 600  # 10 minutes
    start_time = time.time()
    
    while st.session_state.job_status in ['queued', 'processing'] and (time.time() - start_time < max_wait_time):
        elapsed_time = time.time() - start_time
        
        try:
            response = requests.get(f"{backend_url}/status/{job_id}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.job_status = data['status']
                
                with status_placeholder.container():
                    st.markdown(f"**Status:** {data['status'].upper()} | **Elapsed Time:** {elapsed_time:.1f}s")
                
                with progress_placeholder:
                    if data['status'] == 'processing':
                        st.progress(0.5)
                    else:
                        st.progress(0.0)
            elif response.status_code == 404:
                st.session_state.job_status = 'failed'
                status_placeholder.error(f"❌ Job Not Found (404). ID: {job_id[:8]}...")
                break
        except requests.exceptions.RequestException:
            status_placeholder.warning("⚠️ Polling interrupted. Retrying...")
            pass
        
        time.sleep(2)
    
    if st.session_state.job_status in ['completed', 'failed']:
        get_results(backend_url, job_id, status_placeholder, progress_placeholder)
    elif time.time() - start_time >= max_wait_time:
        status_placeholder.error("❌ Polling Timeout (10 minutes). Worker may have stalled.")
        st.session_state.job_status = 'failed'

def get_results(backend_url, job_id, status_placeholder, progress_placeholder):
    """Fetches the final results and updates global state."""
    progress_placeholder.empty()
    
    try:
        response = requests.get(f"{backend_url}/results/{job_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.job_result = data
            st.session_state.verdict = data['verdict']
            st.session_state.job_status = data['status']
            
            status_placeholder.success(f"✅ Analysis complete! Verdict: **{data['verdict'].upper()}**")
            st.query_params["page"] = "Results / Dashboard"
            st.rerun()
        elif response.status_code == 400 and st.session_state.job_status == 'failed':
            data = response.json()
            st.session_state.job_result = data
            st.session_state.verdict = 'Fake'
            status_placeholder.error(f"❌ Analysis Failed: {data.get('error_message', 'Unknown error')}")
            st.query_params["page"] = "Results / Dashboard"
            st.rerun()
    except requests.exceptions.RequestException:
        status_placeholder.error("❌ Failed to connect for final results. Check API health.")
