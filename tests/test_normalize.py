"""Tests for normalization and filtering."""

from hermes_session_exporter.models import Session, Message
from hermes_session_exporter.normalize import derive_title, filter_messages


def test_derive_title_from_metadata():
    s = Session(title="From Meta", messages=[])
    assert derive_title(s) == "From Meta"


def test_derive_title_from_first_user():
    s = Session(title=None, messages=[
        Message(role="assistant", content="skip"),
        Message(role="user", content="My question here"),
    ])
    assert derive_title(s) == "My question here"


def test_derive_title_truncates_long():
    s = Session(title=None, messages=[
        Message(role="user", content="x" * 200),
    ])
    assert len(derive_title(s)) == 100


def test_derive_title_fallback():
    s = Session(title=None, messages=[
        Message(role="assistant", content="no user"),
    ])
    assert derive_title(s) == "Untitled Session"


def test_filter_chat_only():
    s = Session(title="t", messages=[
        Message(role="user", content="a"),
        Message(role="assistant", content="b"),
        Message(role="tool", content="c"),
        Message(role="user", content="d"),
    ])
    filtered = filter_messages(s, chat_only=True)
    assert len(filtered.messages) == 3
    assert all(m.role in ("user", "assistant") for m in filtered.messages)


def test_filter_no_tools():
    s = Session(title="t", messages=[
        Message(role="user", content="a"),
        Message(role="tool", content="b"),
        Message(role="assistant", content="c"),
    ])
    filtered = filter_messages(s, no_tools=True)
    assert len(filtered.messages) == 2
    assert all(m.role != "tool" for m in filtered.messages)


def test_filter_preserves_metadata():
    s = Session(title="t", messages=[], metadata={"key": "val"})
    filtered = filter_messages(s, chat_only=True)
    assert filtered.metadata == {"key": "val"}
