# ── ollama_client.py ──────────────────────────────────────────────────────────
# Thin wrapper around the Ollama REST API.

import json
import requests
from datetime import datetime

from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS


def query(messages: list[dict]) -> str:
    """
    Send a list of {"role": ..., "content": ...} messages to Ollama
    and return the assistant's reply as a plain string.
    """
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ **Ollama is not running.**\n\n"
            "Start it with:\n```\nollama serve\n```\n"
            "Then pull the model:\n```\nollama pull mistral\n```"
        )
    except requests.exceptions.Timeout:
        return (
            "⚠️ **Ollama took too long to respond.**\n\n"
            "The model may still be loading or generating a long reply.\n"
            "Try again, wait a bit longer, or set `OLLAMA_TIMEOUT_SECONDS` higher in `.env`."
        )
    except Exception as exc:
        return f"⚠️ Model error: {exc}"


def query_streaming(messages: list[dict], should_stop_func=None):
    """
    Send messages to Ollama with streaming enabled.
    Yields text chunks as they arrive from the model.
    should_stop_func: callable that returns True if streaming should stop.
    """
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}
    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            # Check if we should stop
            if should_stop_func and should_stop_func():
                response.close()
                return
            
            if line:
                try:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                except Exception:
                    pass
    except requests.exceptions.ConnectionError:
        yield "⚠️ **Ollama is not running.**\n\nStart it with:\n```\nollama serve\n```"
    except requests.exceptions.Timeout:
        yield "⚠️ **Ollama took too long to respond. Try again or increase timeout.**"
    except Exception as exc:
        yield f"⚠️ Model error: {exc}"


def format_ts(ts) -> str:
    """Format a timestamp (datetime or string) for display."""
    if isinstance(ts, datetime):
        return ts.strftime("%b %d · %H:%M")
    return str(ts)[:16]
