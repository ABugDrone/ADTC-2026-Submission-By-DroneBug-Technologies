import datetime

import pandas as pd
import streamlit as st

from modules.notification import trigger_windows_notification
from modules.task_manager import TaskManager
from utils import ai_engine, theme

st.set_page_config(page_title="Meetings & Tasks · BusinessPilot AI", page_icon="", layout="wide")
theme.init_theme_state()
theme.inject_css()

with st.sidebar:
    theme.sidebar_nav("Meetings & Tasks")

theme.page_header("Meetings & Task Scheduler", "Schedule, track, and let AI prioritize your day.")

left, right = st.columns([1, 2], gap="large")

with left:
    with st.container(border=True):
        st.markdown("<p class='section-label'>Schedule Event / Task</p>", unsafe_allow_html=True)
        new_title = st.text_input("Title", placeholder="e.g., Board Meeting", label_visibility="collapsed")
        dc, tc = st.columns(2)
        with dc:
            new_date = st.date_input("Date", datetime.date.today())
        with tc:
            new_time = st.time_input("Time", datetime.time(9, 0))
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        if st.button("Save & Notify", use_container_width=True):
            if new_title:
                TaskManager.add(new_title, new_date, new_time, new_priority)
                trigger_windows_notification(title="Task Added", message=f"Scheduled: '{new_title}' for {new_date}")
                st.success(f"Pinned '{new_title}'!")
                st.rerun()
            else:
                st.error("Title cannot be blank.")

    with st.container(border=True):
        st.markdown("<p class='section-label'>AI Prioritization</p>", unsafe_allow_html=True)
        if st.button("Re-Prioritize with Qwen", use_container_width=True):
            tasks = TaskManager.get_all()
            if tasks:
                tasks_text = "\n".join(f"- {t['title']} (Priority: {t['priority']}, Status: {t['status']})" for t in tasks)
                jobs = [
                    {
                        "prompt": (
                            f"Schedule:\n{tasks_text}\n\n"
                            "Give a 2-line strategic recommendation for the order I should "
                            "tackle these tasks, based on business urgency."
                        ),
                        "system_prompt": "You are an elite chief of staff. Be direct.",
                    },
                    {
                        "prompt": (
                            f"Schedule:\n{tasks_text}\n\n"
                            "In one short line, flag anything overdue or high-risk. "
                            "If nothing looks risky, say so."
                        ),
                        "system_prompt": "You are a risk-aware ops assistant. Be concise.",
                    },
                ]
                with st.spinner("Analyzing..."):
                    results = ai_engine.query_model_many(jobs)
                if results[0].ok:
                    st.info(results[0].text)
                else:
                    st.error(results[0].error)
                if results[1].ok:
                    if any(w in results[1].text.lower() for w in ["overdue", "risk", "late"]):
                        st.warning(results[1].text)
                    else:
                        st.success(results[1].text)
                else:
                    st.error(results[1].error)
            else:
                theme.empty_state(
                    icon_name="calendar-off",
                    title="No tasks yet",
                    message="Add a task above before asking the AI to prioritize your day.",
                )

with right:
    st.markdown("<p class='section-label'>Current Agenda</p>", unsafe_allow_html=True)
    tasks = TaskManager.get_all()
    if tasks:
        df_t = pd.DataFrame(tasks)
        for c in ["date", "time"]:
            if c in df_t.columns:
                df_t[c] = df_t[c].astype(str)

        def _priority_badge(priority: str) -> str:
            kind = {"High": "danger", "Medium": "warning", "Low": "accent"}.get(priority, "accent")
            return theme.status_badge(priority, kind)

        # Render tasks as styled rows with priority badges.
        for idx, row in df_t.iterrows():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.markdown(
                f"**{row['title']}**  \n"
                f"<span style='color:var(--muted);font-size:12px;'>{row['date']} at {row['time']}</span>",
                unsafe_allow_html=True,
            )
            c2.markdown(_priority_badge(row["priority"]), unsafe_allow_html=True)
            c3.markdown(theme.status_badge(row["status"], "success" if row["status"] == "Completed" else "accent"), unsafe_allow_html=True)
            if c4.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.edit_task_idx = idx
                st.rerun()

        if st.button("Clear Completed", use_container_width=True):
            TaskManager.clear_completed()
            st.rerun()
    else:
        theme.empty_state(
            icon_name="calendar-event",
            title="No meetings scheduled",
            message="Your agenda is clear. Add your first meeting or task to get started.",
        )

if st.session_state.get("edit_task_idx") is not None:
    idx = st.session_state.edit_task_idx
    tasks = TaskManager.get_all()
    if 0 <= idx < len(tasks):
        t = tasks[idx]
        with st.expander(f"Editing: {t['title']}", expanded=True):
            new_t = st.text_input("Title", value=t["title"], key="edit_title")
            new_d = st.date_input("Date", value=datetime.date.fromisoformat(t["date"]), key="edit_date")
            new_tm = st.time_input(
                "Time",
                value=datetime.time.fromisoformat(t["time"]) if ":" in t["time"] else datetime.time(9, 0),
                key="edit_time",
            )
            new_p = st.selectbox(
                "Priority",
                ["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(t["priority"]),
                key="edit_prio",
            )
            c1, c2 = st.columns(2)
            if c1.button("Save Changes", type="primary"):
                TaskManager.update_task(idx, title=new_t, date=new_d.isoformat(), time=new_tm.isoformat(), priority=new_p)
                st.session_state.edit_task_idx = None
                st.rerun()
            if c2.button("Cancel"):
                st.session_state.edit_task_idx = None
                st.rerun()
