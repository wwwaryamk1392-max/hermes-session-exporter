"""Tests for all three exporters."""

from hermes_session_exporter.models import Session, Message
from hermes_session_exporter.exporters.markdown import export_markdown
from hermes_session_exporter.exporters.html import export_html
from hermes_session_exporter.exporters.json_export import export_json


def _make_session():
    return Session(
        title="Test",
        messages=[
            Message(role="user", content="Hello world"),
            Message(role="assistant", content="Hi there!\n\n```python\nprint('hi')\n```"),
            Message(role="tool", name="terminal", content="hi"),
        ],
        metadata={"source": "test"},
    )


class TestMarkdown:
    def test_contains_title(self):
        md = export_markdown(_make_session())
        assert "# Test" in md

    def test_contains_roles(self):
        md = export_markdown(_make_session())
        assert "## User" in md
        assert "## Assistant" in md
        assert "## Tool Output" in md

    def test_contains_tool_name(self):
        md = export_markdown(_make_session())
        assert "terminal" in md

    def test_preserves_code_blocks(self):
        md = export_markdown(_make_session())
        assert "```python" in md

    def test_metadata_block(self):
        md = export_markdown(_make_session())
        assert "source" in md


class TestHTML:
    def test_is_valid_html(self):
        html = export_html(_make_session())
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self):
        html = export_html(_make_session())
        assert "Test" in html

    def test_contains_css(self):
        html = export_html(_make_session())
        assert "<style>" in html

    def test_role_classes(self):
        html = export_html(_make_session())
        assert "msg-user" in html
        assert "msg-assistant" in html
        assert "msg-tool" in html

    def test_metadata(self):
        html = export_html(_make_session())
        assert "source" in html


class TestJSON:
    def test_valid_json(self):
        import json
        output = export_json(_make_session())
        data = json.loads(output)
        assert data["title"] == "Test"
        assert len(data["messages"]) == 3

    def test_message_roles(self):
        import json
        output = export_json(_make_session())
        data = json.loads(output)
        roles = [m["role"] for m in data["messages"]]
        assert roles == ["user", "assistant", "tool"]

    def test_metadata_preserved(self):
        import json
        output = export_json(_make_session())
        data = json.loads(output)
        assert data["metadata"]["source"] == "test"
