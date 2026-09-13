# Бесплатные ИИ-собеседники.
from .ollama_local import OllamaLocal, Silence
from .openrouter_free import OpenRouterFree
from .deepseek import DeepSeekCompanion
from .opencode_cli import OpenCodeCompanion
from .chains import FallbackChain

__all__ = ["OllamaLocal", "Silence", "OpenRouterFree",
           "DeepSeekCompanion", "OpenCodeCompanion", "FallbackChain"]