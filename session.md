# How do I export sessions?

---
**created_at:** 2026-07-13T10:00:00Z
---

## User

How do I export my Hermes sessions to Markdown?

## Assistant

You can use hermes-session-exporter:

```bash
hermes-session-exporter export session.json --format md
```

This converts the session to clean GitHub-friendly Markdown.

## User

What about HTML output?

## Assistant

Just change the format flag:

```bash
hermes-session-exporter export session.json --format html -o output.html
```

The HTML is standalone with embedded CSS.

## Tool Output

*Tool: terminal*

$ hermes-session-exporter export session.json -f html
✓ Exported to output.html

## Assistant

Done! The output is ready to share or archive.

## User

Can I redact sensitive info?

## Assistant

Yes, use `--redact`:

```bash
hermes-session-exporter export session.json --redact -f md
```

It strips API keys, emails, and local paths.
