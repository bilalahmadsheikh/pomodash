import streamlit as st
from supabase_client import supabase
from auth import login_register_page
from timer import pomodoro_ui
from analytics import show_dashboard
from datetime import datetime, timedelta, timezone
import json

def save_session_to_storage(session_data):
    """Save session data to browser's localStorage using JavaScript"""
    session_json = json.dumps(session_data, default=str)
    st.components.v1.html(f"""
    <script>
        localStorage.setItem('pomodash_session', '{session_json}');
    </script>
    """, height=0)

def load_session_from_storage():
    """Load session data from browser's localStorage"""
    session_data = st.components.v1.html("""
    <script>
        const sessionData = localStorage.getItem('pomodash_session');
        if (sessionData) {
            window.parent.postMessage({
                type: 'session_data',
                data: JSON.parse(sessionData)
            }, '*');
        }
    </script>
    """, height=0)
    return session_data

def initialize_session():
    """Initialize session from stored data or fresh start"""
    if "session_initialized" not in st.session_state:
        # Try to load from stored session
        stored_session = load_session_from_storage()
        
        if stored_session and isinstance(stored_session, dict):
            # Restore session data
            for key, value in stored_session.items():
                if key in ['access_token', 'refresh_token', 'user', 'expires_in']:
                    st.session_state[key] = value
            
            # Convert timestamp strings back to datetime objects
            if 'token_created_at' in stored_session:
                try:
                    st.session_state.token_created_at = datetime.fromisoformat(stored_session['token_created_at'])
                except:
                    pass
        
        st.session_state.session_initialized = True

def refresh_token_if_needed():
    """Enhanced token refresh with session persistence"""
    initialize_session()
    
    # Check if we have a refresh token but no user (page refresh scenario)
    if "user" not in st.session_state and "refresh_token" in st.session_state:
        try:
            result = supabase.auth.refresh_session(st.session_state.refresh_token)
            session = result.session
            
            # Update session state
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            st.session_state.token_created_at = datetime.now(timezone.utc)
            st.session_state.expires_in = session.expires_in
            st.session_state.user = result.user
            
            # Save to persistent storage
            save_session_data()
            
        except Exception as e:
            clear_session()
            st.warning("⚠️ Session expired. Please log in again.")
            st.stop()
    
    # Check if current token needs refresh
    elif all(k in st.session_state for k in ["refresh_token", "token_created_at", "expires_in"]):
        # Add buffer time (5 minutes) before actual expiry
        buffer_time = 300  # 5 minutes in seconds
        expiration_time = st.session_state.token_created_at.replace(tzinfo=timezone.utc) + timedelta(seconds=st.session_state.expires_in - buffer_time)
        
        if datetime.now(timezone.utc) > expiration_time:
            try:
                result = supabase.auth.refresh_session(st.session_state.refresh_token)
                session = result.session
                
                # Update session state
                st.session_state.access_token = session.access_token
                st.session_state.refresh_token = session.refresh_token
                st.session_state.token_created_at = datetime.now(timezone.utc)
                st.session_state.expires_in = session.expires_in
                st.session_state.user = result.user
                
                # Save to persistent storage
                save_session_data()
                
            except Exception as e:
                clear_session()
                st.warning("⚠️ Session expired. Please log in again.")
                st.stop()

def save_session_data():
    """Save current session data to persistent storage"""
    if "user" in st.session_state:
        session_data = {
            'access_token': st.session_state.get('access_token'),
            'refresh_token': st.session_state.get('refresh_token'),
            'token_created_at': st.session_state.get('token_created_at').isoformat() if st.session_state.get('token_created_at') else None,
            'expires_in': st.session_state.get('expires_in'),
            'user': {
                'id': st.session_state.user.id,
                'email': st.session_state.user.email,
                # Add other user fields you need
            }
        }
        save_session_to_storage(session_data)

def clear_session():
    """Clear session data from both memory and storage"""
    st.session_state.clear()
    st.components.v1.html("""
    <script>
        localStorage.removeItem('pomodash_session');
    </script>
    """, height=0)

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
    
    # Check and refresh token if needed
    refresh_token_if_needed()

    # If no user is logged in, show login page
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
            # Clear session and storage
            clear_session()
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
