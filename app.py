import streamlit as st
from supabase_client import supabase
from auth import login_register_page
from timer import pomodoro_ui
from analytics import show_dashboard
from url_session_manager import (
    is_authenticated, 
    get_current_user, 
    clear_session_from_url,
    load_session_from_url
)

def initialize_session():
    """Initialize session state variables"""
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True

def main():
    st.set_page_config(page_title="Pomodash", layout="wide")

    # Custom CSS for responsiveness
    st.markdown("""
    <style>
    /* Remove Streamlit footer */
    footer {visibility: hidden;}

    /* Responsive content wrapper */
    .responsive-wrapper {
        padding: 1rem;
        max-width: 100%;
        margin: auto;
    }

    /* Responsive columns */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }

    .logout-button {
        text-align: right;
        margin-top: 0.5rem;
    }

    /* Mobile adjustments */
    @media screen and (max-width: 768px) {
        .top-bar {
            flex-direction: column;
            align-items: flex-start;
        }

        .logout-button {
            text-align: left;
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session
    initialize_session()
    
    # Check authentication - this will automatically load from URL if needed
    if not is_authenticated():
        login_register_page()
        return

    # Get current user
    current_user = get_current_user()
    if not current_user:
        login_register_page()
        return

    # Header with logout
    st.markdown('<div class="responsive-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    st.markdown("### 🍅 Pomodash - Productivity Tracker", unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔒 Logout"):
            # Clear session from URL and session state
            clear_session_from_url()
            st.success("Logged out successfully.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Timer and Dashboard
    pomodoro_ui()
    st.markdown("---")
    show_dashboard()
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
