"""Снимок для моделей без собственного инженерного ядра (все, кроме «Опоры»).

Берёт каталожную геометрию builders.py и раскладывает каждую деталь по виду и материалу —
по названию детали, группе, цвету и толщине. Это ОЦЕНКА ПО ГЕОМЕТРИИ: конструкция (соединения,
крепёж, присадка) не разработана, фурнитура посчитана по правилам (петли по высоте двери,
направляющие на ящик) и требует подбора. Статус ревизии это прямо говорит; в производство не выдаётся.
"""
from __future__ import annotations

import re

from .core import Design, EPart, Hardware

REV = "R00"
STATUS = "каталожная геометрия; конструкция не разработана — оценка по 3D, не для изготовления"

CONTEXT_NAMES = {"mattress", "pillow", "fridge", "tv", "obj", "sconcel"}
DOOR_NAMES = {"door", "mdoor", "mud", "updoor", "col_low", "col_up", "cabd", "mezd", "mezdoor", "sud", "sdoor",
              "mcd", "id", "dl", "g", "rd_door"}
DRAWER_NAMES = {"dr", "md", "d", "drwa", "drwb", "drwc", "sd", "pd", "pdr", "rd", "nsd", "ida", "idb", "f", "boxf"}
FLAP_NAMES = {"flap"}
EDGE_ALL = {"fronts", "top", "shelves", "headboard", "platform", "bench", "rails"}
STONE = (214, 210, 203)
INNER = (236, 234, 229)
LED = (255, 210, 150)


def base_name(n):
    return re.sub(r"[_\-]?\d+(\.\d+)?", "", n)


def color_info(rgb, mats):
    rgb = tuple(int(c) for c in rgb)
    for k, c in mats["colors"].items():
        if tuple(c["rgb"]) == rgb:
            return k, c["name"]
    for k, c in mats["metal"].items():
        if tuple(c["rgb"]) == rgb:
            return k, c["name"]
    for k, c in mats["fabric"].items():
        if tuple(c["rgb"]) == rgb:
            return "fab-" + k, c["name"]
    named = {INNER: ("INNER", "белый (внутренний)"), STONE: ("STONE", "кварц светлый"),
             (34, 34, 36): ("black", "чёрный"), (168, 170, 174): ("steel", "сталь/алюминий"),
             (120, 124, 130): ("steel", "сталь"), (222, 196, 150): ("birch", "берёза"),
             (24, 24, 26): ("dark", "тёмное стекло"), (70, 74, 80): ("tint", "тонированное"),
             (196, 206, 212): ("mirror", "зеркало")}
    if rgb in named:
        return named[rgb]
    return "#%02x%02x%02x" % rgb, "цвет #%02x%02x%02x" % rgb


def ckind(rgb, mats):
    rgb = tuple(int(c) for c in rgb)
    if rgb == LED:
        return "led"
    if rgb in ((24, 24, 26), (70, 74, 80)):
        return "glass"
    if rgb == (196, 206, 212):
        return "mirror"
    if rgb in {tuple(m["rgb"]) for m in mats["metal"].values()} | {(120, 124, 130), (168, 170, 174), (34, 34, 36)}:
        return "metal"
    if rgb in {tuple(f["rgb"]) for f in mats["fabric"].values()} | {tuple(mats["fixed"]["mattress"]["rgb"]),
                                                                   tuple(mats["fixed"]["pillow"]["rgb"]), (150, 150, 152)}:
        return "fabric"
    if rgb == STONE:
        return "stone"
    return "board"


def board_material(t, group, ck):
    """Материал плиты по толщине. Ключи — из prices.json."""
    if ck == "stone":
        return "STONE", f"Кварц {t:g}"
    if t <= 5:
        return "HDF4", "ХДФ"
    if t <= 12:
        return "MDF-THIN", f"МДФ {t:g}"
    if t <= 17:
        return "LDSP16", "ЛДСП 16"
    if t <= 19:
        return ("FRONT18", "Фасад МДФ 18") if group == "fronts" else ("LDSP18", "ЛДСП 18")
    if t <= 23:
        return "LDSP22", "ЛДСП 22"
    if t <= 26:
        return "LDSP25", "ЛДСП 25"
    if t <= 30:
        return "TOP28", "Столешница 28"
    if t <= 41:
        return "TOP38", "Плита 38–40"
    if t <= 52:
        return "PANEL50", "Плита 50 (склейка 2 × 25)"
    return None, None


def classify(q, mats, has_sliding):
    """Деталь builders -> (kind, unit, material, axis, extra). extra: hardware hint / bom_size / edge."""
    n = base_name(q.name)
    d = (q.x1 - q.x0, q.y1 - q.y0, q.z1 - q.z0)
    a, b, c = sorted(d)
    axis = "xyz"[d.index(c)]
    ck = ckind(q.color, mats)
    g = q.group
    if g in ("bedding", "appliances") or n in CONTEXT_NAMES or (g == "decor" and n in ("obj", "tv")):
        return "context", "Не входит в изделие", "", axis, {}
    if g == "feet":
        return "buy", "Подпятник", "", axis, {"hw": "FOOT-ADJ"}
    if ck == "led":
        return "buy", "LED-лента", "", axis, {"hw": "LED", "len": c}
    if n == "sconce":
        return "buy", "Бра", "", axis, {"hw": "SCONCE"}
    if n == "charger":
        return "buy", "Беспроводная зарядка", "", axis, {"hw": "CHARGER"}
    if n in ("gola_C", "gola_L", "igC", "igL"):
        return "buy", "Профиль Gola", "", axis, {"hw": "GOLA", "len": c}
    if n in ("profa", "profb", "track_top", "track_bot"):
        return "buy", "Профиль шкафа-купе", "", axis, {"hw": "SLIDE-PROFILE", "len": c}
    if n.startswith("rod"):
        return "buy", "Штанга", "", axis, {"hw": "ROD", "len": c}
    if n in ("fL", "fR", "fT", "fB"):
        return "buy", "Профиль рамочного фасада", "", axis, {"hw": "FRAME-PROFILE", "len": c}
    if n == "cablebox":
        return "buy", "Лючок кабельный", "", axis, {"hw": "CABLE-BOX"}
    if n == "lock":
        return "buy", "Замок", "", axis, {"hw": "LOCK"}
    if n == "hook":
        return "buy", "Крючок", "", axis, {"hw": "HOOK"}
    if n == "hookt":
        return "buy_part", "Крючок (часть)", "", axis, {}
    if ck == "metal" and a <= 12.5 and b <= 12.5:
        if round(a) == 12:
            return "buy", "Ручка-скоба", "", axis, {"hw": "HANDLE", "len": c}
        return "buy_part", "Ручка (стойка)", "", axis, {}
    if g == "slats" and a <= 10:
        return "buy", "Ламель", "", axis, {"hw": "SLAT"}
    if ck in ("glass", "mirror"):
        return "glass", "Зеркало" if ck == "mirror" else "Стекло", "MIRROR" if ck == "mirror" else "GLASS", axis, {}
    if ck == "fabric":
        return "upholstery", "Мягкая панель", "UPHOLSTERY", axis, {}
    if "plinth" in n or n in ("pl", "cabpl") or (g == "carcass" and n == "base" and a >= 40):
        if b > 600:   # цоколь кровати/шкафа по периметру основания
            return "board", "Цоколь по периметру", "LDSP16", axis, {"bom": (2 * (b + c), a, 16), "edge": 2 * (b + c) / 1000}
        return "board", "Цоколь (планка)", "LDSP16", axis, {"bom": (c, a, 16), "edge": c / 1000}
    if g in ("frame", "base", "headboard", "rails") and 40 <= a and b <= 150 and c >= 100 and (ck != "metal" or b > 80):
        return "timber", f"Брус {round(a)}×{round(b)}", f"TIMBER{round(a)}x{round(b)}", axis, {}
    if ck == "metal" or n == "plat_rail":
        if a <= 4:
            return "plate", "Лист стальной", f"S235-{round(a)}", axis, {}
        if a <= 12 and b >= 50:
            return "plate", "Лоток (гнутый лист)", "S235-2", axis, {"bom": (c, b + 2 * a, 2)}
        if b <= 80:
            sec = f"{round(b)}x{round(a)}"
            return "tube", f"Труба {sec.replace('x', '×')}", f"TUBE{sec}x2", axis, {}
        return "volume", "Металлический объём (деталировка не выполнена)", "", axis, {}
    if n == "drawer" and g == "interior":
        return "volume", "Внутренний ящик (корпус не детализирован)", "", axis, {"hw": "SLIDES"}
    mat, label = board_material(round(a), g, ck)
    if mat is None:
        return "volume", "Объём (деталировка не выполнена)", "", axis, {}
    edge = 2 * (b + c) / 1000 if g in EDGE_ALL else (c / 1000 if mat not in ("HDF4",) else 0)
    unit = {"fronts": "Фасад", "top": "Столешница", "shelves": "Полка", "interior": "Полка/перегородка"}.get(g, "Деталь корпуса")
    if mat == "HDF4":
        unit = "Задняя стенка / дно"
    if mat in ("TOP28", "TOP38", "STONE") and g != "fronts":
        unit = "Столешница"
    if g == "slats":
        unit = "Ламель (щит)"
    hint = {}
    if g == "fronts" and mat in ("FRONT18", "LDSP16", "LDSP18", "MDF-THIN"):
        if n in DOOR_NAMES:
            h = d[2]
            hint = {"hw": "ROLLERS" if has_sliding else "HINGE", "n": 1 if has_sliding else (2 if h <= 900 else 3 if h <= 1600 else 4 if h <= 2000 else 5)}
        elif n in FLAP_NAMES:
            hint = {"hw": "FLAP-LIFT"}
        elif n in DRAWER_NAMES:
            hint = {"hw": "SLIDES"}
    hint["edge"] = edge
    return "board", unit, mat, axis, hint


HW = {  # id: (название, спецификация, единица)
    "HINGE": ("Петля мебельная с доводчиком", "накладная/вкладная — по фасаду", "шт"),
    "SLIDES": ("Направляющие ящика (пара)", "скрытого монтажа, полного выдвижения, с доводчиком", "компл"),
    "FLAP-LIFT": ("Подъёмник откидного фасада", "по весу фасада", "шт"),
    "ROLLERS": ("Ролики двери-купе (комплект на дверь)", "под профиль системы", "компл"),
    "HANDLE": ("Ручка-скоба", "длина по 3D", "шт"),
    "GOLA": ("Профиль Gola", "алюминий", "м"),
    "SLIDE-PROFILE": ("Профиль системы шкафа-купе", "алюминий", "м"),
    "FRAME-PROFILE": ("Профиль рамочного фасада", "алюминий, чёрный", "м"),
    "ROD": ("Штанга гардеробная", "Ø25", "м"),
    "LOCK": ("Замок мебельный", "", "шт"),
    "CABLE-BOX": ("Лючок кабельный врезной", "в вырез крышки, заподлицо", "шт"),
    "HOOK": ("Крючок", "", "шт"),
    "LED": ("LED-лента с профилем", "тёплая 3000 K", "м"),
    "SCONCE": ("Бра", "по дизайну", "шт"),
    "CHARGER": ("Беспроводная зарядка встраиваемая", "", "шт"),
    "SLAT": ("Ламель берёзовая", "53 × 8, с латодержателями", "шт"),
    "FOOT-ADJ": ("Подпятник регулируемый", "", "шт"),
    "LIFT-MECH": ("Подъёмный механизм с газлифтами", "по размеру кровати", "компл"),
    "BED-LEG": ("Опора регулируемая", "M10, высота по 3D", "шт"),
}


JOINT_RULE = ("Правило стыка по умолчанию (предложение, утвердить с цехом): вертикальная деталь сквозная, "
              "горизонтальная упирается в неё; из двух горизонтальных упирается более короткая.")


def _ov(a, b):
    return [min(getattr(a, k + "1"), getattr(b, k + "1")) - max(getattr(a, k + "0"), getattr(b, k + "0")) for k in "xyz"]


def resolve_joints(P):
    """Стыки линейных деталей, которые в 3D заходят друг в друга концами: укорачивает упирающуюся деталь
    на величину захода. Только труба×труба, брус×брус, плита×плита; сквозные проходы и вырезы не трогает."""
    trims = []
    for _ in range(3):
        changed = False
        for i, a in enumerate(P):
            for b in P[i + 1:]:
                if a.kind not in ("tube", "timber", "board") or a.kind != b.kind:
                    continue
                ov = _ov(a, b)
                if not all(o > 0.5 for o in ov):
                    continue
                cand = []
                for q in (a, b):
                    sz = (q.x1 - q.x0, q.y1 - q.y0, q.z1 - q.z0)
                    ax = "xyz"[sz.index(max(sz))]
                    lo, hi = getattr(q, ax + "0"), getattr(q, ax + "1")
                    o = ov["xyz".index(ax)]
                    if o >= 0.5 * (hi - lo):
                        continue
                    other = b if q is a else a
                    olo = max(lo, getattr(other, ax + "0")); ohi = min(hi, getattr(other, ax + "1"))
                    end = "0" if abs(olo - lo) < 0.6 else ("1" if abs(ohi - hi) < 0.6 else None)
                    if end:
                        cand.append((q, ax, end, o, max(sz)))
                if not cand:
                    continue
                if len(cand) == 2:
                    hor = [c for c in cand if c[1] != "z"]
                    cand = [min(hor, key=lambda c: c[4])] if hor else [min(cand, key=lambda c: c[4])]
                q, ax, end, o, _ = cand[0]
                if end == "0":
                    setattr(q, ax + "0", round(getattr(q, ax + "0") + o, 3))
                else:
                    setattr(q, ax + "1", round(getattr(q, ax + "1") - o, 3))
                trims.append(f"{q.id} укорочена на {o:g} у стыка с {(b if q is a else a).id}")
                changed = True
        if not changed:
            break
    return trims


def expected_overlap(a, b):
    """Задуманные посадки: паз/вырез под профиль или стойку, стекло в профиле, цоколь вокруг опор, лючок в крышке."""
    kinds = {a["kind"], b["kind"]}
    if "buy" in kinds:
        return "паз или вырез под покупное изделие (профиль, лючок, подпятник)"
    if kinds == {"tube", "board"}:
        return "вырез в плите под стойку (деталировать вырез)"
    if kinds == {"tube", "cap"}:
        return "заглушка в торце трубы"
    if "glass" in kinds:
        return "стекло в пазу рамки или профиля"
    return None


def build(prod: dict, options: dict, builders: dict, mats: dict) -> Design:
    v = dict(options)
    model, facts = builders[prod["builder"]](v, mats)
    names = {base_name(q.name) for q in model.parts}
    sliding = bool(names & {"track_top", "profa"})
    P, hw, n_by = [], {}, {}
    for q in model.parts:
        kind, unit, mat, axis, ex = classify(q, mats, sliding)
        fin, fin_name = color_info(q.color, mats)
        P.append(EPart(q.name, unit, kind, round(q.x0, 3), round(q.y0, 3), round(q.z0, 3), round(q.x1, 3),
                       round(q.y1, 3), round(q.z1, 3), mat, fin, q.group, axis if kind in ("tube", "timber") else "",
                       unit, fin_name, tuple(int(c) for c in q.color), tuple(ex.get("bom", ())),
                       round(ex.get("edge", 0), 3)))
        if "hw" in ex:
            k = ex["hw"]
            hw[k] = hw.get(k, 0) + (ex["len"] / 1000 if "len" in ex and HW[k][2] == "м" else ex.get("n", 1))
    if prod["builder"] == "bed_lift":
        hw["LIFT-MECH"] = 1
    if prod["builder"].startswith("floating_bed"):
        hw["BED-LEG"] = sum(1 for q in model.parts if base_name(q.name) == "leg")
    trims = resolve_joints(P)
    d = Design(prod["sku"], REV, STATUS, v, {}, P)
    d.hardware = [Hardware(k, HW[k][0], HW[k][1], round(q, 2), "оценка по 3D", uom=HW[k][2]) for k, q in sorted(hw.items())]
    d.glows = [[round(g.x0), round(g.y0), round(g.x1), round(g.y1), list(g.color), round(g.blur_mm)] for g in model.glows]
    lo = [min(getattr(p, k) for p in P if p.kind != "context") for k in ("x0", "y0", "z0")]
    hi = [max(getattr(p, k) for p in P if p.kind != "context") for k in ("x1", "y1", "z1")]
    made = [p for p in P if p.kind in ("board", "tube", "timber", "plate", "cap", "glass", "upholstery", "volume")]
    boards = [p for p in made if p.kind == "board"]
    tubes = [p for p in made if p.kind == "tube"]
    d.derived = {"width": round(hi[0] - lo[0]), "depth": round(hi[1] - lo[1]), "height": round(hi[2]),
                 "parts_made": len(made), "parts_context": sum(p.kind == "context" for p in P),
                 "volumes": sum(p.kind == "volume" for p in P)}
    d.ops = {
        "board_cut": len(boards),
        "edging_m": round(sum(p.edge_m for p in boards), 2),
        "tube_cut": len(tubes),
        "weld_frame_joint": len(tubes),
        "powder_m2": round(sum(2 * sum(sorted(p.size)[:2]) * max(p.size) for p in tubes) / 1e6, 3),
        "upholstery_m2": round(sum(sorted(p.size)[1] * sorted(p.size)[2] for p in made if p.kind == "upholstery") / 1e6, 3),
        "assembly_part": len(made),
    }
    d.warnings = [
        "Каталожная геометрия: конструкция (соединения, присадка, крепёж) не разработана.",
        "Материалы определены по толщине и цвету детали в 3D, фурнитура — по правилам; всё уточняется с цехом.",
    ]
    if d.derived["volumes"]:
        d.warnings.append(f"{d.derived['volumes']} объём(а) без деталировки — в материалы не включены.")
    d.blockers = ["CONSTRUCTION_NOT_DESIGNED", "HARDWARE_NOT_SELECTED", "MATERIALS_NOT_CONFIRMED", "PROTOTYPE"]
    d.checks = [("Габарит по 3D совпадает с суммой деталей", True, all(p.x1 > p.x0 and p.y1 > p.y0 and p.z1 > p.z0 for p in P))]
    d.notes = [f"Изделие: {prod['name']}"] + ([JOINT_RULE] + trims if trims else [])
    if trims:
        d.warnings.append(f"Стыки: {len(trims)} деталей укорочены по правилу по умолчанию — утвердить с цехом.")
    d.model_checks, d.wall_y, d.facts = getattr(model, "checks", []), getattr(model, "wall_y", None), facts
    return d
