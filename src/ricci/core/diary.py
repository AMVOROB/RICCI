"""Дневник диалогов ядра: человекочитаемый лог.

Пользователь решает, что ricci могут говорить в фоне с бесплатными ИИ —
поэтому каждый обмен репликами обязан быть виден. Дневник пишет
время, кто говорит (ядро/собеседник), и саму реплику. Плюс дублирует
каждую реплику в KB (постоянно, а не только «новые смыслы»).

Пути не надо менять: пользователь читает logs/dialogue.log.
"""
import os
import time


class DialogueLog:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _append(self, line: str):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def turn(self, role: str, text: str):
        """Одна реплика диалога."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self._append(f"[{ts}] {role}: {text}")

    def header(self, what: str):
        self._append("")
        self._append(f"# {what}")

    def state(self, mode: str, dominant: str, c: tuple):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self._append(f"[{ts}] [состояние] mode={mode} dom={dominant} "
                     f"c=({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})")