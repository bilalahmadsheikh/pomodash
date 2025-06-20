# url_session_manager.py
import streamlit as st
import json
import base64
from datetime import datetime, timezone, timedelta
from supabase_client import supabase

def encode_session_data(data):
    """Encode session data for URL storage"""
    try:
        json_str = json.dumps(data, default=str)
        encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
        return encoded
    except Exception:
        return None

def decode_session_data(encoded_data):
    """Decode session data from URL"""
    try:
        json_str = base64.urlsafe_b64decode(encoded_data.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return None

def save_session_to_url(user, session):
    """Save authentication session to URL parameters"""
    session_data = {
        'user_id': user.id,
        'email': user.email,
        'refresh_token': session.refresh_token,
        'expires_in': session.expires_in,
        'token_created_at': datetime.now(timezone.utc).isoformat()
    }
    
    encoded_data = encode_session_data(session_data)
    if encoded_data:
        # Update URL with session data
        st.query_params.update({"session": encoded_data})
        
        # Also store in session state for current session
        st.session_state.user = user
        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token
        st.session_state.token_created_at = datetime.now(timezone.utc)
        st.session_state.expires_in = session.expires_in

def load_session_from_url():
    """Load and restore session from URL parameters"""
    try:
        # Get session data from URL
        session_param = st.query_params.get("session")
        if not session_param:
            return False
            
        session_data = decode_session_data(session_param)
        if not session_data:
            clear_session_from_url()
            return False
            
        # Check if session data is expired (with 5 minute buffer)
        token_created_at = datetime.fromisoformat(session_data['token_created_at'])
        buffer_time = 300  # 5 minutes
        expiration_time = token_created_at + timedelta(seconds=session_data['expires_in'] - buffer_time)
        
        if datetime.now(timezone.utc) > expiration_time:
            # Try to refresh the token
            try:
                result = supabase.auth.refresh_session(session_data['refresh_token'])
                if result.session and result.user:
                    # Update URL with new session data
                    save_session_to_url(result.user, result.session)
                    return True
                else:
                    clear_session_from_url()
                    return False
            except Exception:
                clear_session_from_url()
                return False
        else:
            # Session is still valid, restore to session state
            try:
                # Try to refresh to get current access token
                result = supabase.auth.refresh_session(session_data['refresh_token'])
                if result.session and result.user:
                    st.session_state.user = result.user
                    st.session_state.refresh_token = result.session.refresh_token
                    st.session_state.access_token = result.session.access_token
                    st.session_state.token_created_at = datetime.now(timezone.utc)
                    st.session_state.expires_in = result.session.expires_in
                    return True
                else:
                    clear_session_from_url()
                    return False
            except Exception:
                clear_session_from_url()
                return False
                
    except Exception as e:
        clear_session_from_url()
        return False

def clear_session_from_url():
    """Clear session data from URL and session state"""
    # Clear URL parameter
    if "session" in st.query_params:
        del st.query_params["session"]
    
    # Clear session state
    keys_to_clear = [
        'access_token', 'refresh_token', 'user', 'expires_in', 'token_created_at',
        'work_duration', 'break_duration', 'phase', 'start_time', 'elapsed',
        'running', 'paused', 'partial_work_minutes', 'partial_break_minutes',
        'skip_to_break', 'start_timestamp', 'session_initialized'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def is_authenticated():
    """Check if user is authenticated via session state or URL"""
    # First check session state
    if "user" in st.session_state and st.session_state.user:
        return True
    
    # If not in session state, try to load from URL
    return load_session_from_url()

def get_current_user():
    """Get current user, loading from URL if necessary"""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    
    if load_session_from_url():
        return st.session_state.get("user")
    
    return None