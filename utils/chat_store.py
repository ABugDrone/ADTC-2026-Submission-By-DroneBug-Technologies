from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from . import config

CHATS_DIR = os.path.join(config.DOCUMENTS_DIR, "chats")

os.makedirs(CHATS_DIR, exist_ok=True)


def _chat_path(chat_id: str) -> str:
    return os.path.join(CHATS_DIR, f"{chat_id}.json")


def list_chats() -> list[dict]:
    chats = []
    for fname in sorted(os.listdir(CHATS_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CHATS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            chats.append({
                "id": data.get("id", fname[:-5]),
                "title": data.get("title", "Untitled"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", [])),
            })
        except Exception:
            pass
    return chats


def load_chat(chat_id: str) -> Optional[dict]:
    path = _chat_path(chat_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_chat(chat_id: str, title: str, messages: list) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = {
        "id": chat_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": messages,
    }
    path = _chat_path(chat_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            data["created_at"] = existing.get("created_at", now)
        except Exception:
            pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def new_chat_id() -> str:
    return uuid.uuid4().hex[:12]


def delete_chat(chat_id: str) -> None:
    path = _chat_path(chat_id)
    if os.path.exists(path):
        os.remove(path)
