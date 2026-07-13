"""Web server with embedded terminal for Hermes Session Exporter TUI."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(title="Hermes Session Exporter Web Panel")

# Store active TUI process
tui_process: subprocess.Popen | None = None
tui_lock = threading.Lock()


class WebSocketManager:
    """Manages WebSocket connections for the terminal."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.output_buffer: list[str] = []
        self.max_buffer = 5000
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send buffered output
        for line in self.output_buffer:
            await websocket.send_text(line)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        self.output_buffer.append(message)
        if len(self.output_buffer) > self.max_buffer:
            self.output_buffer = self.output_buffer[-self.max_buffer:]
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
    
    async def send_input(self, data: str):
        """Send input to the TUI process."""
        global tui_process
        with tui_lock:
            if tui_process and tui_process.stdin:
                try:
                    tui_process.stdin.write(data)
                    tui_process.stdin.flush()
                except Exception:
                    pass


manager = WebSocketManager()


def get_hermes_db() -> Path:
    return Path.home() / "AppData" / "Local" / "hermes" / "state.db"


def read_tui_output():
    """Background thread to read TUI process output."""
    global tui_process
    while True:
        with tui_lock:
            if not tui_process or not tui_process.stdout:
                time.sleep(0.1)
                continue
            try:
                # Read character by character for real-time feel
                char = tui_process.stdout.read(1)
                if not char:
                    time.sleep(0.01)
                    continue
                # Send to websocket clients via asyncio
                asyncio.run(manager.broadcast(char))
            except Exception:
                time.sleep(0.1)


def start_tui_process():
    """Start the TUI subprocess."""
    global tui_process
    with tui_lock:
        if tui_process and tui_process.poll() is None:
            return  # Already running
        
        # Set up environment
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        env["FORCE_COLOR"] = "1"
        
        tui_process = subprocess.Popen(
            [sys.executable, "-m", "hermes_session_exporter.tui"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,  # Unbuffered
            env=env,
        )
        
        # Start output reader thread
        reader = threading.Thread(target=read_tui_output, daemon=True)
        reader.start()


def stop_tui_process():
    """Stop the TUI subprocess."""
    global tui_process
    with tui_lock:
        if tui_process and tui_process.poll() is None:
            try:
                tui_process.terminate()
                tui_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                tui_process.kill()
                tui_process.wait()
            except Exception:
                pass
            tui_process = None


@app.get("/")
async def root() -> HTMLResponse:
    """Serve the web panel with embedded terminal."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Hermes Session Exporter</title>
    <meta charset="utf-8">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace; background: #0d1117; color: #e6edf3; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .header h1 { font-size: 15px; font-weight: 600; color: #58a6ff; display: flex; align-items: center; gap: 8px; }
        .status { display: flex; align-items: center; gap: 10px; font-size: 12px; color: #8b949e; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #3fb950; }
        .status-dot.stopped { background: #f85149; }
        .btn { background: #238636; border: none; color: white; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-family: inherit; }
        .btn:hover { background: #2ea043; }
        .btn:disabled { background: #30363d; color: #8b949e; cursor: not-allowed; }
        .btn.danger { background: #da3633; }
        .btn.danger:hover { background: #f85149; }
        .terminal-container { flex: 1; position: relative; overflow: hidden; }
        #terminal { width: 100%; height: 100%; }
        .loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #8b949e; }
        .footer { background: #161b22; border-top: 1px solid #30363d; padding: 6px 16px; font-size: 11px; color: #8b949e; display: flex; justify-content: space-between; flex-shrink: 0; }
        .shortcuts { display: flex; gap: 16px; }
        .shortcut { display: flex; align-items: center; gap: 4px; }
        .key { background: #21262d; border: 1px solid #30363d; padding: 1px 6px; border-radius: 3px; font-family: inherit; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/xterm@5.3.0/css/xterm.css" />
</head>
<body>
    <div class="header">
        <h1>🤖 Hermes Session Exporter</h1>
        <div class="status">
            <span class="status-dot" id="statusDot"></span>
            <span id="statusText">Starting TUI...</span>
            <button class="btn" id="restartBtn" onclick="restartTUI()" disabled>Restart TUI</button>
            <button class="btn danger" id="killBtn" onclick="killTUI()" disabled>Kill TUI</button>
        </div>
    </div>
    <div class="terminal-container">
        <div id="terminal"></div>
        <div class="loading" id="loading">Loading terminal...</div>
    </div>
    <div class="footer">
        <div class="shortcuts">
            <span class="shortcut"><span class="key">↑↓</span> Navigate sessions</span>
            <span class="shortcut"><span class="key">Enter</span> View messages</span>
            <span class="shortcut"><span class="key">e</span> Export (md/html/json)</span>
            <span class="shortcut"><span class="key">r</span> Refresh</span>
            <span class="shortcut"><span class="key">q</span> Quit</span>
        </div>
        <div>Session data: <code>~/AppData/Local/hermes/state.db</code></div>
    </div>

    <script src="https://unpkg.com/xterm@5.3.0/lib/xterm.js"></script>
    <script src="https://unpkg.com/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
    <script src="https://unpkg.com/xterm-addon-web-links@0.9.0/lib/xterm-addon-web-links.js"></script>
    <script>
        const term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: '"Cascadia Code", "Fira Code", "Consolas", monospace',
            theme: { 
                background: '#0d1117', 
                foreground: '#e6edf3', 
                cursor: '#58a6ff', 
                selection: '#264f78',
                black: '#484f58',
                red: '#ff7b72',
                green: '#3fb950',
                yellow: '#d29922',
                blue: '#58a6ff',
                magenta: '#bc8cff',
                cyan: '#39c5cf',
                white: '#e6edf3',
                brightBlack: '#6e7681',
                brightRed: '#ffa198',
                brightGreen: '#56d364',
                brightYellow: '#e3b341',
                brightBlue: '#79c0ff',
                brightMagenta: '#d2a8ff',
                brightCyan: '#56d4dd',
                brightWhite: '#ffffff',
            },
            convertEol: true,
            allowProposedApi: true,
        });
        
        const fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.loadAddon(new WebLinksAddon.WebLinksAddon());
        
        const container = document.getElementById('terminal');
        term.open(container);
        fitAddon.fit();
        
        window.addEventListener('resize', () => fitAddon.fit());
        
        let ws = null;
        let reconnecting = false;
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('statusDot').classList.remove('stopped');
                document.getElementById('statusText').textContent = 'Connected';
                document.getElementById('restartBtn').disabled = false;
                document.getElementById('killBtn').disabled = false;
                reconnecting = false;
            };
            
            ws.onmessage = (event) => {
                term.write(event.data);
            };
            
            ws.onclose = () => {
                document.getElementById('statusDot').classList.add('stopped');
                document.getElementById('statusText').textContent = 'Disconnected';
                document.getElementById('restartBtn').disabled = false;
                document.getElementById('killBtn').disabled = true;
                if (!reconnecting) {
                    reconnecting = true;
                    setTimeout(connect, 2000);
                }
            };
            
            ws.onerror = (err) => {
                console.error('WebSocket error:', err);
            };
        }
        
        term.onData((data) => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(data);
            }
        });
        
        function restartTUI() {
            document.getElementById('restartBtn').disabled = true;
            document.getElementById('killBtn').disabled = true;
            document.getElementById('statusText').textContent = 'Restarting...';
            fetch('/api/tui/restart', { method: 'POST' })
                .then(r => r.json())
                .then(() => {
                    document.getElementById('statusText').textContent = 'Restarted';
                })
                .catch(err => {
                    console.error('Restart failed:', err);
                    document.getElementById('restartBtn').disabled = false;
                    document.getElementById('killBtn').disabled = false;
                });
        }
        
        function killTUI() {
            document.getElementById('restartBtn').disabled = true;
            document.getElementById('killBtn').disabled = true;
            document.getElementById('statusText').textContent = 'Stopping...';
            fetch('/api/tui/kill', { method: 'POST' })
                .then(r => r.json())
                .then(() => {
                    document.getElementById('statusDot').classList.add('stopped');
                    document.getElementById('statusText').textContent = 'Stopped';
                    document.getElementById('restartBtn').disabled = false;
                });
        }
        
        connect();
    </script>
</body>
</html>
    """
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_input(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/tui/restart")
async def restart_tui():
    stop_tui_process()
    start_tui_process()
    return {"status": "restarted"}


@app.post("/api/tui/kill")
async def kill_tui():
    stop_tui_process()
    return {"status": "stopped"}


@app.get("/api/sessions")
async def list_sessions():
    """List sessions from Hermes DB."""
    import sqlite3
    db = get_hermes_db()
    if not db.exists():
        return {"sessions": []}
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, title, message_count, started_at, ended_at, model, source
        FROM sessions ORDER BY started_at DESC
    """).fetchall()
    conn.close()
    return {"sessions": [dict(r) for r in rows]}


@app.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    """Get messages for a session."""
    import sqlite3
    db = get_hermes_db()
    if not db.exists():
        return {"messages": []}
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, session_id, role, content, tool_name, timestamp
        FROM messages WHERE session_id = ? ORDER BY id
    """, (session_id,)).fetchall()
    conn.close()
    return {"messages": [dict(r) for r in rows]}


@app.get("/health")
async def health():
    return {"status": "ok"}


class ExportRequest(BaseModel):
    session_id: str
    format: str  # md, html, json


ExportRequest.model_rebuild()


@app.post("/api/export")
async def export_session(request: ExportRequest = Body(...)):
    """Export a session to a file."""
    import sqlite3
    from datetime import datetime
    
    db = get_hermes_db()
    if not db.exists():
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT id, session_id, role, content, tool_name, timestamp
        FROM messages WHERE session_id = ? ORDER BY id
    """, (request.session_id,)).fetchall()
    conn.close()
    
    if not rows:
        return {"error": "No messages found"}
    
    # Get session info
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    sess = conn.execute("SELECT title FROM sessions WHERE id = ?", (request.session_id,)).fetchone()
    conn.close()
    
    title = sess["title"] if sess else request.session_id
    
    # Build session object for export
    from .models import Message, Session
    from .exporters.markdown import export_markdown
    from .exporters.html import export_html
    from .exporters.json_export import export_json
    
    model_msgs = [
        Message(
            role=r["role"],
            content=r["content"] or "",
            name=r["tool_name"] if r["tool_name"] else None,
        )
        for r in rows
    ]
    now = datetime.now(timezone.utc)
    sess_obj = Session(
        session_id=request.session_id,
        messages=model_msgs,
        metadata={"session_id": request.session_id},
        title=title,
        started_at=now,
        ended_at=None,
    )
    
    export_fn = {"md": export_markdown, "html": export_html, "json": export_json}[request.format]
    ext_map = {"md": ".md", "html": ".html", "json": ".json"}
    ext = ext_map[request.format]
    
    out_path = Path.home() / "Desktop" / f"session_{request.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    out_path.write_text(export_fn(sess_obj), encoding="utf-8")
    
    return {"status": "ok", "path": str(out_path)}


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the web server."""
    import uvicorn
    
    # Start TUI process on startup
    start_tui_process()
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning")
    finally:
        stop_tui_process()


if __name__ == "__main__":
    run_server()