import pandas as pd
import plotly.express as px
import streamlit as st

from modules.data_analysis import DataAnalyzer
from modules.markitdown_skill import convert_to_markdown
from utils import ai_engine, theme

st.set_page_config(page_title="Data & Charts · BusinessPilot AI", page_icon="", layout="wide")
theme.init_theme_state()
theme.inject_css()

with st.sidebar:
    theme.sidebar_nav("Data & Charts")

theme.page_header("Data Explorer & Charts", "Upload a CSV or document to preview, analyze, and build charts.")

# --- Session state for document mode ---
for k in ("doc_raw", "doc_name", "doc_text"):
    if k not in st.session_state:
        st.session_state[k] = None if k == "doc_raw" else ""

upload_type = st.radio("Upload type", ["CSV (data)", "Document (PDF, DOCX, XLSX, ...)"], horizontal=True, label_visibility="collapsed")

if upload_type.startswith("CSV"):
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is not None:
        df = DataAnalyzer.read_csv(uploaded_file)
        analyzer = DataAnalyzer(df)
        st.session_state.current_csv_context = analyzer.rich_context(20)
        st.session_state.current_csv_name = uploaded_file.name
        st.session_state.current_csv_df = df
        st.session_state.doc_raw = None
        st.session_state.doc_text = ""

        tab1, tab2, tab3 = st.tabs(["Preview", "AI Insight", "Charts"])

        with tab1:
            row_choice = st.radio("Rows", ["5", "12", "All"], horizontal=True, label_visibility="collapsed")
            if row_choice == "All":
                with st.expander("Full Dataset", expanded=True):
                    st.dataframe(df, use_container_width=True, height=600)
                    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), uploaded_file.name, "text/csv")
            else:
                st.dataframe(analyzer.preview(int(row_choice)), use_container_width=True)
            st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")

        with tab2:
            with st.container(border=True):
                st.markdown("<p class='section-label'>Ask the AI about this data</p>", unsafe_allow_html=True)
                analysis_goal = st.text_input("What do you want to know?", placeholder="e.g., sales trend, top product...", label_visibility="collapsed")
                if st.button("Analyze", use_container_width=True):
                    prompt = DataAnalyzer.build_insight_prompt(st.session_state.current_csv_context, analysis_goal)
                    with st.spinner("Analyzing..."):
                        r = ai_engine.query_model(prompt, "You are a senior data scientist. Answer with specific numbers.")
                    if r.ok:
                        st.success(r.text)
                    else:
                        st.error(r.error)

        with tab3:
            with st.container(border=True):
                st.markdown("<p class='section-label'>Build a chart</p>", unsafe_allow_html=True)
                numeric_cols = analyzer.numeric_columns()
                all_cols = analyzer.all_columns()
                if numeric_cols:
                    template = theme.plotly_template()
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        x_axis = st.selectbox("X", all_cols, key="ch_x")
                    with c2:
                        y_axis = st.selectbox("Y", numeric_cols, key="ch_y")
                    with c3:
                        chart_type = st.selectbox("Type", ["Bar", "Line", "Scatter", "Pie"], key="ch_type")

                    if chart_type == "Pie":
                        if x_axis != y_axis:
                            val = st.selectbox("Values", ["Count"] + numeric_cols, key="ch_pie_val")
                            if val == "Count":
                                agg = df[x_axis].value_counts().reset_index()
                                agg.columns = [x_axis, "count"]
                                fig = px.pie(agg, names=x_axis, values="count", template=template)
                            else:
                                fig = px.pie(df, names=x_axis, values=val, template=template)
                        else:
                            fig = px.pie(df, names=x_axis, template=template)
                    elif chart_type == "Bar":
                        fig = px.bar(df, x=x_axis, y=y_axis, template=template)
                    elif chart_type == "Line":
                        fig = px.line(df, x=x_axis, y=y_axis, markers=True, template=template)
                    else:
                        fig = px.scatter(df, x=x_axis, y=y_axis, template=template)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No numeric columns found.")

        st.divider()
        with st.container(border=True):
            st.markdown("<p class='section-label'>Ask About This Data</p>", unsafe_allow_html=True)
            data_qa = st.chat_input("Ask anything about this data...", key="data_qa")
            if data_qa:
                with st.chat_message("user"):
                    st.markdown(data_qa)
                ctx = f"Dataset '{st.session_state.current_csv_name}':\n{st.session_state.current_csv_context}\n\nQuestion: {data_qa}"
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        r = ai_engine.query_model(ctx, "You are a data analyst. Answer with specific numbers.")
                    st.markdown(r.text if r.ok else r.error)

else:
    uploaded_doc = st.file_uploader(
        "Upload a document (.txt, .md, .pdf, .docx, .xlsx, .pptx, .jpg, .png)",
        type=["txt", "md", "csv", "pdf", "docx", "xlsx", "pptx", "jpg", "jpeg", "png", "json", "xml"],
        label_visibility="collapsed",
    )

    if uploaded_doc is not None:
        st.session_state.doc_raw = uploaded_doc.read()
        st.session_state.doc_name = uploaded_doc.name

    if st.session_state.doc_raw:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Convert to Markdown", use_container_width=True):
                with st.spinner("Converting..."):
                    st.session_state.doc_text = convert_to_markdown(
                        st.session_state.doc_raw, st.session_state.doc_name
                    )
                st.rerun()
        with col_b:
            if st.button("Clear", use_container_width=True):
                st.session_state.doc_raw = None
                st.session_state.doc_name = ""
                st.session_state.doc_text = ""
                st.rerun()

        if st.session_state.doc_text:
            st.caption(f"**{st.session_state.doc_name}** — {len(st.session_state.doc_text):,} chars converted")

            doc_tab1, doc_tab2 = st.tabs(["Preview", "Ask AI"])

            with doc_tab1:
                with st.expander("Converted text", expanded=True):
                    st.text_area("", st.session_state.doc_text[:5000], height=300, label_visibility="collapsed")
                    if len(st.session_state.doc_text) > 5000:
                        st.caption(f"Showing first 5,000 of {len(st.session_state.doc_text):,} chars")

            with doc_tab2:
                with st.container(border=True):
                    st.markdown("<p class='section-label'>Ask about this document</p>", unsafe_allow_html=True)
                    doc_query = st.text_input("Your question", placeholder="e.g., summarize, extract key points...", label_visibility="collapsed")
                    if st.button("Ask", use_container_width=True):
                        prompt = (
                            f"Document '{st.session_state.doc_name}':\n\n"
                            f"{st.session_state.doc_text[:3000]}\n\n"
                            f"Question: {doc_query}"
                        )
                        with st.spinner("Thinking..."):
                            r = ai_engine.query_model(prompt, "You are a business analyst.")
                        if r.ok:
                            st.success(r.text)
                        else:
                            st.error(r.error)
    else:
        theme.empty_state(
            icon_name="table",
            title="No document loaded",
            message="Upload a document above to convert and analyze it with AI.",
        )
