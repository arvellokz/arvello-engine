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
from eng import models_new as _MNs  # noqa: E402
_MNs.NST_SLIDES = "blum"   # 14.11: тест — про Blum MOVENTO / пазы; Samet — test_samet.py
from eng import bazis as BZ  # noqa: E402
from eng import kit13  # noqa: E402
from eng import eng002_kit as K  # noqa: E402
from eng.sheetlib import Sheet  # noqa: E402
from eng.verify_new import ERR, allowance_consistent, distinct_names, wall_before_drawers  # noqa: E402

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


s, checks = build("ARV-NST-101", dict(width=1200, level="comf", changer="yes", body="K110", front="K4069"), "nst")
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
neg("Б11 обрезка «…»", s, "БАЗИС Б11:", lambda bz, t, r: t[3].append("Направляющая MOVENTO 760H…"))
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

# ---- разбор 13.11 (Claude-чат + ChatGPT): пп. 1–7, на каждый — негатив
# (1) одинаковые названия у разных позиций шкафа
s3 = copy.deepcopy(s2)
_, rep2, _ = kit13.positions(s3)
a_, b_ = [ids[0] for ps, ids in rep2[:2]]
next(q for q in s3["parts"] if q["id"] == b_)["unit"] = next(q for q in s3["parts"] if q["id"] == a_)["unit"]
res.append(("п.1 шкаф: две позиции с одним названием", "distinct_names", distinct_names(s3)[0] == ERR))
res.append(("п.1 шкаф: названия различаются", "distinct_names", distinct_names(s2)[0] != ERR))
# (2) шкаф: стена после ящиков
st, _ = wall_before_drawers(["14. Короба ящиков: дно в пазы", "15. Установить на место и закрепить к стене ДО "
                             "направляющих и ящиков и навески дверей: уголки 4 шт."], 4)
res.append(("п.2 шкаф: стена после ящиков", "wall_before_drawers", st == ERR))
# (3) обрезка без «…»: текст шире ячейки; характеристика покупного изделия обрезана
Sheet.WRAP = False
sh = Sheet("тест", kit13.stamp_for(s), 1, 1, "—")
sh.table(25, 200, ["A", "B"], [["1", "Направляющая MOVENTO 760H4800S NL 480 полное выдвижение"]], [10, 20])
res.append(("п.3 текст шире ячейки", "check_cells", bool(sh.check_cells())))
kit13.plt.close(sh.fig)
spec = next(h["spec"] for h in s["hardware"] if h["id"] == "SLIDES")
neg("п.3 характеристика обрезана в коде", s, "БАЗИС Б11б",
    lambda bz, t, r: [t_.__setitem__(i, x.replace(spec.split()[-1], "")) for t_ in t for i, x in enumerate(t_)])
# (4) В-2 «без припуска» при припуске в заготовке
st, _ = allowance_consistent(["Кромка ABS 2; припуск на фуговку станка (заготовки даны без припуска)"], 1.0)
res.append(("п.4 В-2 «без припуска»", "allowance_consistent", st == ERR))
res.append(("п.4 В-2 в комплекте", "", status(checks, "В-2") is True))
# (6) зенковка: не указана на листе цеха; A4 ≠ A3
neg("п.6 зенковка не указана", s, "БАЗИС Б4б", lambda bz, t, r: [x.update(cs_marked=set()) for x in bz["panels"].values()])
a4 = "все 4 самореза в готовых отверстиях Ø4,5 с зенковкой (4 на ящик — сокращено [М])"
res.append(("п.6 A4 = A3 (норма)", "a4_vs_a3", not K.a4_vs_a3(a4, s)))
s4 = dict(s, _bazis=copy.deepcopy(s["_bazis"]))
for x in s4["_bazis"][0]["panels"].values():
    x["cs_marked"] = set()
res.append(("п.6 A4 «с зенковкой», A3 без неё", "a4_vs_a3", bool(K.a4_vs_a3(a4, s4))))
res.append(("п.6 A4: 6 саморезов дна, A3: 4", "a4_vs_a3", bool(K.a4_vs_a3(a4.replace("(4 на", "(6 на"), s))))
res.append(("п.6 A3 с зенковкой, A4 молчит", "a4_vs_a3", bool(K.a4_vs_a3("саморезы в отверстия", s))))
# (7) номера мельче 6 pt; длинная панель мелко; выноски пересекаются
neg("п.7 номера 4,6 pt", s, "БАЗИС Б12", lambda bz, t, r: bz["panels"][pid_holes].update(label_pt=4.6))
pid_long = next(p for p, r in s2["_bazis"][0]["panels"].items() if max(r["P"]["fr"].Lu, r["P"]["fr"].Lv) >= 2000)
neg("п.7 боковина шкафа 1:25 (87 мм)", s2, "БАЗИС Б12",
    lambda bz, t, r: bz["panels"][pid_long].update(sc=25, print_long=87))


def m7c(bz, t, r):
    u = next(u for u in bz["units"] if u["U"]["kind"] == "ящик")
    R = [i for i, L_ in enumerate(u["leaders"]) if L_[2][0] > L_[1][0]][:2]   # две выноски вправо
    (p1, a1, b1), (p2, a2, b2) = u["leaders"][R[0]], u["leaders"][R[1]]
    u["leaders"][R[0]], u["leaders"][R[1]] = (p1, a1, b2), (p2, a2, b1)       # кружки поменяли местами
neg("п.7 выноски пересекаются", s, "БАЗИС Б9б", m7c)
res.append(("комод: остальные проверки комплекта", "", all(c[1] for c in checks)))
for tag, rule, ok in res:
    print(f"{'✓' if ok else '✗'} {tag:44s} | {rule}")
from eng.testutil import finish  # noqa: E402
finish(all(r[2] for r in res))
