"""Тест: два свойства ядра ricci (по решению 13.09.2026).

1. АВТОНОМИЯ: ядро для мышления НЕ нуждается во мне —
   живёт на своих ощущениях (тело/граф), даже без входящего текста.
2. ОТВЕТ ПО ДИРЕКТИВЕ: на МОЙ вопрос ядро ОБЯЗАНО ответить,
   при этом вопрос сначала перемалывается корой (не прокидывается сырым).

Запуск:  python tests/test_autonomy.py
"""
import sys
from pathlib import Path

OUT = Path(r"C:\Users\Алексей\AppData\Local\Temp\opencode\ricci-autonomy.txt")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ricci.daemon import Core
from ricci.companions import OllamaLocal


class RecordingCompanion:
    def __init__(self):
        self.requests = []

    def ping(self):
        return True

    def chat(self, prompt: str, system: str = ""):
        self.requests.append(prompt)
        return (f"Ответ для ядра: твой узор говорит — опора важна, "
                f"держись её. (синтетический рот)")


def main():
    comp = RecordingCompanion()
    core = Core(companion=comp)

    lines = []
    # 1) АВТОНОМИЯ: 6 тактов БЕЗ внешнего текста
    lines.append("=== 1. АВТОНОМНОЕ мышление (я меня не трогаю) ===")
    writhing = False
    for i in range(6):
        r, res, agg = core.step()  # никакого feed!
        lines.append(f"t={i} mode={res.mode} c=({res.c[0]:.2f},{res.c[1]:.2f},{res.c[2]:.2f})")
        if res.mode not in ("rest", "sleep"):
            writhing = True
    lines.append(f"автономно переживал такты (были не-rest): {writhing}")

    # 2) ДИРЕКТИВА: мой вопрос → обязательный ответ
    lines.append("\n=== 2. ОТВЕТ НА ВОПРОС (директива) ===")
    q = "Малыш, почему личность живёт во множестве тактов?"
    lines.append(f"вопрос: {q}")
    answer = core.answer(q)
    lines.append(f"ответ ядра: {answer[:200]}")
    last_req = comp.requests[-1] if comp.requests else "(пусто)"
    lines.append(f"запрос к рту (виден МОЙ вопрос, но он в узоре): {last_req[:200]}")
    has_my_question = q[:20] in last_req
    has_state = "опора" in last_req and "желание" in last_req
    lines.append(f"вопрос вошёл в узор: {has_my_question}")
    lines.append(f"запрос несёт состояние коры: {has_state}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()