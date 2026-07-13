"""Export sessions as standalone HTML."""

from __future__ import annotations

import html

from ..models import Session, Message
from ..normalize import derive_title

_CSS = """\
body{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#222}
h1{border-bottom:2px solid #ddd;padding-bottom:.5rem}
.msg{margin:1.5rem 0;padding:1rem;border-radius:6px;border-left:4px solid #ccc}
.msg-user{border-color:#2563eb;background:#eff6ff}
.msg-assistant{border-color:#16a34a;background:#f0fdf4}
.msg-tool{border-color:#9333ea;background:#faf5ff}
.role{font-weight:700;margin-bottom:.3rem}
pre{background:#f5f5f5;padding:.8rem;border-radius:4px;overflow-x:auto}
code{font-family:monospace;font-size:.9em}
.meta{color:#666;font-size:.9em;margin-bottom:1rem;border:1px solid #ddd;padding:.5rem;border-radius:4px}
"""

_ROLE_CLASS = {"user": "msg-user", "assistant": "msg-assistant", "tool": "msg-tool"}
_ROLE_LABEL = {"user": "User", "assistant": "Assistant", "tool": "Tool Output"}


def export_html(session: Session) -> str:
    title = derive_title(session)
    meta_html = ""
    if session.metadata:
        items = "".join(f"<li><b>{html.escape(k)}:</b> {html.escape(str(v))}</li>" for k, v in session.metadata.items())
        meta_html = f'<div class="meta"><ul>{items}</ul></div>'

    body_parts: list[str] = []
    for msg in session.messages:
        cls = _ROLE_CLASS.get(msg.role, "")
        label = _ROLE_LABEL.get(msg.role, msg.role.title())
        tool_note = f'<div class="role">Tool: {html.escape(msg.name)}</div>' if msg.name and msg.role == "tool" else ""
        content = html.escape(msg.content).replace("\n", "<br>")
        body_parts.append(f'<div class="msg {cls}">{tool_note}<div class="role">{label}</div><div>{content}</div></div>')

    body = "\n".join(body_parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
{meta_html}
{body}
</body>
</html>"""
