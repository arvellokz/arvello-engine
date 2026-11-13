"""Правила оформления для цеха по руководству БАЗИС (tools/eng/bazis.py): для каждого правила — негативный случай.

Собирается комплект (комод со столиком и шкаф), затем в копии регистра «что нарисовано» вносится одна ошибка —
проверка этого правила должна дать «ошибка», остальные — пройти.
"""
from __future__ import annotations

import copy
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
from eng import bazis as BZ  # noqa: E402
from eng import kit13  # noqa: E402
from eng.verify_new import ERR, wall_before_drawers  # noqa: E402

res = []


def build(sku, opts, tag):
    s, checks, figs = kit13.write_kit(sku, f"/tmp/bz_{tag}.pdf", {k: str(v) for k, v in opts.items()})
    for f in figs:
        kit13.plt.close(f)
    return s, checks


def status(checks, prefix):
    for n, ok, t in checks:
        if n.startswith(prefix):
            return ok
    return None


def neg(tag, s, prefix, mutate):
    bz, texts, rows = copy.deepcopy(s["_bazis"])
    mutate(bz, texts, rows)
    ch = BZ.verify_bazis(s, bz, texts, rows)
    got = status(ch, prefix)
    res.append((f"{tag}", prefix, got is False))


s, checks = build("ARV-NST-101", dict(width=1200, handle="push", changer="yes", color="O"), "nst")
bz_rules = [c for c in checks if c[0].startswith("БАЗИС")]
res.append(("комод: все правила БАЗИС пройдены", f"{len(bz_rules)} правил", all(c[1] for c in bz_rules)))
P = s["_bazis"][0]["panels"]
pid_holes = next(p for p, r in P.items() if len(r["table"]) > 5)
pid_two = next(p for p, r in P.items() if r["two"])
pid_end = next(p for p, r in P.items() if r["end_drawn"])
pid_gr = next(p for p, r in P.items() if r["P"]["grooves"])
pid_edge = next(p for p, r in P.items() if len(r["P"]["edges"]) >= 2)


def m1(bz, t, r):
    bz["panels"].pop(pid_holes)
neg("Б1 панель без чертежа", s, "БАЗИС Б1", m1)
neg("Б2 нет второго изображения", s, "БАЗИС Б2", lambda bz, t, r: bz["panels"][pid_two].update(two=False))
neg("Б3 нет вида с торца", s, "БАЗИС Б3", lambda bz, t, r: bz["panels"][pid_end].update(end_drawn=set()))


def m4(bz, t, r):
    d = bz["panels"][pid_holes]["drawn"]
    d.pop(next(iter(d)))                          # одно отверстие не пронумеровано на виде
neg("Б4 отверстие без номера на виде", s, "БАЗИС Б4", m4)
neg("Б4 таблица не в порядке типов", s, "БАЗИС Б4",
    lambda bz, t, r: bz["panels"][pid_holes].update(table=list(reversed(bz["panels"][pid_holes]["table"]))))
neg("Б5 паз без сечения", s, "БАЗИС Б5", lambda bz, t, r: bz["panels"][pid_gr].update(sections=set()))


def m6(bz, t, r):
    e = bz["panels"][pid_edge]["P"]["edges"]
    e.reverse()                                   # длинные раньше коротких
neg("Б6 порядок облицовки длинные → короткие", s, "БАЗИС Б6", m6)
neg("Б6 сторона без знака облицовки", s, "БАЗИС Б6", lambda bz, t, r: bz["panels"][pid_edge].update(edges_signed=set()))


def m7(bz, t, r):
    pos = str(bz["panels"][pid_edge]["pos"])
    for row in r:
        if row[0] == pos:
            row[5] = "1 × 1"                      # спецификация без припуска / другая заготовка
neg("Б7 заготовка в спецификации ≠ лист детали", s, "БАЗИС Б7", m7)
neg("Б8 нет операции «раскрой»", s, "БАЗИС Б8",
    lambda bz, t, r: bz["panels"][pid_holes].update(ops=[o for o in bz["panels"][pid_holes]["ops"] if o[1] != "раскрой"]))
neg("Б8 исполнитель не указан", s, "БАЗИС Б8",
    lambda bz, t, r: bz["panels"][pid_holes]["ops"][0].__setitem__(3, ""))


def m9(bz, t, r):
    bz["units"] = [u for u in bz["units"] if u["U"]["kind"] != "ящик"]
neg("Б9 нет сборочного чертежа ящика", s, "БАЗИС Б9", m9)


def m9b(bz, t, r):
    u = next(u for u in bz["units"] if u["U"]["kind"] == "ящик")
    k = next(iter(u["U"]["fast"]))
    u["U"]["fast"][k] += 50                       # крепёж узла × кол-во больше спецификации
neg("Б9 крепёж узла больше спецификации", s, "БАЗИС Б9", m9b)


def m10(bz, t, r):
    des = BZ.designation(s)
    t[5][:] = [x.replace(des, "ARV-NST-101.R01E") for x in t[5]]
neg("Б10 лист без обозначения исполнения", s, "БАЗИС Б10", m10)
neg("Б11 обрезка «…»", s, "БАЗИС Б11", lambda bz, t, r: t[3].append("Направляющая MOVENTO 760H…"))
neg("поле чертежа: сечение на таблице", s, "БАЗИС: изображения",
    lambda bz, t, r: bz["panels"][pid_gr]["draw_boxes"].append((200, 130, 300, 160)))
# крепление к стене до ящиков (замечание к листу «Сборка и контроль»)
st, _ = wall_before_drawers(["8. Короба: дно в пазы", "9. Установить на место и закрепить к стене ДО направляющих и "
                             "ящиков: уголки 3 шт."], 3)
res.append(("стена после ящиков", "wall_before_drawers", st == ERR))
st, _ = wall_before_drawers(["7. Установить на место и закрепить к стене ДО направляющих и ящиков: уголки 2 шт.",
                             "8. Короба: дно"], 3)
res.append(("число уголков ≠ спецификации", "wall_before_drawers", st == ERR))
# шкаф: те же правила проходят
s2, ch2 = build("ARV-WRD-101", dict(width=2400, height=2800, depth=450, handle="push", fill="drawers", color="O"), "wrd")
bz2 = [c for c in ch2 if c[0].startswith("БАЗИС")]
res.append(("шкаф: все правила БАЗИС пройдены", f"{len(bz2)} правил", all(c[1] for c in bz2)))
res.append(("шкаф: остальные проверки комплекта", "", all(c[1] for c in ch2)))
res.append(("комод: остальные проверки комплекта", "", all(c[1] for c in checks)))
for tag, rule, ok in res:
    print(f"{'✓' if ok else '✗'} {tag:44s} | {rule}")
print("ИТОГ:", "все совпали" if all(r[2] for r in res) else "есть расхождения")
