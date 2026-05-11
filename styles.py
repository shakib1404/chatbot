# ── styles.py ─────────────────────────────────────────────────────────────────
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

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

html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

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

.stTextInput > div > div > input,
.stTextInput > div > div > input:focus {
    background: var(--surface) !important;
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

/* ── Send button (➤) — distinct from sidebar buttons ── */
div[data-testid="column"]:last-child .stButton > button {
    background: var(--accent2) !important;
    color: #000 !important;
    font-size: 1.1rem !important;
    padding: 8px 4px !important;
    border-radius: 3px !important;
    border: none !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    background: #0891b2 !important;
    transform: translateY(-1px) !important;
}

/* ── All other buttons ── */
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

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 20px 16px !important; }

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

hr { border-color: var(--border) !important; }
.stAlert { border-radius: 3px !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }

.stSelectbox > div > div {
    background: var(--bg) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
}

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
"""

def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)