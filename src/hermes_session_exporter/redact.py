"""Conservative redaction for sensitive-looking content."""

from __future__ import annotations

import re

from .models import Message

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"(?:api[_-]?key|apikey|token|secret|password)\s*[:=]\s*\S+", re.IGNORECASE), "[REDACTED_CREDENTIAL]"),
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?:/home/[^/\s]+|C:\\Users\\[^\\]+)"), "[REDACTED_PATH]"),
]


def redact_messages(messages: list[Message]) -> list[Message]:
    return [Message(
        role=m.role,
        content=_redact_text(m.content),
        timestamp=m.timestamp,
        name=m.name,
        metadata=m.metadata,
    ) for m in messages]


def _redact_text(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text
