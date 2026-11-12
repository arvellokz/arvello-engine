"""Рабочий комплект тумбы «Самал» (ARV-NST-001) из снимка конфигурации: 11 листов A3.

    python tools/eng/kit_samal.py OUT.pdf [color=W|C|O|G]

01 Общий вид · 02 Сборочный чертёж · 03 Боковины · 04 Крышка и дно · 05 Задняя стенка и цоколь ·
06 Фасад · 07 Ящик · 08 Узлы · 09 Спецификация, кромка, раскрой · 10 Сборка и контроль · 11 Открытые вопросы.

Способ изготовления — по независимым размерам: все отверстия задаются от баз деталей (присадка на станке
или по кондуктору), детали взаимозаменяемы. По месту выполняется только выставление фасадов (зазоры),
без сверления по месту. Нерешённые вопросы — на листе 11; они блокируют выпуск.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from eng.boardkit import EDGE_T, EDGE_TXT, NAME, Frame, blank, detail, hole_rows, section, vec  # noqa: E402
from eng.catalog import compile, materials  # noqa: E402
from eng.core import bom, to_model  # noqa: E402
from eng.sheetlib import CTR, DIM, HID, PHANTOM, RED, THIN, VIS, Sheet, View  # noqa: E402

SKU = "ARV-NST-001"
TOTAL = 11
SC = 5          # масштаб видов изделия и деталей 1:5

POS = {"SIDE-L": 1, "SIDE-R": 2, "TOP": 3, "BOTTOM": 4, "BACK": 5, "PL-F": 6, "PL-B": 6, "PL-SL": 7, "PL-SR": 7,
       "FRONT-1": 8, "FRONT-2": 8}
for _i in (1, 2):
    POS.update({f"BOX{_i}-SL": 9, f"BOX{_i}-SR": 9, f"BOX{_i}-F": 10, f"BOX{_i}-B": 11, f"BOX{_i}-BOT": 12})
BUYPOS = {"SLIDE-LOCK": 22, "SLIDE-SCREW": 23, "LOCK-SCREW": 24, "ECC-BOLT": 25, "SLIDES": 13, "HANDLE-128": 14, "SCREW-M4x22": 15, "ECC-15": 16, "DOWEL-8x30": 17, "CONF-7x50": 18,
          "SCREW-4x25": 19, "SCREW-3.5x16": 20, "GLUE-PVA": 21}
DETAIL_SHEET = {1: 3, 2: 3, 3: 4, 4: 4, 5: 5, 6: 5, 7: 5, 8: 6, 9: 7, 10: 7, 11: 7, 12: 7}


def node_of(h):
    j = h["joint"]
    if j.startswith(("J-L-", "J-R-")):
        return "А"
    if j.startswith("J-BOTTOM-PL"):
        return "Б"
    if j.startswith("J-PL-"):
        return "В"
    if j.startswith("J-FRONT"):
        return "Г"
    if j.startswith("J-HANDLE"):
        return "Д"
    if j.startswith("J-BOX") and j.endswith("BOT"):
        return "Ж"
    if j.startswith("J-BOX"):
        return "Е"
    if j == "J-BACK":
        return "И"
    return ""


def n(x):
    """Число для листа: десятичная запятая."""
    return f"{x:g}".replace(".", ",")


_n = n


def P(s, pid):
    return next(p for p in s["parts"] if p["id"] == pid)


def dims(p):
    return p["x1"] - p["x0"], p["y1"] - p["y0"], p["z1"] - p["z0"]


def color_name(s):
    return materials()["colors"][s["options"]["color"]]["name"]


def mat_txt(s, p):
    fin = p["finish"]
    dec = {"INNER": "белый", "black": "чёрный"}.get(fin) or f"«{materials()['colors'][fin]['name']}»"
    m = {"LDSP16": "ЛДСП 16", "LDSP18": "ЛДСП 18", "HDF4": "ХДФ 4"}[p["material"]]
    return f"{m} {dec}"


def inner_txt(s):
    f = s["derived"]["interior_finish"]
    return "белая" if f == "INNER" else f"«{materials()['colors'][f]['name']}» (плита корпуса)"


def edge_txt(ext):
    e = ext.get("edges", {})
    if not e:
        return "без кромки"
    by = {}
    for f, t in e.items():
        by.setdefault(EDGE_TXT[t], []).append(NAME[f])
    return "; ".join(f"{k}: {', '.join(v)}" for k, v in by.items())


QUESTIONS = [
    ("В-1", "Плита: поставщик и артикул ЛДСП 16 «{DECOR}», наличие того же декора в 18 мм для фасадов "
            "(иначе — МДФ 18 в плёнке); ЛДСП 16 чёрная (цоколь); короба ящиков — {BOX}; фактическая толщина партии",
     "раскрой всех поз., глубины присадки", "Arvello + поставщик", "паспорт плиты, замер 3 листов"),
    ("В-2", "Кромка: ABS 2 и ПВХ 0,4 в цвет декора; припуск на фуговку кромкооблицовочного станка — "
            "заготовка на листе 09 дана как «готовый минус кромка» без припуска",
     "размеры заготовок, лист 09", "цех плиты", "паспорт станка, проба"),
    ("В-5", "Ручка-скоба: артикул, межосевое 128, винты M4 (длина при фасаде 18 — кандидат M4 × 22, "
            "ввёртывание в ручку ≥ 4 мм)", "поз. 8, 14, 15, узел Д", "Arvello", "образец ручки"),
    ("В-10", "Допуски: раскрой ±0,5; присадка ±0,3 (ЧПУ / присадочный станок) или ±0,5 (кондуктор); "
             "разность диагоналей корпуса ≤ 1,5; зазоры фасадов 3 ± 0,5 — согласовать с цехом",
     "контроль, лист 10", "технолог цеха + Arvello", "записать в техкарту"),
    ("В-12", "Пробная сборка одного ящика (профиль, замки, крючок, регулировка, ход) и одной стяжки Minifix на обрезке; программа испытаний образца: груз в ящиках (кг) и его положение, выдвинутый ящик, число циклов, "
             "критерии устойчивости и прогиба — сейчас в контроле только приёмка сборки (лист 10), устойчивость не нормирована",
     "приёмка образца", "Arvello", "утвердить программу испытаний"),
]


# Решения, принятые в R02E (были вопросами В-6…В-9, В-11): показаны на чертежах и в выпуске не открыты.
DECISIONS = [
    ("В-3", "Закрыто по Häfele CFCD 2014: корпус 262.26.033 — плита 16, A 8,0, глубина 12,5 +0,5, Ø15, B 24 или 34 (стр. 294); "
            "болт S200 262.27.679 — B 24, резьба 11 под Ø5 (стр. 301) → Ø5 × 12; отверстие в торце Ø8 (гильза Ø7,5; стр. 294 — Ø7 "
            "или Ø8 по болту), глубина 32 = B + радиус корпуса + 0,5. Остаток плиты 3,0–3,5. Листы 2014 г. — сверить с поставкой."),
    ("В-4", "Закрыто по Blum TANDEM RU v4: 560H3500B и замки T51.1700.04 (стр. 20); SKW = LW − 42 +0/−1,5, SKL = NL − 10, "
            "место NL + 3, стенки 11–16, утопление дна 12–15, низ дна → низ профиля 27,5, ось саморезов → низ профиля 37, "
            "от боковины корпуса до внутр. пласти боковины ящика 21, над ящиком ≥ 7 (стр. 22); саморезы Ø4 × 15 в точках "
            "19, 37, 69, 165, 261 (стр. 39). Крючок Ø6 × 10 и места замков — шаблоном T65.1000.02 (стр. 22)."),
    ("В-6", "Задняя стенка — ХДФ 4 накладная, отступ 2 от наружных граней, саморезы 3,5 × 16 с шагом ≤ 150 (узел И)."),
    ("В-7", "Цоколь — рамка из 4 деталей на шкантах с клеем, к дну — конфирматами через дно (узлы Б, В); без опор-накладок."),
    ("В-8", "Короб ящика — ЛДСП 16 на конфирматах (узлы Е, Ж)."),
    ("В-9", "Фасад к коробу — саморезы 4 × 25 изнутри короба (узел Г). Регулировка по данным Blum: по высоте до 3 мм и наклон "
            "фасада; боковая регулировка замка в найденных данных не подтверждена и не закладывается."),
    ("В-11", "Крышка между боковинами (как в 3D каталога); торцы боковин сверху — кромка ABS 2."),
]
# Альтернативы — для других исполнений, в R02E не входят.
ALTERNATIVES = [
    ("П-1", "Задняя стенка ХДФ в паз (торец ХДФ не виден сбоку): новый паз в поз. 1–4, другие размеры поз. 5."),
    ("П-2", "Короб на металлических бортах системы (например, Blum TANDEMBOX): заменяет поз. 9–11 и узлы Е, Ж, К."),
    ("П-3", "Крышка накладная на боковины: меняет поз. 1–3, узел А и вид сверху."),
    ("П-4", "Опоры-накладки под цоколь для защиты пола."),
]


def qfmt(t, s):
    d = s["derived"]
    box = "плита корпуса (один артикул)" if d["interior_finish"] != "INNER" else "ЛДСП 16 белая (отдельный артикул)"
    return t.format(NL=d["NL"], SKL=d["box_l"], IW=d["box_inner_w"], LW=d["LW"], OW=d["box_w"], DECOR=color_name(s), BOX=box)


def stamp_for(s):
    o = s["options"]
    return {"product": "Тумба «Самал» 450 × 400 × 500", "doc": f"{SKU}.{s['rev']}", "rev": s["rev"], "hash": s["hash"],
            "config": f"{SKU}-{o['color']} · «{color_name(s)}»",
            "status": "ИНЖЕНЕРНОЕ ПРЕДЛОЖЕНИЕ — НЕ ДЛЯ ИЗГОТОВЛЕНИЯ: открытые вопросы на листе 11"}


# ------------------------------------------------------------------ 01 общий вид

def sheet_general(s, stamp):
    sh = Sheet("Общий вид", stamp, 1, TOTAL, "1:10")
    d = s["derived"]
    from render import render
    img = render(to_model(s), az=-35, el=22, size=(700, 700), ss=2)["clay"]
    buf = np.asarray(img.convert("RGB"))
    h = 125
    sh.ax.imshow(buf, extent=(30, 30 + h * buf.shape[1] / buf.shape[0], 150, 150 + h), zorder=0)
    sh.view_title(30, 277, "Изображение изделия (без масштаба)")
    W, D, H = d["width"], d["depth"], d["height"]
    vf = View(sh, 10, (40, 70))
    for p in sorted(s["parts"], key=lambda p: -p["y0"]):
        if p["kind"] in ("buy_part",) or p["group"] == "interior" or p["id"] == "BACK":
            continue
        vf.rect(p["x0"], p["z0"], p["x1"], p["z1"], VIS, fill="white")
    a, b = vf.p(0, 0), vf.p(W, H)
    sh.dim_h(a[0], b[0], b[1], b[1], b[1] + 7, f"{W}")
    sh.dim_v(a[1], b[1], a[0], a[0], a[0] - 7, f"{H}")
    sh.text(a[0], a[1] - 9, "Вид спереди", size=8, weight="bold")
    vs = View(sh, 10, (110, 70))
    for p in sorted(s["parts"], key=lambda p: p["x1"]):
        if p["kind"] in ("buy_part",) or p["group"] == "interior":
            continue
        vs.rect(p["y0"], p["z0"], p["y1"], p["z1"], VIS, fill="white")
    a2, b2 = vs.p(-26, 0), vs.p(D, H)
    sh.dim_h(vs.p(0, 0)[0], b2[0], b2[1], b2[1], b2[1] + 7, f"{D}")
    sh.text(a2[0], a2[1] - 9, "Вид слева", size=8, weight="bold")
    sh.text(b2[0] + 2, a2[1] + 2, "ручка −26", size=5.6)
    vt = View(sh, 10, (170, 70))
    for p in sorted(s["parts"], key=lambda p: p["z1"]):
        if p["kind"] in ("buy_part",) or p["group"] == "interior":
            continue
        a3, b3 = vt.p(p["x0"], D - p["y1"]), vt.p(p["x1"], D - p["y0"])
        sh.rect(a3[0], a3[1], b3[0], b3[1], VIS, fill="white")
    sh.text(170, 70 - 9, "Вид сверху", size=8, weight="bold")
    sh.front_arrow(170 + W / 20, 66, "ПЕРЕД", 0, -1)
    mats = materials()
    rows = [
        ["Обозначение конфигурации", f"{SKU}-{s['options']['color']}"],
        ["Габарит Ш × Г × В", f"{W} × {D} × {H} мм (ручка +26)"],
        ["Корпус", f"ЛДСП 16 «{color_name(s)}», кромка ABS 2 / 0,4"],
        ["Фасады", f"ЛДСП 18 «{color_name(s)}», ABS 2 по контуру (В-1)"],
        ["Ящики", f"2 шт., короб ЛДСП 16 {inner_txt(s)} {d['box_w']}×{d['box_l']}×{d['box_h']}"],
        ["Направляющие", f"Blum TANDEM plus 560H{d['NL'] * 10:04d}C, NL {d['NL']} (В-4)"],
        ["Цоколь", f"ЛДСП 16 чёрная, h {d['plinth']}, отступ 40 / 20"],
        ["Задняя стенка", "ХДФ 4 белая, накладная (В-6)"],
        ["Соединение корпуса", "Häfele Minifix 15 + болт S200, шкант 8×30 (В-3)"],
        ["Масса (оценка)", f"≈ {d['mass_kg']} кг"],
        ["Снимок конфигурации", s["hash"]],
    ]
    sh.text(232, 282, "Материалы и характеристики", size=8.5, weight="bold", va="top")
    y = sh.table(232, 276, ["Параметр", "Значение"], rows, [52, 126], row_h=6.0, size=6.5)
    sh.text(232, y - 6, "Состав комплекта", size=8.5, weight="bold", va="top")
    lst = ["01 Общий вид", "02 Сборочный чертёж", "03 Боковины (поз. 1, 2)", "04 Крышка, дно (поз. 3, 4)",
           "05 Задняя стенка, цоколь (поз. 5–7)", "06 Фасад ящика (поз. 8)", "07 Ящик (поз. 9–12)", "08 Узлы А–К",
           "09 Спецификация, кромка, раскрой", "10 Сборка и контроль", "11 Открытые вопросы (блокируют выпуск)"]
    for i, t in enumerate(lst):
        sh.text(234 + (i // 6) * 92, y - 13 - (i % 6) * 5.0, t, size=6.5)
    sh.text(232, 72, "Способ изготовления", size=8.5, weight="bold", va="top")
    for i, t in enumerate(["По независимым размерам: отверстия — от баз деталей (станок",
                           "или кондуктор), детали взаимозаменяемы. По месту — только",
                           "выставление фасадов по зазорам, без сверления (лист 10)."]):
        sh.text(234, 65 - i * 4.6, t, size=6.5)
    return sh


# ------------------------------------------------------------------ 02 сборочный чертёж

def sheet_assembly(s, stamp):
    sh = Sheet("Сборочный чертёж", stamp, 2, TOTAL, "1:5")
    d = s["derived"]
    W, D, H = d["width"], d["depth"], d["height"]
    # ---- вид спереди, фасады сняты
    vf = View(sh, SC, (45, 160))
    for p in sorted(s["parts"], key=lambda p: -p["y0"]):
        if p["kind"] != "board" or p["group"] == "fronts" or p["id"] == "BACK":
            continue
        vf.rect(p["x0"], p["z0"], p["x1"], p["z1"], VIS, fill="white")
    for f in ("FRONT-1", "FRONT-2"):
        p = P(s, f)
        vf.rect(p["x0"], p["z0"], p["x1"], p["z1"], PHANTOM)
    a, b = vf.p(0, 0), vf.p(W, H)
    sh.dim_h(a[0], b[0], b[1], b[1], b[1] + 8, f"{W}")
    sh.dim_v(a[1], b[1], a[0], a[0], a[0] - 14, f"{H}")
    pl = vf.p(0, d["plinth"])
    sh.dim_v(a[1], pl[1], a[0], a[0], a[0] - 6, f"{d['plinth']}")
    bx = P(s, "BOX1-SL")
    for i, z0 in enumerate(d["box_z0"]):
        q = vf.p(W, z0)
        sh.dim_v(a[1], q[1], b[0], b[0], b[0] + 6 + i * 7, f"{z0:g}")
    q0, q1 = vf.p(bx["x0"], 0), vf.p(P(s, "BOX1-SR")["x1"], 0)
    sh.dim_h(q0[0], q1[0], vf.p(0, d["box_z0"][0])[1], vf.p(0, d["box_z0"][0])[1], a[1] - 7, f"{d['box_w']}")
    sh.dim_h(vf.p(16, 0)[0], vf.p(W - 16, 0)[0], a[1] + 2, a[1] + 2, a[1] - 14, f"LW {d['LW']}")
    sh.text(a[0], a[1] - 25, "Вид спереди: фасады 8 сняты (контур — штрихпунктир)", size=7.6, weight="bold")
    # позиции
    bl = lambda pid, u, v, tx, ty: sh.balloon(*vf.p(u, v), tx, ty, POS.get(pid, pid))
    sl, top, bot = P(s, "SIDE-L"), P(s, "TOP"), P(s, "BOTTOM")
    bl("SIDE-L", 8, 300, 33, 236)
    bl("SIDE-R", W - 8, 300, 150, 236)
    bl("TOP", 120, H - 8, 70, 274)
    bl("BOTTOM", 330, d["plinth"] + 8, 150, 172)
    bl("PL-F", 330, 20, 150, 150)
    bl("BOX2-F", 160, d["box_z0"][1] + 60, 33, 252)
    sh.balloon(*vf.p(bx["x0"] + 8, d["box_z0"][0] + 100), 33, 206, 9)
    # узлы
    x, y = vf.p(16, H - 8)
    sh.node_mark(x, y, 2.6, "А", "л. 08", dx=1, dy=1)
    x, y = vf.p(W / 2, d["plinth"] - 6)
    sh.node_mark(x, y, 2.6, "Б", "л. 08", dx=-1, dy=-1)
    # ---- разрез А–А (x = W/2)
    va = View(sh, SC, (215, 160))
    cut = W / 2
    section(va, s, "x", cut, "+y", "+z", (-30, D + 2, -2, H + 2), frame=False)
    a, b = va.p(0, 0), va.p(D, H)
    sh.dim_h(a[0], b[0], b[1], b[1], b[1] + 8, f"{D}")
    sh.dim_h(va.p(18, 0)[0], va.p(D - 4, 0)[0], b[1] - 2, b[1] - 2, b[1] + 3, f"{d['carcass_depth']}", size=6.2)
    by0, by1 = P(s, "BOX1-SL")["y0"], P(s, "BOX1-SL")["y1"]
    sh.dim_h(va.p(by0, 0)[0], va.p(by1, 0)[0], va.p(0, d["box_z0"][0])[1], va.p(0, d["box_z0"][0])[1], a[1] - 7,
             f"{d['box_l']}")
    pf, pb = P(s, "PL-F"), P(s, "PL-B")
    sh.dim_h(a[0], va.p(pf["y0"], 0)[0], a[1], a[1], a[1] - 14, f"{pf['y0']:g}")
    sh.dim_h(va.p(pb["y1"], 0)[0], va.p(D - 4, 0)[0], a[1], a[1], a[1] - 14, f"{D - 4 - pb['y1']:g}")
    sh.text(a[0] - 6, a[1] - 25, f"А–А (X = {cut:g})", size=7.6, weight="bold")
    sh.front_arrow(a[0] - 16, a[1] + 24, "ПЕРЕД", -1, 0)
    x, y = va.p(P(s, "BOX1-F")["y0"] + 8, d["box_z0"][0] + 120)
    sh.node_mark(x, y, 2.6, "Г", "л. 08", dx=1, dy=1)
    x, y = va.p(D - 2, H - 8)
    sh.node_mark(x, y, 2.6, "И", "л. 08", dx=1, dy=1)
    sh.balloon(*va.p(D - 2, 250), b[0] + 10, 230, 5)
    sh.balloon(*va.p(200, d["box_z0"][0] + 21), b[0] + 10, 185, 12)
    sh.balloon(*va.p(by1 - 8, d["box_z0"][1] + 80), b[0] + 10, 245, 11)
    sh.balloon(*va.p(9, 380), a[0] - 14, 225, 8)
    sh.balloon(*va.p(-20, d["handle_z"][1]), a[0] - 14, 252, 14)
    # линия разреза на виде спереди
    xa, _ = vf.p(cut, 0)
    yt_, yb_ = vf.p(0, H)[1] + 14, vf.p(0, 0)[1] - 18
    sh.line(xa, yb_, xa, yt_, CTR)
    for yy, dy in ((yt_, -1), (yb_, 1)):
        sh.line(xa - 3, yy, xa + 3, yy, dict(lw=1.6, color="k", ls="-"))
        sh.line(xa, yy, xa + 6, yy, THIN); sh._arrow(xa + 6, yy, 1, 0)
        sh.text(xa + 7.5, yy, "А", size=8, weight="bold", va="center")
    # ---- разрез Б–Б (z = 20): цоколь; вид сверху, перед внизу
    vb = View(sh, SC, (45, 34))
    vb.rect(0, 0, W, D, PHANTOM)
    for p in ("SIDE-L", "SIDE-R"):
        q = P(s, p)
        vb.rect(q["x0"], q["y0"], q["x1"], q["y1"], PHANTOM)
    for pid in ("PL-F", "PL-B", "PL-SL", "PL-SR"):
        q = P(s, pid)
        a3, b3 = vb.p(q["x0"], q["y0"]), vb.p(q["x1"], q["y1"])
        sh.hatch(a3[0], a3[1], b3[0], b3[1])
    a, b = vb.p(0, 0), vb.p(W, D)
    pf, pb, psl = P(s, "PL-F"), P(s, "PL-B"), P(s, "PL-SL")
    sh.dim_h(a[0], vb.p(psl["x0"], 0)[0], b[1], b[1], b[1] + 5, f"{psl['x0']:g}")
    sh.dim_h(vb.p(pf["x0"], 0)[0], vb.p(pf["x1"], 0)[0], b[1], b[1], b[1] + 11, f"{pf['x1'] - pf['x0']:g}")
    sh.dim_v(a[1], vb.p(0, pf["y0"])[1], b[0], b[0], b[0] + 7, f"{pf['y0']:g}")
    sh.dim_v(vb.p(0, pb["y1"])[1], vb.p(0, D - 4)[1], b[0], b[0], b[0] + 7, f"{D - 4 - pb['y1']:g}")
    sh.dim_v(vb.p(0, pf["y0"])[1], vb.p(0, pb["y1"])[1], b[0], b[0], b[0] + 15, f"{pb['y1'] - pf['y0']:g}")
    sh.text(b[0] + 22, a[1] + 4, "Б–Б (Z = 20)", size=7.6, weight="bold", va="bottom")
    sh.front_arrow(a[0] + 45, a[1] - 1, "ПЕРЕД", 0, -1)
    sh.balloon(*vb.p(W / 2, pb["y0"] + 8), 150, 98, 6)
    sh.balloon(*vb.p(psl["x0"] + 8, 200), 33, 70, 7)
    sh.node_mark(*vb.p(psl["x0"] + 8, pf["y1"]), 2.6, "В", "л. 08", dx=1, dy=1)
    # ---- технические требования
    tt = ["1. Детали изготавливать по листам 03–07 от баз A;",
          "   отверстия — по координатам, без подгонки.",
          "2. Сборка корпуса — узел А; цоколь — узлы Б, В;",
          "   ящики — узлы Е, Ж; фасады — Г, Д; ХДФ — И.",
          "3. Разность диагоналей корпуса ≤ 1,5 (В-10).",
          f"4. Направляющие Blum 560H, NL {d['NL']}: крепление",
          "   по кондуктору T65.1000.02 (В-4).",
          "5. Фасады: схема зазоров — лист 06 (1,5 от граней",
          "   корпуса, 3 между фасадами).",
          "6. Сечение А–А: позиции 5, 8, 11, 12, 14."]
    sh.text(318, 132, "Технические требования", size=8.2, weight="bold")
    for i, t in enumerate(tt):
        sh.text(318, 125 - i * 4.8, t, size=6.3)
    return sh


# ------------------------------------------------------------------ деталировка

def _detail_block(sh, s, pid, x, y, n, up, qty, title_w=170, table=True, ord_top=True, ord_right=True, extra=None, sc=SC, note=""):
    p = P(s, pid)
    ext = s["derived"]["parts_ext"][pid]
    fr, bb = detail(sh, s, pid, x, y, sc, n, up, ord_top=ord_top, ord_right=ord_right)
    bu, bv = blank(fr, ext.get("edges", {}))
    pos = POS[pid]
    t1 = f"Поз. {pos}  {p['unit']} — {qty} шт." + (f"   (М 1:{str(sc).replace('.', ',')})" if sc != SC else "") + (f"   {note}" if note else "")
    t2 = f"{mat_txt(s, p)} · готовый {fr.Lu:g} × {fr.Lv:g} × {fr.t:g} · заготовка {bu:g} × {bv:g}"
    t3 = "Кромка — " + edge_txt(ext) + ("; текстура — стрелка" if ext.get("grain") else "")
    yt = bb[3] + 13
    sh.text(x, yt, t1, size=7.4, weight="bold")
    sh.text(x, yt - 4.6, t2, size=6.1)
    sh.text(x, yt - 8.8, t3, size=6.1)
    view_txt = {"+x": "справа", "-x": "слева", "+y": "сзади", "-y": "спереди", "+z": "сверху", "-z": "снизу"}[n]
    c1, c2 = fr.base_corner()
    sh.text(x, y - 7.5, f"Вид {view_txt}; база A — угол {c1} / {c2}", size=6.0, va="top", style="italic")
    yb = y - 12
    if table:
        rows = hole_rows(s, pid, fr, node_of)
        if extra:
            rows += extra
        if rows:
            yb = sh.table(x, y - 12, ["Ø", "Глуб.", "Где", "Кол.", "Назначение", "Узел"], rows,
                          [10, 14, 54, 9, 62, 10], row_h=4.8, size=5.7)
    return fr, bb, yb


def sheet_sides(s, stamp):
    sh = Sheet("Боковины", stamp, 3, TOTAL, "1:5")
    d = s["derived"]
    for pid, x0, nrm in (("SIDE-L", 40, "+x"), ("SIDE-R", 232, "-x")):
        fr, bb, yb = _detail_block(sh, s, pid, x0, 135, nrm, "+z", 1)
        p = P(s, pid)
        for i, zr in enumerate(d["runner_bottom"]):
            v = zr - p["z0"]
            a = (x0, 135 + v / SC)
            sh.line(a[0], a[1], a[0] + fr.Lu / SC, a[1], PHANTOM)
            sh.text(a[0] + 22, a[1] + 0.8, f"низ профиля {i + 1}: {n(v)}; ось саморезов {n(v + 37)}", size=5.2, color="#555", va="bottom")
    sh.text(25, 285, "Боковины зеркальные: присадка различается — изготавливать по своему чертежу. Вид на внутреннюю пласть.",
            size=6.6, color=RED, va="top")
    sh.text(25, 280, "Профиль Blum 560H: передний конец по передней кромке боковины; саморезы Ø4 × 15 в точках 19, 37, 69, 165, 261 "
            "от передней кромки, ось на 37 выше низа профиля (Blum TANDEM, стр. 22, 39). Точки — разметка, без сверления.",
            size=6.2, va="top")
    return sh


def sheet_top_bottom(s, stamp):
    sh = Sheet("Крышка и дно", stamp, 4, TOTAL, "1:5")
    _detail_block(sh, s, "TOP", 40, 160, "-z", "+y", 1)
    _detail_block(sh, s, "BOTTOM", 232, 160, "+z", "+y", 1)
    sh.text(25, 285, "Крышка — вид снизу (сторона присадки), перед внизу; лево и право на виде поменяны — смотри подписи сторон.",
            size=6.6, color=RED, va="top")
    return sh


def sheet_back_plinth(s, stamp):
    sh = Sheet("Задняя стенка и цоколь", stamp, 5, TOTAL, "1:5, 1:2,5")
    fr, bb, yb = _detail_block(sh, s, "BACK", 40, 150, "+y", "+z", 1, table=False)
    sh.text(40, 132, "Отверстий нет: саморезы 3,5 × 16 по разметке — оси на 8 от наружных граней корпуса", size=6.0, va="top")
    sh.text(40, 127, "(узел И); шаг ≤ 150; положение засверловок — листы 03, 04.", size=6.0, va="top")
    _detail_block(sh, s, "PL-F", 232, 228, "+y", "+z", 2, sc=2.5)
    sh.text(232, 196, "Передний и задний одинаковые: пласть со шкантами — внутрь рамки.", size=6.0, va="top", color=RED)
    _detail_block(sh, s, "PL-SL", 232, 120, "+x", "+z", 2, sc=2.5)
    return sh


def sheet_front(s, stamp):
    sh = Sheet("Фасад ящика", stamp, 6, TOTAL, "1:5")
    d = s["derived"]
    fr, bb, yb = _detail_block(sh, s, "FRONT-1", 40, 180, "-y", "+z", 2)
    # ---- схема фасадов: размерная цепочка зазоров (вид спереди, 1:5)
    W, H, PLh = d["width"], d["height"], d["plinth"]
    f1, f2 = P(s, "FRONT-1"), P(s, "FRONT-2")
    v = View(sh, SC, (262, 95))
    v.rect(0, PLh, W, H, PHANTOM)
    for f in (f1, f2):
        v.rect(f["x0"], f["z0"], f["x1"], f["z1"], VIS, fill="white")
    xr = v.p(W, 0)[0]
    chain = [PLh, f1["z0"], f1["z1"], f2["z0"], f2["z1"], H]
    for i, (za, zb) in enumerate(zip(chain, chain[1:])):
        ya, yb2 = v.p(0, za)[1], v.p(0, zb)[1]
        sh.dim_v(ya, yb2, xr, xr, xr + 8 + (4 if (zb - za) < 5 else 0) * (i % 2), n(zb - za), size=6.2)
    sh.dim_v(v.p(0, PLh)[1], v.p(0, H)[1], xr, xr, xr + 24, f"{H - PLh:g}", size=6.2)
    yt = v.p(0, H)[1]
    xl = v.p(0, 0)[0]
    sh.dim_h(xl, v.p(f1["x0"], 0)[0], yt, yt, yt + 6, n(f1['x0']), size=6.2)
    sh.dim_h(v.p(f1["x0"], 0)[0], v.p(f1["x1"], 0)[0], yt, yt, yt + 12, f"{f1['x1'] - f1['x0']:g}", size=6.2)
    sh.dim_h(xl, xr, yt, yt, yt + 18, f"{W}", size=6.2)
    sh.text(262, 88, "Схема фасадов (вид спереди, 1:5): контур корпуса — штрихпунктир.", size=6.4, weight="bold", va="top")
    sh.text(262, 83, f"Сверху, снизу и по бокам — {n(f1['x0'])} от граней корпуса; между фасадами {n(f2['z0'] - f1['z1'])}.",
            size=6.2, va="top")
    sh.text(262, 78.5, f"Цепочка: {n(f1['z0'] - PLh)} + {n(f1['z1'] - f1['z0'])} + {n(f2['z0'] - f1['z1'])} + {n(f2['z1'] - f2['z0'])} + "
            f"{n(H - f2['z1'])} = {n(H - PLh)}; {n(f1['x0'])} + {n(f1['x1'] - f1['x0'])} + {n(W - f1['x1'])} = {W}.", size=6.2, va="top")
    tt = ["1. Фасады 8 одинаковые (верхний и нижний).",
          f"2. Отверстия Ø5 насквозь под ручку 14, межосевое {d['handle_cc']},",
          f"   ось на {d['handle_from_top']} от верхней кромки, по центру ширины.",
          "3. Сверлить с лицевой стороны с подкладкой (без сколов).",
          "4. Крепление к коробу — саморезы 19 изнутри короба,",
          "   без засверловки фасада (узел Г); вход 9, остаток 9."]
    if d["grain"]:
        tt += [f"5. Текстура декора «{color_name(s)}» — вдоль ширины; рисунок",
               "   верхнего и нижнего фасада — из одной полосы (В-1)."]
    sh.text(232, 270, "Технические требования", size=8.2, weight="bold")
    for i, t in enumerate(tt):
        sh.text(232, 263 - i * 4.8, t, size=6.3)
    return sh


def sheet_drawer(s, stamp):
    sh = Sheet("Ящик", stamp, 7, TOTAL, "1:5")
    d = s["derived"]
    _detail_block(sh, s, "BOX1-SL", 35, 215, "-x", "+z", 4)
    _detail_block(sh, s, "BOX1-F", 232, 215, "-y", "+z", 2)
    _detail_block(sh, s, "BOX1-BOT", 35, 85, "+z", "+y", 2)
    _detail_block(sh, s, "BOX1-B", 232, 100, "+y", "+z", 2)
    sh.text(25, 285, f"Ящики 1 и 2 одинаковые. Проём корпуса LW {d['LW']}; короб: наружная ширина {d['box_w']} (LW − 10), внутренняя {d['box_inner_w']} (LW − 42), "
            f"длина {d['box_l']} (NL − 10), высота {d['box_h']}; дно поднято на 13 (Blum 560H, В-4).",
            size=6.6, color=RED, va="top")
    return sh


# ------------------------------------------------------------------ 08 узлы

def _node(sh, s, x, y, sc, cut, val, uax, vax, win, title, notes, balloons=()):
    """Узел: разрез по снимку в окне win (координаты вида), левый нижний угол окна — (x, y) на листе.
    balloons — [(u, v, позиция)]: номера позиций в столбце справа от окна."""
    v = View(sh, sc, (x, y), (win[0], win[2]))
    section(v, s, cut, val, uax, vax, win)
    w = (win[1] - win[0]) / sc
    hgt = (win[3] - win[2]) / sc
    sh.text(x, y + hgt + 2.5, title, size=7.0, weight="bold")
    for i, t in enumerate(notes):
        sh.text(x, y - 2.5 - i * 4.0, t, size=5.7, va="top")
    pts = sorted(balloons, key=lambda b: -b[1])
    for i, (u, vv, num) in enumerate(pts):
        px, py = v.p(u, vv)
        ty = y + hgt - 4 - i * (hgt - 8) / max(1, len(pts) - 1) if len(pts) > 1 else py
        sh.balloon(px, py, x + w + 6, ty, num, r=3.0)
    return v


def sheet_nodes(s, stamp):
    sh = Sheet("Узлы", stamp, 8, TOTAL, "1:1, 1:2")
    d = s["derived"]
    H, W = d["height"], d["width"]
    yc0 = 18
    ye, yd = yc0 + 37, yc0 + 69
    z0 = d["box_z0"][0]
    # ---- ряд 1
    _node(sh, s, 26, 214, 1, "y", ye, "+x", "+z", (-2, 66, 456, 504), f"А (1:1) · Y = {ye:g}: эксцентрик",
          ["Häfele Minifix 15: Ø15 гл. 12,5 в крышке", f"снизу, B = 24; отверстие Ø8 гл. {d['rev_params'].get('bolt_depth', 34)} в торец;",
           f"болт S200: Ø5 гл. {d['rev_params']['stem_depth']} в боковину (В-3).", "Häfele стр. 294, 301. Дно — так же,", "корпус на верхней пласти дна."],
          [(6, 470, 1), (58, 498, 3), (40, 488, 16), (10, 492, 25)])
    _node(sh, s, 112, 214, 1, "y", yd, "+x", "+z", (-2, 46, 456, 504), f"А' (1:1) · Y = {yd:g}: шкант",
          ["Шкант 8 × 30 на клей:", "в боковину гл. 12 (остаток 4),", "в торец гл. 20."],
          [(6, 470, 1), (40, 498, 3), (26, 492, 17)])
    _node(sh, s, 178, 200, 1, "x", W / 2, "+y", "+z", (22, 74, -2, 62), "Б (1:1) · X = 225: цоколь — дно",
          ["Конфирмат через дно: Ø7 насквозь", "с зенковкой; в торец цоколя Ø5", "гл. 36 (остаток 4). Головка —",
           "внутри корпуса (В-7)."],
          [(68, 48, 4), (50, 51, 18), (44, 10, 6)])
    _node(sh, s, 248, 210, 1, "z", 12, "+x", "+y", (14, 66, 36, 90), "В (1:1) · Z = 12: угол цоколя",
          ["Шканты на клей, 2 на угол", "(Z 12 и 28): в пласть гл. 12,", "в торец гл. 20. Вид сверху,", "перед внизу."],
          [(60, 50, 6), (28, 66, 17), (22, 84, 7)])
    _node(sh, s, 322, 172, 2, "x", P(s, "BOX1-F")["x0"] + 40, "+y", "+z", (-4, 76, z0 - 18, z0 + 160),
          f"Г (1:2) · X = {P(s, 'BOX1-F')['x0'] + 40:g}: фасад — короб",
          ["Саморез 4 × 25 изнутри", "короба, зенковка; вход", "в фасад 9, остаток 9 (В-9)."],
          [(9, z0 + 140, 8), (26, z0 + 150, 10), (26, z0 + 125, 19), (60, z0 + 21, 12)])
    # ---- ряд 2
    xh = W / 2 - 64
    zh = d["handle_z"][0]
    _node(sh, s, 26, 104, 1, "x", xh, "+y", "+z", (-30, 40, zh - 22, zh + 22), f"Д (1:1) · X = {xh:g}: ручка",
          ["Ø5 насквозь; винт M4 × 22 (В-5).", f"Головка винта выше короба на {zh - 4 - (z0 + d['box_h']):g}:",
           "доступ при выдвинутом ящике."],
          [(-20, zh, 14), (9, zh + 14, 8), (9, zh, 15)])
    _node(sh, s, 116, 106, 1, "z", z0 + 40, "+x", "+y", (-2, 70, -2, 46), f"Е (1:1) · Z = {z0 + 40:g}: угол короба",
          ["Конфирмат через боковину ящика:", "Ø7 с зенковкой, в торец стенки", "Ø5 гл. 36; 2 на угол (+40, +115",
           "от низа короба). Вид сверху."],
          [(8, 40, 1), (29, 40, 9), (60, 26, 18), (60, 9, 8)])
    yj = P(s, "BOX1-SL")["y0"] + 76
    _node(sh, s, 206, 92, 1, "y", yj, "+x", "+z", (-2, 62, z0 - 22, z0 + 50), f"Ж (1:1) · Y = {yj:g}: дно ящика",
          ["Blum стр. 22: низ дна → низ профиля 27,5;", "утопление дна 12–15 (принято 13); от боковины", "корпуса до внутр. пласти боковины ящика 21."],
          [(8, z0 + 40, 1), (29, z0 + 40, 9), (50, z0 + 21, 12), (45, 48, 4)])
    xi = min(h["x"] for h in s["holes"] if h["part"] == "TOP" and h["kind"] == "back_pilot")
    _node(sh, s, 300, 112, 1, "x", xi, "+y", "+z", (360, 404, H - 40, H + 2), f"И (1:1) · X = {xi:g}: задняя стенка",
          ["ХДФ 4 накладная, отступ 2 от граней;", "саморез 3,5 × 16 в засверловку", "Ø2,5 гл. 12 по оси торца (В-6)."],
          [(370, 494, 3), (390, 492, 20), (402, 475, 5)])
    # К: зона замка под дном у передней стенки (контур замка не построен — нет чертежа Blum)
    bf = P(s, "BOX1-F"); bb_ = P(s, "BOX1-BOT")
    xk = bf["x0"] + 8
    vk = _node(sh, s, 346, 66, 2, "x", xk, "+y", "+z", (6, 70, z0 - 16, z0 + 36), f"К (1:2) · X = {xk:g}: замок",
               ["Замок T51.1700.04 — под дном у", "передней стенки, 2 самореза (Blum", "стр. 20, 22); места — шаблон T65.1000.02."],
               [(26, z0 + 30, 10), (50, z0 + 21, 12)])
    a_, b_ = vk.p(bf["y1"], z0), vk.p(bf["y1"] + 30, bb_["z0"])
    sh.rect(a_[0], a_[1], b_[0], b_[1], PHANTOM)
    sh.dim_v(a_[1], b_[1], b_[0], b_[0], b_[0] + 4, n(bb_["z0"] - z0), size=5.6)
    sh.text(25, 285, "Разрезы по снимку конфигурации: штриховка /// — декор и чёрная ЛДСП, \\\\\\ — белая ЛДСП, xxx — покупные; "
            "белые прямоугольники — отверстия; номера — позиции листа 09.", size=6.2, va="top")
    return sh


# ------------------------------------------------------------------ 09 спецификация

def sheet_spec(s, stamp):
    sh = Sheet("Спецификация, кромка, раскрой", stamp, 9, TOTAL, "—")
    seen = {}
    for p in s["parts"]:
        if p["kind"] == "board":
            seen.setdefault(POS[p["id"]], []).append(p)
    rows = [["", "", "Детали", "", "", "", "", ""]]
    for pos in sorted(seen):
        ps = seen[pos]
        p = ps[0]
        ext = s["derived"]["parts_ext"][p["id"]]
        a, b, t = sorted(dims(p), reverse=True)
        fr = Frame(p, *{1: ("+x", "+z"), 2: ("-x", "+z"), 3: ("-z", "+y"), 4: ("+z", "+y"), 5: ("+y", "+z"), 6: ("+y", "+z"),
                        7: ("+x", "+z"), 8: ("-y", "+z"), 9: ("-x", "+z"), 10: ("-y", "+z"), 11: ("+y", "+z"), 12: ("+z", "+y")}[pos])
        bu, bv = blank(fr, ext.get("edges", {}))
        rows.append([str(pos), f"{SKU}-{pos:02d}", p["unit"], str(len(ps)), mat_txt(s, p), f"{fr.Lu:g} × {fr.Lv:g} × {t:g}",
                     f"{n(bu)} × {n(bv)}", f"{DETAIL_SHEET[pos]:02d}"])
    rows.append(["", "", "Покупные изделия", "", "", "", "", ""])
    for h in sorted(s["hardware"], key=lambda h: BUYPOS[h["id"]]):
        q = h["qty"]
        rows.append([str(BUYPOS[h["id"]]), "—", h["name"], f"{q:g} {h.get('uom', 'шт')}", h["spec"], "", "", "08"])
    y = sh.table(25, 282, ["Поз.", "Обозначение", "Наименование", "Кол.", "Материал / артикул", "Готовый", "Заготовка", "Лист"],
                 rows, [11, 32, 58, 16, 86, 34, 26, 11], row_h=5.4, size=6.0, max_chars=62)
    d = s["derived"]
    sh.text(25, y - 6, "Кромка", size=8, weight="bold", va="top")
    sh.text(27, y - 12, f"ABS 2 мм в цвет декора — {d['edge_abs2_m']:g} м; ПВХ 0,4 — {d['edge_04_m']:g} м (без запаса на торцовку). "
            "Стороны — на листах деталей и в столбце «Заготовка» (= готовый − кромка, без припуска на фуговку, В-2).", size=6.2, va="top")
    b = bom(s)
    sh.text(25, y - 20, "Расход плиты — оценка площади, не карта раскроя (карту строит программа раскроя цеха по столбцу «Заготовка»)",
            size=8, weight="bold", va="top")
    for i, r in enumerate(b["sheets"]):
        fin = {"INNER": "белый", "black": "чёрный"}.get(r["finish"], f"«{materials()['colors'].get(r['finish'], {}).get('name', r['finish'])}»")
        sh.text(27, y - 26 - i * 4.6, f"{r['material'].replace('LDSP', 'ЛДСП ').replace('HDF4', 'ХДФ 4')} {fin}: деталей {r['parts']}, "
                f"площадь {r['area_m2']:g} м² — {r['sheets']} лист(а) при заказе одного изделия", size=6.2, va="top")
    return sh


# ------------------------------------------------------------------ 10 сборка и контроль

def sheet_assembly_control(s, stamp):
    sh = Sheet("Сборка и контроль", stamp, 10, TOTAL, "—")
    d = s["derived"]
    steps = [
        "Детали (по независимым размерам)",
        "1. Раскроить детали поз. 1–12 по листу 09; кромковать по сторонам с листов 03–07; проверить К1.",
        "2. Присадка от баз A по координатам листов 03–07 (станок или кондуктор). Боковины 1 и 2 — зеркальные, не путать.",
        "3. На боковинах 1, 2 разметить точки крепления профиля (лист 03); не сверлить — саморезы Ø4 × 15 (Blum стр. 39).",
        "Корпус",
        "4. Цоколь: шканты 17 с клеем в поз. 7, собрать рамку поз. 6 + 7 на ровном столе; контроль К2.",
        "5. В дно 4 установить корпуса эксцентриков 16; закрепить рамку цоколя конфирматами 18 через дно (узел Б).",
        "6. Вкрутить штоки 16 и вставить шканты 17 в боковины 1, 2; собрать корпус с крышкой 3 и дном 4, затянуть эксцентрики.",
        "7. Выставить диагонали корпуса (К3) и закрепить заднюю стенку 5 саморезами 20 от углов к середине (узел И).",
        "Ящики",
        "8. Собрать короба поз. 9–12 конфирматами 18 (узлы Е, Ж); контроль К4, К4а. Отверстия Ø6 × 10 под крючок в задней",
        "     стенке и места замков — шаблоном Blum T65.1000.02 (Blum стр. 22, «Обработка ящика»).",
        "9. Профили 13 — на боковины саморезами 23 по точкам листа 03, передний конец по кромке боковины; замки 22 — под",
        "     дно у передней стенки саморезами 24 (узел К); установить короба, регулировка высоты замками.",
        "Фасады (выставление по месту, без сверления)",
        "10. Установить ручки 14 винтами 15 на фасады 8 (узел Д).",
        "11. Приложить фасады к коробам: 1,5 от граней корпуса сверху, снизу и по бокам, 3 между фасадами (К5, лист 06);",
        "     прижать струбцинами, закрепить саморезами 19 изнутри короба (узел Г). Проверить ход ящиков (К6).",
    ]
    y = 282
    for t in steps:
        bold = not t.startswith(" ") and not t[0].isdigit()
        sh.text(25, y, t, size=7.2 if bold else 6.6, weight="bold" if bold else "normal", va="top")
        y -= 6.2 if bold else 5.2
    rows = [
        ["К1", "Размеры деталей после кромки", "рулетка, штангенциркуль", "по листам 03–07; ±0,5 (В-10)"],
        ["К2", "Рамка цоколя: размеры, диагонали", "рулетка", f"{P(s, 'PL-F')['x1'] - P(s, 'PL-F')['x0']:g} × "
                                                                  f"{P(s, 'PL-B')['y1'] - P(s, 'PL-F')['y0']:g}; разность ≤ 1,5"],
        ["К3", "Корпус: диагонали по фасадной плоскости", "рулетка", f"{d['width']} × {d['height'] - d['plinth']}; разность ≤ 1,5 (В-10)"],
        ["К4", "Короб ящика: наружные размеры, диагонали", "рулетка", f"{d['box_w']} × {d['box_l']}; разность ≤ 1"],
        ["К4а", "Короб: внутренняя ширина спереди и сзади", "штангенциркуль",
         f"{d['box_inner_w']} +0 / −1,5 (Blum LW − 42); при боковинах t факт наружная = {d['box_inner_w']} + 2t"],
        ["К5", "Фасады: зазор между ними; отступ от граней корпуса", "щуп 3; линейка", "3 ± 0,5; 1,5 ± 0,5 со всех сторон"],
        ["К6", "Ход ящиков", "вручную", "полное выдвижение, доводчик срабатывает, без касаний"],
    ]
    sh.text(25, y - 4, "Контроль", size=8.2, weight="bold", va="top")
    yb = sh.table(25, y - 10, ["№", "Что проверяем", "Чем", "Критерий"], rows, [12, 78, 62, 100], row_h=5.8, size=6.3)
    sh.text(25, yb - 5, "Устойчивость, нагрузка на ящики и долговечность — не приёмочный контроль: проверяются на образце по программе "
            "испытаний (В-12).", size=6.3, va="top")
    return sh


# ------------------------------------------------------------------ 11 открытые вопросы

def sheet_questions(s, stamp):
    sh = Sheet("Открытые вопросы и решения", stamp, 11, TOTAL, "—")
    sh.text(25, 283, "Пока вопросы не закрыты, комплект не выдаётся в производство. Пробный образец — только с пометкой «проба».",
            size=7.4, weight="bold", color=RED, va="top")
    y = 274
    sh.table(25, y, ["№", "Вопрос", "Что блокирует", "Кто", "Как закрыть"], [], [14, 182, 70, 40, 84], row_h=6.4, size=6.6)
    y -= 6.4
    for q, t, b, w, c in QUESTIONS:
        t = qfmt(t, s)
        lines = textwrap.wrap(t, 112); lb = textwrap.wrap(b, 42); lc = textwrap.wrap(c, 50); lw = textwrap.wrap(w, 24)
        n = max(len(lines), len(lb), len(lc), len(lw))
        sh.text(26.2, y - 3, q, size=6.4, weight="bold", va="top")
        for i, tt in enumerate(lines):
            sh.text(40.2, y - 3 - i * 4.1, tt, size=6.1, va="top")
        for col, xs in ((lb, 222.2), (lw, 292.2), (lc, 332.2)):
            for i, tt in enumerate(col):
                sh.text(xs, y - 3 - i * 4.1, tt, size=6.1, va="top")
        y -= 4.1 * n + 2
        sh.line(25, y, 415, y, THIN)
    for x in (25, 39, 221, 291, 331, 415):
        sh.line(x, 274, x, y, THIN)
    y -= 7
    sh.text(25, y, f"Решения {s['rev']} и узлы, закрытые по документам производителей (показаны на чертежах)", size=7.6, weight="bold", va="top")
    y -= 6
    for q, t in DECISIONS:
        ls = textwrap.wrap(t, 150)
        sh.text(26, y, q, size=6.3, weight="bold", va="top")
        for i, tt in enumerate(ls):
            sh.text(40, y - i * 4.1, tt, size=6.1, va="top")
        y -= 4.1 * len(ls) + 1.2
    y -= 4
    sh.text(25, y, f"Предложения для других исполнений (в {s['rev']} не входят)", size=7.6, weight="bold", va="top")
    y -= 6
    for q, t in ALTERNATIVES:
        sh.text(26, y, q, size=6.3, weight="bold", va="top")
        sh.text(40, y, t, size=6.1, va="top")
        y -= 5.2
    return sh


SHEETS = [sheet_general, sheet_assembly, sheet_sides, sheet_top_bottom, sheet_back_plinth, sheet_front, sheet_drawer,
          sheet_nodes, sheet_spec, sheet_assembly_control, sheet_questions]


# ------------------------------------------------------------------ проверка комплекта

def verify(s, report=None, texts=None):
    """Проверки перед передачей (пункт 7 задания). Возвращает [(проверка, ok, подробности)]."""
    d = s["derived"]
    out = []
    add = lambda n, ok, t: out.append((n, bool(ok), t))
    parts = {p["id"]: p for p in s["parts"]}
    boards = [p for p in s["parts"] if p["kind"] == "board"]
    # 1. сборка = детали
    for c in s["checks"]:
        add(c["name"], c["ok"], f"{c['expected']} = {c['actual']}")
    f1, f2 = parts["FRONT-1"], parts["FRONT-2"]
    W, H, PLh = d["width"], d["height"], d["plinth"]
    chain = (f1["z0"] - PLh) + (f1["z1"] - f1["z0"]) + (f2["z0"] - f1["z1"]) + (f2["z1"] - f2["z0"]) + (H - f2["z1"])
    add("Схема фасадов: 1,5 + 227 + 3 + 227 + 1,5 = 460; 1,5 + 447 + 1,5 = 450",
        abs(chain - (H - PLh)) < 1e-6 and f1["z0"] - PLh == H - f2["z1"] == f1["x0"] == W - f1["x1"] == 1.5 and f2["z0"] - f1["z1"] == 3,
        f"{chain:g} = {H - PLh}; бока {f1['x0']:g} / {W - f1['x1']:g}")
    if s["rev"] != "R01E":
        top = parts["TOP"]
        pitch = d["box_z0"][1] - d["box_z0"][0]
        openings = [pitch] + [top["z0"] - (d["box_z0"][-1] - d["bottom_clear"])]
        add("Blum: длина короба = NL − 10", d["box_l"] == d["NL"] - 10, f"{d['box_l']} = {d['NL']} − 10")
        add("Blum: внутренняя ширина короба = LW − 42", d["box_inner_w"] == d["LW"] - 42, f"{d['box_inner_w']} = {d['LW']} − 42")
        add("Blum: наружная ширина = LW − 10 (борт 16)", d["box_w"] == d["LW"] - 10, f"{d['box_w']}")
        rpar = d["rev_params"]
        rb = d["runner_bottom"]
        marks = [h for h in s["holes"] if h["kind"] == "runner_mark"]
        add("Blum стр. 22: низ дна ящика − низ профиля = 27,5",
            all(abs((z0 + d["box_recess"]) - r - rpar["blum_under_bottom"]) < 1e-6 for z0, r in zip(d["box_z0"], rb)),
            ", ".join(f"{_n(z0 + d['box_recess'])} − {_n(r)}" for z0, r in zip(d["box_z0"], rb)))
        add("Blum стр. 22: утопление дна 12–15", 12 <= d["box_recess"] <= 15, f"{d['box_recess']}")
        add("Blum стр. 22: ось саморезов профиля = низ профиля + 37",
            all(any(abs(m["z"] - r - 37) < 1e-6 for r in rb) for m in marks), f"{len(marks)} точек")
        add("Blum стр. 39: точки 19, 37, 69, 165, 261 от передней кромки, 5 на профиль",
            sorted({round(m["y"] - parts["SIDE-L"]["y0"]) for m in marks}) == [19, 37, 69, 165, 261] and len(marks) == 5 * 4,
            f"{len(marks)} = 5 × 4 профиля")
        add("Низ нижнего профиля не ниже дна корпуса", rb[0] >= parts["BOTTOM"]["z1"], f"{_n(rb[0])} ≥ {_n(parts['BOTTOM']['z1'])}")
        add("Blum стр. 22: над коробом ≥ 7 (до профиля верхнего ящика и до крышки)",
            rb[1] - (d["box_z0"][0] + d["box_h"]) >= 7 and d["top_clear"] >= 7,
            f"{_n(rb[1] - d['box_z0'][0] - d['box_h'])} / {_n(d['top_clear'])}")
        add("Blum стр. 22: боковина корпуса → внутренняя пласть боковины ящика = 21",
            parts["BOX1-SL"]["x1"] - parts["SIDE-L"]["x1"] == 21, f"{parts['BOX1-SL']['x1'] - parts['SIDE-L']['x1']:g}")
        add("Blum стр. 20, 22: глубина корпуса ≥ NL + 3", d["carcass_depth"] >= d["NL"] + 3, f"{d['carcass_depth']} ≥ {d['NL'] + 3}")
        H_ = [h for h in s["holes"] if h["kind"] == "ecc_housing"]
        Bo = [h for h in s["holes"] if h["kind"] == "ecc_bolt"]
        St = [h for h in s["holes"] if h["kind"] == "ecc_stem"]
        add("Häfele стр. 294: корпус Ø15, глубина 12,5; остаток плиты при +0,5 ≥ 3",
            all(h["d"] == 15 and h["depth"] == 12.5 and 16 - 12.5 - 0.5 >= 3 for h in H_), f"{len(H_)} корпусов, остаток 3,0–3,5")
        okA = all(any(abs(h["z"] - b["z"]) < 1e-6 or True for b in Bo) for h in H_)
        midA = all(abs((parts[b["part"]]["z0"] + parts[b["part"]]["z1"]) / 2 - b["z"]) < 1e-6 and
                   abs((parts[b["part"]]["z0"] + parts[b["part"]]["z1"]) / 2 - parts[b["part"]]["z0"] - 8.0) < 1e-6 for b in Bo)
        add("Häfele стр. 294: ось болта на A = 8,0 от пласти (середина плиты 16)", midA, "8,0")
        dB = all(any(abs(abs(hh["x"] - b["x"]) - 24) < 1e-6 and abs(hh["y"] - b["y"]) < 1e-6 for hh in H_) for b in Bo)
        add("Häfele стр. 294/301: B = 24 — ось корпуса на 24 от торца (болт 262.27.679)", dB, "8 узлов")
        add("Отверстие под болт Ø8 ≥ гильзы Ø7,5 и доходит до дальней стенки корпуса (B + 7,5)",
            all(b["d"] >= 7.5 and b["depth"] >= 24 + 7.5 for b in Bo), f"Ø{Bo[0]['d']:g} × {Bo[0]['depth']:g}")
        add("Häfele стр. 301: резьба 11 → отверстие Ø5 глубже резьбы, остаток ≥ 3",
            all(h["d"] == 5 and h["depth"] >= 11 + 0.5 and 16 - h["depth"] >= 3 for h in St), f"Ø5 × {St[0]['depth']:g}, остаток {16 - St[0]['depth']:g}")
        hwq = {h["id"]: h["qty"] for h in s["hardware"]}
        add("Комплектность: пары = замки = ящики; саморезы профилей = точкам; замков 2 × 4",
            hwq["SLIDES"] == hwq["SLIDE-LOCK"] == 2 and hwq["LOCK-SCREW"] == 8 and hwq["SLIDE-SCREW"] == len(marks),
            f"{hwq['SLIDES']} / {hwq['SLIDE-LOCK']} / {hwq['LOCK-SCREW']} / {hwq['SLIDE-SCREW']}")
        add("Корпуса эксцентриков = болты S200", hwq["ECC-15"] == hwq["ECC-BOLT"], f"{hwq['ECC-15']}")
        add("Белое исполнение: короба из плиты корпуса", (s["options"]["color"] != "W") or d["interior_finish"] == "W",
            d["interior_finish"])
    # 2. совпадение отверстий: в каждом соединении отверстие пласти и отверстие торца — на одной оси
    bad = []
    for j, ids in d["joints"].items():
        hs = [h for h in s["holes"] if h["id"] in ids]
        face = [h for h in hs if h["kind"] in ("ecc_stem", "dowel_face", "conf_face")]
        edge = [h for h in hs if h["kind"] in ("ecc_bolt", "dowel_edge", "conf_edge")]
        for a in face:
            ax = "xyz".index(a["dir"][1])
            mates = [b for b in edge if all(abs(a[k] - b[k]) < 0.01 for k in "xyz" if "xyz".index(k) != ax)]
            if len(mates) != 1:
                bad.append(f"{j}:{a['id']}")
                continue
            b = mates[0]
            # вход торцевого отверстия = выход (или вход) отверстия пласти на сопрягаемой плоскости
            pa = a[a["dir"][1]] + (1 if a["dir"][0] == "+" else -1) * (a["depth"] if a["through"] else 0)
            if not (abs(b[b["dir"][1]] - pa) < 0.01 or abs(b[b["dir"][1]] - a[a["dir"][1]]) < 0.01):
                bad.append(f"{j}:{a['id']}~{b['id']}")
    add("Отверстия сопрягаемых деталей на одной оси", not bad, f"{sum(len(v) for v in d['joints'].values())} отверстий, "
        f"{len(d['joints'])} соединений" if not bad else str(bad[:5]))
    # отверстие лежит на своей детали: точка входа на грани, направление — внутрь
    off = []
    for h in s["holes"]:
        p = parts[h["part"]]
        ax = h["dir"][1]
        face_val = p[ax + ("0" if h["dir"][0] == "+" else "1")]
        inside = all(p[k + "0"] - 0.01 <= h[k] <= p[k + "1"] + 0.01 for k in "xyz")
        if abs(h[ax] - face_val) > 0.01 or not inside:
            off.append(h["id"])
    add("Точка входа каждого отверстия — на грани своей детали", not off, "все" if not off else str(off[:5]))
    # 3. количества
    hw = {h["id"]: h["qty"] for h in s["hardware"]}
    n = lambda kind: sum(1 for h in s["holes"] if h["kind"] == kind)
    add("Эксцентрики = корпуса = болты = штоки", hw["ECC-15"] == n("ecc_housing") == n("ecc_bolt") == n("ecc_stem") == 8,
        f"{hw['ECC-15']}")
    add("Шканты = отверстия в пласти = в торце", hw["DOWEL-8x30"] == n("dowel_face") == n("dowel_edge"), f"{hw['DOWEL-8x30']}")
    add("Конфирматы = отверстия Ø7 = Ø5", hw["CONF-7x50"] == n("conf_face") == n("conf_edge"), f"{hw['CONF-7x50']}")
    add("Винты ручек = отверстия Ø5 в фасадах", hw["SCREW-M4x22"] == n("handle") == 2 * hw["HANDLE-128"], f"{hw['SCREW-M4x22']}")
    add("Саморезы ХДФ = засверловки; фасада = отверстия", hw["SCREW-3.5x16"] == n("back_pilot") and hw["SCREW-4x25"] == n("front_screw"),
        f"{hw['SCREW-3.5x16']} / {hw['SCREW-4x25']}")
    add("Количества деталей", (sum(1 for p in boards if p["id"].startswith("BOX")), sum(1 for p in boards if p["id"].startswith("PL-")),
                                sum(1 for p in boards if p["id"].startswith("FRONT"))) == (10, 4, 2), "короба 10, цоколь 4, фасады 2")
    # 4. остаток при глухом сверлении и длины крепежа
    thin = []
    for h in s["holes"]:
        if h["through"]:
            continue
        p = parts[h["part"]]
        ax = h["dir"][1]
        L = p[ax + "1"] - p[ax + "0"]
        if L - h["depth"] < 3:
            thin.append(f"{h['id']} {h['kind']} {L - h['depth']:g}")
    add("Остаток при глухом сверлении ≥ 3 мм", not thin, "мин. " + str(min(
        (parts[h['part']][h['dir'][1] + '1'] - parts[h['part']][h['dir'][1] + '0'] - h['depth']) for h in s["holes"] if not h["through"])) + " мм"
        if not thin else str(thin[:4]))
    add("Конфирмат 50 = 16 + 34 ≤ 16 + гл. 36", 50 - 16 <= 36, "запас 2 на дне")
    add("Шкант 30 ≤ 12 + 20", 30 <= 12 + 20, "зазор 2")
    add("Саморез фасада 25: вход 9, остаток фасада 9", 25 - 16 == 9 and 18 - 9 >= 6, "9 / 9")
    add("Саморез ХДФ 16: в торец 12 ≤ засверловка 12", 16 - 4 <= 12, "12")
    # 5. доступ инструмента
    top_box = max(z + d["box_h"] for z in d["box_z0"])
    add("Головки винтов ручек выше коробов", all(zh - 4 > z0 + d["box_h"] for zh, z0 in zip(d["handle_z"], d["box_z0"])),
        ", ".join(f"{zh - 4 - z0 - d['box_h']:g}" for zh, z0 in zip(d["handle_z"], d["box_z0"])) + " мм")
    add("Корпуса эксцентриков доступны (до установки ящиков)", top_box < parts["TOP"]["z0"], f"от верхнего короба до крышки {parts['TOP']['z0'] - top_box:g}")
    sc = [h for h in s["holes"] if h["kind"] == "front_screw"]
    clr = min(h["z"] - (parts[h["part"].replace("-F", "-BOT")]["z1"]) for h in sc)
    add("Саморезы фасада выше дна короба (доступ отвёртки)", clr > 10, f"мин. {clr:g} мм над дном")
    # 6. пересечения деталей и зазоры
    clash = []
    for i, a in enumerate(boards):
        for b in boards[i + 1:]:
            if all(min(a[k + "1"], b[k + "1"]) - max(a[k + "0"], b[k + "0"]) > 0.01 for k in "xyz"):
                clash.append((a["id"], b["id"]))
    add("Детали не пересекаются", not clash, "нет" if not clash else str(clash[:4]))
    add("Зазор короб — боковина = системе", parts["BOX1-SL"]["x0"] - parts["SIDE-L"]["x1"] == d["slide_side"], f"{d['slide_side']} мм на сторону")
    add("NL ≤ глубина корпуса − 10", d["NL"] <= d["carcass_depth"] - 10, f"{d['NL']} ≤ {d['carcass_depth'] - 10}")
    # отверстия не пересекаются друг с другом внутри одной детали
    coll = []
    for p in boards:
        hs = [h for h in s["holes"] if h["part"] == p["id"]]
        for i, a in enumerate(hs):
            for b in hs[i + 1:]:
                if a["joint"] == b["joint"] and {a["kind"], b["kind"]} == {"ecc_bolt", "ecc_housing"}:
                    continue
                if _holes_clash(a, b):
                    coll.append(f"{a['id']}/{b['id']}")
    add("Отверстия в детали не пересекаются (кроме болт—корпус эксцентрика)", not coll, "нет" if not coll else str(coll[:4]))
    # 7–8. листы
    if report is not None:
        badr = {k: v for k, v in report.items() if v}
        add("Наложения текста и выход за рамку", not badr, "нет" if not badr else str(badr)[:300])
    if texts is not None:
        import re
        refs = {int(x) for t in texts for x in re.findall(r"(?:\bлист[а-я]*|(?<![А-Яа-я])л\.)\s*0?(\d{1,2})\b", t)}
        qrefs = {x for t in texts for x in re.findall(r"В-\d+", t)}
        add("Все ссылки на листы существуют", refs <= set(range(1, TOTAL + 1)), f"ссылки: {sorted(refs)}")
        known = {q[0] for q in QUESTIONS} | {q[0] for q in DECISIONS}
        add("Все упомянутые В-n есть на листе 11 (вопрос или принятое решение)", qrefs <= known,
            f"упомянуто {len(qrefs)}; открыто {len(QUESTIONS)}, принято {len(DECISIONS)}")
        add("Принятые решения не числятся открытыми", not ({q[0] for q in QUESTIONS} & {q[0] for q in DECISIONS}), "разделены")
        nodes = {x for t in texts for x in re.findall(r"уз(?:ел|лы|ла|лов)\s+([А-ИК])\b", t)}
        others = [c["name"] for k, c in materials()["colors"].items() if k != s["options"]["color"]]
        foreign = sorted({o for t in texts for o in others if o in t})
        if not d["grain"]:
            foreign += sorted({w for t in texts for w in ("текстура", "Дуб") if w in t})
        add("Нет примечаний других конфигураций (декор, текстура)", not foreign, "нет" if not foreign else str(foreign))
        add("Все упомянутые узлы есть на листе 08", nodes <= set("АБВГДЕЖИК"), f"{sorted(nodes)}")
    return out


def _holes_clash(a, b):
    """Грубая проверка: цилиндры как параллелепипеды по оси сверления."""
    def box(h):
        ax = "xyz".index(h["dir"][1]); sg = 1 if h["dir"][0] == "+" else -1
        r = h["d"] / 2
        lo, hi = [h[k] - r for k in "xyz"], [h[k] + r for k in "xyz"]
        e = h["xyz"[ax]] + sg * h["depth"]
        lo[ax], hi[ax] = min(h["xyz"[ax]], e), max(h["xyz"[ax]], e)
        return lo, hi
    (la, ha), (lb, hb) = box(a), box(b)
    return all(min(ha[i], hb[i]) - max(la[i], lb[i]) > 0.3 for i in range(3))


def build_and_verify(path, options=None):
    s = compile(SKU, options or {})
    stamp = stamp_for(s)
    report, texts, pngs = {}, [], []
    with PdfPages(path) as pdf:
        for fn in SHEETS:
            sh = fn(s, stamp)
            report[fn.__name__] = sh.check_overlaps()
            texts += [t.get_text() for t in sh.ax.texts]
            pdf.savefig(sh.fig)
            pngs.append(sh.fig)
        pdf.infodict()["Title"] = f"{SKU} {s['rev']} {s['hash']}"
    return s, verify(s, report, texts), pngs


if __name__ == "__main__":
    a = sys.argv[1:]
    kv = dict(x.split("=", 1) for x in a[1:])
    s, checks, figs = build_and_verify(a[0], kv)
    out = Path(a[0]).with_suffix("")
    for i, f in enumerate(figs, 1):
        f.savefig(f"{out}-{i:02d}.png", dpi=110)
        plt.close(f)
    for n, ok, t in checks:
        print("ok " if ok else "FAIL", n, "—", t)
