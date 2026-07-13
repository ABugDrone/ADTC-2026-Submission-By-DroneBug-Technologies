import pandas as pd
import plotly.express as px
import streamlit as st

from modules.financial import FinancialAnalyzer, AFRICAN_CURRENCIES
from utils import ai_engine, theme

st.set_page_config(page_title="Financial Analyst · BusinessPilot AI", page_icon="", layout="wide")
theme.init_theme_state()
theme.inject_css()

with st.sidebar:
    theme.sidebar_nav("Financial Analyst")

theme.page_header("Financial Analyst", "Analyze margins, costs, and get CFO-style recommendations.")

if "finance_messages" not in st.session_state:
    st.session_state.finance_messages = []

currency_name = st.selectbox("Currency", list(AFRICAN_CURRENCIES.keys()), key="fin_cur")
sym = AFRICAN_CURRENCIES[currency_name]["symbol"]

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    with st.container(border=True):
        st.markdown("<p class='section-label'>Enter Figures</p>", unsafe_allow_html=True)
        revenue = st.number_input(f"Revenue ({sym})", value=100000, step=10000)
        cogs = st.number_input(f"COGS ({sym})", value=40000, step=5000)
        opex = st.number_input(f"OpEx ({sym})", value=30000, step=5000)

analyzer = FinancialAnalyzer(revenue, cogs, opex, currency_name)
metrics = analyzer.get_metrics()

with col2:
    with st.container(border=True):
        st.markdown("<p class='section-label'>Key Metrics</p>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("Gross Profit", f"{sym}{metrics['gross_profit']:,}")
        m1.metric("Gross Margin", f"{metrics['gross_margin']:.1f}%")
        m2.metric("Revenue", f"{sym}{metrics['revenue']:,}")
        m2.metric("Net Profit", f"{sym}{metrics['net_profit']:,}")

    with st.container(border=True):
        st.markdown("<p class='section-label'>Cost Breakdown</p>", unsafe_allow_html=True)
        cost_df = pd.DataFrame(
            {
                "Category": ["COGS", "OpEx", "Gross Profit"],
                "Amount": [metrics["cogs"], metrics["opex"], metrics["gross_profit"]],
            }
        )
        fig = px.bar(
            cost_df,
            x="Amount",
            y="Category",
            orientation="h",
            color="Category",
            color_discrete_map={
                "COGS": theme.palette()["danger"],
                "OpEx": theme.palette()["warning"],
                "Gross Profit": theme.palette()["success"],
            },
            template=theme.plotly_template(),
        )
        fig.update_layout(
            template=theme.plotly_template(),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

rc, cc = st.columns([1, 1], gap="large")

with rc:
    with st.container(border=True):
        st.markdown("<p class='section-label'>Executive Review</p>", unsafe_allow_html=True)
        if st.button("Generate CFO Summary", use_container_width=True):
            with st.spinner("Synthesizing..."):
                r = ai_engine.query_model(analyzer.build_review_prompt(), "You are a pragmatic CFO for African markets. Be hyper-concise.")
            if r.ok:
                st.markdown(r.text)
            else:
                st.error(r.error)

with cc:
    with st.container(border=True):
        st.markdown("<p class='section-label'>Finance Chat</p>", unsafe_allow_html=True)
        fi = st.chat_input("Ask about finance, budgeting, or investments...", key="fin_chat")
        if fi:
            ctx = (
                f"Current {currency_name} — Revenue: {sym}{revenue:,}, "
                f"COGS: {sym}{cogs:,}, OpEx: {sym}{opex:,}, "
                f"Gross Profit: {sym}{metrics['gross_profit']:,}, "
                f"Net Profit: {sym}{metrics['net_profit']:,}, "
                f"Gross Margin: {metrics['gross_margin']:.1f}%.\n\n"
                f"Question: {fi}"
            )
            with st.chat_message("user"):
                st.markdown(fi)
            st.session_state.finance_messages.append({"role": "user", "content": fi})
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    r = ai_engine.query_model(ctx, f"You are a financial advisor for African businesses. Reference specific {sym} amounts.")
                st.markdown(r.text if r.ok else r.error)
            st.session_state.finance_messages.append({"role": "assistant", "content": r.text if r.ok else r.error})

        for msg in st.session_state.finance_messages[-4:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
