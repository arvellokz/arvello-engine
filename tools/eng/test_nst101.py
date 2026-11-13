"""Тесты ARV-NST-101 по разбору R01E (снимок 99ae006f07058ae4): негативные случаи и сравнение исполнений."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
from eng import cab, kit13, models_new as MN  # noqa: E402

BASE = dict(width=1200, handle="push", changer="yes", body="K110", front="K4069")
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
# 3. MOVENTO: точки профиля TANDEM вместо таблицы стр. 437 каталога Blum
orig_pts = cab.movento_points
cab.movento_points = lambda NL: cab.blum_points(NL, True)
_, ch = run({**BASE, "changer": "no"}, "mpts")
expect("MOVENTO: точки TANDEM", ch, "MOVENTO TIP-ON BLUMOTION", "ошибка")
cab.movento_points = orig_pts
# 4. MOVENTO: тяжёлый ящик, а блок оставлен L1 (до 20 кг)
orig_unit, orig_load = cab.tob_unit, MN.DRAWER_LOAD
cab.tob_unit = lambda NL, kg: ("L1", "T60L7340")
MN.DRAWER_LOAD = 30
_, ch = run({**BASE, "changer": "no"}, "munit")
expect("MOVENTO: груз 30 кг, блок L1", ch, "MOVENTO TIP-ON BLUMOTION", "ошибка")
cab.tob_unit = orig_unit
_, ch = run({**BASE, "changer": "no"}, "munit2")
expect("MOVENTO: груз 30 кг, блок по массе", ch, "MOVENTO TIP-ON BLUMOTION", "пройдено")
MN.DRAWER_LOAD = orig_load
# 5. MOVENTO: старый короб — дно без пазов (между боковинами)
cab.MOVENTO["groove"] = 0
_, ch = run({**BASE, "changer": "no"}, "mgr")
expect("MOVENTO: дно без пазов", ch, "MOVENTO (раскрой Blum", "ошибка")
cab.MOVENTO["groove"] = 5
_, ch = run(BASE, "mok")
expect("MOVENTO: исполнение по Blum", ch, "MOVENTO (раскрой Blum", "пройдено")
expect("MOVENTO: исполнение по Blum", ch, "MOVENTO TIP-ON BLUMOTION", "пройдено")
expect("MOVENTO: исполнение по Blum", ch, "Детали не пересекаются", "пройдено")
# 6. ENG-002: фасад висит в 2,5 от передней стенки (как было при TIP-ON до 12.11) — вход самореза 6,5
orig_dr = cab.Build.drawers
def gap_drawers(self, *a, **k):
    recs = orig_dr(self, *a, **k)
    for r in recs:
        fr = self.get(r["front"])
        fr.y0 -= 2.5; fr.y1 -= 2.5
    return recs
cab.Build.drawers = gap_drawers
_, ch = run({**BASE, "changer": "no"}, "fgap")
expect("фасад с зазором 2,5 от стенки", ch, "Фасад ящика: вплотную", "ошибка")
cab.Build.drawers = orig_dr
_, ch = run({**BASE, "changer": "no"}, "fok")
expect("фасад вплотную", ch, "Фасад ящика: вплотную", "пройдено")
# 7. Проверка инструкции комода (13.11): левый уголок к стене под основанием столика
orig_chest = MN.chest6
def angle_under(o):
    b = orig_chest(o)
    if b.derived.get("wall_angles"):
        b.derived["wall_angles"][0].update(x0=60, x1=100)
    return b
MN.NEW["ARV-NST-101"] = ("Комод на 6 ящиков", angle_under); MN.MODELS.update(MN.NEW)
_, ch = run(BASE, "wa")
expect("уголок под столиком", ch, "Уголки к стене", "ошибка")
def angle_low(o):
    b = orig_chest(o)
    a_ = [x for x in b.derived.get("wall_angles", []) if x.get("inside")][0]
    # опустили в зону верхнего ящика и сдвинули вперёд на 50 (14.11: ХДФ 3 — короб кончается за 1 мм до уголка)
    a_.update(z0=a_["z0"] - 100, z1=a_["z1"] - 100, y0=a_["y0"] - 50, y1=a_["y1"] - 50)
    return b
MN.NEW["ARV-NST-101"] = ("Комод на 6 ящиков", angle_low); MN.MODELS.update(MN.NEW)
_, ch = run(BASE, "wa3")
expect("внутренний уголок в ящике", ch, "Уголки к стене", "ошибка")
MN.NEW["ARV-NST-101"] = ("Комод на 6 ящиков", orig_chest); MN.MODELS.update(MN.NEW)
_, ch = run(BASE, "wa2")
expect("уголки свободны", ch, "Уголки к стене", "пройдено")
# 8. Сокращение крепежа 13.11 [М]: ХДФ ≈ 34, дно ящика 4 на ящик; Blum не тронут
s_, _ = run(BASE, "fx")
Hq = {h["id"]: h["qty"] for h in s_["hardware"]}
for k, want in (("SCREW-3.5x16", 34), ("SCREW-4x25D", 24), ("SLIDE-SCREW-M", 72), ("LOCK-SCREW", 24)):
    res.append(("крепёж комода", k, str(want), str(Hq.get(k)), Hq.get(k) == want))
for tag, name, want, got, good in res:
    print(f"{'✓' if good else '✗'} {tag:36s} | {name:28s} | ожидалось: {want:13s} | получено: {got}")
from eng.testutil import finish  # noqa: E402
finish(all(r[-1] for r in res))
