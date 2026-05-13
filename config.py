# ── config.py ─────────────────────────────────────────────────────────────────
# Central place for all app-wide constants and session-state defaults.

import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))

# How many turns of history to send to Ollama
OLLAMA_CONTEXT_TURNS = 20

# With summary mode enabled, only recent turns are included directly.
SUMMARY_RECENT_TURNS = int(os.getenv("SUMMARY_RECENT_TURNS", "6"))

# Streamlit page config (consumed by app.py)
PAGE_CONFIG = dict(
    page_title="NeuralChat · AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session-state keys and their initial values
SESSION_DEFAULTS: dict = {
    "logged_in":  False,
    "username":   "",
    "page":       "login",
    "active_tab": "chat",
    "active_chat_id": "",
    "active_chat_title": "",
}