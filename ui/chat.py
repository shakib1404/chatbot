# ── ui/chat.py ────────────────────────────────────────────────────────────────
import time
from datetime import datetime

import streamlit as st

from config import OLLAMA_CONTEXT_TURNS
from db import save_message, get_chat_history, get_user_stats
from ollama_client import query as ollama_query, query_streaming, format_ts


# ── Public entry point ────────────────────────────────────────────────────────

def render_chat() -> None:
    if "stop_generation" not in st.session_state:
        st.session_state.stop_generation = False
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    _render_sidebar()
    _render_header()

    history = get_chat_history(st.session_state.username)
    pending = st.session_state.get("pending_prompt")

    # ── 1. Render all history messages ────────────────────────────────────────
    _render_all_messages(history, inject_user_msg=pending)

    # ── 2. If pending → generate reply right here, in this same run ──────────
    if pending:
        # IMPORTANT: Clear pending immediately so it doesn't execute again on rerun
        st.session_state.pending_prompt = None
        
        # If stop was already clicked, skip streaming and show input box
        if st.session_state.get("stop_generation"):
            st.session_state.stop_generation = False
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            _render_input_box()
            return
        
        # Save the user message
        save_message(st.session_state.username, "user", pending)

        ollama_msgs = [
            {"role": m["role"], "content": m["content"]}
            for m in history[-OLLAMA_CONTEXT_TURNS:]
        ] + [{"role": "user", "content": pending}]

        reply, was_stopped = _stream_response(ollama_msgs)
        
        # Only save if we got a response
        if reply.strip():
            save_message(st.session_state.username, "assistant", reply)
        
        # Reset flag and show input box
        st.session_state.stop_generation = False
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        _render_input_box()
        return

    # ── 3. Input box (only shown when idle) ───────────────────────────────────
    _render_input_box()


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


def _render_all_messages(history: list[dict], inject_user_msg: str | None = None) -> None:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    if not history and not inject_user_msg:
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
        # Inject the in-flight user bubble — appears on the RIGHT immediately
        if inject_user_msg:
            _render_bubble({
                "role": "user",
                "content": inject_user_msg,
                "timestamp": datetime.now(),
            })

    st.markdown("</div>", unsafe_allow_html=True)


# ── Custom input box ──────────────────────────────────────────────────────────

def _render_input_box() -> None:
    """
    Replaces st.chat_input with a plain text_input + button.
    st.chat_input is bottom-anchored and interferes with render order.
    This custom box sits naturally below the messages in DOM order.
    """
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col_input, col_btn = st.columns([8, 1])

    def _submit_prompt() -> None:
        prompt = st.session_state.get("input_text", "").strip()
        if not prompt:
            return
        st.session_state.pending_prompt = prompt
        st.session_state.stop_generation = False
        st.session_state.input_text = ""

    with col_input:
        user_text = st.text_input(
            label="chat_input",
            label_visibility="collapsed",
            placeholder="Ask Mistral anything…",
            key="input_text",
            on_change=_submit_prompt,
        )

    with col_btn:
        st.button("➤", key="send_btn", use_container_width=True, on_click=_submit_prompt)


# ── Streaming / animation ─────────────────────────────────────────────────────

def _stream_response(ollama_msgs: list[dict]) -> tuple[str, bool]:
    """
    Stream response from model and return (text, was_stopped).
    Returns a tuple with the response text and whether it was stopped.
    """
    # Typing indicator placeholder
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

    ts = format_ts(datetime.now())

    # Stop button — rendered BEFORE streaming starts
    def _set_stop():
        st.session_state.stop_generation = True

    stop_col, _ = st.columns([1, 5])
    with stop_col:
        st.button("■ STOP", key="stop_btn", on_click=_set_stop, type="secondary")

    # Stream response word-by-word
    shown: list[str] = []
    stopped = False

    def _should_stop():
        """Check if stop flag is set."""
        return st.session_state.get("stop_generation", False)

    try:
        for chunk in query_streaming(ollama_msgs, should_stop_func=_should_stop):
            if st.session_state.get("stop_generation"):
                stopped = True
                break
            
            # Accumulate words from the chunk
            words = chunk.split(" ")
            for word in words:
                if not word:
                    continue
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
                time.sleep(0.02)
            
            if stopped:
                break
    except Exception as e:
        shown.append(f"❌ Error: {str(e)}")

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

    return final_text, stopped