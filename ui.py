import streamlit as st
from backend import read_pdf, chunk_text, create_vectorstore, retrieve, generate_answer_stream

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="DocuMind — AI Document Intelligence",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded",
)

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
    --amber: #f59e0b; --rose: #f43f5e;
    --text: #fafafa; --text2: #a1a1aa; --text3: #52525b;
    --grad: linear-gradient(135deg, #8b5cf6, #06b6d4);
    --grad2: linear-gradient(135deg, #f59e0b, #f43f5e, #8b5cf6);
    --r: 14px; --r-sm: 10px;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
}
[data-testid="stAppViewContainer"]::before {
    content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(ellipse 600px 400px at 20% 15%, rgba(245,158,11,0.06), transparent),
        radial-gradient(ellipse 500px 500px at 80% 70%, rgba(139,92,246,0.05), transparent),
        radial-gradient(ellipse 400px 300px at 50% 90%, rgba(6,182,212,0.04), transparent);
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.25); border-radius: 99px; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 100px !important; }

[data-testid="stHeader"] {
    background: rgba(9,9,11,0.85) !important;
    backdrop-filter: blur(16px) saturate(180%) !important;
    border-bottom: 1px solid var(--border) !important;
}

/* ── Sidebar ── */
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
    background: rgba(245,158,11,0.1) !important; border-color: var(--amber) !important;
    box-shadow: 0 0 24px rgba(245,158,11,0.15) !important; transform: translateY(-1px) !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--glass) !important; border: 1px dashed rgba(245,158,11,0.25) !important;
    border-radius: var(--r) !important; padding: 0.5rem !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--amber) !important;
    box-shadow: 0 0 30px rgba(245,158,11,0.08) !important;
}
[data-testid="stFileUploader"] label {
    color: var(--text2) !important; font-size: 0.85rem !important;
}
[data-testid="stFileUploader"] small { color: var(--text3) !important; }
[data-testid="stFileUploader"] button {
    background: var(--glass) !important; color: var(--text2) !important;
    border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important;
}

/* ── Hero ── */
.dm-hero { text-align: center; padding: 1.5rem 0 0.4rem; }
.dm-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 50px;
    background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.2);
    font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--amber);
}
.dm-title {
    font-size: 2.4rem; font-weight: 900; margin: 8px 0 0;
    background: var(--grad2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.03em; line-height: 1.15;
}
.dm-sub { color: var(--text2); font-size: 0.92rem; margin-top: 4px; font-weight: 400; }

/* ── Status Pill ── */
.dm-status {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 16px; border-radius: 50px; margin: 10px 0 6px;
    background: var(--glass); border: 1px solid var(--border);
    font-size: 0.78rem; color: var(--text2);
}
.dm-dot {
    width: 7px; height: 7px; border-radius: 50%;
    animation: blink 2s ease-in-out infinite;
}
.dm-dot.active { background: var(--emerald); }
.dm-dot.waiting { background: var(--text3); }
@keyframes blink {
    0%,100% { opacity:1; box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
    50% { opacity:0.6; box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}

/* ── Welcome Card ── */
.dm-welcome {
    background: var(--glass); border: 1px solid var(--border);
    border-radius: var(--r); padding: 2rem 1.5rem;
    margin: 1rem 0; text-align: center; backdrop-filter: blur(8px);
}
.dm-welcome h3 { color: var(--text); font-size: 1.1rem; font-weight: 600; margin: 0 0 8px; }
.dm-welcome p { color: var(--text2); font-size: 0.85rem; line-height: 1.6; margin: 0; }
.dm-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-top: 1.2rem; }
.dm-feat {
    background: rgba(255,255,255,0.02); border: 1px solid var(--border);
    border-radius: var(--r-sm); padding: 0.9rem 0.6rem;
    transition: all 0.25s ease; cursor: default;
}
.dm-feat:hover {
    background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.15);
    transform: translateY(-2px);
}
.dm-feat-icon { font-size: 1.3rem; margin-bottom: 4px; }
.dm-feat-label { font-size: 0.73rem; color: var(--text2); font-weight: 500; }

/* ── Info Card ── */
.dm-info {
    background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.15);
    border-radius: var(--r-sm); padding: 0.7rem 1rem; margin: 0.6rem 0;
    font-size: 0.82rem; color: var(--amber);
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    padding: 0.5rem 0 !important;
    animation: msgIn 0.35s cubic-bezier(0.22,1,0.36,1);
}
@keyframes msgIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    font-size: 0.92rem !important; line-height: 1.75 !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
    background: rgba(139,92,246,0.1) !important; color: var(--purple-light) !important;
    padding: 2px 6px; border-radius: 5px; font-size: 0.84rem;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] pre {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important; padding: 1rem !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong {
    color: var(--amber) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    color: var(--text) !important; margin-bottom: 4px;
}
.stChatMessage > div:last-child {
    background: var(--glass) !important; border: 1px solid var(--border) !important;
    border-radius: var(--r) !important; padding: 0.9rem 1.1rem !important;
    backdrop-filter: blur(8px) !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] { border-top: none !important; padding-top: 0.6rem !important; }
[data-testid="stChatInput"] > div {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: 14px !important; transition: all 0.3s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--amber) !important;
    box-shadow: 0 0 30px rgba(245,158,11,0.1) !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text) !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important; caret-color: var(--amber) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text3) !important; }
[data-testid="stChatInput"] button {
    background: var(--amber) !important; border: none !important;
    border-radius: 10px !important; transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover {
    background: #fbbf24 !important; transform: scale(1.08) !important;
}
[data-testid="stChatInput"] button svg { fill: #09090b !important; }

.stSpinner > div { border-color: var(--amber) transparent transparent transparent !important; }
hr { border: none !important; height: 1px !important; background: var(--border) !important; margin: 1rem 0 !important; }

/* ── Stats ── */
.dm-stat {
    background: var(--glass); border: 1px solid var(--border);
    border-radius: var(--r-sm); padding: 0.7rem; text-align: center;
}
.dm-stat-num {
    font-size: 1.3rem; font-weight: 700;
    background: var(--grad2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.dm-stat-label { font-size: 0.68rem; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

/* ── Alerts ── */
.stSuccess > div { background: rgba(16,185,129,0.06) !important; border: 1px solid rgba(16,185,129,0.2) !important; border-radius: var(--r-sm) !important; color: var(--emerald) !important; }
.stError > div { background: rgba(244,63,94,0.06) !important; border: 1px solid rgba(244,63,94,0.2) !important; border-radius: var(--r-sm) !important; color: var(--rose) !important; }

@media (max-width: 768px) {
    .dm-title { font-size: 1.7rem; }
    .dm-grid { grid-template-columns: 1fr 1fr; }
    .dm-welcome { padding: 1.2rem; }
}
@media (max-width: 480px) { .dm-grid { grid-template-columns: 1fr; } }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "vector_ready" not in st.session_state:
    st.session_state.vector_ready = False
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center; padding: 0.6rem 0 0.2rem;">
        <div style="font-size: 1.8rem; margin-bottom: 2px;">🔮</div>
        <div style="font-size: 1.1rem; font-weight: 800;
             background: linear-gradient(135deg, #f59e0b, #f43f5e, #8b5cf6);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            DocuMind
        </div>
        <div style="font-size: 0.65rem; color: #52525b; letter-spacing: 2px; text-transform: uppercase;">
            AI Document Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── PDF Upload ──
    st.markdown("##### 📄 Document")
    uploaded = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if uploaded:
        # Reset if new file uploaded
        if st.session_state.pdf_name != uploaded.name:
            st.session_state.vector_ready = False
            st.session_state.history = []
            st.session_state.pdf_name = uploaded.name

        if not st.session_state.vector_ready:
            with st.spinner("⚡ Analyzing document..."):
                text = read_pdf(uploaded)
                if not text or not text.strip():
                    st.error("Could not extract text. The PDF may be image-only.")
                    st.stop()
                chunks = chunk_text(text, 800, 200)
                if not chunks:
                    st.error("No text chunks created.")
                    st.stop()
                index, embeds = create_vectorstore(chunks)

                st.session_state.chunks = chunks
                st.session_state.index = index
                st.session_state.embeds = embeds
                st.session_state.raw_text = text
                st.session_state.vector_ready = True

        # Show doc info
        st.markdown(f"""
        <div class="dm-info">
            📎 <strong>{uploaded.name}</strong><br>
            <span style="font-size:0.72rem; opacity:0.7;">
                {len(st.session_state.chunks)} chunks · {len(st.session_state.raw_text):,} chars
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Settings ──
    st.markdown("##### ⚙️ Settings")
    temperature = st.slider("🎛️ Temperature", 0.0, 1.0, 0.7, 0.05,
                            help="0 = precise, 1 = creative")
    max_tokens = st.slider("📝 Max Tokens", 256, 4096, 2048, 128,
                           help="Maximum response length")
    top_k = st.slider("🔍 Context Chunks", 3, 10, 5,
                      help="How many document chunks to retrieve per question")

    st.markdown("---")

    # ── Stats ──
    if st.session_state.history:
        user_msgs = len([h for h in st.session_state.history if h[0] == "user"])
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f'<div class="dm-stat"><div class="dm-stat-num">{user_msgs}</div><div class="dm-stat-label">Questions</div></div>', unsafe_allow_html=True)
        with cols[1]:
            chunks_n = len(st.session_state.get("chunks", []))
            st.markdown(f'<div class="dm-stat"><div class="dm-stat-num">{chunks_n}</div><div class="dm-stat-label">Chunks</div></div>', unsafe_allow_html=True)
        st.markdown("")

    # ── Actions ──
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    if st.button("📄 New Document", use_container_width=True):
        st.session_state.vector_ready = False
        st.session_state.history = []
        st.session_state.pdf_name = None
        st.rerun()


# ──────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────
st.markdown("""
<div class="dm-hero">
    <div class="dm-badge">🔮 RAG-Powered</div>
    <h1 class="dm-title">DocuMind</h1>
    <p class="dm-sub">Upload any PDF. Ask anything. Get deep, detailed answers.</p>
</div>
""", unsafe_allow_html=True)

# Status pill
if st.session_state.vector_ready:
    st.markdown(f"""
    <div style="text-align:center;">
        <div class="dm-status">
            <div class="dm-dot active"></div>
            <span>📎 {st.session_state.pdf_name} — Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center;">
        <div class="dm-status">
            <div class="dm-dot waiting"></div>
            <span>Upload a PDF to begin</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# WELCOME CARD
# ──────────────────────────────────────────────
if not st.session_state.history:
    st.markdown("""
    <div class="dm-welcome">
        <h3>What would you like to know?</h3>
        <p>Upload a PDF and ask questions — I'll give you thorough, well-structured answers with references from your document.</p>
        <div class="dm-grid">
            <div class="dm-feat"><div class="dm-feat-icon">📋</div><div class="dm-feat-label">Summarize</div></div>
            <div class="dm-feat"><div class="dm-feat-icon">🔍</div><div class="dm-feat-label">Deep Analysis</div></div>
            <div class="dm-feat"><div class="dm-feat-icon">📊</div><div class="dm-feat-label">Extract Data</div></div>
            <div class="dm-feat"><div class="dm-feat-icon">❓</div><div class="dm-feat-label">Q&A</div></div>
            <div class="dm-feat"><div class="dm-feat-icon">🔗</div><div class="dm-feat-label">Find Links</div></div>
            <div class="dm-feat"><div class="dm-feat-icon">💡</div><div class="dm-feat-label">Key Insights</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CHAT DISPLAY
# ──────────────────────────────────────────────
for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)


# ──────────────────────────────────────────────
# CHAT INPUT
# ──────────────────────────────────────────────
query = st.chat_input(
    "Ask anything about your document..." if st.session_state.vector_ready else "Upload a PDF first..."
)

if query:
    if not st.session_state.vector_ready:
        st.warning("Please upload a PDF first.")
        st.stop()

    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.history.append(("user", query))

    # Retrieve relevant chunks
    context_chunks = retrieve(
        query,
        st.session_state.chunks,
        st.session_state.index,
        st.session_state.embeds,
        k=top_k,
    )
    context = "\n\n---\n\n".join(context_chunks)

    # Stream response
    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(
                generate_answer_stream(
                    query, context, st.session_state.history,
                    temperature, max_tokens
                )
            )
        except Exception as e:
            reply = f"**Error:** `{str(e)}`\n\nPlease check your API key and try again."
            st.markdown(reply)

    st.session_state.history.append(("assistant", reply))