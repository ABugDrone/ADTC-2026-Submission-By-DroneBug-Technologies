import streamlit as st

from modules.markitdown_skill import convert_to_markdown
from utils import ai_engine, chat_store, db, theme

st.set_page_config(page_title="Chat & Knowledge Base · BusinessPilot AI", page_icon="", layout="wide")
theme.init_theme_state()
theme.inject_css()

with st.sidebar:
    theme.sidebar_nav("Chat & Knowledge Base")
    st.divider()

    # --- Saved Chats sidebar ---
    st.markdown("<p class='section-label' style='margin-top:0;'>Saved Chats</p>", unsafe_allow_html=True)
    saved = chat_store.list_chats()
    current_id = st.session_state.get("chat_id")

    if st.button("+ New Chat", use_container_width=True, key="new_chat_btn"):
        for k in ("chat_id", "chat_title", "messages"):
            st.session_state.pop(k, None)
        st.rerun()

    if saved:
        for c in saved:
            active = "active" if c["id"] == current_id else ""
            label = c["title"][:30] + ("..." if len(c["title"]) > 30 else "")
            if st.button(f"{'>> ' if active else ''}{label}", key=f"sc_{c['id']}", use_container_width=True):
                data = chat_store.load_chat(c["id"])
                if data:
                    st.session_state.chat_id = c["id"]
                    st.session_state.chat_title = data.get("title", "Untitled")
                    st.session_state.messages = data.get("messages", [])
                st.rerun()

        st.divider()
        if current_id and st.button("Delete current chat", use_container_width=True, type="secondary"):
            chat_store.delete_chat(current_id)
            for k in ("chat_id", "chat_title", "messages"):
                st.session_state.pop(k, None)
            st.rerun()

theme.page_header(
    "Chat & Knowledge Base",
    "Upload documents, convert them to Markdown, and ask Qwen questions.",
)

# --- Session state initialisation ---
for k in ("md_raw", "md_name", "md_text", "rag_log", "messages", "chat_id", "chat_title"):
    if k not in st.session_state:
        if k == "rag_log":
            st.session_state[k] = []
        elif k == "messages":
            st.session_state[k] = []
        elif k in ("md_raw",):
            st.session_state[k] = None
        elif k in ("md_text", "md_name", "chat_title"):
            st.session_state[k] = ""
        elif k == "chat_id":
            st.session_state[k] = chat_store.new_chat_id()

if not st.session_state.chat_title:
    st.session_state.chat_title = "Untitled chat"

# --- Auto-save messages ---
if st.session_state.messages:
    chat_store.save_chat(
        st.session_state.chat_id,
        st.session_state.chat_title,
        st.session_state.messages,
    )

# --- Document upload ---
with st.container(border=True):
    st.markdown("<p class='section-label'>Upload Document</p>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload a file (.txt, .md, .csv, .pdf, .docx, .xlsx, .pptx, .jpg, .png)",
        type=["txt", "md", "csv", "pdf", "docx", "xlsx", "pptx", "jpg", "jpeg", "png", "json", "xml"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        st.session_state.md_raw = uploaded.read()
        st.session_state.md_name = uploaded.name

    if st.session_state.md_raw:
        col_a, col_b, col_c, col_d = st.columns([1.2, 1.2, 1.2, 1])
        md_ok = bool(st.session_state.md_text)
        can_index = md_ok and len(st.session_state.md_text.strip()) >= 20

        with col_a:
            if st.button("Convert to Markdown", disabled=md_ok, use_container_width=True):
                with st.spinner("Converting..."):
                    st.session_state.md_text = convert_to_markdown(
                        st.session_state.md_raw, st.session_state.md_name
                    )
                st.rerun()

        with col_b:
            if st.button("Add to Knowledge Base", disabled=not can_index, use_container_width=True):
                text = st.session_state.md_text
                with st.spinner("Chunking & embedding..."):
                    result = db.add_document(st.session_state.md_name, text)
                st.session_state.rag_log.append(
                    f"Indexed **{st.session_state.md_name}** — {result['chunks']} chunks "
                    f"({result['embedded']} with vectors)"
                )
                st.rerun()

        with col_c:
            if st.button("Summarize & Index", disabled=not can_index, use_container_width=True):
                with st.spinner("Summarizing and indexing..."):
                    summary_prompt = (
                        f"Summarize the following document in 3-4 sentences:\n\n"
                        f"{st.session_state.md_text[:2000]}"
                    )
                    summary_result = ai_engine.query_model(
                        summary_prompt,
                        "You are a business analyst. Provide concise summaries.",
                    )
                    summary_text = summary_result.text if summary_result.ok else "(summary failed)"
                    label = f"{st.session_state.md_name} (RAG summary)"
                    full_text = f"SUMMARY: {summary_text}\n\n---\n\n{st.session_state.md_text}"
                    result = db.add_document(label, full_text)
                st.session_state.rag_log.append(
                    f"Summarized & indexed **{st.session_state.md_name}** — "
                    f"{result['chunks']} chunks ({result['embedded']} with vectors)"
                )
                st.rerun()

        with col_d:
            if st.button("Clear", use_container_width=True):
                st.session_state.md_raw = None
                st.session_state.md_name = ""
                st.session_state.md_text = ""
                st.session_state.pop("_insight", None)
                st.rerun()

        # Status pills
        status_pills = [theme.status_badge(f"Loaded: {st.session_state.md_name}", "accent")]
        if st.session_state.md_text:
            status_pills.append(theme.status_badge("Converted", "success"))
        if st.session_state.get("_insight"):
            status_pills.append(theme.status_badge("Insight ready", "success"))
        st.markdown("&nbsp;&nbsp;" + " ".join(status_pills), unsafe_allow_html=True)

        if st.session_state.md_text:
            with st.expander(f"Markdown preview — {st.session_state.md_name}", expanded=False):
                st.text_area("", st.session_state.md_text, height=200, label_visibility="collapsed")
                st.download_button(
                    "Download .md",
                    st.session_state.md_text.encode("utf-8"),
                    f"{st.session_state.md_name}.md",
                    "text/markdown",
                )

        if st.session_state.get("_insight"):
            with st.expander("AI Insight", expanded=True):
                st.markdown(st.session_state["_insight"])
    else:
        theme.empty_state(
            icon_name="file-upload",
            title="No document loaded",
            message="Upload a file above to convert it, index it, or ask the AI about it.",
        )

# --- Knowledge base ---
with st.expander("Knowledge Base (sqlite-vec RAG)", expanded=bool(st.session_state.rag_log)):
    db.init_db()

    if st.session_state.rag_log:
        for msg in st.session_state.rag_log:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;padding:10px 12px;border-radius:10px;background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.18);margin-bottom:8px;'>"
                f"{theme.icon('check', size=16, color='var(--success)')}<span>{msg}</span></div>",
                unsafe_allow_html=True,
            )

    docs = db.list_documents()
    if docs:
        for d in docs:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{d['doc_name']}** — {d['chunks']} chunks, {d['embedded_count']} vectored")
            if c2.button("Delete", key=f"del_{d['doc_name']}", use_container_width=True):
                db.delete_document(d["doc_name"])
                st.rerun()
    else:
        st.caption("No documents indexed yet.")
    st.caption(f"Knowledge base: **{db.chunk_count()}** chunk(s) stored.")

st.divider()

# --- Chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_query := st.chat_input(
    "Ask about the uploaded document, your knowledge base, or anything else..."
):
    # Auto-title on first message
    if not st.session_state.messages:
        st.session_state.chat_title = user_query[:50] + ("..." if len(user_query) > 50 else "")

    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            context_parts = []
            if st.session_state.md_text:
                context_parts.append(
                    f"Document '{st.session_state.md_name}' (converted to Markdown):\n"
                    f"{st.session_state.md_text[:1500]}"
                )

            rag_results = db.search(user_query)
            if rag_results:
                rag_text = "\n".join(
                    f"[{r.source}] {r.content[:300]}" for r in rag_results[:2]
                )
                context_parts.append("Relevant context:\n" + rag_text)
            elif st.session_state.get("current_csv_context"):
                context_parts.append(
                    f"Dataset '{st.session_state.current_csv_name}':\n"
                    f"{st.session_state.current_csv_context[:1500]}"
                )
            else:
                context_parts.append("Context: Default business knowledge.")

            full_prompt = "\n\n".join(context_parts) + f"\n\nQuestion: {user_query}"
            if len(full_prompt) > 8000:
                full_prompt = full_prompt[:8000] + "\n\n[context truncated]"

            result = ai_engine.query_model(
                full_prompt,
                "You are a business analyst. Answer clearly using the provided context. "
                "If the context doesn't fully answer the question, say so and use general knowledge.",
            )

        if result.ok:
            st.markdown(result.text)
            st.session_state.messages.append({"role": "assistant", "content": result.text})
        else:
            st.error(result.error)
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {result.error}"})

    # Persist after each exchange
    chat_store.save_chat(
        st.session_state.chat_id,
        st.session_state.chat_title,
        st.session_state.messages,
    )
