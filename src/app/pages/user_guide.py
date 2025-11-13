import streamlit as st
from pathlib import Path

def render_user_guide():
    """Renders the content of docs/USER_GUIDE.md."""
    st.markdown(f"## TrueSight User Guide", unsafe_allow_html=True)
    st.markdown("---")
    
    guide_path = Path("docs/USER_GUIDE.md")
    
    if guide_path.exists():
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Use st.markdown to render the guide content
            st.markdown(content, unsafe_allow_html=True)
    else:
        st.error("User guide markdown file not found at 'docs/USER_GUIDE.md'.")
        
    # Placeholder content for the guide
    st.markdown("### Placeholder Content (Add detailed guide here)")
    st.markdown("* **Upload:** Max 500 MB, MP4/AVI/MOV only.")
    st.markdown("* **Polling:** Status checks run every 2 seconds.")
    st.markdown("* **Interpretation:** Red theme is FAKE/DANGER. Green theme is REAL/VERIFIED.")