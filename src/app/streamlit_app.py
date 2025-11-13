import streamlit as st
import os
from pathlib import Path
import time
import sys

# --- CONFIGURATION & GLOBAL SETUP ---
BACKEND_URL = os.environ.get("TRUESIGHT_BACKEND_URL", "http://localhost:5000")

# Global UI Tokens
COLOR_RED = "#E60000"
COLOR_RED_GLOW = "#FF2B2B"
COLOR_GREEN = "#00C853"
COLOR_TEXT_BODY = "#E0E0E0"
COLOR_BACKGROUND = "#000000"
COLOR_CARD_BG = "#080808"
COLOR_WHITE_HIGHLIGHT = "#F6F7F9"

# --- GLOBAL STATE MANAGEMENT ---
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'job_result' not in st.session_state:
    st.session_state.job_result = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = 'N/A'
if 'verdict' not in st.session_state:
    st.session_state.verdict = None
if 'filename' not in st.session_state:
    st.session_state.filename = None
if 'file_size_mb' not in st.session_state:
    st.session_state.file_size_mb = None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TrueSight | Forensic Digital Authenticator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DYNAMIC THEME STYLING (CRITICAL VERDICT-BASED COLOR CHANGE) ---
def get_theme_color():
    """Returns the primary accent color based on the current verdict."""
    if st.session_state.verdict == 'Fake':
        return COLOR_RED
    elif st.session_state.verdict == 'Real':
        return COLOR_GREEN
    else:
        return COLOR_RED  # Default to Red/Black theme before verdict

theme_color = get_theme_color()

# Inject custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto:wght@300;400;500&display=swap');
    
    /* Global Styles */
    .stApp {{
        background-color: {COLOR_BACKGROUND};
        color: {COLOR_TEXT_BODY};
        font-family: 'Roboto', sans-serif;
    }}
    
    /* Headers */
    h1, h2, h3 {{
        font-family: 'Orbitron', sans-serif;
        color: {theme_color};
        text-shadow: 0 0 10px {theme_color}80;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_CARD_BG};
        border-right: 2px solid {theme_color};
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {theme_color};
        color: {COLOR_BACKGROUND};
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {COLOR_RED_GLOW if theme_color == COLOR_RED else COLOR_GREEN};
        box-shadow: 0 0 20px {theme_color};
    }}
    
    /* Verdict Display */
    .verdict-readout {{
        font-family: 'Orbitron', sans-serif;
        font-size: 64px;
        font-weight: 900;
        color: {theme_color};
        text-shadow: 0 0 30px {theme_color};
        animation: pulse-glow 2s infinite;
    }}
    
    @keyframes pulse-glow {{
        0%, 100% {{ text-shadow: 0 0 20px {theme_color}; }}
        50% {{ text-shadow: 0 0 40px {theme_color}; }}
    }}
    
    /* Cards */
    .css-1r6slb0 {{
        background-color: {COLOR_CARD_BG};
        border: 1px solid {theme_color}40;
        border-radius: 10px;
    }}
    
    /* Progress Bar */
    .stProgress > div > div {{
        background-color: {theme_color};
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER WITH FLASH ANIMATION ON VERDICT ---
if st.session_state.verdict:
    st.markdown(f"""
    <h1 style='text-align: center; animation: flash-once 0.5s;'>
        🔍 TrueSight | Forensic Digital Authenticator
    </h1>
    <style>
        @keyframes flash-once {{
            0% {{ opacity: 0; }}
            50% {{ opacity: 1; text-shadow: 0 0 50px {theme_color}; }}
            100% {{ opacity: 1; text-shadow: 0 0 20px {theme_color}; }}
        }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <h1 style='text-align: center;'>
        🔍 TrueSight | Forensic Digital Authenticator
    </h1>
    """, unsafe_allow_html=True)

st.markdown(f"<p style='text-align: center; color: {COLOR_TEXT_BODY}; font-size: 14px;'>Advanced AI-Powered Deepfake Detection & Forensic Analysis</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown(f"<h2 style='color: {theme_color}; font-family: Orbitron;'>Navigation</h2>", unsafe_allow_html=True)

page_options = [
    "Upload Video",
    "Results / Dashboard",
    "Explainability",
    "User Guide"
]

# Use query params for navigation
if "page" not in st.query_params:
    st.query_params["page"] = "Upload Video"

current_page = st.query_params["page"]

# Sidebar navigation buttons
for page in page_options:
    if st.sidebar.button(page, key=f"nav_{page}", use_container_width=True):
        st.query_params["page"] = page
        st.rerun()

# Display current page indicator
st.sidebar.markdown(f"**Current Page:** {current_page}")

# System Status Indicator
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color: {theme_color}; font-family: Orbitron;'>System Status</h3>", unsafe_allow_html=True)

try:
    import requests
    health_response = requests.get(f"{BACKEND_URL}/health", timeout=2)
    if health_response.status_code == 200:
        st.sidebar.success("✅ Backend API: Online")
    else:
        st.sidebar.error("❌ Backend API: Offline")
except:
    st.sidebar.error("❌ Backend API: Unreachable")

if st.session_state.current_job_id:
    st.sidebar.info(f"**Active Job:** {st.session_state.current_job_id[:8]}...")
    st.sidebar.info(f"**Status:** {st.session_state.job_status}")

# --- IMPORT PAGE MODULES (FIXED - NO CIRCULAR IMPORTS) ---
# Add pages and components directories to Python path
pages_path = Path(__file__).parent / "pages"
components_path = Path(__file__).parent / "components"
sys.path.insert(0, str(pages_path))
sys.path.insert(0, str(components_path))

# Import page render functions
try:
    from upload import render_upload
    from results import render_results
    from explainability import render_explainability
    from user_guide import render_user_guide
except ImportError as e:
    st.error(f"❌ Failed to import page modules: {e}")
    st.error("Make sure all page files exist in src/app/pages/")
    st.stop()

# --- PAGE ROUTING ---
if current_page == "Upload Video":
    render_upload(BACKEND_URL)
elif current_page == "Results / Dashboard":
    render_results(BACKEND_URL)
elif current_page == "Explainability":
    render_explainability(BACKEND_URL)
elif current_page == "User Guide":
    render_user_guide()
else:
    st.error(f"Unknown page: {current_page}")

# --- FOOTER ---
st.markdown("---")
st.markdown(f"""
<p style='text-align: center; color: {COLOR_TEXT_BODY}; font-size: 12px;'>
    TrueSight v1.0 | Powered by Deep Learning Ensemble Architecture | 
    <a href='#' style='color: {theme_color};'>Documentation</a>
</p>
""", unsafe_allow_html=True)
