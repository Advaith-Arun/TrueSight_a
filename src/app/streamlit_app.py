import streamlit as st
import os
from pathlib import Path
import time
# Note: For Lottie animation, you'd typically need the streamlit-lottie library.
# We will use HTML/CSS animation placeholders instead for a pure Streamlit/Standard component solution.

# --- CONFIGURATION & GLOBAL SETUP ---
# Backend URL is read from environment variable (Defaults to http://localhost:5000)
BACKEND_URL = os.environ.get("TRUESIGHT_BACKEND_URL", "http://localhost:5000")

# Global UI Tokens (From Step 5)
COLOR_RED = "#E60000"
COLOR_RED_GLOW = "#FF2B2B"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"
COLOR_BACKGROUND = "#000000"
COLOR_CARD_BG = "#080808"
COLOR_WHITE_HIGHLIGHT = "#F6F7F9" # For subtle geometric highlights

# --- GLOBAL STATE MANAGEMENT ---
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'job_result' not in st.session_state:
    st.session_state.job_result = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = 'N/A'
if 'verdict' not in st.session_state:
    st.session_state.verdict = None # Real, Fake, N/A

# --- THEME AND CUSTOM CSS INJECTION (Step 5/6) ---
def inject_global_css():
    """Injects custom CSS for the Red/Black Forensic Aesthetic and Orbitron font."""
    # Determine the color based on final verdict for header glow and accents
    verdict_color = COLOR_RED 
    if st.session_state.verdict == 'Real':
         verdict_color = COLOR_GREEN
    elif st.session_state.verdict is None or st.session_state.verdict == 'N/A':
         verdict_color = COLOR_RED # Default to red if status is unknown/neutral
         
    hover_glow = COLOR_RED_GLOW if verdict_color == COLOR_RED else "#33FF88"

    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@400;700&display=swap');

    /* General Styling */
    .stApp {{
        background-color: {COLOR_BACKGROUND};
        color: {COLOR_TEXT_BODY};
        font-family: 'Roboto', sans-serif;
    }}
    /* Typography */
    h1, h2, h3, h4, .orbitron {{
        font-family: 'Orbitron', sans-serif;
        color: {verdict_color};
        text-shadow: 0 0 10px {verdict_color}44; /* Soft glow effect */
    }}
    h1 {{ font-size: 32px; }}
    /* Main Content Text */
    .stMarkdown, .stText, .stDataFrame, .stTable, label {{
        color: {COLOR_TEXT_BODY};
    }}
    /* Card/Container Style */
    .css-1r6dm7m, .stContainer, .stAlert {{
        background-color: {COLOR_CARD_BG} !important;
        border: 1px solid {verdict_color}33;
        box-shadow: 0 0 10px {verdict_color}33;
        padding: 20px;
        border-radius: 8px;
    }}
    /* Sidebar Navigation Links */
    .sidebar-link {{
        display: block;
        padding: 10px 0;
        margin: 5px 0;
        text-decoration: none;
        font-family: 'Orbitron', sans-serif;
        color: {COLOR_RED};
        transition: all 0.2s ease-in-out;
    }}
    .sidebar-link:hover {{
        color: {COLOR_RED_GLOW};
        text-shadow: 0 0 10px {COLOR_RED_GLOW};
        transform: translateX(5px);
    }}
    /* Active Sidebar Link */
    .sidebar-link.active {{
        color: {verdict_color};
        text-shadow: 0 0 10px {verdict_color}99;
        font-weight: 700;
    }}
    /* Custom Verdict Readout (TYPE_VERDICT - 64px) */
    .verdict-readout {{
        font-family: 'Orbitron', sans-serif;
        font-size: 64px;
        font-weight: 700;
        color: {verdict_color};
        text-shadow: 0 0 20px {verdict_color};
        animation: pulse-readout 2s infinite alternate;
    }}
    /* Primary Buttons */
    div.stButton > button:first-child {{
        background-color: {verdict_color};
        color: {COLOR_BACKGROUND};
        font-family: 'Orbitron', sans-serif;
        border: none;
    }}
    div.stButton > button:first-child:hover {{
        background-color: {hover_glow};
        box-shadow: 0 0 10px {hover_glow};
    }}
    /* Polling/Processing Progress Bar Glow */
    .stProgress > div > div > div > div {{
        background-color: {COLOR_RED};
        box-shadow: 0 0 8px {COLOR_RED_GLOW};
        animation: pulse-progress 1s infinite alternate;
    }}

    @keyframes pulse-progress {{
        0% {{ box-shadow: 0 0 8px {COLOR_RED}55; }}
        100% {{ box-shadow: 0 0 15px {COLOR_RED_GLOW}; }}
    }}
    @keyframes pulse-readout {{
        0% {{ transform: scale(1.0); }}
        100% {{ transform: scale(1.02); }}
    }}

    /* TopNav Header Glow (Simulated) */
    .css-1y4pmho {{ /* Target Streamlit main header container */
        background-color: {COLOR_BACKGROUND};
        border-bottom: 2px solid {verdict_color}55;
        box-shadow: 0 0 15px {verdict_color}99;
    }}
    
    /* Animation Placeholder for cyber aesthetic */
    @keyframes subtle-glow {{
        0% {{ box-shadow: 0 0 5px {COLOR_WHITE_HIGHLIGHT}20; }}
        100% {{ box-shadow: 0 0 15px {COLOR_WHITE_HIGHLIGHT}50; }}
    }}
    .cyber-pattern {{
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: -1;
        opacity: 0.1;
        background: repeating-linear-gradient(45deg, {COLOR_BACKGROUND}, {COLOR_BACKGROUND} 10px, {COLOR_WHITE_HIGHLIGHT}10 10px, {COLOR_WHITE_HIGHLIGHT}10 11px);
        animation: subtle-glow 5s infinite alternate;
    }}

    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# --- NAVIGATION HANDLER ---
PAGES = {
    "Home": "Home", # Use "Home" as the default key for the main view
    "Upload Video": "Upload",
    "Results / Dashboard": "Results / Dashboard",
    "Explainability": "Explainability",
    "User Guide": "User Guide"
}

def navigate_to(page_name):
    """Updates the query parameters to navigate to a new page."""
    st.query_params["page"] = page_name
    st.rerun()

def display_sidebar_nav(current_page_name):
    """Renders the thematic sidebar navigation."""
    st.sidebar.markdown(f"# <span class='orbitron' style='color:{COLOR_RED}'>TrueSight</span>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='color:{COLOR_TEXT_BODY}; font-size:12px;'>AI-Powered Forensics</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    for name in PAGES.keys():
        is_active = (name == current_page_name)
        
        # Determine URL and style for link
        target_name = PAGES[name]
        
        link_class = "sidebar-link active" if is_active else "sidebar-link"
        
        # Streamlit-native way to handle the click (reliable)
        if st.sidebar.button(name, key=f"nav_{name}"):
            navigate_to(target_name)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""<footer style='font-size: 10px; color: #555;'>
            &copy; 2025 TrueSight Forensics.
            <br>Built by AI. For AI.
            </footer>""", 
        unsafe_allow_html=True
    )


# --- HOME PAGE (MAIN VIEW) ---
def render_home_page():
    """Renders the main, centered landing page with the Hero content."""
    
    # Hero Title (Orbitron, large)
    st.markdown(
        f'<div style="text-align: center; padding-top: 100px;">'
        f'<h1 class="orbitron" style="font-size: 72px; color:{COLOR_RED}; margin-bottom: 10px;">TrueSight</h1>'
        f'<p style="color: {COLOR_TEXT_BODY}; font-size: 18px; margin-top: 0; text-shadow: none;">AI-Powered Deepfake Video Detection System.</p>'
        f'</div>', 
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(
            f'<div style="text-align: center; border: 1px solid {COLOR_RED}55; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px {COLOR_RED}55;">'
            f'<p style="color: {COLOR_TEXT_BODY}; font-size: 16px;">'
            f'Leveraging multi-stream analysis (Spatial, Frequency, Spatio-Temporal) '
            f'to achieve 70% accuracy in validating digital media integrity. '
            f'</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(f'<div style="text-align: center; margin-top: 30px;">', unsafe_allow_html=True)
        # Primary Action Button (Red Glow Hover)
        if st.button("Start New Analysis", key="home_upload_btn"):
            navigate_to("Upload Video")
        st.markdown(f'</div>', unsafe_allow_html=True)
        
        # Key Metrics (Simplified)
        st.markdown('<div style="margin-top: 40px;">', unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Model Accuracy", "70%", help="Tested on FaceForensics++")
        with col_m2:
            st.metric("Critical Threshold", "0.3", help="Prediction is FAKE if probability > 0.3")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Footer ---
    st.markdown(
        f"""
        <footer style='text-align: center; position: fixed; bottom: 0; left: 0; right: 0; 
        padding: 10px; font-size: 10px; color: #555; background-color: {COLOR_BACKGROUND};'>
        &copy; 2025 TrueSight | Visual Forensics System
        </footer>
        """,
        unsafe_allow_html=True
    )


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # --- CRITICAL FIX: Changed 'title' to 'page_title' ---
    st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="TrueSight Deepfake Detection")

    # Initial CSS injection before any other Streamlit commands
    inject_global_css()
    
    # Retrieve current page name
    query_params = st.query_params
    current_page_name = query_params.get("page", ["Home"])[0]

    # Render Sidebar Navigation
    display_sidebar_nav(current_page_name)
    
    # Add the subtle cyber pattern background
    st.markdown('<div class="cyber-pattern"></div>', unsafe_allow_html=True)

    # Dynamic page loading based on URL parameter
    if current_page_name == "Home":
        render_home_page()
    elif current_page_name == "Upload":
        from pages.upload import render_upload
        render_upload(BACKEND_URL)
    elif current_page_name == "Results / Dashboard":
        from pages.results import render_results
        render_results(BACKEND_URL)
    elif current_page_name == "Explainability":
        from pages.explainability import render_explainability
        render_explainability()
    elif current_page_name == "User Guide":
        from pages.user_guide import render_user_guide
        render_user_guide()
    else:
        # Fallback to Home page if parameter is invalid
        render_home_page()