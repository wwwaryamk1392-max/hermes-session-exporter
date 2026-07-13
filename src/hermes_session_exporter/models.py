"""Internal data models for sessions and messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "user" | "assistant" | "tool"
    content: str
    timestamp: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    session_id: str
    title: str | None
    messages: list[Message]
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    ended_at: str | None = None
