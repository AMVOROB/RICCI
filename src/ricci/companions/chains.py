"""Цепочка собеседников (по решению: big-pickle → deepseek → qwen).

Риччи пробует рты по порядку; берёт первый ответ.
1) big-pickle (opencode CLI) — главный собеседник;
2) DeepSeek — быстрый, если big-pickle недоступен;
3) qwen (Ollama, локальный) — последний фолбэк, когда остальные не ответили.

Демон обращается к роту только на react/want/ponder, не каждый такт.
"""
from .deepseek import DeepSeekCompanion
from .opencode_cli import OpenCodeCompanion
from .ollama_local import OllamaLocal


class FallbackChain:
    def __init__(self, mouths=None):
        self.mouths = mouths or [
            OpenCodeCompanion(model="opencode/big-pickle"),
            DeepSeekCompanion(model="deepseek-chat"),
            OllamaLocal(model="qwen2.5:7b"),
        ]

    def ping(self) -> bool:
        return any(getattr(m, "ping", lambda: False)() for m in self.mouths)

    def chat(self, prompt: str, system: str = "") -> str:
        errors = []
        for m in self.mouths:
            try:
                if not getattr(m, "ping", lambda: False)():
                    raise RuntimeError(f"{type(m).__name__}: нет доступа")
                reply = m.chat(prompt, system=system)
                if reply and reply.strip():
                    return reply
                raise RuntimeError(f"{type(m).__name__}: пустой ответ")
            except Exception as e:
                errors.append(str(e)[:120])
        return ""