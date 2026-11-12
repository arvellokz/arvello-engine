"""Кухни R01E: библиотека модулей и компоновки 6 кухонь (ARV-KIT-001 … 006) на общем ядре eng/cab.py.

Вид — как в каталоге (builders.py: kitchen_gola, builders_more.py: kitchen_std / island / loft); конструкция модулей —
правила «Самал» R02E (корпус ЛДСП 16 на Minifix + шканты, ХДФ 4 накладная, ящики Blum 560H). Модуль — отдельный рабочий
комплект; кухня — сборочный комплект: план, развёртки, перечень модулей, столешница, цоколь, детали уровня кухни.
Петли, навесы, опоры, профили Gola, техника и столешницы — кандидаты (вопросы В-20, В-21, В-35 … В-42).
"""
from __future__ import annotations

from .cab import FASTENERS, GAP, T, TB, TF, Build, EPart
from .models13 import REV, _check, _inner

FASTENERS.update({
    "GOLA-SCREW": ("Саморез крепления профиля Gola", "4 × 16, по системе профиля (кандидат)", "кандидат", "В-35", "шт"),
    "CLIP-SCREW": ("Саморез клипсы цоколя", "3,5 × 16, в комплекте клипсы (кандидат)", "кандидат", "В-37", "шт"),
})

STATUS = ("инженерное предложение R01E: модуль кухни; корпус по правилам «Самал» R02E, ящики Blum 560H и Minifix — по "
          "документам; петли, навесы, опоры, профили Gola и техника — кандидаты; не для изготовления")

DB, DW = 578, 318            # глубина низа / верха: фасад 18 + корпус + ХДФ 4
HB = 720                     # высота корпуса низа
LEG = {"KM": 100, "KG": 120}
WALL_H = {"KM": 720, "KG": 920}
HOB_BODY = 60                # кандидат: корпус варочной панели под верхом столешницы (В-36)
WT = {"KM": 28, "KG": 38}    # столешница: ЛДСП-постформинг 28 / кварц 38


def _legs(b, c, W, leg, yc0, yc1):
    xs = [70, W - 70] if W <= 600 else [70, W / 2, W - 70]
    pts = [(x, yc0 + 90) for x in xs] + [(x, yc1 - 90) for x in xs]
    b.feet("", c, leg, pts, "LEGK", 50, name=f"Опора кухонная регулируемая {leg}",
           spec=f"пластик, h {leg} (регулировка ±15), площадка 50, под клипсу цоколя (кандидат)", status="кандидат",
           note="В-37")


def _rail_screws(b, rail, W):
    for x in (W / 4, 3 * W / 4):
        b.hole(rail.id, "J-WT", "screw_face", x, (rail.y0 + rail.y1) / 2, rail.z0, "+z", 4.5, T, "SCREW-4x30", through=True,
               cs=True, note="саморез в столешницу снизу; засверловка столешницы Ø3 гл. 15 по месту")


def _gola(b, pid, name, W, yc0, z0, z1, art):
    b.part(pid, name, T, yc0, z0, W - T, yc0 + 27, z1, "GOLA", "black", "fronts", kind="buy")
    for S, xf, dr in ((b.get("SIDE-L"), T, "-x"), (b.get("SIDE-R"), W - T, "+x")):
        for y in (yc0 + 8, yc0 + 20):
            b.hole(S.id, f"J-{pid}", "gola", xf, y, (z0 + z1) / 2, dr, 3, 10, "GOLA-SCREW",
                   note="засверловка по торцевой пластине профиля")
    b.buy(pid, name, f"{art}, L = {W - 2 * T}, алюминий чёрный, крепление между боковинами (кандидат)", 1, "кандидат", "В-35")
    b.derived["modules"].add("gola")


# ============================================================================== нижние модули
def base(code, name, W, kind, line, color):
    """kind: D — дверь(и), Y — 3 ящика, Y2 — 2 ящика (остров), S — под мойку, C — угловой слепой."""
    gola = line == "KG"
    leg = LEG[line]
    b = Build(code, REV, STATUS, {"color": color})
    z0, z1 = leg, leg + HB
    yc0, yc1 = TF, DB - TB
    shelves = [(T, W - T, z0 + 344, "Полка", "+")] if kind in ("D", "C") else []
    c = b.carcass("", 0, W, z0, z1, yc0, yc1, color, shelves=shelves, back=(kind != "S"), top=False, label="корпус")
    rf = None
    if not gola:
        rf = b.part("RAIL-F", "Царга передняя", T, yc0, z1 - T, W - T, yc0 + 100, z1, "LDSP16", color, "carcass",
                    edges={"-y": "ABS2"})
        for S, n in ((c["L"], "+x"), (c["R"], "-x")):
            b.conf(S, rf, n, "y", [rf.y0 + 25, rf.y1 - 25], f"J-{S.id[-1]}-RAILF")
        _rail_screws(b, rf, W)
    if kind == "S":
        rb = b.part("RAIL-B", "Царга задняя", T, yc1 - T, z1 - 100, W - T, yc1, z1, "LDSP16", color, "carcass")
        rl = b.part("RAIL-BL", "Царга задняя нижняя", T, yc1 - T, z0 + T, W - T, yc1, z0 + T + 100, "LDSP16", color, "carcass")
        for S, n in ((c["L"], "+x"), (c["R"], "-x")):
            for r, tag in ((rb, "RAILB"), (rl, "RAILBL")):
                b.conf(S, r, n, "z", [r.z0 + 25, r.z1 - 25], f"J-{S.id[-1]}-{tag}")
        b.notes.append("Под мойку: без ХДФ; задние царги вертикальные (верхняя и нижняя), между ними — проход труб; дно "
                       "защитить поддоном (кандидат, В-38).")
    else:
        rb = b.part("RAIL-B", "Царга задняя", T, yc1 - 100, z1 - T, W - T, yc1, z1, "LDSP16", color, "carcass")
        for S, n in ((c["L"], "+x"), (c["R"], "-x")):
            b.conf(S, rb, n, "y", [rb.y0 + 25, rb.y1 - 25], f"J-{S.id[-1]}-RAILB")
        k = max(1, round((W - 56) / 150))
        for i in range(k + 1):
            b.hole(rb.id, "J-BACK", "back_pilot", 28 + (W - 56) * i / k, yc1, z1 - T / 2, "-y", 2.5, 12, "SCREW-3.5x16")
        if not gola:
            _rail_screws(b, rb, W)
    _legs(b, c, W, leg, yc0, yc1)
    zt = z1 - 30 if gola else z1          # Gola: верх фасадов под каналом 30
    if gola:
        _gola(b, "GOLA-L", "Профиль Gola L верхний", W, yc0, z1 - 58, z1, "кандидат: профиль L горизонтальный")
    handle = None if gola else "bar128"
    if kind == "D":
        b.doors("", c, [c["L"]], [(GAP / 2, W - GAP / 2, z0 + GAP / 2, zt - GAP / 2)], color, handle=handle)
    elif kind == "S":
        h = W / 2
        b.doors("", c, [c["L"], c["R"]], [(GAP / 2, h - GAP / 2, z0 + GAP / 2, zt - GAP / 2),
                                          (h + GAP / 2, W - GAP / 2, z0 + GAP / 2, zt - GAP / 2)], color, handle=handle)
    elif kind == "C":
        xb = 650
        b.doors("", c, [c["R"]], [(xb + GAP / 2, W - GAP / 2, z0 + GAP / 2, zt - GAP / 2)], color, handle=handle)
        bl = b.part("BLIND", "Фальш-панель", GAP / 2, 0, z0 + GAP / 2, xb - GAP / 2, TF, zt - GAP / 2, "LDSP18", color, "fronts",
                    unit="Фальш-панель", edges={"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
        pts = []
        for x in (150, 500):
            pts.append(((x, yc0 + 12, c["BOT"].z1, "-z"), (x, TF, c["BOT"].z1 + 12, "-y")))
            pts.append(((x, yc0 + 12, rf.z0, "+z"), (x, TF, rf.z0 - 12, "-y")))
        b.bracket(c["BOT"], bl, "-z", pts[0::2], "J-BLIND-BOT")
        b.bracket(rf, bl, "+z", pts[1::2], "J-BLIND-RAIL")
        b.notes.append("Угловой слепой: фальш-панель 650 закрывает зону примыкания бокового ряда (600 + зазор 50 под ручки); "
                       "дверь 350 (в каталоге 400 — изменено, чтобы дверь не задевала ручки бокового ряда).")
    elif kind == "Y":
        fr = []
        z = z0
        hs = [284, 260, 176] if not gola else None
        if gola:
            fr = [(GAP / 2, W - GAP / 2, z0 + GAP / 2, z0 + 225 - GAP / 2), (GAP / 2, W - GAP / 2, z0 + 225 + GAP / 2, z0 + 450 - GAP / 2),
                  (GAP / 2, W - GAP / 2, z0 + 480 + GAP / 2, zt - GAP / 2)]
            _gola(b, "GOLA-C", "Профиль Gola C средний", W, yc0, z0 + 450, z0 + 480, "кандидат: профиль C горизонтальный")
            caps = [None, z0 + 445, z1 - 63]
            ceil = z1 - 58
        else:
            for h in hs:
                fr.append((GAP / 2, W - GAP / 2, z + GAP / 2, z + h - GAP / 2)); z += h
            caps = [None, None, z1 + WT["KM"] - HOB_BODY - 10]
            ceil = rf.z0
        b.drawers("", c, c["L"], c["R"], c["BOT"].z1, ceil, fr, color, _inner(color), handle=handle, caps=caps)
        b.notes.append(f"Верхний ящик — под варочной панелью: короб ниже корпуса панели (кандидат {HOB_BODY} под верхом "
                       "столешницы) на ≥ 10 (В-36).")
    elif kind == "Y2":
        fr = [(GAP / 2, W - GAP / 2, z0 + GAP / 2, z0 + 450 - GAP / 2), (GAP / 2, W - GAP / 2, z0 + 480 + GAP / 2, zt - GAP / 2)]
        _gola(b, "GOLA-C", "Профиль Gola C средний", W, yc0, z0 + 450, z0 + 480, "кандидат: профиль C горизонтальный")
        b.drawers("", c, c["L"], c["R"], c["BOT"].z1, z1 - 58, fr, color, _inner(color), handle=None,
                  caps=[z0 + 450 - 5, z1 - 58 - 5])
    b.derived.update(width=W, depth=DB, height=z1, plinth=leg)
    b.derived["modules"].add("kitchen")
    _check(b, "Ширина = 2 боковины + дно", W, 2 * T + (c["BOT"].x1 - c["BOT"].x0))
    _check(b, "Высота корпуса", HB, c["L"].z1 - c["L"].z0)
    _check(b, "Глубина = фасад + корпус + ХДФ", DB, TF + (c["L"].y1 - c["L"].y0) + TB)
    if gola and b.derived["drawers"]:
        profs = [z0 + 450, z1 - 58] if kind in ("Y", "Y2") else [z1 - 58]
        for r in b.derived["drawers"]:
            fbot = b.get(r["front"]).z0
            lim = min(pz for pz in profs if pz > fbot) - 5
            _check(b, f"Ящик {r['n']}: короб ниже профиля Gola на ≥ 5", True, r["z0"] + r["h"] <= lim)
    kq = ["В-37", "В-41"] + (["В-35"] if gola else []) + (["В-36"] if kind == "Y" else []) + (["В-38"] if kind == "S" else [])
    b.derived["kq"] = kq
    if kind == "C":
        b.derived["kdec"] = ["Угловой нижний: дверь 350 + фальш-панель 650 (в каталоге 400 + 600) — дверь не задевает ручки "
                             "бокового ряда."]
    b.notes += [f"Корпус ЛДСП 16, без крышки: царги {'задняя' if gola else 'передняя и задняя'} 100; столешница "
                f"{'кварц 38 — на силикон по боковинам и царге' if gola else 'ЛДСП 28 — саморезами 4 × 30 снизу через царги'}.",
                "Межсекционные стяжки Ø5 (4 на стык) — сверлить по месту при монтаже (лист кухни)."]
    return b


# ============================================================================== верхние модули
def wall(code, name, W, line, color, corner=False):
    gola = line == "KG"
    H = WALL_H[line]
    b = Build(code, REV, STATUS, {"color": color})
    yc0, yc1 = TF, DW - TB
    if H > 800:
        sh = [(T, W - T, 300, "Полка", "+"), (T, W - T, 600, "Полка", "+")]
    else:
        sh = [(T, W - T, 352, "Полка", "+")]
    parts = [(344, T, "Стойка")] if corner else []
    if corner:
        sh = [(360, W - T, z, nm, hd) for (_, _, z, nm, hd) in sh]
    c = b.carcass("", 0, W, 0, H, yc0, yc1, color, partitions=parts, shelves=sh, vis_bottom=True, label="корпус")
    b.hangers("", c, "навес скрытый регулируемый под ХДФ 4, кандидат Camar 807 / аналог", note="В-21")
    zb = -20 if gola else 0                # Gola: фасад ниже корпуса на 20 — захват
    handle = None if gola else "bar128"
    x0 = 360 if corner else 0
    n = 1 if (W - x0) <= 600 else 2
    fw = (W - x0) / n
    fronts = [(x0 + i * fw + GAP / 2, x0 + (i + 1) * fw - GAP / 2, zb + GAP / 2, H - GAP / 2) for i in range(n)]
    if n == 2:
        sides, lefts = [c["parts"][0] if corner else c["L"], c["R"]], [True, False]
    else:
        sides, lefts = [c["L"]], [True]
    hz = (fronts[0][3] - fronts[0][2]) - 50
    b.doors("", c, sides, fronts, color, handle=handle, hz_from_top=hz, lefts=lefts)
    if corner:
        bl = b.part("BLIND", "Фальш-панель", GAP / 2, 0, zb + GAP / 2, 360 - GAP / 2, TF, H - GAP / 2, "LDSP18", color, "fronts",
                    unit="Фальш-панель", edges={"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
        pa = [((x, yc0 + 12, c["BOT"].z1, "-z"), (x, TF, c["BOT"].z1 + 12, "-y")) for x in (100, 260)]
        pb = [((x, yc0 + 12, c["TOP"].z0, "+z"), (x, TF, c["TOP"].z0 - 12, "-y")) for x in (100, 260)]
        b.bracket(c["BOT"], bl, "-z", pa, "J-BLIND-BOT")
        b.bracket(c["TOP"], bl, "+z", pb, "J-BLIND-TOP")
        b.notes.append("Угловой слепой верхний: фальш-панель 360 — зона примыкания бокового ряда (318 + 26 под ручки + 16); "
                       "дверь(и) за стойкой.")
    b.derived.update(width=W, depth=DW, height=H, plinth=0)
    b.derived["modules"] |= {"kitchen", "wall"}
    b.derived["kq"] = ["В-41"]
    if corner:
        b.derived["kdec"] = ["Верхний угловой 1000 — слепой: фальш-панель 360 и 2 двери 320 (в каталоге 2 двери по 500); "
                             "боковой верхний ряд примыкает к фальш-панели."]
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота корпуса", H, c["L"].z1 - c["L"].z0)
    _check(b, "Глубина = фасад + корпус + ХДФ", DW, TF + (c["L"].y1 - c["L"].y0) + TB)
    b.notes.append("Верхний модуль: навесы в верхних задних углах, шина к стене — по типу стены (В-21); низ виден — "
                   "кромка ABS по нижним торцам боковин." + (" Фасад ниже корпуса на 20 — захват вместо ручки." if gola else ""))
    return b


# ============================================================================== колонны (Gola)
def column(code, name, kind, color):
    leg, W, z1 = LEG["KG"], 600, 2380
    z0 = leg
    b = Build(code, REV, STATUS, {"color": color})
    yc0, yc1 = TF, DB - TB
    if kind == "F":
        niche_top = z0 + T + 1780
        sh = [(T, W - T, niche_top, "Полка над нишей холодильника", "+"), (T, W - T, 2150, "Полка", "+")]
        split = niche_top + T
        fronts = [(GAP / 2, W - GAP / 2, z0 + GAP / 2, split - GAP / 2), (GAP / 2, W - GAP / 2, split + GAP / 2, z1 - GAP / 2)]
        b.notes += ["Ниша холодильника 1780 × 568 × 550 (кандидат: встраиваемый однокамерный / с морозильником внутри, "
                    "фасад на двери холодильника — по его инструкции, В-38). Линия фасадов 1932 (в каталоге 1440 — "
                    "изменено под нишу 1780).",
                    "Вентиляция холодильника: вырез в ХДФ и решётка в цоколе — по инструкции холодильника (В-38)."]
    else:
        sh = [(T, W - T, z0 + 330, "Полка", "+"), (T, W - T, 824, "Полка под духовой шкаф", "+"),
              (T, W - T, 1437, "Полка под СВЧ", "+"), (T, W - T, 1833, "Полка над СВЧ", "+")]
        fronts = [(GAP / 2, W - GAP / 2, z0 + GAP / 2, 840 - GAP / 2), (GAP / 2, W - GAP / 2, 1849 + GAP / 2, z1 - GAP / 2)]
        b.notes += ["Ниши: духовой шкаф 597 × 568 (полка 824 — 840, кандидат 595 × 560 × 550), СВЧ 380 × 568 (1453 — 1833, "
                    "кандидат встраиваемая 38 см). Вентиляция — вырез ХДФ за нишами, по инструкции техники (В-38).",
                    "Полка под духовой шкаф — нагрузка ≈ 35 кг: проверить на образце (В-12)."]
    c = b.carcass("", 0, W, z0, z1, yc0, yc1, color, shelves=sh, label="колонна")
    _legs(b, c, W, leg, yc0, yc1)
    b.doors("", c, [c["L"]] * len(fronts), fronts, color, handle=None)
    b.buy("PUSH-LATCH", "Толкатель для двери без ручки", "кандидат Blum TIP-ON 956A1004 (или вертикальный профиль Gola)",
          len(fronts), "кандидат", "В-35")
    b.derived.update(width=W, depth=DB, height=z1, plinth=leg)
    b.derived["modules"] |= {"kitchen", "column"}
    b.derived["kq"] = ["В-35", "В-37", "В-38", "В-41"]
    if kind == "F":
        b.derived["kdec"] = ["Колонна холодильника: линия фасадов 1932 под нишу 1780 (в каталоге 1440)."]
    _check(b, "Высота колонны = опоры + корпус", z1, leg + (c["L"].z1 - c["L"].z0))
    _check(b, "Глубина = фасад + корпус + ХДФ", DB, TF + (c["L"].y1 - c["L"].y0) + TB)
    b.warnings.append("Колонна 2260 × 600: крепление к стене уголками в верхней части (2 шт., В-41) — от опрокидывания.")
    b.buy("WALL-ANGLE", "Уголок крепления колонны к стене", "сталь, 2 самореза в крышку + дюбель в стену (кандидат)", 2,
          "кандидат", "В-41")
    return b


# ============================================================================== полки «Лофт»
def loft_frame(code, name, Lf, metal="black"):
    b = Build(code, REV, STATUS, {"length": Lf, "metal": metal})
    prof, H, Dp = "TUBE20x20x2", 750, 278
    xs = [0] + [x for x in range(900, Lf - 100, 900)] + [Lf - 20]
    posts, arms, plates = [], [], []
    top = b.tube("TOPBAR", "Перекладина верхняя", 0, 0, H - 20, Lf, 20, H, prof, metal, "x")
    shelves = []
    for k, zs in enumerate((100, 450), 1):
        shelves.append(b.part(f"SHELF-{k}", "Полка", 0, 20, zs, Lf, Dp - 4, zs + 28, "TOP28", "O", "shelves", unit="Полка",
                              edges={"-y": "ABS2", "+y": "PVC04", "-x": "ABS2", "+x": "ABS2"}))
    for i, x in enumerate(xs):
        p = b.tube(f"POST-{i + 1}", "Стойка", x, 0, 0, x + 20, 20, H - 20, prof, metal, "z")
        b.weld(p, top)
        posts.append(p)
        for k, zs in enumerate((100, 450), 1):
            a = b.tube(f"ARM-{i + 1}-{k}", "Консоль", x, 20, zs - 20, x + 20, Dp - 4, zs, prof, metal, "y")
            b.weld(a, p)
            pl = b.plate(f"WP-{i + 1}-{k}", "Пластина к стене", x - 20, Dp - 4, zs - 50, x + 40, Dp, zs + 10, metal)
            b.weld(pl, a)
            for xh in (x - 10, x + 30):
                b.hole(pl.id, f"J-WALL{i + 1}{k}", "wall_bolt", xh, Dp - 4, zs - 40, "+y", 9, 4, "ANCHOR-M8", through=True,
                       note="анкер по типу стены (В-21)")
            arms.append((a, k))
    for k, S in enumerate(shelves, 1):
        b.top_fix(S, [a for a, kk in arms if kk == k], [70, Dp - 60], "y", f"J-SHELF{k}", insert=False)
    b.derived["frames"].append({"name": "Рама полок", "tubes": [t.id for t in b.P if t.kind == "tube"]})
    b.derived.update(width=Lf, depth=Dp, height=H, plinth=0)
    b.derived["modules"] |= {"kitchen", "loft"}
    b.derived["kq"] = ["В-41", "В-42"]
    b.derived["kdec"] = ["Полки 28 × 254 за стойками (в каталоге 30 × 278 с заходом на стойки)."]
    b.notes += ["Полки — плита-столешница 28 «Дуб» (в каталоге 30), глубина 254 за стойками (в каталоге 278 — стойки "
                "входили в полку); кромка ABS по лицевым торцам.",
                "Рама сварная, труба 20 × 20 × 2, порошковая окраска; каждая консоль — пластиной 60 × 60 × 4 к стене на 2 анкера."]
    b.warnings.append("Консоль 20 × 20 вылетом 254 под полкой с посудой: нагрузка на полку и анкеры — испытать на образце "
                      "(В-42, В-12).")
    return b


# ============================================================================== реестр модулей
def _B(code, nm, W, kind, line, col):
    return (nm, lambda o, a=(code, nm, W, kind, line): base(*a, o["color"]), {"color": col})


def _W(code, nm, W, line, col, corner=False):
    return (nm, lambda o, a=(code, nm, W, line): wall(*a, o["color"], corner=corner), {"color": col})


MODULES = {
    "KM-B600Y": _B("KM-B600Y", "Нижний 600, 3 ящика", 600, "Y", "KM", "W"),
    "KM-B600D": _B("KM-B600D", "Нижний 600, дверь", 600, "D", "KM", "W"),
    "KM-B400D": _B("KM-B400D", "Нижний 400, дверь", 400, "D", "KM", "W"),
    "KM-B800S": _B("KM-B800S", "Нижний 800 под мойку", 800, "S", "KM", "W"),
    "KM-B1000C": _B("KM-B1000C", "Нижний угловой", 1000, "C", "KM", "W"),
    "KM-W600": _W("KM-W600", "Верхний 600", 600, "KM", "W"),
    "KM-W400": _W("KM-W400", "Верхний 400", 400, "KM", "W"),
    "KM-W800": _W("KM-W800", "Верхний 800", 800, "KM", "W"),
    "KM-W1000C": _W("KM-W1000C", "Верхний угловой", 1000, "KM", "W", corner=True),
    "KG-B600Y": _B("KG-B600Y", "Нижний Gola 600, 3 ящика", 600, "Y", "KG", "G"),
    "KG-B600Y2": _B("KG-B600Y2", "Нижний Gola 600, 2 ящика", 600, "Y2", "KG", "G"),
    "KG-B600D": _B("KG-B600D", "Нижний Gola 600, дверь", 600, "D", "KG", "G"),
    "KG-B400D": _B("KG-B400D", "Нижний Gola 400, дверь", 400, "D", "KG", "G"),
    "KG-B800S": _B("KG-B800S", "Нижний Gola 800 под мойку", 800, "S", "KG", "G"),
    "KG-W600": _W("KG-W600", "Верхний Gola 600", 600, "KG", "W"),
    "KG-W400": _W("KG-W400", "Верхний Gola 400", 400, "KG", "W"),
    "KG-W800": _W("KG-W800", "Верхний Gola 800", 800, "KG", "W"),
    "KG-T600F": ("Колонна 600 под холодильник", lambda o: column("KG-T600F", "Колонна 600 под холодильник", "F", o["color"]),
                 {"color": "W"}),
    "KG-T600O": ("Колонна 600 под духовой шкаф и СВЧ",
                 lambda o: column("KG-T600O", "Колонна 600 под духовой шкаф и СВЧ", "O", o["color"]), {"color": "W"}),
    "KL-SH": ("Полки на сварной раме", lambda o: loft_frame("KL-SH", "Полки на сварной раме", int(o["length"]), o["metal"]),
              {"length": 2360, "metal": "black"}),
}


# ============================================================================== компоновки кухонь
def _std_mods(L):
    rem = L - 1400
    mods = [("Y", 600)]
    sink = 800
    while rem >= 600:
        mods.append(("D", 600)); rem -= 600
    if rem >= 300:
        mods.append(("D", rem))
    else:
        sink += rem
    return mods + [("S", sink)]


def _place(b, code, opts, X, Y, Z, rot, tag):
    """Модуль из библиотеки — в кухню как детали вида «module» (в изделии кухни не деталируются)."""
    sub = MODULES[code][1](opts)
    W = sub.derived["width"]
    b.derived["mass_modules"] = round(b.derived.get("mass_modules", 0) + sub.design().derived["mass_kg"], 1)
    for p in sub.P:
        def f(x, y, z):
            if rot == 0:
                return X + x, Y + y, Z + z
            if rot == 90:                     # фасад смотрит в +X, левая боковина — в −Y
                return X - y, Y + x, Z + z
            if rot == 180:                    # фасад смотрит в +Y
                return X + W - x, Y - y, Z + z
            raise ValueError(rot)
        a, c_ = f(p.x0, p.y0, p.z0), f(p.x1, p.y1, p.z1)
        q = EPart(f"{tag}.{p.id}", p.name, "module" if p.kind in ("board", "tube", "plate") else "context",
                  round(min(a[0], c_[0]), 2), round(min(a[1], c_[1]), 2), round(min(a[2], c_[2]), 2),
                  round(max(a[0], c_[0]), 2), round(max(a[1], c_[1]), 2), round(max(a[2], c_[2]), 2),
                  p.material, p.finish, p.group, unit=p.unit, note=code)
        q.edges, q.grain, q.pos = {}, "", None
        b.P.append(q)
    rec = {"tag": tag, "code": code, "name": MODULES[code][0], "x": X, "y": Y, "z": Z, "rot": rot, "w": W,
           "d": sub.derived["depth"], "h": sub.derived["height"], "opts": dict(opts),
           "front_legs": len([p for p in sub.P if p.material == "LEGK"]) // 2}
    b.derived.setdefault("kitchen", {"modules": []})["modules"].append(rec)
    return rec


def _ctx(b, pid, name, x0, y0, z0, x1, y1, z1, fin="black", group="appliances"):
    b.part(pid, name, x0, y0, z0, x1, y1, z1, "APPL", fin, group, kind="context")


def _plinth(b, pid, x0, x1, y, h, color, axis="x", legs=(), flip=False):
    """Цоколь ЛДСП 16 на клипсах к опорам; длиннее 2750 — два куска со стыком на модуле."""
    pieces = [(x0, x1)]
    if x1 - x0 > 2750:
        m = x0 + round((x1 - x0) / 2 / 100) * 100
        pieces = [(x0, m), (m, x1)]
    out = []
    for k, (a, c_) in enumerate(pieces, 1):
        nm = f"{pid}{k if len(pieces) > 1 else ''}"
        if axis == "x":
            p = b.part(nm, "Цоколь", a, y, 0, c_, y + T, h - 3, "LDSP16", color, "base", unit="Цоколь",
                       edges={"+z": "ABS2", "-z": "PVC04", "-x": "ABS2", "+x": "ABS2"})
        else:
            p = b.part(nm, "Цоколь", y - T, a, 0, y, c_, h - 3, "LDSP16", color, "base", unit="Цоколь",
                       edges={"+z": "ABS2", "-z": "PVC04", "-y": "ABS2", "+y": "ABS2"})
        out.append(p)
        for L_ in legs:
            if a + 30 <= L_ <= c_ - 30:
                if axis == "x":
                    b.hole(p.id, f"J-{nm}-CLIP", "pilot", L_, p.y0 if flip else p.y1, h / 2, "+y" if flip else "-y", 3, 10,
                           "CLIP-SCREW",
                           note="клипса цоколя к опоре; засверловка по месту опоры")
                else:
                    b.hole(p.id, f"J-{nm}-CLIP", "pilot", p.x0, L_, h / 2, "+x", 3, 10, "CLIP-SCREW",
                           note="клипса цоколя к опоре; засверловка по месту опоры")
    return out


END_IN = 20                                            # отступ торцевого цоколя от боковины


def _end_plinths(b, ends, h, color):
    """Торцевые цоколи на открытых концах ряда (01.11): закрывают опоры сбоку. Крепление — угловой соединитель
    к лицевому цоколю + клипса к ближней опоре по месту (В-37). ends: (pid, ось, a0, a1, положение)."""
    out = []
    for pid, axis, a0, a1, pos in ends:
        out += _plinth(b, pid, a0, a1, pos, h, color, axis=axis)
    b.buy("PL-CORNER", "Соединитель цоколя угловой 90°", "пластик, под цоколь 16 (кандидат)", len(out), "кандидат", "В-37")
    return out


def _worktop(b, pid, x0, y0, x1, y1, z0, line, cutouts, name="Столешница"):
    mat, t = ("TOP28", 28) if line == "KM" else ("STONE38", 38)
    fin = "WT" if line == "KM" else "QZ"
    e = {"-x": "ABS2", "+x": "ABS2"} if line == "KM" else {}
    p = b.part(pid, name, x0, y0, z0, x1, y1, z0 + t, mat, fin, "top", unit=name, edges=e)
    for (cx, cy, w, d, note) in cutouts:
        b.derived.setdefault("cutouts", []).append({"part": pid, "x0": cx - w / 2, "y0": cy - d / 2, "x1": cx + w / 2,
                                                   "y1": cy + d / 2, "note": note, "draw": True})
    return p


def _run(b, mods, line, colors, X, Y, rot, tag, uppers=True, hob=True, sink=True, upper_shift=0):
    """Ряд нижних (и верхних) модулей по оси ряда. rot 0 — вдоль +X у стены y = Y + DB; rot 90 — вдоль +Y у стены x = X."""
    base_c, top_c = colors
    out, s = [], 0
    leg = LEG[line]
    for k, (kind, w) in enumerate(mods):
        code = {"Y": f"{line}-B600Y", "D": f"{line}-B{w}D", "S": f"{line}-B{w}S", "C": f"{line}-B{w}C",
                "Y2": f"{line}-B600Y2"}[kind]
        if rot == 0:
            r = _place(b, code, {"color": base_c}, X + s, Y, 0, 0, f"{tag}B{k + 1}")
        else:
            r = _place(b, code, {"color": base_c}, X + DB, Y + s, 0, 90, f"{tag}B{k + 1}")
        r["kind"] = kind
        out.append(r)
        s += w
    ups = []
    if uppers:
        s = 0
        z = 1450 if line == "KM" else 1460
        for k, (kind, w) in enumerate(mods if uppers is True else uppers):
            code = f"{line}-W{w}" + ("C" if kind == "C" else "")
            if rot == 0:
                r = _place(b, code, {"color": top_c}, X + s, Y + DB - DW, z, 0, f"{tag}U{k + 1}")
            else:
                r = _place(b, code, {"color": top_c}, X + DW, Y + s + upper_shift, z, 90, f"{tag}U{k + 1}")
            ups.append(r)
            s += w
    return out, ups


def _appliances(b, mods, line, X, Y, wt_top, hob=True, sink=True):
    s = 0
    cut = []
    for r in mods:
        w = r["w"]
        if r["kind"] in ("Y",) and hob:
            _ctx(b, f"HOB{len(cut)}", "Варочная панель (кандидат)", X + s + 5, Y + 40 - 22 + 22, wt_top, X + s + w - 5, Y + 560,
                 wt_top + 6)
            cut.append((X + s + w / 2, Y + 278, 560, 490, "варочная панель — кандидат 590 × 520, вырез 560 × 490 (В-36)"))
            hob = False
        if r["kind"] == "S" and sink:
            xc = X + s + w / 2
            _ctx(b, "SINK", "Мойка (кандидат)", xc - 250, Y + 70, wt_top - 3, xc + 250, Y + 500, wt_top + 1, "steel")
            _ctx(b, "FAUCET", "Смеситель (кандидат)", xc - 15, Y + 520, wt_top, xc + 15, Y + 550, wt_top + 300, "steel")
            _ctx(b, "SPOUT", "Излив", xc - 12, Y + 390, wt_top + 270, xc + 12, Y + 550, wt_top + 300, "steel")
            cut.append((xc, Y + 285, 480, 410, ("мойка врезная 500 × 430 — кандидат, вырез ≈ 480 × 410 по шаблону мойки (В-38)"
                                                 if line == "KM" else "мойка подстольного монтажа 500 × 400 — кандидат, "
                                                 "вырез по шаблону (В-38)")))
            sink = False
        s += w
    return cut


def kitchen(sku, name, o):
    layout = o.get("layout", "straight")
    b = Build(sku, REV, STATUS, dict(o))
    kq = ["В-36", "В-37", "В-38", "В-39", "В-41"]
    if sku in ("ARV-KIT-001", "ARV-KIT-002", "ARV-KIT-003", "ARV-KIT-006"):
        line = "KM"
        base_c = o["base"]
        top_c = o.get("top", base_c)
        wt0 = LEG["KM"] + HB
        if layout == "corner":
            main = [("C", 1000), ("Y", 600), ("S", 800)]
            side = [("Y", 600), ("D", 400)]            # от дальнего конца к углу
            mm, mu = _run(b, main, line, (base_c, top_c), 0, 0, 0, "M")
            sm, su = _run(b, side, line, (base_c, top_c), 0, -1000, 90, "S", upper_shift=260)
            L = 2400
            cut = _appliances(b, mm, line, 0, 0, wt0 + 28)
            _worktop(b, "WT-1", 0, -22, L, DB, wt0, line, [c for c in cut])
            _worktop(b, "WT-2", 0, -1000, DB + 22, -22, wt0, line, [], name="Столешница боковая")
            legs_m = [r["x"] + x for r in mm for x in ([70, r["w"] / 2, r["w"] - 70] if r["w"] > 600 else [70, r["w"] - 70])]
            legs_s = [r["y"] + x for r in sm for x in ([70, r["w"] - 70])]
            _plinth(b, "PL-1", DB - 50 - T, L, 50, LEG[line], base_c, legs=legs_m)
            _plinth(b, "PL-2", -1000, 50, DB - 50, LEG[line], base_c, axis="y", legs=legs_s)
            _end_plinths(b, [("PL-E1", "x", END_IN, DB - 50 - T, -1000 + END_IN),
                             ("PL-E2", "y", 50 + T, DB - END_IN, L - END_IN)], LEG[line], base_c)
            b.warnings.append("Угол: боковой ряд примыкает к фальш-панели углового модуля; угловой стык столешниц — "
                              "алюминиевая планка или евростык (В-39); цоколи в углу — на угловом соединителе.")
            b.derived["kdec"] = ["Угловой нижний: дверь 350 + фальш-панель 650 (каталог: 400 + 600).",
                                 "Верхний боковой ряд сдвинут к углу на 260 (в каталоге — зазор 260 у угла); верхний угловой "
                                 "1000 — слепой с фальш-панелью 360."]
            W_, D_ = L, 1000 + DB
        else:
            L = int(o["length"])
            mods = _std_mods(L)
            mm, mu = _run(b, mods, line, (base_c, top_c), 0, 0, 0, "M", uppers=(sku != "ARV-KIT-006"))
            cut = _appliances(b, mm, line, 0, 0, wt0 + 28)
            _worktop(b, "WT-1", 0, -22, L, DB, wt0, line, cut)
            legs_m = [r["x"] + x for r in mm for x in ([70, r["w"] / 2, r["w"] - 70] if r["w"] > 600 else [70, r["w"] - 70])]
            _plinth(b, "PL-1", 0, L, 50, LEG[line], base_c, legs=legs_m)
            _end_plinths(b, [("PL-E1", "y", 50 + T, DB - END_IN, END_IN + T),
                             ("PL-E2", "y", 50 + T, DB - END_IN, L - END_IN)], LEG[line], base_c)
            W_, D_ = L, DB + 22
            if sku == "ARV-KIT-006":
                Lf = L - 640
                _place(b, "KL-SH", {"length": Lf, "metal": "black"}, 640, DB - 278, 1450, 0, "SH")
                _ctx(b, "HOOD", "Вытяжка купольная 500 (кандидат)", 50, DB - 300, 1500, 550, DB, 1580)
                _ctx(b, "HOOD-C", "Короб вытяжки", 180, DB - 178, 1580, 420, DB, 2300)
                kq.append("В-42")
        b.derived.update(width=W_, depth=D_, height=2170 if sku != "ARV-KIT-006" else 2200, plinth=LEG[line])
    else:
        line = "KG"
        base_c, top_c = o["base"], o["top"]
        L = int(o["length"])
        n_cols = 1 if L < 3000 else 2
        bx0 = 600 * n_cols
        rem = L - bx0 - 1400
        mods = [("Y", 600)]
        sink_w = 800
        while rem >= 600:
            mods.append(("D", 600)); rem -= 600
        if rem >= 300:
            mods.append(("D", rem))
        else:
            sink_w += rem
        mods.append(("S", sink_w))
        cols = []
        for i in range(n_cols):
            cols.append(_place(b, "KG-T600F" if i == 0 else "KG-T600O", {"color": top_c}, i * 600, 0, 0, 0, f"C{i + 1}"))
        _ctx(b, "FRIDGE", "Холодильник встраиваемый (кандидат)", 20, 30, 140, 580, 560, 1910, "white")
        if n_cols == 2:
            _ctx(b, "OVEN", "Духовой шкаф (кандидат)", 604, 0, 843, 1196, 22, 1437)
            _ctx(b, "MICRO", "СВЧ встраиваемая (кандидат)", 604, 0, 1455, 1196, 22, 1831)
        mm, mu = _run(b, mods, line, (base_c, top_c), bx0, 0, 0, "M")
        wt0 = LEG["KG"] + HB
        cut = _appliances(b, mm, line, bx0, 0, wt0 + 38)
        _worktop(b, "WT-1", bx0, -22, L, DB, wt0, line, cut)
        legs_m = [r["x"] + x for r in cols + mm for x in ([70, r["w"] / 2, r["w"] - 70] if r["w"] > 600 else [70, r["w"] - 70])]
        _plinth(b, "PL-1", 0, L, 50, LEG[line], base_c, legs=legs_m)
        _end_plinths(b, [("PL-E1", "y", 50 + T, DB - END_IN, END_IN + T),
                         ("PL-E2", "y", 50 + T, DB - END_IN, L - END_IN)], LEG[line], base_c)
        kq.append("В-35")
        W_, D_, H_ = L, DB + 22, 2380
        b.derived["kdec"] = ["Колонна холодильника: линия фасадов 1932 под нишу 1780 (каталог: 1440)."]
        if sku == "ARV-KIT-005":
            isl = int(o["island"])
            a = (L - isl) / 2
            Yf = -1200
            im = []
            for k in range(isl // 600):
                code = "KG-B600Y2" if k % 2 == 0 else "KG-B600D"
                r = _place(b, code, {"color": base_c}, a + k * 600, Yf, 0, 180, f"I{k + 1}")
                r["kind"] = "Y2" if k % 2 == 0 else "D"
                im.append(r)
            yb = Yf - DB                                     # спина модулей острова
            b.derived["kdec"] = b.derived.get("kdec", []) + [
                "Остров: задняя сторона закрыта панелью ЛДСП 16 в декоре (в каталоге не показана); модули повёрнуты на 180°."]
            b.part("IS-BACK", "Панель задняя острова", a, yb - T, 0, a + isl, yb, wt0 - 2, "LDSP16", base_c, "carcass",
                   unit="Панель задняя острова", edges={"+z": "ABS2", "-z": "PVC04", "-x": "ABS2", "+x": "ABS2"})
            Y0, Y1 = -2100, Yf + 20
            ef = b.part("IS-END-F", "Панель торцевая рифлёная (наружный слой)", a - 40, Y0, 0, a - 18, Y1, wt0, "MDF22", "groove",
                        "carcass", unit="Панель торцевая рифлёная", edges={})
            eb = b.part("IS-END-B", "Панель торцевая (внутренний слой)", a - 18, Y0, 0, a, Y1, wt0, "LDSP18", base_c, "carcass",
                        unit="Панель торцевая, слой", edges={"-y": "ABS2", "+y": "ABS2", "+z": "ABS2"})
            b.screws_into(eb, ef, "-x", "y", [Y0 + 100, (Y0 + Y1) / 2, Y1 - 100], "SCREW-4x30", "J-END-LAYERS",
                          pilot=(3, 12), at=200)
            b.screws_into(eb, ef, "-x", "y", [Y0 + 100, (Y0 + Y1) / 2, Y1 - 100], "SCREW-4x30", "J-END-LAYERS2",
                          pilot=(3, 12), at=wt0 - 200)
            b.part("IS-WF", "Панель торцевая «водопад»", a + isl, Y0, 0, a + isl + 38, Y1, wt0, "STONE38", "QZ", "top",
                   unit="Торец «водопад»", edges={})
            _worktop(b, "IS-TOP", a - 40, Y0, a + isl + 38, Y1, wt0, line, [], name="Столешница острова")
            ilegs = [r["x"] + x for r in im for x in (70, 530)]
            _plinth(b, "PL-I", a, a + isl, Yf - 50 - T, LEG[line], base_c, legs=ilegs, flip=True)
            b.warnings.append("Свес столешницы острова 322 (барная зона) — кварц 38 на торцевых панелях; промежуточные "
                              "опоры свеса / кронштейны — по изготовителю камня (В-40).")
            kq.append("В-40")
            D_ = DB + 2100
        b.derived.update(width=W_, depth=D_, height=H_, plinth=LEG[line])
    b.derived["kq"] = kq
    b.derived["modules"] |= {"kitchen", "kitchen_set"}
    recs = b.derived["kitchen"]["modules"]
    bases = [r for r in recs if r["code"][3] in "BT"]
    walls = [r for r in recs if r["code"][3] == "W"]
    joints = max(0, len(bases) - 1) + max(0, len(walls) - 1)
    b.buy("TIE", "Стяжка межсекционная", "Ø5, пластик / металл, 4 на стык модулей (кандидат)", 4 * joints, "кандидат", "В-41")
    b.buy("CLIP", "Клипса цоколя", "к кухонной опоре, в комплекте саморезы (кандидат)",
          sum(1 for h in b.holes if h["fastener"] == "CLIP-SCREW"), "кандидат", "В-37")
    if walls:
        b.derived["modules"].add("hang")
        b.buy("WALL-RAIL", "Шина навесная (общая на ряд)", "длина по ряду верхних модулей; к стене по типу стены (кандидат)",
              sum(1 for _ in {round(r["rot"]) for r in walls}), "кандидат", "В-21")
    if line == "KM":
        b.buy("WT-END", "Планка торцевая столешницы 28", "алюминий, в цвет (кандидат)", 2, "кандидат", "В-39")
        b.buy("WT-PLINTH", "Плинтус столешницы", "алюминий / пластик, с заглушками, по длине у стен (кандидат)", 1, "кандидат",
              "В-39")
    if layout == "corner":
        b.buy("WT-JOINT", "Планка стыковочная угловая столешницы 28", "алюминий (или евростык на ЧПУ)", 1, "кандидат", "В-39")
    b.buy("SEALANT", "Герметик санитарный", "по мойке и примыканию к стене", 1, "типовой", "", "туба")
    b.buy("APPL", "Техника и мойка", "варочная панель, мойка, смеситель" + (", холодильник, духовой шкаф, СВЧ" if line == "KG" else "")
          + (", вытяжка" if sku == "ARV-KIT-006" else "") + " — по заказу клиента (ниши и вырезы — кандидаты)", 1, "клиент", "В-38",
          "компл")
    b.notes += ["Модули — по своим комплектам (перечень на листе 02); здесь — детали уровня кухни: столешница, цоколь"
                + (", панели острова" if sku == "ARV-KIT-005" else "") + ".",
                "Межсекционные стяжки Ø5 — 4 на стык, сверлить по месту при монтаже; верхние — на общую шину навесов."]
    # проверка: детали кухни не пересекают модули
    made = [p for p in b.P if p.kind in ("board", "tube", "plate")]
    mods_ = [p for p in b.P if p.kind == "module"]
    bad = 0
    for p in made:
        for q in mods_:
            if all(min(getattr(p, k + "1"), getattr(q, k + "1")) - max(getattr(p, k + "0"), getattr(q, k + "0")) > 0.5 for k in "xyz"):
                bad += 1
    _check(b, "Детали кухни не пересекают модули", 0, bad)
    mm_ = [p for p in mods_]
    ov = 0
    recs = b.derived["kitchen"]["modules"]
    for i, r1 in enumerate(recs):
        for r2 in recs[i + 1:]:
            A = [p for p in mm_ if p.id.startswith(r1["tag"] + ".")]
            B = [p for p in mm_ if p.id.startswith(r2["tag"] + ".")]
            for p in A:
                for q in B:
                    if all(min(getattr(p, k + "1"), getattr(q, k + "1")) - max(getattr(p, k + "0"), getattr(q, k + "0")) > 0.5
                           for k in "xyz"):
                        ov += 1
    _check(b, "Модули не пересекаются друг с другом", 0, ov)
    return b


KITCHENS = {
    "ARV-KIT-001": "Кухня «Алатау»", "ARV-KIT-002": "Кухня «Медеу»", "ARV-KIT-003": "Кухня «Тарлан»",
    "ARV-KIT-004": "Кухня «Монолит»", "ARV-KIT-005": "Кухня «Остров»", "ARV-KIT-006": "Кухня «Лофт»",
}

KQ = {
    "В-35": ("Профили Gola (L верхний, C средний) и открывание колонн: система и артикулы, крепление между боковинами или "
             "с вырезом в боковине, заглушки; толкатели / вертикальный профиль для колонн", "модули KG, узел П", "Arvello",
             "каталог профиля — довести до R02E"),
    "В-36": ("Варочная панель: модель, глубина корпуса под столешницей (принято 60), вырез (принято 560 × 490), зазор до "
             "верхнего ящика, подключение", "вырез столешницы, верхний ящик", "Arvello + клиент", "паспорт панели"),
    "В-37": ("Опоры кухонные регулируемые 100 / 120 и клипсы цоколя: артикул, диапазон регулировки, нагрузка на опору",
             "высота кухни, цоколь", "Arvello", "образцы, замер"),
    "В-38": ("Встраиваемая техника и мойка: холодильник (ниша 1780 × 568 × 550, навеска фасада, вентиляция), духовой шкаф "
             "(ниша 597 × 568), СВЧ (380), мойка (модель, вырез, поддон под мойку), подводка воды", "ниши колонн, вырезы",
             "Arvello + клиент", "паспорта техники"),
    "В-39": ("Столешница: ЛДСП-постформинг 28 (поставщик, декор, торцевые планки, плинтус, угловой стык) или кварц 38 "
             "(изготовитель, замер по месту, вырезы, подклейка, стыки); длины кусков", "поз. столешницы", "Arvello + поставщик",
             "КП поставщика, шаблон"),
    "В-40": ("Остров: свес кварца 322 — опоры свеса / кронштейны; стык «водопада» (ус 45°); крепление торцевых панелей "
             "к модулям", "столешница острова, торцы", "изготовитель камня + Arvello", "расчёт изготовителя"),
    "В-41": ("Монтаж: стены (тип, ровность), шина навесов, стяжки межсекционные, крепление колонн к стене, доборные планки "
             "к стенам, герметизация стыков столешницы", "монтаж", "монтажник + Arvello", "замер, техкарта монтажа"),
    "В-42": ("Полки «Лофт»: плита-столешница 28 «Дуб» или щит дуба 30; нагрузка консолей 20 × 20 и анкеров; покрытие рамы",
             "полки, рама", "Arvello + цех металла", "испытание образца"),
}
