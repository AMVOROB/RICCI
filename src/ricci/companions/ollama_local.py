"""Локальный бесплатный собеседник: Ollama (qwen2.5) — без сети."""
import json
import urllib.request


class OllamaLocal:
    def __init__(self, model: str = "qwen2.5:7b", host: str = "127.0.0.1",
                 port: int = 11434):
        self.model = model
        self.url = f"http://{host}:{port}/api/generate"

    def ping(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url[:-len('/api/generate')]}/api/tags",
                                        timeout=3):
                return True
        except Exception:
            return False

    def chat(self, prompt: str, system: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data.get("response", "")


class Silence:
    """Собеседник-молчание: если никого нет рядом."""
    def ping(self) -> bool:
        return True

    def chat(self, prompt: str, system: str = "") -> str:
        return ""