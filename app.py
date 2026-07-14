import streamlit as st

from modules.task_manager import TaskManager
from utils import ai_engine, config, db, seed_kb, theme

st.set_page_config(
    page_title="BusinessPilot AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

TaskManager.initialize()
theme.init_theme_state()
theme.inject_css()

# Seed the knowledge base with built-in business knowledge
try:
    db.init_db()
    n = seed_kb.seed_knowledge_base()
    if n:
        st.session_state["_kb_seeded"] = n
except Exception:
    pass

for key, default in [
    ("chat_history", []),
    ("finance_messages", []),
    ("current_csv_context", None),
    ("current_csv_name", None),
    ("current_csv_df", None),
    ("data_chat_history", []),
    ("edit_task_idx", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    theme.sidebar_nav("Home")

theme.page_header("Welcome back", "Your offline AI workspace — nothing here leaves this machine.")

st.markdown("<p class='section-label'>System Status</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**Chat model**")
        st.caption(config.LLAMA_HOST)
        if st.button("Check connection", key="check_chat", use_container_width=True):
            with st.spinner("Pinging llama-server..."):
                r = ai_engine.query_model("Reply with just OK.", max_tokens=5)
            if r.ok:
                st.success("Connected")
            else:
                st.error(r.error)

with col2:
    with st.container(border=True):
        st.markdown("**Embedding model**")
        st.caption(config.LLAMA_HOST)
        if st.button("Check connection", key="check_embed", use_container_width=True):
            with st.spinner("Pinging embedding server..."):
                r = ai_engine.embed_text("test")
            if r.ok:
                st.success(f"{len(r.vector)}-dim vectors")
            else:
                st.error(r.error)

with col3:
    with st.container(border=True):
        st.markdown("**Knowledge base**")
        try:
            db.init_db()
            count = db.chunk_count()
            seeded = st.session_state.get("_kb_seeded", 0)
            label = f"{count} chunk(s) stored locally"
            if seeded:
                label += f" ({seeded} business topics seeded)"
            st.caption(label)
            st.markdown(theme.status_badge("sqlite-vec", "accent"), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"sqlite-vec unavailable: {e}")

st.write("")
theme.empty_state(
    icon_name="rocket",
    title="Ready to work offline",
    message="Use the sidebar to open a workspace. Your data and AI conversations stay on this machine.",
)
