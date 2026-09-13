"""Главный цикл ядра (демон).

Правила жизни (анти-вирус):
  - между пульсами жёсткий sleep: ядро спит, когда нет событий;
  - rate-limit на активные обработки за окно времени;
  - запись сердечных ударов редкая (не каждый пульс!) — KB не засоряем;
  - graceful exit: стоп-файл или EXIT-сигнал → сохранить состояние, «заснул»;
  - самодиагностика: каждый сердцебиение считает CPU-нагрузку.

Запуск:  python -m ricci.daemon            # жить всегда
         python -m ricci.daemon --once     # прожить N секунд и выйти
"""
import argparse
import os
import sys
import time

from ..heart import PulseSource
from ..sensors.base import NullSensor
from ..sensors.text import TextSensor
from ..sensors.body import BodySensor
from ..sensors.graph import GraphSensor
from ..cortex import ESNReservoir
from ..wave import ThreeTimes
from ..core.collapse import Collapse
from ..core.kb_bridge import KBBridge

KB_DB = r"D:\Projects\KB\.kb\kb.db"
DEFAULT_STOP_FILE = os.path.expandvars(r"%TEMP%\ricci.stop")


class Core:
    """Сборка ядра: сердце → органы → кора → три времени → коллапс."""

    def __init__(self, kb_db: str = KB_DB, n_nodes: int = 256,
                 input_dim: int = 24):
        self.heart = PulseSource(interval=1.0)
        self.sensors = [
            TextSensor(),
            BodySensor(),
            GraphSensor(kb_db),
        ]
        self.cortex = ESNReservoir(n_nodes=n_nodes, input_dim=input_dim)
        self.times = ThreeTimes()
        self.collapse = Collapse()
        self.kb = KBBridge()

    def _input_vector(self) -> list[float]:
        vec = []
        for s in self.sensors:
            d = s.sense()
            vec.append(d.intensity)
            vec.append(d.direction)
        # раздумье / покой:
        vec += [0.0] * (self.cortex.input_dim - len(vec))
        return vec[: self.cortex.input_dim]

    def _desire_vector(self) -> object:
        """Желание (E): прогноз следующего узора → замкнуть контур."""
        anchor = self.times.readout_anchor()
        return anchor if anchor is not None else None

    def step(self, feed: str | None = None):
        """Один удар сердца: весь контур.
        `feed` — если есть входящий текст (извне), иначе органы сами.
        """
        # собрать ощущения ОДИН раз (органы имеют внутреннее состояние)
        deltas = []
        for s in self.sensors:
            if isinstance(s, TextSensor) and feed:
                deltas.append(s.sense(feed))
            else:
                deltas.append(s.sense())

        u = [v for d in deltas for v in (d.intensity, d.direction)]
        u += [0.0] * (self.cortex.input_dim - len(u))
        u = u[: self.cortex.input_dim]

        r_hat = self._desire_vector()
        r = self.cortex.step(u, r_hat)

        agg = sum(d.intensity for d in deltas) / max(1, len(deltas))
        self.times.push_state(r, agg)
        c_L, c_A, c_E = self.times.amplitudes(r, agg, 0.0)
        res = self.collapse.decide(c_L, c_A, c_E)
        return r, res, agg

    def sleep_now(self):
        """Сохранение и уход в сон (graceful)."""
        try:
            self.kb.note_wake("sleep", "L", (1.0, 0.0, 0.0))
        except Exception:
            pass
        return True


def run(once_seconds: float | None = None, stop_file: str = DEFAULT_STOP_FILE,
        kb_write_every: int = 30):
    core = Core()
    print(f"[ricci] сердце завелось. Путь: {sys.argv[0]}", flush=True)
    beats = core.heart.beats_until(once_seconds) if once_seconds \
        else core.heart.beats()
    for _b in beats:
        try:
            r, res, agg = core.step()
        except Exception as e:
            # ядро не должно умереть от частной ошибки органа
            print(f"[ricci] сбой такта: {e}", flush=True)
            continue

        # активных действий мало: в KB пишем редко (каждые kb_write_every тактов
        # или на значимый переход), иначе эмбеддинг-модель грузится каждый раз.
        if res.mode != "rest":
            if (_b.tick % kb_write_every == 0) or (res.mode in ("react", "want")):
                try:
                    core.kb.note_wake(res.mode, res.dominant, res.c)
                except Exception:
                    pass
        if _b.tick % 120 == 0:
            print(f"[ricci] такт {_b.tick}: режим={res.mode}, "
                  f"c=({res.c[0]:.2f},{res.c[1]:.2f},{res.c[2]:.2f}), "
                  f"ощущение={agg:.3f}", flush=True)

        # graceful: стоп-файл → уйти в сон
        if os.path.exists(stop_file):
            os.remove(stop_file)
            print("[ricci] стоп-файл найден — засыпаю.")
            core.sleep_now()
            break
    print("[ricci] сердце остановлено.")


def main():
    ap = argparse.ArgumentParser(prog="ricci")
    ap.add_argument("--once", type=float, default=None,
                    help="жить по часов и выйти (режим демо)")
    ap.add_argument("--stop-file", default=DEFAULT_STOP_FILE)
    args = ap.parse_args()
    run(once_seconds=args.once, stop_file=args.stop_file)


if __name__ == "__main__":
    main()