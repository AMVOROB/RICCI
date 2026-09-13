"""Телесный орган: ощущает состояния тела ИИ (процессор/память/нагрузку).

Не «понимает» систему — чувствует изменение между тактами:
стало тяжелее/легче живётся, вот и всё ощущение.
"""
import psutil

from .base import Delta, Sensor


class BodySensor(Sensor):
    tag = "body"
    rhythm = 5.0

    def __init__(self):
        self._prev = None

    def _state(self) -> tuple[float, float]:
        cpu = psutil.cpu_percent(interval=None) / 100.0
        mem = psutil.virtual_memory().percent / 100.0
        return cpu, mem

    def sense(self) -> Delta:
        cpu, mem = self._state()
        if self._prev is None:
            self._prev = (cpu, mem)
            return Delta(intensity=0.0, direction=0.0, tag=self.tag)
        pc, pm = self._prev
        d_cpu = cpu - pc
        d_mem = mem - pm
        self._prev = (cpu, mem)
        intensity = min(1.0, abs(d_cpu) * 4 + abs(d_mem) * 6)
        direction = 1.0 if (d_cpu + d_mem) > 0 else -1.0
        if intensity < 0.04:
            return Delta(0.0, 0.0, self.tag)
        return Delta(intensity=intensity, direction=direction, tag=self.tag)