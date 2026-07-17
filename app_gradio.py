import datetime
import os

import pandas as pd
import plotly.express as px
import gradio as gr

from modules.data_analysis import DataAnalyzer
from modules.financial import FinancialAnalyzer, AFRICAN_CURRENCIES
from modules.markitdown_skill import convert_to_markdown
from modules.notification import trigger_windows_notification
from modules.task_manager import TaskManager
from utils import ai_engine, chat_store, config, db, seed_kb

TaskManager.initialize()
db.init_db()
try:
    n = seed_kb.seed_knowledge_base()
except Exception:
    pass

LANG_SYSTEM_PROMPTS = {
    "English": "You are a helpful business assistant for African SMEs. Respond in English.",
    "Hausa": "Kai mai taimakon kasuwanci ne ga kananan kamfanoni a Afirka. Ka amsa da Hausar.",
}

def _lang_system(lang):
    return LANG_SYSTEM_PROMPTS.get(lang, LANG_SYSTEM_PROMPTS["English"])

def _check_model():
    try:
        import httpx
        r = httpx.get(f"{config.LLAMA_HOST}/v1/models", timeout=3)
        return "Connected" if r.status_code == 200 else "Not running"
    except Exception:
        return "Not running"

def _check_embed():
    r = ai_engine.embed_text("test")
    return f"{len(r.vector)}-dim vectors" if r.ok else "Not running"

def _check_kb():
    try:
        c = db.chunk_count()
        return f"{c} chunk(s) stored"
    except Exception:
        return "Unavailable"

def home_page():
    status_model = _check_model()
    status_embed = _check_embed()
    status_kb = _check_kb()
    return (
        f"### System Status\n\n"
        f"- **Chat model**: {config.LLAMA_HOST} — {status_model}\n"
        f"- **Embedding**: {status_embed}\n"
        f"- **Knowledge base**: {status_kb}\n\n"
        "Your offline AI workspace — nothing here leaves this machine."
    )

doc_state = gr.State(None)
doc_name_state = gr.State("")
doc_text_state = gr.State("")
rag_log_state = gr.State([])
chat_id_state = gr.State("")
chat_title_state = gr.State("")

finance_messages_state = gr.State([])

csv_df_state = gr.State(None)
csv_name_state = gr.State("")
csv_context_state = gr.State("")
csv_rag_log_state = gr.State([])
doc2_raw_state = gr.State(None)
doc2_name_state = gr.State("")
doc2_text_state = gr.State("")
doc2_rag_log_state = gr.State([])

def chat_with_rag(message, history, lang, doc_text, doc_name, rag_log):
    context_parts = []
    if doc_text:
        context_parts.append(f"Document '{doc_name}' (converted to Markdown):\n{doc_text[:1500]}")
    rag_results = db.search(message)
    if rag_results:
        rag_text = "\n".join(f"[{r.source}] {r.content[:300]}" for r in rag_results[:2])
        context_parts.append("Relevant context:\n" + rag_text)
    if not context_parts:
        context_parts.append("Context: Default business knowledge.")
    full_prompt = "\n\n".join(context_parts) + f"\n\nQuestion: {message}"
    if len(full_prompt) > 8000:
        full_prompt = full_prompt[:8000] + "\n\n[context truncated]"
    result = ai_engine.query_model(
        full_prompt,
        _lang_system(lang) + " Answer clearly using provided context.",
    )
    return result.text if result.ok else f"Error: {result.error}"

def upload_doc(file, doc_state, doc_name_state, doc_text_state, rag_log_state):
    if file is None:
        return doc_state, doc_name_state, doc_text_state, rag_log_state, ""
    raw = open(file, "rb").read()
    name = os.path.basename(file)
    return raw, name, "", rag_log_state, f"Loaded: {name}"

def convert_doc(doc_state, doc_name_state, doc_text_state):
    if doc_state is None:
        return doc_text_state, ""
    text = convert_to_markdown(doc_state, doc_name_state)
    return text, "Converted to Markdown"

def index_doc(doc_name_state, doc_text_state, rag_log_state):
    if not doc_text_state or len(doc_text_state.strip()) < 20:
        return rag_log_state, "Document too short to index"
    result = db.add_document(doc_name_state, doc_text_state)
    msg = f"Indexed **{doc_name_state}** — {result['chunks']} chunks ({result['embedded']} with vectors)"
    new_log = list(rag_log_state) + [msg]
    return new_log, msg

def classify_doc(doc_name_state, doc_text_state):
    if not doc_text_state:
        return ""
    prompt = (
        f"Analyze this document titled '{doc_name_state}':\n\n"
        f"{doc_text_state[:2000]}\n\n"
        "Identify recurring keywords and determine the document category. "
        "Respond in exactly this format:\n"
        "CATEGORY: [one of: Management, Marketing, Finance, Human Resources, Legal, Business Politics, Technical, General]\n"
        "KEYWORDS: [3-5 most frequent/relevant keywords comma-separated]\n"
        "REASON: [1 sentence explaining why based on keyword patterns]"
    )
    result = ai_engine.query_model(prompt, "You are a document analyst. Classify the document type based on keyword patterns.")
    return result.text if result.ok else f"Error: {result.error}"

def summarize_and_index(doc_name_state, doc_text_state, rag_log_state):
    if not doc_text_state:
        return rag_log_state, "No document text"
    summary_prompt = f"Summarize the following document in 3-4 sentences:\n\n{doc_text_state[:2000]}"
    summary_result = ai_engine.query_model(summary_prompt, "You are a business analyst. Provide concise summaries.")
    summary_text = summary_result.text if summary_result.ok else "(summary failed)"
    label = f"{doc_name_state} (RAG summary)"
    full_text = f"SUMMARY: {summary_text}\n\n---\n\n{doc_text_state}"
    result = db.add_document(label, full_text)
    msg = f"Summarized & indexed **{doc_name_state}** — {result['chunks']} chunks ({result['embedded']} with vectors)"
    new_log = list(rag_log_state) + [msg]
    return new_log, msg

def clear_doc():
    return None, "", "", None, None, []

def kb_list():
    docs = db.list_documents()
    if not docs:
        return "No documents indexed yet."
    lines = [f"- **{d['doc_name']}** — {d['chunks']} chunks, {d['embedded_count']} vectored" for d in docs]
    lines.append(f"\nTotal: **{db.chunk_count()}** chunk(s) stored.")
    return "\n".join(lines)

def delete_kb_doc(doc_name):
    db.delete_document(doc_name)
    return kb_list()

def save_chat_on_message(history, chat_id, chat_title):
    if not history:
        return chat_id, chat_title
    if not chat_id:
        chat_id = chat_store.new_chat_id()
    if not chat_title:
        chat_title = history[0][0][:50] + ("..." if len(history[0][0]) > 50 else "")
    chat_store.save_chat(chat_id, chat_title, history)
    return chat_id, chat_title

def load_chat_list():
    saved = chat_store.list_chats()
    if not saved:
        return []
    choices = [(f"{c['title'][:30]} ({c.get('message_count',0)} msgs)", c["id"]) for c in saved]
    return choices

def load_chat_by_id(chat_id):
    data = chat_store.load_chat(chat_id)
    if data:
        msgs = data.get("messages", [])
        title = data.get("title", "Untitled")
        return msgs, title, chat_id
    return [], "", ""

def delete_chat_by_id(chat_id):
    chat_store.delete_chat(chat_id)
    return [], "", ""

def new_chat():
    return [], "", chat_store.new_chat_id()

def finance_calc(revenue, cogs, opex, currency_name):
    analyzer = FinancialAnalyzer(revenue, cogs, opex, currency_name)
    metrics = analyzer.get_metrics()
    sym = metrics["currency"]["symbol"]
    cost_df = pd.DataFrame({
        "Category": ["COGS", "OpEx", "Gross Profit"],
        "Amount": [metrics["cogs"], metrics["opex"], metrics["gross_profit"]],
    })
    fig = px.bar(
        cost_df, x="Amount", y="Category", orientation="h", color="Category",
        color_discrete_map={"COGS": "#EF4444", "OpEx": "#F59E0B", "Gross Profit": "#10B981"},
        template="plotly_dark",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    summary = (
        f"**Revenue**: {sym}{metrics['revenue']:,}\n"
        f"**Gross Profit**: {sym}{metrics['gross_profit']:,} ({metrics['gross_margin']:.1f}%)\n"
        f"**Net Profit**: {sym}{metrics['net_profit']:,}\n"
        f"**COGS**: {sym}{cogs:,} | **OpEx**: {sym}{opex:,}"
    )
    return summary, fig

def finance_cfo_summary(revenue, cogs, opex, currency_name, lang):
    analyzer = FinancialAnalyzer(revenue, cogs, opex, currency_name)
    prompt = analyzer.build_review_prompt()
    result = ai_engine.query_model(prompt, _lang_system(lang) + " You are a pragmatic CFO for African markets. Be hyper-concise.")
    return result.text if result.ok else f"Error: {result.error}"

def finance_chat(message, history, revenue, cogs, opex, currency_name, lang):
    sym = AFRICAN_CURRENCIES[currency_name]["symbol"]
    metrics = FinancialAnalyzer(revenue, cogs, opex, currency_name).get_metrics()
    ctx = (
        f"Current {currency_name} — Revenue: {sym}{revenue:,}, "
        f"COGS: {sym}{cogs:,}, OpEx: {sym}{opex:,}, "
        f"Gross Profit: {sym}{metrics['gross_profit']:,}, "
        f"Net Profit: {sym}{metrics['net_profit']:,}, "
        f"Gross Margin: {metrics['gross_margin']:.1f}%.\n\n"
        f"Question: {message}"
    )
    result = ai_engine.query_model(ctx, _lang_system(lang) + f" You are a financial advisor for African businesses. Reference specific {sym} amounts.")
    return result.text if result.ok else result.error

def data_preview(file):
    if file is None:
        return None, "", "", None, ""
    df = DataAnalyzer.read_csv(file)
    analyzer = DataAnalyzer(df)
    ctx = analyzer.rich_context(20)
    return df, ctx, os.path.basename(file), df.head(12), f"Shape: {df.shape[0]} rows x {df.shape[1]} columns"

def data_analyze_csv(goal, csv_context, csv_name, lang):
    if not csv_context:
        return "No dataset loaded."
    prompt = DataAnalyzer.build_insight_prompt(csv_context, goal)
    result = ai_engine.query_model(prompt, _lang_system(lang) + " You are a senior data scientist. Answer with specific numbers.")
    return result.text if result.ok else result.error

def data_build_chart(x, y, chart_type, df):
    if df is None:
        return None
    template = "plotly_dark"
    if chart_type == "Bar":
        fig = px.bar(df, x=x, y=y, template=template)
    elif chart_type == "Line":
        fig = px.line(df, x=x, y=y, markers=True, template=template)
    elif chart_type == "Scatter":
        fig = px.scatter(df, x=x, y=y, template=template)
    else:
        return None
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def data_pie_chart(x, val, df):
    if df is None:
        return None
    template = "plotly_dark"
    if val == "Count":
        agg = df[x].value_counts().reset_index()
        agg.columns = [x, "count"]
        fig = px.pie(agg, names=x, values="count", template=template)
    else:
        fig = px.pie(df, names=x, values=val, template=template)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def data_qa_csv(question, csv_context, csv_name, lang):
    if not csv_context:
        return "No dataset loaded."
    ctx = f"Dataset '{csv_name}':\n{csv_context}\n\nQuestion: {question}"
    result = ai_engine.query_model(ctx, _lang_system(lang) + " You are a data analyst. Answer with specific numbers.")
    return result.text if result.ok else result.error

def data_index_csv(csv_name, df, csv_rag_log):
    if df is None:
        return csv_rag_log, "No dataset loaded."
    md_desc = f"DATASET: {csv_name}\n\nColumns: {', '.join(df.columns)}\n\nPreview:\n{df.head(10).to_markdown()}\n\nStatistical Summary:\n{df.describe(include='all').to_markdown()}"
    result = db.add_document(csv_name, md_desc)
    msg = f"Indexed dataset **{csv_name}** — {result['chunks']} chunks ({result['embedded']} with vectors)"
    new_log = list(csv_rag_log) + [msg]
    return new_log, msg

def doc2_upload(file, doc2_raw_state, doc2_name_state, doc2_text_state, doc2_rag_log_state):
    if file is None:
        return doc2_raw_state, doc2_name_state, doc2_text_state, doc2_rag_log_state, ""
    raw = open(file, "rb").read()
    name = os.path.basename(file)
    return raw, name, "", doc2_rag_log_state, f"Loaded: {name}"

def doc2_convert(doc2_raw_state, doc2_name_state):
    if doc2_raw_state is None:
        return "", ""
    text = convert_to_markdown(doc2_raw_state, doc2_name_state)
    return text, f"Converted ({len(text):,} chars)"

def doc2_index(doc2_name_state, doc2_text_state, doc2_rag_log_state):
    if not doc2_text_state or len(doc2_text_state.strip()) < 20:
        return doc2_rag_log_state, "Document too short to index"
    result = db.add_document(doc2_name_state, doc2_text_state)
    msg = f"Indexed **{doc2_name_state}** — {result['chunks']} chunks ({result['embedded']} with vectors)"
    new_log = list(doc2_rag_log_state) + [msg]
    return new_log, msg

def doc2_clear():
    return None, "", "", []

def doc2_ask(question, doc2_text_state, doc2_name_state, lang):
    if not doc2_text_state or not question:
        return ""
    prompt = f"Document '{doc2_name_state}':\n\n{doc2_text_state[:3000]}\n\nQuestion: {question}"
    result = ai_engine.query_model(prompt, _lang_system(lang) + " You are a business analyst.")
    return result.text if result.ok else result.error

def doc2_rag_search(query):
    if not query:
        return ""
    results = db.search(query)
    if not results:
        return "No relevant results found."
    lines = []
    for r in results[:5]:
        lines.append(f"**Source:** `{r.source}`\n{r.content[:400]}\n---")
    return "\n".join(lines)

def _parse_dt(dt_str):
    if not dt_str:
        return datetime.date.today().isoformat(), datetime.time(9, 0).isoformat()
    parts = dt_str.split(" ")
    date_part = parts[0] if parts else datetime.date.today().isoformat()
    time_part = parts[1] if len(parts) > 1 else "09:00:00"
    return date_part, time_part

def add_task(title, dt, priority):
    if not title:
        return "Title cannot be blank."
    date_str, time_str = _parse_dt(dt)
    TaskManager.add(title, date_str, time_str, priority)
    trigger_windows_notification(title="Task Added", message=f"Scheduled: '{title}' for {date_str}")
    return f"Pinned '{title}'!"

def list_tasks():
    tasks = TaskManager.get_all()
    if not tasks:
        return "No tasks scheduled yet."
    lines = []
    for i, t in enumerate(tasks):
        badge = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(t["priority"], "⚪")
        status = "✅" if t["status"] == "Completed" else "⏳"
        lines.append(f"{badge} **{t['title']}** — {t['date']} at {t['time']} | {t['priority']} | {status}")
        lines.append(f"  _Edit index: {i}_")
    return "\n".join(lines)

def prioritize_tasks(lang):
    tasks = TaskManager.get_all()
    if not tasks:
        no_tasks = "No tasks to prioritize." if lang == "English" else "Babu ayyuka da za a ba da fifiko."
        return no_tasks, ""
    tasks_text = "\n".join(f"- {t['title']} (Priority: {t['priority']}, Status: {t['status']})" for t in tasks)
    if lang == "Hausa":
        prompt1 = f"Jadawalin:\n{tasks_text}\n\nKa ba da shawarwari guda biyu game da tsarin da ya kamata in bi don kammala wadannan ayyuka, bisa ga gaggawar kasuwanci."
        prompt2 = f"Jadawalin:\n{tasks_text}\n\nA cikin jumla guda, ka nuna wani aiki da ya wuce lokaci ko kuma yana da hadari. Idan babu komai, ka faɗi haka."
        sp1 = "Kai babban jami'in ma'aikata ne. Ka zama kai tsaye."
        sp2 = "Kai mataimaki ne mai sanin hadari. Ka takaice."
    else:
        prompt1 = f"Schedule:\n{tasks_text}\n\nGive a 2-line strategic recommendation for the order I should tackle these tasks, based on business urgency."
        prompt2 = f"Schedule:\n{tasks_text}\n\nIn one short line, flag anything overdue or high-risk. If nothing looks risky, say so."
        sp1 = "You are an elite chief of staff. Be direct."
        sp2 = "You are a risk-aware ops assistant. Be concise."
    jobs = [
        {"prompt": prompt1, "system_prompt": _lang_system(lang) + " " + sp1},
        {"prompt": prompt2, "system_prompt": _lang_system(lang) + " " + sp2},
    ]
    results = ai_engine.query_model_many(jobs)
    r1 = results[0].text if results[0].ok else results[0].error
    r2 = results[1].text if results[1].ok else results[1].error
    return r1, r2

def edit_task_ui(idx, title, dt, priority):
    try:
        idx = int(idx)
    except (ValueError, TypeError):
        return "Invalid index."
    date_str, time_str = _parse_dt(dt)
    TaskManager.update_task(idx, title=title, date=date_str, time=time_str, priority=priority)
    return f"Task {idx} updated."

def delete_task_item(idx):
    try:
        idx = int(idx)
    except (ValueError, TypeError):
        return "Invalid index."
    TaskManager.delete_task(idx)
    return f"Task {idx} deleted."

def clear_completed_tasks():
    TaskManager.clear_completed()
    return "Completed tasks cleared."

with gr.Blocks(title="BusinessPilot AI") as demo:
    gr.Markdown("# BusinessPilot AI  \nYour offline AI workspace — nothing here leaves this machine.")
    lang_selector = gr.Radio(["English", "Hausa"], value="English", label="Language", info="Switch between English and Hausa")

    with gr.Tabs():
        with gr.TabItem("Home"):
            status_btn = gr.Button("Refresh Status")
            status_output = gr.Markdown()
            status_btn.click(fn=home_page, outputs=status_output)
            demo.load(fn=home_page, outputs=status_output)

        with gr.TabItem("Meetings & Tasks"):
            gr.Markdown("### Schedule Event / Task")
            with gr.Row():
                with gr.Column(scale=1):
                    task_title = gr.Textbox(label="Title", placeholder="e.g., Board Meeting")
                    task_dt = gr.DateTime(label="Date & Time", include_time=True, type="string")
                    task_priority = gr.Dropdown(["High", "Medium", "Low"], value="Medium", label="Priority")
                    task_add_btn = gr.Button("Save & Notify", variant="primary")
                    task_result = gr.Markdown()
                with gr.Column(scale=2):
                    gr.Markdown("### Current Agenda")
                    task_list = gr.Markdown()
                    refresh_tasks_btn = gr.Button("Refresh Tasks")
                    with gr.Row():
                        edit_idx = gr.Number(label="Edit Index", precision=0)
                        edit_title = gr.Textbox(label="New Title")
                        edit_priority = gr.Dropdown(["High", "Medium", "Low"], value="Medium", label="New Priority")
                    edit_btn = gr.Button("Update Task")
                    delete_btn = gr.Button("Delete Task", variant="stop")
                    clear_done_btn = gr.Button("Clear Completed")

            gr.Markdown("### AI Prioritization")
            ai_prio_btn = gr.Button("Re-Prioritize with AI")
            with gr.Row():
                prio_result = gr.Markdown(label="Recommendation")
                risk_result = gr.Markdown(label="Risk Flag")

            task_add_btn.click(fn=add_task, inputs=[task_title, task_dt, task_priority], outputs=task_result).then(fn=list_tasks, outputs=task_list)
            refresh_tasks_btn.click(fn=list_tasks, outputs=task_list)
            ai_prio_btn.click(fn=prioritize_tasks, inputs=[lang_selector], outputs=[prio_result, risk_result])
            edit_btn.click(fn=edit_task_ui, inputs=[edit_idx, edit_title, task_dt, edit_priority], outputs=task_result).then(fn=list_tasks, outputs=task_list)
            delete_btn.click(fn=delete_task_item, inputs=[edit_idx], outputs=task_result).then(fn=list_tasks, outputs=task_list)
            clear_done_btn.click(fn=clear_completed_tasks, outputs=task_result).then(fn=list_tasks, outputs=task_list)
            demo.load(fn=list_tasks, outputs=task_list)

        with gr.TabItem("Chat & Knowledge Base"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Upload Document")
                    doc_upload = gr.File(label="Upload file", file_types=[".txt", ".md", ".csv", ".pdf", ".docx", ".xlsx", ".pptx", ".jpg", ".jpeg", ".png", ".json", ".xml"])
                    doc_status = gr.Markdown()
                    with gr.Row():
                        doc_convert_btn = gr.Button("Convert to Markdown")
                        doc_index_btn = gr.Button("Add to KB")
                        doc_summarize_btn = gr.Button("Summarize & Index")
                        doc_classify_btn = gr.Button("Classify")
                        doc_clear_btn = gr.Button("Clear")
                    doc_classify_out = gr.Markdown()
                    doc_convert_status = gr.Markdown()
                    doc_index_status = gr.Markdown()
                    with gr.Accordion("Markdown Preview", open=False):
                        doc_preview = gr.TextArea(label="", lines=10)
                    with gr.Accordion("Knowledge Base", open=False):
                        kb_content = gr.Markdown()
                        kb_refresh_btn = gr.Button("Refresh KB")
                        kb_delete_name = gr.Textbox(label="Delete doc by name")
                        kb_delete_btn = gr.Button("Delete")
                with gr.Column(scale=2):
                    gr.Markdown("### Chat with Knowledge Base")
                    rag_chatbot = gr.Chatbot(height=400)
                    rag_msg = gr.Textbox(label="Message", placeholder="Ask about the uploaded document, your knowledge base, or anything else...")
                    rag_send_btn = gr.Button("Send", variant="primary")
                    rag_new_btn = gr.Button("New Chat")
                    with gr.Accordion("Saved Chats", open=False):
                        saved_chats_dd = gr.Dropdown(label="Select chat", choices=[], interactive=True)
                        saved_chats_refresh = gr.Button("Refresh list")
                        saved_chat_load_btn = gr.Button("Load selected")
                        saved_chat_del_btn = gr.Button("Delete selected")

            doc_upload.change(fn=upload_doc, inputs=[doc_upload, doc_state, doc_name_state, doc_text_state, rag_log_state], outputs=[doc_state, doc_name_state, doc_text_state, rag_log_state, doc_status])
            doc_convert_btn.click(fn=convert_doc, inputs=[doc_state, doc_name_state, doc_text_state], outputs=[doc_text_state, doc_convert_status]).then(fn=lambda t: t, inputs=[doc_text_state], outputs=[doc_preview])
            doc_index_btn.click(fn=index_doc, inputs=[doc_name_state, doc_text_state, rag_log_state], outputs=[rag_log_state, doc_index_status]).then(fn=kb_list, outputs=kb_content)
            doc_summarize_btn.click(fn=summarize_and_index, inputs=[doc_name_state, doc_text_state, rag_log_state], outputs=[rag_log_state, doc_index_status]).then(fn=kb_list, outputs=kb_content)
            doc_classify_btn.click(fn=classify_doc, inputs=[doc_name_state, doc_text_state], outputs=doc_classify_out)
            doc_clear_btn.click(fn=clear_doc, outputs=[doc_state, doc_name_state, doc_text_state, doc_status, doc_convert_status, doc_preview]).then(fn=kb_list, outputs=kb_content)
            kb_refresh_btn.click(fn=kb_list, outputs=kb_content)
            kb_delete_btn.click(fn=delete_kb_doc, inputs=[kb_delete_name], outputs=kb_content)

            def chat_fn(msg, history):
                if history is None:
                    history = []
                history = list(history)
                history.append([msg, None])
                reply = chat_with_rag(msg, history, lang_selector.value, doc_text_state.value, doc_name_state.value, rag_log_state.value)
                history[-1][1] = reply
                cid, ctitle = save_chat_on_message(history, chat_id_state.value, chat_title_state.value)
                return history, "", cid, ctitle

            rag_send_btn.click(fn=chat_fn, inputs=[rag_msg, rag_chatbot], outputs=[rag_chatbot, rag_msg, chat_id_state, chat_title_state])
            rag_msg.submit(fn=chat_fn, inputs=[rag_msg, rag_chatbot], outputs=[rag_chatbot, rag_msg, chat_id_state, chat_title_state])
            rag_new_btn.click(fn=new_chat, outputs=[rag_chatbot, chat_title_state, chat_id_state])

            saved_chats_refresh.click(fn=load_chat_list, outputs=[saved_chats_dd])
            saved_chat_load_btn.click(fn=load_chat_by_id, inputs=[saved_chats_dd], outputs=[rag_chatbot, chat_title_state, chat_id_state])
            saved_chat_del_btn.click(fn=delete_chat_by_id, inputs=[saved_chats_dd], outputs=[rag_chatbot, chat_title_state, chat_id_state])

        with gr.TabItem("Data & Charts"):
            gr.Markdown("### CSV Data Explorer")
            csv_file = gr.File(label="Upload CSV", file_types=[".csv"])
            csv_preview_table = gr.DataFrame(label="Preview", interactive=False)
            csv_info = gr.Markdown()

            gr.Markdown("### Ask the AI about this data")
            csv_goal = gr.Textbox(label="What do you want to know?", placeholder="e.g., sales trend, top product...")
            csv_analyze_btn = gr.Button("Analyze")
            csv_insight = gr.Markdown()

            gr.Markdown("### Build a chart")
            with gr.Row():
                csv_x = gr.Dropdown(label="X axis", choices=[], interactive=True)
                csv_y = gr.Dropdown(label="Y axis", choices=[], interactive=True)
                csv_chart_type = gr.Dropdown(["Bar", "Line", "Scatter", "Pie"], value="Bar", label="Chart type")
                csv_pie_val = gr.Dropdown(label="Values (Pie)", choices=[], interactive=True)
            csv_chart = gr.Plot(label="Chart")

            gr.Markdown("### Ask About This Data")
            csv_qa_input = gr.Textbox(label="Question", placeholder="Ask anything about this data...")
            csv_qa_btn = gr.Button("Ask")
            csv_qa_out = gr.Markdown()

            gr.Markdown("### Index to Knowledge Base")
            csv_index_btn = gr.Button("Index this dataset")
            csv_index_status = gr.Markdown()

            def csv_upload_handler(file):
                df, ctx, name, preview, info = data_preview(file)
                cols = list(df.columns) if df is not None else []
                num_cols = df.select_dtypes(include=["number"]).columns.tolist() if df is not None else []
                return df, ctx, name, preview, info, gr.Dropdown(choices=cols), gr.Dropdown(choices=num_cols), gr.Dropdown(choices=["Count"] + num_cols)

            csv_file.change(fn=csv_upload_handler, inputs=[csv_file], outputs=[csv_df_state, csv_context_state, csv_name_state, csv_preview_table, csv_info, csv_x, csv_y, csv_pie_val])

            csv_analyze_btn.click(fn=data_analyze_csv, inputs=[csv_goal, csv_context_state, csv_name_state, lang_selector], outputs=csv_insight)

            def chart_handler(x, y, chart_type, pie_val, df):
                if chart_type == "Pie":
                    return data_pie_chart(x, pie_val, df)
                return data_build_chart(x, y, chart_type, df)

            csv_chart_type.change(fn=chart_handler, inputs=[csv_x, csv_y, csv_chart_type, csv_pie_val, csv_df_state], outputs=csv_chart)
            csv_x.change(fn=chart_handler, inputs=[csv_x, csv_y, csv_chart_type, csv_pie_val, csv_df_state], outputs=csv_chart)
            csv_y.change(fn=chart_handler, inputs=[csv_x, csv_y, csv_chart_type, csv_pie_val, csv_df_state], outputs=csv_chart)
            csv_pie_val.change(fn=chart_handler, inputs=[csv_x, csv_y, csv_chart_type, csv_pie_val, csv_df_state], outputs=csv_chart)

            csv_qa_btn.click(fn=data_qa_csv, inputs=[csv_qa_input, csv_context_state, csv_name_state, lang_selector], outputs=csv_qa_out)
            csv_index_btn.click(fn=data_index_csv, inputs=[csv_name_state, csv_df_state, csv_rag_log_state], outputs=[csv_rag_log_state, csv_index_status])

        with gr.TabItem("Financial Analyst"):
            gr.Markdown("### Financial Analyst")
            fin_cur = gr.Dropdown(list(AFRICAN_CURRENCIES.keys()), value="Nigerian Naira", label="Currency")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Enter Figures")
                    fin_revenue = gr.Number(label="Revenue", value=100000, step=10000)
                    fin_cogs = gr.Number(label="COGS", value=40000, step=5000)
                    fin_opex = gr.Number(label="OpEx", value=30000, step=5000)
                    fin_calc_btn = gr.Button("Calculate", variant="primary")
                with gr.Column():
                    gr.Markdown("#### Key Metrics")
                    fin_metrics = gr.Markdown()
                    fin_chart = gr.Plot(label="Cost Breakdown")

            fin_cfo_btn = gr.Button("Generate CFO Summary")
            fin_cfo_out = gr.Markdown()

            gr.Markdown("#### Finance Chat")
            fin_chat_input = gr.Textbox(label="Ask about finance, budgeting, or investments...")
            fin_chat_send = gr.Button("Ask")
            fin_chat_out = gr.Markdown()

            fin_calc_btn.click(fn=finance_calc, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur], outputs=[fin_metrics, fin_chart])
            fin_cfo_btn.click(fn=finance_cfo_summary, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur, lang_selector], outputs=fin_cfo_out)
            fin_chat_send.click(fn=finance_chat, inputs=[fin_chat_input, finance_messages_state, fin_revenue, fin_cogs, fin_opex, fin_cur, lang_selector], outputs=fin_chat_out)

            demo.load(fn=finance_calc, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur], outputs=[fin_metrics, fin_chart])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8081, share=False, theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate"), css="footer {display:none !important}")
