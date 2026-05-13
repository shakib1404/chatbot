# ── ui/chat.py ────────────────────────────────────────────────────────────────
import time
from datetime import datetime

import streamlit as st

from config import OLLAMA_CONTEXT_TURNS, SUMMARY_RECENT_TURNS
from db import (
    create_chat_session,
    get_chat_history,
    get_user_stats,
    list_chat_sessions,
    rename_chat_session,
    save_message,
    touch_chat_session,
    update_chat_summary,
)
from ollama_client import query as ollama_query, query_streaming, format_ts


# ── Public entry point ────────────────────────────────────────────────────────


def _normalize_chat_title(text: str, max_len: int = 40) -> str:
    title = " ".join(text.strip().split())
    if len(title) > max_len:
        title = title[:max_len].rstrip() + "…"
    return title or "New chat"


def _build_context_messages(history: list[dict], chat_summary: str, pending: str) -> list[dict]:
    """Build model context from rolling summary + recent turns + latest user input."""
    ollama_msgs: list[dict] = []

    if chat_summary.strip():
        ollama_msgs.append(
            {
                "role": "system",
                "content": (
                    "Conversation summary so far:\n"
                    f"{chat_summary.strip()}\n\n"
                    "Use this as memory for prior context."
                ),
            }
        )

    recent_turns = [
        {"role": m["role"], "content": m["content"]}
        for m in history[-SUMMARY_RECENT_TURNS:]
        if m["role"] in {"user", "assistant"}
    ]
    ollama_msgs.extend(recent_turns)
    ollama_msgs.append({"role": "user", "content": pending})
    return ollama_msgs


def _refresh_chat_summary(chat_id: str, previous_summary: str, user_msg: str, assistant_msg: str) -> None:
    """Incrementally update chat summary using the latest exchange."""
    if not assistant_msg.strip():
        return

    summary_prompt = [
        {
            "role": "system",
            "content": (
                "You maintain a concise rolling conversation summary. "
                "Keep key facts, user preferences, decisions, and unresolved questions. "
                "Write plain text only, max 120 words."
            ),
        },
        {
            "role": "user",
            "content": (
                "Previous summary:\n"
                f"{previous_summary.strip() or '(none)'}\n\n"
                "New exchange:\n"
                f"User: {user_msg}\n"
                f"Assistant: {assistant_msg}\n\n"
                "Return updated summary only."
            ),
        },
    ]

    new_summary = ollama_query(summary_prompt).strip()
    if not new_summary:
        return
    if new_summary.startswith("⚠️") or new_summary.startswith("❌"):
        return

    update_chat_summary(chat_id, new_summary)


def _ensure_active_chat_session() -> tuple[list[dict], dict]:
    username = st.session_state.username
    sessions = list_chat_sessions(username)
    active_chat_id = st.session_state.get("active_chat_id", "")

    active_session = None
    if sessions and active_chat_id:
        active_session = next((s for s in sessions if s["chat_id"] == active_chat_id), None)

    if active_session is None:
        if sessions:
            active_session = sessions[0]
        else:
            new_chat_id = create_chat_session(username, "New chat")
            active_session = {"chat_id": new_chat_id, "title": "New chat"}
            sessions = [active_session]

        st.session_state.active_chat_id = active_session["chat_id"]
        st.session_state.active_chat_title = active_session.get("title", "New chat")

    return sessions, active_session


def _select_chat_session(chat_id: str, title: str) -> None:
    st.session_state.active_chat_id = chat_id
    st.session_state.active_chat_title = title
    st.session_state.pending_prompt = None
    st.session_state.clear_input_text = True
    st.rerun()


def _create_new_chat_session() -> None:
    new_chat_id = create_chat_session(st.session_state.username, "New chat")
    st.session_state.active_chat_id = new_chat_id
    st.session_state.active_chat_title = "New chat"
    st.session_state.pending_prompt = None
    st.session_state.clear_input_text = True
    st.rerun()

def render_chat() -> None:
    if "stop_generation" not in st.session_state:
        st.session_state.stop_generation = False
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""
    if "clear_input_text" not in st.session_state:
        st.session_state.clear_input_text = False

    if st.session_state.clear_input_text:
        st.session_state.input_text = ""
        st.session_state.clear_input_text = False

    sessions, active_session = _ensure_active_chat_session()
    st.session_state.active_chat_title = active_session.get("title", "New chat")

    _render_sidebar()
    _render_header()

    history = get_chat_history(st.session_state.username, st.session_state.active_chat_id)
    chat_summary = active_session.get("summary", "")
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
        if st.session_state.active_chat_title == "New chat":
            new_title = _normalize_chat_title(pending)
            rename_chat_session(st.session_state.active_chat_id, new_title)
            st.session_state.active_chat_title = new_title

        save_message(
            st.session_state.username,
            "user",
            pending,
            chat_id=st.session_state.active_chat_id,
        )

        ollama_msgs = _build_context_messages(history, chat_summary, pending)

        reply, was_stopped = _stream_response(ollama_msgs)
        
        # Save full replies normally, but keep stopped replies out of model context
        if reply.strip():
            save_message(
                st.session_state.username,
                "assistant_partial" if was_stopped else "assistant",
                reply,
                chat_id=st.session_state.active_chat_id,
            )

        _refresh_chat_summary(
            st.session_state.active_chat_id,
            chat_summary,
            pending,
            reply,
        )

        touch_chat_session(st.session_state.active_chat_id)
        
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
        _sidebar_chat_sessions()
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


def _sidebar_chat_sessions() -> None:
    st.markdown("<div class='section-hdr'>CHAT SESSIONS</div>", unsafe_allow_html=True)

    if st.button("＋ NEW CHAT", key="new_chat", use_container_width=True):
        _create_new_chat_session()

    sessions = list_chat_sessions(st.session_state.username)
    if not sessions:
        st.markdown(
            "<div style='font-family:var(--mono);font-size:0.72rem;color:var(--muted);'>No chats yet.</div>",
            unsafe_allow_html=True,
        )
        return

    chat_ids = [session["chat_id"] for session in sessions]
    session_map = {session["chat_id"]: session for session in sessions}

    current_chat_id = st.session_state.get("active_chat_id") or chat_ids[0]
    if current_chat_id not in session_map:
        current_chat_id = chat_ids[0]

    current_index = chat_ids.index(current_chat_id)

    def _chat_label(chat_id: str) -> str:
        session = session_map[chat_id]
        title = session.get("title") or "New chat"
        return f"▶ {title}" if chat_id == st.session_state.get("active_chat_id") else title

    selected_chat_id = st.selectbox(
        "CONTINUE CHAT",
        options=chat_ids,
        index=current_index,
        format_func=_chat_label,
        key="chat_session_selector",
    )

    selected_session = session_map[selected_chat_id]
    if selected_chat_id != st.session_state.get("active_chat_id"):
        _select_chat_session(selected_chat_id, selected_session.get("title") or "New chat")

    st.markdown(
        f"<div style='font-family:var(--mono);font-size:0.62rem;color:var(--muted);margin:6px 0 10px 0;'>"
        f"{format_ts(selected_session.get('updated_at', ''))}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-family:var(--mono);font-size:0.68rem;color:var(--muted);margin-bottom:8px;'>Select a chat above to open its saved history and continue there.</div>",
        unsafe_allow_html=True,
    )


def _sidebar_sign_out() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⏻  SIGN OUT", key="logout"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.session_state.page      = "login"
        st.session_state.active_chat_id = ""
        st.session_state.active_chat_title = ""
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
    chat_title = st.session_state.get("active_chat_title", "New chat")
    st.markdown("""
    <div class='top-bar'>
        <div class='logo'>⚡ NeuralChat</div>
        <div class='badge'>ACTIVE CHAT · {chat_title}</div>
        <div class='badge'>MISTRAL · LOCAL LLM</div>
    </div>
    """.format(chat_title=chat_title), unsafe_allow_html=True)


# ── Message rendering ─────────────────────────────────────────────────────────

def _render_bubble(msg: dict) -> None:
    role         = msg["role"]
    content      = msg["content"]
    ts           = format_ts(msg.get("timestamp", ""))
    is_user      = role == "user"
    is_broken    = role == "assistant_partial"
    av_class     = "user" if is_user else "bot"
    av_label     = st.session_state.username[:2].upper() if is_user else "AI"
    bubble_class = "user" if is_user else "bot"
    row_class    = "user" if is_user else ""

    if is_broken:
        content = (
            "<div style='margin-bottom:8px;font-family:var(--mono);font-size:0.68rem;color:var(--muted);'>broken response</div>"
            f"<div style='opacity:0.82;'>{content}</div>"
        )

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
            if msg["role"] in {"user", "assistant", "assistant_partial"}:
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
    def _submit_prompt() -> None:
        prompt = st.session_state.get("input_text", "").strip()
        if not prompt:
            return
        st.session_state.pending_prompt = prompt
        st.session_state.stop_generation = False
        st.session_state.clear_input_text = True

    with st.form("chat_input_form", clear_on_submit=False):
        col_input, col_btn = st.columns([8, 1])

        with col_input:
            st.text_input(
                label="chat_input",
                label_visibility="collapsed",
                placeholder="Ask Mistral anything…",
                key="input_text",
            )

        with col_btn:
            st.form_submit_button("➤", use_container_width=True, on_click=_submit_prompt)


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
        final_text = final_text.strip()

    placeholder.markdown(f"""
    <div class='msg-row'>
        <div class='avatar bot'>AI</div>
        <div class='bubble bot'>
            {final_text if final_text else "<span style='font-family:var(--mono);font-size:0.7rem;color:var(--muted);'>broken response</span>"}
            <span class='ts'>{ts}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    return final_text, stopped