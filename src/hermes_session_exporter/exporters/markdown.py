"""Export sessions as clean Markdown."""

from __future__ import annotations

from ..models import Session, Message
from ..normalize import derive_title


def export_markdown(session: Session, *, include_metadata: bool = True) -> str:
    title = derive_title(session)
    parts: list[str] = [f"# {title}\n"]

    if include_metadata and session.metadata:
        parts.append("---")
        for k, v in session.metadata.items():
            parts.append(f"**{k}:** {v}")
        parts.append("---\n")

    for msg in session.messages:
        label = _role_label(msg)
        parts.append(f"## {label}\n")
        if msg.name and msg.role == "tool":
            parts.append(f"*Tool: {msg.name}*\n")
        parts.append(msg.content)
        parts.append("")  # blank line separator

    return "\n".join(parts)


def _role_label(msg: Message) -> str:
    labels = {"user": "User", "assistant": "Assistant", "tool": "Tool Output"}
    return labels.get(msg.role, msg.role.title())
