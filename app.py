# ── app.py ────────────────────────────────────────────────────────────────────
# Entry point. Run with: streamlit run app.py

import streamlit as st

from config import PAGE_CONFIG, SESSION_DEFAULTS
import styles
from ui.auth import render_login
from ui.chat import render_chat


# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(**PAGE_CONFIG)

# ── Inject global CSS ─────────────────────────────────────────────────────────
styles.inject()

# ── Initialize session state ──────────────────────────────────────────────────
for key, default in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Router ────────────────────────────────────────────────────────────────────
if st.session_state.logged_in:
    render_chat()
else:
    render_login()
