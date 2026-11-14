"""ENG-005 п. 1: профиль материалов поставщика «ДСП Центр» (cab.SUPPLY) для комода ARV-NST-101; негатив на каждое правило.

    python3 tools/eng/test_eng005.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import cab, kit13  # noqa: E402
from eng import models_new as MN  # noqa: E402
from eng.testutil import finish  # noqa: E402
from eng.verify_new import ERR, OK, supplier_ok  # noqa: E402

res = []
O = {"width": "1200", "level": "comf"}


def ok(name, cond, info=""):
    res.append((name, bool(cond), info))


for ch in ("yes", "no"):
    s = kit13.make("ARV-NST-101", {**O, "changer": ch})
    B = [p for p in s["parts"] if p["kind"] == "board"]
    ext = s["derived"]["parts_ext"]
    st, t = supplier_ok(s)
    ok(f"{ch}: материалы по профилю ДСП Центр", st == OK, t)
    ok(f"{ch}: плита только ЛДСП 16 и ХДФ 3", {p["material"] for p in B} == {"LDSP16", "HDF3"}, {p["material"] for p in B})
    ok(f"{ch}: фасады 16 мм", all(p["y1"] - p["y0"] == 16 for p in B if "FRONT" in p["id"]))
    ok(f"{ch}: кромка только ПВХ 2 и ПВХ 1", {t_ for p in B for t_ in ext[p["id"]]["edges"].values()} == {"PVC2", "PVC1"})
    ok(f"{ch}: фасады — ПВХ 2 по кругу", all(set(ext[p["id"]]["edges"].values()) == {"PVC2"} and len(ext[p["id"]]["edges"]) == 4
                                             for p in B if "FRONT" in p["id"]))
    ok(f"{ch}: цоколь в цвет корпуса", {p["finish"] for p in B if p["id"].startswith("PL-")} ==
       {next(p["finish"] for p in B if p["id"] == "SIDE-L")})
    ok(f"{ch}: по умолчанию корпус Белый 110, фасады Бунратти 4069",
       {p["finish"] for p in B if "FRONT" in p["id"]} == {"K4069"} and next(p["finish"] for p in B if p["id"] == "SIDE-L") == "K110")
    ok(f"{ch}: короба ящиков белые (K110)", {p["finish"] for p in B if "-BOX" in p["id"]} == {"K110"})
    ok(f"{ch}: текстура у Бунратти", all(ext[p["id"]]["grain"] for p in B if p["finish"] == "K4069"))
    ok(f"{ch}: ХДФ 3 — белый фасадный", {p["finish"] for p in B if p["material"] == "HDF3"} == {"HDFW"})
    ok(f"{ch}: кромки на пласти нет", not any(f[1] == min("xyz", key=lambda a: p[a + "1"] - p[a + "0"])
                                              for p in B for f in ext[p["id"]]["edges"]))
    g = next(c for c in s["checks"] if c["name"].startswith("Глубина"))
    ok(f"{ch}: глубина = фасад 16 + зазор + корпус + ХДФ 3", g["ok"] and g["expected"] == g["actual"], g)
    ok(f"{ch}: Samet NS {'500' if ch == 'yes' else '450'}",
       {r["NL"] for r in s["derived"]["drawers"]} == ({500} if ch == "yes" else {450}))
    # негативы: каждая порча ловится проверкой verify_new
    for name, fn in [("фасад ЛДСП 18", lambda p: p.update(material="LDSP18") if "FRONT" in p["id"] else None),
                     ("декор не переведён (O)", lambda p: p.update(finish="O") if p["id"] == "SIDE-L" else None),
                     ("ХДФ толщиной 4 при материале ХДФ 3", lambda p: p.update(y1=p["y0"] + 4) if p["id"] == "BACK" else None)]:
        s2 = copy.deepcopy(s)
        for p in s2["parts"]:
            fn(p)
        ok(f"{ch}: негатив — {name}", supplier_ok(s2)[0] == ERR, supplier_ok(s2)[1])
    s2 = copy.deepcopy(s)
    s2["derived"]["parts_ext"]["SIDE-L"]["edges"]["-y"] = "ABS2"
    ok(f"{ch}: негатив — кромка ABS 2 (нет у ДСП Центра)", supplier_ok(s2)[0] == ERR)
    s2 = copy.deepcopy(s)
    s2["derived"]["parts_ext"]["PL-F"]["edges"]["-y"] = "PVC1"
    ok(f"{ch}: негатив — кромка на пласти цоколя", supplier_ok(s2)[0] == ERR)

# ядро: профиль ДСП Центр не даёт построить кромку на пласти и плиту не той толщины
b = cab.Build("T", "R01E", "", {}, profile="dspc")
try:
    b.part("X", "Цоколь", 0, 0, 0, 1000, 16, 60, "LDSP16", "O", "carcass", edges={"-y": "PVC04"})
    ok("ядро: кромка на пласти — ошибка", False)
except ValueError:
    ok("ядро: кромка на пласти — ошибка", True)
try:
    b.part("Y", "Фасад", 0, 0, 0, 500, 18, 300, "LDSP16", "O", "fronts")
    ok("ядро: толщина 18 при ЛДСП 16 — ошибка", False)
except ValueError:
    ok("ядро: толщина 18 при ЛДСП 16 — ошибка", True)
p = b.part("Z", "Фасад", 0, 0, 0, 500, 16, 300, "LDSP16", "O", "fronts", edges={"-x": "ABS2", "+x": "PVC04"})
ok("ядро: ABS 2 → ПВХ 2, ПВХ 0,4 → ПВХ 1, O → K4069", p.edges == {"-x": "PVC2", "+x": "PVC1"} and p.finish == "K4069")

# старые модели и шкаф — на базовом профиле (не тронуты профилем ДСП Центра)
w = kit13.make("ARV-WRD-101", {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers", "body": "K110", "front": "K4069"})
# шкаф WRD-101 — на профиле ДСП Центра (ENG-005 п. 6, 14.11)
WB = [p for p in w["parts"] if p["kind"] == "board"]
wx = w["derived"]["parts_ext"]
ok("шкаф WRD-101: профиль ДСП Центр, проверка 18 пройдена", w["derived"]["supplier"]["profile"] == "dspc" and
   supplier_ok(w)[0] == OK, supplier_ok(w))
ok("шкаф: двери ЛДСП 16, ХДФ 3", {p["material"] for p in WB if "DOOR" in p["id"]} == {"LDSP16"} and
   {p["material"] for p in WB if p["material"].startswith("HDF")} == {"HDF3"})
ok("шкаф: кромка только ПВХ 2 и ПВХ 1", {t_ for p in WB for t_ in wx[p["id"]]["edges"].values()} <= {"PVC2", "PVC1"})
ok("шкаф: двери — декор фасадов (K4069), корпус и цоколь — K110",
   {p["finish"] for p in WB if "DOOR" in p["id"]} == {"K4069"} and
   {p["finish"] for p in WB if p["id"].startswith(("PLINTH", "S1-SIDE"))} == {"K110"})
ok("шкаф: текстура дверей вертикально", {wx[p["id"]]["grain"] for p in WB if "DOOR" in p["id"]} == {"z"})
from eng.core import bom  # noqa: E402
ok("шкаф: все детали помещаются в лист 2750 × 1830", not any(r["oversize"] for r in bom(w)["sheets"]))
ww = kit13.make("ARV-WRD-101", {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers",
                                "body": "K3114", "front": "K4430"})
ok("шкаф: декоры K3114 / K4430 — корпус и двери в своих декорах, предупреждение о кромке",
   {p["finish"] for p in ww["parts"] if "DOOR" in p["id"]} == {"K4430"} and
   sum("не проверена" in x for x in ww.get("warnings", [])) == 2)
try:
    kit13.make("ARV-WRD-101", {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers",
                               "body": "W"})
    ok("шкаф: негатив — декор не из базы → ошибка", False)
except Exception:
    ok("шкаф: негатив — декор не из базы → ошибка", True)
MN.WRD_PROFILE = "base"
wb = kit13.make("ARV-WRD-101", {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers"})
MN.WRD_PROFILE = "dspc"
ok("шкаф на базовом профиле: двери ЛДСП 18 (профиль отделим)", {p["material"] for p in wb["parts"] if "DOOR" in p["id"]}
   == {"LDSP18"})
# опция цвета — декоры базы ДСП Центра (14.11): другой декор фасадов и корпуса; кромка в цвет не проверена — предупреждение
sw = kit13.make("ARV-NST-101", {**O, "changer": "no", "body": "K3114", "front": "K4446"})
ok("декоры K3114 / K4446: фасады и корпус в своих декорах", {p["finish"] for p in sw["parts"] if "FRONT" in p["id"]} == {"K4446"}
   and next(p["finish"] for p in sw["parts"] if p["id"] == "SIDE-L") == "K3114")
ok("короба и ХДФ белые при любом декоре", {p["finish"] for p in sw["parts"] if "-BOX" in p["id"] or p["id"] == "BACK"} == {"K110", "HDFW"})
ok("декор без проверенной кромки — предупреждение", sum("не проверена" in x for x in sw.get("warnings", [])) == 2, sw["warnings"])
ok("по умолчанию (Белый 110 + Бунратти 4069) — без предупреждения о кромке",
   not any("не проверена" in x for x in kit13.make("ARV-NST-101", {**O, "changer": "no"}).get("warnings", [])))
try:
    MN.chest6({**O, "changer": "no", "body": "W", "front": "K4069"})
    ok("негатив: декор не из базы — ошибка", False)
except ValueError:
    ok("негатив: декор не из базы — ошибка", True)
from eng import bazis as BZ  # noqa: E402
ok("обозначение — полный код декоров", BZ.designation(sw).endswith("-K3114-K4446"), BZ.designation(sw))
from eng.catalog import products  # noqa: E402
ax = {a["key"]: a for a in products()["ARV-NST-101"]["axes"]}
ok("каталог: оси корпус и фасады — 16 декоров, по умолчанию K110 / K4069", ax["body"]["values"][0] == "K110" and
   ax["front"]["values"][0] == "K4069" and len(ax["body"]["values"]) == len(ax["front"]["values"]) == 16 and "color" not in ax)
# комод на базовом профиле строится как раньше (профиль отделим)
MN.NST_PROFILE = "base"
sb = kit13.make("ARV-NST-101", {**O, "changer": "no"})
MN.NST_PROFILE = "dspc"
ok("комод на базовом профиле: фасады ЛДСП 18, ХДФ 4", {p["material"] for p in sb["parts"] if p["kind"] == "board"} ==
   {"LDSP16", "LDSP18", "HDF4"})

for n, o_, info in res:
    print("ok  " if o_ else "FAIL", n, "" if o_ else info)
finish(all(o_ for _, o_, _ in res))
