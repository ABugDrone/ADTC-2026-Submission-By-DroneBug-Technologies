import datetime
import os

# Disable ALL telemetry before importing gradio
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

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

    def _badge(ok, label):
        color = "#4ade80" if ok else "#f87171"
        bg = "rgba(34,197,94,0.15)" if ok else "rgba(239,68,68,0.15)"
        border = "1px solid rgba(34,197,94,0.3)" if ok else "1px solid rgba(239,68,68,0.3)"
        return f"<span style='font-size:11px;font-weight:600;color:{color};background:{bg};border:{border};padding:3px 8px;border-radius:999px;'>{label}</span>"

    _card = "background:rgba(30,41,59,0.85);border:1px solid rgba(59,130,246,0.25);border-radius:12px;padding:14px;"

    cards = (
        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;'>"
        f"<div style='{_card}'>"
        f"<p style='font-size:13px;font-weight:500;color:#94a3b8;margin:0 0 4px;'>Chat model</p>"
        f"<p style='font-size:12px;color:#64748b;margin:0 0 10px;'>{config.LLAMA_HOST}</p>"
        f"{_badge(status_model=='Connected', status_model)}</div>"
        f"<div style='{_card}'>"
        f"<p style='font-size:13px;font-weight:500;color:#94a3b8;margin:0 0 4px;'>Embedding model</p>"
        f"<p style='font-size:12px;color:#64748b;margin:0 0 10px;'>{config.LLAMA_HOST}</p>"
        f"{_badge('dim' in status_embed, status_embed)}</div>"
        f"<div style='{_card}'>"
        f"<p style='font-size:13px;font-weight:500;color:#94a3b8;margin:0 0 4px;'>Knowledge base</p>"
        f"<p style='font-size:12px;color:#64748b;margin:0 0 10px;'>sqlite-vec, local file</p>"
        f"{_badge('chunk' in status_kb, status_kb)}</div></div>"
    )

    tasks = TaskManager.get_all()
    pri_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
    items = ""
    for t in tasks[:20]:
        pri = t.get("priority", "Medium")
        pc = pri_colors.get(pri, "#94a3b8")
        icon = "\u2705" if t.get("status") == "Completed" else "\u23f3"
        items += (
            f"<div style='display:flex;align-items:center;justify-content:space-between;padding:8px 10px;border:1px solid rgba(59,130,246,0.2);border-radius:8px;margin-bottom:6px;background:rgba(15,23,42,0.5);'>"
            f"<div><p style='font-size:13px;margin:0;color:#e2e8f0;'>{icon} {t['title']}</p>"
            f"<p style='font-size:11px;margin:0;color:#64748b;'>{t.get('date','')} {t.get('time','')}</p></div>"
            f"<span style='font-size:11px;font-weight:600;color:#fff;background:{pc};padding:3px 10px;border-radius:999px;'>{pri}</span></div>"
        )
    if not items:
        items = "<p style='font-size:13px;color:#64748b;margin:0;'>No tasks scheduled yet.</p>"

    agenda = (
        f"<div style='{_card}'>"
        f"<p style='font-size:13px;font-weight:500;color:#94a3b8;margin:0 0 10px;'>Todays agenda</p>"
        f"<div style='max-height:300px;overflow-y:auto;'>{items}</div></div>"
    )

    footer = (
        f"<p style='font-size:13px;color:#64748b;margin:16px 0 0;'>Your offline AI workspace \u2014 nothing here leaves this machine.</p>"
    )

    return cards + agenda + footer

doc_state = gr.State(None)
doc_name_state = gr.State("")
doc_text_state = gr.State("")
rag_log_state = gr.State([])
chat_id_state = gr.State("")
chat_title_state = gr.State("")

finance_messages_state = gr.State([])

csv_meta_state = gr.State(None)  # {name, cols, num_cols, shape_row, shape_col, filepath}
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
    filepath = str(file)
    raw = open(filepath, "rb").read()
    name = os.path.basename(filepath)
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
        # Gradio 6: extract first user message content
        first_msg = next((m.get("content", "") for m in history if m.get("role") == "user"), "")
        chat_title = first_msg[:50] + ("..." if len(first_msg) > 50 else "")
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
        # Convert old tuple format to new messages format for Gradio 6
        converted = []
        for m in msgs:
            if isinstance(m, dict) and "role" in m:
                converted.append(m)
            elif isinstance(m, (list, tuple)) and len(m) == 2:
                converted.append({"role": "user", "content": str(m[0])})
                converted.append({"role": "assistant", "content": str(m[1])})
        return converted, title, chat_id
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
        color_discrete_map={"COGS": "#ef4444", "OpEx": "#f59e0b", "Gross Profit": "#10b981"},
        template="plotly_dark",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="#1e293b", plot_bgcolor="#0f172a", showlegend=False,
                      font=dict(color="#e2e8f0", family="Segoe UI, Arial, sans-serif"))
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

def _csv_to_markdown(filepath, name):
    filepath = str(filepath)
    df = DataAnalyzer.read_csv(filepath)
    md = f"DATASET: {name}\n\n"
    md += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n\n"
    md += "## Columns\n"
    for c in df.columns:
        md += f"- **{c}**: {df[c].dtype}"
        if pd.api.types.is_numeric_dtype(df[c]):
            md += f" (min={df[c].min()}, max={df[c].max()}, mean={df[c].mean():.2f})"
        elif df[c].nunique() < 20:
            md += f" (unique values: {', '.join(str(v) for v in df[c].unique()[:10])})"
        else:
            md += f" (unique={df[c].nunique()})"
        md += "\n"
    md += "\n## Sample rows (first 5)\n"
    md += df.head(5).to_markdown(index=False)
    md += "\n\n## Summary statistics\n"
    try:
        md += df.describe(include='all').to_markdown()
    except Exception:
        md += df.describe().to_markdown()
    del df
    return md

def csv_process_and_index(filepath):
    filepath = str(filepath)
    name = os.path.basename(filepath)
    md = _csv_to_markdown(filepath, name)
    result = db.add_document(name, md)
    df = DataAnalyzer.read_csv(filepath)
    cols = list(df.columns)
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    shape = df.shape
    del df
    meta = {"name": name, "cols": cols, "num_cols": num_cols, "shape_row": shape[0], "shape_col": shape[1], "filepath": filepath}
    msg = f"Auto-indexed **{name}** — {result['chunks']} chunks, {result['embedded']} vectors. Ask questions below."
    return meta, msg

def data_qa_csv(question, meta, lang):
    if not meta:
        return "No dataset loaded. Upload a CSV first."
    rag_results = db.search(question)
    context = ""
    if rag_results:
        context = "\n".join(f"[{r.source}] {r.content[:500]}" for r in rag_results[:2])
    else:
        context = f"Dataset: {meta['name']} ({meta['shape_row']} rows, {meta['shape_col']} cols, columns: {', '.join(meta['cols'])})"
    prompt = f"{context}\n\nQuestion: {question}"
    result = ai_engine.query_model(prompt, _lang_system(lang) + " You are a data analyst. Answer with specific numbers.")
    return result.text if result.ok else result.error

def data_build_chart(x, y, chart_type, pie_val, meta):
    if not meta:
        return None
    df = DataAnalyzer.read_csv(str(meta["filepath"]))
    template = "plotly_dark"
    color_seq = ["#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"]
    if chart_type == "Pie":
        if pie_val == "Count":
            agg = df[x].value_counts().reset_index()
            agg.columns = [x, "count"]
            fig = px.pie(agg, names=x, values="count", template=template, color_discrete_sequence=color_seq)
        else:
            fig = px.pie(df, names=x, values=pie_val, template=template, color_discrete_sequence=color_seq)
    elif chart_type == "Bar":
        fig = px.bar(df, x=x, y=y, template=template, color_discrete_sequence=color_seq)
    elif chart_type == "Line":
        fig = px.line(df, x=x, y=y, markers=True, template=template, color_discrete_sequence=color_seq)
    elif chart_type == "Scatter":
        fig = px.scatter(df, x=x, y=y, template=template, color_discrete_sequence=color_seq)
    else:
        del df
        return None
    fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0", family="Segoe UI, Arial, sans-serif"))
    del df
    return fig

def doc2_upload(file, doc2_raw_state, doc2_name_state, doc2_text_state, doc2_rag_log_state):
    if file is None:
        return doc2_raw_state, doc2_name_state, doc2_text_state, doc2_rag_log_state, ""
    filepath = str(file)
    raw = open(filepath, "rb").read()
    name = os.path.basename(filepath)
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

CUSTOM_THEME = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")

CUSTOM_CSS = """
* { font-family: 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif !important; }

.gradio-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%) !important;
    min-height: 100vh !important;
    max-width: 100% !important;
}

.gradio-container > .main > div:first-child {
    text-align: center;
    padding: 2rem 1rem !important;
    margin-bottom: 1.5rem !important;
    background: rgba(15, 23, 42, 0.8) !important;
    border-bottom: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 12px !important;
}

.gradio-container > .main > div:first-child h1 {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0.5rem !important;
}

.gradio-container > .main > div:first-child p {
    color: #94a3b8 !important;
    font-size: 1.1rem !important;
    margin-top: 0.5rem !important;
}

/* Tab styling */
.tabs {
    background: transparent !important;
    border: none !important;
}

.tab-item {
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    margin: 0 4px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}

.tab-item:hover {
    background: rgba(59, 130, 246, 0.15) !important;
    color: #60a5fa !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    transform: translateY(-2px) !important;
}

.tab-item.selected {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4) !important;
}

/* Cards for sections */
.card {
    background: rgba(30, 41, 59, 0.95) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(10px) !important;
}

/* Buttons */
button.primary {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}

button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
}

button.secondary {
    background: rgba(51, 65, 85, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    color: #cbd5e1 !important;
}

button.secondary:hover {
    background: rgba(59, 130, 246, 0.2) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    color: #60a5fa !important;
}

button.stop {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
}

/* Inputs */
input, textarea, select {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    transition: all 0.2s ease !important;
}

input:focus, textarea:focus, select:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

label {
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

/* Chatbot */
.chatbot {
    background: rgba(30, 41, 59, 0.95) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

.chatbot .message {
    padding: 1rem !important;
    border-radius: 10px !important;
    margin: 0.5rem !important;
}

.chatbot .message.user {
    background: rgba(59, 130, 246, 0.15) !important;
    border-left: 3px solid #3b82f6 !important;
}

.chatbot .message.bot {
    background: rgba(139, 92, 246, 0.15) !important;
    border-left: 3px solid #8b5cf6 !important;
}

/* Status indicators */
.status-connected {
    color: #22c55e !important;
    font-weight: 600 !important;
}

.status-disconnected {
    color: #ef4444 !important;
    font-weight: 600 !important;
}

/* Accordion */
.accordion {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 10px !important;
    margin: 0.5rem 0 !important;
}

.accordion-header {
    background: rgba(51, 65, 85, 0.8) !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}

/* File upload */
.file-upload {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 2px dashed rgba(59, 130, 246, 0.3) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    text-align: center !important;
    transition: all 0.2s ease !important;
}

.file-upload:hover {
    border-color: #3b82f6 !important;
    background: rgba(59, 130, 246, 0.05) !important;
}

/* Dataframe */
.dataframe {
    background: rgba(30, 41, 59, 0.95) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 10px !important;
}

.dataframe th {
    background: rgba(51, 65, 85, 0.8) !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

.dataframe td {
    color: #cbd5e1 !important;
}

/* Markdown */
markdown {
    color: #e2e8f0 !important;
}

markdown h1, markdown h2, markdown h3, markdown h4 {
    color: #3b82f6 !important;
    font-weight: 700 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}

markdown ul, markdown ol {
    padding-left: 1.5rem !important;
    color: #cbd5e1 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px !important;
}

::-webkit-scrollbar-track {
    background: rgba(30, 41, 59, 0.5) !important;
}

::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.4) !important;
    border-radius: 4px !important;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.6) !important;
}

/* Hide Gradio footer */
footer {
    display: none !important;
}

/* Language radio */
.radio {
    background: rgba(30, 41, 59, 0.9) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 10px !important;
    padding: 0.75rem !important;
}

/* Section headers */
.section-header {
    color: #3b82f6 !important;
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    margin-bottom: 1rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 2px solid rgba(59, 130, 246, 0.2) !important;
}
"""

with gr.Blocks(title="BusinessPilot AI") as demo:
    gr.Markdown("# BusinessPilot AI  \nYour offline AI workspace — nothing here leaves this machine.")
    lang_selector = gr.Radio(["English", "Hausa"], value="English", label="Language", info="🌍 Switch between English and Hausa")

    with gr.Tabs():
        with gr.TabItem("Home"):
            status_btn = gr.Button("🔄 Refresh Status", variant="primary")
            status_output = gr.Markdown()
            status_btn.click(fn=home_page, outputs=status_output)
            demo.load(fn=home_page, outputs=status_output)

        with gr.TabItem("📅 Meetings & Tasks"):
            gr.Markdown('<p class="section-header">Schedule Event / Task</p>')
            with gr.Row():
                with gr.Column(scale=1):
                    task_title = gr.Textbox(label="Title", placeholder="e.g., Board Meeting")
                    task_dt = gr.DateTime(label="Date & Time", include_time=True, type="string")
                    task_priority = gr.Dropdown(["High", "Medium", "Low"], value="Medium", label="Priority")
                    task_add_btn = gr.Button("💾 Save & Notify", variant="primary")
                    task_result = gr.Markdown()
                with gr.Column(scale=2):
                    gr.Markdown('<p class="section-header">Current Agenda</p>')
                    task_list = gr.Markdown()
                    refresh_tasks_btn = gr.Button("🔄 Refresh Tasks")
                    with gr.Row():
                        edit_idx = gr.Number(label="Edit Index", precision=0)
                        edit_title = gr.Textbox(label="New Title")
                        edit_priority = gr.Dropdown(["High", "Medium", "Low"], value="Medium", label="New Priority")
                    edit_btn = gr.Button("✏️ Update Task")
                    delete_btn = gr.Button("🗑️ Delete Task", variant="stop")
                    clear_done_btn = gr.Button("🧹 Clear Completed")

            gr.Markdown('<p class="section-header">AI Prioritization</p>')
            ai_prio_btn = gr.Button("🧠 Re-Prioritize with AI", variant="primary")
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

        with gr.TabItem("💬 Chat & Knowledge Base"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown('<p class="section-header">Upload Document</p>')
                    doc_upload = gr.File(label="Upload file", file_types=[".txt", ".md", ".csv", ".pdf", ".docx", ".xlsx", ".pptx", ".jpg", ".jpeg", ".png", ".json", ".xml"])
                    doc_status = gr.Markdown()
                    with gr.Row():
                        doc_convert_btn = gr.Button("📝 Convert to MD")
                        doc_index_btn = gr.Button("📚 Add to KB")
                    with gr.Row():
                        doc_summarize_btn = gr.Button("📋 Summarize & Index")
                        doc_classify_btn = gr.Button("🏷️ Classify")
                        doc_clear_btn = gr.Button("❌ Clear")
                    doc_classify_out = gr.Markdown()
                    doc_convert_status = gr.Markdown()
                    doc_index_status = gr.Markdown()
                    with gr.Accordion("Markdown Preview", open=False):
                        doc_preview = gr.TextArea(label="", lines=10)
                    with gr.Accordion("Knowledge Base", open=False):
                        kb_content = gr.Markdown()
                        kb_refresh_btn = gr.Button("🔄 Refresh KB")
                        kb_delete_name = gr.Textbox(label="Delete doc by name")
                        kb_delete_btn = gr.Button("🗑️ Delete")
                with gr.Column(scale=2):
                    gr.Markdown('<p class="section-header">Chat with Knowledge Base</p>')
                    rag_chatbot = gr.Chatbot(height=450)
                    rag_msg = gr.Textbox(label="Message", placeholder="🔍 Ask about your documents, knowledge base, or anything else...")
                    with gr.Row():
                        rag_send_btn = gr.Button("📤 Send", variant="primary")
                        rag_new_btn = gr.Button("✨ New Chat")
                    with gr.Accordion("Saved Chats", open=False):
                        saved_chats_dd = gr.Dropdown(label="Select chat", choices=[], interactive=True)
                        with gr.Row():
                            saved_chats_refresh = gr.Button("🔄 Refresh")
                            saved_chat_load_btn = gr.Button("📂 Load")
                            saved_chat_del_btn = gr.Button("🗑️ Delete")

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
                # Gradio 6: messages format with {role, content}
                history.append({"role": "user", "content": msg})
                reply = chat_with_rag(msg, history, lang_selector.value, doc_text_state.value, doc_name_state.value, rag_log_state.value)
                history.append({"role": "assistant", "content": reply})
                cid, ctitle = save_chat_on_message(history, chat_id_state.value, chat_title_state.value)
                return history, "", cid, ctitle

            rag_send_btn.click(fn=chat_fn, inputs=[rag_msg, rag_chatbot], outputs=[rag_chatbot, rag_msg, chat_id_state, chat_title_state])
            rag_msg.submit(fn=chat_fn, inputs=[rag_msg, rag_chatbot], outputs=[rag_chatbot, rag_msg, chat_id_state, chat_title_state])
            rag_new_btn.click(fn=new_chat, outputs=[rag_chatbot, chat_title_state, chat_id_state])

            saved_chats_refresh.click(fn=load_chat_list, outputs=[saved_chats_dd])
            saved_chat_load_btn.click(fn=load_chat_by_id, inputs=[saved_chats_dd], outputs=[rag_chatbot, chat_title_state, chat_id_state])
            saved_chat_del_btn.click(fn=delete_chat_by_id, inputs=[saved_chats_dd], outputs=[rag_chatbot, chat_title_state, chat_id_state])

        with gr.TabItem("📊 Data & Charts"):
            gr.Markdown('<p class="section-header">CSV Data Explorer</p>')
            csv_file = gr.File(label="Upload CSV", file_types=[".csv"])
            csv_status = gr.Markdown()
            csv_preview_table = gr.DataFrame(label="Preview", interactive=False)
            csv_info = gr.Markdown()

            gr.Markdown('<p class="section-header">Ask About This Data (English/Hausa)</p>')
            csv_qa_input = gr.Textbox(label="Question", placeholder="💬 Ask anything about this data...")
            csv_qa_btn = gr.Button("🗣️ Ask", variant="primary")
            csv_qa_out = gr.Markdown()

            gr.Markdown('<p class="section-header">Build a Chart</p>')
            with gr.Row():
                csv_x = gr.Dropdown(label="X axis", choices=[], interactive=True)
                csv_y = gr.Dropdown(label="Y axis", choices=[], interactive=True)
                csv_chart_type = gr.Dropdown(["Bar", "Line", "Scatter", "Pie"], value="Bar", label="Chart type")
                csv_pie_val = gr.Dropdown(label="Values (Pie)", choices=[], interactive=True)
            csv_build_btn = gr.Button("📊 Build Chart", variant="primary")
            csv_chart = gr.Plot(label="Chart")

            def csv_upload_handler(file):
                if file is None:
                    return None, "", None, [], [], []
                meta, msg = csv_process_and_index(file)
                df = DataAnalyzer.read_csv(str(file))
                preview = df.head(12)
                info = f"Shape: {df.shape[0]} rows x {df.shape[1]} columns"
                del df
                return meta, meta["name"], preview, info, gr.Dropdown(choices=meta["cols"]), gr.Dropdown(choices=meta["num_cols"]), gr.Dropdown(choices=["Count"] + meta["num_cols"])

            csv_file.change(fn=csv_upload_handler, inputs=[csv_file], outputs=[csv_meta_state, csv_status, csv_preview_table, csv_info, csv_x, csv_y, csv_pie_val])

            csv_qa_btn.click(fn=data_qa_csv, inputs=[csv_qa_input, csv_meta_state, lang_selector], outputs=csv_qa_out)

            csv_build_btn.click(fn=data_build_chart, inputs=[csv_x, csv_y, csv_chart_type, csv_pie_val, csv_meta_state], outputs=csv_chart)

        with gr.TabItem("💰 Financial Analyst"):
            gr.Markdown('<p class="section-header">Financial Analyst</p>')
            fin_cur = gr.Dropdown(list(AFRICAN_CURRENCIES.keys()), value="Nigerian Naira", label="🌍 Currency")
            with gr.Row():
                with gr.Column():
                    gr.Markdown('<p class="section-header">Enter Figures</p>')
                    fin_revenue = gr.Number(label="Revenue", value=100000, step=10000)
                    fin_cogs = gr.Number(label="COGS", value=40000, step=5000)
                    fin_opex = gr.Number(label="OpEx", value=30000, step=5000)
                    fin_calc_btn = gr.Button("🧮 Calculate", variant="primary")
                with gr.Column():
                    gr.Markdown('<p class="section-header">Key Metrics</p>')
                    fin_metrics = gr.Markdown()
                    fin_chart = gr.Plot(label="Cost Breakdown")

            fin_cfo_btn = gr.Button("📊 Generate CFO Summary", variant="primary")
            fin_cfo_out = gr.Markdown()

            gr.Markdown('<p class="section-header">Finance Chat (English/Hausa)</p>')
            fin_chat_input = gr.Textbox(label="Ask about finance, budgeting, or investments...")
            fin_chat_send = gr.Button("💬 Ask")
            fin_chat_out = gr.Markdown()

            fin_calc_btn.click(fn=finance_calc, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur], outputs=[fin_metrics, fin_chart])
            fin_cfo_btn.click(fn=finance_cfo_summary, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur, lang_selector], outputs=fin_cfo_out)
            fin_chat_send.click(fn=finance_chat, inputs=[fin_chat_input, finance_messages_state, fin_revenue, fin_cogs, fin_opex, fin_cur, lang_selector], outputs=fin_chat_out)

            demo.load(fn=finance_calc, inputs=[fin_revenue, fin_cogs, fin_opex, fin_cur], outputs=[fin_metrics, fin_chart])

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    demo.launch(
        server_name="0.0.0.0",
        server_port=8081,
        share=False,
        theme=CUSTOM_THEME,
        css=CUSTOM_CSS,
        ssr_mode=False,
        num_workers=1,
        show_error=False,
    )
