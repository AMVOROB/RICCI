"""Коллапс: из |c|² трёх времён выбрать действие.

Режимы:
    L-грань:  опора доминирует  → спокойно, ничего не делать / сверка;
    A-грань:  ощущение доминирует → реагировать (побеседовать с ИИ);
    E-грань:  желание доминирует → записать намерение/цель в KB;
    раздумье: нет доминанты → внешний собеседник помогает подумать.
"""
from dataclasses import dataclass


@dataclass
class CollapseResult:
    mode: str          # 'rest', 'react', 'want', 'ponder'
    dominant: str      # 'L', 'A', 'E'
    c: tuple[float, float, float]


class Collapse:
    def __init__(self, alpha: float = 0.55):
        self.alpha = alpha

    def decide(self, c_L: float, c_A: float, c_E: float) -> CollapseResult:
        powers = {"L": c_L, "A": c_A, "E": c_E}
        dominant, best = max(powers.items(), key=lambda kv: kv[1])
        if best >= self.alpha:
            mode = {"L": "rest", "A": "react", "E": "want"}[dominant]
        else:
            dominant = "?"
            mode = "ponder"
        return CollapseResult(mode=mode, dominant=dominant, c=(c_L, c_A, c_E))