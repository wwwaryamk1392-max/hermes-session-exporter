"""TUI-based session browser using Textual."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Label, Static
from textual.widgets.data_table import RowKey
from textual.message import Message
from textual.screen import ModalScreen
from textual.binding import Binding

from hermes_session_exporter.models import Session, Message
from hermes_session_exporter.exporters.markdown import export_markdown
from hermes_session_exporter.exporters.html import export_html
from hermes_session_exporter.exporters.json_export import export_json
from hermes_session_exporter.normalize import filter_messages


def get_hermes_db() -> Path:
    return Path.home() / "AppData" / "Local" / "hermes" / "state.db"


def load_sessions() -> list[dict[str, Any]]:
    db = get_hermes_db()
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, title, message_count, started_at, ended_at, model, source
        FROM sessions
        ORDER BY started_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_messages(session_id: str) -> list[dict[str, Any]]:
    db = get_hermes_db()
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, session_id, role, content, tool_name, tool_input, tool_output, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY id
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def session_to_model(session: dict[str, Any], messages: list[dict[str, Any]]) -> Session:
    """Convert raw DB rows to Session model."""
    msgs = []
    for m in messages:
        content = m["content"] or ""
        if m["tool_name"]:
            content = f"[Tool: {m['tool_name']}]\n{content}"
        msgs.append(Message(
            role=m["role"],
            content=content,
            tool_calls=m["tool_input"],
            tool_result=m["tool_output"],
            timestamp=m["timestamp"],
        ))
    started = datetime.fromtimestamp(session["started_at"], tz=timezone.utc) if session["started_at"] else datetime.now(timezone.utc)
    ended = datetime.fromtimestamp(session["ended_at"], tz=timezone.utc) if session["ended_at"] else None
    return Session(
        session_id=session["id"],
        messages=msgs,
        metadata={"model": session["model"], "source": session["source"]},
        title=session["title"] or None,
        started_at=started,
        ended_at=ended,
    )


class MessageView(Static):
    """Scrollable view of session messages."""

    def __init__(self, session: Session, **kwargs):
        super().__init__(**kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        for msg in self.session.messages:
            role_label = {"user": "👤 User", "assistant": "🤖 Assistant", "tool": "🔧 Tool"}.get(msg.role, msg.role)
            yield Static(f"[bold]{role_label}[/bold]\n{msg.content}", classes="message")


class ExportDialog(ModalScreen):
    """Modal dialog to choose export format."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel")]

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Export session: {self.session.session_id[:8]}..."),
            Button("Markdown (.md)", id="export_md", variant="primary"),
            Button("HTML (.html)", id="export_html", variant="primary"),
            Button("JSON (.json)", id="export_json", variant="primary"),
            Button("Cancel", id="cancel", variant="default"),
            id="export_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        fmt = event.button.id.replace("export_", "")
        self.dismiss(fmt)


class SessionBrowser(App):
    """Main TUI app for browsing and exporting Hermes sessions."""

    CSS = """
    Screen {
        layout: horizontal;
    }
    #sessions_panel {
        width: 40%;
        border-right: solid $primary;
    }
    #messages_panel {
        width: 60%;
    }
    #session_table {
        height: 100%;
    }
    .message {
        padding: 1;
        margin: 1 0;
        border: solid $secondary;
    }
    #export_dialog {
        width: 50;
        height: auto;
        padding: 2;
        border: solid $primary;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("enter", "view_messages", "View"),
        Binding("e", "export", "Export"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.sessions: list[dict[str, Any]] = []
        self.current_session: Session | None = None
        self.current_messages: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sessions_panel"):
                yield Label("Hermes Sessions", id="sessions_title")
                yield DataTable(id="session_table", cursor_type="row")
            with Vertical(id="messages_panel"):
                yield Label("Messages", id="messages_title")
                yield Static("Select a session to view messages", id="messages_content")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        self.sessions = load_sessions()
        table = self.query_one("#session_table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Messages", "Model", "When", "Title")
        for i, s in enumerate(self.sessions, 1):
            started = datetime.fromtimestamp(s["started_at"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if s["started_at"] else "?"
            title = s["title"] or "(untitled)"
            table.add_row(str(i), str(s["message_count"]), s["model"] or "?", started, title, key=s["id"])

    def action_refresh(self) -> None:
        self.refresh_sessions()
        self.notify("Refreshed")

    def action_view_messages(self) -> None:
        table = self.query_one("#session_table", DataTable)
        if table.cursor_row >= len(self.sessions):
            return
        session_id = self.sessions[table.cursor_row]["id"]
        self.load_session_messages(session_id)

    def load_session_messages(self, session_id: str) -> None:
        self.current_messages = load_messages(session_id)
        session_data = next((s for s in self.sessions if s["id"] == session_id), {})
        self.current_session = session_to_model(session_data, self.current_messages)
        content = self.query_one("#messages_content", Static)
        content.remove_children()
        for msg in self.current_session.messages:
            role_label = {"user": "👤 User", "assistant": "🤖 Assistant", "tool": "🔧 Tool"}.get(msg.role, msg.role)
            content.mount(Static(f"[bold]{role_label}[/bold]\n{msg.content}", classes="message"))

    def action_export(self) -> None:
        if not self.current_session:
            self.notify("No session selected", severity="warning")
            return
        self.push_screen(ExportDialog(self.current_session), self.handle_export)

    def handle_export(self, fmt: str | None) -> None:
        if not fmt or not self.current_session:
            return
        desktop = Path.home() / "Desktop"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = {"md": "md", "html": "html", "json": "json"}[fmt]
        out_path = desktop / f"session_{self.current_session.session_id}_{ts}.{ext}"

        filtered = filter_messages(self.current_session.messages, chat_only=False, no_tools=False)

        if fmt == "md":
            export_markdown(self.current_session, out_path, filtered=filtered)
        elif fmt == "html":
            export_html(self.current_session, out_path, filtered=filtered)
        elif fmt == "json":
            export_json(self.current_session, out_path, filtered=filtered)

        self.notify(f"Exported to {out_path}")


def run_tui() -> None:
    """Entry point for the TUI."""
    app = SessionBrowser()
    app.run()