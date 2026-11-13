"""2D-комплект из снимка: A3, проекции в стандартном масштабе, спецификация, раскрой, перечень деталей.

Геометрия берётся только из snapshot["parts"], поэтому чертёж совпадает с 3D, спецификацией и затратами.
Лист 1 — общий вид; далее — спецификация (детали, покупные, раскрой плит и труб, проверки) и перечень деталей.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from .core import SHEET, bom, cut_plan, tube_lengths  # noqa: E402

A3 = (420, 297)  # мм
IN = 25.4
RED = "#A23B2A"
SCALES = (5, 10, 15, 20, 25, 40, 50)
from . import fonts  # noqa: E402

FONTS = fonts.setup()        # шрифт — только из tools/eng/fonts/, иначе ошибка
NAMES = {k: v["name"] for k, v in json.loads(
    (Path(__file__).resolve().parents[2] / "catalog/prices.json").read_text(encoding="utf-8"))["materials"].items()}
KIND_RU = {"board": "плита", "tube": "труба", "timber": "брус", "plate": "лист", "cap": "заглушка", "glass": "стекло",
           "upholstery": "мягкая", "volume": "объём", "buy": "покупное"}


_MATS = json.loads((Path(__file__).resolve().parents[2] / "catalog/materials.json").read_text(encoding="utf-8"))
FINISH = {**{k: v["name"] for k, v in _MATS["colors"].items()}, **{k: v["name"] for k, v in _MATS["metal"].items()},
          **{"fab-" + k: v["name"] for k, v in _MATS["fabric"].items()},
          "INNER": "Белый (внутренний)", "STONE": "Кварц светлый", "steel": "Сталь/алюминий", "birch": "Берёза",
          "dark": "Тёмное стекло", "tint": "Тонированное", "mirror": "Зеркало"}


def fin_name(k):
    return FINISH.get(k, k or "")


def mat_name(k):
    return NAMES.get(k, k or "—")


def _opts(snap):
    return ", ".join(f"{k} {v}" for k, v in snap["options"].items())


def _page(title, sub, snap, n, total):
    fig = plt.figure(figsize=(A3[0] / IN, A3[1] / IN))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, A3[0]); ax.set_ylim(0, A3[1]); ax.axis("off")
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=0.8))
    ax.plot([10, 410], [265, 265], lw=0.6, c="k"); ax.plot([10, 410], [24, 24], lw=0.6, c="k")
    ax.text(16, 278, f"ARVELLO / {snap.get('product', snap['sku']).upper()}", fontsize=12, weight="bold", va="center")
    ax.text(16, 270, f"{n:02d} / {title}", fontsize=10, weight="bold", va="center")
    st = snap["rev_status"]
    ax.text(404, 278, f"{snap['rev']} · {st}", fontsize=7.5, color=RED, ha="right", va="center", weight="bold")
    ax.text(404, 270, sub, fontsize=8, ha="right", va="center")
    ax.text(16, 17, f"{snap['sku']} / {snap['rev']} / снимок {snap['hash']} / {_opts(snap)} / размеры в мм",
            fontsize=6.8, va="center")
    ax.text(404, 17, f"Лист {n} / {total}", fontsize=8, ha="right", va="center", weight="bold")
    ax.text(16, 13, "Разработал (Arvello): ____________   Проверил: ____________   "
                    "Создано генератором из снимка конфигурации; в производство не выдано", fontsize=6.5,
            va="center", color="#444")
    return fig, ax


def _proj(view):
    if view == "front":      # смотрим с переда: гор. x, верт. z, ближе = меньше y
        return (lambda p: (p["x0"], p["x1"])), (lambda p: (p["z0"], p["z1"])), (lambda p: -p["y0"])
    if view == "side":       # смотрим справа: гор. y (перед слева), верт. z, ближе = больше x
        return (lambda p: (p["y0"], p["y1"])), (lambda p: (p["z0"], p["z1"])), (lambda p: p["x1"])
    return (lambda p: (p["x0"], p["x1"])), (lambda p: (p["y0"], p["y1"])), (lambda p: p["z1"])


def _view(fig, snap, view, x_mm, y_mm, scale, title, skip=(), title_xy=None, box=None):
    """Проекция в истинном масштабе: x_mm, y_mm — левый нижний угол вида на листе."""
    parts = [p for p in snap["parts"] if p["group"] not in skip and p["kind"] != "buy_part"]
    H, V, far = _proj(view)
    if box:
        h0, h1, v0, v1 = box
    else:
        hs = [v for p in parts for v in H(p)]; vs = [v for p in parts for v in V(p)]
        h0, h1, v0, v1 = min(hs), max(hs), min(vs), max(vs)
    w, h = (h1 - h0) / scale, (v1 - v0) / scale
    ax = fig.add_axes([x_mm / A3[0], y_mm / A3[1], w / A3[0], h / A3[1]])
    ax.set_xlim(h0, h1); ax.set_ylim(v0, v1); ax.axis("off")
    for p in sorted(parts, key=far):
        (a, b), (c, d) = H(p), V(p)
        if p["kind"] == "context":
            ax.add_patch(Rectangle((a, c), b - a, d - c, fill=False, ec="#9A9DA2", lw=0.35, ls=(0, (3, 2)), clip_on=False))
            continue
        ls = (0, (4, 2)) if p["kind"] == "buy" else "-"
        fc = "#E8EDF0" if p["group"] == "top" else ("#D9DCE0" if p["kind"] in ("tube", "plate", "timber") else "white")
        ax.add_patch(Rectangle((a, c), b - a, d - c, fc=fc, ec="k", lw=0.45, ls=ls, clip_on=False))
    tx, ty = title_xy or (x_mm, y_mm - 4)
    fig.axes[0].text(tx, ty, title, fontsize=8, weight="bold", va="top")
    return ax, (h0, h1, v0, v1)


def _dim(ax, a, b, at, text, horiz=True, s=10):
    kw = dict(lw=0.5, c="k", clip_on=False)
    t = 1.2 * s
    if horiz:
        ax.plot([a, b], [at, at], **kw)
        for x in (a, b):
            ax.plot([x - t, x + t], [at - t, at + t], **kw)
        ax.text((a + b) / 2, at + 1.4 * s, text, ha="center", va="bottom", fontsize=7, clip_on=False)
    else:
        ax.plot([at, at], [a, b], **kw)
        for y in (a, b):
            ax.plot([at - t, at + t], [y - t, y + t], **kw)
        ax.text(at - 1.6 * s, (a + b) / 2, text, ha="right", va="center", fontsize=7, rotation=90, clip_on=False)


# ------------------------------------------------------------------ лист 1: общий вид

def sheet_general_opora(snap, pdf, n, total):
    d = snap["derived"]
    fig, page = _page("Общий вид и габариты", "масштаб видов 1:10", snap, n, total)
    s = 10
    ax, (x0, x1, z0, z1) = _view(fig, snap, "front", 30, 160, s, "Вид спереди", title_xy=(30, 138))
    _dim(ax, 0, d["length"], z1 + 60, f"{d['length']:g}")
    _dim(ax, 0, d["height"], -90, f"{d['height']:g}", horiz=False)
    _dim(ax, 0, 150, -60, "150")
    if d["link"]:
        _dim(ax, 190, 190 + d["link"], -140, f"{d['link']:g} (связь)")
    zf = d["feet_h"]
    _dim(ax, zf, zf + d["frame_h"], d["length"] + 90, f"{d['frame_h']:g} (рама)", horiz=False)
    if zf:
        _dim(ax, 0, zf, d["length"] + 170, f"{zf:g}", horiz=False)
    ax2, _ = _view(fig, snap, "side", 250, 160, s, "Вид справа", title_xy=(250, 138))
    _dim(ax2, 0, d["width"], d["height"] + 60, f"{d['width']:g}")
    _dim(ax2, 100, d["width"] - 100, -60, f"{d['bar']:g}")
    _view(fig, snap, "top", 30, 40, s, "Вид сверху\nбез столешницы\n(пунктир — контур\nстолешницы)",
          skip=("top",), title_xy=(197, 130), box=(0, d["length"], 0, d["width"]))
    fig.axes[-1].add_patch(Rectangle((0, 0), d["length"], d["width"], fill=False, lw=0.6, ls=(0, (6, 3))))
    fig.axes[-1].text(10, 20, "ПЕРЕД ↓  ·  X →", fontsize=6.5)
    y = 120
    page.text(250, y + 10, "Главные размеры", fontsize=8.5, weight="bold")
    rows = [("Столешница", f"{d['length']} × {d['width']} × {d['top_t']}"),
            ("Высота рамы", f"{d['frame_h']}"), ("Стойка", f"{d['leg']}"), ("Перекладина", f"{d['bar']}"),
            ("Связь", f"{d['link']}" if d["link"] else "нет"),
            ("Подпятник, уст. высота", f"{d['feet_h']}" if d["feet_h"] else "нет (рама на полу)"),
            ("Подпятники от кромки, Y", f"{d['feet_y']}" if d.get("feet_y") else "—"),
            ("Нагрузка на край до опрокидывания", f"≈ {d['tip_load_kg']} кг (оценка, масса {d['mass_kg']} кг)")]
    for i, (k, v) in enumerate(rows):
        page.text(250, y - i * 6, k, fontsize=7.5); page.text(330, y - i * 6, v, fontsize=7.5)
    pdf.savefig(fig); plt.close(fig)


def _bbox(snap):
    P = [p for p in snap["parts"] if p["kind"] != "buy_part"]
    return ([min(p[k] for p in P) for k in ("x0", "y0", "z0")], [max(p[k] for p in P) for k in ("x1", "y1", "z1")])


def pick_scale(W, D, H):
    for s in SCALES:
        if W / s + 40 + D / s <= 360 and H / s + D / s + 60 <= 205:
            return s
    return SCALES[-1]


def sheet_general(snap, pdf, n, total):
    lo, hi = _bbox(snap)
    W, D, H = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
    s = pick_scale(W, D, H)
    fig, page = _page("Общий вид и габариты", f"масштаб видов 1:{s}", snap, n, total)
    y_top, x0 = 44, 30
    y_front = y_top + D / s + 34
    axf, _ = _view(fig, snap, "front", x0, y_front, s, "Вид спереди", box=(lo[0], hi[0], lo[2], hi[2]))
    _dim(axf, lo[0], hi[0], hi[2] + 4 * s, f"{W:.0f}", s=s)
    _dim(axf, lo[2], hi[2], lo[0] - 5 * s, f"{H:.0f}", horiz=False, s=s)
    axs, _ = _view(fig, snap, "side", x0 + W / s + 40, y_front, s, "Вид справа", box=(lo[1], hi[1], lo[2], hi[2]))
    _dim(axs, lo[1], hi[1], hi[2] + 4 * s, f"{D:.0f}", s=s)
    _view(fig, snap, "top", x0, y_top, s, "Вид сверху", box=(lo[0], hi[0], lo[1], hi[1]))
    fig.axes[-1].text(lo[0] + 2 * s, lo[1] + 2 * s, "ПЕРЕД ↓", fontsize=6.5)
    page.text(404, 28, "Сплошная линия — детали изделия · штрих — покупные изделия · серый штрих — не входит в изделие "
                       "(техника, матрас, декор для фото)", fontsize=6.3, ha="right", color="#555")
    pdf.savefig(fig); plt.close(fig)


# ------------------------------------------------------------------ спецификация (с переносом на новые листы)

def _spec_lines(snap):
    b = bom(snap)
    d = snap["derived"]
    L = []
    if "width" in d and "length" not in d:
        L.append(("text", f"Габарит изделия: {d['width']} × {d['depth']} × {d['height']} мм (ширина × глубина × высота)"))
    for w in snap["warnings"]:
        L.append(("warn", "• " + w))
    L.append(("gap",))
    L.append(("h", "Изготавливаемые детали"))
    L.append(("th", ("Наименование", "Материал", "Декор / цвет", "Размер, мм", "Кол.", "Кромка, м")))
    for r in b["made"]:
        L.append(("tr", (r["unit"], mat_name(r["material"]), fin_name(r.get("finish", "")), r["size"], str(r["qty"]),
                         f"{r['edge_m']:.1f}" if r.get("edge_m") else "")))
    if b["buy"]:
        L.append(("gap",)); L.append(("h", "Покупные изделия"))
        L.append(("th", ("Наименование", "Спецификация", "", "Статус", "Кол.", "Ед.")))
        for h in b["buy"]:
            L.append(("tr", (h["name"], h["spec"], "", h["status"] + (f"; {h['note']}" if h.get("note") else ""),
                             f"{h['qty']:g}", h.get("uom", "шт"))))
    if b["sheets"]:
        L.append(("gap",))
        L.append(("h", f"Раскрой плит (лист {SHEET[0]} × {SHEET[1]}, торцовка 10, пропил 4; оценка полосами)"))
        L.append(("th", ("Материал", "Декор", "Деталей", "Площадь, м²", "Листов", "Заполнение")))
        for x in b["sheets"]:
            L.append(("tr", (mat_name(x["material"]), fin_name(x["finish"]), str(x["parts"]), f"{x['area_m2']:.2f}",
                             str(x["sheets"]), f"{x['use'] * 100:.0f}%")))
            if x["oversize"]:
                L.append(("warn", f"   Не помещается в лист ({mat_name(x['material'])}): {', '.join(x['oversize'])} — нужен стык или другой формат"))
    tubes = sorted({p["material"] for p in snap["parts"] if p["kind"] == "tube"})
    for t in tubes:
        bars = cut_plan(tube_lengths(snap, t))
        L.append(("gap",)); L.append(("h", f"Раскрой: {mat_name(t)} (хлыст 6000, пропил 3, торцовка 10 × 2)"))
        for i, bar in enumerate(bars, 1):
            L.append(("text", f"Хлыст {i}: " + " + ".join(f"{x:g}" for x in bar["pieces"]) + f"; остаток {bar['rest']:g}"))
    if snap["checks"]:
        L.append(("gap",)); L.append(("h", "Проверки правил"))
        for c in snap["checks"]:
            L.append(("chk", c))
    return L


def _parts_lines(snap):
    L = [("h", "Перечень деталей (id совпадают с 3D и спецификацией)"),
         ("th", ("ID", "Наименование", "Вид", "Материал", "Декор / цвет", "Размер L × W × T, мм", "Кромка, м"))]
    for p in snap["parts"]:
        if p["kind"] in ("context", "buy_part"):
            continue
        dims = sorted(p.get("bom_size") or (p["x1"] - p["x0"], p["y1"] - p["y0"], p["z1"] - p["z0"]), reverse=True)
        L.append(("tr7", (p["id"], p["unit"] or p["name"], KIND_RU.get(p["kind"], p["kind"]), mat_name(p["material"]),
                          fin_name(p.get("finish", "")), " × ".join(f"{x:g}" for x in dims),
                          f"{p['edge_m']:.2f}" if p.get("edge_m") else "")))
    return L


COLS6 = (20, 100, 175, 250, 345, 375)
COLS7 = (20, 70, 150, 180, 255, 305, 380)
ROW = 5.4


def _paginate(lines, top=255, bottom=30):
    pages, cur, y, last_th = [], [], top, None
    for ln in lines:
        need = 8 if ln[0] == "h" else (3 if ln[0] == "gap" else ROW)
        if y - need < bottom:
            pages.append(cur); cur, y = [], top
            if ln[0] in ("tr", "tr7") and last_th:
                cur.append(last_th); y -= ROW
        if ln[0] == "th":
            last_th = ln
        cur.append(ln); y -= need
    if cur:
        pages.append(cur)
    return pages


def _render(page, lines, top=255):
    y = top
    for ln in lines:
        k = ln[0]
        if k == "gap":
            y -= 3; continue
        if k == "h":
            page.text(20, y, ln[1], fontsize=9, weight="bold"); y -= 8; continue
        if k in ("text", "warn"):
            page.text(20, y, ln[1], fontsize=7, color=RED if k == "warn" else "k"); y -= ROW; continue
        if k == "chk":
            c = ln[1]
            page.text(20, y, ("✓ " if c["ok"] else "✗ ") + f"{c['name']}: ожидается {c['expected']}, получено {c['actual']}",
                      fontsize=7, color="k" if c["ok"] else RED); y -= ROW; continue
        cols = COLS7 if (k == "tr7" or (k == "th" and len(ln[1]) == 7)) else COLS6
        for c, v in zip(cols, ln[1]):
            txt = str(v)
            lim = 30 if c in (100, 250, 70) else 22
            if len(txt) > lim + 8 and c not in (20,):
                txt = txt[:lim + 6] + "…"
            page.text(c, y, txt, fontsize=6.8, weight="bold" if k == "th" else "normal")
        y -= ROW


def write_pdf(snap, path):
    spec_pages = _paginate(_spec_lines(snap))
    part_pages = _paginate(_parts_lines(snap))
    total = 1 + len(spec_pages) + len(part_pages)
    with PdfPages(path) as pdf:
        if snap["sku"] == "ARV-TBL-003":
            sheet_general_opora(snap, pdf, 1, total)
        else:
            sheet_general(snap, pdf, 1, total)
        n = 2
        for i, pg in enumerate(spec_pages):
            fig, page = _page("Спецификация и раскрой" + (f" (продолжение {i})" if i else ""),
                              "из того же снимка, что 3D и затраты", snap, n, total)
            _render(page, pg); pdf.savefig(fig); plt.close(fig); n += 1
        for i, pg in enumerate(part_pages):
            fig, page = _page("Перечень деталей" + (f" (продолжение {i})" if i else ""),
                              "оценка по 3D; присадка и крепёж не разработаны" if snap["rev"] == "R00" else "детали ревизии",
                              snap, n, total)
            _render(page, pg); pdf.savefig(fig); plt.close(fig); n += 1
        pdf.infodict()["Title"] = f"{snap['sku']} {snap['rev']} {snap['hash']}"
    return total
