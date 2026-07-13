"""CLI entry point for hermes-session-exporter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loader import load_input, detect_input_type
from .normalize import derive_title, filter_messages
from .redact import redact_messages
from .exporters.markdown import export_markdown
from .exporters.html import export_html
from .exporters.json_export import export_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hermes-session-exporter",
        description="Export Hermes Agent sessions to Markdown, HTML, or JSON.",
    )
    sub = p.add_subparsers(dest="command")

    # export
    exp = sub.add_parser("export", help="Export session(s) to a target format")
    exp.add_argument("input", help="JSON file, JSONL file, or directory of session files")
    exp.add_argument("--format", "-f", choices=["md", "html", "json"], default="md")
    exp.add_argument("--output", "-o", help="Output file path (single session)")
    exp.add_argument("--output-dir", help="Output directory (batch / --split)")
    exp.add_argument("--split", action="store_true", help="Write each session to a separate file")
    exp.add_argument("--no-tools", action="store_true", help="Exclude tool messages")
    exp.add_argument("--chat-only", action="store_true", help="Include only user + assistant messages")
    exp.add_argument("--redact", action="store_true", help="Redact sensitive-looking content")
    exp.add_argument("--title", help="Override session title")
    exp.add_argument("--json", dest="json_output", action="store_true", help="Machine-readable JSON status output")

    # inspect
    ins = sub.add_parser("inspect", help="Print a summary of the input")
    ins.add_argument("input", help="JSON file, JSONL file, or directory of session files")

    return p


def cmd_export(args: argparse.Namespace) -> None:
    try:
        sessions = load_input(args.input)
    except (ValueError, FileNotFoundError) as e:
        _fail(str(e), args.json_output)
        return

    if not sessions:
        _fail("No sessions found in input.", args.json_output)
        return

    ext_map = {"md": ".md", "html": ".html", "json": ".json"}
    ext = ext_map[args.format]

    export_fn = {"md": export_markdown, "html": export_html, "json": export_json}[args.format]

    results: list[dict] = []

    for i, session in enumerate(sessions):
        if args.title:
            session.title = args.title
        session = filter_messages(session, no_tools=args.no_tools, chat_only=args.chat_only)
        if args.redact:
            from .models import Message
            session.messages = redact_messages(session.messages)

        output = export_fn(session)
        title = derive_title(session)

        if args.split or len(sessions) > 1:
            outdir = Path(args.output_dir) if args.output_dir else Path(".")
            outdir.mkdir(parents=True, exist_ok=True)
            safe_name = _safe_filename(title)
            out_path = outdir / f"{safe_name}{ext}"
        elif args.output:
            out_path = Path(args.output)
        else:
            out_path = Path(f"session{ext}")

        out_path.write_text(output, encoding="utf-8")
        results.append({"title": title, "path": str(out_path), "messages": len(session.messages)})

    if args.json_output:
        print(json.dumps({"status": "ok", "exports": results}, indent=2))
    else:
        for r in results:
            print(f"✓ {r['title'][:60]} → {r['path']} ({r['messages']} messages)")


def cmd_inspect(args: argparse.Namespace) -> None:
    try:
        sessions = load_input(args.input)
    except (ValueError, FileNotFoundError) as e:
        _fail(str(e), False)
        return

    input_type = detect_input_type(args.input)
    total_msgs = sum(len(s.messages) for s in sessions)
    roles = set()
    warnings: list[str] = []

    for s in sessions:
        for m in s.messages:
            roles.add(m.role)
        if not s.messages:
            warnings.append(f"Session '{derive_title(s)}' has no messages.")

    print(f"Input type:     {input_type}")
    print(f"Sessions:       {len(sessions)}")
    print(f"Total messages: {total_msgs}")
    print(f"Roles found:    {', '.join(sorted(roles)) or 'none'}")
    if sessions:
        print(f"Title:          {derive_title(sessions[0])}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  ⚠ {w}")


def _fail(msg: str, json_output: bool) -> None:
    if json_output:
        print(json.dumps({"status": "error", "message": msg}))
    else:
        print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _safe_filename(title: str) -> str:
    return "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip().replace(" ", "_")[:60] or "session"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "export":
        cmd_export(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
