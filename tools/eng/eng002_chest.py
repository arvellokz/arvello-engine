"""ENG-002 · П1 — инструкция сборщику на весь комод ARV-NST-101 (A4, печать 100 %).

Разделы: обложка (опрокидывание, наборы, инструмент) → набор «Корпус» → корпус (предустановка, стойки, боковины, крышка,
стяжка стоек, задняя стенка) → цоколь → направляющие → ящики ×6 (страницы из eng002_guide) → карта ящиков →
крепление к стене (таблица типов стен) → пеленальный столик (только в исполнении со столиком).
Все детали, отверстия и количества — из модели генератора; подход — из сравнения с IKEA (docs/eng-002/01, раздел 6),
рисунки IKEA не копируются. Технологические значения — cab.TECH (решение владельца 12.11), метка [М], проверка [О].
Проверки выпуска — как у инструкции ящика (крепёж с видимой стороны, тексты, круги) + количество крепежа во всех
шагах = спецификации. Пример — НЕ утверждён.

Запуск: python3 tools/eng/eng002_chest.py out.pdf [width=1200 changer=yes]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

from eng import eng002_drawer as E  # noqa: E402
from eng import eng002_guide as G  # noqa: E402
from eng import kit13  # noqa: E402
from eng.cab import TECH  # noqa: E402
from eng.sheetlib import RED  # noqa: E402

BLUE, OKC = G.BLUE, G.OKC


# ------------------------------------------------------------------ данные
def chest_data(opts):
    D = E.drawer_data(opts)
    s = D["s"]
    pos, _, hp = kit13.positions(s)
    D["P"] = {p["id"]: p for p in s["parts"]}
    D["cpos"], D["view_errors"], D["zooms"], D["used"] = pos, [], [], {}
    D["changer"] = any(p["id"].startswith("CH-") for p in s["parts"])
    return D


def H_(D, joint_prefix, kind, part=None):
    return [h for h in D["s"]["holes"] if h["joint"].startswith(joint_prefix) and h["kind"] == kind
            and (part is None or h["part"] == part)]


def use(D, fid, n, where):
    """Учёт крепежа по шагам: в конце сумма сверяется со спецификацией."""
    D["used"].setdefault(fid, []).append((where, n))


def ball(pg, x, y, n):
    E.pos_ball(pg, x, y, n, r=3.6)


def obl(pg, D, box, items, **kw):
    ob = E.Oblique(pg, box, [b for b, _, _ in items], **kw)
    ob.draw(items)
    return ob


def fasten(pg, D, ob, holes, where):
    ob.fasteners(holes)
    E._check_view(D, ob, where)


# разные значки для разного крепежа на одном рисунке (проверка Codex 13.11): болт — синий треугольник,
# шкант — жёлтый квадрат, корпус эксцентрика — серый круг
SYM = {"ecc_stem": (BLUE, "^", 1.8), "dowel_face": ("#e0b54a", "s", 1.5), "ecc_housing": ("#9aa3ad", "o", 2.3)}


def fasten_kinds(pg, D, ob, holes, where):
    for kind, (col, shp, r) in SYM.items():
        hs = [h for h in holes if h["kind"] == kind]
        if hs:
            ob.fasteners(hs, col, r, shp)
    E._check_view(D, ob, where)


def sym(pg, x, y, kind):
    col, shp, r = SYM[kind]
    r *= 1.4
    if shp == "s":
        pg.ax.add_patch(Rectangle((x - r, y - r), 2 * r, 2 * r, fc=col, ec="k", lw=0.6, zorder=20))
    elif shp == "^":
        pg.ax.add_patch(Polygon([(x - r * 1.2, y - r), (x + r * 1.2, y - r), (x, y + r * 1.3)], fc=col, ec="k", lw=0.6,
                                zorder=20))
    else:
        pg.ax.add_patch(Circle((x, y), r, fc=col, ec="k", lw=0.6, zorder=20))


def badge(pg, x, y, n, pos, text, kind):
    sym(pg, x + 2, y, kind)
    G.count_badge(pg, x + 7, y, n, pos, text)


def ecc_zoom(pg, cx, cy, R=24):
    """Схема корпуса эксцентрика (не контур Häfele): гнездо Ø15 на 24 от кромки, стрелка корпуса — к кромке, где болт."""
    ax = pg.ax
    ax.add_patch(Circle((cx, cy), R, fc="white", ec="k", lw=1.4, zorder=14))
    ax.add_patch(Rectangle((cx - R * 0.9, cy + R * 0.45), R * 1.8, R * 0.25, fc=G.WOOD2, ec="k", lw=0.8, zorder=15))
    pg.text(cx, cy + R + 3, "кромка детали — сюда входит болт", size=6.5, ha="center", va="bottom", zorder=16)
    ax.add_patch(Circle((cx, cy - R * 0.15), R * 0.42, fc="#c9ced4", ec="k", lw=0.9, zorder=16))
    ax.add_patch(FancyArrowPatch((cx, cy - R * 0.15), (cx, cy + R * 0.42), arrowstyle="-|>", mutation_scale=11,
                                 color=RED, lw=1.6, zorder=17))
    pg.text(cx, cy - R * 0.72, "стрелка на корпусе — к кромке", size=6.3, ha="center", zorder=16, weight="bold")
    pg.text(cx, cy - R - 3.5, "схема (не контур Häfele): Ø15, центр 24 от кромки [Д]", size=6.8, ha="center", va="top")


def parts(D, *ids):
    return [D["P"][i] for i in ids]


# ================================================================== страницы
def page_cover(D, n, total):
    pg = G.Page(D, n, total, "Комод · обложка")
    s, nd = D["s"], D["nd"]
    d = s["derived"]
    pg.text(14, 270, "КОМОД ARV-NST-101", size=20, weight="bold")
    pg.text(14, 260, f"{d['width']:g} × {d['depth']:g} × {d['height']:g} · {kit13.cfg_ru(s, short=True)}", size=9)
    pg.text(14, 254, "Инструкция для сборщика Arvello. Пример ENG-002 — не утверждён.", size=8, color="#444")
    # опрокидывание
    pg.ax.add_patch(Rectangle((14, 196), 182, 50, fc="#fbe3df", ec=RED, lw=1.6))
    pg.ax.add_patch(Polygon([(30, 236), (22, 222), (38, 222)], closed=True, fc="#ffd54f", ec="k", lw=1.2))
    pg.text(30, 227, "!", size=14, weight="bold", ha="center", va="center")
    pg.text(46, 238, "ОПРОКИДЫВАНИЕ", size=13, weight="bold", color=RED, va="center")
    for i, t in enumerate(["Комод ОБЯЗАТЕЛЬНО крепится к стене (раздел «Стена»), до загрузки ящиков.",
                           "Детская комната: проверить крепление рукой после установки.",
                           "Не открывать одновременно несколько нагруженных ящиков; тяжёлое — вниз."] +
                          (["Пеленальный столик — только на закреплённом к стене комоде (В-106)."] if D["changer"] else [])):
        pg.text(46, 226 - 7 - i * 6, t, size=8.0)
    pg.text(14, 186, "Наборы (детали подписаны номером позиции на наклейке)", size=9.5, weight="bold")
    rows = [["Корпус", "боковины, дно, крышка, 2 стойки, задняя стенка + крепёж", "1"],
            ["Цоколь", "4 детали цоколя + шканты, конфирматы", "1"],
            ["Ящик", "5 деталей короба + фасад + крепёж + замки (на ОДИН ящик)", f"{nd}"],
            ["Корпус: Blum", "направляющие MOVENTO, TIP-ON BLUMOTION, синхронизация", f"{nd} компл."],
            ["Стена", "уголки и крепёж по типу стены", "1"]] + \
           ([["Столик", "основание, 3 бортика + крепёж, матрас", "1"]] if D["changer"] else [])
    pg.table(14, 181, ["Набор", "Что внутри", "Кол."], rows, [32, 132, 18], row_h=6.0, size=7.8)
    pg.text(14, 132, "Инструмент", size=9.5, weight="bold")
    pg.text(14, 126, "шестигранник 4 · отвёртка PH2 · дрель с битами · сверло Ø3 · шаблон Blum T65.1000.02 ·", size=8)
    pg.text(14, 121, "рулетка 3 м · уровень · угольник · мягкая подложка; крепёж к стене — по типу стены", size=8)
    pg.text(14, 108, "Порядок", size=9.5, weight="bold")
    order = ["К1–К9 · корпус, цоколь", "К10 · СТЕНА", "К11–К12 · направляющие", f"Я1–Я10 · ящики ×{nd}",
             "К13–К14 · схема, проверка"] + (["С1–С2 · столик"] if D["changer"] else [])
    for i, t in enumerate(order):
        x = 14 + (i % 3) * 62
        y = 100 - (i // 3) * 8
        pg.text(x, y, t, size=9)
    pg.line(14, 72, 64, 72, dict(lw=1.2, color="k", ls="-"))
    for k in range(6):
        pg.line(14 + k * 10, 72, 14 + k * 10, 74.5 if k % 5 else 76, dict(lw=0.8, color="k", ls="-"))
    pg.text(70, 73, "50 мм — проверка печати 100 % (крепёж на наборах — в натуральную величину)", size=7.5, va="center")
    pg.text(14, 58, "Метки: [М] — наше значение по модели · [Д] — документ Blum · [О] — проверить на первом изделии.",
            size=7.5, color="#444")
    t = TECH
    pg.text(14, 52, f"Значения Arvello по умолчанию [М]: паз под дно {kit13.n_(16 + t['groove_w_add'])}, зазор дна "
            f"{kit13.n_(t['bottom_clear'])} на сторону; крючок и замки — сборщик по шаблону.", size=7.5, color="#444")
    return pg


def page_set_carcass(D, n, total):
    pg = G.Page(D, n, total, "Набор «Корпус» и «Цоколь»")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    pg.text(12, 278, "Набор «Корпус» и «Цоколь»", size=14, weight="bold")
    cells = [("SIDE-L", "боковина Л"), ("SIDE-R", "боковина П"), ("BOTTOM", "дно"), ("TOP", "крышка"),
             ("PART-1", "стойка Л"), ("PART-2", "стойка П"), ("BACK", "задняя стенка ХДФ"),
             ("PL-F", "цоколь перед."), ("PL-B", "цоколь задн."), ("PL-SL", "цоколь бок. Л"), ("PL-SR", "цоколь бок. П")]
    for i, (pid, nm) in enumerate(cells):
        x, y = 12 + (i % 4) * 48, 238 - (i // 4) * 36
        b = P[pid]
        ob = E.Oblique(pg, (x + 8, y, x + 40, y + 26), [b], sgn=1)
        ob.draw([(b, E.HL, {})])
        ball(pg, x + 4, y + 23, pos[pid])
        pg.text(x + 24, y - 3, f"1× {nm}", size=7, ha="center", va="center")
        let = G.side_letter(b["name"])
        if let:
            G.sticker(pg, x + 30, y + 22, pos[pid], let)
    pg.text(12, 140, "Крепёж корпуса и цоколя (длина — в натуральную величину, головки условно)", size=9, weight="bold")
    H = D["H"]
    cnt = lambda fid: sum(1 for h in D["s"]["holes"] if h.get("fastener") == fid and "BOX" not in h["joint"]
                          and "FRONT" not in h["joint"] and not h["joint"].startswith("J-CH"))
    rows = [("DOWEL-8x30", "шкант 8 × 30", "dowel"), ("CONF-7x50", "конфирмат 7 × 50", "conf"),
            ("SCREW-3.5x16", "саморез 3,5 × 16 (ХДФ)", "screw"), ("SCREW-4x25P", "саморез 4 × 25 (стойки)", "screw")]
    y = 128
    for fid, nm, kind in rows:
        d_, L = G.fdims(fid)
        if kind == "dowel":
            pg.ax.add_patch(Rectangle((14, y - d_ / 2), L, d_, fc="#e8c99a", ec="k", lw=0.6, hatch="||"))
        else:
            G.screw_shape(pg.ax, 14, y, d_, L, 0.0, kind, 1.0)
        pg.text(72, y, f"{cnt(fid)}×", size=12, weight="bold", va="center")
        ball(pg, 86, y, hp[fid])
        pg.text(92, y, nm, size=8, va="center")
        y -= 13
    # эксцентрики — условно
    pg.ax.add_patch(Circle((22, y), 7.5, fc="#c9ced4", ec="k", lw=0.8))
    pg.ax.add_patch(Rectangle((19, y - 0.8), 6, 1.6, fc="k"))
    pg.text(72, y, f"{cnt('ECC-15')}×", size=12, weight="bold", va="center")
    ball(pg, 86, y, hp["ECC-15"])
    pg.text(92, y, "корпус эксцентрика Minifix 15 (условно)", size=8, va="center")
    y -= 13
    G.screw_shape(pg.ax, 14, y, 5, 24 + 11, 0.0, "screw", 1.0)
    pg.text(72, y, f"{H['ECC-BOLT']['qty']}×", size=12, weight="bold", va="center")
    ball(pg, 86, y, hp["ECC-BOLT"])
    pg.text(92, y, "болт стяжки S200 (условно)", size=8, va="center")
    pg.text(12, 40, f"Расходник: клей ПВА D3 (поз. {hp['GLUE-PVA']}) — {kit13.n_(H['GLUE-PVA']['qty'])} кг, для шкантов (К1, К2, К9а).",
            size=7.5)
    pg.text(12, 34, "Направляющие и TIP-ON BLUMOTION — набор «Корпус: Blum» (раздел 3); крепёж ящиков — в наборах «Ящик».",
            size=7.5)
    return pg


def page_pre(D, n, total):
    """Корпус · 1–2: предустановка болтов стяжки и шкантов."""
    pg = G.Page(D, n, total, "Корпус · К1–К2")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    G.step(pg, 12, 279, "К1", prefix="", title="Болты стяжки и шканты — в боковины (внутренняя сторона)")
    for i, (pid, sg) in enumerate((("SIDE-L", 1), ("SIDE-R", -1))):
        S = P[pid]
        ob = obl(pg, D, (16 + i * 92, 196, 100 + i * 92, 266), [(S, E.HL, {})], sgn=sg)
        st = [h for h in D["s"]["holes"] if h["part"] == pid and h["kind"] in ("ecc_stem", "dowel_face")]
        fasten_kinds(pg, D, ob, st, f"корпус 1 {pid}")
        ball(pg, *ob.p(S["x0"], S["y0"], S["z1"] + 40), pos[pid])
        G.sticker(pg, *ob.p(S["x0"], S["y1"], S["z1"] + 60), pos[pid], G.side_letter(S["name"]))
    nb = len(H_(D, "J-L", "ecc_stem")) + len(H_(D, "J-R", "ecc_stem"))
    nd_ = len(H_(D, "J-L", "dowel_face")) + len(H_(D, "J-R", "dowel_face"))
    use(D, "ECC-BOLT", nb, "шаг 1"); use(D, "DOWEL-8x30", nd_, "шаг 1")
    badge(pg, 16, 186, nb, hp["ECC-BOLT"], "болт стяжки (▲) — вкрутить до упора, шестигранник 4", "ecc_stem")
    badge(pg, 16, 176, nd_, hp["DOWEL-8x30"], "шкант 8 × 30 (■) — на клей ПВА, вбить до упора", "dowel_face")
    G.step(pg, 12, 160, "К2", prefix="", title="Болты и шканты — в дно и крышку (места под стойки)")
    B, T = P["BOTTOM"], P["TOP"]
    obB = obl(pg, D, (16, 80, 100, 150), [(B, E.HL, {})], sgn=1)
    fasten_kinds(pg, D, obB, [h for h in D["s"]["holes"] if h["part"] == "BOTTOM" and h["kind"] in ("ecc_stem", "dowel_face")],
                 "корпус 2 дно")
    obT = obl(pg, D, (108, 80, 196, 150), [(T, E.HL, {})], sgn=1, zs=-1)
    fasten_kinds(pg, D, obT, [h for h in D["s"]["holes"] if h["part"] == "TOP" and h["kind"] in ("ecc_stem", "dowel_face")],
                 "корпус 2 крышка")
    ball(pg, *obB.p(B["x0"], B["y0"], B["z1"] + 30), pos["BOTTOM"])
    ball(pg, *obT.p(T["x0"], T["y0"], T["z0"] - 30), pos["TOP"])
    pg.text(58, 76, "дно — сверху", size=7, ha="center", style="italic")
    pg.text(152, 76, "крышка — вид снизу (внутренняя сторона)", size=7, ha="center", style="italic")
    nb2 = len(H_(D, "J-PART", "ecc_stem")); nd2 = len(H_(D, "J-PART", "dowel_face"))
    use(D, "ECC-BOLT", nb2, "шаг 2"); use(D, "DOWEL-8x30", nd2, "шаг 2")
    badge(pg, 16, 64, nb2, hp["ECC-BOLT"], "болт стяжки (▲)", "ecc_stem")
    badge(pg, 16, 54, nd2, hp["DOWEL-8x30"], "шкант 8 × 30 (■) на клей", "dowel_face")
    G.check_box(pg, 110, 70, 90, ["болты вкручены до упора,", "шканты выступают одинаково"])
    return pg


def page_housings(D, n, total):
    pg = G.Page(D, n, total, "Корпус · К3")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    G.step(pg, 12, 279, "К3", prefix="", title="Корпуса эксцентриков — в дно, крышку и стойки (стрелкой к краю)")
    B, T, S1, S2 = P["BOTTOM"], P["TOP"], P["PART-1"], P["PART-2"]
    obB = obl(pg, D, (16, 200, 100, 266), [(B, E.HL, {})], sgn=1)
    fasten_kinds(pg, D, obB, [h for h in D["s"]["holes"] if h["part"] == "BOTTOM" and h["kind"] == "ecc_housing"], "корпус 3 дно")
    obT = obl(pg, D, (108, 200, 196, 266), [(T, E.HL, {})], sgn=1, zs=-1)
    fasten_kinds(pg, D, obT, [h for h in D["s"]["holes"] if h["part"] == "TOP" and h["kind"] == "ecc_housing"], "корпус 3 крышка")
    ob1 = obl(pg, D, (16, 120, 100, 190), [(S1, E.HL, {})], sgn=-1)
    fasten_kinds(pg, D, ob1, [h for h in D["s"]["holes"] if h["part"] == "PART-1" and h["kind"] == "ecc_housing"], "корпус 3 ст. Л")
    ob2 = obl(pg, D, (108, 120, 196, 190), [(S2, E.HL, {})], sgn=1)
    fasten_kinds(pg, D, ob2, [h for h in D["s"]["holes"] if h["part"] == "PART-2" and h["kind"] == "ecc_housing"], "корпус 3 ст. П")
    for ob, pid, z in ((obB, "BOTTOM", B["z1"] + 30), (obT, "TOP", T["z0"] - 30)):
        b = P[pid]
        ball(pg, *ob.p(b["x0"], b["y0"], z), pos[pid])
    ball(pg, *ob1.p(S1["x1"], S1["y0"], S1["z1"] + 30), pos["PART-1"])
    ball(pg, *ob2.p(S2["x0"], S2["y0"], S2["z1"] + 30), pos["PART-2"])
    pg.text(58, 116, "стойка Л — со стороны ЛЕВОЙ колонны", size=7, ha="center", style="italic")
    pg.text(152, 116, "стойка П — со стороны ПРАВОЙ колонны", size=7, ha="center", style="italic")
    nh = len([h for h in D["s"]["holes"] if h["kind"] == "ecc_housing"])
    use(D, "ECC-15", nh, "шаг 3")
    badge(pg, 16, 104, nh, hp["ECC-15"], "корпус эксцентрика Minifix 15 (●) — стрелкой к кромке", "ecc_housing")
    ecc_zoom(pg, 160, 66)
    h0 = next(h for h in D["s"]["holes"] if h["kind"] == "ecc_housing" and h["part"] == "PART-1")
    G.check_box(pg, 16, 92, 120, ["корпуса заподлицо с пластью, не затянуты",
                                  "стойки: гнёзда смотрят в СВОЮ колонну —",
                                  "иначе после сборки к ним не подобраться"])
    pg.text(16, 50, "Корпус Ø15, гл. 12,5; болт B 24 (Häfele, узел А комплекта) [Д].", size=7.5, color="#444")
    _ = h0
    return pg


def page_stands(D, n, total):
    pg = G.Page(D, n, total, "Корпус · К4–К5")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    B, S1, S2, L, R = P["BOTTOM"], P["PART-1"], P["PART-2"], P["SIDE-L"], P["SIDE-R"]
    G.step(pg, 12, 279, "К4", prefix="", title="Стойки — на дно; эксцентрики стоек повернуть (затянуть)")
    # стойка двойная: Л и П показаны раздельно (раздвинуты), каждая — гнёздами в свою колонну
    s1m, s2m = E.moved(S1, dx=-110, dz=120), E.moved(S2, dx=110, dz=120)
    ob = obl(pg, D, (16, 186, 196, 266), [(B, E.DONE, {}), (s1m, E.HL, {}), (s2m, E.HL, {})], sgn=1)
    for S, S0 in ((s1m, S1), (s2m, S2)):
        ym = (S["y0"] + S["y1"]) / 2
        ob.arrow(((S["x0"] + S["x1"]) / 2, ym, S["z0"] - 5), ((S0["x0"] + S0["x1"]) / 2, ym, B["z1"] + 40))
    ball(pg, *ob.p(s1m["x0"], s1m["y0"], s1m["z1"] + 20), pos["PART-1"])
    ball(pg, *ob.p(s2m["x1"], s2m["y0"], s2m["z1"] + 20), pos["PART-2"])
    G.sticker(pg, *ob.p(s1m["x0"] - 260, s1m["y1"], s1m["z1"] + 40), pos["PART-1"], "Л")
    G.sticker(pg, *ob.p(s2m["x1"] + 60, s2m["y1"], s2m["z1"] + 40), pos["PART-2"], "П")
    x, y = ob.p(s1m["x0"], s1m["y0"] + 100, s1m["z0"] + 300)
    E.callout(pg, x, y, x - 4, y - 32, "стойка Л: гнёзда — влево", 7.5)
    x, y = ob.p(s2m["x1"], s2m["y0"] + 100, s2m["z0"] + 300)
    E.callout(pg, x, y, x + 6, y - 44, "стойка П: гнёзда — вправо", 7.5)
    hb = [h for h in D["s"]["holes"] if h["kind"] == "ecc_housing" and h["part"] in ("PART-1", "PART-2")
          and h["joint"].endswith("BOTTOM")]
    G.check_box(pg, 16, 180, 184, [f"{len(hb)} эксцентрика стоек (нижние) — повернуть по часовой до упора, шестигранник 4",
                                   "стойка Л — со стороны левой колонны, стойка П — со стороны правой"])
    G.step(pg, 12, 158, "К5", prefix="", title="Боковины — к дну; эксцентрики дна повернуть изнутри")
    lm, rm = E.moved(L, dx=-140), E.moved(R, dx=140)
    ob2 = obl(pg, D, (16, 66, 196, 148), [(B, E.DONE, {}), (S1, E.DONE, {}), (S2, E.DONE, {}), (lm, E.HL, {}),
                                          (rm, E.HL, {})], sgn=1)
    zc = L["z0"] + 200
    ob2.arrow((lm["x1"] + 10, L["y0"] + 100, zc), (L["x1"] + 40, L["y0"] + 100, zc))
    ob2.arrow((rm["x0"] - 10, R["y0"] + 100, zc), (R["x0"] - 40, R["y0"] + 100, zc))
    ball(pg, *ob2.p(lm["x0"], lm["y0"], lm["z1"]), pos["SIDE-L"])
    ball(pg, *ob2.p(rm["x1"], rm["y0"], rm["z1"]), pos["SIDE-R"])
    G.sticker(pg, *ob2.p(lm["x0"] - 200, lm["y1"], lm["z1"]), pos["SIDE-L"], "Л")
    G.sticker(pg, *ob2.p(rm["x1"] + 40, rm["y1"], rm["z1"]), pos["SIDE-R"], "П")
    hd = [h for h in D["s"]["holes"] if h["kind"] == "ecc_housing" and h["part"] == "BOTTOM"]
    G.check_box(pg, 16, 58, 184, [f"{len(hd)} эксцентрика в дне — повернуть до упора (доступ сверху, изнутри)",
                                  "боковины стоят ровно по передней кромке дна"])
    return pg


def page_top(D, n, total):
    pg = G.Page(D, n, total, "Корпус · К6–К7")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    B, T, S1, S2, L, R = (P[k] for k in ("BOTTOM", "TOP", "PART-1", "PART-2", "SIDE-L", "SIDE-R"))
    G.step(pg, 12, 279, "К6", prefix="", title="Крышка — сверху на боковины и стойки; затянуть эксцентрики")
    tm = E.moved(T, dz=140)
    ob = obl(pg, D, (16, 176, 196, 266), [(B, E.DONE, {}), (S1, E.DONE, {}), (S2, E.DONE, {}), (L, E.DONE, {}),
                                          (R, E.DONE, {}), (tm, E.HL, {})], sgn=1)
    for xx in (T["x0"] + 200, T["x1"] - 200):
        ob.arrow((xx, (T["y0"] + T["y1"]) / 2, tm["z0"] - 5), (xx, (T["y0"] + T["y1"]) / 2, T["z1"] + 30))
    ball(pg, *ob.p(tm["x0"], tm["y0"], tm["z1"] + 20), pos["TOP"])
    ht = [h for h in D["s"]["holes"] if h["kind"] == "ecc_housing" and h["part"] == "TOP"]
    hs = [h for h in D["s"]["holes"] if h["kind"] == "ecc_housing" and h["part"] in ("PART-1", "PART-2")
          and h["joint"].endswith("TOP")]
    G.check_box(pg, 16, 170, 184, [f"{len(ht)} эксцентрика в крышке (изнутри, снизу) и {len(hs)} верхних в стойках —",
                                   "повернуть до упора; крышка заподлицо с боковинами"])
    G.step(pg, 12, 150, "К7", prefix="", title="Стойки стянуть между собой: 2 самореза 4 × 25 из левой колонны")
    st = H_(D, "J-ST-PAIR", "screw_face")
    ob2 = obl(pg, D, (16, 70, 120, 142), [(B, E.DONE, {}), (S2, E.DONE, {}), (S1, E.HL, {})], sgn=-1)
    fasten(pg, D, ob2, st, "корпус 7")
    use(D, "SCREW-4x25P", len(st), "шаг 7")
    z = G.zoom(pg, D, st[0], 160, 104, R=28, win=30, label="сечение: стойка Л + стойка П (из модели)",
               allowed={"PART-1", "PART-2"})
    D["zooms"].append(("корпус 7", st[0], z))
    G.count_badge(pg, 16, 62, len(st), hp["SCREW-4x25P"], "саморез 4 × 25 · PH2 · из левой колонны")
    pl = next(h for h in D["s"]["holes"] if h["joint"] == "J-ST-PAIR" and h["kind"] == "pilot")
    G.check_box(pg, 16, 52, 184, [f"засверловка в правой стойке Ø{kit13.n_(pl['d'])} гл. {kit13.n_(pl['depth'])} [М]; "
                                  "головки заподлицо"])
    return pg


def page_back(D, n, total):
    pg = G.Page(D, n, total, "Корпус · К8")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    car = [P[k] for k in ("BOTTOM", "TOP", "PART-1", "PART-2", "SIDE-L", "SIDE-R")]
    BK = P["BACK"]
    G.step(pg, 12, 279, "К8", prefix="", title="Выставить диагонали, затем задняя стенка ХДФ")
    ob = obl(pg, D, (16, 160, 196, 266), [(q, E.DONE, {}) for q in car] + [(BK, E.HL, {})], sgn=1, ys=-1)
    hb = H_(D, "J-BACK", "back_pilot")
    # саморез входит через ХДФ: точка — на наружной стороне задней стенки, засверловка — в торце детали корпуса
    hbv = [{**h, "part": BK["id"], "y": BK["y1"]} for h in hb]
    fasten(pg, D, ob, hbv, "корпус 8")
    use(D, "SCREW-3.5x16", len(hb), "шаг 8")
    ball(pg, *ob.p(BK["x1"], BK["y1"], BK["z1"] + 20), pos["BACK"])
    pg.text(105, 154, "вид сзади", size=7, ha="center", style="italic")
    G.count_badge(pg, 16, 142, len(hb), hp["SCREW-3.5x16"], "саморез 3,5 × 16 · PH2 · шаг ≈ 150 [М]")
    d = D["s"]["derived"]
    W, Hc = P["SIDE-R"]["x1"] - P["SIDE-L"]["x0"], P["SIDE-L"]["z1"] - P["SIDE-L"]["z0"]
    diag = (W ** 2 + Hc ** 2) ** 0.5
    G.check_box(pg, 16, 130, 184, [f"диагонали корпуса по фасаду равны: ≈ {diag:.0f}, разность ≤ 1,5 [М]",
                                   "ХДФ — накладная, отступ 2 от граней; сначала 4 угла, потом остальное",
                                   "в двойную стойку — только в левую половину (по разметке) [М]"])
    return pg


def page_runners(D, n, total):
    pg = G.Page(D, n, total, "Направляющие")
    P, r, hp, nd, H = D["P"], D["r"], D["hpos"], D["nd"], D["H"]
    G.step(pg, 12, 279, "К11", prefix="", title=f"Направляющие MOVENTO: {nd} пар, по 6 саморезов на профиль")
    S = P["SIDE-L"]
    marks = [h for h in D["s"]["holes"] if h["part"] == "SIDE-L" and h["kind"] == "runner_mark"]
    sc = 0.12
    x0, y0 = 22, 162
    pg.rect(x0, y0, x0 + (S["y1"] - S["y0"]) * sc, y0 + (S["z1"] - S["z0"]) * sc, dict(lw=1.0, color="k", ls="-"),
            fill="#f3f3f3")
    for h in marks:
        u = x0 + (h["y"] - S["y0"]) * sc
        v = y0 + (h["z"] - S["z0"]) * sc
        pg.ax.add_patch(Circle((u, v), 1.0, fc=RED, ec="k", lw=0.4, zorder=12))
    zs = sorted({h["z"] for h in marks})
    for z in zs:
        v = y0 + (z - S["z0"]) * sc
        pg.ax.add_patch(Rectangle((x0, v - 3), r["NL"] * sc, 6, fc="#cfe0f5", ec=BLUE, lw=0.6, zorder=8, alpha=0.7))
        pg.text(x0 + (S["y1"] - S["y0"]) * sc + 3, v, f"ось {kit13.n_(round(z - S['z0'], 1))} от низа боковины",
                size=7, va="center")
    pg.text(x0, y0 - 5, "боковина Л, вид изнутри; перед — слева; красные точки — разметка саморезов [Д: Blum с. 428]",
            size=7)
    pts = sorted({round(h["y"] - (S["y0"]), 1) for h in marks})
    pg.text(x0, y0 - 10, "от передней кромки: " + " / ".join(kit13.n_(v) for v in pts), size=7.5, weight="bold")
    nm = len([h for h in D["s"]["holes"] if h["kind"] == "runner_mark"])
    use(D, "SLIDE-SCREW-M", nm, "шаг 10")
    r0 = D["s"]["derived"]["drawers"]
    fl, rb0 = r0[0]["floor"], r0[0]["rb"]
    pitch = r0[1]["rb"] - r0[0]["rb"]
    pg.text(x0, y0 - 16, f"нижняя ось {kit13.n_(round(rb0 + 38 - S['z0'], 1))} = дно {kit13.n_(fl - S['z0'])} + 38 (мин. Blum над "
            f"опорой [Д]) + {kit13.n_(rb0 - fl)} запас [М]; шаг по высоте {kit13.n_(round(pitch, 1))} = шаг фасадов [М]", size=6.8)
    pg.text(x0, y0 - 21, "Запас 1: Blum задаёт минимум 38 — запас держит его при допуске толщины плиты ±0,3; Blum его не требует.",
            size=6.5, color="#444")
    G.count_badge(pg, 16, 126, nm, hp["SLIDE-SCREW-M"], "саморез 609.1500 Ø3,5 × 15 · без сверления, по разметке")
    G.check_box(pg, 16, 116, 184, ["все колонки и стойки — одинаково: профиль Л на левую стенку колонны, П — на правую",
                                   "профили ставят ПОСЛЕ сборки корпуса; ось — по разметке (мин. 38 над дном [Д] + запас 1 [М])",
                                   "профили одного ящика — на одной высоте (уровень)"])
    G.step(pg, 12, 86, "К12", prefix="", title="TIP-ON BLUMOTION и синхронизация — по инструкции Blum в упаковке")
    sync = H["TIPON-SYNC"]["spec"]
    pg.text(16, 74, f"Набор на ящик: {sync.split(' (')[0].replace('Blum ', '')} [Д].", size=7.5)
    pg.text(16, 68, "Синхронизацию отрезать: " + sync.split("синхронизация ")[-1].split(" (")[0] + " [Д].", size=7.5)
    G.check_box(pg, 16, 62, 184, ["состав поставки Blum сверить с упаковкой до установки [О]",
                                  "зазор фасад — корпус 2,5 выставить на шаге фасада Я10"])
    return pg


def page_drawer_map(D, n, total):
    pg = G.Page(D, n, total, "Ящики: схема")
    nd = D["nd"]
    G.step(pg, 12, 279, "К13", prefix="", title=f"Ящики: {nd} шт. — шаги Я1–Я10, затем в проём по схеме")
    d = D["s"]["derived"]
    drs = d["drawers"]
    P = D["P"]
    W, Hc = d["width"], P["SIDE-L"]["z1"]
    sc = 0.1
    x0, y0 = 24, 160
    pg.rect(x0, y0, x0 + W * sc, y0 + Hc * sc, dict(lw=1.2, color="k", ls="-"))
    for i, rr in enumerate(drs):
        fr = P[rr["front"]]
        pg.rect(x0 + fr["x0"] * sc, y0 + fr["z0"] * sc, x0 + fr["x1"] * sc, y0 + fr["z1"] * sc,
                dict(lw=0.8, color="k", ls="-"), fill="#f3d6ae")
        pg.text(x0 + (fr["x0"] + fr["x1"]) / 2 * sc, y0 + (fr["z0"] + fr["z1"]) / 2 * sc, str(i + 1), size=12,
                weight="bold", ha="center", va="center")
    pg.text(x0 + W * sc + 6, y0 + Hc * sc - 6, "Все ящики одинаковые —", size=8)
    pg.text(x0 + W * sc + 6, y0 + Hc * sc - 11, "любой в любой проём.", size=8)
    pg.text(x0 + W * sc + 6, y0 + Hc * sc - 20, "Ставить снизу вверх,", size=8)
    pg.text(x0 + W * sc + 6, y0 + Hc * sc - 25, "по одному.", size=8)
    G.check_box(pg, 16, 136, 184, ["комод уже закреплён к стене (К10) — только после этого ставить ящики",
                                   "первый ящик — целиком с фасадом и проверкой (Я10), потом остальные"])
    return pg


def page_final(D, n, total):
    pg = G.Page(D, n, total, "Итоговая проверка")
    nd = D["nd"]
    G.step(pg, 12, 279, "К14", prefix="", title=f"Все {nd} ящиков на месте: итоговая проверка")
    G.check_box(pg, 16, 266, 184, ["зазоры фасадов: 3 между, 1,5 по краям, 2,5 до корпуса [М][Д]",
                                   "каждый ящик: нажатие открывает, мягко закрывается, ничего не задевает",
                                   "комод не качается и не отходит от стены (К10)",
                                   "крышка и фасады чистые; лишний крепёж не остался"])
    return pg


def page_plinth(D, n, total):
    """К9: цоколь — (а) рамка из 4 деталей на шкантах, разнесено; (б) корпус на рамку, конфирматы через дно изнутри."""
    pg = G.Page(D, n, total, "Цоколь · К9а–К9б")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    F, Bk, SL, SR, BOT = (P[k] for k in ("PL-F", "PL-B", "PL-SL", "PL-SR", "BOTTOM"))
    hd = [h for h in D["s"]["holes"] if h["joint"].startswith("J-PL") and h["kind"] == "dowel_face"]
    he = [h for h in D["s"]["holes"] if h["joint"].startswith("J-PL") and h["kind"] == "dowel_edge"]
    G.step(pg, 12, 279, "К9а", prefix="", title="Рамка цоколя: 4 детали на шкантах (на клей)")
    gap = 140
    Fm, Bm = E.moved(F, dy=-gap), E.moved(Bk, dy=gap)
    ob = obl(pg, D, (16, 178, 196, 266), [(SL, E.HL, {}), (SR, E.HL, {}), (Fm, E.HL, {}), (Bm, E.HL, {})], sgn=1)
    mv = {"PL-F": -gap, "PL-B": gap}
    pts_e = [(h["x"], h["y"], h["z"]) for h in he]                    # шканты в торцах боковых деталей
    ob.dots(pts_e, "#e0b54a", 1.5, "s")
    for h in hd:                                                       # ответные отверстия в переднем / заднем
        ob.dots([(h["x"], h["y"] + mv.get(h["part"], 0), h["z"])], "white", 1.3, "o")
    for W, d in ((Fm, 1), (Bm, -1)):
        xm = (W["x0"] + W["x1"]) / 2
        yy = W["y1"] if d > 0 else W["y0"]
        ob.arrow((xm, yy + 0 * d, W["z1"] + 10), (xm, yy + d * (gap - 40), W["z1"] + 10))
    for pid, W in (("PL-F", Fm), ("PL-B", Bm), ("PL-SL", SL), ("PL-SR", SR)):
        ball(pg, *ob.p(W["x0"] if pid != "PL-SR" else W["x1"], W["y0"], W["z1"] + 50), pos[pid])
    G.sticker(pg, *ob.p(SL["x0"] - 120, SL["y1"], SL["z1"] + 60), pos["PL-SL"], "Л")
    G.sticker(pg, *ob.p(SR["x1"] - 120, SR["y1"], SR["z1"] + 60), pos["PL-SR"], "П")
    use(D, "DOWEL-8x30", len(hd), "К9а")
    badge(pg, 16, 168, len(hd), hp["DOWEL-8x30"], "шкант 8 × 30 (■) — в торцы боковых деталей, на клей", "dowel_face")
    pg.text(23, 160, "белые кружки — ответные отверстия в переднем и заднем цоколе", size=7)
    G.check_box(pg, 16, 154, 184, ["углы рамки 90° (угольник), диагонали рамки равны",
                                   "передний цоколь — с отступом от фасадов (по рисунку), задний — у стены"])
    G.step(pg, 12, 126, "К9б", prefix="", title="Корпус — на рамку; конфирматы сверху через дно корпуса")
    hc = [h for h in D["s"]["holes"] if h["joint"].startswith("J-BOT-PL") and h["kind"] == "conf_face"]
    B_up = E.moved(BOT, dz=0)
    ob2 = obl(pg, D, (16, 40, 120, 116), [(q, E.DONE, {}) for q in (F, Bk, SL, SR)] + [(B_up, E.HL, {})], sgn=1)
    ob2.fasteners(hc, RED, 1.4)
    E._check_view(D, ob2, "К9б")
    pg.text(68, 34, "дно корпуса сверху (корпус целиком не показан)", size=7, ha="center", style="italic")
    use(D, "CONF-7x50", len(hc), "К9б")
    G.count_badge(pg, 126, 108, len(hc), hp["CONF-7x50"], "конфирмат 7 × 50")
    pg.text(126, 99, "изнутри корпуса, сверху вниз,", size=7.5)
    pg.text(126, 94, "шестигранник 4", size=7.5)
    G.check_box(pg, 126, 86, 74, ["корпус заподлицо с рамкой", "сзади; спереди — отступ", "цоколя по рисунку",
                                  "конфирматы без перекоса"])
    return pg


def page_wall(D, n, total):
    pg = G.Page(D, n, total, "Стена")
    hp, H = D["hpos"], D["H"]
    G.step(pg, 12, 279, "К10", prefix="", title="Крепление к стене — ДО направляющих и ящиков")
    P = D["P"]
    T, BK = P["TOP"], P["BACK"]
    car = [P[k] for k in ("BOTTOM", "TOP", "PART-1", "PART-2", "SIDE-L", "SIDE-R", "BACK")]
    ob = obl(pg, D, (16, 186, 196, 266), [(q, E.DONE, {}) for q in car], sgn=1)
    q = H["WALL-ANGLE"]["qty"]
    wa_all = D["s"]["derived"]["wall_angles"]
    wa = [a_ for a_ in wa_all if not a_.get("inside")]
    for a_ in [a_ for a_ in wa_all if a_.get("inside")]:
        cx_, cy_ = ob.p((a_["x0"] + a_["x1"]) / 2, a_["y1"], (a_["z0"] + a_["z1"]) / 2)
        pg.ax.add_patch(Circle((cx_, cy_), 3.0, fc="none", ec=BLUE, lw=1.4, ls="--", zorder=14))
        E.callout(pg, cx_, cy_, cx_ - 8, cy_ - 52, "3-й уголок: внутри левой колонны под крышкой, через ХДФ в стену [М]",
                  7.2, BLUE)
    for a_ in wa:
        pts = [ob.p(a_["x0"], a_["y0"], a_["z"]), ob.p(a_["x1"], a_["y0"], a_["z"]), ob.p(a_["x1"], a_["y1"], a_["z"]),
               ob.p(a_["x0"], a_["y1"], a_["z"])]
        pg.ax.add_patch(Polygon(pts, closed=True, fc=BLUE, ec="k", lw=0.6, zorder=13))
        cx_, cy_ = ob.p((a_["x0"] + a_["x1"]) / 2, (a_["y0"] + a_["y1"]) / 2, a_["z"])
        pg.ax.add_patch(Circle((cx_, cy_), 2.4, fc=BLUE, ec="k", lw=0.6, zorder=14))
    x, y = ob.p((wa[-1]["x0"] + wa[-1]["x1"]) / 2, wa[-1]["y1"], T["z1"])
    xs_ = " и ".join(kit13.n_((a_["x0"] + a_["x1"]) / 2) for a_ in wa)
    E.callout(pg, x, y, x - 90, y - 30, f"{len(wa)} уголка на крышке у стены: центры {xs_} от левого края [М]", 7.5, BLUE)
    if D["changer"]:
        pg.text(16, 96, "Со столиком: крышка слева занята столиком — оба верхних уголка справа от основания; слева — 3-й",
                size=7.5, color=BLUE)
        pg.text(16, 90, "уголок внутри колонны под крышкой (над верхним ящиком свободно ≈ 75, уголок 40) — проверено по "
                "модели [М].", size=7.5, color=BLUE)
    G.count_badge(pg, 16, 176, q, hp["WALL-ANGLE"], H["WALL-ANGLE"]["name"].lower() + " — изделие не выбрано (В-48)")
    pg.text(16, 166, "Крепёж в стену — по типу стены [М], проверить вытягиванием рукой [О]:", size=8.5, weight="bold")
    rows = [["бетон, кирпич полнотелый", "дюбель нейлоновый 8 + шуруп 5 × 60", "сверло Ø8 по бетону, глубина 65"],
            ["кирпич пустотелый, газобетон", "дюбель для пустотелых / газобетона 8–10", "сверлить без удара"],
            ["гипсокартон", "в профиль / закладную или дюбель «молли»", "без закладной — не крепить детскую"],
            ["дерево", "шуруп 5 × 50 без дюбеля", "засверловка Ø3"]]
    pg.table(16, 160, ["Стена", "Крепёж", "Как"], rows, [50, 74, 60], row_h=6.2, size=7.2)
    G.check_box(pg, 16, 120, 184, ["комод выставлен по уровню; уголки к крышке — 2 самореза каждый [М]",
                                   "после крепления потянуть комод на себя — не отходит от стены"])
    pg.text(16, 78, "Тип стены неизвестен до выезда (В-48) — крепёж везёт сборщик по таблице.", size=7.5, color="#444")
    pg.text(16, 72, "Уголки — на крышке снаружи; разметке направляющих внутри колонн не мешают.", size=7.5, color="#444")
    pg.ax.add_patch(Rectangle((16, 30), 184, 34, fc="#fbe3df", ec=RED, lw=1.2))
    pg.text(20, 58, "НЕ ДЛЯ РАБОЧЕЙ ВЕРСИИ: узел крепления не подтверждён (В-48)", size=8, color=RED, weight="bold")
    pg.text(20, 51, f"Набор «Стена»: уголок {q} шт. (артикул не выбран), саморезы к крышке 2 на уголок (тип и длина",
            size=7.2)
    pg.text(20, 45, "не выбраны), крепёж в стену — по таблице. Нужны: конкретный уголок и крепёж, проверка узла на", size=7.2)
    pg.text(20, 39, "образце (вытягивание) и запись результата. Таблица стен и проверка рукой этого не заменяют.", size=7.2)
    return pg


def page_changer(D, n, total):
    pg = G.Page(D, n, total, "Пеленальный столик")
    P, pos, hp = D["P"], D["cpos"], D["hpos"]
    G.step(pg, 12, 279, "С1", prefix="", title="Столик: бортики к основанию — конфирматы")
    base = P["CH-BASE"]
    rims = [P[k] for k in ("CH-BACK", "CH-L", "CH-R")]
    ob = obl(pg, D, (16, 186, 120, 266), [(base, E.DONE, {})] + [(q, E.HL, {}) for q in rims], sgn=1, zs=-1)
    hc = [h for h in D["s"]["holes"] if h["joint"].startswith("J-CH") and h["kind"] == "conf_face" and h["part"] == "CH-BASE"]
    fasten(pg, D, ob, hc, "столик 14 снизу")
    hc2 = [h for h in D["s"]["holes"] if h["joint"] in ("J-CH-BL", "J-CH-BR") and h["kind"] == "conf_face"]
    use(D, "CONF-7x50", len(hc) + len(hc2), "С1")
    pg.text(68, 180, "вид снизу на основание", size=7, ha="center", style="italic")
    G.count_badge(pg, 126, 250, len(hc), hp["CONF-7x50"], "конфирмат снизу через основание")
    G.count_badge(pg, 126, 240, len(hc2), hp["CONF-7x50"], "конфирмат: задний бортик → боковые")
    G.step(pg, 12, 166, "С2", prefix="", title="Столик — на крышку слева: 4 самореза снизу через крышку")
    mt = H_(D, "J-CH-MOUNT", "screw_face")
    T = P["TOP"]
    ob2 = obl(pg, D, (16, 80, 120, 156), [(T, E.HL, {}), (base, E.DONE, {})] + [(q, E.DONE, {}) for q in rims], sgn=1, zs=-1)
    fasten(pg, D, ob2, mt, "столик 15")
    use(D, "SCREW-4x25T", len(mt), "С2")
    pg.text(68, 74, "вид снизу: крышка комода, столик сверху", size=7, ha="center", style="italic")
    ob3 = obl(pg, D, (128, 186, 198, 226), [(T, E.DONE, {}), (base, E.HL, {})] + [(q, E.HL, {}) for q in rims], sgn=1)
    for a_ in [q_ for q_ in D["s"]["derived"]["wall_angles"] if not q_.get("inside")]:
        x, y = ob3.p((a_["x0"] + a_["x1"]) / 2, (a_["y0"] + a_["y1"]) / 2, a_["z"])
        pg.ax.add_patch(Circle((x, y), 2.2, fc=BLUE, ec="k", lw=0.6, zorder=13))
    pg.text(163, 181, "верхние уголки (синие) — вне основания;", size=6.8, ha="center", color=BLUE)
    pg.text(163, 177, "3-й — внутри левой колонны (К10)", size=6.8, ha="center", color=BLUE)
    G.count_badge(pg, 126, 140, len(mt), hp["SCREW-4x25T"], "саморез 4 × 25 · снизу")
    pg.text(126, 130, "доступ — из верхнего левого ящика", size=7.5)
    pg.text(126, 125, "(ящик снять)", size=7.5)
    G.check_box(pg, 126, 118, 74, ["матрас 700 × 500 ложится", "внутрь бортиков целиком;",
                                   "столик не качается", "проверка столика — В-106 [О]"])
    pg.text(16, 46, f"Набор «Столик»: основание, 3 бортика, конфирматы {len(hc) + len(hc2)}, саморезы 4 × 25 — {len(mt)}, "
            f"заглушки Ø14 — 4, матрас (модель не выбрана, В-106).", size=7.2)
    pg.text(16, 39, "НЕ ДЛЯ РАБОЧЕЙ ВЕРСИИ: столик не проверен на образце (В-106).", size=7.5, color=RED, weight="bold")
    G.check_box(pg, 16, 64, 184, ["комод закреплён к стене ДО установки столика",
                                  "при снятии столика — заглушки Ø14 в отверстия крепления"])
    return pg


def labels(D):
    """Наклейки: по одной на каждую изготавливаемую деталь (из модели): позиция, Л / П, наименование."""
    out = []
    for p in D["s"]["parts"]:
        if p["kind"] != "board":
            continue
        out.append((D["cpos"][p["id"]], G.side_letter(p["name"]), p["name"]))
    return sorted(out, key=lambda t: (t[0], t[1]))


def page_labels(D, n, total, chunk, k, pages):
    pg = G.Page(D, n, total, f"Наклейки {k}/{pages}")
    pg.text(12, 278, "Наклейки на детали (П16) — печатаем сами, если цех не клеит", size=11, weight="bold")
    pg.text(12, 271, "Клеить на ЗАДНИЙ торец детали (после сборки не виден); ХДФ — на тыльную сторону; фасад — изнутри. [М]",
            size=7.5)
    cw, chh = 46, 21
    for i, (pos, let, name) in enumerate(chunk):
        x = 12 + (i % 4) * (cw + 1.5)
        y = 262 - (i // 4) * (chh + 1.5)
        pg.ax.add_patch(Rectangle((x, y - chh), cw, chh, fc="white", ec="#888", lw=0.6, ls=(0, (2, 1.5))))
        pg.text(x + 2, y - 7.5, str(pos), size=16, weight="bold", va="center")
        if let:
            pg.text(x + cw - 3, y - 7.5, let, size=18, weight="bold", va="center", ha="right", color=RED)
        pg.text(x + 2, y - 15, name[:36], size=5.8, va="center")
        pg.text(x + 2, y - 19, f"ARV-NST-101 · {D['s']['options'].get('changer') == 'yes' and 'со столиком' or 'без столика'}"
                f" · {D['s']['hash'][:8]}", size=5.2, va="center", color="#666")
    return pg


def verify_counts(D):
    """Крепёж в шагах = спецификации (для деталей корпуса, цоколя, направляющих, столика; ящики — ×6 по разделу)."""
    H = D["H"]
    nd = D["nd"]
    box = {"CONF-7x50": len(E.joint_holes(D, "BOX", "conf_face")) * nd, "SCREW-4x25D": len(E.joint_holes(D, "BOT-", "screw_face")) * nd,
           "SCREW-4x25": len(E.joint_holes(D, "FRONT", "front_screw")) * nd}
    bad = []
    need = {h["fastener"] for h in D["s"]["holes"] if h.get("fastener")} | set(D["used"])
    for fid in sorted(need):
        tot = sum(n for _, n in D["used"].get(fid, [])) + box.get(fid, 0)
        if fid in H and abs(H[fid]["qty"] - tot) > 0.01:
            bad.append(f"{fid}: в шагах {tot}, в спецификации {H[fid]['qty']}")
    return bad


def write(path, opts):
    D = chest_data(opts)
    D["doc_label"] = "комод"
    G.STEP_PREFIX.update(p="Я", rails="шаги К11–К12 этой инструкции")
    # порядок (проверка 13.11): корпус и цоколь → СТЕНА → направляющие → схема ящиков → ящики Я1–Я10 → итог → столик
    makers = [page_cover, page_set_carcass, page_pre, page_housings, page_stands, page_top, page_back, page_plinth, page_wall,
              page_runners, page_drawer_map]
    makers += [("drawer", m) for m in G.PAGES]
    makers += [page_final] + ([page_changer] if D["changer"] else [])
    lab = labels(D)
    per = 44
    chunks = [lab[i:i + per] for i in range(0, len(lab), per)]
    for k, ch in enumerate(chunks, 1):
        makers.append(("labels", (lambda c=ch, kk=k: (lambda D_, n_, t_: page_labels(D_, n_, t_, c, kk, len(chunks))))()))
    total = len(makers)
    pages = []
    with PdfPages(path) as pdf:
        for i, mk in enumerate(makers, 1):
            pg = (mk[1] if isinstance(mk, tuple) else mk)(D, i, total)
            pg.fig.canvas.draw()
            pages.append(pg)
            pdf.savefig(pg.fig)
            pg.fig.savefig(str(path).replace(".pdf", f"-{i:02d}.png"), dpi=110)
    G.STEP_PREFIX.update(p="", rails="инструкция корпуса, шаги направляющих")
    res = G.verify_guide(D, pages)
    bad = verify_counts(D)
    res.append(("Крепёж в шагах = спецификации", not bad, bad[:3]))
    nboard = sum(1 for p in D["s"]["parts"] if p["kind"] == "board")
    pairs = [p["id"] for p in D["s"]["parts"] if p["kind"] == "board" and G.side_letter(p["name"]) == ""
             and any(w in p["id"] for w in ("SIDE-L", "SIDE-R", "PART-1", "PART-2", "-SL", "-SR", "CH-L", "CH-R"))]
    res.append(("Наклейки: по одной на деталь, у парных деталей есть Л / П", len(lab) == nboard and not pairs,
                f"наклеек {len(lab)}, деталей {nboard}; без Л/П: {pairs[:3]}"))
    for pg in pages:
        G.plt.close(pg.fig)
    return D, res


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "eng002_chest.pdf"
    o = {"width": "1200", "handle": "push", "changer": "yes", "body": "K110", "front": "K4069"}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        o[k] = v
    D, res = write(out, o)
    for name, ok, t in res:
        print(f"{'ok ' if ok else 'FAIL'} {name} — {t if not ok else 'да'}")
    sys.exit(0 if all(r[1] for r in res) else 1)
