import uuid
import json
from datetime import datetime
from pathlib import Path
import streamlit as st
from backend import get_response_stream, get_available_models, _get_key

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="NexusAI — Multi-Model Chat",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CHAT HISTORY PERSISTENCE
# ──────────────────────────────────────────────
HISTORY_DIR = Path(__file__).parent / ".chat_history"
HISTORY_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You are NexusAI, a brilliant and versatile AI assistant. "
    "You excel at any task — coding, analysis, creative writing, math, science, "
    "history, health, business, and more. You give clear, well-structured, "
    "detailed responses. Use markdown formatting, code blocks, and bullet points "
    "when appropriate. Be concise yet thorough. Be warm but professional."
)

def _new_chat_data(chat_id=None):
    return {
        "id": chat_id or str(uuid.uuid4())[:8],
        "title": "New Chat",
        "created": datetime.now().isoformat(),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
    }

def _save_chat(chat_data):
    path = HISTORY_DIR / f"{chat_data['id']}.json"
    path.write_text(json.dumps(chat_data, ensure_ascii=False), encoding="utf-8")

def _load_all_chats():
    chats = []
    for f in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            chats.append(data)
        except Exception:
            pass
    chats.sort(key=lambda c: c.get("created", ""), reverse=True)
    return chats

def _delete_chat(chat_id):
    path = HISTORY_DIR / f"{chat_id}.json"
    if path.exists():
        path.unlink()

def _auto_title(messages):
    """Generate a short title from the first user message."""
    for m in messages:
        if m["role"] == "user":
            text = m["content"].strip()
            if len(text) > 40:
                return text[:37] + "..."
            return text if text else "New Chat"
    return "New Chat"

# ──────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0

def _load_chat_into_session(chat_data):
    st.session_state.current_chat_id = chat_data["id"]
    st.session_state.messages = chat_data["messages"]
    st.session_state.msg_count = len([m for m in chat_data["messages"] if m["role"] == "user"])

def _save_current_chat():
    """Save current session to disk."""
    if not any(m["role"] == "user" for m in st.session_state.messages):
        return  # Don't save empty chats
    chat_id = st.session_state.current_chat_id or str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = chat_id
    chat_data = {
        "id": chat_id,
        "title": _auto_title(st.session_state.messages),
        "created": datetime.now().isoformat(),
        "messages": st.session_state.messages,
    }
    _save_chat(chat_data)

def _start_new_chat():
    _save_current_chat()
    new = _new_chat_data()
    st.session_state.current_chat_id = new["id"]
    st.session_state.messages = new["messages"]
    st.session_state.msg_count = 0


# ──────────────────────────────────────────────
# PREMIUM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg: #09090b; --bg2: #0f0f13; --bg3: #16161d;
    --glass: rgba(255,255,255,0.04); --border: rgba(255,255,255,0.06);
    --purple: #8b5cf6; --purple-light: #a78bfa;
    --cyan: #06b6d4; --emerald: #10b981; --pink: #ec4899;
    --text: #fafafa; --text2: #a1a1aa; --text3: #52525b;
    --grad: linear-gradient(135deg, #8b5cf6, #06b6d4);
    --grad2: linear-gradient(135deg, #8b5cf6, #ec4899, #06b6d4);
    --r: 14px; --r-sm: 10px;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}
[data-testid="stAppViewContainer"]::before {
    content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse 600px 400px at 15% 20%, rgba(139,92,246,0.07), transparent),
        radial-gradient(ellipse 500px 500px at 85% 70%, rgba(6,182,212,0.05), transparent),
        radial-gradient(ellipse 400px 300px at 50% 90%, rgba(236,72,153,0.04), transparent);
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.25); border-radius: 99px; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 100px !important; }

[data-testid="stHeader"] {
    background: rgba(9,9,11,0.85) !important;
    backdrop-filter: blur(16px) saturate(180%) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] {
    background: var(--bg2) !important; border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--text2) !important; font-size: 0.88rem; line-height: 1.6;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {
    color: var(--text2) !important; font-size: 0.82rem !important; font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--glass) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important;
    padding: 0.55rem 1rem !important; font-weight: 500 !important;
    font-size: 0.85rem !important; font-family: 'Inter', sans-serif !important;
    transition: all 0.25s ease !important; width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(139,92,246,0.1) !important; border-color: var(--purple) !important;
    box-shadow: 0 0 24px rgba(139,92,246,0.15) !important; transform: translateY(-1px) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--bg3) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important; color: var(--text) !important;
}

.chat-group-label {
    font-size: 0.68rem; font-weight: 600; color: var(--text3);
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 12px 12px 4px; margin-top: 4px;
}

/* ── Hero ── */
.nx-hero { text-align: center; padding: 1.8rem 0 0.6rem; }
.nx-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 50px;
    background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.2);
    font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--purple-light);
}
.nx-title {
    font-size: 2.6rem; font-weight: 900; margin: 10px 0 0;
    background: var(--grad2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.03em; line-height: 1.15;
}
.nx-sub { color: var(--text2); font-size: 0.95rem; margin-top: 6px; font-weight: 400; }

.nx-model-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 16px; border-radius: 50px; margin: 12px 0 6px;
    background: var(--glass); border: 1px solid var(--border);
    font-size: 0.78rem; color: var(--text2);
}
.nx-dot {
    width: 7px; height: 7px; border-radius: 50%; background: var(--emerald);
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
    0%,100% { opacity:1; box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
    50% { opacity:0.6; box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}

.nx-welcome {
    background: var(--glass); border: 1px solid var(--border);
    border-radius: var(--r); padding: 2rem 1.5rem;
    margin: 1rem 0; text-align: center; backdrop-filter: blur(8px);
}
.nx-welcome h3 { color: var(--text); font-size: 1.15rem; font-weight: 600; margin: 0 0 8px; }
.nx-welcome p { color: var(--text2); font-size: 0.88rem; line-height: 1.6; margin: 0; }
.nx-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-top: 1.2rem; }
.nx-feat {
    background: rgba(255,255,255,0.02); border: 1px solid var(--border);
    border-radius: var(--r-sm); padding: 0.9rem 0.6rem;
    transition: all 0.25s ease; cursor: default;
}
.nx-feat:hover {
    background: rgba(139,92,246,0.06); border-color: rgba(139,92,246,0.15);
    transform: translateY(-2px);
}
.nx-feat-icon { font-size: 1.4rem; margin-bottom: 4px; }
.nx-feat-label { font-size: 0.75rem; color: var(--text2); font-weight: 500; }

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    padding: 0.6rem 0 !important;
    animation: msgIn 0.35s cubic-bezier(0.22,1,0.36,1);
}
@keyframes msgIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    font-size: 0.93rem !important; line-height: 1.75 !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
    background: rgba(139,92,246,0.1) !important; color: var(--purple-light) !important;
    padding: 2px 6px; border-radius: 5px; font-size: 0.85rem;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] pre {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important; padding: 1rem !important;
}
.stChatMessage > div:last-child {
    background: var(--glass) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r) !important; padding: 0.9rem 1.1rem !important;
    backdrop-filter: blur(8px) !important;
}
[data-testid="stChatMessage"] [data-testid="stAvatar"] {
    border-radius: 10px !important; box-shadow: 0 2px 10px rgba(0,0,0,0.25) !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] { border-top: none !important; padding-top: 0.8rem !important; }
[data-testid="stChatInput"] > div {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: 14px !important; transition: all 0.3s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--purple) !important;
    box-shadow: 0 0 30px rgba(139,92,246,0.12) !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text) !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.93rem !important; caret-color: var(--purple-light) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text3) !important; }
[data-testid="stChatInput"] button {
    background: var(--purple) !important; border: none !important;
    border-radius: 10px !important; transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover {
    background: var(--purple-light) !important; transform: scale(1.08) !important;
}
[data-testid="stChatInput"] button svg { fill: white !important; }

.stSpinner > div { border-color: var(--purple) transparent transparent transparent !important; }
hr { border: none !important; height: 1px !important; background: var(--border) !important; margin: 1.2rem 0 !important; }

@media (max-width: 768px) {
    .nx-title { font-size: 1.8rem; }
    .nx-grid { grid-template-columns: 1fr 1fr; }
    .nx-welcome { padding: 1.2rem; }
}
@media (max-width: 480px) { .nx-grid { grid-template-columns: 1fr; } }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
available = get_available_models()

with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center; padding: 0.8rem 0 0.3rem;">
        <div style="font-size: 1.8rem; margin-bottom: 2px;">✦</div>
        <div style="font-size: 1.1rem; font-weight: 800;
             background: linear-gradient(135deg, #8b5cf6, #06b6d4);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            NexusAI
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── New Chat Button ──
    if st.button("✦  New Chat", key="new_chat", use_container_width=True):
        _start_new_chat()
        st.rerun()

    st.markdown("---")

    # ── Chat History ──
    all_chats = _load_all_chats()
    chats_with_msgs = [c for c in all_chats if any(m["role"] == "user" for m in c.get("messages", []))]

    if chats_with_msgs:
        # Group by time
        now = datetime.now()
        today_chats = []
        yesterday_chats = []
        week_chats = []
        older_chats = []

        for chat in chats_with_msgs:
            try:
                created = datetime.fromisoformat(chat["created"])
                diff = (now - created).days
                if diff == 0:
                    today_chats.append(chat)
                elif diff == 1:
                    yesterday_chats.append(chat)
                elif diff <= 7:
                    week_chats.append(chat)
                else:
                    older_chats.append(chat)
            except Exception:
                older_chats.append(chat)

        def render_chat_group(label, chats_list):
            if not chats_list:
                return
            st.markdown(f'<div class="chat-group-label">{label}</div>', unsafe_allow_html=True)
            for chat in chats_list:
                is_active = chat["id"] == st.session_state.current_chat_id
                cols = st.columns([5, 1])
                with cols[0]:
                    title = chat.get("title", "New Chat")
                    if st.button(
                        f"{'💬' if is_active else '○'} {title}",
                        key=f"load_{chat['id']}",
                        use_container_width=True,
                    ):
                        _save_current_chat()
                        _load_chat_into_session(chat)
                        st.rerun()
                with cols[1]:
                    if st.button("🗑", key=f"del_{chat['id']}"):
                        _delete_chat(chat["id"])
                        if chat["id"] == st.session_state.current_chat_id:
                            _start_new_chat()
                        st.rerun()

        render_chat_group("Today", today_chats)
        render_chat_group("Yesterday", yesterday_chats)
        render_chat_group("Previous 7 Days", week_chats)
        render_chat_group("Older", older_chats)

    else:
        st.markdown(
            '<div style="text-align:center; padding:1rem 0; font-size:0.82rem; color:#52525b;">'
            'No chat history yet.<br>Start a conversation!</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Model Selector ──
    model_names = list(available.keys())
    if model_names:
        selected_model = st.selectbox(
            "🔮 Model", model_names, index=0, key="selected_model", help="Choose your AI model"
        )
        model_info = available[selected_model]
        st.caption(f"{model_info['icon']} {model_info['speed']} · {model_info['provider'].upper()}")
    else:
        selected_model = "LLaMA 3.3 70B"
        st.warning("No API keys found.")

    # Temperature
    st.slider(
        "🎛️ Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05,
        key="temperature", help="0 = precise, 1 = creative"
    )

    st.markdown("---")

    # ── Clear All History ──
    if st.button("🗑️ Clear All History", key="clear_all", use_container_width=True):
        for f in HISTORY_DIR.glob("*.json"):
            f.unlink()
        st.session_state.current_chat_id = None
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.msg_count = 0
        st.rerun()

    st.markdown("---")

    # ── API Keys ──
    st.markdown("##### 🔑 API Keys")
    for name, key_var in [("Groq", "GROQ_API_KEY"), ("OpenAI", "OPENAI_API_KEY"), ("Gemini", "GEMINI_API_KEY")]:
        active = bool(_get_key(key_var))
        icon = "🟢" if active else "⚫"
        st.markdown(
            f"<span style='font-size:0.8rem;color:{'#10b981' if active else '#52525b'}'>"
            f"{icon} {name}</span>", unsafe_allow_html=True
        )

    st.markdown("""
    <div style="font-size:0.68rem; color:#3f3f46; text-align:center; line-height:1.5; margin-top:8px;">
        Add keys to <code style="color:#8b5cf6;">addon.env</code>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────
st.markdown("""
<div class="nx-hero">
    <div class="nx-badge">✦ Multi-Model AI</div>
    <h1 class="nx-title">NexusAI</h1>
    <p class="nx-sub">One interface. Every model. Blazing fast.</p>
</div>
""", unsafe_allow_html=True)

# Model pill
if available:
    current_model_name = st.session_state.get("selected_model", model_names[0] if model_names else "LLaMA 3.3 70B")
    m_info = available.get(current_model_name, list(available.values())[0])
    st.markdown(f"""
    <div style="text-align:center;">
        <div class="nx-model-pill">
            <div class="nx-dot"></div>
            <span>{m_info['icon']} {current_model_name} · {m_info['provider'].upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# WELCOME CARD
# ──────────────────────────────────────────────
user_msgs = [m for m in st.session_state.messages if m["role"] != "system"]
if not user_msgs:
    st.markdown("""
    <div class="nx-welcome">
        <h3>What can I help you build today?</h3>
        <p>Switch between models instantly. Groq for speed, GPT for depth, Gemini for versatility.</p>
        <div class="nx-grid">
            <div class="nx-feat"><div class="nx-feat-icon">💻</div><div class="nx-feat-label">Code & Debug</div></div>
            <div class="nx-feat"><div class="nx-feat-icon">📊</div><div class="nx-feat-label">Analyze Data</div></div>
            <div class="nx-feat"><div class="nx-feat-icon">✍️</div><div class="nx-feat-label">Write Content</div></div>
            <div class="nx-feat"><div class="nx-feat-icon">🧮</div><div class="nx-feat-label">Solve Math</div></div>
            <div class="nx-feat"><div class="nx-feat-icon">🔬</div><div class="nx-feat-label">Research</div></div>
            <div class="nx-feat"><div class="nx-feat-icon">💡</div><div class="nx-feat-label">Brainstorm</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CHAT HISTORY DISPLAY
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ──────────────────────────────────────────────
# CHAT INPUT
# ──────────────────────────────────────────────
if prompt := st.chat_input("Message NexusAI..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.msg_count += 1

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(
                get_response_stream(
                    st.session_state.messages,
                    model_name=st.session_state.get("selected_model", "LLaMA 3.3 70B"),
                    temperature=st.session_state.get("temperature", 0.7),
                )
            )
        except Exception as e:
            reply = f"**Error:** `{str(e)}`\n\nCheck your API key and try again."
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Auto-save after each message
    _save_current_chat()
