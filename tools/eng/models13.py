"""Инженерные ядра R01E для 13 моделей тумб, комодов и столов (на общем ядре eng/cab.py).

Вид — как в каталоге (builders_more.py); конструкция — правила «Самал» R02E (корпус, ящики Blum, Minifix)
и «Опора» R03E (сварные рамы, столешница на резьбовых втулках). Ревизия R01E: инженерное предложение,
manufacturing_allowed = False; закрытые по документам узлы и кандидаты — в QUESTIONS / DECISIONS модели.
"""
from __future__ import annotations

from .cab import GAP, T, TB, TF, TIPON_GAP, Build

REV = "R01E"
STATUS = ("инженерное предложение R01E: вид как в каталоге; ящики Blum 560H и стяжки Minifix — по документам; "
          "остальная фурнитура — кандидаты; не для изготовления")


def _inner(color):
    return color if color == "W" else "INNER"


def _check(b, name, exp, act):
    b.checks.append((name, exp, round(act, 3) if isinstance(act, float) else act))


def _fronts_col(x0, x1, z0, z1, heights=None, n=None):
    """Фасады в колонке x0..x1 между z0 и z1: зазор 1,5 по краям, 3 между фасадами."""
    if heights is None:
        hs = [(z1 - z0) / n] * n
    else:
        hs = heights
    out, z = [], z0
    for h in hs:
        out.append((x0 + GAP / 2, x1 - GAP / 2, z + GAP / 2, z + h - GAP / 2))
        z += h
    return out


# =============================================================================== комод «Самал»
def chest(o):
    color = o["color"]
    W, H, D, PL = 800, 850, 450, 60
    b = Build("ARV-NST-002", REV, STATUS, {"color": color})
    c = b.carcass("", 0, W, PL, H, TF, D - TB, color, label="корпус")
    b.plinth("", c, PL, front=50, side=20, back=16)
    fr = _fronts_col(0, W, PL, H, n=4)
    b.drawers("", c, c["L"], c["R"], c["BOT"].z1, c["TOP"].z0, fr, color, _inner(color), handle="bar128", handle_through=True,
              box_max=170)
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = цоколь + боковина", H, PL + (c["L"].z1 - c["L"].z0))
    _check(b, "Глубина = фасад + корпус + ХДФ", D, TF + (c["L"].y1 - c["L"].y0) + TB)
    b.notes += ["Как тумба «Самал»: корпус ЛДСП 16, фасады ЛДСП 18 в декоре, цоколь ЛДСП 16 чёрная, ХДФ 4 накладная.",
                "Ручки: винты M4 × 40 сквозь фасад и стенку короба — короба на полную высоту проёма (отличие от тумбы)."]
    return b


# =============================================================================== ТВ-тумба «Кок-Тобе»
def tv_floor(o):
    color = o["color"]
    W, H, D, LEG = 1600, 450, 400, 60
    b = Build("ARV-NST-003", REV, STATUS, {"color": color})
    c = b.carcass("", 0, W, LEG, H, TF, D - TB, color, partitions=[(500, T, "Стойка"), (W - 516, T, "Стойка")],
                  shelves=[(516, W - 516, 240, "Полка ниши", "+")], vis_bottom=True, label="корпус")
    pts = [(66, 76), (W - 66, 76), (66, D - 76), (W - 66, D - 76)]
    b.feet("", c, LEG, pts, "LEG", 40, name="Ножка 40 × 40 × 60", spec="чёрная, площадка 40 × 40, 4 самореза (кандидат)")
    z0, z1 = LEG, H
    doors = [(GAP / 2, 508 - GAP / 2, z0 + GAP / 2, z1 - GAP / 2), (W - 508 + GAP / 2, W - GAP / 2, z0 + GAP / 2, z1 - GAP / 2)]
    b.doors("", c, [c["L"], c["R"]], doors, color, handle="bar128", hz_from_top=50 - GAP / 2)
    b.derived.update(width=W, depth=D, height=H, plinth=LEG)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = ножка + боковина", H, LEG + (c["L"].z1 - c["L"].z0))
    _check(b, "Ниша между стойками", W - 2 * 516, c["shelves"][0].x1 - c["shelves"][0].x0)
    b.warnings.append("Нагрузка на крышку (телевизор) и прогиб дна между ножками на пролёте 1500 — проверить на образце (В-12); "
                      "при необходимости — 2 средние ножки (П-1).")
    return b


# =============================================================================== «Луна»
def nightstand_float(o):
    color, W = o["color"], int(o["width"])
    D, z0, z1 = 350, 400, 600
    b = Build("ARV-NST-004", REV, STATUS, {"width": W, "color": color})
    yc0 = TF + TIPON_GAP
    c = b.carcass("", 0, W, z0, z1, yc0, D - TB, color, shelves=[(T, W - T, z0 + 54, "Полка ниши", "+")], vis_bottom=True,
                  label="корпус")
    sh = c["shelves"][0]
    fr = [(GAP / 2, W - GAP / 2, sh.z1 + GAP / 2, z1 - GAP / 2)]
    b.drawers("", c, c["L"], c["R"], sh.z1, c["TOP"].z0, fr, color, _inner(color), handle=None, tipon=True)
    b.hangers("", c, "навес скрытый регулируемый под ХДФ 4, кандидат Camar 807 / аналог (В-21)")
    # подсветка и зарядка
    BOT = c["BOT"]
    b.part("LED", "Профиль светодиодный с лентой 2700 K", 20, 40, z0 - 8, W - 20, 60, z0, "LED", "black", "decor", kind="buy")
    for x in (40, W - 40):
        b.hole(BOT.id, "J-LED", "led_screw", x, 50, z0, "+z", 2, 8, "SCREW-3x12", note="крепёж профиля")
    b.hole("BACK", "J-LED", "cable", W - 40, D - TB, z0 + 30, "+y", 10, TB, through=True, note="ввод кабеля питания")
    b.buy("LED", "Профиль LED накладной 16 × 8 + лента 2700 K + блок 12 В", f"длина {W - 40}", 1, "кандидат", "В-27")
    tp = c["TOP"]
    b.hole(tp.id, "J-CHARGER", "cutout_round", W - 105, 165, z1, "-z", 80, T, through=True,
           note="кандидат: встраиваемая беспроводная зарядка под Ø80 (В-27)")
    b.part("CHARGER", "Беспроводная зарядка встраиваемая", W - 150, 120, z1, W - 60, 210, z1 + 4, "CHARGER", "black", "decor",
           kind="buy")
    b.buy("CHARGER", "Беспроводная зарядка встраиваемая Qi 15 Вт", "монтаж в отверстие Ø80 в плите 16, блок питания", 1,
          "кандидат", "В-27")
    b.glows.append([-80, -40, W + 80, D, (255, 196, 120), 150])
    b.derived.update(width=W, depth=D, height=z1 - z0, plinth=0, z_bottom=z0)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (tp.x1 - tp.x0))
    _check(b, "Высота корпуса", z1 - z0, c["L"].z1 - c["L"].z0)
    _check(b, "Глубина = фасад + зазор TIP-ON + корпус + ХДФ", D, TF + TIPON_GAP + (c["L"].y1 - c["L"].y0) + TB)
    _check(b, "Ниша под ящиком, мм в свету", 38, sh.z0 - BOT.z1)
    return b


# =============================================================================== «Волна»
def chest_fluted(o):
    W, color, metal = int(o["width"]), o["color"], o["metal"]
    D, LEGH, H = 450, 150, 900
    FT = 22
    b = Build("ARV-NST-005", REV, STATUS, {"width": W, "color": color, "metal": metal})
    yc0 = FT + TIPON_GAP
    cols = 2 if W >= 1200 else 1
    parts_ = [(W / 2 - T, T, "Стойка"), (W / 2, T, "Стойка")] if cols == 2 else []
    c = b.carcass("", 0, W, LEGH, H, yc0, D - TB, color, partitions=parts_, label="корпус")
    edges = {"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"}
    colsx = [(0, W)] if cols == 1 else [(0, W / 2), (W / 2, W)]
    verts = [c["L"]] + c["parts"] + [c["R"]]
    for j, (xa, xb) in enumerate(colsx):
        L_, R_ = (verts[0], verts[-1]) if cols == 1 else ((verts[0], verts[1]) if j == 0 else (verts[2], verts[3]))
        fr = _fronts_col(xa, xb, LEGH, H, n=3)
        b.drawers(f"C{j + 1}-" if cols == 2 else "", c, L_, R_, c["BOT"].z1, c["TOP"].z0, fr, color, _inner(color), handle=None,
                  tipon=True, front_mat="MDF22", front_t=FT, front_edges=edges, front_unit="Фасад рифлёный", box_max=200)
    # рифление (фрезеровка фасада): декоративная геометрия для 3D
    for p in [q for q in b.P if q.unit == "Фасад рифлёный"]:
        n_ = int((p.x1 - p.x0 - 12) // 32)
        off = (p.x1 - p.x0 - n_ * 32) / 2
        for i in range(n_):
            a = p.x0 + off + i * 32 + 6
            b.part(f"{p.id}-G{i + 1}", "Канавка рифления (фрезеровка)", a, 0, p.z0 + 8, a + 12, 6, p.z1 - 8, "MILL", "groove",
                   "fronts", kind="buy_part")
    # металлическое подстолье
    prof, leg = "TUBE20x20x2", 20
    zr0, zr1 = LEGH - 20, LEGH
    rf = b.tube("BASE-F", "Царга продольная", 40, 40, zr0, W - 40, 60, zr1, prof, metal, "x")
    rb = b.tube("BASE-B", "Царга продольная", 40, D - 60, zr0, W - 40, D - 40, zr1, prof, metal, "x")
    rl = b.tube("BASE-L", "Царга поперечная", 40, 60, zr0, 60, D - 60, zr1, prof, metal, "y")
    rr = b.tube("BASE-R", "Царга поперечная", W - 60, 60, zr0, W - 40, D - 60, zr1, prof, metal, "y")
    rails = [rf, rb, rl, rr]
    if cols == 2:
        rm = b.tube("BASE-M", "Царга поперечная", W / 2 - 10, 60, zr0, W / 2 + 10, D - 60, zr1, prof, metal, "y")
        rails.append(rm)
    legs = []
    for i, (x, y) in enumerate([(40, 40), (W - 60, 40), (40, D - 60), (W - 60, D - 60)], 1):
        lg = b.tube(f"BASE-LEG{i}", "Ножка", x, y, 0, x + leg, y + leg, zr0, prof, metal, "z")
        legs.append(lg)
    for lg in legs:
        for r in (rf, rb, rl, rr):
            if r.x0 <= lg.x0 + 0.1 and lg.x1 <= r.x1 + 0.1 and r.y0 <= lg.y0 + 0.1 and lg.y1 <= r.y1 + 0.1:
                b.weld(lg, r)
        for r in (rl, rr):
            pass
    for r in (rl, rr) + ((rm,) if cols == 2 else ()):
        b.weld(r, rf)
        b.weld(r, rb)
    BOT = c["BOT"]
    for r, along, vals in ((rf, "x", [120, W / 2 - 60 if cols == 2 else W / 2, W - 120]),
                           (rb, "x", [120, W / 2 - 60 if cols == 2 else W / 2, W - 120]),
                           (rl, "y", [D / 2]), (rr, "y", [D / 2])):
        for v in vals:
            p = {"x": (r.x0 + r.x1) / 2, "y": (r.y0 + r.y1) / 2, along: v}
            b.hole(r.id, "J-BASE-BOT", "tube_top", p["x"], p["y"], r.z1, "-z", 4.5, 2, "SCREW-4x13", through=True,
                   note="верхняя стенка; в нижней — Ø8 доступ")
            b.hole(r.id, "J-BASE-BOT", "tube_access", p["x"], p["y"], r.z0, "+z", 8, 2, through=True)
            b.hole(BOT.id, "J-BASE-BOT", "pilot", p["x"], p["y"], BOT.z0, "+z", 3, 10, note="засверловка по раме")
    b.buy("GLIDE-20", "Заглушка трубы 20 × 20 с подпятником M6", "регулируемая, войлок (кандидат)", 4, "кандидат", "В-26")
    b.derived["frames"].append({"name": "Подстолье", "tubes": [p.id for p in rails + legs]})
    b.derived.update(width=W, depth=D, height=H, plinth=LEGH, columns=cols)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = подстолье + корпус", H, zr1 + (c["L"].z1 - c["L"].z0))
    _check(b, "Глубина = фасад + зазор TIP-ON + корпус + ХДФ", D, FT + TIPON_GAP + (c["L"].y1 - c["L"].y0) + TB)
    if cols == 2:
        b.notes.append("Центральная стойка двойная (2 × ЛДСП 16): саморезы профилей Blum с обеих сторон не встречаются.")
    b.warnings.append("Фасады — МДФ 22 с фрезерованным рифлением (канавки 12 × 6, шаг 32) под плёнку/эмаль — кандидат (В-30).")
    return b


# =============================================================================== «Поток»
def vanity_float(o):
    W, color, metal = int(o["width"]), o["color"], o["metal"]
    D, ZT, WT = 460, 850, 22
    b = Build("ARV-BTH-001", REV, STATUS, {"width": W, "color": color, "metal": metal})
    top = b.part("WORKTOP", "Столешница", 0, 0, ZT - WT, W, D, ZT, "LDSP22", color, "top",
                 edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    prof = "TUBE30x20x2"
    frames = []
    for i, x in enumerate((0, W - 30), 1):
        fp = b.tube(f"FR{i}-POST-F", "Стойка передняя", x, 0, 250, x + 30, 20, ZT - WT, prof, metal, "z")
        fw = b.tube(f"FR{i}-POST-B", "Стойка задняя (к стене)", x, D - 20, 250, x + 30, D, ZT - WT, prof, metal, "z")
        rt = b.tube(f"FR{i}-RAIL-T", "Ригель верхний", x, 20, ZT - WT - 20, x + 30, D - 20, ZT - WT, prof, metal, "y")
        rbt = b.tube(f"FR{i}-RAIL-B", "Ригель нижний", x, 20, 250, x + 30, D - 20, 270, prof, metal, "y")
        for r in (rt, rbt):
            b.weld(r, fp); b.weld(r, fw)
        sgn = 1 if i == 1 else -1
        xi = x + 30 if i == 1 else x
        pls = []
        for k, y in enumerate((100, D - 140), 1):
            pl = b.plate(f"FR{i}-PL{k}", "Опорная пластина полки", min(xi, xi + sgn * 30), y, 266, max(xi, xi + sgn * 30), y + 40,
                         270, metal)
            b.weld(pl, rbt)
            pls.append(pl)
        frames.append((fp, fw, rt, rbt, pls))
        b.derived["frames"].append({"name": f"Рама {'левая' if i == 1 else 'правая'}",
                                    "tubes": [fp.id, fw.id, rt.id, rbt.id]})
        for z in (300, ZT - WT - 60):
            b.hole(fw.id, f"J-WALL{i}", "wall_bolt", x + 15, D - 20, z, "+y", 9, 20, "ANCHOR-M8", through=True,
                   note="сквозь обе стенки; в лицевой — Ø13 доступ")
            b.hole(fw.id, f"J-WALL{i}", "tube_access", x + 15, D - 20, z, "+y", 13, 2, through=True)
    b.top_fix(top, [f[2] for f in frames], [120, D - 120], "y", "J-TOP", insert=False)
    # полка
    shelf = b.part("SHELF", "Полка нижняя", 30, 20, 270, W - 30, D - 20, 292, "LDSP22", "O", "shelves",
                   edges={"-y": "ABS2", "+y": "ABS2"})
    for (fp, fw, rt, rbt, pls) in frames:
        for pl in pls:
            xc, yc = (pl.x0 + pl.x1) / 2, (pl.y0 + pl.y1) / 2
            b.hole(pl.id, "J-SHELF", "plate_hole", xc, yc, pl.z0, "+z", 4.5, 4, "SCREW-4x16C", through=True)
            b.hole(shelf.id, "J-SHELF", "pilot", xc, yc, shelf.z0, "+z", 3, 12)
    # корпус с ящиком
    yc0 = TF + TIPON_GAP
    cz1 = ZT - WT
    c = b.carcass("", 30, W - 30, cz1 - 300, cz1, yc0, D - TB, color, vis_bottom=True, label="корпус")
    for (fp, fw, rt, rbt, pls), S, n in zip(frames, (c["L"], c["R"]), ("+x", "-x")):
        for y in (150, D - 130):
            xo = rt.x0 if n == "+x" else rt.x1
            xi = rt.x1 if n == "+x" else rt.x0
            zc = (rt.z0 + rt.z1) / 2
            b.hole(rt.id, "J-FRAME-CARC", "tube_side", xo, y, zc, "+x" if n == "+x" else "-x", 4.5, 30, "SCREW-4x13", through=True,
                   note="Ø4,5 во внутренней стенке, Ø8 в наружной — доступ")
            b.hole(S.id, "J-FRAME-CARC", "pilot", S.x0 if n == "+x" else S.x1, y, zc, n, 3, 10)
    # корпус к столешнице снизу
    tp = c["TOP"]
    for y in (110, D - 120):
        b.screws_into(tp, top, "+z", "x", [tp.x0 + 80, tp.x1 - 80], "SCREW-4x30", "J-CARC-TOP", pilot=(3, 12), at=y)
    fr = [(30 + GAP / 2, W - 30 - GAP / 2, cz1 - 300 + GAP / 2, cz1 - GAP / 2)]
    b.drawers("", c, c["L"], c["R"], c["BOT"].z1, tp.z0, fr, color, _inner(color), handle=None, tipon=True,
              notch=(W / 2, 220, yc0 + 150))
    # раковина и слив
    b.hole(top.id, "J-SINK", "cutout_round", W / 2, 240, ZT, "-z", 45, WT, through=True,
           note="кандидат: под донный клапан раковины (В-28)")
    b.hole(tp.id, "J-SINK", "cutout_round", W / 2, 240, tp.z1, "-z", 60, T, through=True, note="проход сифона")
    b.part("SINK", "Раковина накладная", W / 2 - 250, 60, ZT, W / 2 + 250, 420, ZT + 130, "SINK", "white", "appliances",
           kind="context")
    b.buy("SINK-DRAIN", "Донный клапан click-clack + сифон компактный", "под раковину заказчика (В-28)", 1, "кандидат", "", "компл")
    b.derived.update(width=W, depth=D, height=ZT, plinth=0, z_bottom=250)
    _check(b, "Корпус между рамами", W - 60, c["R"].x1 - c["L"].x0)
    _check(b, "Верх столешницы", ZT, top.z1)
    _check(b, "Глубина = фасад + зазор TIP-ON + корпус + ХДФ", D, TF + TIPON_GAP + (c["L"].y1 - c["L"].y0) + TB)
    b.warnings += ["Ящик U-образный: канал 220 вокруг сифона (за осью слива, от Y = {:g}).".format(yc0 + 150),
                   "Влажное помещение: ЛДСП и кромка влагостойкие, все торцы под кромку ABS (В-32)."]
    return b


# =============================================================================== «Мобиль»
def mobile_pedestal(o):
    color = o["color"]
    W, D, H, CAS = 420, 520, 600, 50
    b = Build("ARV-OFF-005", REV, STATUS, {"color": color})
    c = b.carcass("", 0, W, CAS, H, TF, D - TB, color, vis_bottom=True, label="корпус")
    pts = [(40, 50), (W - 40, 50), (40, D - 75), (W - 40, D - 75)]
    b.feet("", c, CAS, pts, "CASTER", 40, name="Колесо Ø40 на площадке", spec="2 с тормозом, 2 без; высота 50 (кандидат)")
    fr = _fronts_col(0, W, CAS, H, heights=[180, 160, 210])
    b.drawers("", c, c["L"], c["R"], c["BOT"].z1, c["TOP"].z0, fr, color, _inner(color), handle="bar128", handle_through=True,
              box_max=170)
    top_front = next(p for p in b.P if p.id == "FRONT-3")
    b.hole(top_front.id, "J-LOCK", "lock", W - 50, 0, H - 30, "+y", 19, TF, through=True, note="кандидат: под цилиндр замка (В-22)")
    b.part("LOCK", "Замок центральный (цилиндр)", W - 60, -6, H - 40, W - 40, 0, H - 20, "LOCK", "steel", "fronts", kind="buy")
    b.buy("LOCK", "Замок центральный на 3 ящика с тягой", "цилиндр Ø19, тяга по правой боковине (кандидат)", 1, "кандидат", "В-22")
    b.derived.update(width=W, depth=D, height=H, plinth=CAS)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = колесо + боковина", H, CAS + (c["L"].z1 - c["L"].z0))
    b.warnings.append("Порядок ящиков взят из 3D каталога (снизу 180, 160, сверху 210); в описании каталога «верхний неглубокий» — "
                      "уточнить (В-34).")
    return b


# =============================================================================== «Студент»
def desk_student(o):
    color, side = o["color"], o.get("side", "right")
    W, H, D, WT = 1200, 750, 600, 22
    PW = 416
    b = Build("ARV-TBL-002", REV, STATUS, {"color": color, "side": side})
    top = b.part("WORKTOP", "Столешница", 0, 0, H - WT, W, D, H, "LDSP22", color, "top",
                 edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    px0 = W - PW if side == "right" else 0
    c = b.carcass("", px0, px0 + PW, 30 - T, H - WT, TF, D - TB, color, side_drop=30 - T, label="тумба")
    fr = _fronts_col(px0, px0 + PW, 30, H - WT, n=3)
    b.drawers("", c, c["L"], c["R"], c["BOT"].z1, c["TOP"].z0, fr, color, _inner(color), handle="bar128", handle_through=True,
              box_max=180)
    lx = 0 if side == "right" else W - T
    leg = b.part("LEG", "Опора боковая", lx, 0, 0, lx + T, D, H - WT, "LDSP16", color, "carcass",
                 edges={"-y": "ABS2", "+y": "ABS2", "-z": "PVC04"})
    mx0, mx1 = (T, px0) if side == "right" else (px0 + PW, W - T)
    mod = b.part("MODESTY", "Царга задняя", mx0, D - 120, 300, mx1, D - 104, H - WT, "LDSP16", color, "carcass",
                 edges={"-z": "ABS2"})
    nl = "+x" if side == "right" else "-x"
    hd = "+" if side == "right" else "-"
    b.ecc(top, leg, "-z", "y", [60, D / 2, D - 60], hd, "J-TOP-LEG")
    b.dowel(top, leg, "-z", "y", [110, D - 110], "J-TOP-LEG")
    b.ecc(leg, mod, nl, "z", [mod.z0 + 40, mod.z1 - 60], "+", "J-LEG-MOD")
    b.dowel(leg, mod, nl, "z", [mod.z0 + 90], "J-LEG-MOD")
    ps = c["L"] if side == "right" else c["R"]
    b.ecc(ps, mod, "-x" if side == "right" else "+x", "z", [mod.z0 + 40, mod.z1 - 60], "+", "J-PED-MOD")
    b.dowel(ps, mod, "-x" if side == "right" else "+x", "z", [mod.z0 + 90], "J-PED-MOD")
    b.ecc(top, mod, "-z", "x", [mod.x0 + 120, (mod.x0 + mod.x1) / 2, mod.x1 - 120], "+", "J-TOP-MOD")
    tp = c["TOP"]
    for y in (110, D - 110):
        b.screws_into(tp, top, "+z", "x", [tp.x0 + 80, tp.x1 - 80], "SCREW-4x30", "J-PED-TOP", pilot=(3, 12), at=y)
    b.buy("GLIDE-PAD", "Подпятник забивной Ø20 под боковину", "пластик/войлок, 2 на опору и 2 на тумбу (кандидат)", 4, "кандидат",
          "В-26")
    b.derived.update(width=W, depth=D, height=H, plinth=0)
    _check(b, "Тумба: ширина", PW, c["R"].x1 - c["L"].x0)
    _check(b, "Высота = боковина тумбы + столешница", H, (c["L"].z1 - c["L"].z0) + WT)
    _check(b, "Царга между опорой и тумбой", W - PW - T, mod.x1 - mod.x0)
    return b


# =============================================================================== «Фокус» / «Модуль»
def desk_frame(o, sku="ARV-TBL-004", office=False):
    W, top_c, metal = int(o["size"]), o["top"], o["metal"]
    D = int(o.get("depth", 700))
    ped = (o.get("pedestal", "yes") == "yes") and not office
    H, t = 750, 25
    opts = {"size": W, "top": top_c, "metal": metal}
    if office:
        opts.update(depth=D, screen=o.get("screen", "none"))
    else:
        opts.update(pedestal="yes" if ped else "no")
    b = Build(sku, REV, STATUS, opts)
    top = b.part("TOP", "Столешница", 0, 0, H - t, W, D, H, "LDSP25", top_c, "top",
                 edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    prof = "TUBE60x30x2"
    U = H - t
    bars = []
    for i, x in enumerate((60, W - 120), 1):
        lf = b.tube(f"FR{i}-LEG-F", "Стойка", x, 40, 30, x + 60, 70, U - 30, prof, metal, "z")
        lb = b.tube(f"FR{i}-LEG-B", "Стойка", x, D - 70, 30, x + 60, D - 40, U - 30, prof, metal, "z")
        ft = b.tube(f"FR{i}-FOOT", "Опора нижняя", x, 30, 0, x + 60, D - 30, 30, prof, metal, "y")
        br = b.tube(f"FR{i}-BAR", "Перекладина верхняя", x, 40, U - 30, x + 60, D - 40, U, prof, metal, "y")
        for lg in (lf, lb):
            b.weld(lg, ft); b.weld(lg, br)
        b.glide(ft, [(x + 30, 60), (x + 30, D - 60)], f"J-FR{i}-GLIDE")
        bars.append(br)
        b.derived["frames"].append({"name": f"Рама {'левая' if i == 1 else 'правая'}", "tubes": [lf.id, lb.id, ft.id, br.id]})
    # балка с торцевыми пластинами на болтах M6 к перекладинам
    bm = b.tube("BEAM", "Балка задняя", 124, D - 120, U - 30, W - 124, D - 90, U, "TUBE30x30x2", metal, "x")
    for k, (x0, x1, br, dr) in enumerate(((120, 124, bars[0], "-x"), (W - 124, W - 120, bars[1], "+x")), 1):
        pl = b.plate(f"BEAM-PL{k}", "Пластина торцевая балки", x0, D - 125, U - 30, x1, D - 85, U, metal)
        b.weld(pl, bm)
        for y in (D - 115, D - 95):
            b.hole(pl.id, f"J-BEAM{k}", "plate_hole", x1 if dr == "-x" else x0, y, U - 15, dr, 7, 4, "BOLT-M6x16", through=True)
            b.hole(br.id, f"J-BEAM{k}", "rivnut6", br.x1 if dr == "-x" else br.x0, y, U - 15, dr, 9, 2, through=True,
                   note="заклёпочная гайка M6 в боковую стенку")
    b.derived["frames"].append({"name": "Балка", "tubes": [bm.id]})
    b.top_fix(top, bars, [100, D / 2, D - 100], "y", "J-TOP-FR")
    b.top_fix(top, [bm], [W / 3, 2 * W / 3], "x", "J-TOP-BEAM")
    # лоток кабель-канала (гнутый лист 2 мм)
    xe = W - 610 if ped else W - 200
    tb = b.plate("TRAY-B", "Лоток: дно", 200, D - 262, U - 122, xe, D - 120, U - 120, metal, mat="S235-2")
    tf = b.plate("TRAY-F", "Лоток: передний борт", 200, D - 262, U - 120, xe, D - 260, U - 50, metal, mat="S235-2")
    tr = b.plate("TRAY-R", "Лоток: задний борт", 200, D - 122, U - 120, xe, D - 120, U - 30, metal, mat="S235-2")
    for x in [200 + 60 + (xe - 320) * i / 2 for i in range(3)]:
        b.hole(tr.id, "J-TRAY", "tray_hole", x, D - 120, U - 45, "-y", 4.5, 2, "SCREW-ST4.2x13", through=True,
               note="в балку — засверловка Ø3,5 по месту")
    b.derived["notes_tray"] = "лоток — один лист 2 мм, гибка 2 × 90°"
    if ped:
        yc0 = 12 + TF + TIPON_GAP
        c = b.carcass("PED-", W - 600, W - 180, U - 330, U, yc0, 520 - TB, top_c, vis_bottom=True, label="тумба подвесная")
        fr = _fronts_col(W - 600, W - 180, U - 330, U, n=2)
        for p in fr:
            pass
        recs = b.drawers("PED-", c, c["L"], c["R"], c["BOT"].z1, c["TOP"].z0, fr, top_c, _inner(top_c), handle=None, tipon=True)
        for p in b.P:
            if p.id.startswith("PED-FRONT"):
                p.y0, p.y1 = 12, 12 + TF
        tp = c["TOP"]
        for y in (yc0 + 80, 520 - TB - 80):
            b.screws_into(tp, top, "+z", "x", [tp.x0 + 80, tp.x1 - 80], "SCREW-4x30", "J-PED-TOP", pilot=(3, 12), at=y)
    if office and o.get("screen") == "front":
        sc = b.part("SCREEN", "Экран-перегородка", 100, D - 18, H, W - 100, D - 2, H + 400, "LDSP16", "G", "screen",
                    edges={"-x": "ABS2", "+x": "ABS2", "+z": "ABS2"})
        b.buy("SCREEN-CLAMP", "Кронштейн-струбцина экрана", "на кромку столешницы 25, 2 шт. (кандидат)", 2, "кандидат", "В-29")
    b.derived.update(width=W, depth=D, height=H, plinth=0)
    _check(b, "Высота = рама + столешница", H, U + t)
    _check(b, "Стойка = рама − 60", U - 60, bars[0].z0 - 30)
    _check(b, "Балка между перекладинами (с пластинами)", W - 240, bm.x1 - bm.x0 + 8)
    b.blockers += ["FRAME_AND_WELD_VERIFICATION", "INSERT_PULL_OUT_AND_TORQUE", "COATING"]
    return b


def office_desk(o):
    return desk_frame({**o, "pedestal": "no"}, sku="ARV-OFF-001", office=True)


# =============================================================================== «Совет»
def meeting_table(o):
    L, top_c, metal = int(o["length"]), o["top"], o["metal"]
    D, H, t = 1200, 750, 25
    U = H - t
    b = Build("ARV-OFF-003", REV, STATUS, {"length": L, "top": top_c, "metal": metal})
    top = b.part("TOP", "Столешница", 0, 0, U, L, D, H, "LDSP25", top_c, "top",
                 edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    prof = "TUBE40x40x2"
    nb = 2 if L <= 3000 else 3
    xs = [300, L - 340] if nb == 2 else [300, L / 2 - 20, L - 340]
    bars = []
    for i, x in enumerate(xs, 1):
        a = b.tube(f"FR{i}-LEG-F", "Стойка", x, 250, 40, x + 40, 290, U - 40, prof, metal, "z")
        c_ = b.tube(f"FR{i}-LEG-B", "Стойка", x, D - 290, 40, x + 40, D - 250, U - 40, prof, metal, "z")
        f = b.tube(f"FR{i}-FOOT", "Опора нижняя", x, 150, 0, x + 40, D - 150, 40, prof, metal, "y")
        tb = b.tube(f"FR{i}-BAR", "Перекладина верхняя", x, 150, U - 40, x + 40, D - 150, U, prof, metal, "y")
        for lg in (a, c_):
            b.weld(lg, f); b.weld(lg, tb)
        b.glide(f, [(x + 20, 200), (x + 20, D - 200)], f"J-FR{i}-GLIDE")
        bars.append(tb)
        b.derived["frames"].append({"name": f"Рама {i}", "tubes": [a.id, c_.id, f.id, tb.id]})
    beams = []
    for k in range(nb - 1):
        xa, xb = xs[k] + 40, xs[k + 1]
        bm = b.tube(f"BEAM{k + 1}", "Балка продольная", xa + 4, D / 2 - 20, U - 40, xb - 4, D / 2 + 20, U, prof, metal, "x")
        for s, (x0, x1, br, dr) in enumerate(((xa, xa + 4, bars[k], "-x"), (xb - 4, xb, bars[k + 1], "+x")), 1):
            pl = b.plate(f"BEAM{k + 1}-PL{s}", "Пластина торцевая балки", x0, D / 2 - 25, U - 40, x1, D / 2 + 25, U, metal)
            b.weld(pl, bm)
            for y in (D / 2 - 12, D / 2 + 12):
                b.hole(pl.id, f"J-BEAM{k + 1}{s}", "plate_hole", x1 if dr == "-x" else x0, y, U - 20, dr, 7, 4, "BOLT-M6x16", through=True)
                b.hole(br.id, f"J-BEAM{k + 1}{s}", "rivnut6", br.x1 if dr == "-x" else br.x0, y, U - 20, dr, 9, 2, through=True,
                       note="заклёпочная гайка M6")
        beams.append(bm)
        b.derived["frames"].append({"name": f"Балка {k + 1}", "tubes": [bm.id]})
    b.top_fix(top, bars, [220, D / 2 - 120, D / 2 + 120, D - 220], "y", "J-TOP-FR")
    for bm in beams:
        n_ = max(2, round((bm.x1 - bm.x0) / 600))
        vals = [bm.x0 + (bm.x1 - bm.x0) * (i + 0.5) / n_ for i in range(n_)]
        vals = [v for v in vals if abs(v - L / 2) > 260]
        b.top_fix(top, [bm], vals, "x", "J-TOP-BEAM")
    b.derived["cutouts"] = [{"part": "TOP", "x0": L / 2 - 200, "y0": D / 2 - 70, "x1": L / 2 + 200, "y1": D / 2 + 70,
                             "note": "кандидат: под лючок 400 × 140 (В-29)"}]
    b.part("CABLEBOX", "Лючок кабельный встраиваемый", L / 2 - 200, D / 2 - 70, H - 2, L / 2 + 200, D / 2 + 70, H, "CABLEBOX",
           "black", "top", kind="buy")
    b.buy("CABLEBOX", "Лючок кабельный встраиваемый 400 × 140", "розетки 230 В + USB/LAN по заказу (кандидат)", 1, "кандидат", "В-29")
    b.derived.update(width=L, depth=D, height=H, plinth=0)
    _check(b, "Высота = рама + столешница", H, U + t)
    if L > 2780:
        b.warnings.append(f"Столешница {L} × {D} одним куском — из плиты формата 3660 × 1830 (В-31); из 2800 × 2070 не выходит.")
    b.warnings.append("Лючок по центру над продольной балкой: глубина лючка под столешницей — не более 25 + зазор до балки (В-29).")
    b.blockers += ["FRAME_AND_WELD_VERIFICATION", "INSERT_PULL_OUT_AND_TORQUE", "COATING"]
    return b


# =============================================================================== «Дастархан»
def table_4legs(o):
    Lx, top_c, metal = int(o["size"]), o["top"], o["metal"]
    D = 800 if Lx <= 1200 else 900
    H, t, leg, ins = 750, 28, 40, 60
    U = H - t
    b = Build("ARV-TBL-001", REV, STATUS, {"size": Lx, "top": top_c, "metal": metal})
    top = b.part("TOP", "Столешница", 0, 0, U, Lx, D, H, "TOP28", top_c, "top",
                 edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    legs = []
    for i, (x, y) in enumerate([(ins, ins), (Lx - ins - leg, ins), (ins, D - ins - leg), (Lx - ins - leg, D - ins - leg)], 1):
        lg = b.tube(f"LEG{i}", "Ножка", x, y, 0, x + leg, y + leg, U, "TUBE40x40x2", metal, "z")
        legs.append(lg)
        b.glide(lg, [(x + leg / 2, y + leg / 2)], f"J-LEG{i}-GLIDE")
    ap = "TUBE60x20x2"
    af = b.tube("APR-F", "Царга продольная", ins + leg, ins, U - 60, Lx - ins - leg, ins + 20, U, ap, metal, "x")
    ab = b.tube("APR-B", "Царга продольная", ins + leg, D - ins - 20, U - 60, Lx - ins - leg, D - ins, U, ap, metal, "x")
    al = b.tube("APR-L", "Царга поперечная", ins, ins + leg, U - 60, ins + 20, D - ins - leg, U, ap, metal, "y")
    ar = b.tube("APR-R", "Царга поперечная", Lx - ins - 20, ins + leg, U - 60, Lx - ins, D - ins - leg, U, ap, metal, "y")
    for a_ in (af, ab, al, ar):
        for lg in legs:
            if (a_.axis == "x" and abs(lg.y0 - a_.y0) < 0.1 or abs(lg.y1 - a_.y1) < 0.1 and a_.axis == "x") or \
               (a_.axis == "y" and (abs(lg.x0 - a_.x0) < 0.1 or abs(lg.x1 - a_.x1) < 0.1)):
                if a_.axis == "x" and (abs(lg.x1 - a_.x0) < 0.1 or abs(lg.x0 - a_.x1) < 0.1):
                    b.weld(a_, lg)
                if a_.axis == "y" and (abs(lg.y1 - a_.y0) < 0.1 or abs(lg.y0 - a_.y1) < 0.1):
                    b.weld(a_, lg)
    b.derived["frames"].append({"name": "Подстолье", "tubes": [p.id for p in legs + [af, ab, al, ar]]})
    b.top_fix(top, [af, ab], [Lx / 4, Lx / 2, 3 * Lx / 4], "x", "J-TOP-APR")
    b.top_fix(top, [al, ar], [D / 2], "y", "J-TOP-APR")
    b.derived.update(width=Lx, depth=D, height=H, plinth=0)
    _check(b, "Высота = ножка + столешница", H, U + t)
    _check(b, "Ножки от краёв", ins, legs[0].x0)
    b.blockers += ["FRAME_AND_WELD_VERIFICATION", "INSERT_PULL_OUT_AND_TORQUE", "COATING"]
    b.notes.append("Столешница 28 — плита-столешница ЛДСП 28 с кромкой ABS 2 (как в каталоге), втулки M6 гл. 17, остаток 11.")
    return b


# =============================================================================== «Руководитель»
def exec_desk(o):
    W, color, acc, side = int(o["size"]), o["color"], o["accent"], o.get("return", "right")
    D, H, t = 900, 750, 38
    U = H - t
    b = Build("ARV-OFF-007", REV, STATUS, {"size": W, "color": color, "accent": acc, "return": side})
    E4 = {"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"}
    top = b.part("TOP", "Столешница", 0, 0, U, W, D, H, "TOP38", color, "top", edges=E4)
    legs = {}
    for k, (xo, xi) in (("L", (0, 25)), ("R", (W - 25, W - 50))):
        a = b.part(f"LEG{k}-O", "Опора панельная, наружный слой", min(xo, xo + 25), 0, 0, max(xo, xo + 25), D, U, "LDSP25", color,
                   "carcass", edges={"-y": "ABS2", "+y": "ABS2", "-z": "PVC04"})
        i_ = b.part(f"LEG{k}-I", "Опора панельная, внутренний слой", min(xi, xi + 25), 0, 0, max(xi, xi + 25), D, U, "LDSP25", color,
                    "carcass", edges={"-y": "ABS2", "+y": "ABS2", "-z": "PVC04"})
        legs[k] = (a, i_)
    mod = b.part("MODESTY", "Царга передняя", 50, 80, 250, W - 50, 98, U, "LDSP18", acc, "carcass", edges={"-z": "ABS2"})
    b.ecc(top, legs["L"][1], "-z", "y", [80, D / 2, D - 80], "-", "J-TOP-LEGL")
    b.dowel(top, legs["L"][1], "-z", "y", [140, D - 140], "J-TOP-LEGL")
    b.ecc(top, legs["R"][1], "-z", "y", [80, D / 2, D - 80], "+", "J-TOP-LEGR")
    b.dowel(top, legs["R"][1], "-z", "y", [140, D - 140], "J-TOP-LEGR")
    b.ecc(legs["L"][1], mod, "+x", "z", [mod.z0 + 50, mod.z1 - 60], "-", "J-LEGL-MOD")
    b.ecc(legs["R"][1], mod, "-x", "z", [mod.z0 + 50, mod.z1 - 60], "-", "J-LEGR-MOD")
    b.ecc(top, mod, "-z", "x", [mod.x0 + 200, W / 2, mod.x1 - 200], "-", "J-TOP-MOD")
    b.notes.append("Опоры 50 = 2 × ЛДСП 25 на клею ПВА D3 под прессом + 6 шкантов 8 × 30 (В-33); Minifix — во внутреннем слое.")
    b.buy("GLUE-PANEL", "Клей ПВА D3 для склейки опор", "≈ 150 г/м²", 0.3, "типовой", "", "кг")
    # приставка: тумба в своих координатах (фронт к креслу), затем поворот
    rx0 = W - 600 if side == "right" else 0
    rtop = b.part("RTOP", "Столешница приставки", rx0, D, U, rx0 + 600, D + 1100, H, "TOP38", color, "top",
                  edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    sub = Build(b.sku, REV, STATUS, {})
    yc0 = TF + TIPON_GAP
    c = sub.carcass("RET-", 0, 1100, 30 - T, U, yc0, 600 - TB, acc, partitions=[(542, T, "Стойка")], side_drop=30 - T,
                    label="тумба приставки")
    P1 = c["parts"][0]
    fr = _fronts_col(550, 1100, 30, U, n=3)
    sub.drawers("RET-", c, P1, c["R"], c["BOT"].z1, c["TOP"].z0, fr, acc, _inner(acc), handle=None, tipon=True)
    dr = [(GAP / 2, 550 - GAP / 2, 30 + GAP / 2, U - GAP / 2)]
    sub.doors("RET-", c, [c["L"]], dr, acc, handle=None)
    sub.buy("PUSH-LATCH", "Толкатель двери TIP-ON", "кандидат Blum TIP-ON 956.1004 + планка (петли без пружины) — В-20", 1,
            "кандидат", "", "шт")
    tp = c["TOP"]
    if side == "right":
        fmap = lambda x, y, z: (rx0 + y, D + 1100 - x, z)
        dm = {"+x": "-y", "-x": "+y", "+y": "+x", "-y": "-x", "+z": "+z", "-z": "-z"}
    else:
        fmap = lambda x, y, z: (rx0 + 600 - y, D + x, z)
        dm = {"+x": "+y", "-x": "-y", "+y": "-x", "-y": "+x", "+z": "+z", "-z": "-z"}
    b.merge(sub, fmap, lambda d: dm[d])
    tpm = b.get("RET-TOP")
    for k_ in ("y",):
        pass
    # крышка тумбы -> столешница приставки
    for vx in (tpm.x0 + 120, tpm.x1 - 120):
        b.screws_into(tpm, rtop, "+z", "y", [tpm.y0 + 120, (tpm.y0 + tpm.y1) / 2, tpm.y1 - 120], "SCREW-4x30", "J-RET-TOP",
                      pilot=(3, 12), at=vx)
    # столешницы стола и приставки — стяжки по шву Y = D
    for x in (rx0 + 150, rx0 + 450):
        b.hole(top.id, "J-TOP-SEAM", "top_conn", x, D - 75, U, "+z", 35, 20, "TOP-CONN", note="кандидат: Ø35 гл. 20 + паз 10 до шва")
        b.hole(rtop.id, "J-TOP-SEAM", "top_conn", x, D + 75, U, "+z", 35, 20, note="ответная часть")
    b.derived.update(width=W, depth=D + 1100, height=H, plinth=0, desk_depth=D)
    _check(b, "Высота = опора + столешница", H, U + t)
    _check(b, "Царга между опорами", W - 100, mod.x1 - mod.x0)
    b.warnings.append("Тумба приставки: 3 ящика TIP-ON и дверь на толкателе смотрят к креслу; низ корпуса на 30 от пола.")
    return b


# =============================================================================== «Приём»
def reception(o):
    W, color, acc = int(o["width"]), o["color"], o["accent"]
    D = 800
    b = Build("ARV-OFF-004", REV, STATUS, {"width": W, "color": color, "accent": acc})
    E2 = {"-y": "ABS2", "+y": "ABS2", "+z": "ABS2"}
    ZL = 1064
    sides = {}
    for k, (xo, xi) in (("L", (0, 18)), ("R", (W - 18, W - 36))):
        a = b.part(f"SIDE{k}-O", "Боковина, наружный слой", min(xo, xo + 18), 24, 0, max(xo, xo + 18), D, ZL, "LDSP18", color,
                   "carcass", edges=E2)
        i_ = b.part(f"SIDE{k}-I", "Боковина, внутренний слой", min(xi, xi + 18), 24, 0, max(xi, xi + 18), D, ZL, "LDSP18", color,
                    "carcass", edges=E2)
        sides[k] = (a, i_)
    flute = b.part("FLUTE", "Панель лицевая рифлёная", 0, 2, 60, W, 24, ZL - 4, "MDF22", acc, "carcass",
                   edges={"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
    n_ = int((W - 40) // 40)
    off = (W - n_ * 40) / 2
    for i in range(n_):
        a = off + i * 40 + 12
        b.part(f"FLUTE-G{i + 1}", "Канавка рифления (фрезеровка)", a, 2, 80, a + 16, 10, ZL - 24, "MILL", "groove", "carcass",
               kind="buy_part")
    fs = b.part("FRONT-S", "Панель лицевая несущая", 36, 24, 60, W - 36, 40, ZL, "LDSP16", color, "carcass")
    ledge_lo = b.part("LEDGE-L", "Полка посетителя, нижний слой", -20, -40, ZL, W + 20, 320, ZL + 18, "LDSP18", color, "top",
                      edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    ledge_up = b.part("LEDGE-U", "Полка посетителя, верхний слой", -20, -40, ZL + 18, W + 20, 320, ZL + 36, "LDSP18", color, "top",
                      edges={"-y": "ABS2", "+y": "ABS2", "-x": "ABS2", "+x": "ABS2"})
    work = b.part("WORK", "Столешница рабочая", 36, 40, 725, W - 36, D, 750, "LDSP25", color, "top", edges={"+y": "ABS2"})
    pl = b.part("PLINTH", "Цоколь", 36, 44, 0, W - 36, 60, 60, "LDSP16", "black", "carcass")   # 14.11: кромка «-y» была на пласти — убрана
    # соединения
    b.ecc(sides["L"][1], fs, "+x", "z", [120, ZL / 2, ZL - 80], "+", "J-SIDEL-FS")
    b.ecc(sides["R"][1], fs, "-x", "z", [120, ZL / 2, ZL - 80], "+", "J-SIDER-FS")
    b.ecc(sides["L"][1], work, "+x", "y", [90, D - 60], "+", "J-SIDEL-WORK")
    b.ecc(sides["R"][1], work, "-x", "y", [90, D - 60], "+", "J-SIDER-WORK")
    b.dowel(sides["L"][1], work, "+x", "y", [(90 + D - 60) / 2], "J-SIDEL-WORK")
    b.dowel(sides["R"][1], work, "-x", "y", [(90 + D - 60) / 2], "J-SIDER-WORK")
    b.ecc(ledge_lo, sides["L"][1], "-z", "y", [80, 260], "-", "J-LEDGE-SL")
    b.ecc(ledge_lo, sides["R"][1], "-z", "y", [80, 260], "+", "J-LEDGE-SR")
    b.ecc(ledge_lo, fs, "-z", "x", [W / 4, W / 2, 3 * W / 4], "+", "J-LEDGE-FS")
    b.conf(fs, work, "+y", "x", [W / 4, W / 2, 3 * W / 4], "J-FS-WORK")
    for z in (140, ZL / 2, ZL - 140):
        b.screws_into(fs, flute, "-y", "x", [W / 6, W / 2, 5 * W / 6], "SCREW-4x30", "J-FS-FLUTE", pilot=(3, 12), at=z)
    b.ecc(sides["L"][1], pl, "+x", "z", [30], "-", "J-SIDEL-PL")
    b.ecc(sides["R"][1], pl, "-x", "z", [30], "-", "J-SIDER-PL")
    b.notes.append("Боковины и полка посетителя — 2 × ЛДСП 18 на клею (В-33); Minifix — во внутреннем / нижнем слое.")
    b.buy("GLUE-PANEL", "Клей ПВА D3 для склейки слоёв", "≈ 150 г/м²", 0.6, "типовой", "", "кг")
    # тумба: фронт к сотруднику (+Y), собирается в своих координатах
    sub = Build(b.sku, REV, STATUS, {})
    yc0 = TF + TIPON_GAP
    PWd = (W - 36) - (W - 470)
    c = sub.carcass("PED-", 0, PWd, 30 - T, 725, yc0, 460 - TB, color, side_drop=30 - T, label="тумба")
    fr = _fronts_col(0, PWd, 30, 725, n=3)
    sub.drawers("PED-", c, c["L"], c["R"], c["BOT"].z1, c["TOP"].z0, fr, color, _inner(color), handle=None, tipon=True)
    fmap = lambda x, y, z: ((W - 36) - x, D - y, z)
    dm = {"+x": "-x", "-x": "+x", "+y": "-y", "-y": "+y", "+z": "+z", "-z": "-z"}
    b.merge(sub, fmap, lambda d: dm[d])
    ptop = b.get("PED-TOP")
    for vx in (ptop.x0 + 80, ptop.x1 - 80):
        b.screws_into(ptop, work, "+z", "y", [ptop.y0 + 80, ptop.y1 - 80], "SCREW-4x30", "J-PED-WORK", pilot=(3, 12), at=vx)
    ps = b.get("PED-SIDE-L")          # после поворота — у правой боковины стойки
    b.screws_into(ps, sides["R"][1], "+x", "y", [ps.y0 + 80, ps.y1 - 80], "SCREW-4x30", "J-PED-SIDE", pilot=(3, 12), at=350)
    b.part("LED", "Профиль светодиодный с лентой 2700 K", 20, 10, 52, W - 20, 22, 60, "LED", "black", "decor", kind="buy")
    b.buy("LED", "Профиль LED + лента 2700 K + блок 12 В", f"длина {W - 40}, под рифлёной панелью", 1, "кандидат", "В-27")
    b.glows.append([0, -60, W, 120, (255, 196, 120), 160])
    b.buy("GLIDE-PAD", "Подпятник забивной Ø20", "под боковины и тумбу (кандидат)", 6, "кандидат", "В-26")
    b.derived.update(width=W, depth=D, height=ZL + 36, plinth=60)
    _check(b, "Высота стойки = боковина + 2 × 18", 1100, ZL + 36)
    _check(b, "Рабочая столешница между боковинами", W - 72, work.x1 - work.x0)
    b.warnings.append("Рифление: МДФ 22, канавки 16 × 8 с шагом 40 (в каталоге выступ 12 — уточнить, В-30).")
    return b


MODELS = {
    "ARV-NST-002": ("Комод «Самал»", chest), "ARV-NST-003": ("ТВ-тумба «Кок-Тобе»", tv_floor),
    "ARV-NST-004": ("Тумба «Луна»", nightstand_float), "ARV-NST-005": ("Комод «Волна»", chest_fluted),
    "ARV-BTH-001": ("Тумба «Поток»", vanity_float), "ARV-OFF-005": ("Тумба «Мобиль»", mobile_pedestal),
    "ARV-TBL-002": ("Стол «Студент»", desk_student), "ARV-TBL-004": ("Стол «Фокус»", desk_frame),
    "ARV-OFF-001": ("Стол «Модуль»", office_desk), "ARV-OFF-003": ("Стол «Совет»", meeting_table),
    "ARV-TBL-001": ("Стол «Дастархан»", table_4legs), "ARV-OFF-007": ("Стол «Руководитель»", exec_desk),
    "ARV-OFF-004": ("Ресепшн «Приём»", reception),
}


def build(sku, options):
    b = MODELS[sku][1](options)
    return b.design()
