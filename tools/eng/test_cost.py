"""ENG-005 п. 5: себестоимость из движка = реальной смете ДСП Центра; негативы.

Смета 14.11 (docs/поставщики/dspc/2026-11-14_смета_комод_без_столика.md): комод без столика, Бунратти 4069, белый 110,
цоколь ЧЁРНЫЙ, ХДФ 3, фасады 16 — 74 064,85 ₸ (материалы 60 720 + работы 13 344,85). Модель с тем же чёрным цоколем
должна дать то же (расхождение — только наклейка: корпус в модели на 3 мм глубже, чем введено в кабинет).

    python3 tools/eng/test_cost.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import cab, kit13  # noqa: E402
from eng import export_cost as EC  # noqa: E402
from eng import models_new as MN  # noqa: E402
from eng.testutil import finish  # noqa: E402

res = []
O = {"width": "1200", "level": "comf", "changer": "no", "body": "K4069", "front": "K4069"}


def ok(name, cond, info=""):
    res.append((name, bool(cond), info))


# 1. как в смете: цоколь чёрный
cab.SUPPLY["dspc_black"] = dict(cab.SUPPLY["dspc"], plinth_fin="black")
MN.NST_PROFILE = "dspc_black"
sb = kit13.make("ARV-NST-101", O)
MN.NST_PROFILE = "dspc"
cb = EC.cost(sb)
ok("смета: материалы = 60 720", round(cb["mat"]) == 60720, cb["mat"])
ok("смета: листы 4 (дуб, белый, чёрный, ХДФ)", sorted(cb["sheets"].values()) == [1, 1, 1, 1], cb["sheets"])
ok("смета: распил 8 000", sum(x["sum"] for x in cb["lines"] if x["what"].startswith("Распил")) == 8000)
ok("смета: наклейка 29,69 ± 0,05 м", abs(next(x["qty"] for x in cb["lines"] if x["what"].startswith("Наклейка")) - 29.69) < 0.05)
ok("смета: итого 74 064,85 ± 0,1 %", abs(cb["dspc"] - 74064.85) / 74064.85 < 0.001, cb["dspc"])
ok("смета: всё сопоставлено поставщику", not cb["missing"], cb["missing"])

# 2. текущая модель: цоколь в цвет корпуса — без чёрного листа
s = kit13.make("ARV-NST-101", O)
c = EC.cost(s)
ok("комод: всё сопоставлено", not c["missing"], c["missing"])
ok("комод: 3 листа (без чёрного)", len(c["sheets"]) == 3, c["sheets"])
ok("комод: дешевле сметы на чёрный лист + распил (≈ 18 600)", 18000 < cb["dspc"] - c["dspc"] < 19500, cb["dspc"] - c["dspc"])
lt = EC.level_totals("ARV-NST-101", O)
ok("комод: три уровня Samet по ценам прайса (эконом 3 307, стандарт 6 925, комфорт 10 816 × 6)",
   [x["slides"]["price"] for x in lt.values()] == [3307, 6925, 10816] and
   all(x["total"] == round(x["dspc"] + 6 * x["slides"]["price"]) for x in lt.values()), {k: x["total"] for k, x in lt.items()})
ok("комод: эконом < стандарт < комфорт", lt["эконом"]["total"] < lt["стандарт"]["total"] < lt["комфорт"]["total"])
ok("эконом: пометка о коде продавца 12722325 — «уточнить»", "12722325" in lt["эконом"]["note"])
ok("комод без столика: комфорт — Samet 127230305 по цене прайса", "127230305" in c["slides"]["комфорт"]["name"] and
   c["totals"]["комфорт"] == round(c["dspc"] + 6 * 10816))
ok("комод: направляющих = ящиков (6)", all(x["nd"] == 6 for x in c["slides"].values()))
ok("комод: метры кромки = модели", abs(sum(c["edge_m"].values()) - sum(s["derived"]["edge_m"].values())) < 0.02)
ok("комод: отверстий в счётчике = в модели", sum(c["holes"].values()) == len(s["holes"]))
ok("комод: Ø15 и Ø4,5 — без цены (прайс их не называет)", {x.split(" ")[0] for x in c["drill_missing"]} == {"Ø4,5", "Ø15"},
   c["drill_missing"])
c3 = EC.cost(s, batch=3)
ok("партия 3: на изделие не дороже одного заказа", c3["dspc"] <= c["dspc"], (c3["dspc"], c["dspc"]))
sw = EC.cost(kit13.make("ARV-NST-101", {**O, "changer": "yes"}))
ok("со столиком дороже без столика", sw["dspc"] > c["dspc"], (sw["dspc"], c["dspc"]))
ok("без столика NS 450 — цена направляющих своего артикула", not c["slide_note"], c["slide_note"])
ok("со столиком NS 500 (127230306) — нет цены, «уточнить», в сумму не идёт", "127230306" in sw["slide_note"] and
   sw["totals"]["комфорт"] is None, sw["slide_note"])

# 3. негативы
pr = EC.load_prices()
p2 = copy.deepcopy(pr)
del p2["sheets"]["ЛДСП Белый 110 (корпус) SM 16*2750*1830 SwissKrono"]
c2 = EC.cost(s, p2)
ok("негатив: нет цены листа — «не сопоставлено», в сумму не идёт", c2["missing"] and c2["dspc"] < c["dspc"], c2["missing"][:1])
p2 = copy.deepcopy(pr)
del p2["edge"]["PVC2|K4069"]
ok("негатив: нет цены кромки — «не сопоставлено»", any("кромка PVC2" in m for m in EC.cost(s, p2)["missing"]))
ok("негатив: декор без цены (Графит 3114) — «не сопоставлено»", EC.cost(kit13.make("ARV-NST-101", {**O, "body": "K3114"}))["missing"])
s2 = copy.deepcopy(s)
for p in s2["parts"]:
    if p["id"] == "SIDE-L":
        p["z1"] += 2000                          # деталь больше листа по площади — лишний лист
ok("негатив: площадь выросла — листов больше", sum(EC.cost(s2)["sheets"].values()) > sum(c["sheets"].values()))

for n, o_, info in res:
    print("ok  " if o_ else "FAIL", n, "" if o_ else info)
finish(all(o_ for _, o_, _ in res))
