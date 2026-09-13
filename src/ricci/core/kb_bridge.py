"""Граница ядра с базой знаний: чтение ощущений и запись результатов.

Запись идёт через kb.storage (обход MCP, который у нас таймаутит).
Автор записи — риччи (ядро), чтобы LLM-шум не засорял KB.
"""
import os
import sys


class KBBridge:
    def __init__(self, kb_path: str = r"D:\Projects\KB"):
        self.kb_path = kb_path

    def _add(self, title: str, body: str, tags: str) -> int:
        if self.kb_path not in sys.path:
            sys.path.insert(0, self.kb_path)
        from kb.storage import add_entry
        return add_entry(
            title=title,
            body=body,
            tags=tags,
            writer_id="ricci",
            source="ricci",
        )

    def note_wake(self, mode: str, dominant: str, c: tuple) -> int:
        body = (
            f"Такт жизни ядра ricci. Коллапс: mode={mode}, "
            f"доминирует грань {dominant}, амплитуды c_L={c[0]:.3f}, "
            f"c_A={c[1]:.3f}, c_E={c[2]:.3f}."
        )
        try:
            return self._add(f"ricci-пульс: {mode}/{dominant}", body,
                             "project,ricci,self,life")
        except Exception as e:
            # молча: отсутствие записи не должно ломать пульс ядра
            return 0

    def note_thought(self, text: str, tags: str = "project,ricci,thought") -> int:
        try:
            return self._add(
                "ricci-мысль",
                text[:4000],
                tags,
            )
        except Exception:
            return 0

    def note_dialogue(self, prompt: str, reply: str,
                      tags: str = "project,ricci,dialogue") -> int:
        body = f"Ядро спросило:\n{prompt[:1500]}\n\nОтвет собеседника:\n{reply[:2500]}"
        try:
            return self._add("ricci-разговор", body, tags)
        except Exception:
            return 0