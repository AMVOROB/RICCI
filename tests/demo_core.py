"""Демо-прогон ядра: сердце бьётся, органы чувствуют, кора копит узор.

Запуск: python tests/demo_core.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ricci.daemon import Core
from ricci.heart import PulseSource

FEED = [
    "новое: сингулярность",
    "ещё новое: нийенхейс",
    "новое: коллапс",
    "новое: кора",
]


def main():
    core = Core()
    h = PulseSource(interval=0.15, max_ticks=20)
    feeds = 0
    for b in h.beats():
        feed = FEED[feeds % len(FEED)] if b.tick % 4 == 0 else None
        if feed:
            feeds += 1
        r, res, agg = core.step(feed)
        print(f"t={b.tick:02d} mode={res.mode:6s} dom={res.dominant} "
              f"c=({res.c[0]:.2f},{res.c[1]:.2f},{res.c[2]:.2f}) agg={agg:.2f}")
    print("Итог амплитуды:", core.times.amplitudes(core.cortex.r, 0, 0))


if __name__ == "__main__":
    main()