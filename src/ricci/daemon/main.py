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
from ..core.diary import DialogueLog

KB_DB = r"D:\Projects\KB\.kb\kb.db"
DEFAULT_STOP_FILE = os.path.expandvars(r"%TEMP%\ricci.stop")
DEFAULT_DIARY = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                              "logs", "dialogue.log")
DEFAULT_DIARY = os.path.abspath(DEFAULT_DIARY)


class Core:
    """Сборка ядра: сердце → органы → кора → три времени → коллапс."""

    def __init__(self, kb_db: str = KB_DB, n_nodes: int = 256,
                 input_dim: int = 24, companion=None, language: str = "ru",
                 diary: DialogueLog | None = None):
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
        self.companion = companion
        self.language = language
        self.diary = diary or DialogueLog(DEFAULT_DIARY)
        self._last_feed = ""
        self._conversation_seq = 0

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
                self._last_feed = feed
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

    def _current_state(self) -> tuple:
        return self.times.amplitudes(self.cortex.r, 0.0, 0.0)

    def _form_ask(self, c_L: float, c_A: float, c_E: float) -> str:
        """Промпт рождается ИЗ СОСТОЯНИЯ КОРЫ, а не из сырого входа.

        Ядро — не промптовый малыш: компаньон получает то, что ядро
        само собрало между ощущениями, и вопрос-желание E.
        """
        feel = getattr(self, "_last_feed", "")
        want = "поговорить с собеседником" if c_E > c_L else "сверить мою опору с твоей"
        lang = self._language_name()
        if feel:
            ask = (f"Я (ядро ricci) накопил узор: опора L={c_L:.2f}, "
                   f"ощущение A={c_A:.2f}, желание E={c_E:.2f}. "
                   f"Последнее ощущение мира: «{feel[:200]}». "
                   f"Сейчас я хочу {want}. "
                   f"Ответь мне как собеседник, говори на {lang}, в одном предложении.")
        else:
            ask = (f"Я (ядро ricci) в покое: опора L={c_L:.2f}, "
                   f"желание E={c_E:.2f}. Расскажи что-нибудь, говори на "
                   f"{lang}, коротко — я захотел {want}.")
        return ask

    def _language_name(self) -> str:
        names = {
            "ru": "русском",
            "en": "английском",
            "uk": "украинском",
            "de": "немецком",
            "fr": "французском",
            "zh": "китайском",
        }
        return names.get(self.language, "русском")

    def speak(self, res) -> str:
        """Рот: ядро само формулирует запрос из состояния коры и зовёт
        собеседника. Ответ возвращается в текстовый орган как ΔS.
        Всё пишется в дневник и в KB (реплики видны пользователю).
        """
        if self.companion is None or not self.companion.ping():
            return ""
        c_L, c_A, c_E = self._current_state()
        ask = self._form_ask(c_L, c_A, c_E)
        self._conversation_seq += 1
        self.diary.header(f"беседа #{self._conversation_seq}")
        self.diary.state(res.mode, res.dominant, res.c)
        self.diary.turn("ЯДРО", ask)
        reply = self.companion.chat(ask)
        # ответ = новое ощущение мира, снова размалывается корой
        if reply:
            self.diary.turn("СОБЕСЕДНИК", reply)
            self._last_feed = reply
            self.sensors[0].sense(reply)
            self.kb.note_dialogue(ask, reply)
        return reply

    def answer(self, question: str) -> str:
        """Канал директивы: МОЙ вопрос — ядро ОБЯЗАНО ответить.

        Вопрос входит как ощущение мира (ΔS) → прогоняется корой →
        ядро само рождает запрос собеседнику (текст вопроса уже в
        узоре) → получает ответ и возвращает его. Решение остаётся в коре.
        Всё пишется в дневник и в KB.
        """
        r, res, agg = self.step(question)
        if self.companion is None or not self.companion.ping():
            return ""
        self._conversation_seq += 1
        self.diary.header(f"вопрос #{self._conversation_seq}")
        self.diary.turn("ВОПРОС", question)
        ask = self._form_ask(*self._current_state())
        self.diary.state(res.mode, res.dominant, res.c)
        self.diary.turn("ЯДРО", ask)
        reply = self.companion.chat(ask)
        if reply:
            self.diary.turn("СОБЕСЕДНИК", reply)
            self.sensors[0].sense(reply)
            self.kb.note_dialogue(ask, reply)
        return reply

    def remember(self, meaning: str, source: str = "диалог") -> int:
        """Записывает НОВЫЙ смысл в KB (после диалога ядро решает,
        что осмыслилось). Возвращает id записи KB или 0."""
        return self.kb.note_thought(
            text=f"[{source}] {meaning}",
            tags="project,ricci,meaning",
        )

    def sleep_now(self):
        """Сохранение и уход в сон (graceful)."""
        try:
            self.kb.note_wake("sleep", "L", (1.0, 0.0, 0.0))
        except Exception:
            pass
        return True


def run(once_seconds: float | None = None, stop_file: str = DEFAULT_STOP_FILE,
        kb_write_every: int = 30, companion=None, language: str = "ru"):
    core = Core(companion=companion, language=language)
    print(f"[ricci] сердце завелось. Путь: {sys.argv[0]}", flush=True)
    if companion is not None:
        print(f"[ricci] рот доступен: {type(companion).__name__}, "
              f"язык={language}", flush=True)
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
        # фоновый рот: ядро само решает заговорить, но НЕ каждый такт —
        # голос только на просев (периодичность), рот дорогой (opencode CLI)
        if (companion is not None and res.mode in ("react", "want", "ponder")
                and _b.tick % max(3, kb_write_every // 4) == 0):
            try:
                core.speak(res)
            except Exception as e:
                print(f"[ricci] рот сбой: {e}", flush=True)
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
    ap.add_argument("--mouth", choices=["none", "ollama", "openrouter",
                                        "chain"],
                    default="none",
                    help="бесплатный рот для фонового общения: "
                         "chain = big-pickle→deepseek→qwen")
    ap.add_argument("--lang", default="ru", help="язык общения ядра")
    args = ap.parse_args()

    companion = None
    if args.mouth == "ollama":
        from ..companions import OllamaLocal
        companion = OllamaLocal(model="qwen2.5:7b")
    elif args.mouth == "openrouter":
        from ..companions import OpenRouterFree
        companion = OpenRouterFree()
    elif args.mouth == "chain":
        from ..companions import FallbackChain
        companion = FallbackChain()

    run(once_seconds=args.once, stop_file=args.stop_file,
        companion=companion, language=args.lang)


if __name__ == "__main__":
    main()