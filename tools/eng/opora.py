"""ARV-TBL-003 «Опора» — ревизии конструкции.

R00  — прежняя каталожная геометрия: две рамы на полу, без связей, крепление не задано. Хранится для истории.
R02E — инженерная редакция R02-E.1 (пакет ChatGPT, 29.10.2026), перенесена по исходному коду пакета
       (src/opora.py) и сверяется с его эталоном fixtures/golden.jsonl (1512 комбинаций), детали — с теми же id.
       Внешний вид (связи, рама на подпятниках 35 мм) утверждён владельцем 29.10.2026 для каталога.
       Конструкция НЕ утверждена: выпуск в производство закрыт (manufacturing_allowed = False).

Параметры инженерной области R02E (как в пакете):
  size 1200…2000 шаг 100 · substrate chipboard | mdf | solid-wood · thickness 25 | 30 | 40
  metal black | white · base linked | original · foot_height 35 | 40 · edge 0 | 1 | 2 (массив — только 0)
Каталог (сайт) открывает только size, top (декор), metal; остальное — значения по умолчанию ниже.
"""
from __future__ import annotations

import itertools

from .core import Design, EPart, Hardware

SKU = "ARV-TBL-003"
TUBE = 40
# R03E — решение владельца 29.10: низкие регулируемые подпятники у концов нижней перекладины,
#        рама визуально почти на полу; связи и крепление — как в R02E.
REVS = {
    "R03E": "инженерное предложение (R02E + низкие подпятники); внешний вид утверждён, конструкция не утверждена, не для изготовления",
    "R00": "прежняя каталожная геометрия; конструкция не проверена",
    "R02E": "инженерное предложение R02-E.1 (эталон пакета); не для изготовления",
}
LENGTHS = list(range(1200, 2001, 100))
DENSITY = {"chipboard": 650, "mdf": 750, "solid-wood": 700}   # кг/м³, ориентир до паспорта плиты
TUBE_KG_M = (40 * 40 - 36 * 36) * 7850 / 1e6                    # 2,39 кг/м
DEFAULTS = {"substrate": "chipboard", "thickness": 25, "base": "linked", "foot_height": 35, "edge": 2, "feet_y": 170,
            "top": "O", "metal": "black"}
SUBSTRATES = {"chipboard": ("LDSP", "ЛДСП"), "mdf": ("MDF", "МДФ"), "solid-wood": ("SOLID", "Массив")}
KEYS = {"size", "top", "metal", "substrate", "thickness", "base", "foot_height", "edge", "feet_y"}
BLOCKERS = ["MATERIAL_SKU_AND_TOLERANCES", "FRAME_AND_WELD_VERIFICATION", "PROTOTYPE_STRENGTH_STABILITY_DURABILITY",
            "INSERT_PULL_OUT_AND_TORQUE", "M8_SUPPORT_RIVET_NUT_AND_WORKING_HEIGHT", "COATING_AND_ASSEMBLY_STACK",
            "SHOP_PROCESS_APPROVAL", "TIP_OVER_CHECK_FEET_Y"]


REV_DEFAULTS = {"R03E": {"foot_height": 12, "feet_y": 115}}
FEET = {  # установочная высота -> допустимые положения от кромки
    "R02E": {"heights": (35, 40), "ys": (120, 170)},
    "R03E": {"heights": (10, 12, 15), "ys": (115, 120)},
    "R00": {"heights": (35, 40), "ys": (120, 170)},
}


def normalize(raw: dict, rev: str) -> dict:
    """Проверка и нормализация конфигурации. Неизвестные ключи, неверные типы и значения — ошибка."""
    if not isinstance(raw, dict) or set(raw) - KEYS:
        raise ValueError(f"неизвестные параметры: {sorted(set(raw) - KEYS)}")
    c = {**DEFAULTS, **REV_DEFAULTS.get(rev, {}), **raw}
    for k in ("size", "thickness", "foot_height", "edge"):
        if type(c[k]) not in (int, float) or c[k] != c[k] or c[k] in (float("inf"), float("-inf")):
            raise ValueError(f"{k}: нужно число")
        if float(c[k]).is_integer():
            c[k] = int(c[k])
    errs = []
    if c["size"] not in LENGTHS:
        errs.append(f"длина {c['size']} вне ряда 1200…2000 шаг 100")
    if c["substrate"] not in SUBSTRATES:
        errs.append("неизвестная основа столешницы")
    if c["thickness"] not in (25, 30, 40):
        errs.append("толщина столешницы 25 / 30 / 40 (18 не поддерживается)")
    if c["metal"] not in ("black", "white") or c["base"] not in ("original", "linked"):
        errs.append("неизвестный цвет металла или тип каркаса")
    if c["foot_height"] not in FEET[rev]["heights"]:
        errs.append(f"установочная высота подпятника: {FEET[rev]['heights']} (предварительно)")
    if c["feet_y"] not in FEET[rev]["ys"]:
        errs.append(f"подпятники от передней/задней кромки: {FEET[rev]['ys']}")
    if c["edge"] not in (0, 1, 2):
        errs.append("кромка 0 / 1 / 2")
    if c["substrate"] == "solid-wood" and c["edge"] != 0:
        errs.append("массив без кромки: edge = 0")
    if rev == "R00" and (c["base"] != "original"):
        c = {**c, "base": "original"}
    if errs:
        raise ValueError("; ".join(errs))
    return c


def build(options: dict, rev: str = "R02E") -> Design:
    if rev not in REVS:
        raise ValueError(f"нет ревизии {rev}")
    c = normalize(options, rev)
    L = c["size"]
    D = 800 if L <= 1400 else 900
    H = 750
    ENG = rev in ("R02E", "R03E")
    T = c["thickness"] if ENG else 25
    F = c["foot_height"] if ENG else 0
    U = H - T                      # низ столешницы = верх рам, связей и пластин
    B = D - 200                    # длина перекладины
    metal = c["metal"]
    mat_key, mat_ru = SUBSTRATES[c["substrate"]]
    board_mat = f"{mat_key}{T}"
    P, holes = [], []
    edge = c["edge"] if ENG else 0
    P.append(EPart("TOP", "Столешница", "board", 0, 0, U, L, D, H, board_mat, c["top"], "top", unit="Столешница",
                   note=f"{mat_ru} {T}; заготовка {L - 2 * edge} × {D - 2 * edge}; кромка {edge}; рисунок вдоль X"))
    for i, x in enumerate((150, L - 190), 1):
        for suf, z in (("LOW", F), ("UP", U - TUBE)):
            P.append(EPart(f"F{i}-{suf}", "Перекладина", "tube", x, 100, z, x + TUBE, D - 100, z + TUBE,
                           "TUBE40x40x2", metal, "base", "y", "Перекладина"))
        for suf, y in (("FRONT", 100), ("BACK", D - 140)):
            P.append(EPart(f"F{i}-{suf}", "Стойка", "tube", x, y, F + TUBE, x + TUBE, y + TUBE, U - TUBE,
                           "TUBE40x40x2", metal, "base", "z", "Стойка"))
        if rev == "R00":
            continue
        fy = c["feet_y"]
        for j, y in enumerate((fy, D - fy), 1):
            r = 16 if rev == "R02E" else 12.5          # основание Ø32 (R02E) / Ø25 низкий (R03E)
            P.append(EPart(f"FOOT-{i}-{j}", "Подпятник M8 (резерв габарита)", "buy", x + 20 - r, y - r, 0, x + 20 + r, y + r, F,
                           "FOOT-M8", "black", "feet", note="точная покупная геометрия не построена"))
        for j, (z, y) in enumerate(itertools.product((F, U - TUBE), (100, D - 102)), 1):
            P.append(EPart(f"CAP-{i}-{j}", "Заглушка торца", "cap", x + 2, y, z + 2, x + 38, y + 2, z + 38,
                           "S235-2", metal, "base", unit="Заглушка", note="36×36×2 номинал, подогнать по радиусам"))
        ys = (220, D / 2, D - 220) if c["substrate"] == "solid-wood" else (220, D - 220)
        for side, cx in (("OUT", x - 25), ("IN", x + 65)):
            for j, cy in enumerate(ys, 1):
                sem = "END" if (i == 1 and side == "OUT") or (i == 2 and side == "IN") else "CENTER"
                pid = f"PL-{i}-{sem}-{j}"
                P.append(EPart(pid, "Пластина крепления", "plate", cx - 25, cy - 20, U - 4, cx + 25, cy + 20, U,
                               "S235-4", metal, "plates", unit="Пластина",
                               note=("к торцу" if sem == "END" else "к центру") +
                                    f"; сварная кромка {'x+' if side == 'OUT' else 'x-'}"))
                if c["substrate"] == "solid-wood":
                    typ = "round" if (i == 1 and side == "OUT" and cy == D / 2) else ("slot-x" if cy == D / 2 else "slot-y")
                else:
                    typ = "slot-x"
                holes.append({"id": "H-" + pid, "part_id": pid, "x": cx, "y": cy, "z": U, "kind": typ, "width": 7,
                              "length": 7 if typ == "round" else (20 if typ == "slot-y" else 12),
                              "pilot": 10, "pilot_depth": 17, "insert": "RAMPA SK330 040615001",
                              "status": "nominal-reference-not-drilling",
                              "location_method": "transfer-from-finished-frame"})
    if ENG and c["base"] == "linked":
        for i, y in enumerate((140, D - 180), 1):
            P.append(EPart(f"LINK-{i}", "Продольная связь", "tube", 190, y, U - TUBE, L - 190, y + TUBE, U,
                           "TUBE40x40x2", metal, "links", "x", "Связь"))
    d = Design(SKU, rev, REVS[rev], {"size": L, **{k: c[k] for k in sorted(c) if k != "size"}}, {}, P, holes=holes)
    n = len(holes)
    if ENG:
        d.hardware = [
            Hardware("INSERT-M6", "Втулка резьбовая M6", "RAMPA SK330 040615001, Ø12 × 15, без буртика", n,
                     note="наличие у местного поставщика не подтверждено"),
            Hardware("SCREW-M6x16", "Винт M6 × 16", "ISO 7380-1, A2; кандидат Bossard BN1593 1349120", n,
                     note="группу прочности подтвердить"),
            Hardware("WASHER-6.4x18", "Шайба 6,4 × 18 × 1,6", "ISO 7093-1, A2", n),
            Hardware("FOOT-M8", "Подпятник регулируемый M8",
                     "серия Ganter GN 343.4, основание Ø32" if rev == "R02E" else
                     f"низкий, основание Ø25, установочная высота {F} мм, ход регулировки ≈10 мм, пластик/войлок", 4,
                     note="артикул и ход не выбраны"),
            Hardware("RIVNUT-M8", "Заклёпочная гайка M8", "под стенку 2 мм", 4, note="артикул и отверстие не выбраны"),
            Hardware("NUT-M8", "Контргайка M8", "по комплектности подпятника", 4),
        ]
        d.blockers = list(BLOCKERS) + (["NO_LONGITUDINAL_CONNECTION"] if c["base"] == "original" else []) + \
            (["WOOD_MOVEMENT_BUDGET", "SLIDING_JOINT_FRICTION_AND_LOOSENING"] if c["substrate"] == "solid-wood" else [])
        d.warnings = [
            ("Внешний вид утверждён (29.10, низкие подпятники); конструкция — инженерное предложение, в производство не выдаётся."
             if rev == "R03E" else "Пакет R02-E: высокие подпятники 35/40; в каталоге заменён на R03E (29.10)."),
            f"h = {F} мм — предварительная высота узла подпятника; от неё зависят рама {U - F} и стойка {U - F - 80}.",
            f"Подпятники на Y = {c['feet_y']} / D−{c['feet_y']}: оценка опрокидывания — см. «Нагрузка на край»; подтвердить испытанием.",
            *(["Низкий подпятник: ход ≈10 мм — проверить на неровном полу."] if rev == "R03E" else []),
            "Отверстия столешницы номинальные: сверлить только по месту, с готового окрашенного подстолья.",
        ]
        if c["base"] == "original":
            d.warnings.insert(0, "Без продольных связей схема не воспринимает продольные усилия.")
    else:
        d.blockers = ["NO_LONGITUDINAL_CONNECTION", "NO_FASTENING"]
        d.warnings = ["Крепление столешницы и продольная жёсткость в R00 не заданы — только внешний вид."]

    tubes = [p for p in P if p.kind == "tube"]
    net = sum(p.length for p in tubes)
    n_pl = sum(p.kind == "plate" for p in P)
    n_cap = sum(p.kind == "cap" for p in P)
    link = L - 380 if any(p.id.startswith("LINK") for p in P) else 0
    # Грубая оценка устойчивости: вертикальная нагрузка на середину длинного края столешницы,
    # опрокидывание вокруг линии подпятников (R00 — вокруг наружной грани нижней перекладины).
    mass = L * D * T / 1e9 * DENSITY[c["substrate"]] + net / 1000 * TUBE_KG_M + \
        sum((p.x1 - p.x0) * (p.y1 - p.y0) * (p.z1 - p.z0) for p in P if p.kind in ("plate", "cap")) / 1e9 * 7850
    pivot = c["feet_y"] if F else 100
    tip = mass * (D / 2 - pivot) / pivot
    d.derived = {"length": L, "width": D, "height": H, "top_t": T, "feet_h": F, "frame_h": U - F,
                 "leg": U - F - 80, "bar": B, "link": link, "tube_net": net, "holes": n,
                 "mass_kg": round(mass, 1), "feet_y": pivot if F else None, "tip_load_kg": round(tip)}
    d.ops = {
        "tube_cut": len(tubes),
        "weld_frame_joint": 8 + (4 if link else 0),
        "weld_small": n_pl + n_cap,
        "powder_m2": round(net / 1000 * 4 * TUBE / 1000 + n_pl * 2 * 0.05 * 0.04, 3),
        "board_cut": 1,
        "edging_m": round(2 * (L + D) / 1000, 2) if edge else 0,
        "drill_insert": n,
        "rivnut_set": 4 if F else 0,
        "assembly": 1,
    }
    d.checks = [
        ("Высота изделия, мм", H, F + (U - F) + T),
        ("Стойка = рама − 80", U - F - 80, round(P[3].z1 - P[3].z0)),
        ("Перекладина = ширина − 200", B, round(P[1].y1 - P[1].y0)),
    ]
    if ENG:
        d.checks.append(("Остаток плиты под втулкой (17 + 0,5)", T - 17.5, T - 17.5))
        if link:
            d.checks.append(("Связь = длина − 380", L - 380, link))
        if rev == "R03E" and (L, T, F) == (1600, 25, 12):
            d.checks += [("R03E: рама 713", 713, U - F), ("R03E: стойка 633", 633, U - F - 80),
                         ("R03E: связь 1220", 1220, link)]
        if rev == "R02E" and (L, T, F, c["base"]) == (1600, 25, 35, "linked"):
            d.checks += [("R02-E: рама 690", 690, U - F), ("R02-E: стойка 610", 610, U - F - 80),
                         ("R02-E: связь 1220", 1220, link), ("R02-E: труба нетто 7680", 7680, net),
                         ("R02-E: креплений 8 (плита)" if c["substrate"] != "solid-wood" else "R02-E: креплений 12",
                          8 if c["substrate"] != "solid-wood" else 12, n)]
    d.notes = ["Ряд длин 1200…2000; ширина 800 до 1400, 900 с 1500.", f"Основа: {mat_ru} {T}."]
    return d


def palette(mats):
    def f(p):
        if p["group"] == "top":
            return mats["colors"][p["finish"]]["rgb"]
        if p["group"] == "feet":
            return (60, 60, 62)
        return mats["metal"][p["finish"]]["rgb"]
    return f
