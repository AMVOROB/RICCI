"""Наблюдатель диалога риччи: HTML каждые 10 сек показывает дневник.

GET /          — страница (автообновление через fetch каждые 10с)
GET /api/log   — последние 300 строк дневника + ts + status
POST /api/stop — стоп-файл → ядро корректно уснёт

Запуск:  python server\watch.py [--port 8765]
"""
import argparse
import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LOG = BASE / "logs" / "dialogue.log"
PID = BASE / "logs" / "daemon.pid"
STOP = Path(os.environ.get("TEMP", "/tmp")) / "ricci.stop"


def pid_alive(pid_path: Path) -> bool:
    """Windows-проверка живости процесса через tasklist."""
    try:
        pid = int(pid_path.read_text().strip())
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return f'"{pid}"' in out
    except Exception:
        return False

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Живой диалог риччи</title>
<style>
  body { font-family: Consolas, monospace; background: #0e1117; color: #c9d1d9; margin: 0; padding: 16px; }
  h1 { font-size: 18px; color: #58a6ff; }
  .meta { color: #8b949e; font-size: 12px; margin-bottom: 12px; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-left: 8px; }
  .alive { background: #238636; color: #fff; }
  .dead  { background: #f85149; color: #fff; }
  .log { white-space: pre-wrap; font-size: 13px; line-height: 1.5; }
  .log .hdr { color: #d2a8ff; font-weight: bold; margin-top: 8px; display: inline-block; }
  .log .quest { color: #7ee787; }
  .log .nucleus { color: #79c0ff; }
  .log .mouth { color: #ffa657; }
  .log .state { color: #8b949e; font-style: italic; }
  button { background: #f85149; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; margin-left: 12px; }
</style>
</head>
<body>
  <h1>Живой диалог риччи <span id="status" class="status dead">...</span></h1>
  <div class="meta" id="meta">последнее обновление: --</div>
  <div class="log" id="log"></div>
  <button id="stop">остановить ядро</button>
<script>
  async function refresh() {
    try {
      const r = await fetch('/api/log');
      const d = await r.json();
      const lines = d.lines;
      const el = document.getElementById('log');
      let html = '';
      for (const ln of lines) {
        let cls = '';
        if (ln.startsWith('# ')) cls = 'hdr';
        else if (ln.includes('ЯДРО')) cls = 'nucleus';
        else if (ln.includes('СОБЕСЕДНИК')) cls = 'mouth';
        else if (ln.includes('ВОПРОС')) cls = 'quest';
        else if (ln.includes('[состояние]')) cls = 'state';
        if (cls) html += `<span class="${cls}">${ln}</span>\\n`;
        else html += ln + '\\n';
      }
      el.innerHTML = html || '(пока тишина)';
      const st = document.getElementById('status');
      st.textContent = d.alive ? 'ядро живо' : 'ядро спит/выключено';
      st.className = 'status ' + (d.alive ? 'alive' : 'dead');
      document.getElementById('meta').textContent =
        'последнее обновление: ' + new Date().toLocaleTimeString();
    } catch (e) {
      document.getElementById('meta').textContent = 'ошибка: ' + e.message;
    }
  }
  document.getElementById('stop').onclick = async () => {
    await fetch('/api/stop', {method: 'POST'});
    setTimeout(refresh, 2000);
  };
  refresh();
  setInterval(refresh, 10000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send(200, PAGE.encode("utf-8"),
                       "text/html; charset=utf-8")
        elif self.path == "/api/log":
            lines = []
            if LOG.exists():
                raw = LOG.read_text(encoding="utf-8", errors="replace")
                lines = raw.splitlines()[-300:]
            data = json.dumps({
                "lines": lines,
                "ts": time.time(),
                "alive": pid_alive(PID),
            }, ensure_ascii=False)
            self._send(200, data.encode("utf-8"),
                       "application/json; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path == "/api/stop":
            STOP.write_text("stop", encoding="utf-8")
            self._send(200, json.dumps({"stopped": True}).encode(),
                       "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    print(f"[watch] http://localhost:{args.port}/  (лог: {LOG.name})")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler) \
        .serve_forever()


if __name__ == "__main__":
    main()