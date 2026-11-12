"""Тесты ARV-NST-101 по разбору R01E (снимок 99ae006f07058ae4): негативные случаи и сравнение исполнений."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
from eng import cab, kit13, models_new as MN  # noqa: E402

BASE = dict(width=1200, handle="push", changer="yes", color="O")
res = []


def run(opts, tag):
    s, checks, figs = kit13.write_kit("ARV-NST-101", f"/tmp/n_{tag}.pdf", {k: str(v) for k, v in opts.items()})
    for f in figs:
        kit13.plt.close(f)
    return s, checks


def st(checks, name):
    for n, ok, t in checks:
        if n.startswith(name):
            return "ошибка" if not ok else "пройдено"
    return "нет проверки"


def expect(tag, ch, name, want):
    got = st(ch, name)
    res.append((tag, name, want, got, got == want))


# 1. корпуса эксцентриков обеих стоек с одной стороны (как в R01E 99ae…) — доступ закрыт
orig = cab.Build.carcass
def same_side(self, *a, **k):
    if k.get("partitions"):
        k["partitions"] = [tuple(p[:3]) + ("+",) for p in k["partitions"]]
    return orig(self, *a, **k)
cab.Build.carcass = same_side
_, ch = run(BASE, "acc")
expect("стойки: эксцентрики с одной стороны", ch, "Доступ инструмента", "ошибка")
cab.Build.carcass = orig
# 2. исполнения со столиком и без
_, ch = run(BASE, "ok")
expect("исполнение со столиком", ch, "Помещается: матрас", "пройдено")
expect("исполнение со столиком", ch, "Высота изделия", "пройдено")
expect("исполнение со столиком", ch, "Доступ инструмента", "пройдено")
s0, ch0 = run({**BASE, "changer": "no"}, "no")
expect("без столика", ch0, "Помещается: матрас", "нет проверки")
expect("без столика", ch0, "Высота изделия", "пройдено")
for tag, name, want, got, good in res:
    print(f"{'✓' if good else '✗'} {tag:36s} | {name:28s} | ожидалось: {want:13s} | получено: {got}")
print("ИТОГ:", "все совпали" if all(r[-1] for r in res) else "есть расхождения")
