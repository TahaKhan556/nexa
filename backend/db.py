"""SQLite chat history storage."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "chat.db"


def init_db():
    """Initialize the chat database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            refined_prompt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(role: str, content: str, refined_prompt: str = None):
    """Save a message to the database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO messages (role, content, refined_prompt) VALUES (?, ?, ?)",
        (role, content, refined_prompt),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 50):
    """Get recent chat history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in reversed(rows)]


def clear_history():
    """Clear all chat history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
