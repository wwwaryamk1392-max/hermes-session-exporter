"""Tests for redaction."""

from hermes_session_exporter.models import Message
from hermes_session_exporter.redact import redact_messages


def test_redact_api_key():
    msgs = [Message(role="user", content="Use sk-abcdefghij1234567890abcdef for auth")]
    result = redact_messages(msgs)
    assert "sk-" not in result[0].content
    assert "[REDACTED_API_KEY]" in result[0].content


def test_redact_email():
    msgs = [Message(role="user", content="Send to user@example.com")]
    result = redact_messages(msgs)
    assert "user@example.com" not in result[0].content
    assert "[REDACTED_EMAIL]" in result[0].content


def test_redact_bearer_token():
    msgs = [Message(role="user", content="Bearer abc123token123")]
    result = redact_messages(msgs)
    assert "Bearer [REDACTED]" in result[0].content


def test_redact_home_path():
    msgs = [Message(role="user", content="File at /home/alice/docs/file.txt")]
    result = redact_messages(msgs)
    assert "/home/alice" not in result[0].content


def test_no_redact_clean_text():
    msgs = [Message(role="user", content="Hello, this is normal text.")]
    result = redact_messages(msgs)
    assert result[0].content == "Hello, this is normal text."


def test_redact_preserves_role():
    msgs = [Message(role="assistant", content="sk-12345678901234567890abcdefgh")]
    result = redact_messages(msgs)
    assert result[0].role == "assistant"
