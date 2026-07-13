# hermes-session-exporter

Export [Hermes Agent](https://github.com/NousResearch/hermes-agent) conversation sessions into clean, shareable formats.

## Install

### From GitHub (recommended)

```bash
git clone https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
cd hermes-session-exporter
pip install -e .
```

### One-liner

```bash
pip install git+https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
```

### From source

```bash
git clone https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
cd hermes-session-exporter
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e .
```

Requires: Python 3.10+

## Usage

### Export to Markdown

```bash
hermes-session-exporter export session.json --format md
hermes-session-exporter export session.json -f md -o output.md
```

### Export to HTML

```bash
hermes-session-exporter export session.json --format html -o output.html
```

### Export to JSON (normalized)

```bash
hermes-session-exporter export session.json --format json -o normalized.json
```

### Batch export a directory

```bash
hermes-session-exporter export ./sessions/ --format md --split --output-dir ./exported/
```

### Filter messages

```bash
hermes-session-exporter export session.json --no-tools -f md
hermes-session-exporter export session.json --chat-only -f md
```

### Redact sensitive content

```bash
hermes-session-exporter export session.json --redact -f md
```

### Inspect input

```bash
hermes-session-exporter inspect session.json
```

Output:
```
Input type:     JSON
Sessions:       1
Total messages: 12
Roles found:    assistant, tool, user
Title:          How do I export sessions?
```

### Machine-readable output

```bash
hermes-session-exporter export session.json -f md --json
```

```json
{
  "status": "ok",
  "exports": [{"title": "...", "path": "session.md", "messages": 12}]
}
```

## Supported Input

| Format | Structure |
|--------|-----------|
| `.json` | Single session (`{"messages": [...]}`), array of sessions, or wrapped (`{"sessions": [...]}`) |
| `.jsonl` | One message per line, or one session object per line |
| Directory | Scans all `.json` and `.jsonl` files |

## Supported Output

| Flag | Output |
|------|--------|
| `--format md` | GitHub-flavored Markdown |
| `--format html` | Standalone HTML with embedded CSS |
| `--format json` | Normalized JSON with stable structure |

## Sample Output

### Markdown

```markdown
# How do I export sessions?

## User

How do I export my Hermes sessions to Markdown?

## Assistant

You can use hermes-session-exporter:

```bash
hermes-session-exporter export session.json --format md
```

This converts the session to clean GitHub-friendly Markdown.
```

### HTML

Standalone HTML with embedded CSS, role-based color coding (blue for user, green for assistant, purple for tool output), and semantic markup.

## Limitations

- No streaming/progress for large files (reads entire file into memory).
- Redaction is pattern-based — not an audit tool.
- HTML uses minimal inline CSS, no JS, no external dependencies.
- No rewrite/summarize — raw content only.

## Roadmap

- CSV/table export for message overview
- Token counting per message
- Stdin/pipe support
