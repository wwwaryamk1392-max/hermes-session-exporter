# hermes-session-exporter

Export [Hermes Agent](https://github.com/NousResearch/hermes-agent) conversation sessions to clean, shareable formats (Markdown, HTML, JSON). Includes an interactive TUI browser and a web panel for localhost access.

## Features

- **Export formats**: Markdown (GitHub-flavored), HTML (standalone with embedded CSS), JSON (normalized)
- **Interactive TUI**: Browse, preview, and export sessions from your local Hermes database
- **Web panel**: Run `hermes-session-exporter web` → open `http://127.0.0.1:8765` in browser (embedded xterm.js terminal)
- **Select & batch export**: Press `s` to select multiple sessions, `E` to export all at once
- **Filters**: `--chat-only`, `--no-tools`, `--redact` sensitive content
- **Cross-platform**: Windows, macOS, Linux (Python 3.10+)

## Install

### Quick (pipx - recommended)

```bash
pipx install git+https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
```

### Quick (pip)

```bash
pip install --user git+https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
```

### From source

```bash
git clone https://github.com/wwwaryamk1392-max/hermes-session-exporter.git
cd hermes-session-exporter
pip install -e .
```

## Usage

### Web Panel (browser)

```bash
hermes-session-exporter web
# Server starts at http://127.0.0.1:8765
# Open in browser — full TUI running in embedded terminal
```

Options:
```bash
hermes-session-exporter web --host 0.0.0.0 --port 8080
```

### TUI (terminal)

```bash
hermes-session-exporter
# or explicitly:
hermes-session-exporter browse
```

**Keys:**
| Key | Action |
|-----|--------|
| `↑/↓` | Navigate sessions |
| `Enter` | View messages |
| `e` | Export current session |
| `s` | **Select/deselect session** ✅ |
| `E` | Export all selected sessions |
| `r` | Refresh list |
| `q` | Quit |

### CLI Export (files)

```bash
# Export JSON file to Markdown
hermes-session-exporter export session.json --format md

# Export to HTML
hermes-session-exporter export session.json --format html -o out.html

# Export to normalized JSON
hermes-session-exporter export session.json --format json -o normalized.json

# Batch export directory
hermes-session-exporter export ./sessions/ --format md --split --output-dir ./out/

# Filter messages
hermes-session-exporter export session.json --chat-only --format md
hermes-session-exporter export session.json --no-tools --format md
hermes-session-exporter export session.json --redact --format md

# Inspect input
hermes-session-exporter inspect session.json
```

## Input Formats

| Format | Structure |
|--------|-----------|
| `.json` | Single session `{"messages": [...]}`, array of sessions, or wrapped `{"sessions": [...]}` |
| `.jsonl` | One message per line, or one session object per line |
| Directory | Scans all `.json` and `.jsonl` files |

## Output Formats

| Format | Description |
|--------|-------------|
| `--format md` | GitHub-flavored Markdown with role headers |
| `--format html` | Standalone HTML with embedded CSS (blue=user, green=assistant, purple=tool) |
| `--format json` | Normalized JSON with stable structure |

## How It Works

1. **Local Hermes DB**: Reads from `~/AppData/Local/hermes/state.db` (Windows) or `~/.local/share/hermes/state.db` (Linux/macOS)
2. **Sessions table**: `id`, `title`, `message_count`, `started_at`, `ended_at`, `model`, `source`
3. **Messages table**: `id`, `session_id`, `role`, `content`, `tool_name`, `timestamp`, `tool_calls`, `tool_call_id`
4. **Exports** saved to Desktop by default

## Project Structure

```
hermes-session-exporter/
├── src/hermes_session_exporter/
│   ├── cli.py           # CLI entry point (web, browse, export, inspect)
│   ├── tui.py           # Textual TUI browser with select/export
│   ├── web.py           # FastAPI + uvicorn + xterm.js web panel
│   ├── models.py        # Session, Message dataclasses
│   ├── normalize.py     # Filtering (chat-only, no-tools, redact)
│   ├── loader.py        # File loading (json, jsonl, dir)
│   ├── exporters/
│   │   ├── markdown.py  # MD export
│   │   ├── html.py      # HTML export
│   │   └── json_export.py
│   └── redact.py        # PII/secret redaction
├── tests/
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.10+
- `textual>=0.80` (TUI)
- `fastapi`, `uvicorn[standard]`, `websockets`, `textual-web` (web panel)
- `pydantic` (models)

## License

MIT