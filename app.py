import streamlit as st
from supabase_client import supabase
from auth import login_register_page
from timer import pomodoro_ui
from analytics import show_dashboard
from datetime import datetime, timedelta, timezone

def refresh_token_if_needed():
    if "user" not in st.session_state and "refresh_token" in st.session_state:
        try:
            result = supabase.auth.refresh_session(st.session_state.refresh_token)
            session = result.session
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            st.session_state.token_created_at = datetime.now(timezone.utc)
            st.session_state.expires_in = session.expires_in
            st.session_state.user = result.user
        except Exception as e:
            st.session_state.clear()
            st.warning("⚠ Session expired. Please log in again.")
            st.stop()
    elif all(k in st.session_state for k in ["refresh_token", "token_created_at", "expires_in"]):
        expiration_time = st.session_state.token_created_at.replace(tzinfo=timezone.utc) + timedelta(seconds=st.session_state.expires_in)
        if datetime.now(timezone.utc) > expiration_time:
            try:
                result = supabase.auth.refresh_session(st.session_state.refresh_token)
                session = result.session
                st.session_state.access_token = session.access_token
                st.session_state.refresh_token = session.refresh_token
                st.session_state.token_created_at = datetime.now(timezone.utc)
                st.session_state.expires_in = session.expires_in
                st.session_state.user = result.user
            except Exception as e:
                st.session_state.clear()
                st.warning("⚠ Session expired. Please log in again.")
                st.stop()


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
    refresh_token_if_needed()

    if "user" not in st.session_state or st.session_state.user is None:
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
