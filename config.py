# ── config.py ─────────────────────────────────────────────────────────────────
# Central place for all app-wide constants and session-state defaults.

import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# How many turns of history to send to Ollama
OLLAMA_CONTEXT_TURNS = 20

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
}