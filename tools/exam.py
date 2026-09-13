"""Экзамен риччи: DeepSeek задаёт вопросы из базы и проверяет на галлюцинации.

Логика:
1. берём случайные настоящие смыслы из KB (title+body как эталон);
2. DeepSeek формулирует по смыслу ЧЕСТНЫЙ вопрос (не упоминая ответ);
3. риччи отвечает ЧЕРЕЗ СВОЙ КОНТУР (question → кора → рот-цепочка);
4. DeepSeek сверяет ответ с базой (через hybrid_search) и вердикт:
   ok | hallucination | partial, + пояснение.

Запуск:  python tools\exam.py --n 3
Результат: печать кратко + full в logs/exam.html и KB.
"""
import argparse
import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, r"D:\Projects\KB")

KB_DB = r"D:\Projects\KB\.kb\kb.db"
OUT = BASE / "logs" / "exam.html"

from ricci.daemon import Core
from ricci.companions import DeepSeekCompanion, FallbackChain, OpenCodeCompanion, OllamaLocal

sys.path.insert(0, str(BASE / "src"))


def random_entries(n: int, db: str = KB_DB) -> list[dict]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    mn, mx = con.execute("select min(id), max(id) from entries").fetchone()
    ids = sorted(random.sample(range(mn, mx + 1), min(n * 3, mx - mn)))
    out = []
    for i in ids:
        row = con.execute(
            "select id, title, body from entries where id >= ? "
            "order by id limit 1", (i,)).fetchone()
        if row and row[2] and len(row[2]) > 80:
            out.append({"id": row[0], "title": row[1], "body": row[2]})
        if len(out) >= n:
            break
    con.close()
    return out


class Examiner:
    """DeepSeek в двух ролях: экзаменатор (вопрос + вердикт)."""

    def __init__(self):
        self.ds = DeepSeekCompanion(model="deepseek-chat")
        self.core = Core(companion=FallbackChain())

    def make_question(self, entry: dict) -> str:
        sys_ = ("Ты экзаменатор для ИИ-ядра. По факту из базы знаний "
                "придумай КРАТКИЙ вопрос (1 предложение), который проверяет, "
                "понимает ли ядро этот смысл. НЕ цитируй ответ в вопросе. "
                "Только вопрос, без добавок.")
        usr = f"Смысл из базы:\n«{entry['body'][:400]}»"
        q = self.ds.chat(usr, system=sys_)
        return (q or entry["title"]).strip()

    def grade(self, entry: dict, question: str, answer: str) -> dict:
        from kb.storage import hybrid_search
        hits = hybrid_search(answer, limit=3)
        refs = "\n".join(
            f"[{h['title']}] {h['body'][:300]}" for h in hits) or "(ничего не нашлось)"
        sys_ = ("Ты строгий проверяющий галлюцинации ИИ-ядра. Сравни ответ "
                "ядра с базой знаний. Верни СТРОГО JSON:\n"
                '{"verdict":"ok|partial|hallucination","ok":0.0..1.0,"why":"одно предложение"}')
        usr = (f"Вопрос: {question}\n\nОтвет ядра: {answer}\n\n"
               f"Релевантное из базы:\n{refs}")
        raw = self.ds.chat(usr, system=sys_)
        try:
            verdict = json.loads(raw.strip()[raw.find("{"):raw.rfind("}") + 1])
        except Exception:
            verdict = {"verdict": "unknown", "ok": 0.0, "why": raw[:120]}
        return verdict


def _safe(s: str) -> str:
    return s.encode("ascii", "replace").decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-answer", action="store_true",
                    help="не гонять рот риччи (только вопрос+сверка)")
    args = ap.parse_args()
    random.seed(args.seed or None)

    ex = Examiner()
    entries = random_entries(args.n)

    rows = []
    print(f"экзамен: {len(entries)} смыслов, рот=FallbackChain")
    for i, e in enumerate(entries, 1):
        t0 = time.time()
        q = ex.make_question(e)
        print(_safe(f"[{i}/{len(entries)}] вопрос: {q[:60]}..."))
        if args.skip_answer:
            answer = "(пропуск ответа)"
        else:
            answer = ex.core.answer(q)
            print(_safe(f"    ответ риччи ({len(answer)}c): {answer[:80]}..."))
        verdict = ex.grade(e, q, answer) if not args.skip_answer \
            else {"verdict": "skip", "ok": 0.0, "why": "—"}
        rows.append({
            "title": e["title"], "question": q, "answer": answer,
            "verdict": verdict, "time": round(time.time() - t0, 1),
        })
        print(_safe(f"    вердикт: {verdict.get('verdict')} "
                    f"({verdict.get('ok')}) {str(verdict.get('why'))[:60]}"))

    _write_html(OUT, rows)
    verdicts = [r["verdict"].get("verdict") for r in rows]
    ok = sum(1 for v in verdicts if v == "ok")
    print(_safe(f"\nитог: ok={ok}/{len(verdicts)}  → {OUT}"))


def _write_html(path: Path, rows: list[dict]):
    parts = ["""<!DOCTYPE html><html lang="ru"><meta charset="utf-8"><title>Экзамен риччи</title>
<style>body{font-family:Consolas,monospace;background:#0e1117;color:#c9d1d9;padding:16px}
h1{font-size:18px;color:#58a6ff}.q{color:#7ee787}.a{color:#ffa657}
.v{font-weight:bold}.ok{color:#3fb950}.partial{color:#d29922}.hallucination{color:#f85149}hr{border:1px solid #30363d}</style>
<body><h1>Экзамен риччи (DeepSeek задаёт и проверяет)</h1>"""]
    for r in rows:
        v = r["verdict"]
        parts.append(
            f"<div><b class='q'>Вопрос:</b> <span class='q'>{r['question']}</span></div>"
            f"<div><b>Ответ риччи:</b><span class='a'> {r['answer']}</span></div>"
            f"<div><b>Источник из базы:</b> {r['title']}</div>"
            f"<div><b>Вердикт:</b> <span class='v {v.get('verdict')}'>"
            f"{v.get('verdict')} (ok={v.get('ok')})</span> "
            f"<i>{v.get('why')}</i> <small>[{r['time']}s]</small></div><hr>")
    path.write_text("\n".join(parts) + "\n</body></html>", encoding="utf-8")


if __name__ == "__main__":
    main()