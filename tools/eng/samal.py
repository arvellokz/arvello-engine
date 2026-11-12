"""ARV-NST-001 тумба «Самал» — инженерное ядро (первая корпусная модель шаблона).

R01E — инженерное предложение 29.10.2026. Внешний вид — как в каталоге (450 × 400 × 500, 2 ящика,
накладные фасады, утопленный чёрный цоколь 40, ручки-скобы). Конструкция — правила из
questions-template.md, принятые как СТАРТОВОЕ ПРЕДЛОЖЕНИЕ, не утверждены цехом:
  корпус ЛДСП 16: боковины на всю высоту корпуса, крышка и дно между боковинами;
  соединение корпуса — эксцентриковая стяжка (Häfele Minifix 15 + болт S200) + шканты 8×30 (боковины видимые);
  задняя стенка ХДФ 4 накладная на саморезах; цоколь — рамка из ЛДСП 16 на шкантах, к дну конфирматами;
  ящики — короб ЛДСП 16 белый на скрытых направляющих полного выдвижения (кандидат: система LW−42, NL 350);
  фасады ЛДСП 18 в декоре корпуса, кромка ABS 2 по контуру; ручка 128 мм.
Всё, что зависит от артикула (размеры корпуса эксцентрика, присадка направляющих, длины винтов),
записано как кандидат и закрыто вопросами В-n (kit_samal.QUESTIONS). manufacturing_allowed = False.

Система координат изделия: x — ширина слева направо (вид спереди), y — глубина от лицевой
плоскости фасадов (y = 0) назад, z — высота от пола. База A — левый передний нижний угол корпуса.

Отверстие: {id, part, joint, kind, x, y, z (точка входа на поверхности детали), dir ('+x' … '-z' —
направление сверления в материал), d, depth, through, cs (зенковка), fastener, note}.
"""
from __future__ import annotations

import math

from .core import Design, EPart, Hardware

SKU = "ARV-NST-001"
REVS = {
    "R01E": "инженерное предложение R01E (корпус, присадка, крепёж); вид как в каталоге; конструкция не утверждена, не для изготовления",
    "R02E": "R01E + выбранная фурнитура: Blum TANDEM plus BLUMOTION 560H, Häfele Minifix 15 / S200; короб по документации Blum; "
            "не для изготовления до закрытия вопросов листа 11",
}
# Что меняется по ревизиям (R02E — замечания владельца 29.10, вечер)
REVP = {
    "R01E": {"box_lift": 3, "box_h": 150, "stem_depth": 11, "same_white": False},
    # Зазор 14 под коробом (верхняя пласть дна корпуса → нижняя кромка боковины ящика), верхний ≥ 7, высота ≤ проём − 21 —
    # ПРЕДПОЛОЖЕНИЕ по каталогу Blum 563H, для 560H не подтверждено (В-4б). Короб 140 — чтобы винты ручек были выше короба.
    # Häfele S200 262.27.679: резьба 11 → отверстие Ø5 глубиной 12 (остаток 4).
    # R02E — по документам (29.10, ночь): Blum TANDEM RU v4 стр. 22 «Необходимое пространство в корпусе»:
    #   низ профиля → ось самореза крепления 37*; низ дна ящика → низ профиля (нижняя граница) min 27,5*;
    #   утопление дна 12–15 (принято 13) → низ боковины ящика на 14,5 выше низа профиля. Профиль на 1 мм выше дна корпуса.
    #   Häfele стр. 301: S200 262.27.679 — резьба 11 под Ø5 → отверстие Ø5 × 12; гильза Ø7,5 → отверстие в торце Ø8
    #   (стр. 294: Ø7 или Ø8 по болту), глубина 32 = B 24 + радиус корпуса 7,5 + 0,5.
    "R02E": {"box_lift": 1 + 27.5 - 13, "box_h": 140, "stem_depth": 12, "same_white": True, "bolt_depth": 32,
             "runner_gap": 1, "blum_under_bottom": 27.5, "blum_screw_axis": 37,
             "blum_screws": (19, 37, 69, 165, 261)},
}
SLIDE = {"system": "Blum TANDEM plus BLUMOTION 560H, 30 кг, полное выдвижение", "article_tpl": "560H{NL:04d}B",
         "lock": "T51.1700.04 (пара левый/правый)", "screw": "саморез Ø4 × 15 (Blum) или системный винт Ø6 × 14,5 661.1450.HG",
         "jig": "кондуктор Blum T65.1000.02", "front_screw_from_edge": 37, "inner_w": "LW − 42 (+0 / −1,5)", "skl": "NL − 10",
         "bottom_clear": 14, "top_clear_min": 7, "height_minus": 21}
ECC_ART = {"housing": "Häfele Minifix 15, корпус 262.26.033 (без бортика) для плиты 16: Ø15, глубина 12,5 +0,5, A = 8",
           "bolt": "Häfele S200 262.27.679: B = 24, ввинчивание Ø5, резьба 11"}

# ---------------------------------------------------------------- параметры (предложение)
W, H, D = 450, 500, 400          # габарит корпуса с фасадами
T, TF, TB = 16, 18, 4            # корпус ЛДСП 16, фасад ЛДСП 18, задняя стенка ХДФ 4
PL = 40                          # высота цоколя
PL_FRONT, PL_SIDE, PL_BACK = 40, 20, 16     # отступы цоколя от лица фасадов / боковин / задней кромки корпуса
GAP = 3                          # зазоры фасадов
N_DR = 2
SLIDE_SIDE = 5                   # зазор короб — боковина на сторону (система LW − 42 при бортах 16)
SLIDE_SERIES = (250, 270, 300, 350, 400, 450, 500)
BOX_H = 150
BOX_RECESS = 13                  # дно ящика поднято от низа боковин (под направляющую)
BOX_LIFT = 3                     # низ нижнего короба над дном корпуса
HANDLE_CC, HANDLE_FROM_TOP = 128, 45
ECC = {"housing_d": 15, "housing_depth": 12.5, "B": 24, "bolt_d": 8, "bolt_depth": 34, "stem_d": 5, "stem_depth": 11}
DOWEL = {"d": 8, "L": 30, "face_depth": 12, "edge_depth": 20}
CONF = {"d_face": 7, "d_edge": 5, "L": 50, "edge_depth": 36}
FRONT_SCREW = {"d": 4.5, "L": 25}
BACK_SCREW = {"pilot_d": 2.5, "pilot_depth": 12, "L": 16, "step": 150, "end": 30}
EDGE = {"ABS2": 2.0, "PVC04": 0.4}
DENSITY = 650                    # ЛДСП, кг/м³ (ориентир)

BLOCKERS = ["BOARD_AND_DECOR_SUPPLY", "EDGE_AND_BLANK_ALLOWANCE", "CAM_CONNECTOR_ARTICLE", "SLIDE_SYSTEM_AND_BOX",
            "HANDLE_ARTICLE_AND_SCREW", "BACK_PANEL_METHOD", "PLINTH_METHOD", "SHOP_TOLERANCES", "PROTOTYPE_TEST"]


def _edge_len(p, face):
    sx, sy, sz = p.x1 - p.x0, p.y1 - p.y0, p.z1 - p.z0
    return {"-x": (sy, sz), "+x": (sy, sz), "-y": (sx, sz), "+y": (sx, sz), "-z": (sx, sy), "+z": (sx, sy)}[face]


def _round_slide(depth):
    ok = [s for s in SLIDE_SERIES if s <= depth - 10]
    return max(ok)


def build(options: dict, rev: str = "R02E") -> Design:
    if rev not in REVS:
        raise ValueError(f"нет ревизии {rev}")
    color = options.get("color", "W")
    if color not in ("W", "C", "O", "G"):
        raise ValueError("цвет W / C / O / G")
    grain = color == "O"
    rp = REVP[rev]
    BOX_H, BOX_LIFT = rp["box_h"], rp["box_lift"]
    inner_fin = color if (rp["same_white"] and color == "W") else "INNER"   # белое исполнение: короба из той же плиты
    P, holes, joints = [], [], {}

    def part(pid, name, x0, y0, z0, x1, y1, z1, mat, fin, group, unit, edges=None, grain_axis="", pos=None, note=""):
        e = EPart(pid, name, "board", x0, y0, z0, x1, y1, z1, mat, fin, group, unit=unit, note=note)
        e.edges = edges or {}
        e.grain = grain_axis if (grain and fin == color) else ""
        e.pos = pos
        P.append(e)
        return e

    yc0, yc1 = TF, D - TB                    # корпус по глубине
    Dc = yc1 - yc0
    zc0 = PL
    # ---- корпус
    part("SIDE-L", "Боковина левая", 0, yc0, zc0, T, yc1, H, "LDSP16", color, "carcass", "Боковина левая",
         {"-y": "ABS2", "+z": "ABS2", "-z": "PVC04"}, "z", 1)
    part("SIDE-R", "Боковина правая", W - T, yc0, zc0, W, yc1, H, "LDSP16", color, "carcass", "Боковина правая",
         {"-y": "ABS2", "+z": "ABS2", "-z": "PVC04"}, "z", 2)
    part("TOP", "Крышка", T, yc0, H - T, W - T, yc1, H, "LDSP16", color, "carcass", "Крышка", {"-y": "ABS2"}, "x", 3)
    part("BOTTOM", "Дно", T, yc0, zc0, W - T, yc1, zc0 + T, "LDSP16", color, "carcass", "Дно", {"-y": "PVC04"}, "x", 4)
    part("BACK", "Задняя стенка", 2, yc1, zc0 + 2, W - 2, D, H - 2, "HDF4", "INNER", "carcass", "Задняя стенка", pos=5)
    # ---- цоколь (рамка)
    px0, px1 = PL_SIDE, W - PL_SIDE
    py0, py1 = PL_FRONT, yc1 - PL_BACK
    part("PL-F", "Цоколь продольный", px0, py0, 0, px1, py0 + T, PL, "LDSP16", "black", "carcass", "Цоколь продольный",
         {"-x": "PVC04", "+x": "PVC04"}, pos=6)
    part("PL-B", "Цоколь продольный", px0, py1 - T, 0, px1, py1, PL, "LDSP16", "black", "carcass", "Цоколь продольный",
         {"-x": "PVC04", "+x": "PVC04"}, pos=6)
    part("PL-SL", "Цоколь боковой", px0, py0 + T, 0, px0 + T, py1 - T, PL, "LDSP16", "black", "carcass", "Цоколь боковой", pos=7)
    part("PL-SR", "Цоколь боковой", px1 - T, py0 + T, 0, px1, py1 - T, PL, "LDSP16", "black", "carcass", "Цоколь боковой", pos=7)
    # ---- фасады
    zf0, zf1 = zc0 + GAP / 2, H - GAP / 2
    fh = (zf1 - zf0 - GAP * (N_DR - 1)) / N_DR
    fronts = []
    for i in range(N_DR):
        a = zf0 + i * (fh + GAP)
        fronts.append(part(f"FRONT-{i + 1}", "Фасад ящика", GAP / 2, 0, a, W - GAP / 2, TF, a + fh, "LDSP18", color,
                           "fronts", "Фасад ящика", {"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"}, "x", 8))
    # ---- ящики
    LW = W - 2 * T
    NL = _round_slide(Dc)
    bw = LW - 2 * SLIDE_SIDE
    bl = NL - 10
    bx0, bx1 = T + SLIDE_SIDE, W - T - SLIDE_SIDE
    by0, by1 = yc0, yc0 + bl
    boxes = []
    for i in range(N_DR):
        z0 = zc0 + T + BOX_LIFT + (fronts[i].z0 - fronts[0].z0)
        z1 = z0 + BOX_H
        k = f"BOX{i + 1}"
        sl = part(f"{k}-SL", "Боковина ящика", bx0, by0, z0, bx0 + T, by1, z1, "LDSP16", inner_fin, "interior", "Боковина ящика",
                  {"+z": "PVC04"}, pos=9)
        sr = part(f"{k}-SR", "Боковина ящика", bx1 - T, by0, z0, bx1, by1, z1, "LDSP16", inner_fin, "interior", "Боковина ящика",
                  {"+z": "PVC04"}, pos=9)
        fp = part(f"{k}-F", "Стенка ящика передняя", bx0 + T, by0, z0, bx1 - T, by0 + T, z1, "LDSP16", inner_fin, "interior",
                  "Стенка ящика передняя", {"+z": "PVC04"}, pos=10)
        bp = part(f"{k}-B", "Стенка ящика задняя", bx0 + T, by1 - T, z0, bx1 - T, by1, z1, "LDSP16", inner_fin, "interior",
                  "Стенка ящика задняя", {"+z": "PVC04"}, pos=11)
        bt = part(f"{k}-BOT", "Дно ящика", bx0 + T, by0 + T, z0 + BOX_RECESS, bx1 - T, by1 - T, z0 + BOX_RECESS + T, "LDSP16",
                  inner_fin, "interior", "Дно ящика", pos=12)
        boxes.append((sl, sr, fp, bp, bt))
    # ---- ручки (покупные; в 3D — планка и две стойки)
    hz = []
    for i, f in enumerate(fronts):
        zc = f.z1 - HANDLE_FROM_TOP
        hz.append(zc)
        xc = W / 2
        P.append(EPart(f"HANDLE-{i + 1}", "Ручка-скоба 128", "buy", xc - 80, -26, zc - 6, xc + 80, -14, zc + 6, "HANDLE-128",
                       "black", "fronts", unit="Ручка"))
        for s, xx in (("a", xc - HANDLE_CC / 2), ("b", xc + HANDLE_CC / 2)):
            P.append(EPart(f"HANDLE-{i + 1}{s}", "Стойка ручки", "buy_part", xx - 5, -14, zc - 5, xx + 5, 0, zc + 5, "HANDLE-128",
                           "black", "fronts", unit="Ручка"))

    # ---------------------------------------------------------------- отверстия
    def hole(pid, joint, kind, x, y, z, dr, d, depth, fastener=None, through=False, cs=False, note=""):
        h = {"id": f"H{len(holes) + 1:03d}", "part": pid, "joint": joint, "kind": kind, "x": round(x, 2), "y": round(y, 2),
             "z": round(z, 2), "dir": dr, "d": d, "depth": depth, "through": through, "cs": cs, "fastener": fastener, "note": note}
        holes.append(h)
        joints.setdefault(joint, []).append(h["id"])
        return h

    # корпус: боковина ↔ крышка/дно — эксцентрик + шканты
    for side, xf, into_side, into_board, sgn in (("SIDE-L", T, "-x", "+x", 1), ("SIDE-R", W - T, "+x", "-x", -1)):
        for board, zc, hdir, hz_face in (("TOP", H - T / 2, "+z", H - T), ("BOTTOM", zc0 + T / 2, "-z", zc0 + T)):
            j = f"J-{side[-1]}-{board}"
            for yl in (37, Dc - 37):
                y = yc0 + yl
                hole(side, j, "ecc_stem", xf, y, zc, into_side, ECC["stem_d"], rp["stem_depth"], "ECC-15")
                hole(board, j, "ecc_bolt", xf, y, zc, into_board, ECC["bolt_d"], rp.get("bolt_depth", ECC["bolt_depth"]))
                hole(board, j, "ecc_housing", xf + sgn * ECC["B"], y, hz_face, hdir, ECC["housing_d"], ECC["housing_depth"])
            for yl in (37 + 32, Dc - 37 - 32):
                y = yc0 + yl
                hole(side, j, "dowel_face", xf, y, zc, into_side, DOWEL["d"], DOWEL["face_depth"], "DOWEL-8x30")
                hole(board, j, "dowel_edge", xf, y, zc, into_board, DOWEL["d"], DOWEL["edge_depth"])
    # цоколь: углы на шкантах, рамка к дну конфирматами через дно
    for strip, yface, dface, dend, end_y in (("PL-F", py0 + T, "-y", "+y", py0 + T), ("PL-B", py1 - T, "+y", "-y", py1 - T)):
        for side, xc in (("PL-SL", px0 + T / 2), ("PL-SR", px1 - T / 2)):
            j = f"J-{strip}-{side}"
            for zz in (12, PL - 12):
                hole(strip, j, "dowel_face", xc, yface, zz, dface, DOWEL["d"], DOWEL["face_depth"], "DOWEL-8x30")
                hole(side, j, "dowel_edge", xc, end_y, zz, dend, DOWEL["d"], DOWEL["edge_depth"])
    pts = [("PL-F", x, py0 + T / 2) for x in (70, W / 2, W - 70)] + [("PL-B", x, py1 - T / 2) for x in (70, W / 2, W - 70)] + \
          [("PL-SL", px0 + T / 2, (py0 + py1) / 2), ("PL-SR", px1 - T / 2, (py0 + py1) / 2)]
    for strip, x, y in pts:
        j = f"J-BOTTOM-{strip}"
        hole("BOTTOM", j, "conf_face", x, y, zc0 + T, "-z", CONF["d_face"], T, "CONF-7x50", through=True, cs=True)
        hole(strip, j, "conf_edge", x, y, zc0, "-z", CONF["d_edge"], CONF["edge_depth"])
    # задняя стенка: саморезы в торцы корпуса (засверловка в торец; в ХДФ без отверстий)
    span = lambda a, b: [round(a + (b - a) * k / max(1, math.ceil((b - a) / BACK_SCREW["step"])))
                         for k in range(math.ceil((b - a) / BACK_SCREW["step"]) + 1)]     # целые мм для разметки
    for side, x in (("SIDE-L", T / 2), ("SIDE-R", W - T / 2)):
        for z in span(zc0 + BACK_SCREW["end"], H - BACK_SCREW["end"]):
            hole(side, "J-BACK", "back_pilot", x, yc1, z, "-y", BACK_SCREW["pilot_d"], BACK_SCREW["pilot_depth"], "SCREW-3.5x16")
    for board, z in (("TOP", H - T / 2), ("BOTTOM", zc0 + T / 2)):
        for x in span(T + 44, W - T - 44):
            hole(board, "J-BACK", "back_pilot", x, yc1, z, "-y", BACK_SCREW["pilot_d"], BACK_SCREW["pilot_depth"], "SCREW-3.5x16")
    # профиль направляющей: точки крепления саморезами Ø4 × 15 на внутренней пласти боковин корпуса
    # (Blum стр. 39, NL 300–380, верхний ряд: A — ○ и ◐ = 19, 37, 69, 165, 261 от передней кромки; стр. 22 — ось на 37 выше низа профиля)
    if "blum_screws" in rp:
        for sl_, *_ in boxes:
            z_axis = sl_.z0 - (rp["blum_under_bottom"] - BOX_RECESS) + rp["blum_screw_axis"]
            for side, xf, dr in (("SIDE-L", T, "-x"), ("SIDE-R", W - T, "+x")):
                for yy in rp["blum_screws"]:
                    hole(side, f"J-RUNNER-{side[-1]}-{sl_.id[3]}", "runner_mark", xf, yc0 + yy, z_axis, dr, 4, 0, "SLIDE-SCREW",
                         note="разметка, без сверления")
    # ящики
    for i, (sl, sr, fp, bp, bt) in enumerate(boxes):
        n = i + 1
        z0 = sl.z0
        for side, xo, xi, d_in, d_edge in ((sl, sl.x0, sl.x1, "+x", "+x"), (sr, sr.x1, sr.x0, "-x", "-x")):
            for panel in (fp, bp):
                yc = (panel.y0 + panel.y1) / 2
                j = f"J-BOX{n}-{side.id[-2:]}-{panel.id[-1]}"
                for zz in (40, BOX_H - 35):
                    hole(side.id, j, "conf_face", xo, yc, z0 + zz, d_in, CONF["d_face"], T, "CONF-7x50", through=True, cs=True)
                    hole(panel.id, j, "conf_edge", xi, yc, z0 + zz, d_edge, CONF["d_edge"], CONF["edge_depth"])
            j = f"J-BOX{n}-{side.id[-2:]}-BOT"
            for yl in (76, bl - 76):
                hole(side.id, j, "conf_face", xo, by0 + yl, bt.z0 + T / 2, d_in, CONF["d_face"], T, "CONF-7x50", through=True, cs=True)
                hole(bt.id, j, "conf_edge", xi, by0 + yl, bt.z0 + T / 2, d_edge, CONF["d_edge"], CONF["edge_depth"])
        for panel, yo, yi, dr in ((fp, fp.y0, fp.y1, "+y"), (bp, bp.y1, bp.y0, "-y")):
            j = f"J-BOX{n}-{panel.id[-1]}-BOT"
            for x in (bx0 + T + 80, bx1 - T - 80):
                hole(panel.id, j, "conf_face", x, yo, bt.z0 + T / 2, dr, CONF["d_face"], T, "CONF-7x50", through=True, cs=True)
                hole(bt.id, j, "conf_edge", x, yi, bt.z0 + T / 2, dr, CONF["d_edge"], CONF["edge_depth"])
        # фасад ↔ передняя стенка: саморезы изнутри короба
        j = f"J-FRONT{n}-BOX{n}"
        for x in (bx0 + T + 40, bx1 - T - 40):
            for zz in (55, 125):
                hole(fp.id, j, "front_screw", x, fp.y1, z0 + zz, "-y", FRONT_SCREW["d"], T, "SCREW-4x25", through=True, cs=True,
                     note="зенковка изнутри короба; в фасад — без засверловки, вход 9")
        # ручка: сквозные Ø5 в фасаде
        j = f"J-HANDLE{n}"
        for x in (W / 2 - HANDLE_CC / 2, W / 2 + HANDLE_CC / 2):
            hole(f"FRONT-{n}", j, "handle", x, 0, hz[i], "+y", 5, TF, "SCREW-M4x22", through=True)

    # ---------------------------------------------------------------- кромка
    for p in P:
        if p.kind == "board":
            p.edge_m = round(sum(max(_edge_len(p, f)) for f in p.edges) / 1000, 3)
    hw_count = {}
    for h in holes:
        if h["fastener"]:
            hw_count[h["fastener"]] = hw_count.get(h["fastener"], 0) + 1
    hw_count["SCREW-M4x22"] = hw_count.get("SCREW-M4x22", 0)
    d = Design(SKU, rev, REVS[rev], {"color": color}, {}, P, holes=holes)
    if rev == "R01E":
        d.hardware = [
            Hardware("SLIDES", "Направляющие скрытого монтажа (пара)", f"полное выдвижение, доводчик, NL {NL} (В-4)",
                     N_DR, "кандидат", "артикул и присадка — по системе", "компл"),
            Hardware("ECC-15", "Стяжка эксцентриковая Ø15 со штоком", "кандидат Minifix 15 / аналог (В-3)", hw_count["ECC-15"],
                     "кандидат", "", "компл"),
        ]
    else:
        n_lock_screw = 2 * 2 * N_DR
        d.hardware = [
            Hardware("SLIDES", "Направляющая TANDEM plus BLUMOTION (пара Л/П)", f"Blum 560H{NL * 10:04d}B, NL {NL}, 30 кг (Blum стр. 20)",
                     N_DR, "по документу", "крепёж и замки в комплект не входят", "компл"),
            Hardware("SLIDE-LOCK", "Замок ящика (пара Л/П)", "Blum T51.1700.04", N_DR, "выбрано", "", "компл"),
            Hardware("SLIDE-SCREW", "Саморез крепления профиля", "Ø4 × 15 (Blum стр. 39, тип A): 5 на профиль — 19, 37, 69, 165, 261",
                     hw_count["SLIDE-SCREW"], "по документу", "", "шт"),
            Hardware("LOCK-SCREW", "Саморез крепления замка", "2 на замок (Blum стр. 20, рис.); тип — по поставке Blum",
                     n_lock_screw, "по рисунку", "тип самореза в документе не указан", "шт"),
            Hardware("ECC-15", "Корпус эксцентрика Minifix 15", "Häfele 262.26.033 (bright), плита 16: A 8,0, X 12,5 +0,5 (стр. 294)",
                     hw_count["ECC-15"], "по документу", "лист 2014 г. — сверить с поставкой", "шт"),
            Hardware("ECC-BOLT", "Болт стяжки S200", "Häfele 262.27.679 (galvanized), B 24, резьба 11 под Ø5 (стр. 301)",
                     hw_count["ECC-15"], "по документу", "лист 2014 г. — сверить с поставкой", "шт"),
        ]
    d.hardware += [
        Hardware("HANDLE-128", "Ручка-скоба", f"межосевое {HANDLE_CC}, чёрная матовая (В-5)", N_DR, "кандидат", "", "шт"),
        Hardware("SCREW-M4x22", "Винт ручки M4 × 22", "в комплекте ручки (В-5)", hw_count["SCREW-M4x22"], "кандидат", "", "шт"),
        Hardware("DOWEL-8x30", "Шкант 8 × 30", "берёза, рифлёный", hw_count["DOWEL-8x30"], "типовой", "", "шт"),
        Hardware("CONF-7x50", "Конфирмат 7 × 50", "под шестигранник 4", hw_count["CONF-7x50"], "типовой", "", "шт"),
        Hardware("SCREW-4x25", "Саморез 4 × 25", "потай, по ЛДСП (В-9)", hw_count["SCREW-4x25"], "типовой", "", "шт"),
        Hardware("SCREW-3.5x16", "Саморез 3,5 × 16", "с прессшайбой, для ХДФ (В-6)", hw_count["SCREW-3.5x16"], "типовой", "", "шт"),
        Hardware("GLUE-PVA", "Клей ПВА D3", "для шкантов цоколя", 0.05, "типовой", "", "кг"),
    ]
    d.blockers = list(BLOCKERS)
    boards = [p for p in P if p.kind == "board"]
    mass = sum((p.x1 - p.x0) * (p.y1 - p.y0) * (p.z1 - p.z0) for p in boards if p.material.startswith("LDSP")) / 1e9 * DENSITY + \
        sum((p.x1 - p.x0) * (p.z1 - p.z0) * TB for p in boards if p.material == "HDF4") / 1e9 * 850
    d.derived = {"width": W, "depth": D, "height": H, "carcass_depth": Dc, "LW": LW, "NL": NL, "box_w": bw, "box_l": bl,
                 "box_h": BOX_H, "front_h": round(fh, 2), "handle_cc": HANDLE_CC, "handle_from_top": HANDLE_FROM_TOP, "plinth": PL, "handle_z": hz, "mass_kg": round(mass, 1),
                 "holes": len(holes), "edge_abs2_m": 0, "edge_04_m": 0, "slide_side": SLIDE_SIDE,
                 "box_z0": [b[0].z0 for b in boxes], "box_inner_w": bw - 2 * T,
                 "bottom_clear": boxes[0][0].z0 - (zc0 + T), "top_clear": (H - T) - boxes[-1][0].z1,
                 "interior_finish": inner_fin, "grain": grain, "rev_params": {k: v for k, v in rp.items()},
                 "runner_bottom": [b[0].z0 - (rp.get("blum_under_bottom", 0) - BOX_RECESS) if "blum_under_bottom" in rp else None
                                   for b in boxes], "box_recess": BOX_RECESS}
    for p in boards:
        for face, typ in p.edges.items():
            key = "edge_abs2_m" if typ == "ABS2" else "edge_04_m"
            d.derived[key] = round(d.derived[key] + max(_edge_len(p, face)) / 1000, 3)
    d.derived["parts_ext"] = {p.id: {"edges": p.edges, "grain": p.grain, "pos": p.pos} for p in boards}
    d.derived["joints"] = joints
    d.ops = {"board_cut": len(boards), "edging_m": round(d.derived["edge_abs2_m"] + d.derived["edge_04_m"], 2),
             "drill_hole": len(holes),
             "assembly": 1}
    d.checks = [
        ("Ширина = 2 боковины + крышка", W, round(2 * T + (P[2].x1 - P[2].x0))),
        ("Высота = цоколь + боковина", H, round(PL + (P[0].z1 - P[0].z0))),
        ("Глубина = фасад + корпус + ХДФ", D, round(TF + Dc + TB)),
        ("Фасады + зазоры = высота корпуса", H - PL, round(N_DR * fh + GAP * N_DR, 3)),
        ("Короб = LW − 2 × зазор", LW - 2 * SLIDE_SIDE, round(bx1 - bx0)),
        ("Длина короба = NL − 10", NL - 10, round(by1 - by0)),
    ]
    if rev == "R01E":
        d.warnings = [
            "Конструкция — инженерное предложение R01E: соединения, присадка и фурнитура не утверждены цехом; выпуск закрыт.",
            f"Направляющие: система не выбрана (кандидат NL {NL}, внутренняя ширина короба LW − 42) — присадка по шаблону (В-4).",
            "Эксцентрики: Ø15 × 12,5 и B = 24 — кандидат Minifix 15 для плиты 16 (В-3).",
        ]
    else:
        d.warnings = [
            "R02E: узлы Blum 560H и Häfele Minifix сверены с чертежами производителей (Blum TANDEM RU v4 стр. 20, 22, 39; "
            "Häfele CFCD 2014 стр. 294, 301); выпуск закрыт до пробной сборки (В-12) и вопросов В-1, В-2, В-5, В-10.",
            f"Короб: NL − 10 = {bl}; внутренняя ширина LW − 42 = {bw - 2 * T}; дно поднято на 13; низ дна на 27,5 выше низа профиля; "
            "ось крепления профиля на 37 выше его низа.",
            "Отверстие под крючок в задней стенке (Ø6 × 10) и места замков — по шаблону Blum T65.1000.02 (стр. 22).",
        ]
        d.blockers = ["BOARD_AND_DECOR_SUPPLY", "EDGE_AND_BLANK_ALLOWANCE", "HANDLE_ARTICLE_AND_SCREW", "SHOP_TOLERANCES",
                      "PROTOTYPE_ASSEMBLY_AND_TEST", "SUPPLY_MATCHES_2014_HAFELE_SHEETS"]
    d.notes = ["Корпус ЛДСП 16, фасады ЛДСП 18 в декоре корпуса; короба ящиков ЛДСП 16 белая (в белом исполнении R02E — "
               "та же плита, что корпус); цоколь ЛДСП 16 чёрная.",
               "Задняя стенка ХДФ 4 накладная, отступ 2 мм от наружных граней корпуса."]
    return d


def palette(mats):
    black, inner = (34, 34, 36), (236, 234, 229)

    def f(p):
        fin = p["finish"]
        if fin in mats["colors"]:
            return mats["colors"][fin]["rgb"]
        return black if fin == "black" else inner
    return f
