from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

import sqlite_vec

from . import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.VEC_DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(embed_dim: int = config.EMBED_DIM) -> None:
    conn = _connect()
    conn.execute(
        f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks USING vec0(
            embedding float[{embed_dim}]
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS doc_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    try:
        conn.execute("ALTER TABLE doc_metadata ADD COLUMN embedded INTEGER DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()


@dataclass
class RetrievedChunk:
    content: str
    source: str
    distance: float
    method: str


def add_document(name: str, text: str) -> dict:
    from .ai_engine import embed_text

    chunks = _chunk_text(text)
    conn = _connect()
    vec_total = 0
    raw_total = 0
    for i, chunk in enumerate(chunks):
        result = embed_text(chunk)
        cursor = conn.execute(
            "INSERT INTO doc_metadata (doc_name, chunk_index, chunk_text, embedded) VALUES (?, ?, ?, ?)",
            (name, i, chunk, 1 if result.ok else 0),
        )
        row_id = cursor.lastrowid
        if result.ok:
            conn.execute(
                "INSERT INTO doc_chunks (rowid, embedding) VALUES (?, ?)",
                (row_id, json.dumps(result.vector)),
            )
            vec_total += 1
        raw_total += 1
    conn.commit()
    conn.close()
    return {"chunks": raw_total, "embedded": vec_total}


def search(query: str, top_k: int = config.RAG_TOP_K) -> list[RetrievedChunk]:
    from .ai_engine import embed_text

    result = embed_text(query)
    conn = _connect()
    if result.ok:
        rows = conn.execute(
            "SELECT m.doc_name, m.chunk_text, v.distance, m.embedded "
            "FROM doc_chunks v JOIN doc_metadata m ON v.rowid = m.id "
            "WHERE v.embedding MATCH ? AND k = ? "
            "ORDER BY v.distance",
            (json.dumps(result.vector), top_k),
        ).fetchall()
        conn.close()
        return [
            RetrievedChunk(
                content=r["chunk_text"], source=r["doc_name"],
                distance=r["distance"], method="vector"
            )
            for r in rows
        ]
    terms = query.lower().split()
    placeholders = " OR ".join(["chunk_text LIKE ?"] * len(terms))
    params = [f"%{t}%" for t in terms]
    rows = conn.execute(
        f"SELECT doc_name, chunk_text, 0.0 as distance, embedded "
        f"FROM doc_metadata WHERE {placeholders} "
        f"ORDER BY chunk_index LIMIT ?",
        params + [top_k],
    ).fetchall()
    conn.close()
    return [
        RetrievedChunk(
            content=r["chunk_text"], source=r["doc_name"],
            distance=r["distance"], method="keyword"
        )
        for r in rows
    ]


def list_documents() -> list[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        "SELECT DISTINCT doc_name, COUNT(*) as chunks, "
        "SUM(embedded) as embedded_count, MAX(created_at) as created "
        "FROM doc_metadata GROUP BY doc_name ORDER BY created DESC"
    ).fetchall()
    conn.close()
    return rows


def delete_document(name: str) -> None:
    conn = _connect()
    ids = conn.execute(
        "SELECT id FROM doc_metadata WHERE doc_name = ?", (name,)
    ).fetchall()
    for row in ids:
        conn.execute("DELETE FROM doc_chunks WHERE rowid = ?", (row["id"],))
    conn.execute("DELETE FROM doc_metadata WHERE doc_name = ?", (name,))
    conn.commit()
    conn.close()


def chunk_count() -> int:
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM doc_metadata").fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


def _chunk_text(text: str, chunk_size: int = config.RAG_CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
