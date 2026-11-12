"""Остальные модели каталога Arvello: стандартные (STD), трендовые и офисные.

Все размеры в мм. Оси: x — ширина (слева направо), y — глубина (y=0 — лицевая плоскость, к стене растёт),
z — высота. Корпус ЛДСП 16, фасад 18, зазор 3, столешница 28/38 — стандарты Blum / Ana White.
Каждый builder возвращает (model, facts); model.checks — что проверить на фото, model.wall_y — где стена.
"""
from __future__ import annotations

from builders import (BLACK, GLASS_DARK, INNER, MIRROR, STEEL, STONE, BUILDERS, _carcass, _fronts, _rgb,
                      kitchen_gola)
from render import Glow, Model, Part

LED = (255, 210, 150)        # светящаяся лента / бра
TINT = (70, 74, 80)          # тонированное стекло
CERAMIC = (246, 246, 244)    # раковина


def C(mats, k):
    return _rgb(mats, "colors", k)


def M(mats, k):
    return _rgb(mats, "metal", k)


def _xform(parts, f, tag=""):
    """Переносит детали функцией f(x0,y0,x1,y1) -> (X0,Y0,X1,Y1)."""
    out = []
    for p in parts:
        X0, Y0, X1, Y1 = f(p.x0, p.y0, p.x1, p.y1)
        out.append(Part(p.name + tag, min(X0, X1), min(Y0, Y1), p.z0, max(X0, X1), max(Y0, Y1), p.z1, p.color, p.group))
    return out


def _hh(name, xc, z, L=160, y=0):
    """Горизонтальная ручка-скоба на фасаде с лицевой плоскостью y."""
    return [Part(name, xc - L / 2, y - 26, z - 6, xc + L / 2, y - 14, z + 6, BLACK, "fronts"),
            Part(name + "a", xc - L / 2 + 6, y - 14, z - 5, xc - L / 2 + 16, y, z + 5, BLACK, "fronts"),
            Part(name + "b", xc + L / 2 - 16, y - 14, z - 5, xc + L / 2 - 6, y, z + 5, BLACK, "fronts")]


def _hv(name, x, zc, L=320, y=0):
    """Вертикальная ручка-скоба."""
    return [Part(name, x - 6, y - 26, zc - L / 2, x + 6, y - 14, zc + L / 2, BLACK, "fronts"),
            Part(name + "a", x - 5, y - 14, zc - L / 2 + 6, x + 5, y, zc - L / 2 + 16, BLACK, "fronts"),
            Part(name + "b", x - 5, y - 14, zc + L / 2 - 16, x + 5, y, zc + L / 2 - 6, BLACK, "fronts")]


def _drawers(name, x0, x1, z0, z1, color, n, handles=True, y0=0, heights=None):
    """n ящиков друг над другом с ручками по центру."""
    P = []
    hs = heights or [(z1 - z0) / n] * n
    z = z0
    for i, h in enumerate(hs):
        P += _fronts(f"{name}{i}_", x0, x1, z, z + h, color, y0=y0)
        if handles:
            P += _hh(f"{name}{i}_h", (x0 + x1) / 2, z + h - 45 if h > 160 else z + h / 2, y=y0)
        z += h
    return P


def _tube(name, x0, y0, z0, x1, y1, z1, color, group="frame"):
    return Part(name, x0, y0, z0, x1, y1, z1, color, group)


def _ribs(name, x0, x1, z0, z1, y_face, color, step=30, rib=18, depth=10, axis="x", group="fronts"):
    """Рифление: вертикальные рейки на плоскости y_face (выступают к y меньше)."""
    P = []
    n = int((x1 - x0) // step)
    off = (x1 - x0 - n * step) / 2 + (step - rib) / 2
    for i in range(n):
        a = x0 + off + i * step
        P.append(Part(f"{name}{i}", a, y_face - depth, z0, a + rib, y_face, z1, color, group))
    return P


# ---------------------------------------------------------------- кухни STD
def _kitchen_run(pfx, mods, base_c, top_c, handles=True, uppers=True, plinth=100, ctop=820, wt=28, up0=1450, up1=2170,
                 hob=True, sink=True):
    """Прямой ряд кухни по модулям [(вид, ширина)]: corner/drawers/doors/sink."""
    P = []
    x = 0
    wt_top = ctop + wt
    hob_done = False
    for k, (kind, w) in enumerate(mods):
        P += _carcass(f"{pfx}b{k}", x, x + w, 18, 578, plinth, ctop, base_c, shelves=() if kind == "drawers" else (460,))
        if kind == "drawers":
            P += _drawers(f"{pfx}d{k}", x, x + w, plinth, ctop, base_c, 3, handles, heights=[300, 260, ctop - plinth - 560])
            if hob and not hob_done:
                P.append(Part(f"{pfx}hob", x + 5, 40, wt_top, x + w - 5, 560, wt_top + 6, GLASS_DARK, "appliances"))
                hob_done = True
        elif kind == "corner":
            P.append(Part(f"{pfx}filler{k}", x, 0, plinth, x + 600, 18, ctop, base_c, "carcass"))
            P += _fronts(f"{pfx}cd{k}", x + 600, x + w, plinth, ctop, base_c)
            if handles:
                P += _hh(f"{pfx}cdh{k}", x + 600 + (w - 600) / 2, ctop - 50)
        else:
            n = 1 if w <= 600 else 2
            P += _fronts(f"{pfx}door{k}_", x, x + w, plinth, ctop, base_c, n=n)
            if handles:
                for i in range(n):
                    P += _hh(f"{pfx}dh{k}_{i}", x + (i + .5) * w / n, ctop - 50)
        if kind == "sink" and sink:
            xc = x + w / 2
            P += [Part(f"{pfx}sink", xc - 250, 70, wt_top, xc + 250, 500, wt_top + 3, STEEL, "appliances"),
                  Part(f"{pfx}faucet", xc - 15, 520, wt_top, xc + 15, 550, wt_top + 300, STEEL, "appliances"),
                  Part(f"{pfx}spout", xc - 12, 390, wt_top + 270, xc + 12, 550, wt_top + 300, STEEL, "appliances")]
        if uppers:
            P += _carcass(f"{pfx}u{k}", x, x + w, 278, 578, up0, up1, top_c, shelves=(up0 + 360,))
            n = 1 if w <= 600 else 2
            P += _fronts(f"{pfx}ud{k}_", x, x + w, up0, up1, top_c, n=n, y0=260)
            if handles:
                for i in range(n):
                    P += _hh(f"{pfx}udh{k}_{i}", x + (i + .5) * w / n, up0 + 50, y=260)
        x += w
    P.append(Part(f"{pfx}plinth", 0, 50, 0, x, 578, plinth, base_c, "carcass"))
    P.append(Part(f"{pfx}worktop", 0, -22, ctop, x, 578, wt_top, v_worktop_color, "carcass"))
    return P, x


v_worktop_color = (205, 190, 168)   # ЛДСП-столешница под дерево/камень (стандарт)


def _std_mods(L):
    rem = L - 1400
    mods = [("drawers", 600)]
    sink = 800
    while rem >= 600:
        mods.append(("doors", 600)); rem -= 600
    if rem >= 300:
        mods.append(("doors", rem))
    else:
        sink += rem
    return mods + [("sink", sink)]


def kitchen_std(v, mats):
    """ARV-KIT-001 «Алатау» / 002 «Медеу» / 003 «Тарлан» — стандартные кухни с ручками."""
    base_c, top_c = C(mats, v["base"]), C(mats, v["top"])
    layout = v.get("layout", "straight")
    if layout == "corner":
        P, L = _kitchen_run("m", [("corner", 1000), ("drawers", 600), ("sink", 800)], base_c, top_c)
        P2, L2 = _kitchen_run("s", [("doors", 400), ("drawers", 600)], base_c, top_c, hob=False, sink=False)
        P += _xform(P2, lambda x0, y0, x1, y1: (600 - y1, -x1, 600 - y0, -x0), "_2")
        size = f"{L} + {L2 + 600}"
    else:
        L = int(v["length"])
        P, L = _kitchen_run("m", _std_mods(L), base_c, top_c)
        size = f"{L}"
    m = Model(P, [], [])
    m.wall_y = 578
    n_low = sum(1 for p in P if p.group == "fronts" and p.z1 <= 830 and p.name.count("h") == 0 and "_h" not in p.name)
    m.checks = [("Угловая кухня: " if layout == "corner" else "Прямая кухня ") + f"{size} мм, высота до верха шкафов 2170",
                "Нижние шкафы 850 мм со столешницей, верхние 720 мм, между ними 600 мм",
                "На каждом фасаде чёрная ручка-скоба: низ — у верхнего края, верх — у нижнего",
                "Модуль с 3 ящиками под варочной панелью, мойка над двухдверным модулем"]
    facts = [
        (f"L-shaped kitchen, {size.replace(' + ', ' cm and ')} mm runs" if layout == "corner"
         else f"Straight one-wall kitchen {L / 10:.0f} cm long") +
        ", lower cabinets 85 cm high with a 28 mm worktop, wall cabinets 72 cm high, top of wall cabinets at 217 cm.",
        f"Lower fronts in {mats['colors'][v['base']]['prompt']}; wall cabinets in {mats['colors'][v['top']]['prompt']}; "
        "every front has a slim black bar handle (lower ones near the top edge, upper ones near the bottom edge).",
        "A three-drawer unit under a black glass hob; a stainless steel sink with faucet above a two-door unit; "
        "laminate worktop in warm beige stone look; recessed plinth.",
    ]
    return m, facts


# ---------------------------------------------------------------- шкафы STD
def wardrobe_hinged(v, mats):
    """ARV-WRD-001 «Арна» — распашной шкаф с ручками, 1200/1800 × 2400 × 580."""
    W = int(v["width"]); c = C(mats, v["color"])
    H, plinth, main_top, y1 = 2400, 80, 1980, 580
    n = W // 600
    P = []
    for i in range(n):
        x0 = i * 600
        kind = "HSD"[i % 3]
        sh = [main_top - 300] if kind != "S" else [500, 850, 1200, 1550, main_top - 300]
        P += _carcass(f"sec{i}", x0, x0 + 600, 18, y1, plinth, main_top, c, shelves=sh)
        if kind in "HD":
            P.append(Part(f"rod{i}", x0 + 16, 280, main_top - 380, x0 + 584, 305, main_top - 355, STEEL, "interior"))
        if kind == "D":
            P.append(Part(f"rod{i}b", x0 + 16, 280, 1000, x0 + 584, 305, 1025, STEEL, "interior"))
        P += _carcass(f"mez{i}", x0, x0 + 600, 18, y1, main_top, H, c)
        P += _fronts(f"door{i}", x0, x0 + 600, plinth, main_top, c)
        P += _fronts(f"mez{i}d", x0, x0 + 600, main_top, H, c)
        hx = x0 + (560 if i % 2 == 0 else 40)
        P += _hv(f"h{i}", hx, 1100) + _hh(f"hm{i}", x0 + 300, main_top + 60)
    P.append(Part("plinth", 0, 50, 0, W, y1, plinth, c, "carcass"))
    m = Model(P, [], []); m.wall_y = y1
    m.checks = [f"Распашной шкаф {W} × {H} × {y1} мм: {n} высоких дверей + {n} антресольных",
                "На высоких дверях вертикальные ручки 320 мм у стыка дверей, на антресоли — горизонтальные",
                "Цоколь утоплен, корпус и фасады одного цвета"]
    facts = [f"Freestanding hinged wardrobe {W / 10:.0f} cm wide, 240 cm high, 58 cm deep, {n} tall doors and {n} small upper "
             f"doors, slim black vertical bar handles 32 cm long, small horizontal handles on upper doors.",
             f"Body and fronts in {mats['colors'][v['color']]['prompt']}; recessed plinth."]
    return m, facts


def wardrobe_sliding(v, mats):
    """ARV-WRD-002 «Каскад» — шкаф-купе 1800/2400 × 2400 × 620, двери в алюминиевом профиле."""
    W = int(v["width"]); c = C(mats, v["color"])
    H, depth = 2400, 620
    nd = 2 if W <= 1800 else 3
    n = W // 600
    P = []
    y0 = 90
    sw = (W - 36) / n                      # секции стоят между боковинами корпуса и под его крышкой
    for i in range(n):
        x0 = 18 + i * sw
        kind = "HSHD"[i % 4]
        sh = [2000] if kind != "S" else [500, 850, 1200, 1550, 2000]
        P += _carcass(f"sec{i}", x0, x0 + sw, y0, depth, 60, H - 18, INNER, shelves=sh)
        if kind in "HD":
            P.append(Part(f"rod{i}", x0 + 16, 340, 1920, x0 + sw - 16, 365, 1945, STEEL, "interior"))
    P += [Part("side_L", 0, 0, 0, 18, depth, H, c, "carcass"), Part("side_R", W - 18, 0, 0, W, depth, H, c, "carcass"),
          Part("top", 0, 0, H - 18, W, depth, H, c, "carcass"), Part("plinth", 18, 60, 0, W - 18, depth, 60, c, "carcass"),
          Part("track_top", 18, 0, H - 60, W - 18, 80, H - 18, STEEL, "fronts"),
          Part("track_bot", 18, 0, 0, W - 18, 80, 30, STEEL, "fronts")]
    dw = (W - 36 + 30 * (nd - 1)) / nd
    for i in range(nd):
        xa = 18 + i * (dw - 30)
        yp = 10 if i % 2 == 0 else 45
        mirror = v.get("doors") == "mirror" and i == nd // 2
        P.append(Part(f"door{i}", xa + 20, yp + 8, 50, xa + dw - 20, yp + 18, H - 70, MIRROR if mirror else c, "fronts"))
        P += [Part(f"prof{i}a", xa, yp, 30, xa + 20, yp + 26, H - 60, STEEL, "fronts"),
              Part(f"prof{i}b", xa + dw - 20, yp, 30, xa + dw, yp + 26, H - 60, STEEL, "fronts")]
    m = Model(P, [], []); m.wall_y = depth
    m.checks = [f"Шкаф-купе {W} × {H} × {depth} мм, {nd} раздвижные двери в алюминиевом профиле",
                "Двери в двух плоскостях, верхняя и нижняя направляющие видны",
                "Центральная дверь с зеркалом" if v.get("doors") == "mirror" else "Все двери из ЛДСП в цвет корпуса"]
    facts = [f"Sliding-door wardrobe {W / 10:.0f} cm wide, 240 cm high, 62 cm deep with {nd} sliding doors in slim "
             "silver aluminium frame profiles running in top and bottom tracks; doors overlap in two planes.",
             f"Body and door panels in {mats['colors'][v['color']]['prompt']}" +
             ("; the middle door is a full-height mirror." if v.get("doors") == "mirror" else "; no mirrors.")]
    return m, facts


def hallway_open(v, mats):
    """ARV-WRD-003 «Порог» — открытая прихожая 1200 × 2100 × 400: шкаф + вешалка + обувница."""
    c = C(mats, v["color"]); W, H, D = 1200, 2100, 400
    P = _carcass("cab", 0, 400, 18, D, 60, H, c, shelves=(500, 900, 1300, 1700))
    P += _fronts("cabd", 0, 400, 60, H, c) + _hv("cabh", 360, 1050)
    P.append(Part("cabpl", 0, 50, 0, 400, D, 60, c, "carcass"))
    P += [Part("bench_L", 400, 18, 0, 416, D, 450, c, "carcass"), Part("bench_R", W - 16, 18, 0, W, D, 450, c, "carcass"),
          Part("bench_top", 400, 0, 450, W, D, 476, c, "carcass"), Part("bench_sh", 416, 30, 220, W - 16, D, 236, c, "carcass"),
          Part("bench_bot", 416, 30, 40, W - 16, D, 56, c, "carcass"),
          Part("panel", 400, D - 18, 476, W, D, H, c, "carcass"),
          Part("hat", 400, 100, H - 26, W, D - 18, H, c, "carcass")]
    for i in range(5):
        x = 460 + i * 160
        P += [Part(f"hook{i}", x - 8, D - 90, 1680, x + 8, D - 18, 1696, BLACK, "fronts"),
              Part(f"hook{i}t", x - 8, D - 90, 1696, x + 8, D - 74, 1730, BLACK, "fronts")]
    m = Model(P, [], []); m.wall_y = D
    m.checks = ["Слева узкий шкаф 400 мм с одной дверью и вертикальной ручкой",
                "Справа открытая зона: панель с 5 чёрными крючками, полка для шапок сверху",
                "Внизу скамья-обувница 450 мм с двумя открытыми полками"]
    facts = [f"Compact open hallway unit 120 x 210 x 40 cm in {mats['colors'][v['color']]['prompt']}: on the left a narrow "
             "40 cm cabinet with one tall door and a black bar handle; on the right an open coat zone with a back panel, "
             "five black hooks and a hat shelf on top; below it a 45 cm high shoe bench with two open shelves."]
    return m, facts


# ---------------------------------------------------------------- столы, кровати, тумбы STD
def table_4legs(v, mats):
    """ARV-TBL-001 «Дастархан» — обеденный стол на четырёх металлических ножках."""
    Lx = int(v["size"]); D = 800 if Lx <= 1200 else 900
    H, t, leg, ins = 750, 28, 40, 60
    top, met = C(mats, v["top"]), M(mats, v["metal"])
    P = [Part("top", 0, 0, H - t, Lx, D, H, top, "top")]
    for i, (x, y) in enumerate([(ins, ins), (Lx - ins - leg, ins), (ins, D - ins - leg), (Lx - ins - leg, D - ins - leg)]):
        P.append(Part(f"leg{i}", x, y, 0, x + leg, y + leg, H - t, met, "frame"))
    P += [Part("apr_f", ins, ins, H - t - 60, Lx - ins, ins + 20, H - t, met, "frame"),
          Part("apr_b", ins, D - ins - 20, H - t - 60, Lx - ins, D - ins, H - t, met, "frame"),
          Part("apr_l", ins, ins, H - t - 60, ins + 20, D - ins, H - t, met, "frame"),
          Part("apr_r", Lx - ins - 20, ins, H - t - 60, Lx - ins, D - ins, H - t, met, "frame")]
    m = Model(P, [], [])
    m.checks = [f"Стол {Lx} × {D} × {H} мм, столешница {t} мм", f"4 квадратные ножки {leg}×{leg} в {ins} мм от краёв",
                "Под столешницей металлическая царга по периметру"]
    facts = [f"Rectangular dining table {Lx / 10:.0f} x {D / 10:.0f} cm, 75 cm high, {t} mm top in "
             f"{mats['colors'][v['top']]['prompt']}, four straight square {leg} mm steel legs set {ins / 10:.0f} cm in from "
             f"the edges joined by a slim steel apron; metal {mats['metal'][v['metal']]['prompt']}."]
    return m, facts


def desk_student(v, mats):
    """ARV-TBL-002 «Студент» — письменный стол 1200 × 750 × 600 с тумбой на 3 ящика."""
    c = C(mats, v["color"]); W, H, D = 1200, 750, 600
    side = v.get("side", "right")
    px0 = W - 416 if side == "right" else 0
    P = [Part("top", 0, 0, H - 22, W, D, H, c, "carcass")]
    P += _carcass("ped", px0, px0 + 416, 18, D, 0, H - 22, c)
    P += _drawers("pdr", px0, px0 + 416, 30, H - 22, c, 3)
    lx = 0 if side == "right" else W - 16
    P += [Part("leg", lx, 0, 0, lx + 16, D, H - 22, c, "carcass"),
          Part("modesty", 16 if side == "right" else 416, D - 120, 300, (W - 416) if side == "right" else W - 16, D - 104, H - 22, c, "carcass")]
    m = Model(P, [], []); m.wall_y = D
    m.checks = [f"Стол {W} × {H} × {D} мм, тумба с 3 ящиками {'справа' if side == 'right' else 'слева'}",
                "С другой стороны опора — сплошная боковина, сзади царга", "Ручки — чёрные скобы на ящиках"]
    facts = [f"Simple writing desk 120 x 60 cm, 75 cm high in {mats['colors'][v['color']]['prompt']}: a three-drawer "
             f"pedestal with black bar handles on the {side}, a solid side panel as the other support, a modesty panel at the back."]
    return m, facts


def bed_lift(v, mats):
    """ARV-BED-001 «Самал» — кровать из ЛДСП с подъёмным механизмом."""
    mw = int(v["size"]); c = C(mats, v["color"])
    W, L = mw + 64, 2032
    P = [Part("plinth", 40, 40, 0, W - 40, L - 40, 40, BLACK, "carcass"),
         Part("side_L", 0, 0, 40, 32, L, 400, c, "carcass"), Part("side_R", W - 32, 0, 40, W, L, 400, c, "carcass"),
         Part("foot", 32, 0, 40, W - 32, 32, 400, c, "carcass"), Part("bottom", 32, 32, 60, W - 32, L, 76, INNER, "interior"),
         Part("divider", W / 2 - 8, 32, 76, W / 2 + 8, L, 300, INNER, "interior"),
         Part("frame", 32, 32, 330, W - 32, L, 370, (150, 150, 150), "fronts"),
         Part("mattress", 40, 40, 370, W - 40, L - 8, 590, _rgb(mats, "fixed", "mattress"), "fronts"),
         Part("headboard", 0, L, 40, W, L + 32, 1100, c, "headboard")]
    pw = (mw - 120) / 2
    for i in range(2):
        x0 = 72 + i * (pw + 40)
        P.append(Part(f"pillow{i}", x0, L - 450, 590, x0 + pw, L - 60, 720, _rgb(mats, "fixed", "pillow"), "fronts"))
    m = Model(P, [], [])
    m.checks = [f"Кровать-короб под матрас {mw}×2000, борт 360 мм, изголовье 1100 мм от пола",
                "Короб стоит на утопленном чёрном цоколе 40 мм", "Под основанием — бельевой ящик (виден при снятых фасадах)"]
    facts = [f"Box bed for a {mw // 10} x 200 cm mattress in {mats['colors'][v['color']]['prompt']}: straight 36 cm high side "
             "rails, a flat rectangular headboard 110 cm high, set on a slim recessed black plinth; storage box with a lift-up base.",
             "Plain white mattress and two white pillows."]
    return m, facts


def nightstand(v, mats):
    """ARV-NST-001 «Самал» — тумба 450 × 400 × 500, 2 ящика. Геометрия — из инженерного ядра (tools/eng/samal.py)."""
    from eng.core import snapshot, to_model
    from eng.revisions import catalog_rev
    from eng.samal import D, build, palette
    snap = snapshot(build({"color": v["color"]}, catalog_rev("ARV-NST-001")))
    pal = palette(mats)
    for p in snap["parts"]:
        p["rgb"] = list(pal(p))
    m = to_model(snap)
    m.wall_y = D
    m.snapshot = snap
    m.checks = ["Тумба 450 × 500 × 400 мм, 2 ящика с ручками-скобами", "Чёрный утопленный цоколь 40 мм"]
    facts = [f"Bedside table 45 x 40 cm, 50 cm high, two drawers with slim black bar handles, "
             f"{mats['colors'][v['color']]['prompt']}, recessed black plinth."]
    return m, facts


def chest(v, mats):
    """ARV-NST-002 «Самал» — комод 800 × 850 × 450, 4 ящика."""
    c = C(mats, v["color"]); W, H, D = 800, 850, 450
    P = _carcass("b", 0, W, 18, D, 60, H, c) + _drawers("dr", 0, W, 60, H, c, 4)
    P.append(Part("pl", 20, 50, 0, W - 20, D - 20, 60, BLACK, "carcass"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = ["Комод 800 × 850 × 450 мм, 4 одинаковых ящика", "Чёрные ручки-скобы по центру ящиков, утопленный цоколь"]
    facts = [f"Chest of drawers 80 x 45 cm, 85 cm high with four equal drawers and slim black bar handles, "
             f"{mats['colors'][v['color']]['prompt']}, recessed black plinth."]
    return m, facts


def tv_floor(v, mats):
    """ARV-NST-003 «Кок-Тобе» — напольная ТВ-тумба 1600 × 450 × 400."""
    c = C(mats, v["color"]); W, H, D = 1600, 450, 400
    P = _carcass("b", 0, W, 18, D, 60, H, c)
    P += [Part("div1", 500, 18, 76, 516, D - 4, H - 16, c, "carcass"), Part("div2", W - 516, 18, 76, W - 500, D - 4, H - 16, c, "carcass"),
          Part("nsh", 516, 30, 240, W - 516, D - 4, 256, c, "carcass")]
    P += _fronts("dl", 0, 508, 60, H, c) + _fronts("dr", W - 508, W, 60, H, c)
    P += _hh("hl", 254, H - 50) + _hh("hr", W - 254, H - 50)
    for i, x in enumerate((30, W - 70, 30, W - 70)):
        y = 40 if i < 2 else D - 80
        P.append(Part(f"leg{i}", x, y, 0, x + 40, y + 40, 60, BLACK, "frame"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = ["Напольная тумба 1600 × 450 × 400 мм на 4 чёрных ножках 60 мм",
                "По краям две двери с ручками, в центре открытая ниша с полкой"]
    facts = [f"Low TV stand 160 x 40 cm, 45 cm high in {mats['colors'][v['color']]['prompt']}, two doors with black bar "
             "handles at the ends, an open centre niche with a shelf, four short black square legs."]
    return m, facts


# ---------------------------------------------------------------- трендовые
def bed_cocoon(v, mats):
    """ARV-BED-003 «Кокон» — кровать с мягкой стеновой панелью во всю стену, подвесные тумбы и бра."""
    mw = int(v["size"]); fab = _rgb(mats, "fabric", v["fabric"]); c = C(mats, v["color"])
    W, L = mw + 80, 2080
    PW = W + 2 * 650
    x0 = 650
    wall = L + 60
    P = [Part("base", x0 + 60, 60, 0, x0 + W - 60, L - 60, 60, BLACK, "carcass"),
         Part("bed", x0, 0, 60, x0 + W, L, 360, fab, "carcass"),
         Part("mattress", x0 + 40, 40, 360, x0 + W - 40, L - 20, 580, _rgb(mats, "fixed", "mattress"), "bedding")]
    pw = (mw - 120) / 2
    for i in range(2):
        a = x0 + 80 + i * (pw + 40)
        P.append(Part(f"pillow{i}", a, L - 450, 580, a + pw, L - 60, 710, _rgb(mats, "fixed", "pillow"), "bedding"))
    n = int(PW // 400)
    sw = PW / n
    for i in range(n):
        P.append(Part(f"soft{i}", i * sw + 4, L + 10, 300, (i + 1) * sw - 4, L + 40, 1500, fab, "headboard"))
    P.append(Part("panel_base", 0, L + 40, 0, PW, wall, 2500, c, "headboard"))
    for i, nx in enumerate((x0 - 600, x0 + W + 100)):
        P += _carcass(f"ns{i}", nx, nx + 500, L - 340, L + 10, 450, 650, c)
        P += _fronts(f"nsd{i}", nx, nx + 500, 450, 650, c, y0=L - 358)
        P += [Part(f"sconce{i}", nx + 230, L - 60, 1250, nx + 270, L + 10, 1450, BLACK, "decor"),
              Part(f"sconce{i}l", nx + 225, L - 70, 1350, nx + 275, L - 50, 1420, LED, "decor")]
    m = Model(P, [], []); m.wall_y = wall
    m.checks = [f"Кровать {mw}×2000 в мягкой ткани, стоит на утопленном чёрном цоколе",
                f"За ней мягкая стеновая панель во всю стену {PW:.0f} мм: {n} вертикальных секций высотой 1200 мм",
                "По бокам подвесные тумбы 500 мм с ящиком (без ножек) и два настенных бра"]
    facts = [f"Upholstered bed for a {mw // 10} x 200 cm mattress in {mats['fabric'][v['fabric']]['prompt']}, low 36 cm "
             "rails on a recessed black plinth.",
             f"Behind it a full-wall soft headboard {PW / 10:.0f} cm wide made of {n} vertical upholstered panels from 30 to "
             f"150 cm height, over a smooth wall cladding in {mats['colors'][v['color']]['prompt']}.",
             "On each side a wall-hung nightstand 50 cm wide with one handleless drawer, no legs, and a slim black wall "
             "sconce above with a warm glow."]
    return m, facts


def nightstand_float(v, mats):
    """ARV-NST-004 «Луна» — подвесная тумба с подсветкой и беспроводной зарядкой."""
    W = int(v["width"]); c = C(mats, v["color"]); D, z0, z1 = 350, 400, 600
    P = _carcass("b", 0, W, 18, D, z0, z1, c) + _fronts("d", 0, W, z0 + 70, z1, c)
    P += [Part("shelf_gap", 16, 18, z0 + 16, W - 16, 40, z0 + 70, INNER, "carcass"),
          Part("charger", W - 150, 120, z1, W - 60, 210, z1 + 4, GLASS_DARK, "decor"),
          Part("led", 20, 40, z0 - 4, W - 20, 60, z0, LED, "decor")]
    m = Model(P, [Glow(-80, -40, W + 80, D, (255, 196, 120), blur_mm=150)], []); m.wall_y = D
    m.checks = [f"Подвесная тумба {W} × {D} × {z1 - z0} мм, низ на высоте {z0} мм, ножек нет",
                "Верх — ящик без ручки, снизу открытая ниша", "Под тумбой тёплая подсветка на пол, на крышке круг зарядки"]
    facts = [f"Wall-hung bedside table {W / 10:.0f} x 35 cm, 20 cm high, floating 40 cm above the floor, no legs, "
             f"one handleless drawer over a slim open niche, {mats['colors'][v['color']]['prompt']}; warm LED glow from "
             "underneath on the floor and wall; a small black wireless charging pad set into the top."]
    return m, facts


def chest_fluted(v, mats):
    """ARV-NST-005 «Волна» — комод с рифлёными фасадами на металлическом цоколе."""
    W = int(v["width"]); c = C(mats, v["color"]); met = M(mats, v["metal"])
    D, legh, H = 450, 150, 900
    P = _carcass("b", 0, W, 18, D, legh, H, c)
    cols = 2 if W >= 1200 else 1
    for j in range(cols):
        xa, xb = j * W / cols, (j + 1) * W / cols
        z = legh
        for i in range(3):
            h = (H - legh) / 3
            P += _fronts(f"f{j}_{i}", xa, xb, z, z + h, c)
            P += _ribs(f"r{j}_{i}_", xa + 6, xb - 6, z + 8, z + h - 8, 0, c, step=32, rib=20, depth=8)
            z += h
    P += [Part("fr_f", 40, 40, legh - 20, W - 40, 60, legh, met, "frame"), Part("fr_b", 40, D - 60, legh - 20, W - 40, D - 40, legh, met, "frame")]
    for i, (x, y) in enumerate([(40, 40), (W - 60, 40), (40, D - 60), (W - 60, D - 60)]):
        P.append(Part(f"leg{i}", x, y, 0, x + 20, y + 20, legh, met, "frame"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = [f"Комод {W} × {H} × {D} мм на металлическом подстолье высотой {legh} мм",
                f"{cols * 3} ящиков с вертикальным рифлением (рейки ~20 мм, шаг 32 мм), ручек нет",
                "Тонкие металлические ножки 20×20 по углам"]
    facts = [f"Chest of drawers {W / 10:.0f} x 45 cm, 90 cm high, raised on a slim {mats['metal'][v['metal']]['prompt']} "
             f"frame base with 15 cm tall square legs; {cols * 3} handleless drawers with vertical fluted (reeded) fronts, "
             f"ribs about 2 cm wide; finish {mats['colors'][v['color']]['prompt']}."]
    return m, facts


def kitchen_island(v, mats):
    """ARV-KIT-005 «Остров» — кухня Gola + остров-барная стойка с рифлёным торцом."""
    m0, facts0 = kitchen_gola({"length": v["length"], "base": v["base"], "top": v["top"]}, mats)
    P = list(m0.parts)
    base_c = C(mats, v["base"])
    isl = int(v["island"]); L = int(v["length"])
    a = (L - isl) / 2
    loc = []
    for k in range(isl // 600):
        x = k * 600
        loc += _carcass(f"i{k}", x, x + 600, 18, 578, 120, 840, base_c)
        if k % 2 == 0:
            loc += _fronts(f"id{k}a", x, x + 600, 600, 810, base_c) + _fronts(f"id{k}b", x, x + 600, 120, 570, base_c)
            loc.append(Part(f"igC{k}", x, 25, 570, x + 600, 45, 600, BLACK, "carcass"))
        else:
            loc += _fronts(f"id{k}", x, x + 600, 120, 810, base_c)
        loc.append(Part(f"igL{k}", x, 25, 810, x + 600, 45, 840, BLACK, "carcass"))
    loc.append(Part("iplinth", 0, 50, 0, isl, 578, 120, base_c, "carcass"))
    P += _xform(loc, lambda x0, y0, x1, y1: (a + x0, -1200 - y1, a + x1, -1200 - y0), "")
    P += [Part("iwt", a - 40, -2100, 840, a + isl + 40, -1180, 878, STONE, "carcass"),
          Part("iwaterfall", a + isl, -2100, 0, a + isl + 40, -1180, 840, STONE, "carcass"),
          Part("iend", a - 40, -2100, 0, a, -1180, 840, base_c, "carcass")]
    P += _xform(_ribs("irib", -2090, -1190, 10, 830, 0, base_c, step=40, rib=24, depth=12),
                lambda x0, y0, x1, y1: (a - 40 + y0, x0, a - 40 + y1, x1), "")
    m = Model(P, [], []); m.wall_y = 600
    m.checks = m0.checks[:3] + [f"Остров {isl} × 900 мм в 1200 мм перед кухней, ящики обращены к кухне",
                                "Со стороны комнаты свес столешницы 300 мм под барные стулья",
                                "Левый торец острова рифлёный, правый — столешница опускается до пола"]
    facts = facts0 + [f"In front of it, with a 120 cm aisle, a kitchen island {isl / 10:.0f} x 90 cm with handleless drawers "
                      "facing the kitchen, a 30 cm worktop overhang on the room side for bar stools, the right end with a "
                      "waterfall worktop down to the floor and the left end panel with vertical fluted ribs."]
    return m, facts


def kitchen_loft(v, mats):
    """ARV-KIT-006 «Лофт» — кухня с открытыми полками на сварном каркасе вместо верхних шкафов."""
    L = int(v["length"]); base_c = C(mats, v["base"]); met = M(mats, "black"); oak = C(mats, "O")
    P, L = _kitchen_run("m", _std_mods(L), base_c, base_c, uppers=False)
    P += [Part("hood_c", 50, 278, 1500, 550, 578, 1580, BLACK, "appliances"),
          Part("hood_ch", 180, 400, 1580, 420, 578, 2300, BLACK, "appliances")]
    for z in (1550, 1900):
        P.append(Part(f"shelf{z}", 640, 300, z, L, 578, z + 30, oak, "shelves"))
    posts = [640] + [x for x in range(640 + 900, L - 100, 900)] + [L - 20]
    for i, x in enumerate(posts):
        P.append(Part(f"post{i}", x, 300, 1450, x + 20, 320, 2200, met, "frame"))
        for z in (1530, 1880):
            P.append(Part(f"arm{i}_{z}", x, 300, z, x + 20, 578, z + 20, met, "frame"))
    P.append(Part("topbar", 640, 300, 2180, L, 320, 2200, met, "frame"))
    m = Model(P, [], []); m.wall_y = 578
    m.checks = [f"Прямая кухня {L} мм без верхних шкафов, нижние фасады с чёрными ручками",
                f"Справа от вытяжки две дубовые полки 30 мм на сварной раме 20×20: {len(posts)} стоек и верхняя перекладина",
                "Над варочной панелью чёрная купольная вытяжка"]
    facts = [f"Industrial-style straight kitchen {L / 10:.0f} cm long with lower cabinets only in "
             f"{mats['colors'][v['base']]['prompt']} with slim black bar handles and a warm beige laminate worktop.",
             "Instead of wall cabinets: two thick open oak shelves held by a welded matte black square-tube frame "
             f"({len(posts)} thin vertical posts and a top rail) fixed to the wall; a black chimney hood over the hob."]
    return m, facts


def glass_cabinet(v, mats):
    """ARV-WRD-005 «Витрина» — шкаф с дверями в алюминиевой рамке с тонированным стеклом и подсветкой."""
    W = int(v["width"]); c = C(mats, v["color"]); H, D = 2000, 400
    nd = W // 400
    sh = (450, 850, 1250, 1650)
    P = _carcass("b", 0, W, 18, D, 80, H, c, shelves=sh)
    for z in sh:
        P.append(Part(f"led{z}", 20, 30, z - 4, W - 20, 45, z, LED, "interior"))
    P.append(Part("pl", 20, 50, 0, W - 20, D, 80, BLACK, "carcass"))
    dw = W / nd
    for i in range(nd):
        xa, xb = i * dw + 1.5, (i + 1) * dw - 1.5
        P += [Part(f"g{i}", xa + 20, 4, 83, xb - 20, 12, H - 3, TINT, "fronts"),
              Part(f"fL{i}", xa, 0, 82, xa + 20, 18, H - 2, BLACK, "fronts"), Part(f"fR{i}", xb - 20, 0, 82, xb, 18, H - 2, BLACK, "fronts"),
              Part(f"fT{i}", xa, 0, H - 22, xb, 18, H - 2, BLACK, "fronts"), Part(f"fB{i}", xa, 0, 82, xb, 18, 102, BLACK, "fronts")]
    for i in range(4):
        P.append(Part(f"obj{i}", 100 + i * (W - 250) / 3, 150, sh[i % 4] + 16, 150 + i * (W - 250) / 3, 250, sh[i % 4] + 196, (180, 170, 160), "decor"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = [f"Шкаф {W} × {H} × {D} мм, {nd} стеклянные двери в тонкой чёрной алюминиевой рамке 20 мм",
                "Стекло тонированное (серое), сквозь него видны полки", "Под каждой полкой светится тёплая LED-лента"]
    facts = [f"Display cabinet {W / 10:.0f} x 40 cm, 200 cm high, body in {mats['colors'][v['color']]['prompt']}, "
             f"{nd} tall doors of grey tinted glass in slim 2 cm matte black aluminium frames, four glass-visible shelves "
             "each lit by a warm LED strip, a few decorative objects inside, recessed black plinth."]
    return m, facts


def open_wardrobe(v, mats):
    """ARV-WRD-006 «Каркас» — открытая гардеробная система: сварные стойки + полки и ящики из плиты."""
    W = int(v["width"]); c = C(mats, v["color"]); met = M(mats, v["metal"])
    H, D, step = 2200, 450, 800
    xs = list(range(0, W + 1, step))
    P = []
    for i, x in enumerate(xs):
        x = min(x, W - 30)
        P += [Part(f"pf{i}", x, 30, 0, x + 30, 50, H, met, "frame"), Part(f"pb{i}", x, D - 50, 0, x + 30, D - 30, H, met, "frame"),
              Part(f"pt{i}", x, 30, H - 20, x + 30, D - 30, H, met, "frame"), Part(f"pm{i}", x, 30, 100, x + 30, D - 30, 120, met, "frame")]
    for k in range(len(xs) - 1):
        a, b = xs[k] + 30, min(xs[k + 1], W - 30)
        kind = "HSD"[k % 3]
        P.append(Part(f"top{k}", a, 30, H - 280, b, D - 30, H - 255, c, "shelves"))
        if kind == "H":
            P.append(Part(f"rod{k}", a, 215, H - 360, b, 240, H - 335, met, "frame"))
            P.append(Part(f"low{k}", a, 30, 300, b, D - 30, 325, c, "shelves"))
        elif kind == "S":
            for z in (500, 850, 1200, 1550):
                P.append(Part(f"sh{k}_{z}", a, 30, z, b, D - 30, z + 25, c, "shelves"))
        else:
            P += _carcass(f"dbox{k}", a, b, 40, D - 30, 120, 720, c)
            P += _drawers(f"dd{k}", a, b, 120, 720, c, 3, handles=False, y0=22)
            P.append(Part(f"rod{k}", a, 215, H - 360, b, 240, H - 335, met, "frame"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = [f"Открытая система {W} × {H} × {D} мм: {len(xs)} сварных рамы-стойки из трубы 30 мм",
                "Секции: штанга с полкой / 4 полки / комод из 3 ящиков без ручек + штанга",
                "Полки из плиты 25 мм, дверей нет"]
    facts = [f"Open walk-in wardrobe system {W / 10:.0f} cm wide, 220 cm high, 45 cm deep: {len(xs)} welded "
             f"{mats['metal'][v['metal']]['prompt']} ladder frames of slim square tube, between them 25 mm shelves in "
             f"{mats['colors'][v['color']]['prompt']}, hanging rails, open shelves and a low three-drawer box with handleless "
             "fronts; no doors."]
    return m, facts


def shelf_divider(v, mats):
    """ARV-LIV-002 «Грань» — стеллаж-перегородка из металла и дерева."""
    W = int(v["width"]); oak = C(mats, "O"); c = C(mats, v["color"]); met = M(mats, v["metal"])
    H, D = 2000, 350
    n = W // 400
    P = []
    for i in range(n + 1):
        x = min(i * 400, W - 20)
        P += [Part(f"pf{i}", x, 0, 0, x + 20, 20, H, met, "frame"), Part(f"pb{i}", x, D - 20, 0, x + 20, D, H, met, "frame")]
    levels = [0, 400, 800, 1200, 1600, H - 25]
    for j, z in enumerate(levels):
        P.append(Part(f"sh{j}", 0, 0, z, W, D, z + 25, oak, "shelves"))
    for j in range(len(levels) - 1):
        for i in range(n):
            if (i + j) % 3 == 1:
                a = i * 400 + 20
                P += _carcass(f"box{i}_{j}", a, a + 380, 10, D - 10, levels[j] + 25, levels[j] + 25 + 300, c)
                P.append(Part(f"boxf{i}_{j}", a, 0, levels[j] + 28, a + 380, 10, levels[j] + 322, c, "fronts"))
    m = Model(P, [], [])
    m.checks = [f"Стеллаж {W} × {H} × {D} мм из чёрных стоек 20×20 и 6 дубовых полок",
                "Открыт с обеих сторон — работает как перегородка", "Часть ячеек закрыта коробами из плиты в шахматном порядке"]
    facts = [f"Freestanding room-divider shelving {W / 10:.0f} x 35 cm, 200 cm high, open from both sides: thin "
             f"{mats['metal'][v['metal']]['prompt']} square posts, six solid oak shelves 25 mm thick, and some cells closed "
             f"by boxes with a flat front in {mats['colors'][v['color']]['prompt']} in a checkerboard rhythm."]
    return m, facts


def desk_frame(v, mats, office=False):
    """ARV-TBL-004 «Фокус» — рабочий стол на металлокаркасе с кабель-каналом и подвесной тумбой."""
    W = int(v["size"]); D = int(v.get("depth", 700)); top = C(mats, v["top"]); met = M(mats, v["metal"])
    H, t = 750, 25
    P = [Part("top", 0, 0, H - t, W, D, H, top, "top")]
    for i, x in enumerate((60, W - 120)):
        P += [Part(f"leg{i}a", x, 40, 0, x + 60, 70, H - t, met, "frame"), Part(f"leg{i}b", x, D - 70, 0, x + 60, D - 40, H - t, met, "frame"),
              Part(f"foot{i}", x, 30, 0, x + 60, D - 30, 30, met, "frame"), Part(f"bar{i}", x, 40, H - t - 30, x + 60, D - 40, H - t, met, "frame")]
    ped = v.get("pedestal", "yes") == "yes"
    xe = W - 610 if ped else W - 200          # лоток кабель-канала заканчивается у тумбы
    P += [Part("beam", 120, D - 120, H - t - 60, W - 120, D - 90, H - t - 30, met, "frame"),
          Part("tray", 200, D - 250, H - t - 120, xe, D - 120, H - t - 110, met, "frame"),   # дно лотка
          Part("tray_f", 200, D - 260, H - t - 120, xe, D - 250, H - t - 50, met, "frame")]  # передний борт (один гнутый лист с дном)
    if ped:
        c = top
        P += _carcass("ped", W - 600, W - 180, 30, 520, H - t - 330, H - t, c)
        P += _drawers("pd", W - 600, W - 180, H - t - 330, H - t, c, 2, handles=False, y0=12)
    if v.get("screen") == "front":
        P.append(Part("screen", 100, D - 20, H, W - 100, D, H + 400, (150, 150, 152), "screen"))
    m = Model(P, [], [])
    m.checks = [f"Стол {W} × {D} × {H} мм на двух прямоугольных металлических рамах 60×30",
                "Сзади под столешницей металлический кабель-канал",
                "Справа под столешницей подвесная тумба на 2 ящика без ручек" if ped else "Тумбы нет"]
    if v.get("screen") == "front":
        m.checks.append("Сверху по заднему краю экран-перегородка 400 мм")
    facts = [f"{'Office' if office else 'Home office'} desk {W / 10:.0f} x {D / 10:.0f} cm, 75 cm high, 25 mm top in "
             f"{mats['colors'][v['top']]['prompt']} on two closed rectangular {mats['metal'][v['metal']]['prompt']} side "
             "frames with a rear beam and a metal cable tray under the back edge" +
             ("; a hanging two-drawer handleless pedestal under the right side of the top." if ped else "."),
             ]
    if v.get("screen") == "front":
        facts.append("A grey 40 cm high privacy screen panel along the back edge.")
    return m, facts


def vanity_float(v, mats):
    """ARV-BTH-001 «Поток» — подвесная тумба под раковину на металлической раме."""
    W = int(v["width"]); c = C(mats, v["color"]); met = M(mats, v["metal"]); D = 460
    z_top = 850
    P = [Part("wt", 0, 0, z_top - 20, W, D, z_top, c, "top"),
         Part("sink", W / 2 - 250, 60, z_top, W / 2 + 250, 420, z_top + 130, CERAMIC, "appliances"),
         Part("faucet", W / 2 - 15, D - 20, z_top + 250, W / 2 + 15, D, z_top + 280, STEEL, "appliances"),
         Part("spout", W / 2 - 12, D - 200, z_top + 250, W / 2 + 12, D - 20, z_top + 270, STEEL, "appliances")]
    P += _carcass("box", 30, W - 30, 30, D, z_top - 320, z_top - 20, c)     # между стойками рамы 30 мм
    P += _fronts("dr", 30, W - 30, z_top - 320, z_top - 20, c)
    for i, x in enumerate((0, W - 30)):
        P += [Part(f"fv{i}", x, 0, 250, x + 30, 20, z_top - 20, met, "frame"),
              Part(f"fh{i}", x, 0, 250, x + 30, D, 270, met, "frame"),
              Part(f"fw{i}", x, D - 20, 250, x + 30, D, z_top - 20, met, "frame")]
    P.append(Part("shelf", 30, 20, 270, W - 30, D - 20, 290, C(mats, "O"), "shelves"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = [f"Подвесная тумба {W} × {D} мм, верх на высоте {z_top} мм, пол свободен",
                "Металлическая рама из трубы 30 мм держит столешницу и нижнюю дубовую полку",
                "Под столешницей один широкий ящик без ручки, сверху накладная раковина, смеситель из стены"]
    facts = [f"Wall-hung bathroom vanity {W / 10:.0f} x 46 cm, top at 85 cm, floor left free: a slim "
             f"{mats['metal'][v['metal']]['prompt']} tube frame carries a countertop and a wide handleless drawer in "
             f"{mats['colors'][v['color']]['prompt']}, an open oak shelf low in the frame, a white vessel basin on top and a "
             "wall-mounted faucet."]
    return m, facts


# ---------------------------------------------------------------- офис
def office_desk(v, mats):
    return desk_frame({**v, "pedestal": "no"}, mats, office=True)


def bench_system(v, mats):
    """ARV-OFF-002 «Бенч» — бенч-система на 2/4/6 мест с перегородками и кабель-каналом."""
    seats = int(v["seats"]); top = C(mats, v["top"]); met = M(mats, v["metal"])
    pairs = max(1, seats // 2)
    w, d, H = 1400, 700, 750
    W, D = pairs * w, 2 * d
    P = []
    for side in range(2):
        y0 = side * d
        for i in range(pairs):
            P.append(Part(f"top{side}_{i}", i * w + 2, y0 + 2, H - 25, (i + 1) * w - 2, y0 + d - 2, H, top, "top"))
    for i in range(pairs + 1):
        x = min(i * w, W - 60) if i else 40
        P += [Part(f"leg{i}a", x, 60, 0, x + 60, 90, H - 25, met, "frame"), Part(f"leg{i}b", x, D - 90, 0, x + 60, D - 60, H - 25, met, "frame"),
              Part(f"foot{i}", x, 50, 0, x + 60, D - 50, 30, met, "frame"), Part(f"bar{i}", x, 60, H - 55, x + 60, D - 60, H - 25, met, "frame")]
    P += [Part("tray", 100, d - 150, H - 140, W - 100, d + 150, H - 130, met, "frame"),
          Part("beam", 100, d - 15, H - 85, W - 100, d + 15, H - 55, met, "frame")]
    for i in range(pairs):
        P.append(Part(f"scr{i}", i * w + 50, d - 12, H, (i + 1) * w - 50, d + 12, H + 400, (150, 150, 152), "screen"))
    m = Model(P, [], [])
    m.checks = [f"Бенч на {seats} мест: {pairs} × 2 стола {w}×{d} лицом друг к другу, общий габарит {W} × {D}",
                f"{pairs + 1} общих металлических опор-рам, по центру кабель-канал",
                "Между сидящими напротив серые экраны-перегородки 400 мм"]
    facts = [f"Office bench desk system for {seats} people: {pairs} pairs of 140 x 70 cm desks facing each other, overall "
             f"{W / 10:.0f} x {D / 10:.0f} cm, tops in {mats['colors'][v['top']]['prompt']}, shared "
             f"{mats['metal'][v['metal']]['prompt']} rectangular leg frames, a central cable tray and grey 40 cm acoustic "
             "screens between facing desks."]
    return m, facts


def meeting_table(v, mats):
    """ARV-OFF-003 «Совет» — стол для переговоров с кабельным лючком."""
    L = int(v["length"]); D = 1200; H, t = 750, 25
    top = C(mats, v["top"]); met = M(mats, v["metal"])
    P = [Part("top", 0, 0, H - t, L, D, H, top, "top")]
    nb = 2 if L <= 3000 else 3
    xs = [300, L - 340] if nb == 2 else [300, L / 2 - 20, L - 340]
    for i, x in enumerate(xs):
        P += [Part(f"a{i}", x, 250, 0, x + 40, 290, H - t, met, "frame"), Part(f"b{i}", x, D - 290, 0, x + 40, D - 250, H - t, met, "frame"),
              Part(f"f{i}", x, 150, 0, x + 40, D - 150, 40, met, "frame"), Part(f"t{i}", x, 150, H - t - 40, x + 40, D - 150, H - t, met, "frame")]
    P += [Part("beam", 300, D / 2 - 20, H - t - 60, L - 300, D / 2 + 20, H - t - 20, met, "frame"),
          Part("cablebox", L / 2 - 200, D / 2 - 70, H - 2, L / 2 + 200, D / 2 + 70, H, (60, 62, 66), "top")]  # лючок заподлицо с крышкой
    m = Model(P, [], [])
    m.checks = [f"Стол {L} × {D} × {H} мм, {nb} металлических U-опоры, продольная балка",
                "По центру столешницы прямоугольный кабельный лючок 400×140", f"Мест: {2 * (L // 600)}"]
    facts = [f"Conference table {L / 10:.0f} x 120 cm, 75 cm high, 25 mm top in {mats['colors'][v['top']]['prompt']} on {nb} "
             f"{mats['metal'][v['metal']]['prompt']} closed rectangular frames joined by a longitudinal beam; a dark "
             "rectangular cable access box flush in the centre of the top."]
    return m, facts


def reception(v, mats):
    """ARV-OFF-004 «Приём» — стойка ресепшн: высокий борт 1100 + рабочая зона 750."""
    W = int(v["width"]); c = C(mats, v["color"]); acc = C(mats, v["accent"])
    D = 800
    P = [Part("front", 0, 0, 60, W, 40, 1060, acc, "carcass"),
         Part("ledge", -20, -40, 1060, W + 20, 320, 1100, c, "top"),
         Part("side_L", 0, 0, 0, 40, D, 1060, c, "carcass"), Part("side_R", W - 40, 0, 0, W, D, 1060, c, "carcass"),
         Part("work", 40, 40, 725, W - 40, D, 750, c, "top"),
         Part("plinth", 30, 20, 0, W - 30, 60, 60, BLACK, "carcass"),
         Part("led", 20, 18, 30, W - 20, 22, 60, LED, "decor")]
    P += _carcass("ped", W - 470, W - 40, 340, D, 0, 725, c) + _drawers("pd", W - 470, W - 40, 0, 725, c, 3, handles=False, y0=D)
    P += _ribs("frib", 20, W - 20, 80, 1040, 0, acc, step=40, rib=24, depth=12, group="carcass")
    m = Model(P, [], []); m.wall_y = None
    m.checks = [f"Стойка {W} × {D} мм: лицевой борт 1100 мм с рифлением, сверху полка для посетителей 360 мм",
                "За бортом рабочая зона 750 мм и тумба с 3 ящиками", "Внизу борта тонкая тёплая подсветка на пол"]
    facts = [f"Reception desk {W / 10:.0f} x 80 cm: a 110 cm high front panel with vertical fluted ribs in "
             f"{mats['colors'][v['accent']]['prompt']}, a transaction ledge on top in {mats['colors'][v['color']]['prompt']}, "
             "behind it a 75 cm work surface with a drawer pedestal, a warm LED line at the bottom of the front panel."]
    return m, facts


def mobile_pedestal(v, mats):
    """ARV-OFF-005 «Тумба» — мобильная тумба на колёсах, 3 ящика, замок."""
    c = C(mats, v["color"]); W, D, H = 420, 520, 600
    P = _carcass("b", 0, W, 18, D, 50, H, c) + _drawers("d", 0, W, 50, H, c, 3, heights=[180, 160, H - 50 - 340])
    for i, (x, y) in enumerate([(20, 30), (W - 60, 30), (20, D - 70), (W - 60, D - 70)]):
        P.append(Part(f"w{i}", x, y, 0, x + 40, y + 40, 50, BLACK, "frame"))
    P.append(Part("lock", W - 60, -6, H - 40, W - 40, 0, H - 20, STEEL, "fronts"))
    m = Model(P, [], [])
    m.checks = ["Тумба 420 × 520 × 600 мм на 4 колёсах", "3 ящика (верхний неглубокий) с ручками-скобами, замок сверху справа"]
    facts = [f"Mobile office pedestal 42 x 52 cm, 60 cm high on four small black casters, three drawers (shallow top "
             f"drawer) with slim black bar handles and a small lock, {mats['colors'][v['color']]['prompt']}."]
    return m, facts


def office_cabinet(v, mats):
    """ARV-OFF-006 «Архив» — офисный шкаф 800 × 2000 × 400: закрытый или с открытым верхом."""
    c = C(mats, v["color"]); W, H, D = 800, 2000, 400
    sh = (430, 800, 1170, 1540)
    P = _carcass("b", 0, W, 18, D, 60, H, c, shelves=sh)
    P.append(Part("pl", 20, 50, 0, W - 20, D, 60, c, "carcass"))
    if v["type"] == "closed":
        P += _fronts("d", 0, W, 60, H, c, n=2) + _hv("h0", 370, 1050) + _hv("h1", 430, 1050)
    else:
        P += _fronts("d", 0, W, 60, 800, c, n=2) + _hh("h0", 200, 760) + _hh("h1", 600, 760)
        for z in sh[1:]:
            P.append(Part(f"files{z}", 40, 120, z + 16, W - 300, 380, z + 316, (200, 190, 170), "decor"))
    m = Model(P, [], []); m.wall_y = D
    m.checks = ["Шкаф 800 × 2000 × 400 мм, 5 уровней под папки",
                "Две высокие двери с вертикальными ручками" if v["type"] == "closed" else "Внизу две двери до 800 мм, выше открытые полки"]
    facts = [f"Office storage cabinet 80 x 40 cm, 200 cm high in {mats['colors'][v['color']]['prompt']}, " +
             ("two tall doors with black vertical bar handles." if v["type"] == "closed"
              else "two low doors with black handles up to 80 cm, open shelves with file boxes above.")]
    return m, facts


def exec_desk(v, mats):
    """ARV-OFF-007 «Руководитель» — стол руководителя на панельных опорах + приставка с тумбой."""
    c = C(mats, v["color"]); acc = C(mats, v["accent"]); W = int(v["size"]); D, H = 900, 750
    P = [Part("top", 0, 0, H - 38, W, D, H, c, "top"),
         Part("leg_L", 0, 0, 0, 50, D, H - 38, c, "carcass"),
         Part("modesty", 50, 80, 250, W - 50, 98, H - 38, acc, "carcass")]
    side = v.get("return", "right")
    if side == "right":
        P.append(Part("leg_R", W - 50, 0, 0, W, D, H - 38, c, "carcass"))
        rx0 = W - 600
    else:
        P.append(Part("leg_R", W - 50, 0, 0, W, D, H - 38, c, "carcass"))
        rx0 = 0
    P.append(Part("ret_top", rx0, D, H - 38, rx0 + 600, D + 1100, H, c, "top"))
    P += _carcass("ret_ped", rx0, rx0 + 600, D, D + 1100, 0, H - 38, acc)
    # тумба приставки ящиками к руководителю (к центру)
    loc = _drawers("rd", 0, 450, 30, H - 38, acc, 3, handles=False)
    if side == "right":
        P += _xform(loc, lambda x0, y0, x1, y1: (rx0 - y1, D + 100 + x0, rx0 - y0, D + 100 + x1), "")
    else:
        P += _xform(loc, lambda x0, y0, x1, y1: (rx0 + 600 + y0, D + 100 + x0, rx0 + 600 + y1, D + 100 + x1), "")
    m = Model(P, [], [])
    m.checks = [f"Стол {W} × {D} × {H} мм, столешница 38 мм на двух сплошных панельных опорах 50 мм",
                f"{'Справа' if side == 'right' else 'Слева'} сзади приставка 1100 × 600 с тумбой: 3 ящика смотрят к креслу",
                "Царга спереди и тумба — акцентным цветом"]
    facts = [f"Executive desk {W / 10:.0f} x 90 cm with a 38 mm top in {mats['colors'][v['color']]['prompt']} on two solid "
             f"5 cm thick panel legs, a recessed modesty panel and a 110 x 60 cm return on the {side} side behind it "
             f"with a three-drawer handleless pedestal in {mats['colors'][v['accent']]['prompt']}."]
    return m, facts


BUILDERS.update({
    "kitchen_std": kitchen_std, "wardrobe_hinged": wardrobe_hinged, "wardrobe_sliding": wardrobe_sliding,
    "hallway_open": hallway_open, "table_4legs": table_4legs, "desk_student": desk_student, "bed_lift": bed_lift,
    "nightstand": nightstand, "chest": chest, "tv_floor": tv_floor,
    "bed_cocoon": bed_cocoon, "nightstand_float": nightstand_float, "chest_fluted": chest_fluted,
    "kitchen_island": kitchen_island, "kitchen_loft": kitchen_loft, "glass_cabinet": glass_cabinet,
    "open_wardrobe": open_wardrobe, "shelf_divider": shelf_divider, "desk_frame": desk_frame, "vanity_float": vanity_float,
    "office_desk": office_desk, "bench_system": bench_system, "meeting_table": meeting_table, "reception": reception,
    "mobile_pedestal": mobile_pedestal, "office_cabinet": office_cabinet, "exec_desk": exec_desk,
})
