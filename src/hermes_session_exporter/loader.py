"""Load session data from JSON, JSONL files, or directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Message, Session


def load_input(path: str | Path) -> list[Session]:
    """Load sessions from a file or directory."""
    p = Path(path)
    if p.is_dir():
        return _load_directory(p)
    if p.suffix == ".jsonl":
        return _load_jsonl(p)
    if p.suffix == ".json":
        return _load_json(p)
    raise ValueError(f"Unsupported file type: {p.suffix} (use .json or .jsonl)")


def _load_json(path: Path) -> list[Session]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return _normalize_top_level(data)


def _load_jsonl(path: Path) -> list[Session]:
    messages: list[Message] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "messages" in obj or "session" in obj:
            sessions = _normalize_top_level(obj)
            if len(sessions) == 1 and not messages:
                return sessions
            for s in sessions:
                messages.extend(s.messages)
        else:
            msg = _coerce_message(obj)
            if msg:
                messages.append(msg)
    return [Session(title=None, messages=messages)] if messages else []


def _load_directory(dirpath: Path) -> list[Session]:
    all_sessions: list[Session] = []
    for f in sorted(dirpath.iterdir()):
        if f.suffix in (".json", ".jsonl"):
            all_sessions.extend(load_input(f))
    if not all_sessions:
        raise FileNotFoundError(f"No .json or .jsonl files found in {dirpath}")
    return all_sessions


def _normalize_top_level(data: Any) -> list[Session]:
    if isinstance(data, dict):
        if "messages" in data:
            return [_session_from_dict(data)]
        for key in ("sessions", "data", "conversation", "history"):
            if key in data and isinstance(data[key], (list, dict)):
                inner = data[key]
                if isinstance(inner, dict):
                    return [_session_from_dict(inner)]
                if isinstance(inner, list):
                    return [_session_from_dict(item) for item in inner if isinstance(item, dict)]
        return [_session_from_dict(data)]
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "messages" in data[0]:
            return [_session_from_dict(item) for item in data]
        msgs = [_coerce_message(item) for item in data if isinstance(item, dict)]
        msgs = [m for m in msgs if m is not None]
        return [Session(title=None, messages=msgs)] if msgs else []
    raise ValueError(f"Cannot parse top-level type: {type(data).__name__}")


def _session_from_dict(d: dict) -> Session:
    raw_messages = d.get("messages", [])
    messages = [_coerce_message(m) for m in raw_messages if isinstance(m, dict)]
    messages = [m for m in messages if m is not None]
    title = d.get("title") or d.get("name")
    metadata = {k: v for k, v in d.items() if k not in ("messages", "title", "name")}
    return Session(title=title, messages=messages, metadata=metadata)


def _coerce_message(d: dict) -> Message | None:
    content = d.get("content", "")
    if isinstance(content, dict):
        content = content.get("text", content.get("value", json.dumps(content)))
    if not isinstance(content, str):
        content = json.dumps(content) if content else ""

    role = d.get("role", d.get("type", "unknown"))
    role_map = {"human": "user", "ai": "assistant", "bot": "assistant", "system": "assistant"}
    role = role_map.get(role, role)
    if role not in ("user", "assistant", "tool"):
        role = "assistant"

    name = d.get("name", d.get("tool_name"))
    timestamp = d.get("timestamp", d.get("ts", d.get("created_at")))
    skip_keys = {"content", "role", "type", "name", "tool_name", "timestamp", "ts", "created_at"}
    metadata = {k: v for k, v in d.items() if k not in skip_keys}

    return Message(role=role, content=content, timestamp=timestamp, name=name, metadata=metadata)


def detect_input_type(path: str | Path) -> str:
    p = Path(path)
    if p.is_dir():
        files = list(p.glob("*.json")) + list(p.glob("*.jsonl"))
        return f"directory ({len(files)} session files)"
    if p.suffix == ".jsonl":
        return "JSONL"
    if p.suffix == ".json":
        return "JSON"
    return f"unknown ({p.suffix})"
