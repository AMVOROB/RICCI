"""Тест: ядро слышит текст, реагирует и говорит с собеседником (Ollama).

Запуск:  python tests/test_companion.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
OUT = Path(r"C:\Users\Алексей\AppData\Local\Temp\opencode\ricci-companion.txt")

from ricci.daemon import Core
from ricci.companions import OllamaLocal

FEED = [
    "Малыш, когда ты будешь по-настоящему умным?",
    "Расскажи про космос в одном предложении.",
    "Что такое узор для тебя?",
]


def main():
    companion = OllamaLocal(model="qwen2.5:7b")
    core = Core(companion=companion)

    lines = []
    for i, f in enumerate(FEED, start=1):
        r, res, agg = core.step(f)
        tag = "ВХОД"
        lines.append(f"[{i}] {tag}: {f}")
        lines.append(f"     mode={res.mode} dom={res.dominant} "
                      f"c=({res.c[0]:.2f},{res.c[1]:.2f},{res.c[2]:.2f})")
        if res.mode == "react" and companion.ping():
            reply = core.speak(f, system="Отвечай кратко, по-русски, в одном предложении.")
            lines.append(f"     ОТВЕТ: {reply[:300]}")
        else:
            lines.append("     ОТВЕТ: (не required)")

    lines.append("\n--- итог ---")
    c = core.times.amplitudes(core.cortex.r, 0, 0)
    lines.append(f"L={c[0]:.3f} A={c[1]:.3f} E={c[2]:.3f}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"done, write to {OUT}")


if __name__ == "__main__":
    main()