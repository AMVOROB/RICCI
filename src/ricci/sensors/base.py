"""Базовый орган ощущений.

Принцип (Алексей, 13.09.2026): орган НЕ понимает мир. Он фиксирует
изменение ΔS между тактами своего канала: «изменилось — насколько — куда».
Понимание живёт в Коре, а не в органе.
"""
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Delta:
    """Ощущение: изменение относительно прошлого такта."""
    intensity: float      # 0..1 — насколько изменилось
    direction: float      # -1..1 — притекло (+1) / утекло (-1)
    tag: str              # 'voice', 'text', 'graph', 'body'


class Sensor(ABC):
    tag = "sensor"
    rhythm = 1.0          # с каким периодом орган считывается (сек)

    @abstractmethod
    def sense(self) -> Delta:
        ...


class NullSensor(Sensor):
    """Тихий орган: ничего не меняется (для тестов/покоя)."""
    tag = "null"

    def sense(self) -> Delta:
        return Delta(intensity=0.0, direction=0.0, tag=self.tag)