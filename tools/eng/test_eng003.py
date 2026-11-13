"""ENG-003: таблица распила (.xlsx) совпадает с CSV выпуска; негативные случаи — каждая порча ловится сверкой.

    python3 tools/eng/test_eng003.py
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import export_cutting as X  # noqa: E402
from eng import kit13  # noqa: E402
from eng.eng002_kit import BASE, WRD  # noqa: E402
from eng.testutil import finish  # noqa: E402

V = Path(__file__).resolve().parents[2] / "docs" / "eng-002" / "выпуск"
SETS = [("ARV-NST-101", {**BASE, "changer": "yes"}, "ARV-NST-101_комод_со_столиком"),
        ("ARV-NST-101", {**BASE, "changer": "no"}, "ARV-NST-101_комод_без_столика"),
        ("ARV-WRD-101", WRD, "ARV-WRD-101_шкаф_2400x2800x450")]
res = []
tmp = Path(tempfile.mkdtemp())

for sku, o, stem in SETS:
    s = kit13.make(sku, dict(o))
    csvp = V / f"{stem}_детали_и_покупные.csv"
    xp = tmp / f"{stem}.xlsx"
    blocks = X.write_xlsx(xp, s)
    bad = X.check_xlsx_file(xp, blocks) + X.check_vs_csv(s, blocks, csvp)
    res.append((f"{stem}: таблица = CSV выпуска", not bad, bad[:2]))
    rows = [r for b in blocks for r in b]
    res.append((f"{stem}: у каждой детали длина ≥ ширины или задана текстура",
                all(r["L"] >= r["W"] or r["grain"] == "вдоль длины" for r in rows), ""))
    res.append((f"{stem}: при одной кромке на паре сторон она в Д1/Ш1",
                all(not (r["edges"][1] and not r["edges"][0]) and not (r["edges"][3] and not r["edges"][2]) for r in rows), ""))

    def neg(name, f):
        b2 = copy.deepcopy(blocks)
        f(b2)
        e = X.check_vs_csv(s, b2, csvp)
        res.append((f"{stem}: негатив — {name}", bool(e), e[:1]))

    neg("пропала деталь", lambda b: b[0].pop())
    neg("другое кол-во", lambda b: b[0][0].update(qty=b[0][0]["qty"] + 1))
    neg("другая длина", lambda b: b[0][0].update(L=b[0][0]["L"] + 1))
    neg("другое название", lambda b: b[0][0].update(name="Деталь"))
    neg("другой декор", lambda b: b[0][0].update(deco="белый"))
    neg("кромка потеряна", lambda b: b[0][0]["edges"].__setitem__(0, ""))
    neg("два материала в блоке", lambda b: b[0].append(copy.deepcopy(b[1][0])))
    neg("материал разбит на два блока", lambda b: b.append([b[0].pop()]))

    s_bad = dict(s, hash="0000000000000000")
    res.append((f"{stem}: негатив — другой снимок модели", bool(X.check_vs_csv(s_bad, blocks, csvp)), ""))

# файл: двойная пустая строка между блоками
from openpyxl import load_workbook  # noqa: E402
s = kit13.make("ARV-NST-101", {**BASE, "changer": "yes"})
xp = tmp / "two_blank.xlsx"
blocks = X.write_xlsx(xp, s)
wb = load_workbook(xp)
ws = wb["Раскрой"]
r0 = next(i for i, r in enumerate(ws.iter_rows(min_row=4), 4) if all(c.value is None for c in r))
ws.insert_rows(r0)
wb.save(xp)
e = X.check_xlsx_file(xp, blocks)
res.append(("негатив — две пустые строки между блоками", bool(e), e[:1]))

# кромка на пласти в модели ловится (цоколь комода, 13.11 — ждёт решения владельца)
pl = X.plast_edges(s)
res.append(("кромка на пласти в модели находится (цоколь PL-F/PL-B)", {p for p, *_ in pl} == {"PL-F", "PL-B"}, pl))
res.append(("шкаф: кромки на пласти нет", not X.plast_edges(kit13.make("ARV-WRD-101", dict(WRD))), ""))

for n, ok, info in res:
    print("ok  " if ok else "FAIL", n, "" if ok else info)
finish(all(ok for _, ok, _ in res))
