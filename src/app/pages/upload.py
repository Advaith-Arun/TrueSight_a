import streamlit as st
import requests
import time
import json
from streamlit_app import BACKEND_URL # Import global variable

def render_upload(backend_url):
    """Handles video file upload, initiates asynchronous processing, and manages polling."""
    st.markdown(f"## New Analysis Request", unsafe_allow_html=True)
    
    # Reset result state when navigating to upload
    if st.session_state.verdict is not None:
         st.session_state.verdict = None
         st.session_state.job_result = None

    uploaded_file = st.file_uploader(
        "Upload Video (MP4, AVI, MOV)",
        type=["mp4", "avi", "mov"],
        accept_multiple_files=False,
        help="Max size 500 MB. File will be deleted after analysis."
    )
    
    st.markdown("---")

    if st.session_state.current_job_id and st.session_state.job_status in ['queued', 'processing']:
        st.info(f"Job **{st.session_state.current_job_id[:8]}** is already running. Monitoring status...")
        poll_status_ui(backend_url)
        return # Block new uploads while polling

    if uploaded_file is not None:
        
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 500:
             st.error("❌ Error 413: File exceeds 500 MB limit.")
             return
        
        st.markdown(f"**File:** {uploaded_file.name} | **Size:** {file_size_mb:.2f} MB")
        
        if st.button("Initiate Analysis (POST /upload)", key="analyze_btn"):
            st.session_state.verdict = None # Clear previous verdict color
            st.session_state.job_result = None # Clear previous result
            
            with st.spinner("Uploading video..."):
                try:
                    # API Call: POST /upload
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
                        st.rerun() # Start polling UI
                    elif response.status_code == 400:
                         st.error(f"❌ Upload Failed (400): {response.json().get('message', 'Invalid file type.')}")
                    else:
                         st.error(f"❌ Upload Failed ({response.status_code}): Server error. Try again.")
                         
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Connection Error: Backend API not reachable at {backend_url}. Please ensure the server is running.")
                except Exception as e:
                    st.exception(f"An unexpected error occurred: {e}")

def poll_status_ui(backend_url):
    """
    Manages the polling loop and progress bar display (Flow A).
    """
    job_id = st.session_state.current_job_id
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    polling_count = 0
    max_wait_time = 600 # 10 minutes (600 seconds)
    start_time = time.time()

    while st.session_state.job_status in ['queued', 'processing'] and (time.time() - start_time < max_wait_time):
        polling_count += 1
        elapsed_time = time.time() - start_time
        
        try:
            # API Call: GET /status/{job_id}
            response = requests.get(f"{backend_url}/status/{job_id}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.job_status = data['status']
                
                # Update UI elements
                with status_placeholder.container():
                    status_color = "#FFC107" if data['status'] == 'queued' else "#E60000"
                    st.markdown(
                        f"**Status:** <span style='color:{status_color}; font-family:Orbitron'>{data['status'].upper()}</span> | **Elapsed Time:** {elapsed_time:.1f}s",
                        unsafe_allow_html=True
                    )
                
                with progress_placeholder:
                    # Progress bar animation is handled by custom CSS (pulsing Red glow)
                    if data['status'] == 'processing':
                         st.progress(0.5) # Arbitrary progress for visual pulse effect
                    else:
                         st.progress(0.0)

            elif response.status_code == 404:
                st.session_state.job_status = 'failed'
                status_placeholder.error(f"❌ Job Not Found (404). ID: {job_id[:8]}...")
                break # Exit loop
                
        except requests.exceptions.RequestException:
             status_placeholder.warning("⚠️ Polling interrupted. Retrying...")
             pass # Will retry after sleep

        time.sleep(2) # Polling interval (2 seconds)

    # --- FINAL RESULT RETRIEVAL ---
    if st.session_state.job_status in ['completed', 'failed']:
        get_results(backend_url, job_id, status_placeholder, progress_placeholder)
        
    elif time.time() - start_time >= max_wait_time:
         status_placeholder.error("❌ Polling Timeout (10 minutes). Worker may have stalled.")
         st.session_state.job_status = 'failed'


def get_results(backend_url, job_id, status_placeholder, progress_placeholder):
    """Fetches the final results and updates global state."""
    progress_placeholder.empty()
    try:
        # API Call: GET /results/{job_id}
        response = requests.get(f"{backend_url}/results/{job_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.job_result = data
            st.session_state.verdict = data['verdict']
            st.session_state.job_status = data['status']
            
            # Successful completion
            status_placeholder.success(f"✅ Analysis complete! Verdict: **{data['verdict'].upper()}**")
            
            # Rerun the app to apply the new verdict theme (Red/Green header glow)
            st.query_params["page"] = "Results / Dashboard"
            st.rerun()

        elif response.status_code == 400 and st.session_state.job_status != 'failed':
            # This should not happen if status=completed/failed, but handles race condition
             status_placeholder.warning("⚠️ Results not ready yet. Trying again...")
             time.sleep(2)
             get_results(backend_url, job_id, status_placeholder, progress_placeholder)
             
        elif response.status_code == 400 and st.session_state.job_status == 'failed':
            # Analysis Failed: retrieve error message
            data = response.json()
            st.session_state.job_result = data
            st.session_state.verdict = 'Fake' # Default to fake/danger theme for failed analysis
            status_placeholder.error(f"❌ Analysis Failed: {data.get('error_message', 'Unknown task error.')}")
            st.query_params["page"] = "Results / Dashboard"
            st.rerun()
            
        else:
            status_placeholder.error(f"❌ Could not retrieve final results (HTTP {response.status_code}).")

    except requests.exceptions.RequestException:
        status_placeholder.error("❌ Failed to connect for final results. Check API health.")