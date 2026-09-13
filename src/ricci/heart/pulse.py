__all__ = ["PulseSource", "Beat"]

from dataclasses import dataclass
from time import monotonic, sleep


@dataclass
class Beat:
    """Один такт сердца: время тика относительно старта."""
    tick: int
    interval: float
    t_abs: float


class PulseSource:
    """Метроном. Даёт такты с интервалом `interval` секунд.

    Анти-вирус: между тактами жёсткий sleep, активной работы нет.
    Ядро просыпается только на очередной удар сердца.
    """

    def __init__(self, interval: float = 1.0, max_ticks: int | None = None):
        self.interval = max(0.05, interval)
        self.max_ticks = max_ticks
        self._start = monotonic()
        self._ticks = 0

    def beats(self):
        """Бесконечный генератор ударов."""
        n = 0
        while self.max_ticks is None or n < self.max_ticks:
            sleep(self.interval)
            n += 1
            self._ticks = n
            yield Beat(tick=n, interval=self.interval,
                       t_abs=monotonic() - self._start)

    def beats_until(self, seconds: float):
        """Бьёт до заданного времени (для демо/тестов)."""
        deadline = self._start + seconds
        n = 0
        while monotonic() < deadline:
            sleep(self.interval)
            n += 1
            self._ticks = n
            yield Beat(tick=n, interval=self.interval,
                       t_abs=monotonic() - self._start)

    @property
    def ticks(self):
        return self._ticks