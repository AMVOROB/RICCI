"""Три времени личности (Алексей, 13.09.2026):
    - L («был»): опора — инварианты истории коры, на что опираюсь;
    - A («есть»): ощущение — текущий ΔS, внимание в моменте;
    - E («будет»): желание — тренд/предиктор следующего узора.

Амплитуды (c_L, c_A, c_E) → |c|² = кому сейчас принадлежит голос.
Эмоция — это «хочу» (вперёд), а не память.
"""
import numpy as np
from collections import deque


class ThreeTimes:
    def __init__(self, hist_len: int = 40):
        self.hist = deque(maxlen=hist_len)
        self.intens = deque(maxlen=hist_len)

    def push_state(self, r: np.ndarray, intensity: float = 0.0):
        self.hist.append(r.copy())
        self.intens.append(intensity)

    def amplitudes(self, r: np.ndarray, delta_intensity: float,
                   delta_direction: float) -> tuple[float, float, float]:
        """Вернуть (c_L, c_A, c_E) — амплитуды трёх времён.

        L — опора: насколько состояние согласовано с инвариантом истории
           (проекция на среднее прошлого; если узел крепкий — опора сильна).
        A — ощущение: актуальная интенсивность ΔS в моменте.
        E — желание: тренд/предиктор ощущений (внешних!), а не самовозбуждение
            коры. В молчании интенсивность→0 и желание гаснет — ядро «опирается»
            на прожитое (L), а не крутится в пустоту.
        """
        c_L = 0.0
        if len(self.hist) > 2:
            mean_r = np.mean(np.array(self.hist), axis=0)
            denom = np.linalg.norm(mean_r) * np.linalg.norm(r) + 1e-12
            c_L = max(0.0, float(np.dot(mean_r, r) / denom))  # косинус опоры

        c_A = max(0.0, min(1.0, delta_intensity * (1.0 if delta_direction >= 0
                                                   else 0.5)))

        # E из тренда ВНЕШНИХ ощущений (память интенсивностей)
        e_trend = 0.0
        if len(self.intens) >= 3:
            it = list(self.intens)[-4:]
            mean_i = sum(it) / len(it)
            growing = all(it[j + 1] >= it[j] - 1e-9 for j in range(len(it) - 1))
            e_trend = min(1.0, mean_i * (1.5 if growing else 0.8))
        c_E = e_trend if e_trend > 0.001 else 0.0

        # нормализация (не обязательно, но удобно для |c|²)
        s = c_L + c_A + c_E
        if s > 0:
            c_L, c_A, c_E = c_L / s, c_A / s, c_E / s
        return (c_L, c_A, c_E)

    def readout_anchor(self) -> np.ndarray | None:
        """Среднее прошлого (опора L)."""
        if not self.hist:
            return None
        return np.mean(np.array(self.hist), axis=0)