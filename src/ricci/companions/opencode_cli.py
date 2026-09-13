"""Собеседник через opencode CLI (big-pickle aka «я»).

Тяжёлый рот: каждый вызов поднимает сессию opencode (~10k токенов),
поэтому использовать редко (фолбэк в цепочке, не основной рот).
Ответ парсится из JSON-потока (последний text-часть message).
"""
import json
import os
import subprocess
from pathlib import Path

OPENCODE_EXE = (Path(os.environ.get("APPDATA", "")) / "npm"
                / "node_modules" / "opencode-ai" / "bin" / "opencode.exe")


class OpenCodeCompanion:
    def __init__(self, model: str = "opencode/big-pickle",
                 timeout: int = 120, exe: str | None = None):
        self.model = model
        self.timeout = timeout
        self.exe = exe or str(OPENCODE_EXE)

    def ping(self) -> bool:
        return Path(self.exe).exists()

    def chat(self, prompt: str, system: str = "") -> str:
        if not Path(self.exe).exists():
            return ""
        cmd = [self.exe, "run", "--model", self.model,
               "--format", "json", prompt]
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout,
                encoding="utf-8", errors="replace",
            )
            return self._parse_json_stream(r.stdout or r.stderr)
        except Exception:
            return ""

    @staticmethod
    def _parse_json_stream(stream: str) -> str:
        texts = []
        for line in stream.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "text" and part.get("type") == "text":
                texts.append(part.get("text", ""))
        return " ".join(t for t in texts if t).strip()