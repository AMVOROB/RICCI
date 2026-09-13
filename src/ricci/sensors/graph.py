"""Графовый орган: ощущает движение в пространстве смыслов (KB).

Фаза 1: чтение количества/последней записи KB — база «дышит»?
Фаза 2 (позже): Ollivier–Ricci кривизна подграфа — возникло противоречие.
Сейчас орган фиксирует ΔS «стало записей больше / теги изменились».
"""
import sqlite3
import os

from .base import Delta, Sensor


class GraphSensor(Sensor):
    tag = "graph"
    rhythm = 10.0

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._prev = None

    def _state(self):
        if not os.path.exists(self.db_path):
            return None
        try:
            con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            n = con.execute("select count(*) from entries").fetchone()[0]
            last = con.execute(
                "select max(id) from entries").fetchone()[0]
            con.close()
            return n, last
        except Exception:
            return None

    def sense(self) -> Delta:
        st = self._state()
        if st is None:
            return Delta(0.0, 0.0, self.tag)
        if self._prev is None:
            self._prev = st
            return Delta(0.0, 0.0, self.tag)
        n, last = st
        pn, pl = self._prev
        self._prev = st
        intensity = min(1.0, abs(n - pn) / 20.0)
        direction = 1.0 if n > pn else (-1.0 if n < pn else 0.0)
        if intensity < 1e-6:
            return Delta(0.0, 0.0, self.tag)
        return Delta(intensity=intensity, direction=direction, tag=self.tag)