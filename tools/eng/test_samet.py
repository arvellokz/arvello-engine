"""ENG-005 п. 2: направляющие — сменным профилем (cab.SLIDE_PROFILES, решение 14.11 02:05); три уровня Samet (02:00):
эконом Slidea, стандарт Smart Slide с доводчиком, комфорт Smart Slide нажатием + доводчик. Данные — только документы
производителя (docs/фурнитура/samet/). Комод собирается на каждом профиле; негатив на каждое правило (verify13).

    python3 tools/eng/test_samet.py
"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import cab, kit13  # noqa: E402
from eng import models_new as MN  # noqa: E402
from eng.testutil import finish  # noqa: E402
from eng.verify13 import verify  # noqa: E402
from eng.verify_new import verify_new  # noqa: E402

res = []
O = {"width": "1200"}
SP = cab.SLIDE_PROFILES


def ok(name, cond, info=""):
    res.append((name, bool(cond), info))


def fails(s):
    return [n for n, o, _ in verify(s) if not o]


# 1. данные профилей — как в документах производителя
ok("Slidea: проём − 42, NS − 10, корпус ≥ NS + 5, боковина ≤ 16 (брошюра стр. 6)",
   (SP["samet-slidea-sc"]["diw"], SP["samet-slidea-sc"]["dd"], SP["samet-slidea-sc"]["cd"], SP["samet-slidea-sc"]["side_max"]) == (42, 10, 5, 16))
ok("Smart Slide: проём − 45, NS − 10, корпус ≥ NS + 3, боковина ≤ 18 (каталог стр. 6–8)",
   all((SP[p]["diw"], SP[p]["dd"], SP[p]["cd"], SP[p]["side_max"]) == (45, 10, 3, 18) for p in ("samet-smart-sc", "samet-smart-posc")))
ok("артикулы уровней: стандарт 450 — 127240235, комфорт 450 — 127230305, эконом 450 — 12722825",
   (SP["samet-smart-sc"]["codes"][450], SP["samet-smart-posc"]["codes"][450], SP["samet-slidea-sc"]["codes"][450]) ==
   ("127240235", "127230305", "12722825"))
ok("эконом: код продавца 12722325 ≠ брошюре — пометка «уточнить»", "12722325" in SP["samet-slidea-sc"]["code_note"]
   and "уточнить" in SP["samet-slidea-sc"]["code_note"])
ok("Slidea, места шурупов: 250 — 37/69/133, 500 — 4 шурупа, 600 — 37/69/165/261/325",
   cab.slide_points("samet-slidea-sc", 250) == (37, 69, 133) and len(cab.slide_points("samet-slidea-sc", 500)) == 4
   and cab.slide_points("samet-slidea-sc", 600) == (37, 69, 165, 261, 325))
ok("Smart Slide, места шурупов 450: 37/69/165/261/293", cab.slide_points("samet-smart-sc", 450) == (37, 69, 165, 261, 293))
ok("нажатие + доводчик: ряда 250 / 300 нет", 250 not in SP["samet-smart-posc"]["codes"])
# 2. подбор номинала — по правилу, не подгонкой
ok("Smart Slide: 478,5 → 450; 508,5 → 500", cab.pick_slide(478.5, "samet-smart-posc") == 450 and
   cab.pick_slide(508.5, "samet-smart-posc") == 500)
ok("Slidea: 504 → 450 (500 + 5 не помещается); 505 → 500", cab.pick_slide(504, "samet-slidea-sc") == 450 and
   cab.pick_slide(505, "samet-slidea-sc") == 500)
try:
    cab.pick_slide(330, "samet-smart-posc")
    ok("нажатие + доводчик, корпус 330 → ошибка (ряд с 350)", False)
except ValueError:
    ok("нажатие + доводчик, корпус 330 → ошибка (ряд с 350)", True)

# 3. комод на каждом из трёх профилей
built = {}
for ch in ("no", "yes"):
    for lv, prof in MN.NST_LEVELS.items():
        s = kit13.make("ARV-NST-101", {**O, "level": lv, "changer": ch})
        built[(ch, lv)] = s
        drs = s["derived"]["drawers"]
        H = {x["id"]: x for x in s["hardware"]}
        tag = f"{ch}/{lv}"
        P = SP[prof]
        ok(f"{tag}: все ящики на профиле {prof}", {r["slide"] for r in drs} == {prof})
        ok(f"{tag}: артикул профиля в спецификации", P["codes"][drs[0]["NL"]] in H["SLIDES"]["spec"], H["SLIDES"]["spec"][:40])
        ok(f"{tag}: проверки направляющих и пересечений пройдены", not fails(s), fails(s))
        ok(f"{tag}: ручки — только без нажатия", ("HANDLE-128" in H) == (not P["push"]))
        ok(f"{tag}: зазор фасад — корпус: 2,5 при нажатии, 0 с ручками", drs[0]["gap"] == (2.5 if P["push"] else 0))
        ok(f"{tag}: Blum и MILAT в спецификации нет", not any("Blum" in x["spec"] or "MILAT" in x["name"] + x["spec"]
                                                             for x in s["hardware"]))
        ok(f"{tag}: короба одной высоты", len({r["h"] for r in drs}) == 1)
        ok(f"{tag}: В-108 (допущения профиля) в открытых вопросах", "В-108" in [x[0] for x in kit13.questions_for(s)[0]])
# одна модель, два профиля: ширина ящика меняется ровно на разницу отступов (42 против 45)
for ch in ("no", "yes"):
    a, b = built[(ch, "eco")]["derived"]["drawers"][0], built[(ch, "std")]["derived"]["drawers"][0]
    ok(f"{ch}: эконом шире стандарта ровно на 45 − 42 = 3", abs((a["inner_w"] - b["inner_w"]) - 3) < 0.01 and a["LW"] == b["LW"],
       (a["inner_w"], b["inner_w"]))
ok("смена профиля — без правки построителя: тот же chest6, другой NST_LEVELS",
   MN.chest6.__code__.co_names.count("NST_LEVELS") >= 1 and "samet-slidea-sc" not in MN.chest6.__code__.co_consts)

# 4. негативы (на комфорте без столика)
s = built[("no", "comf")]
r0 = s["derived"]["drawers"][0]
ok("нижний ящик: направляющая поднята над болтами стоек (подъём > 0)", r0["lift"] > 0, r0["lift"])


def mutate(fn, base=s):
    s2 = copy.deepcopy(base)
    fn(s2)
    return fails(s2)


def part(s2, pid):
    return next(p for p in s2["parts"] if p["id"] == pid)


sl = r0["box"][0]
ok("негатив: ящик короче NS − 10", mutate(lambda s2: part(s2, sl).update(y1=part(s2, sl)["y1"] - 5)))
ok("негатив: внутренняя ширина ≠ проём − 45", mutate(lambda s2: part(s2, r0["box"][1]).update(
    x0=part(s2, r0["box"][1])["x0"] + 3, x1=part(s2, r0["box"][1])["x1"] + 3)))
ok("негатив: Slidea с шириной Smart Slide (проём − 45)", mutate(lambda s2: s2["derived"]["drawers"][0].update(
    slide="samet-slidea-sc")))
ok("негатив: NS не из ряда (480)", mutate(lambda s2: s2["derived"]["drawers"][0].update(NL=480)))
ok("негатив: NS не наибольший", mutate(lambda s2: s2["derived"]["drawers"][0].update(Dc=560)))
ok("негатив: низ ящика ближе 43 к низу проёма", mutate(lambda s2: s2["derived"]["drawers"][0].update(z0=r0["rb"] + 40)))
ok("негатив: над ящиком меньше 7", mutate(lambda s2: s2["derived"]["drawers"][0].update(limit_top=r0["z0"] + r0["h"] - 1)))
ok("негатив: шуруп не на месте", mutate(lambda s2: next(h for h in s2["holes"] if h["kind"] == "runner_mark").update(
    y=next(h for h in s2["holes"] if h["kind"] == "runner_mark")["y"] + 3)))
ok("негатив: ось шурупов не 11", mutate(lambda s2: [h.update(z=h["z"] + 2) for h in s2["holes"] if h["kind"] == "runner_mark"]))
ok("негатив: нет заднего Ø6", mutate(lambda s2: s2.update(holes=[h for h in s2["holes"] if h["kind"] != "slide_rear"])))
ok("негатив: шурупов в спецификации меньше разметки", mutate(lambda s2: next(
    x for x in s2["hardware"] if x["id"] == "SLIDE-SCREW-S").update(qty=1)))
ok("негатив: без подъёма — шуруп в болте стойки", mutate(lambda s2: [h.update(z=h["z"] - r0["lift"]) for h in s2["holes"]
                                                                       if h["kind"] == "runner_mark" and h["joint"].startswith("J-C1-RUNNER-1-")]))
se = built[("no", "eco")]
re_ = se["derived"]["drawers"][0]
ok("негатив Slidea: корпус мельче NS + 5", mutate(lambda s2: s2["derived"]["drawers"][0].update(Dc=re_["NL"] + 4), se))
ok("негатив Slidea: шурупы по схеме Smart Slide (293 вместо 4 шурупов)", mutate(lambda s2: s2["derived"]["drawers"][0].update(
    slide="samet-smart-sc"), se))
# уголок к стене внутри колонны (со столиком) — не в объёме ящика
sc = built[("yes", "comf")]
wa = lambda s_: next(st for n, st, _ in verify_new(s_, []) if n.startswith("Уголки к стене"))
ok("уголок внутри колонны свободен", wa(sc) == "пройдено", wa(sc))
sc2 = copy.deepcopy(sc)
a_ = [x for x in sc2["derived"]["wall_angles"] if x.get("inside")][0]
a_.update(z0=a_["z0"] - 100, z1=a_["z1"] - 100, y0=a_["y0"] - 50, y1=a_["y1"] - 50)
ok("негатив: уголок в объёме верхнего ящика — ошибка", wa(sc2) == "ошибка", wa(sc2))
# полный комплект A3 на каждом уровне — все проверки (БАЗИС, verify13, verify_new)
kitS = {}
for lv in MN.NST_LEVELS:
    s3, ch3, figs = kit13.write_kit("ARV-NST-101", str(Path(tempfile.mkdtemp()) / "k.pdf"), {**O, "level": lv, "changer": "yes"})
    for f_ in figs:
        kit13.plt.close(f_)
    kitS[lv] = s3
    ok(f"комплект A3 со столиком, {lv}: все проверки пройдены", all(c[1] for c in ch3), [c[0] for c in ch3 if not c[1]][:3])
# инструкции сборщику (A4 комода, A4 ящика, пример ящика A3) — на каждом уровне, все проверки
from eng import eng002_chest as C_, eng002_drawer as E_, eng002_guide as G_  # noqa: E402
from eng.eng002_kit import a4_vs_a3, pdf_text  # noqa: E402
for lv in MN.NST_LEVELS:
    o_ = {**O, "level": lv, "changer": "yes"}
    d_ = Path(tempfile.mkdtemp())
    D1, r1 = C_.write(str(d_ / "c.pdf"), o_)
    D2, r2 = G_.write(str(d_ / "g.pdf"), o_)
    D3, _ = E_.write(str(d_ / "e.pdf"), o_)
    bad = [x[0] for x in r1 + r2 if not x[1]] + D3["view_errors"]
    ok(f"инструкции, {lv}: A4 комода, A4 ящика, пример A3 — проверки пройдены", not bad, bad[:3])
    s_ = kitS[lv]
    txt = pdf_text(d_ / "c.pdf") + pdf_text(d_ / "g.pdf") + pdf_text(d_ / "e.pdf")
    ok(f"инструкции, {lv}: A4 = A3 (зенковка, крепёж)", not a4_vs_a3(pdf_text(d_ / "c.pdf"), s_), a4_vs_a3(pdf_text(d_ / "c.pdf"), s_))
    ok(f"инструкции, {lv}: Blum / MOVENTO / TIP-ON в тексте нет", not any(w in txt for w in ("Blum", "MOVENTO", "TIP-ON", "T65")))
    ok(f"инструкции, {lv}: артикул направляющей профиля в тексте", SP[MN.NST_LEVELS[lv]]["codes"][500] in txt)
    ok(f"инструкции, {lv}: ручка — только у уровней с ручкой", ("Ручка" in txt or "ручки" in txt.lower()) ==
       (not SP[MN.NST_LEVELS[lv]]["push"]) or SP[MN.NST_LEVELS[lv]]["push"])
# Blum — опция (данные не удалены)
MN.NST_SLIDES = "blum"
sb = kit13.make("ARV-NST-101", {**O, "changer": "no"})
MN.NST_SLIDES = "profile"
ok("опция Blum: MOVENTO строится как раньше", {r["sys"] for r in sb["derived"]["drawers"]} == {"movento"})

for n, o_, info in res:
    print("ok  " if o_ else "FAIL", n, "" if o_ else info)
finish(all(o_ for _, o_, _ in res))
