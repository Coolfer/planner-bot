import os
import sqlite3
from typing import Optional, List, Dict

DB_PATH = os.getenv("DB_PATH", "/data/planner.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'house',
            duration_min INTEGER DEFAULT 30,
            priority INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            plan_text TEXT,
            advice_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_task(name: str, category: str = "house", duration_min: int = 30, priority: int = 1) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO tasks (name, category, duration_min, priority, completed) VALUES (?, ?, ?, ?, 0)",
        (name, category, duration_min, priority),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_pending_tasks() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, category, duration_min, priority FROM tasks WHERE completed = 0 ORDER BY priority DESC, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_plan_for_date(date_str: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM plans WHERE date = ?", (date_str,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_plan(date_str: str, plan_text: str, advice_text: str = ""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO plans (date, plan_text, advice_text) VALUES (?, ?, ?)",
        (date_str, plan_text, advice_text),
    )
    conn.commit()
    conn.close()


def get_user_prefs() -> Dict[str, str]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT key, value FROM user_prefs").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def set_user_pref(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO user_prefs (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
