"""Текстовый орган: ощущает новизну приходящего текста.

Чувствует ΔS между «что было в окне» и «что пришло» — не смысл,
а меру изменения. Смысл извлекает кора.
"""
import hashlib

from .base import Delta, Sensor


class TextSensor(Sensor):
    tag = "text"
    rhythm = 0.5

    def __init__(self, window: int = 16, n_buckets: int = 256):
        self.window = window
        self.n_buckets = n_buckets
        self._seen: list[str] = []

    def _signature(self, text: str):
        """Стабильный хеш-признак текста (дёшево, без эмбеддинга)."""
        h = hashlib.blake2b(text.encode("utf-8", "ignore"), digest_size=8).digest()
        return int.from_bytes(h, "big") % self.n_buckets

    def sense(self, text: str | None = None) -> Delta:
        if text is None:
            return Delta(0.0, 0.0, self.tag)

        # старая «норма» — распределение признаков в окне
        old = self._seen[-self.window:] if self._seen else []
        old_buckets = set(map(self._signature, old))
        new_bucket = self._signature(text)

        novelty = 1.0 if new_bucket not in old_buckets else 0.0
        if len(old_buckets) > 0:
            fraction = len(old_buckets) / self.n_buckets
            intensity = novelty * (0.5 + 0.5 * fraction) \
                if novelty else 0.1 * fraction
        else:
            intensity = novelty

        self._seen.append(text)
        if len(self._seen) > self.window * 2:
            self._seen = self._seen[-self.window:]

        direction = 1.0 if novelty else -0.2
        return Delta(intensity=min(1.0, intensity),
                     direction=direction, tag=self.tag)