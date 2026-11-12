"""Параметрические модели изделий Arvello.

Каждый builder получает вариант (словарь осей) и справочник материалов и возвращает:
  model — геометрия для референсов и чертежа;
  facts — точные английские фразы о конструкции и размерах для промпта
          (числа берутся из той же геометрии, поэтому промпт и референс не расходятся).
"""
from __future__ import annotations

from render import Glow, Model, Part


def _rgb(mats, kind, key):
    return tuple(mats[kind][key]["rgb"])


def floating_bed(v, mats):
    """ARV-BED-002 «Нимб» v2 — парящая кровать на стальном каркасе.

    Конструкция (по открытым планам парящих кроватей + расчёт устойчивости):
      - стальное основание 40x40x2: рама 1300x1700 + 2 поперечины + 6 опор с регулируемыми ножками,
        опоры строго по углам и серединам длинных сторон основания (они задают площадь опоры);
      - отступ основания от края платформы 200 мм со всех сторон (было 300 — опрокидывалась);
      - стальная рама платформы 40x40x2 + 5 поперечин на всю ширину, приварена к основанию;
      - облицовка ЛДСП 16: борт платформы 150 мм, нижняя крышка, тёмный цоколь вокруг опор;
      - ортопедические ламели на раме; изголовье на двух стальных стойках, крепится к платформе и к стене.
    v["view"] == "skeleton" — показать только несущий каркас (для цеха и проверки).
    """
    mw = int(v["size"])
    ml = 2000
    W, L = mw + 100, ml + 100
    inset = int(v.get("inset", 200))
    tube = 40
    leg_top = 220            # верх опор = низ рамы основания
    base_top = leg_top + tube  # 260 — верх рамы основания
    plat_z0, plat_z1 = 170, 320  # борт платформы
    slat_z = base_top + tube   # 300 — верх рамы платформы, на ней ламели
    body = _rgb(mats, "colors", v["color"])
    metal = _rgb(mats, "metal", "black")
    steel = (120, 124, 130)
    skeleton = v.get("view") == "skeleton"
    P = []
    bx0, by0, bx1, by1 = inset, inset, W - inset, L - inset
    # --- стальное основание
    legs_x = (bx0, bx1 - tube)
    legs_y = (by0, (by0 + by1 - tube) / 2, by1 - tube)
    for x in legs_x:
        for y in legs_y:
            P.append(Part(f"leg_{x:.0f}_{y:.0f}", x, y, 0, x + tube, y + tube, leg_top, steel if skeleton else metal, "base"))
    sb = [(bx0, by0, bx0 + tube, by1), (bx1 - tube, by0, bx1, by1), (bx0, by0, bx1, by0 + tube), (bx0, by1 - tube, bx1, by1)]
    for k in (1, 2):
        y = by0 + (by1 - by0) * k / 3 - tube / 2
        sb.append((bx0, y, bx1, y + tube))
    for i, (x0, y0, x1, y1) in enumerate(sb):
        P.append(Part(f"base_rail{i}", x0, y0, leg_top, x1, y1, base_top, steel if skeleton else metal, "base"))
    # --- стальная рама платформы
    c = 16  # толщина облицовки
    pr = [(c, c, c + tube, L - c), (W - c - tube, c, W - c, L - c), (c, c, W - c, c + tube), (c, L - c - tube, W - c, L - c)]
    for k in range(1, 6):
        y = c + (L - 2 * c) * k / 6 - tube / 2
        pr.append((c, y, W - c, y + tube))
    # продольная средняя — отрезками между поперечинами (поперечины сквозные, отрезки упираются)
    ys = [c + tube] + [c + (L - 2 * c) * k / 6 + s for k in range(1, 6) for s in (-tube / 2, tube / 2)] + [L - c - tube]
    for a, b in zip(ys[0::2], ys[1::2]):
        pr.append((W / 2 - tube / 2, a, W / 2 + tube / 2, b))
    for i, (x0, y0, x1, y1) in enumerate(pr):
        P.append(Part(f"plat_rail{i}", x0, y0, base_top, x1, y1, slat_z, steel if skeleton else body, "platform"))
    # ламели
    n_sl = 26
    for i in range(n_sl):
        y = c + 30 + i * (L - 2 * c - 60 - 53) / (n_sl - 1)
        for half in range(2):
            x0 = c + tube + 5 if half == 0 else W / 2 + tube / 2 + 5
            x1 = W / 2 - tube / 2 - 5 if half == 0 else W - c - tube - 5
            P.append(Part(f"slat{i}_{half}", x0, y, slat_z, x1, y + 53, slat_z + 8, (222, 196, 150), "slats"))
    # изголовье: стальные стойки
    hb_top = 1300
    for x in (W * 0.2, W * 0.8 - tube):
        P.append(Part(f"hb_post{x:.0f}", x, L, plat_z0, x + tube, L + 20, hb_top - 60, steel if skeleton else body, "headboard"))
    if not skeleton:
        # облицовка платформы
        P += [Part("side_front", 0, 0, plat_z0, W, c, plat_z1, body, "platform"),
              Part("side_back", 0, L - c, plat_z0, W, L, plat_z1, body, "platform"),
              Part("side_left", 0, c, plat_z0, c, L - c, plat_z1, body, "platform"),
              Part("side_right", W - c, c, plat_z0, W, L - c, plat_z1, body, "platform")]
        # нижняя крышка — рамка с вырезом под основание
        P += [Part("under_l", c, c, plat_z0, bx0, L - c, plat_z0 + 16, body, "platform"),
              Part("under_r", bx1, c, plat_z0, W - c, L - c, plat_z0 + 16, body, "platform"),
              Part("under_f", bx0, c, plat_z0, bx1, by0, plat_z0 + 16, body, "platform"),
              Part("under_b", bx0, by1, plat_z0, bx1, L - c, plat_z0 + 16, body, "platform")]
        # тёмный цоколь вокруг опор
        P.append(Part("plinth", bx0, by0, 15, bx1, by1, plat_z0, metal, "base"))
        top = plat_z1
        P.append(Part("mattress", 50, 50, top, W - 50, L - 50, top + 220, _rgb(mats, "fixed", "mattress"), "bedding"))
        pw = (mw - 120) / 2
        for i in range(2):
            x0 = 50 + 40 + i * (pw + 40)
            P.append(Part(f"pillow{i}", x0, L - 50 - 450, top + 220, x0 + pw, L - 50 - 60, top + 220 + 130,
                          _rgb(mats, "fixed", "pillow"), "bedding"))
        P.append(Part("headboard", 0, L + 20, plat_z0, W, L + 38, hb_top, body, "headboard"))
    hb = v["headboard"]
    if not skeleton and hb == "fluted":
        step, rib = 60, 36
        n = int((W - 40) // step)
        x = (W - n * step) / 2 + (step - rib) / 2
        for i in range(n):
            P.append(Part(f"rib{i}", x + i * step, L - 2, plat_z1 + 60, x + i * step + rib, L + 20, hb_top - 30,
                          body, "headboard"))
    elif not skeleton and hb == "soft":
        fab = _rgb(mats, "fabric", v.get("fabric", "beige"))
        n = 4 if mw <= 1600 else 5
        gap = 14
        pw2 = (W - 60 - gap * (n - 1)) / n
        for i in range(n):
            x0 = 30 + i * (pw2 + gap)
            P.append(Part(f"panel{i}", x0, L - 60, plat_z1 + 140, x0 + pw2, L + 20, hb_top - 40, fab, "headboard"))
    glows = []
    if v.get("led", "off") != "off" and not skeleton:
        led = _rgb(mats, "fixed", "led_warm" if v["led"] == "warm" else "led_neutral")
        glows.append(Glow(inset - 120, inset - 120, W - inset + 120, L - inset + 120, led, blur_mm=200))
    dims = [("front", "z", 0, plat_z0, W, 46, f"{plat_z0}"),
            ("front", "x", 0, inset, 60, 40, f"{inset}")]
    m = Model(P, glows, dims)
    m.checks = [f"Платформа {W}×{L} мм, борт {plat_z1 - plat_z0} мм, низ платформы на высоте {plat_z0} мм",
                f"Тёмное основание утоплено на {inset} мм со всех сторон — кровать «парит»",
                f"Изголовье во всю ширину, высота {hb_top} мм от пола, не касается пола",
                "Изголовье: " + {"flat": "гладкое", "fluted": "вертикальные рейки с шагом 60 мм", "soft": "мягкие вертикальные панели"}[hb]]
    n_soft = (4 if mw <= 1600 else 5)
    hb_desc = {
        "flat": "a flat smooth headboard panel",
        "fluted": "a headboard with closely spaced vertical fluted ribs (about 6 cm pitch)",
        "soft": f"an upholstered headboard made of {n_soft} tall vertical soft panels in "
                f"{mats['fabric'][v.get('fabric', 'beige')]['prompt']}",
    }[hb]
    facts = [
        f"Low rectangular platform bed for a {mw // 10} x {ml // 10} cm mattress; platform {W / 10:.0f} cm wide, "
        f"{L / 10:.0f} cm long, with a {(plat_z1 - plat_z0) / 10:.0f} cm high side panel; top of the platform "
        f"{plat_z1 / 10:.0f} cm above the floor.",
        f"Under the platform there is a dark recessed plinth set back {inset / 10:.0f} cm from every edge; the underside "
        f"of the platform is {plat_z0 / 10:.0f} cm above the floor, so the bed visibly floats with a shadow gap.",
        f"Headboard: {hb_desc}, full platform width, {hb_top / 10:.0f} cm high from the floor, directly behind the platform.",
        f"Platform and headboard material: {mats['colors'][v['color']]['prompt']}; plinth: {mats['metal']['black']['prompt']}.",
        "Plain white mattress with two white pillows, neatly made, no blanket hanging over the edges.",
    ]
    if v.get("led", "off") != "off":
        facts.append(f"A {mats['fixed']['led_warm' if v['led'] == 'warm' else 'led_neutral']['prompt']} "
                     "comes from under the platform and lights the floor around the plinth; no visible LED strip or wires.")
    else:
        facts.append("No lighting under the bed.")
    return m, facts


def dining_table_u(v, mats):
    """ARV-TBL-003 «Опора» — геометрия берётся из инженерного ядра (tools/eng/opora.py).

    Для 3D-каталога и фото используется каталожная ревизия из catalog/revisions.json (сейчас R00).
    Инженерные редакции (R02E) живут там же, но в каталог не попадают, пока их не утвердят."""
    from eng.core import snapshot, to_model
    from eng.opora import build, palette
    from eng.revisions import catalog_rev
    snap = snapshot(build({"size": int(v["size"]), "top": v["top"], "metal": v["metal"]}, catalog_rev("ARV-TBL-003")))
    m = to_model(snap, palette(mats))
    d = snap["derived"]
    Lx, D, H, t = d["length"], d["width"], d["height"], d["top_t"]
    inset, prof = 150, 40
    m.dims = [("front", "x", 0, inset, H - t, -40, f"{inset}")]
    m.snapshot = snap
    seats = 4 if Lx <= 1400 else 6
    m.checks = [f"Столешница {Lx}×{D}×{t} мм, высота стола {H} мм",
                f"Две замкнутые прямоугольные рамы из трубы {prof}×{prof}, в {inset} мм от торцов"]
    if d["link"]:
        m.checks.append("Под столешницей две продольные трубы между рамами, снизу видны")
    else:
        m.checks.append("Между рамами нет перемычки, других ножек нет")
    if d["feet_h"]:
        m.checks.append(f"Рамы стоят на 4 круглых опорах, нижняя перекладина в {d['feet_h']} мм над полом")
    facts = [
        f"Rectangular dining table {Lx / 10:.0f} x {D / 10:.0f} cm, total height {H / 10:.0f} cm, seats {seats}.",
        f"Table top {t} mm thick with straight square edges, made of {mats['colors'][v['top']]['prompt']}.",
        f"Base: two closed rectangular welded frames made of {prof} x {prof} mm square steel tube, one near each end of the "
        f"table, {inset / 10:.0f} cm in from the ends; each frame is a vertical rectangle {d['bar'] / 10:.0f} cm wide "
        f"(two legs, top bar under the top, foot bar " + ("on the floor). " if not d["feet_h"] else
        f"{d['feet_h'] / 10:.1f} cm above the floor on four small round glides). ") +
        ("Two slim longitudinal tubes run under the top between the frames." if d["link"]
         else "No other legs, no stretcher between the frames."),
        f"Metal: {mats['metal'][v['metal']]['prompt']}.",
    ]
    return m, facts


BUILDERS = {"floating_bed": floating_bed, "dining_table_u": dining_table_u}


def floating_bed_wood(v, mats):
    """ARV-BED-002W «Нимб Wood» — деревянная версия парящей кровати.

    Основа: открытый план Ana White «Simple Floating Bed» (продажа изделий разрешена автором),
    переведён в мм и под местные материалы. Отличия от оригинала:
      - брус 45x95 вместо 2x4 (38x89), мебельный щит 20 мм вместо доски 1x10;
      - наружные «лестницы» шире (вставки 200 мм вместо 133), основание стоит ПОД вставками —
        так получен отступ ~140 мм вместо ~70 мм и нагрузка идёт в основание напрямую;
      - основание из бруса 45x145 (просвет 145 мм, иначе «парения» почти не видно);
      - 5 вставок в каждой лестнице вместо 3; 14 ламелей вместо 10 (зазор ~50 мм под пенные матрасы).
    """
    mw = int(v["size"])
    c = 20                    # щит боковин и изножья
    W = mw + 2 * c
    ml = 2000
    y0, y1 = c, c + ml        # рамы-лестницы по длине
    rb, rh = 45, 95           # брус
    base_z1 = 145             # основание 45x145 на ребро: 0..145 (просвет под кроватью)
    lad_z0, lad_z1 = base_z1, base_z1 + rh   # лестницы 145..240
    slat_t = 20
    top = lad_z1 + slat_t     # 260 — верх ламелей
    rail_z1 = lad_z0 + 235    # 380 — верх боковин
    blk_o, blk_c = 200, 120
    inset = 140               # наружная плоскость щита -> наружная грань основания
    body = _rgb(mats, "colors", v["color"])
    dark = _rgb(mats, "metal", "black")
    raw = (214, 186, 140)
    skeleton = v.get("view") == "skeleton"
    wood = raw if skeleton else body
    P = []
    # основание (тёмное)
    bx0, bx1 = inset, W - inset
    by0 = inset
    P += [Part("base_l", bx0, by0, 0, bx0 + rb, y1, base_z1, dark, "base"),
          Part("base_r", bx1 - rb, by0, 0, bx1, y1, base_z1, dark, "base"),
          Part("base_f", bx0 + rb, by0, 0, bx1 - rb, by0 + rb, base_z1, dark, "base"),
          Part("base_b", bx0 + rb, y1 - rb, 0, bx1 - rb, y1, base_z1, dark, "base")]
    # лестницы
    lad = [(c, blk_o), (W - c - 2 * rb - blk_o, blk_o), (W / 2 - rb - blk_c / 2, blk_c)]
    for i, (x, blk) in enumerate(lad):
        P += [Part(f"lad{i}_a", x, y0, lad_z0, x + rb, y1, lad_z1, wood, "frame"),
              Part(f"lad{i}_b", x + rb + blk, y0, lad_z0, x + 2 * rb + blk, y1, lad_z1, wood, "frame")]
        for k in range(5):
            y = y0 + k * (ml - rb) / 4
            P.append(Part(f"lad{i}_blk{k}", x + rb, y, lad_z0, x + rb + blk, y + rb, lad_z1, wood, "frame"))
    # ламели
    n = 14
    sw = 95 if mw <= 1600 else 120   # для 1800 пролёт между лестницами больше -> ламель шире
    gap = (ml - n * sw) / (n - 1)
    for i in range(n):
        y = y0 + i * (sw + gap)
        P.append(Part(f"slat{i}", c, y, lad_z1, W - c, y + sw, top, (222, 196, 150), "slats"))
    hb_top = 1220
    P += [Part("leg_l", 0, y1, 0, 95, y1 + rb, hb_top - 45, wood, "headboard"),
          Part("leg_r", W - 95, y1, 0, W, y1 + rb, hb_top - 45, wood, "headboard"),
          Part("hb_top", 0, y1, hb_top - 45, W, y1 + 45, hb_top, wood, "headboard")]
    if not skeleton:
        P += [Part("rail_l", 0, y0, lad_z0, c, y1, rail_z1, body, "rails"),
              Part("rail_r", W - c, y0, lad_z0, W, y1, rail_z1, body, "rails"),
              Part("foot", 0, 0, lad_z0, W, c, rail_z1, body, "rails"),
              Part("hb_panel", 0, y1 + rb, lad_z0, W, y1 + rb + 9, hb_top, body, "headboard"),
              Part("mattress", c + 5, y0 + 5, top, W - c - 5, y1 - 5, top + 220, _rgb(mats, "fixed", "mattress"), "bedding")]
        pw = (mw - 120) / 2
        for i in range(2):
            x0 = c + 40 + i * (pw + 40)
            P.append(Part(f"pillow{i}", x0, y1 - 450, top + 220, x0 + pw, y1 - 60, top + 350,
                          _rgb(mats, "fixed", "pillow"), "bedding"))
    dims = [("front", "z", 0, lad_z0, W, 46, f"{lad_z0}"),
            ("front", "x", 0, inset, 60, 40, f"{inset}")]
    m = Model(P, [], dims)
    m.checks = [f"Рама {W}×{y1 + rb + 9} мм, боковины 235 мм выступают над ламелями на {rail_z1 - top} мм",
                f"Чёрное основание утоплено на {inset} мм, просвет под кроватью {lad_z0} мм",
                f"Изголовье — рамка {hb_top} мм: две стойки стоят на полу, верхний брус, панель сзади",
                f"Ламелей 14, три продольные рамы-лестницы"]
    facts = [
        f"Low solid-wood platform bed for a {mw // 10} x {ml // 10} cm mattress; frame {W / 10:.0f} cm wide and "
        f"{(y1 + rb) / 10:.1f} cm long; 2 cm thick side boards {235 / 10:.1f} cm high rise {(rail_z1 - top) / 10:.0f} cm "
        "above the slats and hold the mattress like a tray.",
        f"A dark recessed base set back {inset / 10:.0f} cm from the sides and the foot; the underside of the bed is "
        f"{lad_z0 / 10:.1f} cm above the floor, so the bed looks like it floats.",
        f"Headboard: a simple wooden frame {hb_top / 10:.0f} cm high from the floor, two square legs at the corners standing "
        "on the floor, a top rail and a recessed flat panel between the legs.",
        f"Wood finish: {mats['colors'][v['color']]['prompt']}; base: matte black.",
        "Plain white mattress with two white pillows, neatly made.",
    ]
    return m, facts


BUILDERS["floating_bed_wood"] = floating_bed_wood


# ---------------------------------------------------------------- корпусная мебель
# Корпусная мебель строится по стандартным размерам систем Blum (корпус ЛДСП 16 мм,
# фасад 18 мм, зазор 3 мм) и сверяется с открытыми шаблонами Ana White.
# Оси: x — ширина (слева направо), y — глубина (y=0 — лицевая плоскость фасадов, к стене y растёт), z — высота.

BLACK = (34, 34, 36)
STEEL = (168, 170, 174)
INNER = (236, 234, 229)       # внутренняя ЛДСП белая
STONE = (214, 210, 203)       # светлый кварц
GLASS_DARK = (24, 24, 26)
MIRROR = (196, 206, 212)


def _carcass(name, x0, x1, y0, y1, z0, z1, color, t=16, shelves=(), group="carcass"):
    """Полый корпус: боковины, дно, крышка, задняя стенка ХДФ, полки на высотах shelves."""
    P = [Part(f"{name}_L", x0, y0, z0, x0 + t, y1, z1, color, group),
         Part(f"{name}_R", x1 - t, y0, z0, x1, y1, z1, color, group),
         Part(f"{name}_bot", x0 + t, y0, z0, x1 - t, y1, z0 + t, color, group),
         Part(f"{name}_top", x0 + t, y0, z1 - t, x1 - t, y1, z1, color, group),
         Part(f"{name}_back", x0 + t, y1 - 4, z0 + t, x1 - t, y1, z1 - t, INNER, group)]
    for i, z in enumerate(shelves):
        P.append(Part(f"{name}_sh{i}", x0 + t, y0 + 20, z, x1 - t, y1 - 4, z + t, INNER, "interior"))
    return P


def _fronts(name, x0, x1, z0, z1, color, n=1, y0=0, t=18, gap=3):
    """n фасадов в ряд по ширине x0..x1 с зазором gap."""
    w = (x1 - x0) / n
    return [Part(f"{name}{i}", x0 + i * w + gap / 2, y0, z0 + gap / 2, x0 + (i + 1) * w - gap / 2, y0 + t, z1 - gap / 2,
                 color, "fronts") for i in range(n)]


def _paint_ends(P, names, color):
    """Видимые торцевые боковины — в цвет фасадов."""
    for p in P:
        if p.name in names:
            p.color = color


def kitchen_gola(v, mats):
    """ARV-KIT-004 «Монолит» — линейная кухня без ручек (профиль Gola), колонны до верха антресолей.

    Источник размеров: модули Blum (корпус 720, глубина 560, ЛДСП 16), сверка — Ana White frameless base/wall.
    """
    L = int(v["length"])
    base_c = _rgb(mats, "colors", v["base"])
    top_c = _rgb(mats, "colors", v["top"])
    plinth, carc_top, wt = 120, 840, 38
    wt_top = carc_top + wt                 # 878 — рабочая поверхность
    gola = 30                               # высота канала Gola
    up0, up1 = 1460, 2380                   # верхние шкафы 920 мм
    cy0, cy1 = 18, 578                      # корпус низа
    uy0 = cy1 - 300                         # корпус верха глубиной 300
    P = []
    n_cols = 1 if L < 3000 else 2
    bx0 = 600 * n_cols
    rem = L - bx0 - 1400
    mods = [("drawers", 600)]
    sink_w = 800
    while rem >= 600:
        mods.append(("doors", 600)); rem -= 600
    if rem >= 300:
        mods.append(("doors", rem))
    else:
        sink_w += rem
    mods.append(("sink", sink_w))
    # колонны
    for i in range(n_cols):
        x0 = i * 600
        P += _carcass(f"col{i}", x0, x0 + 600, cy0, cy1, plinth, up1, top_c,
                      shelves=() if i == 0 else (1500, 1900))
        if i == 0:   # встроенный холодильник
            P.append(Part("fridge", x0 + 20, cy0 + 10, plinth + 20, x0 + 580, cy1 - 10, 1900, (226, 228, 230), "interior"))
            P += _fronts("col0_low", x0, x0 + 600, plinth, 1440, top_c)
            P += _fronts("col0_up", x0, x0 + 600, 1440, up1, top_c)
        else:        # духовой шкаф + микроволновка
            P += _fronts("col1_low", x0, x0 + 600, plinth, 840, top_c)
            P.append(Part("oven", x0 + 4, 0, 843, x0 + 596, 22, 1437, GLASS_DARK, "appliances"))
            P.append(Part("micro", x0 + 4, 0, 1440, x0 + 596, 22, 1820, GLASS_DARK, "appliances"))
            P += _fronts("col1_up", x0, x0 + 600, 1820, up1, top_c)
    # низ
    x = bx0
    for k, (kind, w) in enumerate(mods):
        P += _carcass(f"base{k}", x, x + w, cy0, cy1, plinth, carc_top, base_c,
                      shelves=() if kind == "drawers" else (480,))
        P.append(Part(f"gola_L{k}", x, 25, carc_top - gola, x + w, 45, carc_top, BLACK, "carcass"))
        if kind == "drawers":
            z_c = 570
            P += _fronts(f"drw{k}a", x, x + w, z_c + gola, carc_top - gola, base_c)
            P.append(Part(f"gola_C{k}", x, 25, z_c, x + w, 45, z_c + gola, BLACK, "carcass"))
            mid = (plinth + z_c) / 2
            P += _fronts(f"drw{k}b", x, x + w, mid, z_c, base_c)
            P += _fronts(f"drw{k}c", x, x + w, plinth, mid, base_c)
            P.append(Part("hob", x + 5, 40, wt_top, x + w - 5, 560, wt_top + 6, GLASS_DARK, "appliances"))
        else:
            P += _fronts(f"door{k}_", x, x + w, plinth, carc_top - gola, base_c, n=1 if w <= 600 else 2)
        if kind == "sink":
            xc = x + w / 2
            P += [Part("sink", xc - 260, 70, wt_top, xc + 260, 500, wt_top + 3, STEEL, "appliances"),
                  Part("faucet", xc - 15, 520, wt_top, xc + 15, 550, wt_top + 320, STEEL, "appliances"),
                  Part("spout", xc - 12, 380, wt_top + 290, xc + 12, 550, wt_top + 320, STEEL, "appliances")]
        # верх над модулем
        P += _carcass(f"up{k}", x, x + w, uy0, cy1, up0, up1, top_c, shelves=(up0 + 300, up0 + 600))
        P += _fronts(f"updoor{k}_", x, x + w, up0 - 20, up1, top_c, n=1 if w <= 600 else 2, y0=uy0 - 18)
        x += w
    P.append(Part("plinth", 0, 50, 0, L, cy1, plinth, base_c, "carcass"))
    P.append(Part("worktop", bx0, -22, carc_top, L, cy1, wt_top, STONE, "carcass"))
    m = Model(P, [], [])
    n_low = sum(1 for p in P if p.group == "fronts" and p.z1 <= carc_top and p.x0 >= bx0)
    n_up = sum(1 for p in P if p.group == "fronts" and p.z0 >= up0 - 30)
    m.checks = [f"Слева {n_cols} колонн{'а' if n_cols == 1 else 'ы'} до верха верхних шкафов",
                f"Нижних фасадов: {n_low}, верхних: {n_up}, ручек нет",
                "Под столешницей тёмный горизонтальный канал Gola, второй канал над нижними ящиками",
                "Варочная панель над модулем с ящиками, мойка — крайний правый модуль",
                "Цоколь утоплен, столешница светлая, верх и низ разных цветов"]
    m.wall_y = 600
    facts = [
        f"Straight one-wall kitchen {L / 10:.0f} cm long, fully handleless with a recessed black Gola channel profile "
        "running under the worktop and above the lower drawers; flat slab fronts with 3 mm gaps, no handles or knobs.",
        f"Left end: {n_cols} tall column cabinet{'s' if n_cols > 1 else ''} 60 cm wide reaching the top of the wall cabinets "
        f"({up1 / 10:.0f} cm high){', one with built-in black oven and microwave' if n_cols > 1 else ''}.",
        f"Lower cabinets {wt_top / 10:.1f} cm high to the worktop, recessed plinth; lower fronts in "
        f"{mats['colors'][v['base']]['prompt']}.",
        f"Wall cabinets {(up1 - up0) / 10:.0f} cm tall, 30 cm deep, bottom at {up0 / 10:.0f} cm, fronts extend 2 cm below the "
        f"cabinets as a finger pull; wall cabinets and columns in {mats['colors'][v['top']]['prompt']}.",
        "Light warm grey quartz worktop 38 mm thick; black glass induction hob above the drawer unit; "
        "stainless steel undermount sink with a tall faucet at the right end.",
    ]
    return m, facts


def wardrobe_flush(v, mats):
    """ARV-WRD-004 «Стена» — встроенный шкаф до потолка без ручек (push-to-open)."""
    W, H = int(v["width"]), int(v["height"])
    c = _rgb(mats, "colors", v["color"])
    plinth = 80
    main_top = 2040 if H <= 2400 else 2280
    y0, y1 = 18, 600
    n = W // 600
    pattern = {2: "HS", 3: "HSD", 4: "HSSD"}[n]
    P = []
    for i, kind in enumerate(pattern):
        x0 = i * 600
        sh = [main_top - 300]
        if kind == "S":
            sh = list(range(plinth + 16 + 480, main_top - 200, 340)) + [main_top - 300]
            for d in range(2):
                z = plinth + 30 + d * 220
                P.append(Part(f"drawer{i}_{d}", x0 + 22, y0 + 20, z, x0 + 578, y1 - 40, z + 200, INNER, "interior"))
        P += _carcass(f"sec{i}", x0, x0 + 600, y0, y1, plinth, main_top, INNER, shelves=sorted(set(sh)))
        if kind in "HD":
            P.append(Part(f"rod{i}", x0 + 16, 290, main_top - 380, x0 + 584, 315, main_top - 355, STEEL, "interior"))
        if kind == "D":
            P.append(Part(f"rod{i}b", x0 + 16, 290, 1000, x0 + 584, 315, 1025, STEEL, "interior"))
        P += _carcass(f"mez{i}", x0, x0 + 600, y0, y1, main_top, H, INNER)
        P += _fronts(f"door{i}", x0, x0 + 600, plinth, main_top, c)
        P += _fronts(f"mezdoor{i}", x0, x0 + 600, main_top, H, c)
    P.append(Part("plinth", 0, 50, 0, W, y1, plinth, c, "carcass"))
    _paint_ends(P, ("sec0_L", "mez0_L", f"sec{n - 1}_R", f"mez{n - 1}_R"), c)
    m = Model(P, [], [])
    m.wall_y = y1
    m.checks = [f"{n} высоких двер{'и' if n < 5 else 'ей'} + {n} антресольных, ручек нет (открывание нажатием)",
                f"Высота до потолка {H} мм, двери {main_top - plinth} мм, антресоль {H - main_top} мм",
                "Все фасады одного цвета, зазоры 3 мм, цоколь утоплен на 5 см",
                "Внутри: " + ", ".join({"H": "штанга", "S": "полки + 2 ящика", "D": "две штанги"}[k] for k in pattern)]
    facts = [
        f"Built-in wardrobe {W / 10:.0f} cm wide, floor to ceiling {H / 10:.0f} cm, 60 cm deep, flush with the wall like a "
        "flat wall of doors.",
        f"{n} tall flat doors {(main_top - plinth) / 10:.0f} cm high and {n} small upper doors above them, all the same width, "
        "3 mm gaps, no handles at all (push-to-open).",
        f"All fronts in {mats['colors'][v['color']]['prompt']}; recessed 8 cm plinth in the same color.",
    ]
    return m, facts


def hallway_set(v, mats):
    """ARV-WRD-007 «Вход» — шкаф до потолка + подвесная скамья на кронштейнах + зеркало с подсветкой."""
    W = int(v["width"])
    c = _rgb(mats, "colors", v["color"])
    cab_w = {1600: 800, 2000: 1000, 2400: 1200}[W]
    bench_w = W - cab_w
    H, plinth, main_top = 2400, 80, 2040
    wall = 568
    P = []
    x0 = bench_w
    P += _carcass("cab", x0, W, 18, wall, plinth, main_top, INNER, shelves=(main_top - 300, plinth + 16 + 200))
    P.append(Part("rod", x0 + 16, 280, main_top - 380, W - 16, 305, main_top - 355, STEEL, "interior"))
    P += _carcass("cabmez", x0, W, 18, wall, main_top, H, INNER)
    P += _fronts("door", x0, W, plinth, main_top, c, n=2 if cab_w > 600 else 1)
    P += _fronts("mezdoor", x0, W, main_top, H, c, n=2 if cab_w > 600 else 1)
    P.append(Part("plinth", x0, 50, 0, W, wall, plinth, c, "carcass"))
    _paint_ends(P, ("cab_L", "cabmez_L", "cab_R", "cabmez_R"), c)
    # скамья: щит 40 мм на двух стальных Г-кронштейнах
    seat_z0, seat_z1, bd = 420, 460, 350
    P.append(Part("seat", 20, wall - bd, seat_z0, bench_w - 20, wall, seat_z1, c if v["color"] == "O" else _rgb(mats, "colors", "O"), "bench"))
    for i, bx in enumerate((150, bench_w - 190)):
        P += [Part(f"br{i}_v", bx, wall - 20, 260, bx + 40, wall, seat_z0, BLACK, "bench"),
              Part(f"br{i}_h", bx, wall - bd + 20, seat_z0 - 20, bx + 40, wall, seat_z0, BLACK, "bench")]
    mw = min(600, bench_w - 300)
    mc = bench_w / 2
    P.append(Part("mirror", mc - mw / 2, wall - 25, 900, mc + mw / 2, wall, 1900, MIRROR, "mirror"))
    m = Model(P, [], [])
    m.wall_y = wall
    nd = 2 if cab_w > 600 else 1
    m.checks = [f"Справа шкаф {cab_w} мм до потолка: {nd} высок{'ие двери' if nd > 1 else 'ая дверь'} + антресоль, без ручек",
                f"Слева подвесная скамья {bench_w - 40} мм на двух чёрных кронштейнах, под ней пол свободен",
                f"Над скамьёй зеркало {mw:.0f}×1000 мм с подсветкой по контуру",
                "Сиденье скамьи — дуб (щит 40 мм)"]
    facts = [
        f"Entryway set {W / 10:.0f} cm wide against one wall: on the right a floor-to-ceiling wardrobe {cab_w / 10:.0f} cm wide "
        f"and 57 cm deep with {nd} tall handleless door{'s' if nd > 1 else ''} and small upper door{'s' if nd > 1 else ''}, "
        f"fronts in {mats['colors'][v['color']]['prompt']}.",
        f"On the left a wall-mounted floating bench {(bench_w - 40) / 10:.0f} cm long, 35 cm deep, seat 4 cm thick oak at "
        "46 cm height, carried by two slim black steel L-brackets fixed to the wall; the floor under the bench is free.",
        f"Above the bench a rectangular frameless mirror {mw / 10:.0f} x 100 cm with a soft warm LED glow around its edge.",
    ]
    return m, facts


def tv_unit(v, mats):
    """ARV-LIV-001 «Экран» — подвесная ТВ-тумба + стеновая панель (гладкая или с накладными рейками)."""
    L = int(v["length"])
    c = _rgb(mats, "colors", v["color"])
    panel = v.get("panel", "none")
    z0, z1, depth = 250, 600, 400
    n = L // 600
    pattern = {3: "DOD", 4: "DOOD"}[n]
    P = []
    P += _carcass("con", 0, L, 18, depth, z0, z1, c, shelves=())
    for i in range(1, n):
        P.append(Part(f"div{i}", i * 600 - 8, 18, z0 + 16, i * 600 + 8, depth - 4, z1 - 16, c, "carcass"))
    for i, k in enumerate(pattern):
        if k == "D":
            P += _fronts(f"flap{i}", i * 600, (i + 1) * 600, z0, z1, c)
    wall = depth
    if panel != "none":
        pc = _rgb(mats, "colors", v.get("panel_color", v["color"]))
        P.append(Part("panel", 0, depth, 0, L, depth + 18, 2400, pc, "panel"))
        wall = depth + 18
        if panel == "slats":
            step, rib = 60, 40
            k = int((L - 20) // step)
            xs = (L - k * step) / 2 + (step - rib) / 2
            for i in range(k):
                for (a, b) in ((0, z0 - 10), (z1 + 10, 2400)):
                    P.append(Part(f"slat{i}_{a}", xs + i * step, depth - 20, a, xs + i * step + rib, depth, b, pc, "panel"))
    tvw, tvh = 1440, 830
    P.append(Part("tv", L / 2 - tvw / 2, depth - 60, 800, L / 2 + tvw / 2, depth - 30, 800 + tvh, GLASS_DARK, "decor"))
    m = Model(P, [], [])
    m.wall_y = wall
    nf = pattern.count("D")
    m.checks = [f"Подвесная тумба {L} × {depth} × {z1 - z0} мм, низ на высоте {z0} мм, ножек нет",
                f"{nf} откидных фасада без ручек по краям, {pattern.count('O')} открытых ниш{'и' if pattern.count('O') > 1 else 'а'} в центре",
                {"none": "Стеновой панели нет", "flat": "За тумбой гладкая панель от пола до 2400 мм",
                 "slats": "За тумбой панель с вертикальными рейками 40 мм с шагом 60 мм"}[panel],
                "Телевизор 65\" (1440×830) — только для масштаба"]
    facts = [
        f"Wall-mounted floating TV console {L / 10:.0f} cm long, {depth / 10:.0f} cm deep, {(z1 - z0) / 10:.0f} cm high, "
        f"bottom edge {z0 / 10:.0f} cm above the floor, no legs; {nf} handleless flip-down doors at the ends and "
        f"{pattern.count('O')} open center niche{'s' if pattern.count('O') > 1 else ''}; {mats['colors'][v['color']]['prompt']}.",
        {"none": "Plain painted wall behind, no wall panel.",
         "flat": f"Behind it a flat wall panel {L / 10:.0f} cm wide from floor to 240 cm in the same finish.",
         "slats": f"Behind it a wall panel {L / 10:.0f} cm wide from floor to 240 cm covered with vertical wooden slats "
                  "4 cm wide with 2 cm gaps, in the same finish."}[panel],
        "A 65-inch black TV mounted on the wall centered above the console.",
    ]
    return m, facts


BUILDERS.update({"kitchen_gola": kitchen_gola, "wardrobe_flush": wardrobe_flush,
                 "hallway_set": hallway_set, "tv_unit": tv_unit})


# остальные модели каталога регистрируются в BUILDERS при импорте
import builders_more  # noqa: E402,F401
