import json
import datetime
import threading
import time

try:
    from utils.config import TASKS_FILE, CHECK_INTERVAL_SECONDS
    from modules.notification import trigger_windows_notification
except ImportError:
    # Running as script, not as module
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.config import TASKS_FILE, CHECK_INTERVAL_SECONDS
    from modules.notification import trigger_windows_notification


class TaskManager:
    _tasks = []
    _lock = threading.Lock()
    _scheduler_started = False

    @classmethod
    def initialize(cls):
        cls._load()
        if not cls._scheduler_started:
            cls._scheduler_started = True
            thread = threading.Thread(target=cls._scheduler_loop, daemon=True)
            thread.start()

    @classmethod
    def _load(cls):
        try:
            with open(TASKS_FILE, "r") as f:
                data = json.load(f)
            with cls._lock:
                cls._tasks = data
        except (FileNotFoundError, json.JSONDecodeError):
            cls._tasks = []

    @classmethod
    def _save(cls):
        with cls._lock:
            with open(TASKS_FILE, "w") as f:
                json.dump(cls._tasks, f, indent=2)

    @classmethod
    def get_all(cls):
        with cls._lock:
            return cls._tasks.copy()

    @classmethod
    def add(cls, title, date, time_val, priority):
        date_str = date.isoformat() if hasattr(date, "isoformat") else str(date)
        time_str = time_val.isoformat() if hasattr(time_val, "isoformat") else str(time_val)
        task = {
            "title": title,
            "date": date_str,
            "time": time_str,
            "priority": priority,
            "status": "Pending"
        }
        with cls._lock:
            cls._tasks.append(task)
        cls._save()
        return task

    @classmethod
    def delete_task(cls, index):
        with cls._lock:
            if 0 <= index < len(cls._tasks):
                cls._tasks.pop(index)
        cls._save()

    @classmethod
    def update_task(cls, index, **kwargs):
        with cls._lock:
            if 0 <= index < len(cls._tasks):
                for k, v in kwargs.items():
                    cls._tasks[index][k] = v
        cls._save()

    @classmethod
    def toggle_status(cls, index):
        with cls._lock:
            if 0 <= index < len(cls._tasks):
                current = cls._tasks[index].get("status", "Pending")
                cls._tasks[index]["status"] = "Completed" if current == "Pending" else "Pending"
        cls._save()

    @classmethod
    def clear_completed(cls):
        with cls._lock:
            cls._tasks = [t for t in cls._tasks if t.get("status") != "Completed"]
        cls._save()

    @classmethod
    def to_dataframe(cls):
        import pandas as pd
        tasks = cls.get_all()
        if not tasks:
            return pd.DataFrame()
        df = pd.DataFrame(tasks)
        for col in ["date", "time"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df

    @classmethod
    def _scheduler_loop(cls):
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            tasks = cls.get_all()
            now = datetime.datetime.now()
            for task in tasks:
                if task.get("status") == "Completed":
                    continue
                try:
                    task_date = datetime.datetime.strptime(task["date"][:10], "%Y-%m-%d").date()
                    task_time_str = task["time"][:8]
                    task_time = datetime.datetime.strptime(task_time_str, "%H:%M:%S").time()
                    task_dt = datetime.datetime.combine(task_date, task_time)
                except (ValueError, KeyError):
                    continue
                diff_seconds = abs((now - task_dt).total_seconds())
                if diff_seconds <= CHECK_INTERVAL_SECONDS:
                    trigger_windows_notification(
                        title=f"Task Due: {task['title']}",
                        message=f"Priority: {task['priority']} | Scheduled: {task['date']} {task['time']}"
                    )
