"""Основной бесплатный/дешёвый собеседник: DeepSeek API.

Первым в цепочке: быстрый (~1с), ключ уже есть в opencode.json
(provider.deepseek.options.apiKey). Риччи говорит с ним в первую очередь.
"""
import json
import os
import urllib.request
from pathlib import Path

CONFIG = Path(os.path.expanduser("~")) / ".config" / "opencode" / "opencode.json"
API = "https://api.deepseek.com/v1/chat/completions"


def _deepseek_key() -> str:
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
        return cfg["provider"]["deepseek"]["options"].get("apiKey", "")
    except Exception:
        return ""


class DeepSeekCompanion:
    def __init__(self, model: str = "deepseek-chat", key: str | None = None):
        self.model = model
        self.key = key or _deepseek_key()

    def ping(self) -> bool:
        return bool(self.key)

    def chat(self, prompt: str, system: str = "") -> str:
        if not self.key:
            return ""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.8,
        }).encode()
        req = urllib.request.Request(
            API, data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]