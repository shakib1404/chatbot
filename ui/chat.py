# ── ui/chat.py ────────────────────────────────────────────────────────────────
import time
from datetime import datetime

import streamlit as st

from config import OLLAMA_CONTEXT_TURNS
from db import save_message, get_chat_history, get_user_stats
from ollama_client import query as ollama_query, format_ts


# ── Public entry point ────────────────────────────────────────────────────────

def render_chat() -> None:
    if "stop_generation" not in st.session_state:
        st.session_state.stop_generation = False

    _render_sidebar()
    _render_header()

    history = get_chat_history(st.session_state.username)
    _render_messages(history)
    _handle_input(history)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        _sidebar_user_info()
        _sidebar_stats()
        _sidebar_history()
        _sidebar_sign_out()
        _sidebar_footer()


def _sidebar_user_info() -> None:
    st.markdown(f"""
    <div style='font-family:var(--mono);font-size:0.7rem;color:var(--muted);margin-bottom:4px;'>LOGGED IN AS</div>
    <div style='font-family:var(--mono);font-size:1rem;font-weight:700;color:var(--accent2);margin-bottom:20px;'>
        ◈ {st.session_state.username}
    </div>
    """, unsafe_allow_html=True)


def _sidebar_stats() -> None:
    stats = get_user_stats(st.session_state.username)
    st.markdown(f"""
    <div class='stat-grid'>
        <div class='stat-card'><div class='num'>{stats['total_messages']}</div><div class='lbl'>MESSAGES</div></div>
        <div class='stat-card'><div class='num'>{stats['user_messages']}</div><div class='lbl'>QUERIES</div></div>
    </div>
    """, unsafe_allow_html=True)


def _sidebar_history() -> None:
    st.markdown("<div class='section-hdr'>RECENT HISTORY</div>", unsafe_allow_html=True)
    history   = get_chat_history(st.session_state.username)
    user_msgs = [m for m in history if m["role"] == "user"][-6:][::-1]

    if user_msgs:
        for m in user_msgs:
            q = m["content"][:55] + "…" if len(m["content"]) > 55 else m["content"]
            st.markdown(f"""
            <div class='hist-item'>
                <div class='hist-q'>{q}</div>
                <div class='hist-t'>{format_ts(m.get('timestamp', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='font-family:var(--mono);font-size:0.72rem;color:var(--muted);'>No history yet.</div>",
            unsafe_allow_html=True,
        )


def _sidebar_sign_out() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⏻  SIGN OUT", key="logout"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.session_state.page      = "login"
        st.rerun()


def _sidebar_footer() -> None:
    st.markdown("""
    <div style='margin-top:auto;padding-top:30px;font-family:var(--mono);font-size:0.6rem;color:var(--muted);'>
        POWERED BY<br>
        <span style='color:var(--accent2);'>MISTRAL × OLLAMA</span><br>
        STORAGE: MONGODB
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────

def _render_header() -> None:
    st.markdown("""
    <div class='top-bar'>
        <div class='logo'>⚡ NeuralChat</div>
        <div class='badge'>MISTRAL · LOCAL LLM</div>
    </div>
    """, unsafe_allow_html=True)


# ── Message rendering ─────────────────────────────────────────────────────────

def _render_messages(history: list[dict]) -> None:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    if not history:
        st.markdown("""
        <div style='text-align:center;padding:60px 0;'>
            <div style='font-size:2.5rem;margin-bottom:12px;'>⚡</div>
            <div style='font-family:var(--mono);font-size:0.85rem;color:var(--muted);'>
                No messages yet.<br>Ask anything below.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in history:
            _render_bubble(msg)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_bubble(msg: dict) -> None:
    role         = msg["role"]
    content      = msg["content"]
    ts           = format_ts(msg.get("timestamp", ""))
    is_user      = role == "user"
    av_class     = "user" if is_user else "bot"
    av_label     = st.session_state.username[:2].upper() if is_user else "AI"
    bubble_class = "user" if is_user else "bot"
    row_class    = "user" if is_user else ""

    st.markdown(f"""
    <div class='msg-row {row_class}'>
        <div class='avatar {av_class}'>{av_label}</div>
        <div class='bubble {bubble_class}'>
            {content}
            <span class='ts'>{ts}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Input + state machine ─────────────────────────────────────────────────────

def _handle_input(history: list[dict]) -> None:
    prompt = st.chat_input("Ask Mistral anything…")
    if not prompt:
        return

    st.session_state.stop_generation = False

    # Render the new user message immediately on the right in the same run.
    _render_bubble({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now(),
    })

    # Build the Ollama context from the existing history plus the new prompt.
    live_history = history + [{"role": "user", "content": prompt}]
    save_message(st.session_state.username, "user", prompt)
    _do_generate(prompt, live_history)


# ── Generation ────────────────────────────────────────────────────────────────

def _do_generate(prompt: str, history: list[dict]) -> None:
    ollama_msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-OLLAMA_CONTEXT_TURNS:]
    ]
    # Guard: ensure the new prompt is the last message sent to Ollama
    if not ollama_msgs or ollama_msgs[-1]["content"] != prompt:
        ollama_msgs.append({"role": "user", "content": prompt})

    reply = _stream_response(ollama_msgs)
    save_message(st.session_state.username, "assistant", reply)
    st.rerun()   # → IDLE


def _stream_response(ollama_msgs: list[dict]) -> str:
    """
    Fetch from Ollama, animate word-by-word, support stop via on_click callback.

    Why on_click?
    Streamlit processes button clicks only on the rerun they trigger.
    A plain `if st.button(...)` cannot interrupt a running loop in the SAME
    execution.  Using `on_click=_set_stop` writes the flag into session_state
    BEFORE the script body reruns, so the loop sees it True at its very first
    iteration on that rerun → effectively instant stop.
    """

    # Typing indicator
    placeholder = st.empty()
    placeholder.markdown("""
    <div class='msg-row'>
        <div class='avatar bot'>AI</div>
        <div class='bubble bot'>
            <span class='typing-dot'></span>
            <span class='typing-dot'></span>
            <span class='typing-dot'></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner(""):
        reply = ollama_query(ollama_msgs)

    ts = format_ts(datetime.now())

    # Stop button BEFORE animation so layout doesn't jump
    def _set_stop():
        st.session_state.stop_generation = True

    stop_col, _ = st.columns([1, 5])
    with stop_col:
        st.button("■ STOP", key="stop_btn", on_click=_set_stop, type="secondary")

    # Word-by-word animation
    shown:  list[str] = []
    stopped = False

    for word in reply.split(" "):
        if st.session_state.get("stop_generation"):
            stopped = True
            break

        shown.append(word)
        placeholder.markdown(f"""
        <div class='msg-row'>
            <div class='avatar bot'>AI</div>
            <div class='bubble bot'>
                {" ".join(shown)}<span style='opacity:0.4;'>▌</span>
                <span class='ts'>{ts}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.04)

    # Final render
    final_text = " ".join(shown)
    if stopped:
        final_text += (
            " <span style='font-family:var(--mono);font-size:0.7rem;"
            "color:var(--muted);'>[stopped]</span>"
        )

    placeholder.markdown(f"""
    <div class='msg-row'>
        <div class='avatar bot'>AI</div>
        <div class='bubble bot'>
            {final_text}
            <span class='ts'>{ts}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.session_state.stop_generation = False
    return " ".join(shown)