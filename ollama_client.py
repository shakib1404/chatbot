# ── ollama_client.py ──────────────────────────────────────────────────────────
# Thin wrapper around the Ollama REST API.

import requests
from datetime import datetime
from config import OLLAMA_URL, OLLAMA_MODEL


def query(messages: list[dict]) -> str:
    """
    Send a list of {"role": ..., "content": ...} messages to Ollama
    and return the assistant's reply as a plain string.
    """
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ **Ollama is not running.**\n\n"
            "Start it with:\n```\nollama serve\n```\n"
            "Then pull the model:\n```\nollama pull mistral\n```"
        )
    except Exception as e:
        return f"⚠️ Model error: {e}"


def format_ts(ts) -> str:
    """Format a timestamp (datetime or string) for display."""
    if isinstance(ts, datetime):
        return ts.strftime("%b %d · %H:%M")
    return str(ts)[:16]