import pandas as pd
import plotly.express as px
import streamlit as st

from modules.data_analysis import DataAnalyzer
from utils import ai_engine, theme

st.set_page_config(page_title="Data & Charts · BusinessPilot AI", page_icon="", layout="wide")
theme.init_theme_state()
theme.inject_css()

with st.sidebar:
    theme.sidebar_nav("Data & Charts")

theme.page_header("Data Explorer & Charts", "Upload a CSV to preview, analyze, and build charts.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

if uploaded_file is not None:
    df = DataAnalyzer.read_csv(uploaded_file)
    analyzer = DataAnalyzer(df)
    st.session_state.current_csv_context = analyzer.rich_context(20)
    st.session_state.current_csv_name = uploaded_file.name
    st.session_state.current_csv_df = df

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
    theme.empty_state(
        icon_name="table",
        title="No dataset loaded",
        message="Upload a CSV file above to preview rows, generate AI insights, and build interactive charts.",
    )
