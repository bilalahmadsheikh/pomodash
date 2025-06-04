import streamlit as st
from supabase_client import supabase
from auth import login_register_page
from timer import pomodoro_ui
from analytics import show_dashboard

def main():
    st.set_page_config(page_title="Pomodash", layout="wide")  # Use 'wide' for better responsiveness

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

    if "user" not in st.session_state:
        login_register_page()
        return

    # Header with logout
    st.markdown('<div class="responsive-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    st.markdown("### 🍅 Pomodash - Productivity Tracker", unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔒 Logout"):
            st.session_state.clear()
            st.success("Logged out.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Timer and Dashboard
    pomodoro_ui()
    st.markdown("---")
    show_dashboard()
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
