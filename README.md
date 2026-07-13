# hermes-session-exporter

Export [Hermes Agent](https://github.com/NousResearch/hermes-agent) conversation sessions into clean, shareable formats.

## Why

Hermes stores sessions as raw JSON/JSONL. This tool turns them into GitHub-friendly Markdown, standalone HTML, or normalized JSON — ready for sharing, archiving, or downstream tooling.

## Install

```bash
pip install -e .
```

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
# Exclude tool messages
hermes-session-exporter export session.json --no-tools -f md

# Chat only (user + assistant)
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
Roles found:    assistant, user
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

## Limitations

- No streaming/progress for large files (read entire file into memory).
- Redaction is pattern-based — not an audit tool.
- HTML output uses minimal inline CSS, no JS, no external dependencies.
- No rewrite/summarize — raw content only.

## Roadmap

- CSV/table export for message overview
- Token counting per message
- Filter by role with regex patterns
- Stdin/pipe support
