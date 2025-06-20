import streamlit as st
from supabase_client import supabase
from datetime import datetime, timezone
from url_session_manager import save_session_to_url, clear_session_from_url

# ------------------ Custom CSS ------------------
def inject_custom_css():
    st.markdown("""
        <style>
        .app-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ff4b4b;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .stButton > button {
            font-weight: 600;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
        }
        .login-register-toggle .stButton > button {
            border: 2px solid #ff4b4b;
            background-color: #0e1117;
            color: #ff4b4b;
        }
        .login-register-toggle .stButton > button:hover {
            background-color: #ff4b4b;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

# ------------------ Login UI ------------------
def handle_login():
    email = st.session_state.login_email
    password = st.session_state.login_password

    if not email or not password:
        st.session_state.login_error = "Please enter both email and password."
        return

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if result.user and result.session:
            # Save session to URL (this also updates session state)
            save_session_to_url(result.user, result.session)
            
            # Clear login fields and errors
            st.session_state.login_email = ""
            st.session_state.login_password = ""
            st.session_state.login_error = None
            
            st.success("✅ Login successful!")
            st.rerun()

        else:
            st.session_state.login_error = "❌ Invalid credentials. Please try again."

    except Exception as e:
        error_message = str(e)
        if "Invalid login credentials" in error_message:
            st.session_state.login_error = "❌ Invalid email or password."
        elif "Email not confirmed" in error_message:
            st.session_state.login_error = "❌ Please confirm your email address first."
        else:
            st.session_state.login_error = f"❌ Login failed: {error_message}"

def login():
    with st.container():
        st.markdown("### 🔐 Login to your account")
        
        # Initialize login fields if they don't exist
        if "login_email" not in st.session_state:
            st.session_state.login_email = ""
        if "login_password" not in st.session_state:
            st.session_state.login_password = ""
        
        st.text_input("Email", key="login_email", value=st.session_state.login_email)
        st.text_input("Password", type="password", key="login_password", value=st.session_state.login_password)

        st.button("Login", on_click=handle_login, type="primary")

        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])

# ------------------ Register UI ------------------
def register():
    with st.container():
        st.markdown("### 📝 Create a new account")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        register_btn = st.button("Register", key="register_button", type="primary")

        if register_btn:
            if not email or not password:
                st.error("❌ Please fill in all fields.")
                return
            
            if password != confirm_password:
                st.error("❌ Passwords do not match.")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long.")
                return
            
            try:
                result = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                if result.user:
                    st.success("✅ Account created successfully! Please check your email for confirmation, then log in.")
                    # Switch to login mode
                    st.session_state.mode = "Login"
                    st.rerun()
                else:
                    st.error("❌ Registration failed. Please try again.")
                    
            except Exception as e:
                error_message = str(e)
                if "already registered" in error_message.lower():
                    st.error("❌ This email is already registered. Please log in instead.")
                else:
                    st.error(f"❌ Registration failed: {error_message}")

# ------------------ Combined UI ------------------
def login_register_page():
    inject_custom_css()
    st.markdown('<div class="app-title">🍅 Pomodash Productivity Tracker</div>', unsafe_allow_html=True)

    if "mode" not in st.session_state:
        st.session_state.mode = "Login"

    st.markdown("#### Select your mode:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Login", key="toggle_login", use_container_width=True):
            st.session_state.mode = "Login"
            # Clear any error messages when switching modes
            st.session_state.pop("login_error", None)
            st.rerun()
    
    with col2:
        if st.button("📝 Register", key="toggle_register", use_container_width=True):
            st.session_state.mode = "Register"
            # Clear any error messages when switching modes
            st.session_state.pop("login_error", None)
            st.rerun()

    st.markdown("---")

    if st.session_state.mode == "Login":
        login()
    else:
        register()
