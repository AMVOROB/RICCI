"""Бесплатный сетевой собеседник: OpenRouter :free.

Ключ берётся из opencode auth.json (обычный путь). Только модели :free.
"""
import json
import urllib.request
from pathlib import Path


OPENCODE_AUTH = Path.home() / ".local" / "share" / "opencode" / "auth.json"


def _openrouter_key() -> str:
    try:
        data = json.loads(OPENCODE_AUTH.read_text(encoding="utf-8"))
        return data.get("openrouter", {}).get("key", "") \
            if isinstance(data.get("openrouter"), dict) else ""
    except Exception:
        return ""


# Здоровые бесплатные модели (из нашего реестра #7820)
FREE_MODELS = [
    "literate/gemma-4-31b-it:free",
    "literate/gemma-4-26b-a4b-it:free",
    "intellect/nex-n2.5-pro:free",
    "linguify/ling-3.0-flash-fin:free",
]


class OpenRouterFree:
    def __init__(self, model: str = FREE_MODELS[0], key: str | None = None):
        self.model = model
        self.key = key or _openrouter_key()
        self.url = "https://openrouter.ai/api/v1/chat/completions"

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
            "model": self.model, "messages": messages,
            "max_tokens": 256,
        }).encode()
        req = urllib.request.Request(
            self.url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.key}",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]