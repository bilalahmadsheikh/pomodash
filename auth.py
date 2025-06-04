import streamlit as st
from supabase_client import supabase

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

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if result.user:
            st.session_state.user = result.user
            st.session_state.login_error = None
            st.experimental_rerun()
        else:
            st.session_state.login_error = "No user returned."

    except Exception:
        st.session_state.login_error = "❌ Login failed. Please check your credentials."


def login():
    with st.container():
        st.markdown("### 🔐 Login to your account")
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_password")

        st.button("Login", on_click=handle_login)

        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])



# ------------------ Register UI ------------------
def register():
    with st.container():
        st.markdown("### 📝 Create a new account")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")

        register_btn = st.button("Register", key="register_button")

        if register_btn:
            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("✅ Account created! Check your email to confirm.")
            except Exception:
                st.error("❌ Registration failed. Try again.")

# ------------------ Combined UI ------------------
def login_register_page():
    inject_custom_css()
    st.markdown('<div class="app-title">🍅 Pomodash Productivity Tracker</div>', unsafe_allow_html=True)

    if "mode" not in st.session_state:
        st.session_state.mode = "Login"

    st.markdown("#### Select your mode:")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            with st.container():
                with st.container().container():
                    with st.container().container().container():
                        with st.container().container().container().container():
                            if st.button("🔑 Login", key="toggle_login"):
                                st.session_state.mode = "Login"
        with col2:
            if st.button("📝 Register", key="toggle_register"):
                st.session_state.mode = "Register"

    st.markdown("---")

    if st.session_state.mode == "Login":
        login()
    else:
        register()
