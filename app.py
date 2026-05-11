import streamlit as st
import requests
import json
from datetime import datetime
import time
from db import (
    create_user, verify_user, save_message,
    get_chat_history, get_user_stats
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeuralChat · AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

/* ── Root variables ── */
:root {
    --bg:        #0a0a0f;
    --surface:   #111118;
    --border:    #1e1e2e;
    --accent:    #7c3aed;
    --accent2:   #06b6d4;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --user-bg:   #1e1b4b;
    --bot-bg:    #0f172a;
    --danger:    #ef4444;
    --success:   #10b981;
    --mono:      'Space Mono', monospace;
    --sans:      'Syne', sans-serif;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

/* ── Top title bar ── */
.top-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 0 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.top-bar .logo {
    font-family: var(--mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent2);
    letter-spacing: -1px;
}
.top-bar .badge {
    background: var(--accent);
    color: #fff;
    font-family: var(--mono);
    font-size: 0.6rem;
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 1px;
}

/* ── Login card ── */
.login-wrap {
    max-width: 420px;
    margin: 60px auto;
    padding: 40px 36px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    position: relative;
    overflow: hidden;
}
.login-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.login-title {
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent2);
    margin-bottom: 6px;
}
.login-sub {
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 28px;
    font-family: var(--mono);
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextInput > div > div > input:focus {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.15) !important;
}
label { color: var(--muted) !important; font-family: var(--mono) !important; font-size: 0.75rem !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    padding: 10px 22px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.15s, transform 0.1s !important;
}
.stButton > button:hover {
    background: #6d28d9 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Chat messages ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 12px 0;
}
.msg-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}
.msg-row.user { flex-direction: row-reverse; }
.avatar {
    width: 34px;
    height: 34px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
}
.avatar.user { background: var(--accent); color: #fff; }
.avatar.bot  { background: var(--accent2); color: #000; }
.bubble {
    max-width: 72%;
    padding: 12px 16px;
    border-radius: 3px;
    font-size: 0.88rem;
    line-height: 1.65;
    font-family: var(--sans);
    position: relative;
}
.bubble.user {
    background: var(--user-bg);
    border: 1px solid rgba(124,58,237,0.3);
    border-top-right-radius: 0;
}
.bubble.bot {
    background: var(--bot-bg);
    border: 1px solid var(--border);
    border-top-left-radius: 0;
}
.bubble .ts {
    display: block;
    font-size: 0.65rem;
    color: var(--muted);
    font-family: var(--mono);
    margin-top: 8px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 20px 16px !important; }

/* ── Stat cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 16px 0;
}
.stat-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 12px;
    text-align: center;
}
.stat-card .num {
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent2);
}
.stat-card .lbl {
    font-family: var(--mono);
    font-size: 0.62rem;
    color: var(--muted);
    margin-top: 2px;
}

/* ── History tab items ── */
.hist-item {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 10px 12px;
    margin-bottom: 8px;
    border-left: 3px solid var(--accent);
}
.hist-item .hist-q {
    font-size: 0.78rem;
    color: var(--text);
    font-family: var(--sans);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.hist-item .hist-t {
    font-size: 0.62rem;
    color: var(--muted);
    font-family: var(--mono);
    margin-top: 4px;
}

/* ── Chat input area ── */
.stChatInput > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
}
.stChatInput textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Alerts ── */
.stAlert { border-radius: 3px !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--bg) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
}

/* ── Section headers ── */
.section-hdr {
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: var(--muted);
    text-transform: uppercase;
    margin: 20px 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}

/* ── Typing indicator ── */
.typing-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--accent2);
    border-radius: 50%;
    margin: 0 2px;
    animation: bounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%,80%,100% { transform: translateY(0); opacity: 0.4; }
    40%          { transform: translateY(-6px); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
for k, v in [
    ("logged_in", False), ("username", ""), ("page", "login"),
    ("active_tab", "chat"),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Ollama helper ─────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"

def query_ollama(messages: list[dict]) -> str:
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
    if isinstance(ts, datetime):
        return ts.strftime("%b %d · %H:%M")
    return str(ts)[:16]

# ╔══════════════════════════════════════════════════════════════════════════════
# ║  AUTH PAGES
# ╚══════════════════════════════════════════════════════════════════════════════
def render_login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div class='login-wrap'>
            <div class='login-title'>⚡ NeuralChat</div>
            <div class='login-sub'>// sign in to continue</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["SIGN IN", "REGISTER"])

        with tab_login:
            uname = st.text_input("USERNAME", key="li_u", placeholder="enter username")
            pwd   = st.text_input("PASSWORD", key="li_p", type="password", placeholder="••••••••")
            if st.button("AUTHENTICATE →", key="btn_login"):
                if verify_user(uname, pwd):
                    st.session_state.logged_in = True
                    st.session_state.username  = uname
                    st.session_state.page      = "chat"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with tab_reg:
            nu = st.text_input("USERNAME", key="reg_u", placeholder="choose a username")
            np = st.text_input("PASSWORD", key="reg_p", type="password", placeholder="min 6 characters")
            np2= st.text_input("CONFIRM",  key="reg_p2",type="password", placeholder="repeat password")
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

# ╔══════════════════════════════════════════════════════════════════════════════
# ║  MAIN CHAT PAGE
# ╚══════════════════════════════════════════════════════════════════════════════
def render_chat():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
        <div style='font-family:var(--mono);font-size:0.7rem;color:var(--muted);margin-bottom:4px;'>LOGGED IN AS</div>
        <div style='font-family:var(--mono);font-size:1rem;font-weight:700;color:var(--accent2);margin-bottom:20px;'>
            ◈ {st.session_state.username}
        </div>
        """, unsafe_allow_html=True)

        stats = get_user_stats(st.session_state.username)
        st.markdown(f"""
        <div class='stat-grid'>
            <div class='stat-card'><div class='num'>{stats['total_messages']}</div><div class='lbl'>MESSAGES</div></div>
            <div class='stat-card'><div class='num'>{stats['user_messages']}</div><div class='lbl'>QUERIES</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-hdr'>RECENT HISTORY</div>", unsafe_allow_html=True)
        history = get_chat_history(st.session_state.username)
        user_msgs = [m for m in history if m["role"] == "user"][-6:][::-1]
        if user_msgs:
            for m in user_msgs:
                q = m["content"][:55] + "…" if len(m["content"]) > 55 else m["content"]
                st.markdown(f"""
                <div class='hist-item'>
                    <div class='hist-q'>{q}</div>
                    <div class='hist-t'>{format_ts(m.get('timestamp',''))}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-family:var(--mono);font-size:0.72rem;color:var(--muted);'>No history yet.</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⏻  SIGN OUT", key="logout"):
            for k in ["logged_in","username","page"]:
                st.session_state[k] = False if k == "logged_in" else ""
            st.session_state.page = "login"
            st.rerun()

        st.markdown("""
        <div style='margin-top:auto;padding-top:30px;font-family:var(--mono);font-size:0.6rem;color:var(--muted);'>
            POWERED BY<br>
            <span style='color:var(--accent2);'>MISTRAL × OLLAMA</span><br>
            STORAGE: MONGODB
        </div>
        """, unsafe_allow_html=True)

    # ── Header ──
    st.markdown("""
    <div class='top-bar'>
        <div class='logo'>⚡ NeuralChat</div>
        <div class='badge'>MISTRAL · LOCAL LLM</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load history from DB ──
    history = get_chat_history(st.session_state.username)

    # ── Render existing messages ──
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
            role = msg["role"]
            content = msg["content"]
            ts = format_ts(msg.get("timestamp", ""))
            av_class = "user" if role == "user" else "bot"
            av_label = st.session_state.username[:2].upper() if role == "user" else "AI"
            bubble_class = "user" if role == "user" else "bot"
            row_class = "user" if role == "user" else ""
            st.markdown(f"""
            <div class='msg-row {row_class}'>
                <div class='avatar {av_class}'>{av_label}</div>
                <div class='bubble {bubble_class}'>
                    {content}
                    <span class='ts'>{ts}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat input ──
    if prompt := st.chat_input("Ask Mistral anything…"):
        # Save user message
        save_message(st.session_state.username, "user", prompt)

        # Build message list for Ollama (last 20 turns for context)
        ollama_msgs = [
            {"role": m["role"], "content": m["content"]}
            for m in history[-20:]
        ] + [{"role": "user", "content": prompt}]

        with st.spinner(""):
            bot_placeholder = st.empty()
            bot_placeholder.markdown("""
            <div class='msg-row'>
                <div class='avatar bot'>AI</div>
                <div class='bubble bot'>
                    <span class='typing-dot'></span>
                    <span class='typing-dot'></span>
                    <span class='typing-dot'></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            reply = query_ollama(ollama_msgs)

        # Stream the reply into the chat bubble (typing effect)
        try:
            ts = format_ts(datetime.now())
            # reveal text progressively (by character) to simulate streaming
            for i in range(1, len(reply) + 1):
                partial = reply[:i]
                bot_placeholder.markdown(f"""
                <div class='msg-row'>
                    <div class='avatar bot'>AI</div>
                    <div class='bubble bot'>
                        {partial}
                        <span class='ts'>{ts}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.01)
        except Exception:
            # fallback: render full reply if streaming fails
            bot_placeholder.markdown(f"""
            <div class='msg-row'>
                <div class='avatar bot'>AI</div>
                <div class='bubble bot'>
                    {reply}
                    <span class='ts'>{format_ts(datetime.now())}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        save_message(st.session_state.username, "assistant", reply)
        st.rerun()

# ╔══════════════════════════════════════════════════════════════════════════════
# ║  ROUTER
# ╚══════════════════════════════════════════════════════════════════════════════
if st.session_state.logged_in:
    render_chat()
else:
    render_login()