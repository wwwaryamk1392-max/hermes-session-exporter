"""Filter and derive metadata for sessions."""

from __future__ import annotations

from .models import Session


def derive_title(session: Session) -> str:
    if session.title:
        return session.title
    for msg in session.messages:
        if msg.role == "user":
            first_line = msg.content.strip().split("\n")[0]
            return first_line[:100] if first_line else "Untitled Session"
    return "Untitled Session"


def filter_messages(
    session: Session,
    *,
    no_tools: bool = False,
    chat_only: bool = False,
) -> Session:
    msgs = session.messages
    if chat_only:
        msgs = [m for m in msgs if m.role in ("user", "assistant")]
    elif no_tools:
        msgs = [m for m in msgs if m.role != "tool"]
    return Session(
        session_id=session.session_id,
        title=session.title,
        messages=msgs,
        metadata=session.metadata,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )
