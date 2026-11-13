"""Инженерные ядра R01E для оставшихся 15 моделей каталога: кровати, шкафы и прихожие, ТВ-зона, стеллаж, бенч,
офисный шкаф. Вид — как в каталоге (builders.py, builders_more.py); конструкция — правила «Самал» R02E и «Опора» R03E;
отличия от каталога — в derived["kdec"] (вопрос В-43), кандидаты фурнитуры — В-44 … В-51.
"""
from __future__ import annotations

from .cab import GAP, T, TB, TF, Build, FASTENERS
from .models13 import REV, STATUS, MODELS, _check, _fronts_col, _inner

FASTENERS.update({
    "WSCREW-6x140": ("Саморез по дереву 6 × 140", "потай, жёлтый цинк", "типовой", "", "шт"),
    "STAY-SCREW": ("Саморез ограничителя откидного фасада", "в комплекте (кандидат)", "кандидат", "В-49", "шт"),
})


def _hang_rod(b, S1, S2, z, y, spec="штанга овальная 30 × 15, хром", tag=""):
    """Штанга между вертикалями S1 (слева) и S2 (справа): 2 держателя по 2 самореза."""
    for S, xf, dr in ((S1, S1.x1, "-x"), (S2, S2.x0, "+x")):
        for dy in (-12, 12):
            b.hole(S.id, f"J-ROD-{S1.id}{tag}", "pilot", xf, y + dy, z + 15, dr, 2.5, 10, "ROD-SCREW",
                   note="штангодержатель торцевой")
    b.part(f"ROD-{S1.id}{tag}", "Штанга", S1.x1, y - 7.5, z, S2.x0, y + 7.5, z + 30, "ROD", "steel", "interior", kind="buy")
    b.buy("ROD", "Штанга гардеробная", f"{spec}, раскрой по месту", 1, "типовой", "", "шт")
    b.buy("ROD-HOLDER", "Штангодержатель торцевой", "хром, пара на штангу", 2, "типовой", "", "шт")


def _tie_mez(b, top, bot, x0, x1, yc):
    b.screws_into(top, bot, "+z", "x", [x0 + 100, x1 - 100], "SCREW-4x30", f"J-{top.id}-MEZ", pilot=(3, 12), at=yc)


def _anti_tip(b, n=2):
    b.buy("WALL-ANGLE", "Уголок крепления к стене (от опрокидывания)", "сталь, 2 самореза в крышку + дюбель (кандидат)", n,
          "кандидат", "В-48")
    b.derived.setdefault("kq", []).append("В-48")


def _kq(b, *ids):
    b.derived.setdefault("kq", [])
    for q in ids:
        if q not in b.derived["kq"]:
            b.derived["kq"].append(q)


# =============================================================================== шкафы на секциях 600
def _sections(b, W, H, PL, top, D, color, pattern, handles, push=False, inner_drawers=False):
    """Секции 600 + антресоли до H. pattern — H (штанга), S (полки), D (две штанги)."""
    n = len(pattern)
    for i, kind in enumerate(pattern):
        x0 = i * 600
        pre = f"S{i + 1}-"
        yc0, yc1 = TF, D - TB
        if kind == "S":
            zs = [PL + 16 + 480 + k * 340 for k in range(5) if PL + 16 + 480 + k * 340 < top - 300]
        else:
            zs = []
        zs.append(top - 300)
        sh = [(x0 + T, x0 + 600 - T, z, "Полка", "+") for z in sorted(set(zs))]
        c = b.carcass(pre, x0, x0 + 600, PL, top, yc0, yc1, color, shelves=sh, label=f"секция {i + 1}")
        b.plinth(pre, c, PL, front=50, side=20, back=16, fin=color)
        if kind in "HD":
            _hang_rod(b, c["L"], c["R"], top - 380, (yc0 + yc1) / 2)
        if kind == "D":
            _hang_rod(b, c["L"], c["R"], 1000, (yc0 + yc1) / 2, tag="-2")
        if kind == "S" and inner_drawers:
            fl = c["BOT"].z1
            ceil = c["shelves"][0].z0
            fr = [(x0 + T + 26, x0 + 600 - T - 26, fl + 4 + k * 222, fl + 4 + k * 222 + 216) for k in range(2)]
            b.drawers(pre, c, c["L"], c["R"], fl, ceil, fr, "INNER", "INNER", handle=None, front_mat="LDSP16", front_t=16,
                      front_unit="Передняя панель внутреннего ящика", setback=60, box_max=150,
                      front_edges={"-x": "PVC04", "+x": "PVC04", "-z": "PVC04", "+z": "ABS2"})
        m = b.carcass(pre + "M-", x0, x0 + 600, top, H, yc0, yc1, color, label=f"антресоль {i + 1}")
        _tie_mez(b, c["TOP"], m["BOT"], x0, x0 + 600, (yc0 + yc1) / 2)
        left = i % 2 == 0
        side = c["L"] if left else c["R"]
        hd = None if push else "v320"
        b.doors(pre, c, [side], [(x0 + GAP / 2, x0 + 600 - GAP / 2, PL + GAP / 2, top - GAP / 2)], color, handle=hd,
                hz_from_top=(top - PL) - (1100 - PL), lefts=[left])
        ms = m["L"] if left else m["R"]
        b.doors(pre + "M-", m, [ms], [(x0 + GAP / 2, x0 + 600 - GAP / 2, top + GAP / 2, H - GAP / 2)], color,
                handle=None if push else "bar128", hz_from_top=(H - top) - 60, lefts=[left])
    if push:
        b.buy("PUSH-LATCH", "Толкатель TIP-ON для двери без ручки", "кандидат Blum TIP-ON 956A1004 + планка", 2 * n,
              "кандидат", "В-20")
    if n > 1:
        b.buy("TIE", "Стяжка межсекционная Ø5", "4 на стык секций + 2 на антресоль (сверлить по месту)", 6 * (n - 1),
              "кандидат", "В-41")
    _anti_tip(b, n)


def wardrobe_hinged(o):
    W, color = int(o["width"]), o["color"]
    H, PL, top, D = 2400, 80, 1980, 580
    b = Build("ARV-WRD-001", REV, STATUS, {"width": W, "color": color})
    pattern = "HSD"[:W // 600] if W // 600 <= 3 else "HSD" * 2
    _sections(b, W, H, PL, top, D, color, pattern, handles=True)
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = число секций × 600", W, 600 * len(pattern))
    _check(b, "Высота = цоколь + секция + антресоль", H, PL + (top - PL) + (H - top))
    b.notes += ["Шкаф из секций 600: корпус ЛДСП 16 на Minifix, антресоль — отдельный корпус на саморезах 4 × 30 через крышку.",
                "Двери 1896 — 4 петли (кандидат); ручки вертикальные 320 у свободной кромки."]
    _kq(b, "В-41")
    return b


def wardrobe_flush(o):
    W, H, color = int(o["width"]), int(o["height"]), o["color"]
    PL, D = 80, 600
    top = 2040 if H <= 2400 else 2280
    b = Build("ARV-WRD-004", REV, STATUS, {"width": W, "height": H, "color": color})
    pattern = {2: "HS", 3: "HSD", 4: "HSSD"}[W // 600]
    _sections(b, W, H, PL, top, D, color, pattern, handles=False, push=True, inner_drawers=True)
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Высота = цоколь + секция + антресоль", H, PL + (top - PL) + (H - top))
    b.notes += ["Без ручек: двери на петлях без пружины + толкатели TIP-ON (кандидат, В-20).",
                "Внутренние ящики Blum 560H за дверью: отступ 60 от кромки боковины (место под монтажные планки петель); "
                "передняя панель ЛДСП 16 белая, уже проёма на 26 с каждой стороны."]
    _kq(b, "В-41")
    if H > 2400:
        b.warnings.append("Высота 2700: проверить подъём в помещение (диагональ секции ≈ 2390) — собирать на месте.")
    return b


def office_cabinet(o):
    color, typ = o["color"], o["type"]
    W, H, D, PL = 800, 2000, 400, 60
    b = Build("ARV-OFF-006", REV, STATUS, {"type": typ, "color": color})
    sh = [(T, W - T, z, "Полка", "+") for z in (430, 800, 1170, 1540)]
    c = b.carcass("", 0, W, PL, H, TF, D - TB, color, shelves=sh, label="корпус")
    b.plinth("", c, PL, front=50, side=20, back=16, fin=color)
    zt = H if typ == "closed" else 800
    fr = [(GAP / 2, W / 2 - GAP / 2, PL + GAP / 2, zt - GAP / 2), (W / 2 + GAP / 2, W - GAP / 2, PL + GAP / 2, zt - GAP / 2)]
    if typ == "closed":
        b.doors("", c, [c["L"], c["R"]], fr, color, handle="v320", hz_from_top=H - 1050, lefts=[True, False])
    else:
        b.doors("", c, [c["L"], c["R"]], fr, color, handle="bar128", hz_from_top=40 - GAP / 2, lefts=[True, False])
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    b.notes.append("Полки постоянные на Minifix — 5 уровней под папки (высота уровня ≈ 350, папка-регистратор 320).")
    b.warnings.append("Полка 768 под папками (≈ 40 кг): прогиб ЛДСП 16 — проверить на образце (В-12).")
    _anti_tip(b, 2)
    return b


def hallway_open(o):
    color = o["color"]
    W, H, D = 1200, 2100, 400
    b = Build("ARV-WRD-003", REV, STATUS, {"color": color})
    c = b.carcass("C-", 0, 400, 60, H, TF, D - TB, color, shelves=[(T, 400 - T, z, "Полка", "+") for z in (500, 900, 1300, 1700)],
                  label="шкаф")
    b.plinth("C-", c, 60, front=50, side=20, back=16, fin=color)
    b.doors("C-", c, [c["L"]], [(GAP / 2, 400 - GAP / 2, 60 + GAP / 2, H - GAP / 2)], color, handle="v320",
            hz_from_top=H - 1050, lefts=[True])
    bn = b.carcass("B-", 400, W, 40, 450, TF, D - TB, color, shelves=[(400 + T, W - T, 220, "Полка обувная", "+")],
                   back=False, vis_bottom=True, side_drop=40, label="обувница")
    seat = b.part("SEAT", "Сиденье", 400, 0, 450, W, D, 475, "LDSP25", color, "top", unit="Сиденье",
                  edges={"-y": "ABS2", "+x": "ABS2", "-x": "ABS2"})
    b.screws_into(bn["TOP"], seat, "+z", "x", [480, 800, 1120], "SCREW-4x30", "J-SEAT", pilot=(3, 12), at=120)
    b.screws_into(bn["TOP"], seat, "+z", "x", [480, 800, 1120], "SCREW-4x30", "J-SEAT2", pilot=(3, 12), at=D - 120)
    pan = b.part("PANEL", "Панель вешалки", 400, D - T, 475, W, D, H, "LDSP16", color, "carcass", unit="Панель вешалки",
                 edges={"+x": "ABS2", "+z": "ABS2", "-z": "ABS2"})
    hat = b.part("HAT", "Полка для шапок", 400, 100, H - T, W, D - T, H, "LDSP16", color, "carcass", unit="Полка для шапок",
                 edges={"-y": "ABS2", "+x": "ABS2"})
    b.conf(c["R"], pan, "+x", "z", [700, 1300, 1900], "J-CAB-PANEL")
    b.conf(c["R"], hat, "+x", "y", [140, D - T - 40], "J-CAB-HAT")
    b.conf(pan, hat, "-y", "x", [600, 1000], "J-PANEL-HAT")
    b.screws_into(c["R"], bn["L"], "+x", "y", [100, D - 100], "SCREW-4x30", "J-CAB-BENCH", pilot=(3, 12), at=300)
    for i in range(5):
        x = 460 + i * 160
        for z in (1690, 1720):
            b.hole(pan.id, "J-HOOKS", "pilot", x, D - T, z, "+y", 3, 10, "HOOK-SCREW", note="крючок — по месту")
        b.part(f"HOOK-{i + 1}", "Крючок", x - 8, D - 90, 1680, x + 8, D - T, 1730, "HOOK", "black", "fronts", kind="buy")
    b.buy("HOOK", "Крючок настенный двойной", "чёрный матовый (кандидат)", 5, "кандидат", "В-5")
    for z in (900, 1900):
        for x in (600, 1100):
            b.hole(pan.id, "J-WALL", "wall_bolt", x, D - T, z, "+y", 6, T, "ANCHOR-M8", through=True,
                   note="анкер / дюбель по типу стены, под заглушку")
    b.derived.update(width=W, depth=D, height=H, plinth=60)
    _check(b, "Ширина = шкаф 400 + обувница 800", W, 400 + (bn["R"].x1 - bn["L"].x0))
    b.notes.append("Сиденье ЛДСП 25 на крышке обувницы (в каталоге 26); панель вешалки — к стене на 4 анкера и к шкафу конфирматами.")
    _anti_tip(b, 1)
    return b


def glass_cabinet(o):
    W, color = int(o["width"]), o["color"]
    H, D, PL = 2000, 400, 80
    b = Build("ARV-WRD-005", REV, STATUS, {"width": W, "color": color})
    shz = (450, 850, 1250, 1650)
    c = b.carcass("", 0, W, PL, H, TF, D - TB, color, shelves=[(T, W - T, z, "Полка", "+") for z in shz], label="корпус")
    b.plinth("", c, PL, front=40, side=20, back=16, fin="black")
    nd = W // 400
    dw = W / nd
    for i in range(nd):
        xa, xb = i * dw + GAP / 2, (i + 1) * dw - GAP / 2
        left = i % 2 == 0
        S = c["L"] if left else c["R"]
        if nd > 2 and 0 < i < nd - 1:
            S = c["L"] if left else c["R"]
        b.part(f"DOOR-{i + 1}", "Дверь стеклянная в алюминиевой рамке", xa, 0, PL + GAP / 2, xb, TF, H - GAP / 2, "ALUGLASS",
               "black", "fronts", kind="buy")
        if S is c["L"] or S is c["R"]:
            xf, dr = (S.x1, "-x") if S is c["L"] else (S.x0, "+x")
            for z in (PL + 150, (PL + H) / 2, H - 150):
                for dz in (-16, 16):
                    b.hole(S.id, f"J-HINGE{i + 1}", "hinge_plate", xf, S.y0 + 37, z + dz, dr, 5, 13, "SCREW-6.3x13",
                           note="кандидат: планка петли для алюминиевой рамки")
    b.buy("ALUGLASS", "Дверь в алюминиевой рамке 20 мм с тонированным стеклом 4",
          f"{(W / nd - GAP):.0f} × {H - PL - GAP:.0f}, чёрный профиль, стекло графит; под петли для рамки (кандидат)", nd,
          "кандидат", "В-46")
    b.buy("HINGE-ALU", "Петля для алюминиевой рамки 110° с доводчиком", "кандидат Blum CLIP top для рамок 20 мм", 3 * nd,
          "кандидат", "В-46")
    for k, S_ in enumerate(c["shelves"], 1):
        b.part(f"LED-{k}", "Профиль LED под полкой", 20, 30, S_.z0 - 8, W - 20, 45, S_.z0, "LED", "black", "decor", kind="buy")
        for x in (60, W - 60):
            b.hole(S_.id, f"J-LED{k}", "led_screw", x, 38, S_.z0, "+z", 2.5, 8, "SCREW-3x12")
        b.hole(S_.id, f"J-LED{k}", "cable", W / 2, D - TB - 30, S_.z0, "+z", 10, T, through=True, note="ввод кабеля LED")
        b.glows.append([20, 30, W - 20, 45, (255, 196, 120), 60])
    b.buy("LED", "Профиль LED накладной + лента 2700 K + блок 12 В", f"4 × {W - 40}, выключатель (кандидат)", 4, "кандидат", "В-27")
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    b.derived["modules"].add("doors")
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    b.notes.append("Двери — покупные в рамке (кандидат): присадка корпуса — только планки петель; чашки не нужны.")
    _anti_tip(b, 1)
    _kq(b, "В-46")
    return b


def hallway_set(o):
    W, color = int(o["width"]), o["color"]
    cab_w = {1600: 800, 2000: 1000, 2400: 1200}[W]
    bench_w = W - cab_w
    H, PL, top, D = 2400, 80, 2040, 568
    b = Build("ARV-WRD-007", REV, STATUS, {"width": W, "color": color})
    x0 = bench_w
    c = b.carcass("C-", x0, W, PL, top, TF, D - TB, color,
                  shelves=[(x0 + T, W - T, top - 300, "Полка", "+"), (x0 + T, W - T, PL + 16 + 200, "Полка обувная", "+")],
                  label="шкаф")
    b.plinth("C-", c, PL, front=50, side=20, back=16, fin=color)
    _hang_rod(b, c["L"], c["R"], top - 380, (TF + D - TB) / 2)
    m = b.carcass("C-M-", x0, W, top, H, TF, D - TB, color, label="антресоль")
    _tie_mez(b, c["TOP"], m["BOT"], x0, W, (TF + D) / 2)
    nd = 2 if cab_w > 600 else 1
    dw = cab_w / nd
    fr = [(x0 + i * dw + GAP / 2, x0 + (i + 1) * dw - GAP / 2, PL + GAP / 2, top - GAP / 2) for i in range(nd)]
    frm = [(a, b_, top + GAP / 2, H - GAP / 2) for (a, b_, _, _) in fr]
    sides = [c["L"], c["R"]][:nd]
    b.doors("C-", c, sides, fr, color, handle=None, lefts=[True, False][:nd])
    b.doors("C-M-", m, [m["L"], m["R"]][:nd], frm, color, handle=None, lefts=[True, False][:nd])
    b.buy("PUSH-LATCH", "Толкатель TIP-ON для двери без ручки", "кандидат Blum TIP-ON 956A1004", 2 * nd, "кандидат", "В-20")
    seat = b.part("SEAT", "Сиденье скамьи", 20, D - 350, 420, bench_w - 20, D, 458, "TOP38", "O", "top", unit="Сиденье",
                  edges={"-y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    arms = []
    for i, bx in enumerate((150, bench_w - 190), 1):
        v = b.tube(f"BR{i}-V", "Кронштейн, стойка к стене", bx, D - 20, 220, bx + 40, D, 400, "TUBE40x20x2", "black", "z")
        a = b.tube(f"BR{i}-H", "Кронштейн, консоль", bx, D - 330, 400, bx + 40, D, 420, "TUBE40x20x2", "black", "y")
        b.weld(v, a)
        arms.append(a)
        b.derived["frames"].append({"name": f"Кронштейн скамьи {i}", "tubes": [v.id, a.id]})
        for z in (250, 370):
            b.hole(v.id, f"J-WALL{i}", "wall_bolt", bx + 20, D - 20, z, "+y", 9, 20, "ANCHOR-M8", through=True,
                   note="сквозь обе стенки; в лицевой — Ø13 доступ")
            b.hole(v.id, f"J-WALL{i}", "tube_access", bx + 20, D - 20, z, "+y", 13, 2, through=True)
    b.top_fix(seat, arms, [D - 300, D - 60], "y", "J-SEAT", insert=False)
    b.part("MIRROR", "Зеркало с подсветкой", bench_w / 2 - 300, D - 25, 900, bench_w / 2 + 300, D, 1900, "MIRROR", "steel",
           "decor", kind="buy")
    b.buy("MIRROR", "Зеркало 600 × 1000 с LED-подсветкой по контуру", "навеска на стену, блок питания (кандидат)", 1,
          "кандидат", "В-27")
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = скамья + шкаф", W, bench_w + (c["R"].x1 - c["L"].x0))
    b.notes += ["Сиденье — плита-столешница 38 «Дуб» (в каталоге щит 40) на двух сварных кронштейнах 40 × 20 к стене.",
                "Шкаф без ручек: двери на петлях без пружины + TIP-ON."]
    _anti_tip(b, 1)
    _kq(b, "В-21")
    return b


def tv_unit(o):
    L, color, panel = int(o["length"]), o["color"], o.get("panel", "none")
    z0, z1, D = 250, 600, 400
    n = L // 600
    pattern = {3: "DOD", 4: "DOOD"}[n]
    b = Build("ARV-LIV-001", REV, STATUS, {"length": L, "color": color, "panel": panel})
    parts = [(i * 600 - 8, T, "Стойка") for i in range(1, n)]
    c = b.carcass("", 0, L, z0, z1, TF, D - TB, color, partitions=parts, vis_bottom=True, label="консоль")
    b.hangers("", c, "навес скрытый усиленный под ХДФ 4 (≥ 60 кг на пару) + шина, кандидат", note="В-21")
    verts = [c["L"]] + c["parts"] + [c["R"]]
    for i, k in enumerate(pattern):
        if k != "D":
            continue
        a, bb = verts[i], verts[i + 1]
        fx0, fx1 = (a.x0 if i == 0 else i * 600) + GAP / 2, ((i + 1) * 600 if i + 1 < n else L) - GAP / 2
        fl = b.part(f"FLAP-{i + 1}", "Фасад откидной", fx0, 0, z0 + GAP / 2, fx1, TF, z1 - GAP / 2, "LDSP18", color, "fronts",
                    unit="Фасад откидной", edges={"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
        for x in (fx0 + 90, fx1 - 90):
            b.hole(fl.id, f"J-FLAP{i + 1}", "hinge_cup", x, TF, z0 + GAP / 2 + 22.5, "-y", 35, 13, "HINGE",
                   note="кандидат: петля для откидного фасада, чашка у нижней кромки")
            for dx in (-22.5, 22.5):
                b.hole(fl.id, f"J-FLAP{i + 1}", "hinge_cup_screw", x + dx, TF, z0 + GAP / 2 + 22.5 + 9.5, "-y", 2.5, 8,
                       "SCREW-3.5x15", note="засверловка под саморез чашки, схема 45 / 9,5")
            for dx in (-16, 16):
                b.hole(c["BOT"].id, f"J-FLAP{i + 1}", "hinge_plate", x + dx, TF + 37, c["BOT"].z1, "-z", 5, 13, "SCREW-6.3x13",
                       note="кандидат: планка на дне")
        for S, xf, dr in ((a, a.x1, "-x"), (bb, bb.x0, "+x")):
            b.hole(S.id, f"J-STAY{i + 1}", "runner_mark", xf, TF + 60, z0 + 120, dr, 4, 0, "STAY-SCREW",
                   note="разметка подъёмника / ограничителя по шаблону (кандидат)")
    if panel != "none":
        # стеновая панель (02.11): секции ЛДСП 18 по 600 за консолью, на всю длину, высота 2400; рейки — МДФ 22
        HP, step, rib = 2400, 60, 40
        for i in range(n):
            pp = b.part(f"WP-{i + 1}", "Панель стеновая", i * 600, D, 0, (i + 1) * 600, D + 18, HP, "LDSP18", color, "panel",
                        unit="Панель стеновая", edges={"-x": "ABS2", "+x": "ABS2", "+z": "ABS2", "-z": "PVC04"})
            if panel == "slats":
                k = 600 // step
                x0s = i * 600 + (step - rib) / 2
                for j in range(k):
                    for zi, (za, zb) in enumerate(((0, z0 - 10), (z1 + 10, HP)), 1):
                        b.part(f"SL-{i + 1}-{j + 1}-{zi}", "Рейка", x0s + j * step, D - 22, za, x0s + j * step + rib, D, zb,
                               "MDF22", color, "panel", unit=f"Рейка {'нижняя' if zi == 1 else 'верхняя'}",
                               edges={"-y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
        nsl = sum(1 for p in b.P if p.id.startswith("SL-"))
        b.buy("WP-RAIL", "Шина навесная для стеновой панели (french cleat)", "алюминий / ЛДСП, по 2 на секцию; анкеры по типу стены (кандидат)",
              2 * n, "кандидат", "В-49")
        if nsl:
            b.buy("SLAT-FIX", "Крепление реек к панели", "клей ПВА D3 + саморез 3,5 × 30 с тыла панели, по 2 на рейку (кандидат)",
                  2 * nsl, "кандидат", "В-49")
        b.derived.setdefault("kdec", []).append(
            "Стеновая панель: секции ЛДСП 18 по 600 со стыком на линиях секций консоли (в каталоге — один лист); рейки МДФ 22 "
            "(в каталоге 18) только выше и ниже консоли.")
        b.warnings.append("Стеновая панель: консоль навешивается на шину через панель (проставки 18 по месту), "
                          "панель — на шину french cleat; стену проверить на ровность ± 3 мм (В-49).")
    nf = pattern.count("D")
    FASTENERS.setdefault("STAY-SCREW", ("Саморез ограничителя откидного фасада", "в комплекте (кандидат)", "кандидат", "В-49", "шт"))
    b.buy("HINGE", "Петля для откидного фасада", "кандидат Blum CLIP top 90° для откидных + планка", 2 * nf, "кандидат", "В-49")
    b.buy("FLAP-STAY", "Ограничитель / подъёмник откидного фасада + толкатель TIP-ON", "пара на фасад (кандидат)", nf,
          "кандидат", "В-49")
    b.derived.update(width=L, depth=D + (18 if panel != "none" else 0), height=2400 if panel != "none" else z1, plinth=z0)
    b.derived["modules"].add("doors")
    _check(b, "Длина = секции × 600", L, 600 * n)
    b.warnings.append(f"Подвесная консоль {L} мм с ТВ-техникой: навесы и анкеры — по типу стены, нагрузка ≥ 60 кг (В-21).")
    _kq(b, "В-49")
    return b


# =============================================================================== шкаф-купе
def wardrobe_sliding(o):
    W, color, doors = int(o["width"]), o["color"], o.get("doors", "ldsp")
    H, D, PL, Z = 2400, 620, 60, 90          # Z — зона дверей спереди
    b = Build("ARV-WRD-002", REV, STATUS, {"width": W, "color": color, "doors": doors})
    yc1 = D - TB
    c = b.carcass("", 0, W, PL, H, 0, yc1, color, side_drop=PL, back=False, label="корпус")
    n = W // 600
    sw = (W - 2 * T - (n - 1) * T) / n
    verts = [c["L"]]
    ys = b._ecc_ys(yc1 - Z, Z)
    for i in range(1, n):
        xl = T + i * sw + (i - 1) * T
        Pp = b.part(f"PART-{i}", "Стойка", xl, Z, PL + T, xl + T, yc1, H - T, "LDSP16", "INNER", "carcass", edges={"-y": "ABS2"})
        for B_, nn in ((c["TOP"], "-z"), (c["BOT"], "+z")):
            j = f"J-PART{i}-{B_.id}"
            b.ecc(B_, Pp, nn, "y", ys["ecc"], "+", j)
            b.dowel(B_, Pp, nn, "y", ys["dowel"], j)
        verts.append(Pp)
    verts.append(c["R"])
    kinds = "HSHD"
    for i in range(n):
        a, bb = verts[i], verts[i + 1]
        k = kinds[i % 4]
        zs = [2000] if k != "S" else [500, 850, 1200, 1550, 2000]
        ysh = b._ecc_ys(yc1 - Z, Z, shift=-15 if i % 2 else 0)
        for zi, z in enumerate(zs, 1):
            S_ = b.part(f"SH{i + 1}-{zi}", "Полка", a.x1, Z, z, bb.x0, yc1, z + T, "LDSP16", "INNER", "carcass",
                        edges={"-y": "ABS2"})
            for V, nn, tag in ((a, "+x", "L"), (bb, "-x", "R")):
                j = f"J-SH{i + 1}{zi}{tag}"
                b.ecc(V, S_, nn, "y", ysh["ecc"], "+", j)
                b.dowel(V, S_, nn, "y", ysh["dowel"], j)
        if k in "HD":
            _hang_rod(b, a, bb, 1920, (Z + yc1) / 2)
    BK = b.part("BACK", "Задняя стенка", 2, yc1, PL + 2, W - 2, yc1 + TB, H - 2, "HDF4", "INNER", "carcass")
    b._back_screws("", verts, [c["TOP"], c["BOT"]] + [p for p in b.P if p.id.startswith("SH")], yc1, PL, H, 0, W)
    pl = b.part("PL-F", "Цоколь", T, 60, 0, W - T, 60 + T, PL, "LDSP16", color, "carcass", unit="Цоколь",
                edges={"-z": "PVC04"})   # 14.11: ABS 2 на «-y» (пласть) убрана
    b.conf(c["BOT"], pl, "-z", "x", [T + 80 + (W - 2 * T - 160) * k / 4 for k in range(5)], "J-BOT-PL")
    # двери-купе: система профиля (кандидат)
    nd = 2 if W <= 1800 else 3
    dw = (W - 2 * T + 30 * (nd - 1)) / nd
    for k in range(nd):
        xa = T + k * (dw - 30)
        yp = 10 if k % 2 == 0 else 45
        mir = doors == "mirror" and k == nd // 2
        b.part(f"DOOR-{k + 1}", "Дверь-купе в профиле", xa, yp, PL + T + 10, xa + dw, yp + 26, H - T - 40,
               "SLIDEDOOR", "steel" if mir else color, "fronts", kind="buy")
    b.buy("SLIDEDOOR", "Дверь-купе: профиль алюминиевый + заполнение",
          f"{nd} шт. ≈ {dw:.0f} × {H - T - 40 - PL - T - 10:.0f}, заполнение ЛДСП 10 в декоре"
          + (", средняя — зеркало 4" if doors == "mirror" else "") + "; раскрой заполнения — по формулам системы", nd,
          "кандидат", "В-45")
    for tr, B_, zf, dr in (("TOP", c["TOP"], c["TOP"].z0, "+z"), ("BOT", c["BOT"], c["BOT"].z1, "-z")):
        for x in [T + 60 + (W - 2 * T - 120) * k / 5 for k in range(6)]:
            for y in (25, 60):
                b.hole(B_.id, f"J-TRACK-{tr}", "pilot", x, y, zf, dr, 3, 10, "TRACK-SCREW", note="направляющая — по системе")
    b.buy("TRACK", "Направляющие верхняя и нижняя", f"L = {W - 2 * T}, по системе дверей (кандидат)", 1, "кандидат", "В-45", "компл")
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    b.derived["modules"].add("doors")
    _check(b, "Внутренние секции + стойки = ширина между боковинами", W - 2 * T, round(n * sw + (n - 1) * T, 3))
    b.notes += [f"Корпус: боковины до пола, крышка и дно на Minifix; стойки и полки — с отступом {Z} от лица под двери-купе.",
                "Двери в двух плоскостях; перехлёст 30; верхняя направляющая — под крышкой, нижняя — на дне."]
    b.warnings.append("Двери-купе: размеры дверей и заполнения — по документации выбранной системы (В-45).")
    _anti_tip(b, 2)
    _kq(b, "В-45")
    return b


# =============================================================================== гардеробная «Каркас»
def open_wardrobe(o):
    W, color, metal = int(o["width"]), o["color"], o["metal"]
    H, D, step = 2200, 450, 800
    b = Build("ARV-WRD-006", REV, STATUS, {"width": W, "color": color, "metal": metal})
    prof = "TUBE30x20x2"
    xs = [min(x, W - 30) for x in range(0, W + 1, step)]
    posts = []
    for i, x in enumerate(xs, 1):
        pf = b.tube(f"FR{i}-PF", "Стойка передняя", x, 30, 30, x + 30, 50, H, prof, metal, "z")
        pb = b.tube(f"FR{i}-PB", "Стойка задняя", x, D - 50, 30, x + 30, D - 30, H, prof, metal, "z")
        rt = b.tube(f"FR{i}-RT", "Ригель верхний", x, 50, H - 20, x + 30, D - 50, H, prof, metal, "y")
        rb = b.tube(f"FR{i}-RB", "Ригель нижний", x, 50, 100, x + 30, D - 50, 120, prof, metal, "y")
        for r in (rt, rb):
            b.weld(r, pf); b.weld(r, pb)
        for p_ in (pf, pb):
            b.plate(f"{p_.id}-EP", "Пластина опоры", x, p_.y0, 26, x + 30, p_.y1, 30, metal)
            b.weld(b.get(f"{p_.id}-EP"), p_)
            b.hole(f"{p_.id}-EP", f"J-GLIDE{i}", "plate_hole", x + 15, (p_.y0 + p_.y1) / 2, 26, "+z", 9, 4, "GLIDE-M8",
                   through=True, note="гайка M8 приварена сверху")
        b.derived["frames"].append({"name": f"Рама-стойка {i}", "tubes": [pf.id, pb.id, rt.id, rb.id]})
        for z in (1000, H - 200):
            b.hole(pb.id, f"J-WALL{i}", "wall_bolt", x + 15, D - 30, z, "-y", 9, 20, "ANCHOR-M8", through=True,
                   note="к стене; в лицевой стенке Ø13 доступ")
        posts.append((x, pf, pb))
    b.buy("GLIDE-M8", "Опора регулируемая M8", "h 20, Ø30 (кандидат)", 2 * len(xs), "кандидат", "В-26")
    kinds = "HSD"
    for k in range(len(xs) - 1):
        a, bb = xs[k] + 30, xs[k + 1]
        kind = kinds[k % 3]
        lv = [H - 280]
        if kind == "H":
            lv.append(300)
        elif kind == "S":
            lv += [500, 850, 1200, 1550]
        for zi, z in enumerate(sorted(lv), 1):
            S_ = b.part(f"SH{k + 1}-{zi}", "Полка", a, 30, z, bb, D - 30, z + 25, "LDSP25", color, "shelves", unit="Полка",
                        edges={"-y": "ABS2", "+y": "PVC04"})
            for xp, side in ((a, "L"), (bb, "R")):
                for yy, pid in ((30, "PF"), (D - 70, "PB")):
                    px0 = xp if side == "L" else xp - 30
                    pl = b.plate(f"SP{k + 1}-{zi}-{side}{pid}", "Пластина полки", px0, yy, z - 4, px0 + 30, yy + 40, z, metal)
                    frame = k + 1 if side == "L" else k + 2
                    b.weld(pl, b.get(f"FR{frame}-{pid}"))
                    b.hole(pl.id, f"J-SH{k + 1}{zi}", "plate_hole", px0 + 15, yy + 20, z - 4, "+z", 4.5, 4, "SCREW-4x16C",
                           through=True)
                    b.hole(S_.id, f"J-SH{k + 1}{zi}", "pilot", px0 + 15, yy + 20, z, "+z", 3, 12)
        if kind in "HD":
            top = b.get(f"SH{k + 1}-{len(lv)}")
            for x in (a + 60, bb - 60):
                for dy in (-12, 12):
                    b.hole(top.id, f"J-ROD{k + 1}", "pilot", x, D / 2 + dy, top.z0, "+z", 2.5, 12, "ROD-SCREW",
                           note="штангодержатель потолочный")
            b.part(f"ROD-{k + 1}", "Штанга", a, D / 2 - 7.5, top.z0 - 80, bb, D / 2 + 7.5, top.z0 - 50, "ROD", metal,
                   "interior", kind="buy")
            b.buy("ROD", "Штанга гардеробная овальная", "раскрой по месту, держатели потолочные — 2 шт.", 1, "типовой", "")
    b.derived.update(width=W, depth=D, height=H, plinth=30)
    _check(b, "Рамы стоят с шагом 800", True, all(xs[i + 1] - xs[i] <= 800 for i in range(len(xs) - 1)))
    b.notes.append("Рамы-стойки сварные 30 × 20 × 2; полки ЛДСП 25 на приварных пластинах; задние стойки — к стене на анкеры.")
    _kq(b, "В-21", "В-48")
    return b


# =============================================================================== стеллаж «Грань»
def shelf_divider(o):
    W, color, metal = int(o["width"]), o["color"], o["metal"]
    H, D = 2000, 350
    n = W // 400
    b = Build("ARV-LIV-002", REV, STATUS, {"width": W, "color": color, "metal": metal})
    prof = "TUBE20x20x2"
    levels = [40, 400, 800, 1200, 1600, H - 25]
    xs = [min(i * 400, W - 20) for i in range(n + 1)]
    for i, x in enumerate(xs, 1):
        pf = b.tube(f"FR{i}-PF", "Стойка", x, 0, 0, x + 20, 20, H - 25, prof, metal, "z")
        pb = b.tube(f"FR{i}-PB", "Стойка", x, D - 20, 0, x + 20, D, H - 25, prof, metal, "z")
        ids = [pf.id, pb.id]
        for j, z in enumerate(levels, 1):
            cb = b.tube(f"FR{i}-C{j}", "Перемычка", x, 20, z - 20, x + 20, D - 20, z, prof, metal, "y")
            b.weld(cb, pf); b.weld(cb, pb)
            ids.append(cb.id)
        b.derived["frames"].append({"name": f"Рама-лестница {i}", "tubes": ids})
    b.buy("GLIDE-20", "Заглушка-опора регулируемая для трубы 20 × 20", "M6, ход 10 (кандидат)", 2 * len(xs), "кандидат", "В-26")
    shelves = []
    for j, z in enumerate(levels, 1):
        S_ = b.part(f"SH-{j}", "Полка", 0, 20, z, W, D - 20, z + 25, "LDSP25", "O", "shelves", unit="Полка",
                    edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
        shelves.append(S_)
        b.top_fix(S_, [b.get(f"FR{i}-C{j}") for i in range(1, len(xs) + 1)], [80, D - 80], "y", f"J-SH{j}", insert=False)
    nb = 0
    for j in range(len(levels) - 1):
        for i in range(n):
            if (i + j) % 3 != 1:
                continue
            nb += 1
            a = i * 400 + 20
            zb = levels[j] + 25
            pre = f"BX{nb}-"
            cx = b.carcass(pre, a, a + 380, zb, zb + 300, 20 + TF, D - 20 - TB, color, label=f"короб {nb}")
            b.doors(pre, cx, [cx["L"]], [(a + GAP / 2, a + 380 - GAP / 2, zb + GAP / 2, zb + 300 - GAP / 2)], color,
                    handle=None, lefts=[True])
            for d_ in b.P:
                if d_.id == f"{pre}DOOR-1":
                    d_.y0, d_.y1 = 20, 20 + TF
            for h in b.holes:
                if h["part"] == f"{pre}DOOR-1":
                    h["y"] = 20 + TF
            b.screws_into(cx["BOT"], shelves[j], "-z", "x", [a + 80, a + 300], "SCREW-4x30", f"J-{pre}SH", pilot=(3, 12),
                          at=D / 2)
    b.buy("PUSH-LATCH", "Толкатель TIP-ON для дверцы короба", "кандидат Blum TIP-ON 956.1004", nb, "кандидат", "В-20")
    b.derived.update(width=W, depth=D, height=H, plinth=0)
    _check(b, "Рам-лестниц = число пролётов + 1", n + 1, len(xs))
    b.warnings.append("Стеллаж-перегородка 2000 × 350 стоит свободно: крепление к потолку / полу или к стене обязательно "
                      "(В-48); жёсткость вдоль длины — полки на саморезах, проверить на образце (В-12).")
    b.notes.append("Короба с дверцей TIP-ON (в каталоге — глухая лицевая панель); дверца с одной стороны стеллажа.")
    b.derived["kdec"] = ["Короба стеллажа — с дверцей на нажатие (в каталоге глухая панель); полки между стойками глубиной 310 "
                         "(в каталоге полка шире стоек)."]
    _kq(b, "В-48")
    return b


# =============================================================================== бенч «Ряд»
def bench_system(o):
    seats, topc, metal = int(o["seats"]), o["top"], o["metal"]
    pairs = max(1, seats // 2)
    w, d, H, t = 1400, 700, 750, 25
    W, D = pairs * w, 2 * d
    b = Build("ARV-OFF-002", REV, STATUS, {"seats": seats, "top": topc, "metal": metal})
    fx = [40] + [i * w - 30 for i in range(1, pairs)] + [W - 100]
    frames = []
    for i, x in enumerate(fx, 1):
        la = b.tube(f"FR{i}-LA", "Нога", x, 60, 30, x + 60, 90, H - t - 30, "TUBE60x30x2", metal, "z")
        lb = b.tube(f"FR{i}-LB", "Нога", x, D - 90, 30, x + 60, D - 60, H - t - 30, "TUBE60x30x2", metal, "z")
        ft = b.tube(f"FR{i}-FT", "Опора напольная", x, 50, 0, x + 60, D - 50, 30, "TUBE60x30x2", metal, "y")
        tb = b.tube(f"FR{i}-TB", "Ригель верхний", x, 50, H - t - 30, x + 60, D - 50, H - t, "TUBE60x30x2", metal, "y")
        for l_ in (la, lb):
            b.weld(l_, ft); b.weld(l_, tb)
        b.glide(ft, [(x + 30, 80), (x + 30, D - 80)], f"J-GLIDE{i}")
        b.derived["frames"].append({"name": f"Опора {i}", "tubes": [la.id, lb.id, ft.id, tb.id]})
        frames.append(tb)
    b.buy("GLIDE-PAD", "Подпятник регулируемый M8", "h 15, Ø30 (кандидат)", 2 * len(fx), "кандидат", "В-26")
    beams = []
    for i in range(len(fx) - 1):
        xa, xb = fx[i] + 60, fx[i + 1]
        bm = b.tube(f"BM{i + 1}", "Балка", xa + 4, d - 15, H - t - 30, xb - 4, d + 15, H - t, "TUBE30x30x2", metal, "x")
        beams.append(bm)
        b.derived["frames"].append({"name": f"Балка {i + 1}", "tubes": [bm.id]})
        for xe, tag in ((xa, "A"), (xb - 4, "B")):
            pl = b.plate(f"BM{i + 1}-{tag}", "Пластина балки", xe, d - 30, H - t - 30, xe + 4, d + 30, H - t, metal)
            b.weld(pl, bm)
            tbx = frames[i] if tag == "A" else frames[i + 1]
            face = tbx.x1 if tag == "A" else tbx.x0
            for dy in (-20, 20):
                b.hole(pl.id, f"J-BM{i + 1}{tag}", "plate_hole", xe + (0 if tag == "A" else 4), d + dy, H - t - 15,
                       "+x" if tag == "A" else "-x", 7, 4, "SCREW-M6x16", through=True)
                b.hole(tbx.id, f"J-BM{i + 1}{tag}", "rivnut6", face, d + dy, H - t - 15, "-x" if tag == "A" else "+x", 9, 2,
                       "RIVNUT-M6", through=True)
        b.part(f"TRAY{i + 1}", "Лоток кабельный", xa + 20, d - 150, H - t - 140, xb - 20, d + 150, H - t - 130, "TRAY",
               metal, "frame", kind="buy")
        for x in (xa + 150, xb - 150):
            b.hole(bm.id, f"J-TRAY{i + 1}", "tray_hole", x, d, H - t - 30, "+z", 4.5, 2, "SCREW-4x13", through=True)
    b.buy("TRAY", "Лоток кабельный подвесной", "сталь 300 × 100, порошок в цвет опор (кандидат)", len(beams), "кандидат", "В-29")
    tops = []
    for side in range(2):
        y0 = side * d
        for i in range(pairs):
            tp = b.part(f"TOP{side + 1}-{i + 1}", "Столешница", i * w + 2, y0 + 2, H - t, (i + 1) * w - 2, y0 + d - 2, H,
                        "LDSP25", topc, "top", unit="Столешница",
                        edges={"-x": "ABS2", "+x": "ABS2", "-y": "ABS2", "+y": "ABS2"})
            tops.append(tp)
            sup = [f for f in frames if tp.x0 - 1 <= f.x0 and f.x1 <= tp.x1 + 1]
            b.top_fix(tp, sup, [y0 + 120, y0 + d - 120], "y", f"J-{tp.id}-FR")
    for i in range(pairs):
        b.part(f"SCR-{i + 1}", "Экран-перегородка", i * w + 50, d - 12, H, (i + 1) * w - 50, d + 12, H + 400, "SCREEN", "G",
               "screen", kind="buy")
    b.buy("SCREEN", "Экран-перегородка акустический 1300 × 400 × 24", "войлок / ткань на каркасе (кандидат)", pairs,
          "кандидат", "В-29")
    b.buy("SCREEN-CLAMP", "Крепление экрана к столешнице", "струбцина двухсторонняя (кандидат)", 2 * pairs, "кандидат", "В-29")
    b.derived.update(width=W, depth=D, height=H, plinth=0)
    _check(b, "Высота = опора + столешница", H, (H - t) + t)
    b.notes.append("Опоры сварные 60 × 30 × 2 (как «Фокус»); балка 30 × 30 на торцевых пластинах M6 в заклёпочные гайки; "
                   "столешницы ЛДСП 25 на втулках M6.")
    return b


# =============================================================================== кровати
def bed_lift(o):
    mw, color = int(o["size"]), o["color"]
    t = 25
    W, Lin = mw + 10 + 2 * t, 2010
    L = t + Lin
    b = Build("ARV-BED-001", REV, STATUS, {"size": mw, "color": color})
    ed = {"-y": "ABS2", "+z": "ABS2", "-z": "ABS2"}
    SL = b.part("SIDE-L", "Борт боковой", 0, 0, 40, t, L, 400, "LDSP25", color, "carcass", edges=dict(ed))
    SR = b.part("SIDE-R", "Борт боковой", W - t, 0, 40, W, L, 400, "LDSP25", color, "carcass", edges=dict(ed))
    FT = b.part("FOOT", "Борт ножной", t, 0, 40, W - t, t, 400, "LDSP25", color, "carcass", edges={"+z": "ABS2", "-z": "ABS2"})
    HB = b.part("HEAD", "Изголовье", 0, L, 40, W, L + t, 1100, "LDSP25", color, "headboard",
                edges={"-x": "ABS2", "+x": "ABS2", "+z": "ABS2", "-z": "ABS2"})
    BT = b.part("BOTTOM", "Дно бельевого короба", t, t, 40, W - t, L, 56, "LDSP16", "INNER", "carcass")
    DV = b.part("DIVIDER", "Перегородка", W / 2 - 8, t, 56, W / 2 + 8, L, 300, "LDSP16", "INNER", "carcass", edges={"+z": "PVC04"})
    for S, n_ in ((SL, "+x"), (SR, "-x")):
        b.bed_bolt(S, FT, n_, "z", [110, 330], f"J-{S.id}-FOOT", "+")
        b.bed_bolt(HB, S, "-y", "z", [110, 330], f"J-HEAD-{S.id}", "+" if S is SL else "-")
        b.conf(S, BT, n_, "y", [250, 750, 1250, 1750], f"J-{S.id}-BOT")
    b.conf(FT, BT, "+y", "x", [200, W / 2 - 150, W / 2 + 150, W - 200], "J-FOOT-BOT")
    b.conf(HB, BT, "-y", "x", [200, W / 2 - 150, W / 2 + 150, W - 200], "J-HEAD-BOT")
    b.conf(BT, DV, "+z", "y", [300, 1000, 1700], "J-BOT-DIV")
    b.conf(HB, DV, "-y", "z", [120, 240], "J-HEAD-DIV")
    b.conf(FT, DV, "+y", "z", [120, 240], "J-FOOT-DIV")
    # цоколь-рамка под дном
    pf = b.part("PL-F", "Цоколь", 40, 40, 0, W - 40, 56, 40, "LDSP16", "black", "base")   # 14.11: кромка «-y» была на пласти
    pb = b.part("PL-B", "Цоколь", 40, L - 56, 0, W - 40, L - 40, 40, "LDSP16", "black", "base")
    ps = [b.part(f"PL-S{k}", "Цоколь", x, 56, 0, x + 16, L - 56, 40, "LDSP16", "black", "base")
          for k, x in ((1, 40), (2, W / 2 - 8), (3, W - 56))]
    for s_ in ps:
        b.dowel(pf, s_, "+y", "z", [20], f"J-PLF-{s_.id}")
        b.dowel(pb, s_, "-y", "z", [20], f"J-PLB-{s_.id}")
    b.conf(BT, pf, "-z", "x", [120, W / 2 - 200, W / 2 + 200, W - 120], "J-BOT-PLF")
    b.conf(BT, pb, "-z", "x", [120, W / 2 - 200, W / 2 + 200, W - 120], "J-BOT-PLB")
    for s_ in ps:
        b.conf(BT, s_, "-z", "y", [400, 1100, 1800], f"J-BOT-{s_.id}")
    # основание с механизмом — покупное
    b.part("LIFT", "Основание ортопедическое с подъёмным механизмом", t + 5, t + 5, 330, W - t - 5, L - 5, 370, "LIFT", "steel",
           "interior", kind="buy")
    for S, xf, dr in ((SL, t, "-x"), (SR, W - t, "+x")):
        for y in (120, 260, 1100):
            b.hole(S.id, "J-LIFT", "runner_mark", xf, y, 300, dr, 9, 0, "LIFT-BOLT",
                   note="разметка по шаблону механизма; Ø9 насквозь — после примерки (кандидат)")
    b.buy("LIFT", "Основание ортопедическое с газлифтами", f"{mw} × 2000, рама 40 × 25, ламели 53 × 8, газлифты 1200 N (кандидат)",
          1, "кандидат", "В-44")
    b.part("MATTRESS", "Матрас (не входит)", t + 10, t + 10, 370, W - t - 10, L - 10, 590, "APPL", "white", "bedding",
           kind="context")
    b.derived.update(width=W, depth=L + t, height=1100, plinth=40)
    _check(b, "Внутренний проём под основание", mw + 10, W - 2 * t)
    _check(b, "Длина проёма", 2010, L - t)
    b.notes += ["Короб ЛДСП 25: борта и изголовье на кроватных стяжках M6 (по 2 на угол), дно ЛДСП 16 на конфирматах, "
                "стоит на цоколе-рамке 40 (утоплен на 40).",
                "Основание с механизмом — покупное, крепится к бортам болтами M8 по шаблону изготовителя."]
    b.derived["kdec"] = ["Борта и изголовье ЛДСП 25 (в каталоге 32); проём 1610 × 2010 под покупное основание с механизмом."]
    b.warnings.append("Нагрузка: короб с основанием и двумя людьми ≈ 250 кг на дно 16 через цоколь — испытать образец (В-12).")
    _kq(b, "В-44")
    return b


def floating_bed(o):
    mw, hb, color, led = int(o["size"]), o.get("headboard", "flat"), o["color"], o.get("led", "off")
    W, L, inset, tb = mw + 100, 2100, 200, 40
    b = Build("ARV-BED-002", REV, STATUS, {"size": mw, "headboard": hb, "color": color, "led": led})
    prof = "TUBE40x40x2"
    bx0, by0, bx1, by1 = inset, inset, W - inset, L - inset
    legs = []
    for x in (bx0, bx1 - tb):
        for y in (by0, (by0 + by1 - tb) / 2, by1 - tb):
            lg = b.tube(f"LEG-{len(legs) + 1}", "Опора", x, y, 24, x + tb, y + tb, 220, prof, "black", "z")
            pl = b.plate(f"LEG-{len(legs) + 1}-P", "Пластина опоры", x, y, 20, x + tb, y + tb, 24, "black")
            b.weld(pl, lg)
            b.hole(pl.id, f"J-GLIDE{len(legs) + 1}", "plate_hole", x + 20, y + 20, 20, "+z", 9, 4, "GLIDE-M8", through=True,
                   note="гайка M8 приварена сверху")
            legs.append(lg)
    base = [b.tube("B-L", "Рама основания, продольная", bx0, by0, 220, bx0 + tb, by1, 260, prof, "black", "y"),
            b.tube("B-R", "Рама основания, продольная", bx1 - tb, by0, 220, bx1, by1, 260, prof, "black", "y")]
    for k, y in enumerate([by0, by0 + (by1 - by0) / 3 - tb / 2, by0 + 2 * (by1 - by0) / 3 - tb / 2, by1 - tb], 1):
        base.append(b.tube(f"B-C{k}", "Рама основания, поперечина", bx0 + tb, y, 220, bx1 - tb, y + tb, 260, prof, "black", "x"))
    for lg in legs:
        b.weld(lg, base[0] if lg.x0 == bx0 else base[1])
    for cb in base[2:]:
        b.weld(cb, base[0]); b.weld(cb, base[1])
    c = T
    plat = [b.tube("P-L", "Рама платформы, продольная", c, c, 260, c + tb, L - c, 300, prof, "black", "y"),
            b.tube("P-R", "Рама платформы, продольная", W - c - tb, c, 260, W - c, L - c, 300, prof, "black", "y")]
    ycs = [c] + [c + (L - 2 * c) * k / 6 - tb / 2 for k in range(1, 6)] + [L - c - tb]
    for k, y in enumerate(ycs, 1):
        plat.append(b.tube(f"P-C{k}", "Рама платформы, поперечина", c + tb, y, 260, W - c - tb, y + tb, 300, prof, "black", "x"))
    for k in range(len(ycs) - 1):
        ya, yb = ycs[k] + tb, ycs[k + 1]
        m_ = b.tube(f"P-M{k + 1}", "Рама платформы, средняя", W / 2 - tb / 2, ya, 260, W / 2 + tb / 2, yb, 300, prof, "black", "y")
        b.weld(m_, plat[2 + k]); b.weld(m_, plat[3 + k])
    for cr in plat[2:]:
        b.weld(cr, plat[0]); b.weld(cr, plat[1])
        for bl in base[:2]:
            if cr.y0 < bl.y1 and cr.y1 > bl.y0:
                b.weld(cr, bl)
    for bc in base[2:]:
        for pl_ in plat[:2]:
            pass
    b.derived["frames"] += [{"name": "Основание", "tubes": [t_.id for t_ in legs + base]},
                            {"name": "Рама платформы", "tubes": [t_.id for t_ in plat] + [p.id for p in b.P if p.id.startswith("P-M")]}]
    # облицовка
    z0, z1 = 170, 320
    ed = {"+z": "ABS2", "-z": "ABS2"}
    SF = b.part("CL-F", "Облицовка ножная", 0, 0, z0, W, c, z1, "LDSP16", color, "carcass", edges={**ed, "-x": "ABS2", "+x": "ABS2"})
    SB = b.part("CL-B", "Облицовка задняя", 0, L - c, z0, W, L, z1, "LDSP16", color, "carcass", edges={**ed, "-x": "ABS2", "+x": "ABS2"})
    SLp = b.part("CL-L", "Облицовка боковая", 0, c, z0, c, L - c, z1, "LDSP16", color, "carcass", edges=dict(ed))
    SRp = b.part("CL-R", "Облицовка боковая", W - c, c, z0, W, L - c, z1, "LDSP16", color, "carcass", edges=dict(ed))
    for tbx, P_, ax_, face, dr, vals in ((plat[0], SLp, "x", plat[0].x1, "-x", [300, 1000, 1700]),
                                         (plat[1], SRp, "x", plat[1].x0, "+x", [300, 1000, 1700]),
                                         (plat[2], SF, "y", plat[2].y1, "-y", [300, W / 2 - 200, W / 2 + 200, W - 300]),
                                         (plat[-1], SB, "y", plat[-1].y0, "+y", [300, W / 2 - 200, W / 2 + 200, W - 300])):
        for v in vals:
            if ax_ == "x":
                b.hole(tbx.id, f"J-CL-{P_.id}", "tube_side", face, v, 280, dr, 4.5, tb, "SCREW-4x30", through=True,
                       note="в ближней стенке Ø10 — доступ")
                b.hole(P_.id, f"J-CL-{P_.id}", "pilot", P_.x1 if dr == "-x" else P_.x0, v, 280, dr, 3, 10)
            else:
                b.hole(tbx.id, f"J-CL-{P_.id}", "tube_side", v, face, 280, dr, 4.5, tb, "SCREW-4x30", through=True,
                       note="в ближней стенке Ø10 — доступ")
                b.hole(P_.id, f"J-CL-{P_.id}", "pilot", v, P_.y1 if dr == "-y" else P_.y0, 280, dr, 3, 10)
    for S_, B_, n_ in ((SF, SLp, "+y"), (SB, SLp, "-y"), (SF, SRp, "+y"), (SB, SRp, "-y")):
        b.conf(S_, B_, n_, "z", [z0 + 40, z1 - 40], f"J-{S_.id}-{B_.id}")
    # нижняя крышка-рамка
    U = [b.part("UC-L", "Крышка нижняя", c, c, z0, bx0, L - c, z0 + T, "LDSP16", color, "carcass", edges={"+x": "ABS2"}),
         b.part("UC-R", "Крышка нижняя", bx1, c, z0, W - c, L - c, z0 + T, "LDSP16", color, "carcass", edges={"-x": "ABS2"}),
         b.part("UC-F", "Крышка нижняя", bx0, c, z0, bx1, by0, z0 + T, "LDSP16", color, "carcass", edges={"+y": "ABS2"}),
         b.part("UC-B", "Крышка нижняя", bx0, by1, z0, bx1, L - c, z0 + T, "LDSP16", color, "carcass", edges={"-y": "ABS2"})]
    b.conf(SLp, U[0], "+x", "y", [300, 1000, 1700], "J-CLL-UCL")
    b.conf(SRp, U[1], "-x", "y", [300, 1000, 1700], "J-CLR-UCR")
    b.conf(SF, U[2], "+y", "x", [bx0 + 200, W / 2, bx1 - 200], "J-CLF-UCF")
    b.conf(SB, U[3], "-y", "x", [bx0 + 200, W / 2, bx1 - 200], "J-CLB-UCB")
    # цоколь вокруг опор
    PZ0, PZ1 = 20, z0
    sk = [b.part("SK-F", "Цоколь", bx0 - T, by0 - T, PZ0, bx1 + T, by0, PZ1, "LDSP16", "black", "base", edges={"-z": "PVC04"}),
          b.part("SK-B", "Цоколь", bx0 - T, by1, PZ0, bx1 + T, by1 + T, PZ1, "LDSP16", "black", "base", edges={"-z": "PVC04"}),
          b.part("SK-L", "Цоколь", bx0 - T, by0, PZ0, bx0, by1, PZ1, "LDSP16", "black", "base", edges={"-z": "PVC04"}),
          b.part("SK-R", "Цоколь", bx1, by0, PZ0, bx1 + T, by1, PZ1, "LDSP16", "black", "base", edges={"-z": "PVC04"})]
    for S_, B_, n_ in ((sk[0], sk[2], "+y"), (sk[0], sk[3], "+y"), (sk[1], sk[2], "-y"), (sk[1], sk[3], "-y")):
        b.conf(S_, B_, n_, "z", [PZ0 + 30, PZ1 - 30], f"J-{S_.id}-{B_.id}")
    for lg in legs:
        if lg.x0 == bx0:
            b.hole(lg.id, f"J-SK-{lg.id}", "tube_side", bx0 + tb, (lg.y0 + lg.y1) / 2, 120, "-x", 4.5, tb, "SCREW-4x30",
                   through=True, note="в ближней стенке Ø10 — доступ")
            b.hole(sk[2].id, f"J-SK-{lg.id}", "pilot", bx0, (lg.y0 + lg.y1) / 2, 120, "-x", 3, 10)
        else:
            b.hole(lg.id, f"J-SK-{lg.id}", "tube_side", lg.x0, (lg.y0 + lg.y1) / 2, 120, "+x", 4.5, tb, "SCREW-4x30",
                   through=True, note="в ближней стенке Ø10 — доступ")
            b.hole(sk[3].id, f"J-SK-{lg.id}", "pilot", bx1, (lg.y0 + lg.y1) / 2, 120, "+x", 3, 10)
    # ламели
    n_sl = 26
    for i in range(n_sl):
        y = c + 30 + i * (L - 2 * c - 60 - 53) / (n_sl - 1)
        for half in range(2):
            x0 = c + tb + 5 if half == 0 else W / 2 + tb / 2 + 5
            x1 = W / 2 - tb / 2 - 5 if half == 0 else W - c - tb - 5
            b.part(f"SLAT-{i + 1}-{half + 1}", "Ламель", x0, y, 300, x1, y + 53, 308, "SLAT", "O", "slats", kind="buy")
    b.buy("SLAT", "Ламель гнутоклеёная 53 × 8 + латодержатели на трубу 40", f"{n_sl * 2} шт. L = {(W / 2 - tb / 2 - 5) - (c + tb + 5):.0f}",
          n_sl * 2, "кандидат", "В-44")
    # изголовье
    hb_top = 1300
    posts = []
    for k, x in enumerate((W * 0.2, W * 0.8 - tb), 1):
        p_ = b.tube(f"HB-P{k}", "Стойка изголовья", x, L, z0, x + tb, L + 20, hb_top - 60, "TUBE40x20x2", "black", "z")
        posts.append(p_)
        b.derived["frames"].append({"name": f"Стойка изголовья {k}", "tubes": [p_.id]})
        for zz in (272, 292):
            b.hole(p_.id, f"J-HBP{k}", "plate_hole", x + 20, L + 20, zz, "-y", 7, 20, "BOLT-M6x45", through=True)
            b.hole(SB.id, f"J-HBP{k}", "bolt_hole", x + 20, L, zz, "-y", 7, T, through=True)
            b.hole(plat[-1].id, f"J-HBP{k}", "rivnut6", x + 20, plat[-1].y1, zz, "-y", 9, 2, "RIVNUT-M6", through=True)
    hp = b.part("HB-PANEL", "Панель изголовья", 0, L + 20, z0, W, L + 38, hb_top, "LDSP18", color, "headboard",
                edges={"-x": "ABS2", "+x": "ABS2", "+z": "ABS2", "-z": "ABS2"})
    for p_ in posts:
        for zz in (500, 900, 1150):
            b.hole(p_.id, f"J-HBPAN-{p_.id}", "tube_side", (p_.x0 + p_.x1) / 2, L, zz, "+y", 4.5, 20, "SCREW-4x30", through=True,
                   note="в ближней стенке Ø10 — доступ")
            b.hole(hp.id, f"J-HBPAN-{p_.id}", "pilot", (p_.x0 + p_.x1) / 2, L + 20, zz, "+y", 3, 10)
    for x in (W * 0.35, W * 0.65):
        b.hole(hp.id, "J-HB-WALL", "wall_bolt", x, L + 20, 1150, "+y", 6, 18, "ANCHOR-M8", through=True,
               note="к стене, под заглушку")
    # лицевая часть изголовья (02.11): закрывает стойки спереди; вид — по опции headboard
    FASTENERS.setdefault("SCREW-4x60", ("Саморез 4 × 60", "конфирмат-саморез по дереву, с тыла через заднюю панель и стойку",
                                        "типовой", "", "шт"))
    ft = 22 if hb == "fluted" else 18
    fz0 = 330
    FP = b.part("HB-FRONT", {"flat": "Панель изголовья лицевая", "fluted": "Панель изголовья лицевая рифлёная",
                              "soft": "Панель изголовья лицевая (под мягкие панели)"}[hb],
                0, L - ft, fz0, W, L, hb_top, "MDF22" if hb == "fluted" else "LDSP18", color, "headboard",
                edges={} if hb == "fluted" else {"-x": "ABS2", "+x": "ABS2", "+z": "ABS2", "-z": "ABS2"})
    for p_ in posts:
        for zz in (420, 780, 1180):
            xc = (p_.x0 + p_.x1) / 2
            j = f"J-HBFRONT-{p_.id}"
            b.hole(hp.id, j, "screw_face", xc, L + 38, zz, "-y", 4.5, 18, "SCREW-4x60", through=True, cs=True,
                   note="с тыла (сторона стены), через заднюю панель и стойку")
            b.hole(p_.id, j, "tube_side", xc, L + 20, zz, "-y", 4.5, 20, through=True)
            b.hole(FP.id, j, "pilot", xc, L, zz, "-y", 3, 12)
    if hb == "fluted":
        n_g = int((W - 40) // 60)
        off = (W - n_g * 60) / 2
        for i in range(n_g):
            a = off + i * 60 + 20
            b.part(f"HB-G{i + 1}", "Канавка рифления (фрезеровка)", a, L - ft, fz0 + 10, a + 20, L - ft + 6, hb_top - 10,
                   "MILL", "groove", "headboard", kind="buy_part")
        b.notes.append(f"Лицевая панель изголовья: МДФ 22, фрезеровка {n_g} канавок 20 × 6 с шагом 60, окраска / плёнка в цвет (В-44).")
    if hb == "soft":
        n_s = 4 if mw <= 1600 else 5
        gap = 14
        pw2 = (W - 60 - gap * (n_s - 1)) / n_s
        for i in range(n_s):
            x0s = 30 + i * (pw2 + gap)
            bk = b.part(f"HB-SP{i + 1}", "Мягкая панель, основа", x0s, L - ft - 9, 540, x0s + pw2, L - ft, hb_top - 40, "PLY9", "raw",
                        "headboard", unit="Мягкая панель, основа")
            b.part(f"HB-SPU{i + 1}", "Мягкая панель, обивка", x0s, L - ft - 49, 540, x0s + pw2, L - ft - 9, hb_top - 40, "UPH",
                   "beige", "headboard", kind="buy")
            for z in (700, 1100):
                b.screws_into(FP, bk, "-y", "x", [x0s + 60, x0s + pw2 - 60], "PANEL-SCREW", f"J-{bk.id}", pilot=(2.5, 6), at=z)
        b.buy("UPH-PANEL", "Обтяжка мягких панелей изголовья: поролон 30 + ткань", f"{n_s} панели {pw2:.0f} × {hb_top - 40 - 540} (кандидат)",
              n_s, "кандидат", "В-44")
    if led != "off":
        # подсветка (02.11): профиль с лентой по наружному периметру рамы основания, свет вниз на пол
        lz0, lz1 = 238, 254
        sides = [("LED-F", bx0, by0 - 16, bx1, by0), ("LED-B", bx0, by1, bx1, by1 + 16),
                 ("LED-L", bx0 - 16, by0, bx0, by1), ("LED-R", bx1, by0, bx1 + 16, by1)]
        per = 0
        for pid, xa, ya, xb, yb in sides:
            b.part(pid, "Профиль LED с лентой 3000 K", xa, ya, lz0, xb, yb, lz1, "LED", "black", "decor", kind="buy")
            per += max(xb - xa, yb - ya)
        b.buy("LED-STRIP", "Лента LED 24 В тёплая 3000 K, 9,6 Вт/м, IP20", f"{per / 1000:.1f} м по периметру основания (кандидат)",
              round(per / 1000, 1), "кандидат", "В-44", "м")
        b.buy("LED-PROFILE", "Профиль алюминиевый накладной 16 × 16 с рассеивателем, чёрный",
              f"4 отрезка, всего {per / 1000:.1f} м; на двусторонний скотч 3M + 2 самореза на отрезок (кандидат)",
              4, "кандидат", "В-44")
        b.buy("LED-PSU", "Блок питания 24 В 60 Вт", "скрытый, крепится к раме основания (кандидат)", 1, "кандидат", "В-44")
        b.buy("LED-SENSOR", "Датчик движения / выключатель для ленты", "ИК-датчик под кроватью или выключатель у изголовья (кандидат)",
              1, "кандидат", "В-44")
        b.notes.append("Подсветка: профиль 16 × 16 по наружному периметру рамы основания на высоте ≈240, свет вниз; "
                       "блок питания на раме, кабель к розетке у изголовья.")
    b.part("MATTRESS", "Матрас (не входит)", 50, 50, 308, W - 50, L - 50, 528, "APPL", "white", "bedding", kind="context")
    b.derived.setdefault("kdec", [])
    b.derived.update(width=W, depth=L + 38, height=hb_top, plinth=z0)
    _check(b, "Отступ основания от края", inset, bx0)
    b.notes += ["Каркас сварной 40 × 40 × 2: основание на 6 опорах + рама платформы; облицовка ЛДСП 16 саморезами через трубу.",
                "Изголовье: 2 стойки 40 × 20 на болтах M6 в заклёпочные гайки задней поперечины + к стене."]
    b.derived["kdec"] = ["Изголовье: стойки крепятся болтами сквозь заднюю облицовку к раме (в каталоге стойки только за "
                         "платформой); цоколь — панели ЛДСП вокруг опор вместо сплошного короба.",
                         "Изголовье двухслойное (02.11): стойки между задней и лицевой панелью; лицевая — по опции "
                         "(гладкая ЛДСП 18 / рифлёная МДФ 22 с канавками / мягкие панели на ЛДСП 18)."]
    _kq(b, "В-44", "В-21")
    return b


def floating_bed_wood(o):
    mw, color = int(o["size"]), o["color"]
    c, ml = 20, 2000
    W = mw + 2 * c
    y0, y1 = c, c + ml
    rb, rh = 45, 95
    base_z1 = 145
    lz0, lz1 = base_z1, base_z1 + rh
    top = lz1 + 20
    rail_z1 = lz0 + 235
    inset = 140
    b = Build("ARV-BED-002W", REV, STATUS, {"size": mw, "color": color})
    bx0, bx1 = inset, W - inset
    B = [b.part("BS-L", "Основание, продольный брус", bx0, inset, 0, bx0 + rb, y1, base_z1, "BEAM45x145", "black", "base"),
         b.part("BS-R", "Основание, продольный брус", bx1 - rb, inset, 0, bx1, y1, base_z1, "BEAM45x145", "black", "base"),
         b.part("BS-F", "Основание, поперечный брус", bx0 + rb, inset, 0, bx1 - rb, inset + rb, base_z1, "BEAM45x145", "black", "base"),
         b.part("BS-B", "Основание, поперечный брус", bx0 + rb, y1 - rb, 0, bx1 - rb, y1, base_z1, "BEAM45x145", "black", "base"),
         b.part("BS-C", "Основание, средний брус", W / 2 - rb / 2, inset + rb, 0, W / 2 + rb / 2, y1 - rb, base_z1, "BEAM45x145",
                "black", "base")]
    for cr in (B[2], B[3]):
        for lo, n_ in ((B[0], "+x"), (B[1], "-x")):
            b.screws_into(lo, cr, n_, "z", [35, 80], "WSCREW-5x80", f"J-{lo.id}-{cr.id}", pilot=(3.5, 40),
                          at=(cr.y0 + cr.y1) / 2)
        b.screws_into(cr, B[4], "+y" if cr is B[2] else "-y", "z", [35, 80], "WSCREW-5x80", f"J-{cr.id}-C", pilot=(3.5, 40),
                      at=W / 2)
    lad = [(c, 200), (W - c - 2 * rb - 200, 200), (W / 2 - rb - 60, 120)]
    rails = []
    for i, (x, blk) in enumerate(lad, 1):
        ra = b.part(f"L{i}-A", "Лестница, брус", x, y0, lz0, x + rb, y1, lz1, "BEAM45x95", "raw", "frame")
        rbm = b.part(f"L{i}-B", "Лестница, брус", x + rb + blk, y0, lz0, x + 2 * rb + blk, y1, lz1, "BEAM45x95", "raw", "frame")
        rails += [ra, rbm]
        for k in range(5):
            yy = y0 + k * (ml - rb) / 4
            bk = b.part(f"L{i}-K{k + 1}", "Лестница, вставка", x + rb, yy, lz0, x + rb + blk, yy + rb, lz1, "BEAM45x95", "raw", "frame")
            b.screws_into(ra, bk, "+x", "z", [lz0 + 30, lz1 - 30], "WSCREW-5x80", f"J-{bk.id}A", pilot=(3.5, 40), at=yy + rb / 2)
            b.screws_into(rbm, bk, "-x", "z", [lz0 + 30, lz1 - 30], "WSCREW-5x80", f"J-{bk.id}B", pilot=(3.5, 40), at=yy + rb / 2)
            under = [bb for bb in B if bb.x0 < bk.x1 and bb.x1 > bk.x0 and bb.y0 < bk.y1 and bb.y1 > bk.y0]
            for bb in under:
                xm = min(max((max(bb.x0, bk.x0) + min(bb.x1, bk.x1)) / 2, bk.x0 + 50), bk.x1 - 50)
                b.screws_into(bk, bb, "-z", "x", [xm], "WSCREW-6x140", f"J-{bk.id}-{bb.id}", pilot=(3.5, 40), at=yy + rb / 2)
    sw = 95 if mw <= 1600 else 120
    n = 14
    gap = (ml - n * sw) / (n - 1)
    for i in range(n):
        yy = y0 + i * (sw + gap)
        sl = b.part(f"SL-{i + 1}", "Ламель", c, yy, lz1, W - c, yy + sw, top, "PINE20", "raw", "slats")
        for r in rails:
            b.screws_into(sl, r, "-z", "x", [(r.x0 + r.x1) / 2], "WSCREW-4x40", f"J-{sl.id}-{r.id}", pilot=(2.5, 25),
                          at=yy + sw / 2)
    hb_top = 1220
    RL = b.part("RAIL-L", "Боковина", 0, y0, lz0, c, y1, rail_z1, "PINE20", color, "rails", edges={})
    RR = b.part("RAIL-R", "Боковина", W - c, y0, lz0, W, y1, rail_z1, "PINE20", color, "rails", edges={})
    FT = b.part("FOOT", "Изножье", 0, 0, lz0, W, c, rail_z1, "PINE20", color, "rails", edges={})
    LL = b.part("HB-LL", "Изголовье, стойка", 0, y1, 0, 95, y1 + rb, hb_top - 45, "BEAM45x95", color, "headboard")
    LR = b.part("HB-LR", "Изголовье, стойка", W - 95, y1, 0, W, y1 + rb, hb_top - 45, "BEAM45x95", color, "headboard")
    HT = b.part("HB-T", "Изголовье, верхний брус", 0, y1, hb_top - 45, W, y1 + rb, hb_top, "BEAM45x95", color, "headboard")
    HP = b.part("HB-P", "Изголовье, панель", 95, y1 + rb, lz0, W - 95, y1 + rb + 9, hb_top, "PLY9", color, "headboard")
    b.screws_into(rails[0], RL, "-x", "y", [y0 + 150, y0 + ml / 2, y1 - 150], "WSCREW-5x60", "J-RAIL-L", pilot=(3.5, 15),
                  at=(lz0 + lz1) / 2)
    b.screws_into(rails[3], RR, "+x", "y", [y0 + 150, y0 + ml / 2, y1 - 150], "WSCREW-5x60", "J-RAIL-R", pilot=(3.5, 15),
                  at=(lz0 + lz1) / 2)
    for r in rails:
        b.screws_into(FT, r, "+y", "x", [(r.x0 + r.x1) / 2], "WSCREW-5x80", f"J-FOOT-{r.id}", pilot=(3.5, 50),
                      at=(lz0 + lz1) / 2)
    for r, Lg in ((rails[0], LL), (rails[3], LR)):
        b.screws_into(Lg, r, "-y", "x", [(max(r.x0, Lg.x0) + min(r.x1, Lg.x1)) / 2], "WSCREW-5x80", f"J-{Lg.id}-{r.id}",
                      pilot=(3.5, 50), at=(lz0 + lz1) / 2)
    for Lg in (LL, LR):
        b.screws_into(HT, Lg, "-z", "x", [(Lg.x0 + Lg.x1) / 2], "WSCREW-5x80", f"J-HT-{Lg.id}", pilot=(3.5, 50), at=y1 + rb / 2)
    b.screws_into(HP, HT, "-y", "x", [300, W / 2, W - 300], "WSCREW-4x40", "J-HP-HT", pilot=(2.5, 25), at=hb_top - 22)
    b.buy("GLUE-PVA", "Клей ПВА D3 по дереву", "соединения лестниц и основания", 0.2, "типовой", "", "кг")
    b.part("MATTRESS", "Матрас (не входит)", c + 5, y0 + 5, top, W - c - 5, y1 - 5, top + 220, "APPL", "white", "bedding",
           kind="context")
    b.derived.update(width=W, depth=y1 + rb + 9, height=hb_top, plinth=lz0)
    _check(b, "Ламели между боковинами", W - 2 * c, mw)
    b.notes += ["Основа — открытый план Ana White «Simple Floating Bed», переведённый в мм (брус 45 × 95 / 45 × 145, щит 20).",
                "Добавлен средний брус основания под среднюю лестницу (в каталоге средняя лестница опиралась только по концам)."]
    b.derived["kdec"] = ["Средний брус основания 45 × 145 добавлен под среднюю раму-лестницу (в каталоге его нет)."]
    _kq(b, "В-50")
    return b


def bed_cocoon(o):
    mw, fab, color = int(o["size"]), o["fabric"], o["color"]
    W, L = mw + 80, 2080
    PW = W + 1300
    x0 = 650
    t = 25
    b = Build("ARV-BED-003", REV, STATUS, {"size": mw, "fabric": fab, "color": color})
    X0, X1 = x0 + 30, x0 + W - 30
    Y0, Y1 = 30, L - 30
    ring = [b.part("RG-L", "Рамка основания", X0, Y0, 60, X0 + 100, Y1, 76, "LDSP16", "INNER", "carcass"),
            b.part("RG-R", "Рамка основания", X1 - 100, Y0, 60, X1, Y1, 76, "LDSP16", "INNER", "carcass"),
            b.part("RG-F", "Рамка основания", X0 + 100, Y0, 60, X1 - 100, Y0 + 100, 76, "LDSP16", "INNER", "carcass"),
            b.part("RG-B", "Рамка основания", X0 + 100, Y1 - 100, 60, X1 - 100, Y1, 76, "LDSP16", "INNER", "carcass")]
    for s_ in (ring[2], ring[3]):
        b.screws_into(ring[0], s_, "+x", "y", [(s_.y0 + s_.y1) / 2], "SCREW-4x30", f"J-RG-L-{s_.id}", pilot=(3, 12), at=68)
    SL = b.part("FR-L", "Каркас, борт", X0, Y0, 76, X0 + t, Y1, 330, "LDSP25", "INNER", "carcass")
    SR = b.part("FR-R", "Каркас, борт", X1 - t, Y0, 76, X1, Y1, 330, "LDSP25", "INNER", "carcass")
    FT = b.part("FR-F", "Каркас, изножье", X0 + t, Y0, 76, X1 - t, Y0 + t, 330, "LDSP25", "INNER", "carcass")
    HB = b.part("FR-B", "Каркас, изголовье", X0 + t, Y1 - t, 76, X1 - t, Y1, 330, "LDSP25", "INNER", "carcass")
    for S, n_ in ((SL, "+x"), (SR, "-x")):
        b.bed_bolt(S, FT, n_, "z", [130, 280], f"J-{S.id}-F", "+")
        b.bed_bolt(S, HB, n_, "z", [130, 280], f"J-{S.id}-B", "-")
    for S, R in ((SL, ring[0]), (SR, ring[1])):
        b.conf(R, S, "+z", "y", [Y0 + 200, (Y0 + Y1) / 2, Y1 - 200], f"J-{R.id}-{S.id}")
    b.conf(ring[2], FT, "+z", "x", [X0 + 300, (X0 + X1) / 2, X1 - 300], "J-RG-F")
    b.conf(ring[3], HB, "+z", "x", [X0 + 300, (X0 + X1) / 2, X1 - 300], "J-RG-B")
    pls = [b.part("PL-F", "Цоколь", x0 + 60, 60, 0, x0 + W - 60, 76, 60, "LDSP16", "black", "base"),   # 14.11: кромка «-y» была на пласти — убрана
           b.part("PL-B", "Цоколь", x0 + 60, L - 76, 0, x0 + W - 60, L - 60, 60, "LDSP16", "black", "base"),
           b.part("PL-L", "Цоколь", x0 + 60, 76, 0, x0 + 76, L - 76, 60, "LDSP16", "black", "base"),
           b.part("PL-R", "Цоколь", x0 + W - 76, 76, 0, x0 + W - 60, L - 76, 60, "LDSP16", "black", "base")]
    for a_ in (pls[0], pls[1]):
        for s_ in (pls[2], pls[3]):
            b.dowel(a_, s_, "+y" if a_ is pls[0] else "-y", "z", [30], f"J-{a_.id}-{s_.id}")
    b.conf(ring[0], pls[2], "-z", "y", [400, 1000, 1600], "J-RGL-PL")
    b.conf(ring[1], pls[3], "-z", "y", [400, 1000, 1600], "J-RGR-PL")
    for S in (SL, SR):
        for y in (300, 1000, 1700):
            b.hole(S.id, "J-ANGLE", "pilot", S.x1 if S is SL else S.x0, y, 300, "-x" if S is SL else "+x", 3, 12, "SCREW-4x16C",
                   note="уголок опорный основания")
    b.buy("ANGLE", "Уголок опорный под основание", "сталь 40 × 40 × 3, L 60 (кандидат)", 6, "кандидат", "В-44")
    b.part("BASE", "Основание ортопедическое", X0 + t + 2, Y0 + t + 2, 300, X1 - t - 2, Y1 - t - 2, 340, "LIFT", "steel",
           "interior", kind="buy")
    b.buy("BASE", "Основание ортопедическое рамное", f"{mw} × 2000, ламели 53 × 8 (кандидат)", 1, "кандидат", "В-44")
    for pid, a_ in (("UPH-L", (x0, 0, 60, X0, L, 360)), ("UPH-R", (X1, 0, 60, x0 + W, L, 360)),
                    ("UPH-F", (X0, 0, 60, X1, Y0, 360)), ("UPH-T", (X0, Y0, 330, X1, Y0 + 60, 360))):
        b.part(pid, "Обивка (поролон 30 + ткань)", *a_, "UPH", fab, "carcass", kind="buy")
    b.buy("UPH", "Обивка кровати: поролон 30 / синтепон, ткань", f"ткань «{fab}», расход по раскрою обивщика (кандидат)", 1,
          "кандидат", "В-47", "компл")
    b.part("MATTRESS", "Матрас (не входит)", x0 + 40, 40, 360, x0 + W - 40, L - 20, 580, "APPL", "white", "bedding", kind="context")
    # стеновая панель
    half = PW / 2
    WP = [b.part(f"WP-{k}", "Панель стеновая", k_ * half, L + 40, 0, (k_ + 1) * half, L + 56, 2500, "LDSP16", color, "headboard",
                 unit="Панель стеновая", edges={"+z": "ABS2", ("-x" if k_ == 0 else "+x"): "ABS2"})
          for k, k_ in ((1, 0), (2, 1))]
    for P_ in WP:
        for x in (P_.x0 + 200, P_.x1 - 200):
            for z in (400, 1300, 2200):
                b.hole(P_.id, "J-WP-WALL", "wall_bolt", x, L + 40, z, "+y", 6, T, "ANCHOR-M8", through=True,
                       note="к стене; под мягкими панелями / тумбами")
    sx0, sx1 = 600, PW - 600
    ns = 4
    sw_ = (sx1 - sx0) / ns
    for i in range(ns):
        a = sx0 + i * sw_ + 4
        bk = b.part(f"SP-{i + 1}", "Мягкая панель, основа", a, L + 31, 300, a + sw_ - 8, L + 40, 1500, "PLY9", "raw", "headboard",
                    unit="Мягкая панель, основа")
        b.part(f"SPU-{i + 1}", "Мягкая панель, обивка", a, L + 10, 300, a + sw_ - 8, L + 31, 1500, "UPH", fab, "headboard",
               kind="buy")
        Pw = WP[0] if a + sw_ / 2 < half else WP[1]
        for z in (400, 900, 1400):
            b.screws_into(Pw, bk, "-y", "x", [a + 60, a + sw_ - 68], "PANEL-SCREW", f"J-{bk.id}", pilot=(2.5, 6), at=z)
    b.buy("UPH-PANEL", "Обтяжка мягких панелей: поролон 20 + ткань", f"{ns} панели {sw_ - 8:.0f} × 1200 (кандидат)", ns,
          "кандидат", "В-47")
    nsk = 0
    for k, nx in enumerate((x0 - 600, x0 + W + 100), 1):
        pre = f"N{k}-"
        yc0, yc1 = L + 40 - 350 + TF + 3.5, L + 40 - TB
        cN = b.carcass(pre, nx, nx + 500, 450, 650, yc0, yc1, color, vis_bottom=True, label=f"тумба {k}")
        b.drawers(pre, cN, cN["L"], cN["R"], cN["BOT"].z1, cN["TOP"].z0, _fronts_col(nx, nx + 500, 450, 650, n=1), color,
                  _inner(color), handle=None, tipon=True)
        for d_ in b.P:
            if d_.id == f"{pre}FRONT-1":
                d_.y0, d_.y1 = yc0 - TF - 3.5, yc0 - 3.5
        for h in b.holes:
            if h["part"] == f"{pre}FRONT-1":
                h["y"] = yc0 - 3.5 if h["dir"] == "-y" else yc0 - TF - 3.5
        b.hangers(pre, cN, "навес скрытый под ХДФ 4 + шина на стеновую панель (кандидат)", note="В-21")
        b.part(f"SCONCE-{k}", "Бра настенное", nx + 230, L - 30, 1250, nx + 270, L + 40, 1450, "SCONCE", "black", "decor",
               kind="buy")
        nsk += 1
    b.buy("SCONCE", "Бра настенное", "чёрное, LED тёплый, скрытая проводка в стеновой панели (кандидат)", nsk, "кандидат", "В-51")
    b.derived.update(width=PW, depth=L + 56, height=2500, plinth=60)
    _check(b, "Ширина стеновой панели = кровать + 2 × 650", PW, W + 1300)
    b.notes += ["Кровать — каркас ЛДСП 25 под обивку на кроватных стяжках, рамка основания ЛДСП 16 на цоколе 60; "
                "обивка — обивщик по кандидату.",
                "Стеновая панель — 2 листа ЛДСП 16 (стык по центру) на анкерах; мягкие панели — фанера 9 + поролон + ткань, "
                "крепление саморезами сзади до монтажа на стену."]
    b.derived["kdec"] = ["Мягкие панели только в зоне кровати (4 шт. по центру), тумбы навешены на стеновую панель "
                         "(в каталоге мягкие панели во всю ширину, за тумбами)."]
    _kq(b, "В-47", "В-21", "В-51")
    return b


MODELS.update({
    "ARV-BED-001": ("Кровать «Самал»", bed_lift), "ARV-BED-002": ("Кровать «Нимб»", floating_bed),
    "ARV-BED-002W": ("Кровать «Нимб Wood»", floating_bed_wood), "ARV-BED-003": ("Кровать «Кокон»", bed_cocoon),
    "ARV-LIV-001": ("ТВ-зона «Экран»", tv_unit), "ARV-LIV-002": ("Стеллаж «Грань»", shelf_divider),
    "ARV-OFF-002": ("Бенч «Ряд»", bench_system), "ARV-OFF-006": ("Шкаф «Архив»", office_cabinet),
    "ARV-WRD-001": ("Шкаф «Арна»", wardrobe_hinged), "ARV-WRD-002": ("Шкаф-купе «Каскад»", wardrobe_sliding),
    "ARV-WRD-003": ("Прихожая «Порог»", hallway_open), "ARV-WRD-004": ("Шкаф «Стена»", wardrobe_flush),
    "ARV-WRD-005": ("Шкаф «Витрина»", glass_cabinet), "ARV-WRD-006": ("Гардеробная «Каркас»", open_wardrobe),
    "ARV-WRD-007": ("Прихожая «Вход»", hallway_set),
})
REST = ["ARV-BED-001", "ARV-BED-002", "ARV-BED-002W", "ARV-BED-003", "ARV-LIV-001", "ARV-LIV-002", "ARV-OFF-002", "ARV-OFF-006",
        "ARV-WRD-001", "ARV-WRD-002", "ARV-WRD-003", "ARV-WRD-004", "ARV-WRD-005", "ARV-WRD-006", "ARV-WRD-007"]

KQ2 = {
    "В-44": ("Основание кровати: покупное основание (с газлифтами / рамное) — изготовитель, размер, шаблон крепления к "
             "бортам, усилие газлифтов, ламели и латодержатели", "проём короба, отверстия механизма", "Arvello",
             "паспорт основания — довести до R02E"),
    "В-45": ("Двери-купе: система профиля (изготовитель, профиль, ролики, направляющие), формулы раскроя дверей и "
             "заполнения ЛДСП 10 / зеркала 4, доводчики", "двери, направляющие", "Arvello + поставщик системы",
             "каталог системы"),
    "В-46": ("Стеклянные двери в алюминиевой рамке 20: изготовитель, профиль, стекло 4 тонированное (закалка), петли "
             "для рамки и их присадка", "двери, планки петель", "Arvello + поставщик", "образец двери, каталог петель"),
    "В-47": ("Обивка: поролон (марка, толщина), ткань (артикул, расход), технология обтяжки панелей и каркаса кровати, "
             "огнестойкость / износостойкость ткани", "мягкие элементы", "обивщик + Arvello", "образец 300 × 300"),
    "В-48": ("Устойчивость: крепление к стене / потолку (уголки, анкеры), тип стены у клиента; для свободностоящих "
             "стеллажей — крепление к полу и потолку", "монтаж, безопасность", "Arvello + монтажник",
             "расчёт / испытание на опрокидывание"),
    "В-49": ("Откидные фасады: петли для откидных, подъёмник / ограничитель, TIP-ON — артикулы и присадка",
             "фасады консоли", "Arvello", "каталог Blum — довести до R02E"),
    "В-50": ("Брус и щит «Нимб Wood»: порода (сосна / берёза), влажность ≤ 12 %, строгание, сорт; покраска / масло; "
             "саморезы и клей", "все детали кровати", "Arvello + столярный цех", "паспорт материала, проба покрытия"),
    "В-51": ("Бра и электрика у кровати: модель бра, скрытая проводка в стеновой панели, выключатели, розетки у тумб",
             "стеновая панель", "Arvello + электрик", "схема электрики"),
}
