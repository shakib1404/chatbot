# ── ui/auth.py ────────────────────────────────────────────────────────────────
# Renders the Login / Register page.

import streamlit as st
from db import create_user, verify_user


def render_login() -> None:
    """Display the centered login card with Sign-In and Register tabs."""
    _, col, _ = st.columns([1, 1.1, 1])

    with col:
        # Decorative card header (purely visual — actual inputs are native widgets)
        st.markdown("""
        <div class='login-wrap'>
            <div class='login-title'>⚡ NeuralChat</div>
            <div class='login-sub'>// sign in to continue</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["SIGN IN", "REGISTER"])

        with tab_login:
            _render_sign_in()

        with tab_reg:
            _render_register()


# ── private helpers ────────────────────────────────────────────────────────────

def _render_sign_in() -> None:
    uname = st.text_input("USERNAME", key="li_u", placeholder="enter username")
    pwd   = st.text_input("PASSWORD", key="li_p", type="password", placeholder="••••••••")

    if st.button("AUTHENTICATE →", key="btn_login"):
        if verify_user(uname, pwd):
            st.session_state.logged_in = True
            st.session_state.username  = uname
            st.session_state.page      = "chat"
            st.session_state.active_chat_id = ""
            st.session_state.active_chat_title = ""
            st.rerun()
        else:
            st.error("Invalid credentials.")


def _render_register() -> None:
    nu  = st.text_input("USERNAME", key="reg_u",  placeholder="choose a username")
    np  = st.text_input("PASSWORD", key="reg_p",  type="password", placeholder="min 6 characters")
    np2 = st.text_input("CONFIRM",  key="reg_p2", type="password", placeholder="repeat password")

    if st.button("CREATE ACCOUNT →", key="btn_reg"):
        if len(nu) < 3:
            st.error("Username must be ≥ 3 characters.")
        elif len(np) < 6:
            st.error("Password must be ≥ 6 characters.")
        elif np != np2:
            st.error("Passwords do not match.")
        else:
            ok, msg = create_user(nu, np)
            if ok:
                st.success(f"Account created! Sign in as **{nu}**.")
            else:
                st.error(msg)