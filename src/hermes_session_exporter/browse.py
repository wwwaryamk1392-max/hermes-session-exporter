"""Browse Hermes session store (SQLite)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _db_path() -> Path:
    """Find the Hermes state.db file."""
    # Default location on Windows
    candidates = [
        Path(os.environ.get("HERMES_HOME", "")) / "state.db" if os.environ.get("HERMES_HOME") else None,
        Path.home() / "AppData" / "Local" / "hermes" / "state.db",
        Path.home() / ".hermes" / "state.db",
    ]
    for c in candidates:
        if c and c.exists():
            return c
    # Fallback
    return Path.home() / "AppData" / "Local" / "hermes" / "state.db"


def list_sessions() -> list[dict[str, Any]]:
    """Return list of sessions from Hermes store, newest first."""
    db = _db_path()
    if not db.exists():
        return []

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT id, title, model, started_at, message_count, source
            FROM sessions
            WHERE archived = 0 OR archived IS NULL
            ORDER BY started_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_messages(session_id: str) -> list[dict[str, Any]]:
    """Return all messages for a session, chronological."""
    db = _db_path()
    if not db.exists():
        return []

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT id, role, content, tool_name, timestamp
            FROM messages
            WHERE session_id = ? AND active = 1
            ORDER BY id ASC
        """, (session_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def format_timestamp(ts: str | int | float | None) -> str:
    """Format timestamp as YYYY-MM-DD HH:MM."""
    if not ts:
        return "?"
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
    else:
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            return str(ts)
    return dt.strftime("%Y-%m-%d %H:%M")