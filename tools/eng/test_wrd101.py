"""Негативные и вариантные тесты ARV-WRD-101 (разбор R01E, снимок 0e0f07487367a6f2).
python3 tools/eng/test_wrd101.py — печатает «ожидалось → получено» и итог."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
from eng import kit13, models_new as MN, cab  # noqa: E402
from eng.verify_new import ERR, OK, verify_new  # noqa: E402

BASE = dict(width=2400, height=2800, depth=450, handle="push", fill="drawers", color="O")
res = []


def run(opts, tag):
    s, checks, figs = kit13.write_kit("ARV-WRD-101", f"/tmp/t_{tag}.pdf", {k: str(v) for k, v in opts.items()})
    for f in figs:
        kit13.plt.close(f)
    return s, checks


def status(checks, name):
    for n, ok, t in checks:
        if n.startswith(name):
            return ("ошибка" if not ok else t[1:t.index("]")] if t.startswith("[") else "пройдено"), t
    return "нет проверки", ""


def expect(tag, checks, name, want):
    st, t = status(checks, name)
    res.append((tag, name, want, st, st == want))


# 1. несовместимая планка: 173L6100 при отверстиях Ø5 под евровинт
old = cab.Build.design
def bad_design(self, *a, **k):
    self.hw["HINGE"]["spec"] = self.hw["HINGE"]["spec"].replace("173H7100", "173L6100")
    return old(self, *a, **k)
cab.Build.design = bad_design
_, ch = run(BASE, "plate")
expect("планка 173L6100 + Ø5", ch, "Петля: планка", "ошибка")
cab.Build.design = old
# 2. нулевой ход TIP-ON
MN.PUSH_GAP = 0
_, ch = run(BASE, "gap0")
expect("зазор TIP-ON 0", ch, "Дверь TIP-ON: зазор", "ошибка")
MN.PUSH_GAP = 2
# 3. пересекающаяся траектория: выступ планки больше места
MN.PLATE_ENV = {"y": 61, "protr": 25, "dz": 25}
_, ch = run(BASE, "traj")
expect("выступ планки 25", ch, "Ящик за дверью: короб", "ошибка")
MN.PLATE_ENV = {"y": 61, "protr": 11, "dz": 25}
# 4. противоположное направление винта антресоли (сверху вниз, 4 × 30 в крышку)
old_si = cab.Build.screws_into
def flip(self, F, E, n, along, vals, fastener, joint, **k):
    if fastener == "SCREW-4x25M":
        return old_si(self, E, F, "-z", along, vals, "SCREW-4x30", joint, pilot=(3, 12), at=k.get("at"))
    return old_si(self, F, E, n, along, vals, fastener, joint, **k)
cab.Build.screws_into = flip
_, ch = run(BASE, "screw")
expect("винт антресоли сверху 4 × 30", ch, "Саморез сквозь деталь", "ошибка")
cab.Build.screws_into = old_si
# 5. варианты
s, ch = run(BASE, "ctrl")
expect("контрольный", ch, "Дверь TIP-ON: зазор", "пройдено")
expect("контрольный", ch, "Ящик за дверью: короб", "пройдено")
s1, ch = run({**BASE, "width": 1800}, "mirror")      # 3 секции: правая секция с дверью на левой стороне
expect("1800 (зеркальная секция)", ch, "Ящик за дверью: короб", "пройдено")
expect("1800 (зеркальная секция)", ch, "Петля: планка", "пройдено")
s2, ch = run({**BASE, "handle": "bar"}, "bar")
expect("с ручками", ch, "Дверь TIP-ON", "нет проверки")
expect("с ручками", ch, "Чашка петли", "пройдено")
s3, ch = run({**BASE, "fill": "shelves"}, "shelves")
gone = (not s3["derived"]["drawers"] and not any("SPACER" in p["id"] or "BOX" in p["id"] for p in s3["parts"])
        and not any(h["id"] in ("SLIDES", "SLIDE-LOCK", "TIPON-SYNC") for h in s3["hardware"])
        and not any(h["kind"] == "runner_mark" for h in s3["holes"]))
res.append(("без ящиков", "нет коробов, проставок, Blum, разметки профилей", "пройдено", "пройдено" if gone else "ошибка", gone))
expect("без ящиков", ch, "Ящик за дверью", "нет проверки")
for D in (450, 600):
    s4, ch = run({**BASE, "depth": D}, f"d{D}")
    r = s4["derived"]["drawers"][0]
    expect(f"глубина {D} (NL {r['NL']})", ch, "Внутренний ящик Blum", "пройдено")
ok = all(r[-1] for r in res)
for tag, name, want, got, good in res:
    print(f"{'✓' if good else '✗'} {tag:28s} | {name:40s} | ожидалось: {want:14s} | получено: {got}")
print("ИТОГ:", "все совпали" if ok else "есть расхождения")
