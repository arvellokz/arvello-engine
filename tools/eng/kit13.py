"""Рабочие комплекты R01E для 13 моделей (тумбы, комоды, столы) из снимка конфигурации — листы A3.

    python tools/eng/kit13.py SKU OUT.pdf [key=value ...]

Состав (номера листов зависят от модели): 01 Общий вид · 02 Сборочный чертёж · Детали (плита) · Металл ·
Узлы · Спецификация · Сборка и контроль · Открытые вопросы и решения.
Все размеры — из снимка (eng/models13.py на ядре eng/cab.py). Детали изготавливаются по независимым размерам
от баз A; по месту — выставление фасадов и перенос отверстий столешницы с готовой рамы.
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

from eng import boardkit  # noqa: E402
from eng.boardkit import EDGE_TXT, NAME, Frame, blank, detail, hole_rows, section  # noqa: E402
from eng.catalog import default_options, materials, products  # noqa: E402
from eng.core import bom, cut_plan, snapshot, to_model  # noqa: E402
from eng.models13 import MODELS, build  # noqa: E402
from eng import kitchen as KX  # noqa: E402
from eng import models_rest as MR  # noqa: E402
from eng import models_new  # noqa: E402,F401  новые модели (с 11.11.2026)
from eng.sheetlib import CTR, DIM, HID, PHANTOM, RED, THIN, VIS, Sheet, View  # noqa: E402
from eng.verify13 import verify  # noqa: E402

boardkit.KIND_RU.update({
    "foot_screw": "засверловка под саморез опоры", "hanger_screw": "засверловка навеса", "hinge_cup": "чашка петли",
    "hinge_plate": "монтажная планка петли (евровинт)", "hinge_cup_screw": "саморез чашки петли", "handle_box": "винт ручки сквозь короб", "led_screw": "крепёж профиля LED",
    "cable": "ввод кабеля", "cutout_round": "вырез под встраиваемое изделие", "lock": "цилиндр замка",
    "pilot": "засверловка под саморез", "screw_face": "саморез, зенковка", "insert": "втулка резьбовая M6",
    "top_conn": "стяжка столешницы", "bracket_pilot": "уголок мебельный", "tube_top": "под винт", "tube_access": "доступ",
    "tube_side": "под саморез", "wall_bolt": "к стене", "plate_hole": "под винт", "rivnut": "гайка заклёпочная M8",
    "rivnut6": "гайка заклёпочная M6", "tray_hole": "саморез лотка", "gola": "крепление профиля Gola",
    "bed_face": "под стяжку кроватную, насквозь", "bed_edge": "под винт стяжки", "bed_nut": "под гайку-бочонок",
    "bolt_hole": "под болт, насквозь",
})

NODE = {"ecc_stem": "А", "ecc_bolt": "А", "ecc_housing": "А", "dowel_face": "Б", "dowel_edge": "Б", "conf_face": "В",
        "conf_edge": "В", "front_screw": "Г", "handle": "Д", "handle_box": "Д", "back_pilot": "Е", "runner_mark": "Ж",
        "hinge_cup": "И", "hinge_plate": "И", "hinge_cup_screw": "И", "foot_screw": "К", "hanger_screw": "К", "tube_top": "Л", "tube_access": "Л",
        "insert": "Л", "tube_side": "М", "wall_bolt": "М", "plate_hole": "М", "rivnut6": "М", "screw_face": "Н",
        "led_screw": "П", "cable": "П", "cutout_round": "П", "lock": "П", "top_conn": "П", "bracket_pilot": "Н",
        "rivnut": "К", "tray_hole": "М", "gola": "П", "bed_face": "Р", "bed_edge": "Р", "bed_nut": "Р", "bolt_hole": "М"}
NODE_TXT = {
    "А": ("Minifix 15 + болт S200", ["Корпус Ø15 гл. 12,5 (+0,5), B = 24;", "болт: Ø8 гл. 32 в торец, A = 8 от пласти;",
                                     "шток Ø5 гл. 12 в пласть (Häfele стр. 294, 301)."]),
    "Б": ("Шкант 8 × 30", ["Шкант на клей: в пласть гл. 12,", "в торец гл. 20."]),
    "В": ("Конфирмат 7 × 50", ["Ø7 насквозь с зенковкой,", "в торец Ø5 гл. 36."]),
    "Г": ("Фасад — короб", ["Саморез 4 × 25 изнутри короба,", "зенковка; вход в фасад 9."]),
    "Д": ("Ручка", ["Ø5 насквозь; винт M4 (длина —", "в спецификации)."]),
    "Е": ("Задняя стенка ХДФ", ["Накладная, отступ 2 от граней;", "саморез 3,5 × 16 в Ø2,5 гл. 12."]),
    "Ж": ("Профиль Blum 560H", ["Саморез Ø4 × 15 по разметке, без", "сверления; ось — над низом профиля", "37 (TIP-ON — 38)."]),
    "И": ("Петля (кандидат)", ["Чашка Ø35 гл. 13, центр 22,5 от кромки;", "2 самореза чашки 3,5 × 15: ± 22,5, 9,5",
                               "к середине двери; планка 173L8100 —", "системные винты Ø6 в Ø5 гл. 13 (В-20)."]),
    "К": ("Опора / навес", ["Засверловки Ø3 гл. 10 по площадке", "или шаблону навеса."]),
    "Л": ("Столешница — рама", ["Труба: Ø7 сверху, Ø13 снизу;", "втулка M6 Ø10 гл. 17 в плите", "по разметке с готовой рамы."]),
    "М": ("Рама — корпус / стена / балка", ["Сквозное в трубе; саморез", "или болт по спецификации."]),
    "Н": ("Саморез через плиту", ["Ø4,5 насквозь с зенковкой;", "засверловка Ø3 гл. 12."]),
    "Р": ("Стяжка кроватная M6", ["Ø7 насквозь в первой детали;", "Ø7 гл. 70 в торец второй;",
                                  "бочонок Ø10 — поперёк, на 60 от наружной пласти."]),
    "П": ("Встраиваемые изделия", ["Вырезы и вводы — по образцу", "изделия (кандидаты, последний лист)."]),
}

MAT_RU = {"LDSP16": "ЛДСП 16", "LDSP18": "ЛДСП 18", "LDSP22": "ЛДСП 22", "LDSP25": "ЛДСП 25", "HDF4": "ХДФ 4",
          "MDF22": "МДФ 22", "TOP28": "Плита-столешница 28", "TOP38": "Плита-столешница 38",
          "TUBE20x20x2": "Труба 20 × 20 × 2", "TUBE30x20x2": "Труба 30 × 20 × 2", "TUBE60x30x2": "Труба 60 × 30 × 2",
          "TUBE30x30x2": "Труба 30 × 30 × 2", "TUBE40x40x2": "Труба 40 × 40 × 2", "TUBE60x20x2": "Труба 60 × 20 × 2",
          "S235-4": "Лист S235 4", "S235-2": "Лист S235 2", "STONE38": "Кварцевый агломерат 38",
          "BEAM45x95": "Брус строганый 45 × 95", "BEAM45x145": "Брус строганый 45 × 145", "PINE20": "Мебельный щит сосна 20",
          "PLY9": "Фанера 9", "TUBE40x20x2": "Труба 40 × 20 × 2", "LDSP10": "ЛДСП 10"}
LED = (255, 210, 150)


def n_(x):
    return f"{x:g}".replace(".", ",")


def fin_ru(f, kind="board"):
    m = materials()
    if f in m["colors"]:
        return f"«{m['colors'][f]['name']}»"
    if kind in ("tube", "plate") and f in m["metal"]:
        return f"порошок «{m['metal'][f]['name']}»"
    return {"INNER": "белый", "black": "чёрный", "G": "серый", "WT": "«Камень бежевый» (кандидат)",
            "QZ": "светло-серый (кандидат)", "groove": "рифлёная, эмаль в цвет",
            "raw": "без покрытия", "steel": "сталь"}.get(f, f)


def palette(p):
    m = materials()
    f = p["finish"]
    if p["material"] == "LED":
        return LED
    if p["kind"] in ("tube", "plate"):
        return m["metal"][f]["rgb"] if f in m["metal"] else (60, 60, 62)
    if f == "groove":
        return (90, 80, 70)
    if f == "WT":
        return (205, 190, 168)
    if f == "raw":
        return (214, 186, 140)
    if f in ("beige", "grey") and p["kind"] in ("buy", "board"):
        return m["fabric"][f]["rgb"] if f in m.get("fabric", {}) else (200, 190, 175)
    if f == "QZ":
        return (214, 212, 206)
    if p["material"] == "APPL":
        return {"black": (28, 28, 30), "steel": (182, 184, 186), "white": (232, 233, 235)}.get(f, (60, 60, 62))
    if f in m["colors"]:
        return m["colors"][f]["rgb"]
    return {"black": (34, 34, 36), "INNER": (236, 234, 229), "steel": (180, 180, 182), "white": (246, 246, 244)}.get(f, (150, 150, 152))


# ===================================================================== подготовка снимка
def make(sku, options=None):
    if sku in KX.MODULES:
        nm, fn, dflt = KX.MODULES[sku]
        o = {**dflt, **(options or {})}
        s = snapshot(fn(o).design())
        s["product"] = nm
        for p in s["parts"]:
            p["rgb"] = list(palette(p))
        return s
    if sku in KX.KITCHENS:
        o = {**default_options(sku), **(options or {})}
        keys = {a["key"] for a in products()[sku]["axes"]}
        o = {k: (int(v) if isinstance(v, str) and v.isdigit() else v) for k, v in o.items() if k in keys}
        s = snapshot(KX.kitchen(sku, KX.KITCHENS[sku], o).design())
        s["product"] = KX.KITCHENS[sku]
        for p in s["parts"]:
            p["rgb"] = list(palette(p))
        return s
    o = {**default_options(sku), **(options or {})}
    keys = {a["key"] for a in products()[sku]["axes"]}
    o = {k: v for k, v in o.items() if k in keys}
    for k, v in list(o.items()):
        if isinstance(v, str) and v.isdigit():
            o[k] = int(v)
    s = snapshot(build(sku, o))
    s["product"] = MODELS[sku][0]
    for p in s["parts"]:
        p["rgb"] = list(palette(p))
    return s


def signature(s, p):
    hs = sorted((h["kind"], h["d"], h["depth"], h["dir"], round(h["x"] - p["x0"], 1), round(h["y"] - p["y0"], 1),
                 round(h["z"] - p["z0"], 1)) for h in s["holes"] if h["part"] == p["id"])
    dims = (round(p["x1"] - p["x0"], 2), round(p["y1"] - p["y0"], 2), round(p["z1"] - p["z0"], 2))
    return (p["kind"], p["unit"], p["material"], p["finish"], dims, tuple(hs), tuple(sorted(s["derived"].get("parts_ext", {})
                                                                                            .get(p["id"], {}).get("edges", {}).items())))


ORDER = {"carcass": 0, "top": 1, "shelves": 2, "fronts": 3, "interior": 4, "screen": 5, "frame": 6, "base": 7}


def positions(s):
    """Позиции: одинаковые детали (размер, материал, отверстия, кромка) — одна позиция; покупные — после."""
    groups = {}
    for p in s["parts"]:
        if p["kind"] not in ("board", "tube", "plate"):
            continue
        groups.setdefault(signature(s, p), []).append(p["id"])
    def key(item):
        sig, ids = item
        p = next(q for q in s["parts"] if q["id"] == ids[0])
        return ({"board": 0, "plate": 2, "tube": 1}[p["kind"]], ORDER.get(p["group"], 9), p["unit"], ids[0])
    pos, rep = {}, []
    for i, (sig, ids) in enumerate(sorted(groups.items(), key=key), 1):
        for pid in ids:
            pos[pid] = i
        rep.append((i, ids))
    nb = len(rep)
    hpos = {h["id"]: nb + j for j, h in enumerate(s["hardware"], 1)}
    return pos, rep, hpos


def view_dirs(s, p):
    """Нормаль вида (к смотрящему) и «вверх» для деталировки: смотрим на пласть с большинством отверстий."""
    sz = {"x": p["x1"] - p["x0"], "y": p["y1"] - p["y0"], "z": p["z1"] - p["z0"]}
    th = min(sz, key=sz.get)
    cnt = {"+": 0, "-": 0}
    for h in s["holes"]:
        if h["part"] == p["id"] and h["dir"][1] == th:
            cnt[h["dir"][0]] += 1
    n = ("-" if cnt["+"] >= cnt["-"] else "+") + th
    if any(c_.get("draw") and c_["part"] == p["id"] for c_ in s["derived"].get("cutouts", [])):
        n = "+z"
    up = "+z" if th != "z" else "+y"
    return n, up


# ===================================================================== листы
class Ctx:
    def __init__(self, s, total, sheetno):
        self.s, self.total, self.no = s, total, sheetno
        self.pos, self.rep, self.hpos = positions(s)


def _is_new(s):
    return s["sku"] in models_new.NEW


def cfg_ru(s, short=False):
    """Конфигурация словами (только новые модели; у 36 базовых формат прежний)."""
    o = s["options"]
    if not _is_new(s):
        return " · ".join(f"{k}={v}" for k, v in o.items())
    ax = {a["key"]: a for a in products()[s["sku"]]["axes"]}
    out = []
    for k, v in o.items():
        if k == "color":
            out.append("цвет " + fin_ru(v))
        elif k in ("width", "height", "depth"):
            if not short:
                out.append(f"{ax[k]['label'].lower()} {v}")
        else:
            lab = ax.get(k, {}).get("labels", {}).get(str(v), str(v))
            out.append(lab.lower() if short else f"{ax[k]['label'].lower()}: {lab.lower()}")
    return " · ".join(out)


def stamp_for(s):
    o = s["options"]
    cfg = cfg_ru(s, short=True)
    d = s["derived"]
    return {"product": f"{s['product']} {d['width']:g} × {d['depth']:g} × {d['height']:g}"[:44], "doc": f"{s['sku']}.{s['rev']}",
            "rev": s["rev"], "hash": s["hash"], "config": f"{s['sku']} · {cfg}"[:70 if not _is_new(s) else 86],
            "status": "ИНЖЕНЕРНОЕ ПРЕДЛОЖЕНИЕ R01E — НЕ ДЛЯ ИЗГОТОВЛЕНИЯ: открытые вопросы на последнем листе"}


def _scale(*need, extra=()):
    for sc in sorted((2.5, 5, 10, 15, 20, 25, 40, 50) + tuple(extra)):
        if all(a / sc <= b for a, b in need):
            return sc
    return 50


def _proj(view, s, proj, only=None, phantom=None, fill="white"):
    key = {"front": lambda p: -p["y0"], "side": lambda p: p["x1"], "plan": lambda p: p["z1"]}[proj]
    uv = {"front": ("x0", "z0", "x1", "z1"), "side": ("y0", "z0", "y1", "z1"), "plan": ("x0", "y0", "x1", "y1")}[proj]
    for p in sorted(s["parts"], key=key):
        if p["kind"] in ("context",) or (only and not only(p)):
            continue
        st = PHANTOM if (phantom and phantom(p)) else (HID if p["kind"] == "buy" else (THIN if p["kind"] == "buy_part" else VIS))
        view.rect(p[uv[0]], p[uv[1]], p[uv[2]], p[uv[3]], st, fill=None if st is PHANTOM else fill)


def bbox(s, kinds=("board", "tube", "plate", "buy", "module")):
    ps = [p for p in s["parts"] if p["kind"] in kinds]
    return {k: (min(p[k + "0"] for p in ps), max(p[k + "1"] for p in ps)) for k in "xyz"}


def sheet_general(c):
    s = c.s
    sh = Sheet("Общий вид", stamp_for(s), c.no["general"], c.total, "—")
    img = __import__("render").render(to_model(s), az=-35, el=22, size=(700, 700), ss=2)["clay"]
    buf = np.asarray(img.convert("RGB"))
    h = 118
    sh.ax.imshow(buf, extent=(30, 30 + h * buf.shape[1] / buf.shape[0], 155, 155 + h), zorder=0)
    sh.view_title(30, 278, "Изображение изделия (без масштаба)")
    bb = bbox(s)
    d = s["derived"]
    W, D, H = bb["x"][1] - bb["x"][0], bb["y"][1] - bb["y"][0], bb["z"][1] - bb["z"][0]
    sc = _scale((2 * W + D, 150), (H, 70), (D, 70))
    x0 = 32
    vf = View(sh, sc, (x0, 70), (bb["x"][0], bb["z"][0]))
    _proj(vf, s, "front", only=lambda p: p["group"] != "interior")
    a, b = vf.p(bb["x"][0], bb["z"][0]), vf.p(bb["x"][1], bb["z"][1])
    sh.dim_h(a[0], b[0], b[1], b[1], b[1] + 6, n_(W))
    sh.dim_v(a[1], b[1], a[0], a[0], a[0] - 6, n_(H))
    sh.text(a[0], 62, "Вид спереди", size=7.6, weight="bold", va="top")
    xs = b[0] + 18
    vs = View(sh, sc, (xs, 70), (bb["y"][0], bb["z"][0]))
    _proj(vs, s, "side", only=lambda p: p["group"] != "interior")
    a2, b2 = vs.p(bb["y"][0], 0), vs.p(bb["y"][1], bb["z"][1])
    sh.dim_h(a2[0], b2[0], b2[1], b2[1], b2[1] + 6, n_(D))
    sh.text(a2[0], 62, "Вид слева", size=7.6, weight="bold", va="top")
    xt = b2[0] + 18
    vt = View(sh, sc, (xt, 70), (bb["x"][0], -bb["y"][1]))
    for p in sorted(s["parts"], key=lambda p: p["z1"]):
        if p["kind"] in ("context", "buy_part") or p["group"] == "interior":
            continue
        vt.rect(p["x0"], -p["y1"], p["x1"], -p["y0"], VIS, fill="white")
    sh.text(xt, 62, "Вид сверху", size=7.6, weight="bold", va="top")
    sh.text(32, 56, f"Масштаб видов 1:{n_(sc)}", size=6.2, va="top")
    hw = {h["id"]: h for h in s["hardware"]}
    rows = [["Обозначение", f"{s['sku']} · {s['rev']}"], ["Конфигурация", cfg_ru(s, short=_is_new(s))],
            *([["Высоты", "; ".join(f"{t} {n_(v)}" for t, v in d["height_marks"])]] if d.get("height_marks") else []),
            ["Габарит Ш × Г × В", f"{n_(d['width'])} × {n_(d['depth'])} × {n_(d['height'])} мм" +
             (" (с ручками / выступами — по видам)" if abs(D - d["depth"]) > 1 else "")]]
    mats = {}
    for p in s["parts"]:
        if p["kind"] in ("board", "tube", "plate"):
            mats.setdefault(f"{MAT_RU.get(p['material'], p['material'])} {fin_ru(p['finish'], p['kind'])}", 0)
    for k in list(mats)[:7]:
        rows.append(["Материал", k])
    if "SLIDES" in hw:
        rows.append(["Направляющие", hw["SLIDES"]["spec"][:60 if not _is_new(s) else 90]])
    if "HINGE" in hw:
        rows.append(["Петли", "кандидат: " + hw["HINGE"]["spec"][:48]] if not _is_new(s) else
                    ["Петли", hw["HINGE"]["spec"][:90]])
    if _is_new(s) and "LEGK" in hw:
        rows.append(["Опоры", hw["LEGK"]["spec"][:90]])
    rows += [["Масса (оценка)", f"≈ {d['mass_kg']} кг"], ["Снимок конфигурации", s["hash"]]]
    sh.text(232, 282, "Материалы и характеристики", size=8.5, weight="bold", va="top")
    y = sh.table(232, 276, ["Параметр", "Значение"], rows, [40, 138], row_h=5.6, size=6.1)
    sh.text(232, y - 5, "Состав комплекта", size=8.5, weight="bold", va="top")
    per = max(7, -(-len(c.contents) // 2))
    for i, t in enumerate(c.contents):
        sh.text(234 + (i // per) * 92, y - 11.5 - (i % per) * 4.6, t, size=6.2)
    return sh


def sheet_assembly(c):
    s = c.s
    sh = Sheet("Разрезы и размеры" if _is_new(s) else "Сборочный чертёж", stamp_for(s),
               c.no.get("sections", c.no["assembly"]), c.total, "—")
    bb = bbox(s, ("board", "tube", "plate"))
    W, D, H = bb["x"][1] - bb["x"][0], bb["y"][1] - bb["y"][0], bb["z"][1] - bb["z"][0]
    sc = _scale((W, 150), (H, 108), (D, 110), extra=(30,) if _is_new(s) else ())
    vf = View(sh, sc, (40, 160), (bb["x"][0], bb["z"][0]))
    _proj(vf, s, "front", only=lambda p: p["kind"] in ("board", "tube", "plate") and p["group"] != "fronts")
    for p in s["parts"]:
        if p["group"] == "fronts" and p["kind"] == "board":
            vf.rect(p["x0"], p["z0"], p["x1"], p["z1"], PHANTOM)
    a, b = vf.p(bb["x"][0], bb["z"][0]), vf.p(bb["x"][1], bb["z"][1])
    sh.dim_h(a[0], b[0], b[1], b[1], b[1] + 7, n_(W))
    sh.dim_v(a[1], b[1], a[0], a[0], a[0] - 9, n_(H))
    sh.text(a[0], a[1] - 8, f"Вид спереди, М 1:{n_(sc)}", size=7.2, weight="bold", va="top")
    sh.text(a[0], a[1] - 12.5, "фасады — штрихпунктир", size=6.0, va="top")
    # позиции: по одной выноске на позицию (первые 12 по порядку), выноски в столбец справа
    seen, items = set(), []
    for p in s["parts"]:
        ps = c.pos.get(p["id"])
        if ps and ps not in seen and p["group"] != "fronts":
            u, v = (p["x0"] + p["x1"]) / 2, (p["z0"] + p["z1"]) / 2
            if bb["x"][0] <= u <= bb["x"][1]:
                seen.add(ps); items.append((ps, u, v))
    items = items[:12]
    xr = b[0] + 14
    for i, (ps, u, v) in enumerate(sorted(items, key=lambda t: -t[2])):
        ty = b[1] - i * min(8.5, (b[1] - a[1]) / max(1, len(items) - 1)) if len(items) > 1 else b[1]
        sh.balloon(*vf.p(u, v), xr, ty, ps, r=3.0)
    # разрез по оси первого ящика или по середине
    drs = s["derived"].get("drawers", [])
    if drs and not drs[0].get("rotated"):
        bx = next(q for q in s["parts"] if q["id"] == drs[0]["box"][0])
        cut = bx["x1"] + 40
    elif _is_new(s) and s["derived"].get("cut_x"):
        cut = s["derived"]["cut_x"]
    else:
        cut = (bb["x"][0] + bb["x"][1]) / 2
    ox = max(xr + 22, a[0] + 62)
    va = View(sh, sc, (ox, 160), (bb["y"][0] - 30, bb["z"][0]))
    section(va, s, "x", cut, "+y", "+z", (bb["y"][0] - 30, bb["y"][1] + 2, bb["z"][0] - 2, bb["z"][1] + 2), frame=False)
    a3, b3 = va.p(bb["y"][0], bb["z"][0]), va.p(bb["y"][1], bb["z"][1])
    sh.dim_h(a3[0], b3[0], b3[1], b3[1], b3[1] + 7, n_(D))
    lv = s["derived"].get("levels") if _is_new(s) else None
    if lv:                                      # цепочка высот: опоры / секция / антресоль
        for z0_, z1_ in zip(lv, lv[1:]):
            ya_, yb_ = va.p(0, z0_)[1], va.p(0, z1_)[1]
            sh.dim_v(ya_, yb_, b3[0], b3[0], b3[0] + 8, n_(z1_ - z0_))
    sh.text(a3[0] - 6, a3[1] - 8, f"Разрез А–А (X = {n_(round(cut, 1))})", size=7.2, weight="bold", va="top")
    sh.front_arrow(a3[0] - 10, a3[1] + 18, "ПЕРЕД", -1, 0)
    xa = vf.p(cut, 0)[0]
    sh.line(xa, a[1] - 3, xa, b[1] + 3, CTR)
    sh.text(xa + 1.5, b[1] + 3.5, "А", size=7.5, weight="bold")
    # план
    vp = View(sh, sc, (40, 62), (bb["x"][0], bb["y"][0]))
    zc = min(60, bb["z"][0] + 20) if bb["z"][0] < 40 else bb["z"][0] + 10   # подвесные — над низом рамы
    for p in sorted(s["parts"], key=lambda p: p["z1"]):
        if p["kind"] in ("board", "tube", "plate", "buy") and p["z0"] < zc < p["z1"]:
            a4, b4 = vp.p(p["x0"], p["y0"]), vp.p(p["x1"], p["y1"])
            sh.hatch(a4[0], a4[1], b4[0], b4[1], "xxxx" if p["kind"] == "buy" else "////")
    vp.rect(bb["x"][0], bb["y"][0], bb["x"][1], bb["y"][1], PHANTOM)
    a5 = vp.p(bb["x"][0], bb["y"][0])
    sh.text(a5[0], a5[1] - 3, f"Сечение Б–Б (Z = {n_(zc)}), вид сверху, перед внизу", size=7.2, weight="bold", va="top")
    tt = c.tech_req
    sh.text(250, 136, "Технические требования", size=8.0, weight="bold")
    for i, t in enumerate(tt):
        sh.text(250, 129 - i * 4.6, t, size=6.1)
    return sh


def _kfoot(r):
    """Плановый контур модуля по записи компоновки."""
    x, y, w, d = r["x"], r["y"], r["w"], r["d"]
    if r["rot"] == 0:
        return x, y, x + w, y + d
    if r["rot"] == 90:
        return x - d, y, x, y + w
    return x, y - d, x + w, y


def _kz(r):
    code = r["code"]
    if code.startswith("KL"):
        return r["z"], r["z"] + r["h"]
    if code[3] == "W":
        return r["z"], r["z"] + r["h"]
    return r["z"] + (120 if code.startswith("KG") else 100), r["h"]


def sheet_kitchen(c):
    s = c.s
    K = s["derived"]["kitchen"]["modules"]
    sh = Sheet("План, развёртки, модули", stamp_for(s), c.no["assembly"], c.total, "см. виды")
    made = [p for p in s["parts"] if p["kind"] in ("board",)]
    xs = [v for r in K for v in _kfoot(r)[0::2]] + [p[k] for p in made for k in ("x0", "x1")]
    ys = [v for r in K for v in _kfoot(r)[1::2]] + [p[k] for p in made for k in ("y0", "y1")]
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
    # --- план
    sc = _scale((X1 - X0, 175), (Y1 - Y0, 100))
    vp = View(sh, sc, (42, 272 - (Y1 - Y0) / sc), (X0, Y0))
    for p in made:
        vp.rect(p["x0"], p["y0"], p["x1"], p["y1"], THIN)
    for r in K:
        a = _kfoot(r)
        up = r["code"][3] == "W" or r["code"].startswith("KL")
        vp.rect(*a, PHANTOM if up else VIS, fill=None if up else "#f3f1ec")
        if not up:
            cx, cy = vp.p((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
            sh.text(cx, cy, r["tag"], size=5.6, ha="center", va="center", weight="bold")
    a_, b_ = vp.p(X0, Y0), vp.p(X1, Y1)
    sh.dim_h(a_[0], b_[0], b_[1], b_[1], b_[1] + 6, n_(X1 - X0))
    sh.dim_v(a_[1], b_[1], a_[0], a_[0], a_[0] - 7, n_(Y1 - Y0))
    sh.text(30, a_[1] - 4, f"План, М 1:{n_(sc)}: сплошной — низ и колонны, штрих — верхние модули и полки; тонкий — столешницы",
            size=6.4, weight="bold", va="top")
    # --- развёртка основной стены (модули без поворота, у стены y ≥ 0)
    main = [r for r in K if r["rot"] == 0 and r["y"] >= -1]
    ex0 = min(r["x"] for r in main); ex1 = max(r["x"] + r["w"] for r in main)
    sce = _scale((ex1 - ex0, 185), (2400, 80))
    ve = View(sh, sce, (48, 66), (ex0, 0))
    _elev(sh, ve, main, s, "x")
    a2, b2 = ve.p(ex0, 0), ve.p(ex1, 2400)
    sh.dim_h(a2[0], ve.p(ex1, 0)[0], a2[1], a2[1], a2[1] - 5, n_(ex1 - ex0))
    sh.text(48, 66 + 2400 / sce + 9, f"Развёртка основной стены, М 1:{n_(sce)}", size=6.4, weight="bold")
    # --- вторая развёртка: боковой ряд (90°) или остров (180°)
    other = [r for r in K if r["rot"] != 0]
    yt = 282
    if other:
        rot = other[0]["rot"]
        if rot == 90:
            u0 = min(r["y"] for r in other); u1 = max(r["y"] + r["w"] for r in other)
            title = "Развёртка боковой стены (вид от комнаты)"
        else:
            u0 = -max(r["x"] + r["w"] for r in other); u1 = -min(r["x"] for r in other)
            title = "Остров, вид от кухни"
        sc2 = _scale((u1 - u0, 170), (2400 if rot == 90 else 900, 70 if rot == 90 else 40))
        h2 = (2400 if rot == 90 else 900) / sc2
        v2 = View(sh, sc2, (250, yt - 6 - h2), (u0, 0))
        _elev(sh, v2, other, s, "y" if rot == 90 else "-x")
        sh.text(235, yt, f"{title}, М 1:{n_(sc2)}", size=6.4, weight="bold", va="top")
        aa, bb_ = v2.p(u0, 0), v2.p(u1, 0)
        sh.dim_h(aa[0], bb_[0], aa[1], aa[1], aa[1] - 5, n_(u1 - u0))
        yt = yt - 6 - h2 - 12
    # --- таблица модулей
    rows = []
    for r in K:
        o = r["opts"]
        dec = ", ".join(f"{fin_ru(v)}" if k == "color" else f"{k}={v}" for k, v in o.items())
        rows.append([r["tag"], r["code"], r["name"], dec, f"{n_(r['w'])}"])
    sh.text(235, yt, "Модули (каждый — по своему комплекту)", size=7.2, weight="bold", va="top")
    rh = min(5.0, (yt - 8 - 64) / max(1, len(rows) + 1))
    sh.table(235, yt - 5, ["Метка", "Модуль", "Наименование", "Декор / параметры", "Ширина"], rows, [13, 22, 70, 50, 15],
             row_h=rh, size=5.4)
    return sh


def _elev(sh, v, recs, s, axis):
    for r in sorted(recs, key=lambda q: q["code"][3] == "W"):
        if axis == "x":
            u0, u1 = r["x"], r["x"] + r["w"]
        elif axis == "y":
            u0, u1 = r["y"], r["y"] + r["w"]
        else:
            u0, u1 = -(r["x"] + r["w"]), -r["x"]
        z0, z1 = _kz(r)
        st = PHANTOM if r["code"].startswith("KL") else VIS
        v.rect(u0, z0, u1, z1, st, fill="#f3f1ec")
        cx, cy = v.p((u0 + u1) / 2, (z0 + z1) / 2)
        sh.text(cx, cy, r["tag"], size=5.4, ha="center", va="center", weight="bold")
    for p in s["parts"]:
        if p["kind"] == "board" and p["group"] in ("top", "base"):
            if axis == "x" and p["x1"] - p["x0"] > p["y1"] - p["y0"] and p["y0"] > -100:
                v.rect(p["x0"], p["z0"], p["x1"], p["z1"], THIN, fill="#d8d2c6")
            elif axis == "y" and p["y1"] - p["y0"] > p["x1"] - p["x0"] and p["x0"] < 700:
                v.rect(p["y0"], p["z0"], p["y1"], p["z1"], THIN, fill="#d8d2c6")
            elif axis == "-x" and p["y0"] < -1000:
                v.rect(-p["x1"], p["z0"], -p["x0"], p["z1"], THIN, fill="#d8d2c6")
    zs = sorted({_kz(r)[k] for r in recs for k in (0, 1)} | {0})
    ux = min((r["x"] if axis == "x" else r["y"] if axis == "y" else -(r["x"] + r["w"])) for r in recs)
    a = v.p(ux, 0)
    last = -99
    for z in zs:
        pz = v.p(ux, z)[1]
        if pz - last >= 3.0:
            sh.line(a[0] - 2, pz, a[0] - 10, pz, DIM)
            sh.text(a[0] - 10.5, pz, n_(z), size=5.2, ha="right", va="center")
            last = pz


def _detail_block(c, sh, pid, x, y, sc, qty):
    s = c.s
    p = next(q for q in s["parts"] if q["id"] == pid)
    n, up = view_dirs(s, p)
    ext = s["derived"]["parts_ext"].get(pid, {})
    fr, bb = detail(sh, s, pid, x, y, sc, n, up)
    bu, bv = blank(fr, ext.get("edges", {}))
    ps = c.pos[pid]
    sh.text(x, bb[3] + 9, f"Поз. {ps}  {p['unit']} — {qty} шт.   (М 1:{n_(sc)})", size=7.0, weight="bold")
    sh.text(x, bb[3] + 4.8, f"{MAT_RU.get(p['material'], p['material'])} {fin_ru(p['finish'])} · готовый {n_(fr.Lu)} × "
            f"{n_(fr.Lv)} × {n_(fr.t)} · заготовка {n_(round(bu, 1))} × {n_(round(bv, 1))}", size=5.9)
    e = ext.get("edges", {})
    by = {}
    for f, t in e.items():
        by.setdefault(EDGE_TXT[t], []).append(NAME[f])
    sh.text(x, bb[3] + 0.8, "Кромка — " + ("; ".join(f"{k}: {', '.join(v)}" for k, v in by.items()) if e else "нет") +
            ("; текстура — стрелка" if ext.get("grain") else ""), size=5.9)
    vt = {"+x": "справа", "-x": "слева", "+y": "сзади", "-y": "спереди", "+z": "сверху", "-z": "снизу"}[n]
    c1, c2 = fr.base_corner()
    sh.text(x, y - 7.5, f"Вид {vt}; база A — {c1} / {c2}", size=5.7, va="top", style="italic")
    for cu in s["derived"].get("cutouts", []):
        if not cu.get("draw") or cu["part"] != pid:
            continue
        zc = p["z1"] if n == "+z" else p["z0"]
        u0, v0 = fr.uv(cu["x0"], cu["y0"], zc)
        u1, v1 = fr.uv(cu["x1"], cu["y1"], zc)
        ua, ub, va_, vb = min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1)
        sh.rect(x + ua / sc, y + va_ / sc, x + ub / sc, y + vb / sc, dict(lw=0.7, color=RED, ls="--"))
        sh.text(x + (ua + ub) / 2 / sc, y + (va_ + vb) / 2 / sc + 1.6, f"вырез {n_(round(ub - ua))} × {n_(round(vb - va_))}",
                size=5.2, ha="center", va="center", color=RED)
        sh.text(x + (ua + ub) / 2 / sc, y + (va_ + vb) / 2 / sc - 1.6,
                f"центр от A: {n_(round((ua + ub) / 2, 1))} / {n_(round((va_ + vb) / 2, 1))}", size=5.0, ha="center",
                va="center", color=RED)
    for g in s["derived"].get("grooves", []):
        if g["part"] != pid:
            continue
        u0, v0 = fr.uv(g["x0"], g["y0"], g["z0"])
        u1, v1 = fr.uv(g["x1"], g["y1"], g["z1"])
        ua, ub, va_, vb = min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1)
        sh.rect(x + ua / sc, y + va_ / sc, x + ub / sc, y + vb / sc, dict(lw=0.7, color=RED, ls="--"))
    cus = [cu for cu in s["derived"].get("cutouts", []) if cu.get("draw") and cu["part"] == pid]
    cus += [g for g in s["derived"].get("grooves", []) if g["part"] == pid]
    rows = hole_rows(s, pid, fr, lambda h: NODE.get(h["kind"], ""))
    yb = y - 12
    for i, cu in enumerate(cus):
        sh.text(x, y - 12 - i * 3.6, "• " + cu["note"], size=5.3, va="top", color=RED)
    y -= 3.6 * len(cus)
    if rows:
        yb = sh.table(x, y - 12, ["Ø", "Глуб.", "Где", "Кол.", "Назначение", "Узел"], rows[:9], [10, 13, 50, 8, 64, 9],
                      row_h=4.4, size=5.4)
        if len(rows) > 9:
            sh.text(x, yb - 1.5, f"… ещё {len(rows) - 9} групп отверстий — по координатам на виде", size=5.4, va="top")
    return bb, yb




def _block_h(Lv, sc, nrows):
    return Lv / sc + 40 + (4.4 * (min(9, nrows) + 1) if nrows else 0) + (3 if nrows > 9 else 0)


def _pick_sc(Lu, Lv, nrows, limit):
    for sc in (2.5, 5, 10, 15, 20, 25, 40, 50):
        if Lu / sc + 24 <= 172 and _block_h(Lv, sc, nrows) <= limit:
            return sc
    return 50


def plan_details(s, pos, rep):
    """Раскладка уникальных плитных деталей: лист = 2 колонки; колонка — две детали или одна крупная
    (если в половине колонки масштаб мельче 1:20). Возвращает листы: [(блок, x, y_верх, предел_высоты), ...]."""
    blocks = []
    for ps, ids in rep:
        p = next(q for q in s["parts"] if q["id"] == ids[0])
        if p["kind"] != "board":
            continue
        n, up = view_dirs(s, p)
        fr = Frame(p, n, up)
        nrows = len(hole_rows(s, p["id"], fr))
        blocks.append((ps, ids, fr.Lu, fr.Lv, nrows))
    cols, open_pair = [], None
    for blk in blocks:
        _, _, Lu, Lv, nr = blk
        half, full = _pick_sc(Lu, Lv, nr, 92), _pick_sc(Lu, Lv, nr, 214)
        if half > 20 and full < half:
            cols.append(["tall", blk])
        elif open_pair is not None:
            open_pair.append(blk); open_pair = None
        else:
            open_pair = ["pair", blk]; cols.append(open_pair)
    sheets = []
    for i in range(0, len(cols), 2):
        pl = []
        for j, col in enumerate(cols[i:i + 2]):
            cx = 30 if j == 0 else 225
            if col[0] == "tall":
                pl.append((col[1], cx, 272, 242 if j == 0 else 214))
            else:
                pl.append((col[1], cx, 272, 114))
                if len(col) > 2:
                    pl.append((col[2], cx, 152, 140 if j == 0 else 92))
        sheets.append(pl)
    return sheets


def sheet_details(c, placed, k):
    s = c.s
    names = ", ".join(str(b[0][0]) for b in sorted(placed, key=lambda q: q[0][0]))
    sh = Sheet(f"Детали, поз. {names}", stamp_for(s), c.no["details"][k], c.total, "по блокам")
    for (ps, ids, Lu, Lv, nrows), cx, ctop, lim in placed:
        sc = _pick_sc(Lu, Lv, nrows, lim)
        y = ctop - 26 - Lv / sc
        _detail_block(c, sh, ids[0], cx + 4, y, sc, len(ids))
    sh.text(25, 284, "Отверстия — от базы A по координатам на виде; штрих — отверстие в торец или с обратной пласти. "
            "Детали с одинаковой позицией одинаковые.", size=6.0, va="top", color=RED)
    return sh


def sheet_metal(c):
    s = c.s
    sh = Sheet("Металл: рамы и детали", stamp_for(s), c.no["metal"], c.total, "—")
    tubes = [p for p in s["parts"] if p["kind"] == "tube"]
    plates = [p for p in s["parts"] if p["kind"] == "plate"]
    rows, seen = [], {}
    for p in tubes + plates:
        ps = c.pos[p["id"]]
        seen.setdefault(ps, []).append(p)
    for ps in sorted(seen):
        ps_ = seen[ps]
        p = ps_[0]
        if p["kind"] == "tube":
            L = p[p["axis"] + "1"] - p[p["axis"] + "0"]
            size = f"L = {n_(L)}, торцы 90°"
        else:
            a, b_, t = sorted([p["x1"] - p["x0"], p["y1"] - p["y0"], p["z1"] - p["z0"]], reverse=True)
            size = f"{n_(a)} × {n_(b_)} × {n_(t)}"
        nh = len([h for h in s["holes"] if h["part"] == p["id"]])
        rows.append([str(ps), p["unit"], MAT_RU.get(p["material"], p["material"]), size, str(len(ps_)), str(nh), fin_ru(p["finish"], p["kind"])])
    sh.text(25, 283, "Детали из трубы и листа", size=8.2, weight="bold", va="top")
    y = sh.table(25, 277, ["Поз.", "Наименование", "Профиль / лист", "Размер", "Кол.", "Отв./шт", "Покрытие"], rows[:24],
                 [11, 58, 36, 50, 10, 14, 44], row_h=5.0, size=5.9)
    lens = [round(p[p["axis"] + "1"] - p[p["axis"] + "0"], 1) for p in tubes]
    by = {}
    for p in tubes:
        by.setdefault(p["material"], []).append(round(p[p["axis"] + "1"] - p[p["axis"] + "0"], 1))
    yy = y - 6
    sh.text(25, yy, "Раскрой труб (хлыст 6000, пропил 3, торцовка 10 × 2)", size=8.0, weight="bold", va="top")
    for i, (m, L) in enumerate(by.items()):
        bars = cut_plan(L)
        sh.text(27, yy - 6 - i * 4.6, f"{MAT_RU.get(m, m)}: {len(L)} дет., {len(bars)} хлыст(а); остатки "
                f"{', '.join(n_(b['rest']) for b in bars)}", size=6.0, va="top")
    # рамы: вид в плоскости рамы
    frs = s["derived"].get("frames", [])
    x, ytop = 255, 283
    sh.text(x, ytop, "Сварные узлы (вид в плоскости рамы)", size=8.0, weight="bold", va="top")
    shown = 0
    yy2 = ytop - 10
    for f in frs:
        ps_ = [q for q in s["parts"] if q["id"] in f["tubes"]]
        if shown >= 3:
            break
        dx = max(q["x1"] for q in ps_) - min(q["x0"] for q in ps_)
        dy = max(q["y1"] for q in ps_) - min(q["y0"] for q in ps_)
        dz = max(q["z1"] for q in ps_) - min(q["z0"] for q in ps_)
        if dz < 0.5 * max(dx, dy) and dx > dy:
            ua, va_, um, vm = "x", "y", min(q["x0"] for q in ps_), min(q["y0"] for q in ps_)
            lu, lv = dx, dy
        else:
            ua = "y" if dy >= dx else "x"
            va_, um, vm = "z", min(q[ua + "0"] for q in ps_), 0
            lu, lv = (dy if ua == "y" else dx), max(q["z1"] for q in ps_)
        sc = _scale((lu, 140), (lv, 52))
        if yy2 - lv / sc - 12 < 60:
            break
        v = View(sh, sc, (x, yy2 - lv / sc - 6), (um, vm))
        for q in ps_:
            v.rect(q[ua + "0"], q[va_ + "0"], q[ua + "1"], q[va_ + "1"], VIS, fill="white")
        a, b_ = v.p(um, vm), v.p(um + lu, vm + lv)
        sh.dim_h(a[0], b_[0], b_[1], b_[1], b_[1] + 3, n_(round(lu, 1)), size=5.8)
        sh.dim_v(a[1], b_[1], b_[0], b_[0], b_[0] + 5, n_(round(lv, 1)), size=5.8)
        sh.text(x, a[1] - 2, f"{f['name']} (М 1:{n_(sc)}); швы — по контуру стыков, угловые, катет 2 (В-24)", size=5.8, va="top")
        yy2 = a[1] - 10
        shown += 1
    sh.text(255, 66, "Сварка — в кондукторе; разность диагоналей рамы ≤ 2; плоскость опоры столешницы ≤ 0,5.", size=6.0)
    sh.text(255, 61.5, "Порошковая окраска после сварки и зачистки; отверстия — до окраски, резьба — после (В-24).", size=6.0)
    return sh


def sheet_nodes(c):
    s = c.s
    sh = Sheet("Узлы", stamp_for(s), c.no["nodes"], c.total, "1:1")
    letters = []
    for h in s["holes"]:
        L = NODE.get(h["kind"])
        if L and L not in [x[0] for x in letters]:
            letters.append((L, h))
    if _is_new(s):                               # Н — соединение антресоли (если есть), Е — в «остальные»
        mez = next((h for h in s["holes"] if h["kind"] == "screw_face" and h.get("fastener") == "SCREW-4x25M"), None)
        if mez:
            letters = [(L, mez if L == "Н" else h) for L, h in letters]
        pref = "АБВГЖИКНДЛМПРЕ"
        letters.sort(key=lambda t: pref.index(t[0]) if t[0] in pref else 99)
    else:
        letters.sort(key=lambda t: "АБВГДЕЖИКЛМНПР".index(t[0]))
    cells = [(28 + (i % 4) * 98, 182 if i < 4 else 72) for i in range(8)]
    parts = {p["id"]: p for p in s["parts"]}
    for (L, h), (x, y) in zip(letters[:8], cells):
        ax = h["dir"][1]
        others = [a for a in "xyz" if a != ax]
        cut = others[0] if ax != "z" else "y"
        if ax == "z":
            cut = "x" if (parts[h["part"]]["x1"] - parts[h["part"]]["x0"]) > (parts[h["part"]]["y1"] - parts[h["part"]]["y0"]) else "y"
        vax = next(a for a in "xyz" if a not in (ax, cut))
        uax, vv = ("+" + ax, "+" + vax)
        if ax == "z":
            uax, vv = "+" + vax, "+z"
        u_c = h[uax[1]]
        v_c = h[vv[1]]
        win = (u_c - 38, u_c + 38, v_c - 38, v_c + 38)
        v = View(sh, 1, (x, y), (win[0], win[2]))
        section(v, s, cut, h[cut], uax, vv, win)
        tit, notes = NODE_TXT[L]
        if L == "Ж" and any(r.get("sys") == "movento" for r in s["derived"].get("drawers", [])):
            tit = "Профиль Blum MOVENTO 760H"
            notes = ["Саморез Blum 609.1500 Ø3,5 × 15 по", "разметке, без сверления; ось — над", "низом профиля 38 (39, если профиль",
                     "до сборки корпуса); каталог 2024 с. 428."]
        if L == "Н" and h.get("fastener") == "SCREW-4x25M":
            E = next((parts[q["part"]] for q in s["holes"] if q["joint"] == h["joint"] and q["kind"] == "pilot"), None)
            tit = "Антресоль на секцию"
            notes = [f"Саморез 4 × 25 снизу вверх (↑): головка в", f"крышке поз. {c.pos.get(h['part'], '—')} — Ø4,5 насквозь,",
                     "зенковка снизу; вход в дно антресоли", f"поз. {c.pos.get(E['id'], '—') if E else '—'} — 9, засверловка Ø3 гл. 8,",
                     "остаток 7. Доступ — изнутри секции."]
        sh.text(x, y + 82, f"{L} · {tit}", size=6.9, weight="bold")
        sh.text(x, y + 78.2, f"{cut.upper()} = {n_(h[cut])}; деталь поз. {c.pos.get(h['part'], '—')}", size=5.4, color="#444")
        for i, t in enumerate(notes):
            sh.text(x, y - 2.5 - i * 3.7, t, size=5.6, va="top")
    sh.text(25, 284, "Разрезы по снимку конфигурации через представительное отверстие узла: штриховка — рассечённые детали, "
            "белые прямоугольники — отверстия; xxx — покупные.", size=6.0, va="top")
    if len(letters) > 8:
        t = "Остальные узлы: " + ", ".join(f"{L} — {NODE_TXT[L][0]}" for L, _ in letters[8:]) + " — по таблицам отверстий деталей."
        for i, ln in enumerate(textwrap.wrap(t, 95)):
            sh.text(25, 48 - i * 4, ln, size=6.0)
    return sh


def spec_rows(c):
    s = c.s
    rows = [["", "", "Детали", "", "", "", ""]]
    for ps, ids in c.rep:
        p = next(q for q in s["parts"] if q["id"] == ids[0])
        if p["kind"] == "tube":
            L = p[p["axis"] + "1"] - p[p["axis"] + "0"]
            size, blk = f"L = {n_(L)}", ""
        else:
            a, b_, t = sorted([p["x1"] - p["x0"], p["y1"] - p["y0"], p["z1"] - p["z0"]], reverse=True)
            size = f"{n_(a)} × {n_(b_)} × {n_(t)}"
            blk = ""
            if p["kind"] == "board":
                n, up = view_dirs(s, p)
                fr = Frame(p, n, up)
                bu, bv = blank(fr, s["derived"]["parts_ext"].get(p["id"], {}).get("edges", {}))
                blk = f"{n_(round(bu, 1))} × {n_(round(bv, 1))}"
        rows.append([str(ps), p["unit"], str(len(ids)), f"{MAT_RU.get(p['material'], p['material'])} {fin_ru(p['finish'], p['kind'])}",
                     size, blk, ""])
    K = s["derived"].get("kitchen", {}).get("modules", [])
    if K:
        rows.append(["", "", "Модули — по своим комплектам", "", "", "", ""])
        cnt = {}
        for r in K:
            key = (r["code"], tuple(sorted(r["opts"].items())))
            cnt.setdefault(key, []).append(r)
        for i, ((code, _), rs) in enumerate(cnt.items(), 1):
            r = rs[0]
            dec = ", ".join(fin_ru(v) if k == "color" else f"{k}={v}" for k, v in r["opts"].items())
            rows.append([f"М{i}", f"{code} — {r['name']}", str(len(rs)), f"комплект {code} R01E; {dec}; метки {', '.join(q['tag'] for q in rs)}",
                         f"{n_(r['w'])} × {n_(r['d'])} × {n_(r['h'])}", "", "модуль"])
    rows.append(["", "", "Покупные изделия", "", "", "", ""])
    for h in s["hardware"]:
        rows.append([str(c.hpos[h["id"]]), h["name"], f"{n_(round(h['qty'], 2))} {h.get('uom', 'шт')}", h["spec"], "",
                     "", h["status"]])
    return rows


def sheet_spec(c, chunk, k, last):
    s = c.s
    sh = Sheet("Спецификация" + (", кромка, раскрой" if last else ""), stamp_for(s), c.no["spec"][k], c.total, "—")
    y = sh.table(25, 283, ["Поз.", "Наименование", "Кол.", "Материал / артикул", "Готовый", "Заготовка", "Статус"], chunk,
                 [11, 82, 16, 142, 46, 32, 40], row_h=5.0, size=5.6)
    if last:
        d = s["derived"]
        sh.text(25, y - 5, "Кромка", size=8, weight="bold", va="top")
        sh.text(27, y - 11, f"ABS 2 в цвет — {n_(d['edge_abs2_m'])} м; ПВХ 0,4 — {n_(d['edge_04_m'])} м (без запаса). Заготовка = "
                "готовый − кромка, без припуска на фуговку (В-2).", size=6.1, va="top")
        b = bom(s)
        sh.text(25, y - 18, "Расход плиты — оценка по листам 2800 × 2070 (карту строит программа раскроя цеха)", size=8,
                weight="bold", va="top")
        for i, r in enumerate(b["sheets"][:8]):
            over = f"; не помещаются: {', '.join(r['oversize'])}" if r["oversize"] else ""
            sh.text(27, y - 24 - i * 4.4, f"{MAT_RU.get(r['material'], r['material'])} {fin_ru(r['finish'])}: деталей {r['parts']}, "
                    f"{n_(r['area_m2'])} м² — {r['sheets']} лист(а){over}", size=6.0, va="top")
    return sh


def _ranges(nums):
    nums = sorted(nums)
    return f"{nums[0]}–{nums[-1]}" if len(nums) > 1 and nums == list(range(nums[0], nums[-1] + 1)) else ", ".join(map(str, nums))


def control_new(c):
    """Порядок сборки и контроль новых моделей: только применимые шаги, ссылки К — из таблицы."""
    s = c.s
    d = s["derived"]
    H = {h["id"]: h for h in s["hardware"]}
    parts = s["parts"]
    rows = [["К1", "Размеры деталей после кромки", "рулетка, штангенциркуль", f"по листам {c.detail_ref}; ±0,5 (В-10)"]]
    drs = d.get("drawers", [])
    if drs:
        if drs[0].get("sys") == "movento":
            rows.append([f"К{len(rows) + 1}", "Стенки и дно короба по ширине; паз под дно (до сборки)", "штангенциркуль",
                         f"стенки {n_(drs[0]['inner_w'])}, дно {n_(drs[0]['inner_w'] + 10)}: −0,5 / +0; паз 16 × 5"
                         " на 13 от низа — дно входит без люфта"])
        else:
            rows.append([f"К{len(rows) + 1}", "Стенки и дно короба по ширине (до сборки)", "штангенциркуль",
                         f"{n_(drs[0]['inner_w'])} −0,5 / +0 — иначе короб выйдет за К ниже"])
    groups = {}
    for cc in d.get("carcasses", []):
        lab = cc["label"]
        kind = lab.rstrip("0123456789 ").strip()
        key = (kind, round(cc["x1"] - cc["x0"], 1), round(cc["z1"] - cc["z0"], 1))
        groups.setdefault(key, []).append(int(lab.split()[-1]) if lab.split()[-1].isdigit() else 0)
    diag = []
    for (kind, w, h), ns in groups.items():
        name = {"секция": "Секции", "антресоль": "Антресоли"}.get(kind, kind.capitalize())
        k = f"К{len(rows) + 1}"
        rows.append([k, f"{name} {_ranges(ns)}: диагонали по фасадной плоскости", "рулетка",
                     f"{n_(w)} × {n_(h)}; разность ≤ 1,5"])
        diag.append(k)
    if drs:
        rows.append([f"К{len(rows) + 1}", "Короб: внутренняя ширина спереди и сзади", "штангенциркуль",
                     f"{n_(drs[0]['inner_w'])} +0 / −1,5 (Blum LW − 42)"])
    inner = sorted([p for p in parts if p["name"].startswith("Передняя панель внутреннего")], key=lambda p: (p["x0"], p["z0"]))
    gaps = sorted({round(b["z0"] - a["z1"], 1) for a, b in zip(inner, inner[1:]) if abs(a["x0"] - b["x0"]) < 0.1})
    if gaps:
        rows.append([f"К{len(rows) + 1}", f"Передние панели внутренних ящиков: зазор {n_(gaps[0])} между панелями", "щуп",
                     f"{n_(gaps[0])} ± 1; до проставки ≥ 5"])
    if drs:
        rows.append([f"К{len(rows) + 1}", "Ход ящиков" + (" при открытой двери" if d.get("doors") else "") +
                     ("; TIP-ON" if any(r["tipon"] for r in drs) else ""), "вручную", "полное выдвижение, без касаний"])
    rows.append([f"К{len(rows) + 1}", "Двери: зазоры" if d.get("doors") else "Фасады: зазоры", "щуп, линейка",
                 "3 ± 0,5 между; 1,5 ± 0,5 от граней"])
    if d.get("push_gap"):
        rows.append([f"К{len(rows) + 1}", f"Дверь без ручки: зазор дверь — корпус {n_(d['push_gap'])}, открывание нажатием",
                     "щуп, вручную", f"{n_(d['push_gap'])} +1 / −0; дверь открывается от нажатия (В-104)"])
    Hh = s["options"].get("height")
    steps = ["Детали (по независимым размерам)",
             f"1. Раскроить и окромковать детали по листам {c.detail_ref}; присадка от баз A по таблицам отверстий.",
             "2. Левые и правые детали — по своему виду; у каждой группы отверстий подписаны база и сторона входа;",
             "     «разметка» — без сверления (профили Blum, узел Ж).",
             "Корпуса (каждая секция и антресоль отдельно)" if any(p["id"].startswith("S1-") for p in parts) else "Корпус"]
    k = 3
    hasfix = any(p["name"].startswith("Полка жёсткая") for p in parts)
    steps += [f"{k}. Корпуса эксцентриков — в крышку, дно" + (", жёсткие полки" if hasfix else "") +
              "; штоки и шканты — в боковины; собрать (узлы А, Б)."]
    k += 1
    if any(h["joint"] == "J-ST-PAIR" for h in s["holes"]):
        steps.append(f"{k}. Стойки: каждую — к дну и крышке своими эксцентриками (корпуса эксцентриков левой стойки — в левой"
                     " колонне, правой — в правой); затянуть, затем скрутить стойки между собой 4 × 25 со стороны левой"
                     " колонны (узел Н)."); k += 1
    steps.append(f"{k}. Выставить диагонали ({', '.join(diag)}), закрепить ХДФ саморезами от углов к середине (узел Е)."); k += 1
    if "feet" in d.get("modules", []):
        steps.append(f"{k}. Опоры: площадки по разметке, саморезы 4 × 13 в дно (узел К)."); k += 1
    if any(p["name"].startswith("Цоколь") for p in parts) and "CLIP" not in H:
        steps.append(f"{k}. Цоколь: рамка на шкантах, к дну — конфирматы через дно (узлы Б, В)."); k += 1
    if any("SPACER" in p["id"] for p in parts):
        steps.append(f"{k}. Проставки направляющих: к боковинам секций с ящиками, саморезы 4 × 25 через проставку (узел Н);")
        steps.append("     передний торец проставки — за планкой петли (В-105)."); k += 1
    if drs:
        box = (f"{k}. Короба: дно в пазы боковин, передняя и задняя стенки — на дно, конфирматы (узел В); дно к стенкам"
               " саморезами 4 × 25 снизу (узел Н)." if drs[0].get("sys") == "movento" else f"{k}. Короба на конфирматах (узел В).")
        steps += ["Ящики",
                  box + " Сборщик после сборки короба: отверстия под задний крючок Ø6 и"
                  " замки — шаблоном Blum T65.1000.02 (в цехе не сверлятся); первый ящик собрать и проверить с фасадом.",
                  f"{k + 1}. Профили — " + ("саморезами Blum 609.1500 Ø3,5 × 15 по точкам таблицы NL (узел Ж), после сборки"
                  " корпуса (ось 38; если профиль ставят до сборки — ось 39, Blum)" if drs[0].get("sys") == "movento" else
                  "саморезами Ø4 × 15 по точкам таблицы NL (узел Ж)") +
                  (" на проставки" if any("SPACER" in p["id"] for p in parts) else "") + "; установить короба."]
        k += 2
        outer = [r for r in drs if not r.get("setback_front")]
        if outer:
            steps.append(f"{k}. Фасады ящиков: зазоры 3 между фасадами, 1,5 по краям, прижать, саморезы изнутри короба"
                         " (узел Г)."); k += 1
        if gaps:
            steps.append(f"{k}. Передние панели внутренних ящиков: зазор {n_(gaps[0])} между панелями, прижать, саморезы"
                         " изнутри короба (узел Г)."); k += 1
        if any(r["tipon"] for r in drs):
            steps.append("     TIP-ON ящиков: " + (H["TIPON-SYNC"]["spec"].replace(".0 ", " ") if "TIPON-SYNC" in H else "по каталогу Blum") + ".")
    steps.append("Монтаж на объекте")
    if d.get("ceiling_gap"):
        steps.append(f"{k}. Проём: высота изделия {Hh} на опорах в середине регулировки; потолок не ниже "
                     f"{Hh + d['ceiling_gap']} (В-102)."); k += 1
    if d.get("mount_steps"):
        for t_ in d["mount_steps"]:
            steps.append(f"{k}. {t_}"); k += 1
    if "TIE" in H:
        steps.append(f"{k}. Секции на опоры, выставить по уровню опорами (±15); стянуть стяжками Ø5, 4 на стык (В-41)."); k += 1
    if any(p["id"].startswith("S1-M-") for p in parts):
        steps.append(f"{k}. Антресоли на секции: саморезы 4 × 25 снизу через крышку секции в дно антресоли, 2 на секцию"
                     " (узел Н); стяжки антресолей."); k += 1
    if "WALL-ANGLE" in H:
        steps.append(f"{k}. Крепление к стене: уголки, {H['WALL-ANGLE']['qty']} шт. по верху, " +
                     ("до навески дверей и загрузки;" if d.get("doors") else "до загрузки;") +
                     " дюбель / анкер по основанию — монтажник (В-48)."); k += 1
    if d.get("mount_steps_after"):
        for t_ in d["mount_steps_after"]:
            steps.append(f"{k}. {t_}"); k += 1
    if "CLIP" in H:
        steps.append(f"{k}. Цоколь: клипсы на опоры, лицевой и торцевые цоколи на клипсы (узел К)."); k += 1
    if d.get("doors"):
        steps.append(f"{k}. Двери: планки на боковины (евровинты), петли на двери (2 самореза на чашку), навесить (узел И);"
                     " зазоры 3 / 1,5."); k += 1
        if d.get("push_gap"):
            steps.append(f"     TIP-ON дверей: зазор дверь — корпус {n_(d['push_gap'])}, место и пластины — по схеме Blum"
                         " (В-104).")
    return steps, rows


def sheet_control(c):
    s = c.s
    d = s["derived"]
    sh = Sheet("Сборка и контроль", stamp_for(s), c.no["control"], c.total, "—")
    mods = set(d["modules"])
    steps = ["Детали (по независимым размерам)",
             f"1. Раскроить и окромковать детали по листам {c.detail_ref}; присадка от баз A по координатам (станок или кондуктор).",
             "2. Зеркальные детали (левая / правая) — по своему виду; отверстия под профили Blum — только разметка (лист узлов, Ж)."]
    k = 3
    if s["derived"].get("carcasses"):
        steps += ["Корпус",
                  f"{k}. Корпуса эксцентриков — в крышку, дно, стойки, полки; штоки и шканты — в боковины; собрать, затянуть (узлы А, Б).",
                  f"{k + 1}. Выставить диагонали (К3), закрепить ХДФ саморезами от углов к середине (узел Е)."]
        k += 2
    if "plinth" in mods:
        steps.append(f"{k}. Цоколь: рамка на шкантах с клеем, к дну конфирматами через дно (узлы Б, В)."); k += 1
    if "feet" in mods:
        steps.append(f"{k}. Опоры / колёса: площадки по разметке, саморезы 4 × 13 в дно (узел К)."); k += 1
    if "hang" in mods:
        steps.append(f"{k}. Навесы — в верхние задние углы; шина к стене по типу стены (В-21); навесить, выставить."); k += 1
    if d.get("frames"):
        steps += ["Металл",
                  f"{k}. Рамы сварить в кондукторе (лист металла), зачистить, окрасить; гайки заклёпочные — после окраски.",
                  f"{k + 1}. Собрать рамы с балками (болты M6), выставить в плоскости; столешницу положить на раму, разметить",
                  "     втулки через отверстия Ø7, засверлить Ø10 гл. 17, ввернуть втулки, затянуть винты (узел Л)."]
        k += 2
    if d.get("drawers"):
        steps += ["Ящики",
                  f"{k}. Собрать короба на конфирматах (узел В); крючок Ø6 × 10 и замки — шаблоном Blum T65.1000.02.",
                  f"{k + 1}. Профили — саморезами Ø4 × 15 по точкам таблицы NL (узел Ж); замки под дно; установить короба.",
                  f"{k + 2}. Фасады: зазор 3 между фасадами, 1,5 от граней; прижать, саморезы изнутри короба (узел Г)."]
        if any(r["tipon"] for r in d["drawers"]):
            steps.append("     TIP-ON: вал синхронизатора по раскрою LW − 31; зазор фасад — корпус 3,5 (Blum стр. 24).")
        k += 3
    if d.get("doors"):
        steps.append(f"{k}. Двери: петли и планки по таблице (узел И, кандидат), регулировка зазоров 3 / 1,5."); k += 1
    if _is_new(s):
        steps, rows_new = control_new(c)
    if "kitchen_set" in mods:
        steps = ["Изготовление",
                 "1. Модули — по своим комплектам (лист 02, спецификация); детали кухни — по листам " + c.detail_ref + ".",
                 "2. Столешницу заказать по замеру на месте после установки низа (В-39); вырезы — по шаблонам техники (В-36, В-38).",
                 "Монтаж",
                 "3. Замер стен и пола; разметить уровень низа (опоры) и линию шины верхних модулей (В-41).",
                 "4. Низ и колонны: выставить по уровню опорами, стянуть стяжками Ø5 (4 на стык, сверлить по месту), колонны — "
                 "уголками к стене.",
                 "5. Верх: шина к стене, навесить модули, выставить навесами, стянуть стяжками.",
                 "6. Столешница: ЛДСП — саморезами 4 × 30 через царги снизу; кварц — на силикон по боковинам и царгам; стыки и "
                 "примыкания — герметиком.",
                 "7. Техника и мойка — по инструкциям изготовителей; цоколь — на клипсы к опорам (узел К); регулировка фасадов."]
    y = 283
    for t in steps:
        bold = not t.startswith(" ") and not t[0].isdigit()
        sh.text(25, y, t, size=7.0 if bold else 6.2, weight="bold" if bold else "normal", va="top")
        y -= 5.8 if bold else 4.8
    rows = [["К1", "Размеры деталей после кромки", "рулетка, штангенциркуль", f"по листам {c.detail_ref}; ±0,5 (В-10)"]]
    if _is_new(s):
        rows = rows_new
    elif "kitchen_set" in mods:
        rows += [["К2", "Низ: горизонталь по верху корпусов, плоскость фасадов", "уровень 2 м", "≤ 1 на 1000; ≤ 1,5 по ряду"],
                 ["К3", "Верх: горизонталь, вертикаль фасадов", "уровень", "≤ 1 на 1000"],
                 ["К4", "Столешница: стыки, примыкание к стене", "щуп", "стык ≤ 0,3, герметик без разрывов"]]
    for cc in ([] if _is_new(s) else d.get("carcasses", [])[:2]):
        rows.append([f"К{len(rows) + 1}", f"{cc['label'].capitalize()}: диагонали по фасадной плоскости", "рулетка",
                     f"{n_(cc['x1'] - cc['x0'])} × {n_(round(cc['z1'] - cc['z0'], 1))}; разность ≤ 1,5"])
    if d.get("drawers") and not _is_new(s):
        r = d["drawers"][0]
        rows.append([f"К{len(rows) + 1}", "Короб: внутренняя ширина спереди и сзади", "штангенциркуль",
                     f"{n_(r['inner_w'])} +0 / −1,5 (Blum LW − 42)"])
        rows.append([f"К{len(rows) + 1}", "Ход ящиков; TIP-ON — открывание нажатием", "вручную", "полное выдвижение, без касаний"])
    if d.get("frames"):
        rows.append([f"К{len(rows) + 1}", "Рама: диагонали, плоскость опоры столешницы", "рулетка, линейка", "≤ 2; ≤ 0,5"])
    if not _is_new(s):
        rows.append([f"К{len(rows) + 1}", "Фасады / двери: зазоры", "щуп, линейка", "3 ± 0,5 между; 1,5 ± 0,5 от граней"])
    sh.text(25, y - 4, "Контроль", size=8.0, weight="bold", va="top")
    yb = sh.table(25, y - 10, ["№", "Что проверяем", "Чем", "Критерий"], rows, [12, 88, 52, 100], row_h=5.6, size=6.1)
    sh.text(25, yb - 5, "Прочность, устойчивость, нагрузка на ящики и полки — не приёмочный контроль: проверяются на образце "
            "по программе испытаний (В-12).", size=6.1, va="top")
    return sh


def sheet_questions(c):
    s = c.s
    sh = Sheet("Открытые вопросы и решения", stamp_for(s), c.no["questions"], c.total, "—")
    sh.text(25, 283, "Пока вопросы не закрыты, комплект не выдаётся в производство. Пробный образец — только с пометкой «проба».",
            size=7.2, weight="bold", color=RED, va="top")
    y = 275
    sh.table(25, y, ["№", "Вопрос", "Что блокирует", "Кто", "Как закрыть"], [], [14, 186, 66, 40, 84], row_h=6.0, size=6.4)
    y -= 6.0
    for q, t, b, w, h in c.questions:
        lines = textwrap.wrap(t, 116); lb = textwrap.wrap(b, 40); lc = textwrap.wrap(h, 50); lw = textwrap.wrap(w, 24)
        k = max(len(lines), len(lb), len(lc), len(lw))
        sh.text(26.2, y - 2.6, q, size=6.2, weight="bold", va="top")
        for i, tt in enumerate(lines):
            sh.text(40.2, y - 2.6 - i * 3.7, tt, size=5.8, va="top")
        for col, xs in ((lb, 226.2), (lw, 292.2), (lc, 332.2)):
            for i, tt in enumerate(col):
                sh.text(xs, y - 2.6 - i * 3.7, tt, size=5.8, va="top")
        y -= 3.7 * k + 1.8
        sh.line(25, y, 415, y, THIN)
    for x in (25, 39, 225, 291, 331, 415):
        sh.line(x, 275, x, y, THIN)
    y -= 6
    sh.text(25, y, "Закрыто по документам производителей (показано на чертежах)", size=7.4, weight="bold", va="top")
    y -= 5.5
    for q, t in c.decisions:
        ls = textwrap.wrap(t, 160)
        sh.text(26, y, q, size=6.1, weight="bold", va="top")
        for i, tt in enumerate(ls):
            sh.text(40, y - i * 3.7, tt, size=5.8, va="top")
        y -= 3.7 * len(ls) + 1.0
    return sh


# ===================================================================== вопросы
def questions_for(s):
    d = s["derived"]
    mods = set(d["modules"])
    sku = s["sku"]
    parts = s["parts"]
    hw = {h["id"] for h in s["hardware"]}
    decors = sorted({fin_ru(p["finish"]) for p in parts if p["kind"] == "board" and p["finish"] not in ("INNER", "black")})
    Q = [("В-1", f"Плита: поставщик и артикул ЛДСП в декорах {', '.join(decors)}; фактическая толщина партии; белая ЛДСП для "
                 "коробов; наличие нужных толщин в одном декоре", "раскрой всех позиций, глубины присадки", "Arvello + поставщик",
          "паспорт плиты, замер 3 листов"),
         ("В-2", "Кромка ABS 2 и ПВХ 0,4 в цвет; припуск на фуговку станка (заготовки даны без припуска)", "размеры заготовок",
          "цех плиты", "паспорт станка, проба"),
         ("В-10", "Допуски: раскрой ±0,5; присадка ±0,3 (ЧПУ) или ±0,5 (кондуктор); диагонали корпуса ≤ 1,5; рамы ≤ 2; "
                  "зазоры фасадов 3 ± 0,5", "контроль", "технолог цеха + Arvello", "записать в техкарту"),
         ("В-12", "Образец: пробная сборка, программа испытаний (нагрузка на ящики, полки" +
                  (" и столешницу" if any(p["material"].startswith(("TOP", "STONE")) for p in parts) else "") +
                  ", циклы, устойчивость, "
                  "прогиб); устойчивость в R01E не нормирована", "приёмка образца", "Arvello", "утвердить программу, протокол")]
    if "HANDLE-128" in hw:
        Q.append(("В-5", "Ручка-скоба 128: артикул; длина винтов M4 (22 — в фасад, 40 — сквозь фасад и короб), ввёртывание ≥ 4",
                  "узел Д", "Arvello", "образец ручки"))
    if "doors" in mods or "PUSH-LATCH" in hw:
        Q.append(("В-20", "Петли: каталог Blum CLIP top BLUMOTION 110° (или аналог) — размер C, глубина чашки, планка, "
                          "присадка планки; для двери без ручки — TIP-ON для дверей и петли без пружины",
                  "узел И, двери", "Arvello", "прислать PDF каталога петель — довести до R02E"))
    if "hang" in mods or any(h["kind"] == "wall_bolt" for h in s["holes"]):
        Q.append(("В-21", "Крепление к стене: тип стены у клиента; навес / анкеры и их несущая способность (с запасом на "
                          "нагрузку и вес раковины / содержимого)", "монтаж", "Arvello + монтажник", "каталог навеса, протокол"))
    if "LOCK" in hw or "CASTER" in hw:
        Q.append(("В-22", "Колёса (2 с тормозом) и центральный замок на 3 ящика: артикулы, площадки, тяга замка по боковине",
                  "поз. колёс и замка, отверстие Ø19", "Arvello", "каталог и образцы"))
    if "LEG" in hw:
        Q.append(("В-23", "Ножки 40 × 40 × 60: артикул, площадка, саморезы; нагрузка на крышку (ТВ) и пролёт дна",
                  "опоры, устойчивость", "Arvello", "образец, испытание"))
    if d.get("frames"):
        Q.append(("В-24", "Металл: марка стали и сертификат труб; швы (тип, катет, зачистка); порошковое покрытие (цвет, "
                          "толщина); сварка в кондукторе", "лист металла, рамы", "цех металла", "технологическая проба, техкарта"))
    if "top_fix" in mods:
        Q.append(("В-25", "Втулка M6 RAMPA SK330 (как «Опора»): наличие или аналог; вырыв и момент на обрезке выбранной плиты",
                  "узел Л", "Arvello + цех", "протокол пробы"))
    if any(h["kind"] == "rivnut" for h in s["holes"]) or {"GLIDE-20", "GLIDE-PAD"} & hw:
        Q.append(("В-26", "Подпятники / заглушки с регулировкой: артикулы, высота, ход; заклёпочные гайки под стенку 2",
                  "высота изделия, опоры", "Arvello", "образцы, замер"))
    if {"LED", "CHARGER"} & hw:
        Q.append(("В-27", "Подсветка (профиль, лента, блок 12 В) и встраиваемая зарядка: артикулы, вырезы, прокладка кабеля, "
                          "электробезопасность", "вырезы, кабельные вводы", "Arvello", "образцы изделий"))
    if "SINK-DRAIN" in hw:
        Q.append(("В-28", "Раковина и слив: модель раковины клиента, Ø и положение донного клапана, сифон; канал в ящике "
                          "220 мм — проверить по сифону", "вырезы столешницы и крышки, ящик", "Arvello + клиент", "образец"))
    if {"CABLEBOX", "SCREEN-CLAMP"} & hw or any(p["id"].startswith("TRAY") for p in parts):
        Q.append(("В-29", "Кабель-канал / лючок / экран: артикулы, вырез под лючок, глубина лючка над балкой, крепление экрана",
                  "вырезы, лоток", "Arvello", "каталог изделий"))
    if any(p["material"] == "MDF22" for p in parts):
        Q.append(("В-30", "Рифлёные фасады / панель МДФ 22: шаг, ширина и глубина канавок, покрытие (плёнка / эмаль) в цвет "
                          "декора; в каталоге выступ рифления больше — согласовать вид", "фасады", "Arvello + цех МДФ",
                  "образец 300 × 300"))
    if any(p["kind"] == "board" and p["material"] == "LDSP25" and (p["x1"] - p["x0"]) > 2780 for p in parts):
        Q.append(("В-31", "Столешница длиннее 2780 — плита формата 3660 × 1830 в нужном декоре (иначе — шов)", "поз. столешницы",
                  "поставщик", "подтвердить формат"))
    if sku == "ARV-BTH-001":
        Q.append(("В-32", "Влажное помещение: ЛДСП влагостойкая, кромка ABS на всех торцах, герметик по вырезу",
                  "материалы", "Arvello", "паспорт плиты"))
    if any("слой" in p["unit"] for p in parts):
        Q.append(("В-33", "Склейка двухслойных панелей (опоры / боковины / полка): клей, пресс, допуск по толщине",
                  "поз. слоёв", "цех плиты", "проба"))
    if sku == "ARV-OFF-005":
        Q.append(("В-34", "Порядок высот ящиков: в 3D каталога верхний 210, нижний 180; в описании «верхний неглубокий»",
                  "фасады, короба", "Темирлан", "решение по виду"))
    dec = [("В-3", "Häfele CFCD 2014: корпус 262.26.033 — Ø15, гл. 12,5 +0,5, A 8 (стр. 294); болт S200 262.27.679 — B 24, "
                   "резьба 11 под Ø5 (стр. 301) → Ø5 × 12; торец Ø8 × 32. Как «Самал» R02E; листы 2014 г. — сверить с поставкой.")]
    drs = d.get("drawers", [])
    if drs:
        bm = any(not r["tipon"] for r in drs)
        to = any(r["tipon"] for r in drs)
        t = "Blum TANDEM RU v4: 560H"
        if bm:
            t += " BLUMOTION — артикулы стр. 20, место и короб стр. 22 (низ дна → низ профиля 27,5, ось саморезов 37), точки профиля стр. 39"
        if to:
            t += ("; " if bm else "") + (" встроенный TIP-ON — артикулы и синхронизатор T57.1140S (раскрой LW − 31) стр. 23, место и "
                                          "короб стр. 24 (28,5 и 38, зазор фасада 3,5), точки профиля стр. 40")
        mv = [r for r in drs if r.get("sys") == "movento"]
        if mv:
            r0 = mv[0]
            t = ("Blum MOVENTO 760H + TIP-ON BLUMOTION: артикулы, набор TIP-ON BLUMOTION и синхронизация (LW − 267) — каталог "
                 "Blum 2022/23 стр. 436; место в корпусе (низ дна → низ профиля 28,5, ось саморезов 38, над ящиком 7); места "
                 f"саморезов NL {r0['NL']}: {' / '.join(str(v) for v in r0['pts'])} от передней кромки, саморез 609.1500 "
                 "Ø3,5 × 15 (каталог 2024/25 с. 428, вариант A; DXF Blum); точка 28 — только у 766H; зазор фасада 2,5. Короб — "
                 "раскрой конфигуратора Blum 12.11: стенки = боковина − 13 − 16 на дне, дно SKW + 10 в пазах 5")
            if len(mv) < len(drs):
                t += "; остальные ящики — Blum TANDEM 560H"
        inn = [r for r in drs if r.get("setback_front")]
        if inn:
            r0 = inn[0]
            t += (f"; внутренний ящик за дверью (стр. 24, 40): длина с передней панелью SKL + X = {r0['box_l']} + "
                  f"{n_(r0['front_t'])} = {n_(r0['box_l'] + r0['front_t'])}, место от передней панели NL + X + 7 = "
                  f"{n_(r0['NL'] + r0['front_t'] + 7)}")
        t += ". Общее: SKW = LW − 42 (+0/−1,5), SKL = NL − 10, место NL + 3, утопление дна 12–15 (принято 13), замки " + \
             ("T51.7600" if mv else "T51.1700.04") + ", крючок и замки — шаблон T65.1000.02. Ряд NL по глубине корпуса: " + ", ".join(sorted({str(r["NL"]) for r in drs})) + "."
        dec.append(("В-4", t))
        if any(r.get("sys") == "movento" for r in drs):
            dec.append(("В-107", "MOVENTO закрыт данными Blum 12.11: места саморезов — каталог 2024/25 с. 428 и DXF Blum; точка 28 у "
                                 "760H не используется; набор TIP-ON BLUMOTION L1 T60L7340 (до 20 кг) при грузе 10 кг; крючок Ø6 "
                                 "гл. 10 и замки — шаблоном T65.1000.02."))
    for qid in d.get("kq", []):
        if qid not in [q[0] for q in Q]:
            Q.append((qid,) + tuple({**KX.KQ, **MR.KQ2, **d.get("kq_text", {})}[qid]))
    if d.get("kdec"):
        Q.append(("В-43", "Отличия от каталога (вид): " + " ".join(d["kdec"]), "вид модели в каталоге", "Темирлан",
                  "подтвердить или вернуть к каталогу"))
    known = [q[0] for q in Q] + [x[0] for x in dec]
    return Q, dec, known


def tech_req(s, c):
    d = s["derived"]
    t = [f"1. Детали — по листам {c.detail_ref} от баз A; отверстия по координатам,",
         "   без подгонки (кроме втулок столешницы — по раме)." if not _is_new(s) else
         "   без подгонки; съёмные полки — на полкодержателях Ø5.",
         "2. Номера на видах — позиции спецификации.",
         (f"3. Узлы А … П — лист {c.no['nodes']:02d}." if not _is_new(s) else
          f"3. Узлы {', '.join(sorted({NODE[h['kind']] for h in s['holes'] if h['kind'] in NODE}, key='АБВГДЕЖИКЛМНПР'.index))}"
          f" — лист {c.no['nodes']:02d}.")]
    if d.get("drawers"):
        r = d["drawers"][0]
        t += [f"4. Ящики Blum {'MOVENTO 760H' if r.get('sys') == 'movento' else '560H'} NL {r['NL']}: профили по точкам NL (узел Ж);",
              "   крючок и замки — шаблоном T65.1000.02."]
    t.append(f"5. Открытые вопросы — лист {c.no['questions']:02d}.")
    return t


# ===================================================================== сборка комплекта
def write_kit(sku, path, options=None):
    s = make(sku, options)
    pos, rep, hpos = positions(s)
    det = plan_details(s, pos, rep)
    has_metal = any(p["kind"] in ("tube", "plate") for p in s["parts"])
    rows = None
    no = {"general": 1, "assembly": 2}
    k = 3
    newm = sku in models_new.NEW
    if newm:
        no["sections"] = k; k += 1
    no["details"] = list(range(k, k + len(det))); k += len(det)
    dpages = []
    if newm:
        c_tmp = Ctx(s, 0, dict(no, nodes=0, drill=[0]))
        dpages = drill_pages(c_tmp)
        no["drill"] = list(range(k, k + len(dpages))); k += len(dpages)
    if has_metal:
        no["metal"] = k; k += 1
    no["nodes"] = k; k += 1
    c0 = Ctx(s, 0, no)
    rows = spec_rows(c0)
    chunks = [rows[i:i + 44] for i in range(0, len(rows), 44)]
    if len(chunks[-1]) > 40:
        chunks.append([])
    no["spec"] = list(range(k, k + len(chunks))); k += len(chunks)
    no["control"] = k; k += 1
    no["questions"] = k
    total = k
    s["_total_sheets"] = total
    c = Ctx(s, total, no)
    c.detail_ref = f"{no['details'][0]:02d}–{no['details'][-1]:02d}" if len(no["details"]) > 1 else f"{no['details'][0]:02d}"
    c.questions, c.decisions, known = questions_for(s)
    c.tech_req = tech_req(s, c)
    kit_set = "kitchen_set" in s["derived"]["modules"]
    cont = ["01 Общий вид", "02 План и модули" if kit_set else ("02 Карта сборки" if newm else "02 Сборочный чертёж")]
    if newm:
        cont.append(f"{no['sections']:02d} Разрезы и размеры")
    cont += [f"{x:02d} Детали" for x in no["details"]] + [f"{x:02d} Таблица присадки" for x in no.get("drill", [])]
    if has_metal:
        cont.append(f"{no['metal']:02d} Металл")
    cont += [f"{no['nodes']:02d} Узлы"] + [f"{x:02d} Спецификация" for x in no["spec"]] + \
            [f"{no['control']:02d} Сборка и контроль", f"{no['questions']:02d} Вопросы и решения"]
    c.contents = cont
    figs, report, texts = [], {}, []
    fns = [("general", lambda: sheet_general(c))]
    if newm:
        fns += [("assembly", lambda: sheet_assembly_map(c)), ("sections", lambda: sheet_assembly(c))]
    else:
        fns.append(("assembly", lambda: sheet_kitchen(c) if kit_set else sheet_assembly(c)))
    for i, blk in enumerate(det):
        fns.append((f"details{i}", (lambda b=blk, i=i: sheet_details(c, b, i))))
    for i, pg in enumerate(dpages):
        fns.append((f"drill{i}", (lambda pg=pg, i=i: sheet_drill(c, pg, i))))
    if has_metal:
        fns.append(("metal", lambda: sheet_metal(c)))
    fns.append(("nodes", lambda: sheet_nodes(c)))
    for i, ch in enumerate(chunks):
        fns.append((f"spec{i}", (lambda ch=ch, i=i: sheet_spec(c, ch, i, i == len(chunks) - 1))))
    fns += [("control", lambda: sheet_control(c)), ("questions", lambda: sheet_questions(c))]
    with PdfPages(path) as pdf:
        for name, fn in fns:
            sh = fn()
            report[name] = sh.check_overlaps()
            texts += [t.get_text() for t in sh.ax.texts]
            pdf.savefig(sh.fig)
            figs.append(sh.fig)
        pdf.infodict()["Title"] = f"{sku} {s['rev']} {s['hash']}"
    checks = verify(s, report, texts, known)
    if _is_new(s):
        from eng.verify_new import ERR, verify_new
        checks += [(n, st != ERR, f"[{st}] {t}") for n, st, t in verify_new(s, texts)]
    return s, checks, figs



# ===================================================================== новые модели: карта сборки и таблицы присадки
def _side_word(p):
    return "левая" if "SIDE-L" in p["id"] or p["id"].endswith("-L") else "правая" if "SIDE-R" in p["id"] or p["id"].endswith("-R") else ""


def sheet_assembly_map(c):
    """Лист 02 новых моделей: шкаф спереди без дверей, секции слева направо с наполнением, боковины по позициям,
    схема навески дверей и крупно секция с ящиками (с названиями позиций). Лево / право — стоя перед шкафом."""
    s = c.s
    d = s["derived"]
    sh = Sheet("Карта сборки", stamp_for(s), c.no["assembly"], c.total, "см. виды")
    parts = s["parts"]
    P = {p["id"]: p for p in parts}
    bb = bbox(s, ("board",))
    W, H = bb["x"][1] - bb["x"][0], bb["z"][1] - bb["z"][0]
    sc = _scale((W, 175), (H, 190), extra=(15,))
    vf = View(sh, sc, (32, 80), (bb["x"][0], bb["z"][0]))
    has_sec = any(p["id"].startswith("S1-SIDE-L") for p in parts)
    if not has_sec:
        return _parts_map(c, sh)
    nodoor = lambda p: p["kind"] == "board" and not (p["group"] == "fronts" and ("DOOR" in p["id"] or not has_sec))
    _proj(vf, s, "front", only=nodoor)
    _proj(vf, s, "front", only=lambda p: p["kind"] == "buy" and p["group"] == "interior")
    a, b = vf.p(bb["x"][0], bb["z"][0]), vf.p(bb["x"][1], bb["z"][1])
    sh.text(a[0], b[1] + 15, ("Шкаф спереди без дверей" if has_sec else "Изделие спереди без фасадов") +
            f", М 1:{n_(sc)} · лево / право — стоя перед изделием", size=7.6,
            weight="bold")
    # секции и наполнение
    secs = sorted({p["id"].split("-")[0] for p in parts if p["id"].startswith("S") and "-SIDE-L" in p["id"]},
                  key=lambda t: int(t[1:]))
    for sid in secs:
        L, R = P[f"{sid}-SIDE-L"], P[f"{sid}-SIDE-R"]
        xm = vf.p((L["x0"] + R["x1"]) / 2, 0)[0]
        sh.text(xm, b[1] + 7, f"Секция {sid[1:]}", size=7.0, weight="bold", ha="center")
        fill = []
        if any((p["id"].startswith(sid + "-") or p["id"].startswith(f"ROD-{sid}-")) and "ROD" in p["id"] for p in parts):
            fill.append("штанга" + (" выдвижная" if any(p["id"] == f"{sid}-PULLROD" for p in parts) else ""))
        nsh = sum(1 for p in parts if p["id"].startswith(sid + "-") and "SHELF" in p["id"] and "-M-" not in p["id"])
        if nsh:
            fill.append(f"полок {nsh}")
        nbx = sum(1 for r in d.get("drawers", []) if r["pre"] == sid + "-")
        if nbx:
            fill.append(f"ящиков {nbx}")
        door = next((r for r in d.get("doors", []) if r["door"] == f"{sid}-DOOR-1"), None)
        if door:
            fill.append("петли " + ("слева" if door["left"] else "справа"))
        for j, t in enumerate(fill):
            sh.text(xm, a[1] - 3 - j * 3.6, t, size=6.0, ha="center", va="top")
        # боковины: номер позиции у низа каждой
        for S, dx in ((L, -1), (R, 1)):
            x_ = vf.p((S["x0"] + S["x1"]) / 2, 0)[0]
            sh.balloon(x_, vf.p(0, S["z0"] + 300)[1], x_ + dx * 4.2, a[1] - 17, c.pos.get(S["id"], "—"), r=2.6)
        M = P.get(f"{sid}-M-SIDE-L")
        if M:
            ym = vf.p(0, (M["z0"] + M["z1"]) / 2)[1]
            sh.text(xm, ym, "антресоль", size=5.8, ha="center", va="center", color="#555")
    if has_sec:
        sh.text(a[0], a[1] - 22, "В кружках — позиции боковин: левая и правая боковины одной секции — разные позиции "
            "(разная присадка).", size=6.0, va="top")
    # схема навески дверей
    doors = [p for p in parts if p["group"] == "fronts" and "DOOR" in p["id"]]
    if doors:
        s2 = next(x for x in (50, 60, 75, 100, 150) if W / x <= 62 and H / x <= 50)
        vd = View(sh, s2, (346, 222), (bb["x"][0], bb["z"][0]))
        recs = {r["door"]: r for r in d.get("doors", [])}
        for p in doors:
            vd.rect(p["x0"], p["z0"], p["x1"], p["z1"], VIS, fill="white")
            r = recs.get(p["id"])
            if not r:
                continue
            xh, xf = (p["x0"], p["x1"]) if r["left"] else (p["x1"], p["x0"])
            vd.line(xf, p["z0"], xh, (p["z0"] + p["z1"]) / 2, THIN)
            vd.line(xf, p["z1"], xh, (p["z0"] + p["z1"]) / 2, THIN)
            pp = vd.p((p["x0"] + p["x1"]) / 2, (p["z0"] + p["z1"]) / 2)
        g = vd.p(bb["x"][0], bb["z"][1])
        sh.text(346, g[1] + 4, f"Навеска дверей, М 1:{n_(s2)}", size=7.0, weight="bold")
        for j, t in enumerate(("Вершина треугольника —", "сторона петель.", f"Петли, TIP-ON — узел И, лист {c.no['nodes']:02d}.")):
            sh.text(346, 218 - j * 3.6, t, size=5.9, va="top")
    # крупно секция с ящиками (или первая)
    tgt = next((r["pre"][:-1] for r in d.get("drawers", []) if r["pre"].startswith("S")), secs[0] if secs else "все")
    if tgt:
        sec = [p for p in parts if (tgt == "все" or p["id"].startswith(tgt + "-")) and "-M-" not in p["id"]
               and p["kind"] == "board" and not (p["group"] == "fronts" and ("DOOR" in p["id"] or tgt == "все"))]
        x0_, x1_ = min(p["x0"] for p in sec), max(p["x1"] for p in sec)
        z0_, z1_ = min(p["z0"] for p in sec), max(p["z1"] for p in sec)
        s3 = _scale((x1_ - x0_, 60), (z1_ - z0_, 190), extra=(12.5, 15))
        v3 = View(sh, s3, (226, 66), (x0_, z0_))
        _proj(v3, s, "front", only=lambda p: p in sec)
        t3 = v3.p(x0_, z1_)
        sh.text(226, t3[1] + 9, f"Секция {tgt[1:]} крупно, без двери" if tgt != "все" else "Корпус и ящики без фасадов",
                size=7.2, weight="bold")
        sh.text(226, t3[1] + 4.6, f"М 1:{n_(s3)}; позиции и названия деталей секции", size=6.2)
        seen, items = set(), []
        for p in sorted(sec, key=lambda p: -p["z1"]):
            ps = c.pos.get(p["id"])
            if ps and ps not in seen:
                seen.add(ps)
                items.append((ps, p))
        xr = v3.p(x1_, 0)[0] + 12
        anchors = []
        for i, (ps, p) in enumerate(items):
            u = (max(p["x0"], x0_) + min(p["x1"], x1_)) / 2 if p["x1"] - p["x0"] < 200 else min(p["x1"] - 30, p["x0"] + 60 + (i % 4) * 90)
            vz = (p["z0"] + p["z1"]) / 2 if p["z1"] - p["z0"] < 400 else p["z1"] - 120 - (i % 3) * 140
            anchors.append((v3.p(u, vz), ps, p))
        anchors.sort(key=lambda t: -t[0][1])
        gap_ = 5.6
        while True:
            ys, last = [], t3[1] - 3 + gap_
            for (ax_, ay_), _, _ in anchors:
                y_ = min(ay_, last - gap_)
                ys.append(y_); last = y_
            if not ys or ys[-1] >= 62 or gap_ <= 4.4:
                break
            gap_ -= 0.3
        for ((ax_, ay_), ps, p), ty in zip(anchors, ys):
            sh.balloon(ax_, ay_, xr, ty, ps, r=2.4)
            nm = p["unit"] + (f" {_side_word(p)}" if p["unit"].startswith("Боковина") and _side_word(p) and
                              _side_word(p) not in p["unit"] else "")
            sh.text(xr + 4, ty, nm[:34], size=5.9, va="center")
    return sh


def _parts_map(c, sh):
    """Карта сборки изделия без секций: вид спереди без фасадов, позиции с названиями справа."""
    s = c.s
    parts = s["parts"]
    sec = [p for p in parts if p["kind"] == "board" and p["group"] != "fronts"]
    x0_, x1_ = min(p["x0"] for p in sec), max(p["x1"] for p in sec)
    z0_, z1_ = min(p["z0"] for p in sec), max(p["z1"] for p in sec)
    s3 = _scale((x1_ - x0_, 190), (z1_ - z0_, 185), extra=(7.5, 12.5, 15))
    v3 = View(sh, s3, (40, 70), (x0_, z0_))
    _proj(v3, s, "front", only=lambda p: p in sec)
    t3 = v3.p(x0_, z1_)
    sh.text(40, 280, f"Изделие спереди без фасадов, М 1:{n_(s3)} · лево / право — стоя перед изделием", size=7.6,
            weight="bold")
    sh.text(40, 275, "Позиции и названия деталей; фасады — на листах деталей, порядок — лист "
            f"{c.no['control']:02d}.", size=6.2)
    seen, items = set(), []
    for p in sorted(sec, key=lambda p: -p["z1"]):
        ps = c.pos.get(p["id"])
        if ps and ps not in seen:
            seen.add(ps)
            items.append((ps, p))
    xr = v3.p(x1_, 0)[0] + 16
    anchors = []
    for i, (ps, p) in enumerate(items):
        u = (p["x0"] + p["x1"]) / 2 if p["x1"] - p["x0"] < 150 else min(p["x1"] - 20, p["x0"] + 40 + (i % 5) * 70)
        vz = (p["z0"] + p["z1"]) / 2
        anchors.append((v3.p(u, vz), ps, p))
    anchors.sort(key=lambda t: -t[0][1])
    gap_ = 6.0
    while True:
        ys, last = [], min(t3[1] + 10, 268) + gap_
        for (ax_, ay_), _, _ in anchors:
            y_ = min(ay_, last - gap_)
            ys.append(y_); last = y_
        if not ys or ys[-1] >= 62 or gap_ <= 4.4:
            break
        gap_ -= 0.3
    for ((ax_, ay_), ps, p), ty in zip(anchors, ys):
        sh.balloon(ax_, ay_, xr, ty, ps, r=2.4)
        sh.text(xr + 4, ty, p["unit"][:40], size=6.0, va="center")
    return sh


def drill_rows(s, pid, pos):
    """Таблица присадки детали: каждая строка — операция, грань входа, база, U, V (пары координат без измерения рисунка)."""
    p = next(q for q in s["parts"] if q["id"] == pid)
    n, up = view_dirs(s, p)
    fr = Frame(p, n, up)
    bu, bv = fr.base_corner()
    groups = {}
    for h in s["holes"]:
        if h["part"] != pid:
            continue
        dv = boardkit.vec(h["dir"])
        u, v = fr.uv(h["x"], h["y"], h["z"])
        if dv == fr.n or dv == boardkit.neg(fr.n):
            face = "пласть на виде" if dv == boardkit.neg(fr.n) else "обратная пласть"
            if h["through"]:
                face = "пласть на виде, насквозь" if dv == boardkit.neg(fr.n) else "обратная пласть, насквозь"
            w = None
        else:
            face = "торец «" + NAME[boardkit.name_of(boardkit.neg(dv))] + "»"
            w = round((fr.w0 + fr.t) - boardkit.dot((h["x"], h["y"], h["z"]), fr.n), 1)
        if not h["depth"] and not h["through"]:
            op = "разметка, без сверления"
        elif h["kind"] in ("hinge_cup",):
            op = "сверление (чашка)"
        else:
            op = "сверление"
        dep = "насквозь" if h["through"] else ("—" if not h["depth"] else f"{h['depth']:g}")
        if h.get("cs"):
            dep += ", зенковка " + ("на виде" if dv == boardkit.neg(fr.n) else "с обратной")
        node = NODE.get(h["kind"]) or ("Н" if h["kind"] == "pilot" and "MEZ" in h["joint"] or "SPACER" in h["joint"] else "")
        key = (boardkit.KIND_RU.get(h["kind"], h["kind"]), op, face, h["d"], dep, w, node)
        groups.setdefault(key, []).append((round(u, 1), round(v, 1)))
    rows = []
    for g in s["derived"].get("grooves", []):
        if g["part"] != pid:
            continue
        cx = ((g["x0"] + g["x1"]) / 2, (g["y0"] + g["y1"]) / 2, (g["z0"] + g["z1"]) / 2)
        nax = next(ax for ax in "xyz" if g[ax + "1"] - g[ax + "0"] == g["depth"] and (abs(g[ax + "0"] - p[ax + "0"]) < 0.01
                                                                                    or abs(g[ax + "1"] - p[ax + "1"]) < 0.01))
        dv = boardkit.vec(("-" if abs(g[nax + "1"] - p[nax + "1"]) < 0.01 else "+") + nax)
        face = "пласть на виде" if dv == boardkit.neg(fr.n) else "обратная пласть"
        u0, v0 = fr.uv(g["x0"], g["y0"], g["z0"])
        u1, v1 = fr.uv(g["x1"], g["y1"], g["z1"])
        rows.append(["паз под дно ящика", "фрезерование паза, по всей длине", face, f"шир. {n_(g['w'])}", n_(g["depth"]),
                     f"{n_(round(min(u0, u1), 1))}–{n_(round(max(u0, u1), 1))}",
                     f"{n_(round(min(v0, v1), 1))}–{n_(round(max(v0, v1), 1))}", "1", ""])
    for (kind, op, face, dd, dep, w, node), pts in sorted(groups.items(), key=lambda kv: (kv[0][2], -kv[0][3], kv[0][0])):
        byu = {}
        for u, v in pts:
            byu.setdefault(u, []).append(v)
        # строки: U постоянное — список V; если удобнее, V постоянное — список U
        byv = {}
        for u, v in pts:
            byv.setdefault(v, []).append(u)
        if len(byv) < len(byu):
            for v, us in sorted(byv.items()):
                rows.append([kind, op, face + (f", от пласти на виде {n_(w)}" if w is not None else ""), f"Ø{n_(dd)}", dep,
                             " / ".join(n_(x) for x in sorted(us)), n_(v), str(len(us)), node])
        else:
            for u, vs in sorted(byu.items()):
                rows.append([kind, op, face + (f", от пласти на виде {n_(w)}" if w is not None else ""), f"Ø{n_(dd)}", dep,
                             n_(u), " / ".join(n_(x) for x in sorted(vs)), str(len(vs)), node])
    return rows, f"база A — угол «{bu} / {bv}» готовой детали (с кромкой); вид — {'' if n[0] == '-' else ''}как на листе деталей"


def drill_blocks(c):
    s = c.s
    blocks = []
    for ps, ids in c.rep:
        p = next(q for q in s["parts"] if q["id"] == ids[0])
        if p["kind"] != "board":
            continue
        rows, base = drill_rows(s, ids[0], c.pos)
        if rows:
            blocks.append((ps, p, len(ids), rows, base))
    return blocks


DRILL_COLS = ["Назначение", "Операция", "Грань входа", "Ø", "Глубина", "U", "V", "Кол.", "Узел"]
DRILL_W = [46, 30, 72, 10, 42, 50, 98, 9, 9]
DRILL_SIZE, DRILL_LH = 6.3, 3.3


def _wrap_row(r):
    cells = []
    for c_, w in zip(r, DRILL_W):
        lim = max(4, int(w / (DRILL_SIZE * 0.2)))
        txt = str(c_)
        if "/" in txt and len(txt) > lim:            # переносим только между координатами
            out, line = [], ""
            for part in txt.split(" / "):
                cand = part if not line else line + " / " + part
                if len(cand) > lim and line:
                    out.append(line + " /"); line = part
                else:
                    line = cand
            out.append(line)
        else:
            out = textwrap.wrap(txt, lim) or [""]
        cells.append(out)
    return cells


def drill_pages(c, avail=216.0):
    pages, cur, used = [], [], 0.0
    for blk in drill_blocks(c):
        need = 6 + 5 + sum(max(len(x) for x in _wrap_row(r)) * DRILL_LH + 1.6 for r in blk[3]) + 3
        if cur and used + need > avail:
            pages.append(cur); cur, used = [], 0.0
        cur.append(blk); used += need
    if cur:
        pages.append(cur)
    return pages


def sheet_drill(c, page, i):
    s = c.s
    sh = Sheet("Таблица присадки", stamp_for(s), c.no["drill"][i], c.total, "—")
    sh.text(25, 283, "Координаты U (вправо) и V (вверх) — от базы A готовой детали, вид как на листе деталей; для торца — "
            "расстояние от пласти на виде. «Разметка» — без сверления. Узлы — лист " + f"{c.no['nodes']:02d}.", size=6.6,
            va="top")
    y = 275.0
    X = 25
    tot = sum(DRILL_W)
    for ps, p, cnt, rows, base in page:
        sh.text(X, y, f"Поз. {ps}  {p['unit']} — {cnt} шт.", size=7.6, weight="bold", va="top")
        sh.text(X + 110, y - 0.4, base, size=6.2, va="top", color="#333")
        y -= 6.0
        allr = [[[t] for t in DRILL_COLS]] + [_wrap_row(r) for r in rows]
        y0 = y
        for k, cells in enumerate(allr):
            nl = max(len(x) for x in cells)
            h = nl * DRILL_LH + 1.6
            sh.line(X, y, X + tot, y, THIN if k else dict(lw=0.8, color="k", ls="-"))
            cx = X
            for lines, w in zip(cells, DRILL_W):
                for j, t in enumerate(lines):
                    sh.text(cx + 1.0, y - 1.0 - j * DRILL_LH, t, size=DRILL_SIZE, va="top",
                            weight="bold" if k == 0 else "normal")
                cx += w
            y -= h
        sh.line(X, y, X + tot, y, dict(lw=0.8, color="k", ls="-"))
        cx = X
        for w in DRILL_W + [0]:
            sh.line(cx, y0, cx, y, THIN)
            cx += w
        y -= 4.0
    return sh


if __name__ == "__main__":
    a = sys.argv[1:]
    kv = dict(x.split("=", 1) for x in a[2:])
    s, checks, figs = write_kit(a[0], a[1], kv)
    out = Path(a[1]).with_suffix("")
    for i, f in enumerate(figs, 1):
        f.savefig(f"{out}-{i:02d}.png", dpi=90)
        plt.close(f)
    for nm, ok, t in checks:
        print("ok " if ok else "FAIL", nm, "—", t)
