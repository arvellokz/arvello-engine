"""ENG-005 п. 2: ящики комода на Samet Smart Slide full | Power — по каталогу производителя (docs/фурнитура/samet/);
негатив на каждое правило (проверки verify13 «Samet: …»).

    python3 tools/eng/test_samet.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import cab, kit13  # noqa: E402
from eng import models_new as MN  # noqa: E402
from eng.testutil import finish  # noqa: E402
from eng.verify13 import verify  # noqa: E402

res = []
O = {"width": "1200", "handle": "push"}


def ok(name, cond, info=""):
    res.append((name, bool(cond), info))


def samet_checks(s):
    return {n: (o, t) for n, o, t in verify(s) if n.startswith("Samet") or n.startswith("Отверстия в детали")}


def all_ok(s):
    return all(o for o, _ in samet_checks(s).values())


def fails(s):
    return [n for n, (o, _) in samet_checks(s).items() if not o]


# 1. правило подбора NS (каталог: NS + 3 ≤ глубина корпуса, наибольший из ряда)
ok("pick: 478,5 → 450", cab.pick_samet(478.5, "po_sc") == 450)
ok("pick: 508,5 → 500 (не 480: такого номинала у Samet нет)", cab.pick_samet(508.5, "po_sc") == 500)
ok("pick: 502,9 → 450 (500 + 3 не помещается)", cab.pick_samet(502.9, "po_sc") == 450)
ok("pick: Soft Close 330 → 300", cab.pick_samet(330, "sc") == 300)
try:
    cab.pick_samet(330, "po_sc")
    ok("pick: Push-Open + Soft Close 330 → ошибка (ряд с 350)", False)
except ValueError:
    ok("pick: Push-Open + Soft Close 330 → ошибка (ряд с 350)", True)
ok("места винтов: 450 → 37 / 69 / 165 / 261 / 293", cab.samet_points(450) == (37, 69, 165, 261, 293))
ok("места винтов: 350 → 4 винта, 250 → 3", len(cab.samet_points(350)) == 4 and len(cab.samet_points(250)) == 3)

for ch, ns, code in (("no", 450, "127230305"), ("yes", 500, "127230306")):
    for h in ("push", "bar"):
        s = kit13.make("ARV-NST-101", {**O, "handle": h, "changer": ch})
        drs = s["derived"]["drawers"]
        H = {x["id"]: x for x in s["hardware"]}
        tag = f"{ch}/{h}"
        exp_code = code if h == "push" else cab.SAMET["codes"]["sc"][ns]
        ok(f"{tag}: все ящики Samet NS {ns}", {r["sys"] for r in drs} == {"samet"} and {r["NL"] for r in drs} == {ns})
        ok(f"{tag}: артикул {exp_code}", exp_code in H["SLIDES"]["spec"], H["SLIDES"]["spec"][:60])
        ok(f"{tag}: проверки Samet и пересечения отверстий пройдены", all_ok(s), fails(s))
        ok(f"{tag}: Blum в спецификации нет", not any("Blum" in x["spec"] or "MOVENTO" in x["name"] for x in s["hardware"]),
           [x["name"] for x in s["hardware"] if "Blum" in x["spec"]])
        ok(f"{tag}: MILAT в чертеже нет", not any("MILAT" in x["name"] + x["spec"] for x in s["hardware"]))
        ok(f"{tag}: короба одной высоты", len({r["h"] for r in drs}) == 1)
        ok(f"{tag}: вопрос В-108 (допущения [М] Samet) — в открытых вопросах листа",
           "В-108" in [x[0] for x in kit13.questions_for(s)[0]])

s = kit13.make("ARV-NST-101", {**O, "changer": "no"})
P = {p["id"]: p for p in s["parts"]}
r0 = s["derived"]["drawers"][0]
ok("нижний ящик: направляющая поднята над болтами стоек (подъём > 0)", r0["lift"] > 0, r0["lift"])


def mutate(fn):
    s2 = copy.deepcopy(s)
    fn(s2)
    return fails(s2)


def part(s2, pid):
    return next(p for p in s2["parts"] if p["id"] == pid)


sl = r0["box"][0]
ok("негатив: ящик короче NS − 10", mutate(lambda s2: part(s2, sl).update(y1=part(s2, sl)["y1"] - 5)))
ok("негатив: DIW ≠ CIW − 45", mutate(lambda s2: part(s2, r0["box"][1]).update(x0=part(s2, r0["box"][1])["x0"] + 3,
                                                                              x1=part(s2, r0["box"][1])["x1"] + 3)))
ok("негатив: NS не из ряда (480)", mutate(lambda s2: s2["derived"]["drawers"][0].update(NL=480)))
ok("негатив: NS не наибольший (глубина позволяет больше)", mutate(lambda s2: s2["derived"]["drawers"][0].update(Dc=560)))
ok("негатив: низ ящика ближе 43 к низу проёма", mutate(lambda s2: s2["derived"]["drawers"][0].update(z0=r0["rb"] + 40)))
ok("негатив: над ящиком меньше 7", mutate(lambda s2: s2["derived"]["drawers"][0].update(limit_top=r0["z0"] + r0["h"] - 1)))
ok("негатив: шуруп не на месте (37 → 40)", mutate(lambda s2: next(h for h in s2["holes"] if h["kind"] == "runner_mark").update(
    y=next(h for h in s2["holes"] if h["kind"] == "runner_mark")["y"] + 3)))
ok("негатив: ось шурупов не 11 над низом проёма", mutate(lambda s2: [h.update(z=h["z"] + 2) for h in s2["holes"]
                                                                       if h["kind"] == "runner_mark"]))
ok("негатив: нет заднего Ø6", mutate(lambda s2: s2.update(holes=[h for h in s2["holes"] if h["kind"] != "slide_rear"])))
ok("негатив: шурупов в спецификации меньше разметки", mutate(lambda s2: next(x for x in s2["hardware"]
                                                                            if x["id"] == "SLIDE-SCREW-S").update(qty=1)))
# без подъёма нижней направляющей шуруп попадает в болт Minifix стойки — проверка пересечений это видит
cab_SAMET_axis = cab.SAMET["screw_axis"]
ok("негатив: без подъёма — шуруп в болте стойки", mutate(lambda s2: [h.update(z=h["z"] - r0["lift"]) for h in s2["holes"]
                                                                       if h["kind"] == "runner_mark" and h["joint"].startswith("J-C1-RUNNER-1-")]))
# уголок к стене внутри левой колонны (со столиком) не должен попасть в объём ящика
from eng.verify_new import verify_new  # noqa: E402
sc = kit13.make("ARV-NST-101", {**O, "changer": "yes"})
wa = lambda s_: next(st for n, st, _ in verify_new(s_, []) if n.startswith("Уголки к стене"))
ok("уголок внутри колонны свободен (Samet, со столиком)", wa(sc) == "пройдено", wa(sc))
sc2 = copy.deepcopy(sc)
a_ = [x for x in sc2["derived"]["wall_angles"] if x.get("inside")][0]
a_.update(z0=a_["z0"] - 100, z1=a_["z1"] - 100, y0=a_["y0"] - 50, y1=a_["y1"] - 50)
ok("негатив: уголок в объёме верхнего ящика — ошибка", wa(sc2) == "ошибка", wa(sc2))
# полный комплект A3 на Samet — все проверки (БАЗИС, verify13, verify_new) пройдены
import tempfile  # noqa: E402
s3, ch3, figs = kit13.write_kit("ARV-NST-101", str(Path(tempfile.mkdtemp()) / "k.pdf"), {**O, "changer": "yes"})
for f_ in figs:
    kit13.plt.close(f_)
ok("комплект A3 со столиком на Samet: все проверки пройдены", all(c[1] for c in ch3), [c[0] for c in ch3 if not c[1]][:3])
# Blum — опция (данные не удалены)
MN.NST_SLIDES = "blum"
sb = kit13.make("ARV-NST-101", {**O, "changer": "no"})
MN.NST_SLIDES = "samet"
ok("опция Blum: MOVENTO строится как раньше", {r["sys"] for r in sb["derived"]["drawers"]} == {"movento"})

for n, o_, info in res:
    print("ok  " if o_ else "FAIL", n, "" if o_ else info)
finish(all(o_ for _, o_, _ in res))
