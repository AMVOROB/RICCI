"""Орган чтения KB: риччи сам черпает смыслы из нашей базы.

Каждый N-ый такт орган выбирает случайную запись из KB и передаёт
её содержимое как текст-ощущение (ΔS). Ядро «пережёвывает узор базы»
так же, как любой другой текст мира. Это фаза «изучает нашу базу».

Использует kb.storage напрямую (обход MCP — тот таймаутит).
"""
import os
import random
import sqlite3
import sys

from .base import Delta, Sensor


class KBSenseSensor(Sensor):
    tag = "kbsense"
    rhythm = 45.0   # раз в ~45 тактов (ядро молча дышит базой)

    def __init__(self, kb_path: str = r"D:\Projects\KB",
                 db_path: str | None = None,
                 min_id: int = 0, max_id: int = 0):
        self.kb_path = kb_path
        self.db_path = db_path or (
            os.path.join(kb_path, ".kb", "kb.db"))
        self._min_id = min_id
        self._max_id = max_id
        self._last_read = None

    def _bounds(self):
        if not os.path.exists(self.db_path):
            return self._min_id, self._max_id
        try:
            con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            mn, mx = con.execute(
                "select min(id), max(id) from entries").fetchone()
            con.close()
            return (mn or self._min_id, mx or self._max_id)
        except Exception:
            return self._min_id, self._max_id

    def _random_entry(self):
        try:
            mn, mx = self._bounds()
            if not mx:
                return None, None, None
            target = random.randint(mn, mx)
            con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            row = con.execute(
                "select id, title, body from entries "
                "where id >= ? order by id limit 1", (target,)).fetchone()
            con.close()
            if not row or not row[2]:
                return row[0] if row else None, None, None
            return row[0], row[1], row[2]
        except Exception:
            return None, None, None

    def sense(self) -> Delta:
        if random.random() > (self.rhythm / 100.0) * 0.05:
            return Delta(0.0, 0.0, self.tag)
        sid, title, body = self._random_entry()
        if not sid:
            return Delta(0.0, 0.0, self.tag)
        # тело короткое, чтобы не переполнить вектор
        text = title if title else ""
        snippet = body[:250].replace("\n", " ")
        if text and snippet:
            text = f"{text}: {snippet}"
        elif snippet:
            text = snippet
        self._last_read = (sid, text)
        return Delta(intensity=0.55, direction=0.0, tag=self.tag,
                     text=text)