"""ENG-002 · инструкция сборщику ящика комода ARV-NST-101 на A4 (план П11–П14).

Подход взят из инструкций с крупными рисунками (сравнение с IKEA HEMNES — docs/eng-002/01, раздел 6); рисунки не копируются,
всё строится из модели генератора:
  П11 — круг-увеличение у каждого соединения: сечение по отверстию из модели, крепёж, инструмент, вращение, «N ×»;
  П12 — набор «Ящик» с крепежом в натуральную величину (печать 100 %, контрольная линейка 50 мм);
  П13 — пары «правильно / неправильно» в местах реальных ошибок;
  П14 — A4 книжный, одно действие — один рисунок, текст ≤ 2 строк + рамка «проверить».
Проверки при выпуске: крепёж на рисунке — с видимой незакрытой стороны (Oblique.fasteners), тексты не накладываются,
круг-увеличение показывает отверстие своего шага. Пример — НЕ утверждён, не для изготовления.

Запуск: python3 tools/eng/eng002_guide.py out.pdf [width=1200 changer=yes]
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

from eng import eng002_drawer as E  # noqa: E402
from eng.cab import FASTENERS  # noqa: E402
from eng.kit13 import n_ as kit13_n  # noqa: E402
from eng.sheetlib import IN, RED, Sheet  # noqa: E402

A4 = (210.0, 297.0)
OKC, BADC, BLUE = "#2e7d32", RED, "#1f5fa8"
WOOD, WOOD2 = "#f3d6ae", "#e8e8e8"


class Page(Sheet):
    """Страница A4 книжная: рамка, колонтитул с обозначением и статусом. Методы рисования — от Sheet."""

    def __init__(self, D, n, total, title):
        self.fig = plt.figure(figsize=(A4[0] / IN, A4[1] / IN))
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, A4[0]); ax.set_ylim(0, A4[1]); ax.axis("off")
        self.ax = ax
        s = D["s"]
        ax.text(10, 289, "ПРИМЕР ENG-002 — НЕ УТВЕРЖДЕНО, НЕ ДЛЯ ИЗГОТОВЛЕНИЯ", fontsize=6.5, color=RED, weight="bold")
        ax.text(200, 289, title, fontsize=7, ha="right", weight="bold")
        ax.plot([10, 200], [286, 286], lw=0.6, c="k")
        ax.plot([10, 200], [11, 11], lw=0.6, c="k")
        ax.text(10, 7, f"ARV-NST-101 · {D.get('doc_label', 'ящик')} · снимок {s['hash']} · инструкция сборщику "
                f"(A4, печать 100 %)", fontsize=6)
        ax.text(200, 7, f"{n} / {total}", fontsize=7, ha="right", weight="bold")

    def check_overlaps(self, tol=0.6):
        r = self.fig.canvas.get_renderer()
        px = self.fig.bbox.width / A4[0]
        boxes = [(t.get_window_extent(r), t.get_text()) for t in self.ax.texts if t.get_text().strip()]
        bad = []
        for i, (a, ta) in enumerate(boxes):
            if a.x0 < 8 * px or a.x1 > 202 * px or a.y0 < 4 * px or a.y1 > 293 * px:
                bad.append(("за рамкой", ta[:40], ""))
            for b, tb in boxes[i + 1:]:
                ox = min(a.x1, b.x1) - max(a.x0, b.x0)
                oy = min(a.y1, b.y1) - max(a.y0, b.y0)
                if ox > tol * px and oy > tol * px:
                    bad.append(("наложение", ta[:40], tb[:40]))
        return bad


# ------------------------------------------------------------------ крепёж: размеры из обозначения
def fdims(fid):
    """(диаметр, длина) из обозначения крепежа: CONF-7x50 → (7, 50); SCREW-4x25D → (4, 25)."""
    m = re.search(r"(\d+(?:\.\d+)?)x(\d+)", fid or "")
    return (float(m.group(1)), float(m.group(2))) if m else (4.0, 20.0)


def screw_shape(ax, x, y, d, L, ang=0.0, kind="screw", sc=1.0, color="#555", z=20):
    """Крепёж в координатах листа: головка в (x, y), ось — по углу ang (рад), длина L × sc. Головка — условно."""
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (x + (u * ca - v * sa) * sc, y + (u * sa + v * ca) * sc)
    hd = d * (1.9 if kind == "conf" else 2.0)                 # головка — условно, не по стандарту
    head = [P(0, -hd / 2), P(d * 0.6, -d / 2), P(d * 0.6, d / 2), P(0, hd / 2)]
    shank = [P(d * 0.6, -d / 2), P(L - d * 0.8, -d / 2), P(L, 0), P(L - d * 0.8, d / 2), P(d * 0.6, d / 2)]
    ax.add_patch(Polygon(shank, closed=True, fc="#9aa3ad", ec="k", lw=0.5, zorder=z))
    ax.add_patch(Polygon(head, closed=True, fc="#7b848e", ec="k", lw=0.5, zorder=z + 1))
    nturn = int(L / max(1.4, d * 0.45))
    for k in range(1, nturn):
        u = d * 0.6 + k * (L - d * 1.4) / nturn
        a, b = P(u, -d / 2), P(u + d * 0.35, d / 2)
        ax.plot([a[0], b[0]], [a[1], b[1]], lw=0.35, c="k", zorder=z + 1)


def rot_arrow(ax, x, y, r=4.5, color=BLUE, z=25):
    ax.add_patch(Arc((x, y), 2 * r, 2 * r, theta1=30, theta2=300, lw=1.3, color=color, zorder=z))
    t = math.radians(300)
    ex, ey = x + r * math.cos(t), y + r * math.sin(t)
    ax.add_patch(FancyArrowPatch((ex - 0.8, ey - 1.2), (ex + 0.9, ey + 0.4), arrowstyle="-|>", mutation_scale=8,
                                 color=color, lw=1.1, zorder=z))


def count_badge(pg, x, y, n, pos, text):
    pg.text(x, y, f"{n}×", size=13, weight="bold", va="center", zorder=30)
    E.pos_ball(pg, x + 14, y, pos, r=3.6)
    pg.text(x + 19.5, y, text, size=7.5, va="center", zorder=30)


# ------------------------------------------------------------------ П11: круг-увеличение по отверстию из модели
def zoom(pg, D, h, cx, cy, R=27, win=34.0, label="", keys=("SL", "SR", "F", "B", "BOT"), vertical=False, face=None, flip=False, allowed=None):
    """Сечение плоскостью через ось отверстия h, окно ±win мм вокруг входа; крепёж из h["fastener"].
    В сечении — только детали, собранные к этому шагу (keys): корпуса и других ящиков на столе нет.
    Ось крепежа — горизонтально (головка слева) или вертикально (головка снизу, vertical=True)."""
    a = h["dir"][1]
    s = 1 if h["dir"][0] == "+" else -1
    b = "z" if a != "z" else "y"                    # вторая ось сечения (вертикаль круга)
    c = next(k for k in "xyz" if k not in (a, b))   # ось, перпендикулярная плоскости сечения
    sc = R / win
    ax = pg.ax
    clip = Circle((cx, cy), R, transform=ax.transData)
    U = lambda q: (q - h[a]) * s
    V = lambda q: q - h[b]
    allowed = set(allowed) if allowed is not None else {D["ids"][k] for k in keys}
    parts = [p for p in D["s"]["parts"] if p["id"] in allowed and p[c + "0"] <= h[c] <= p[c + "1"]
             and p[a + "1"] >= h[a] - win * 1.5 and p[a + "0"] <= h[a] + win * 1.5
             and p[b + "1"] >= h[b] - win * 1.5 and p[b + "0"] <= h[b] + win * 1.5]
    ax.add_patch(Circle((cx, cy), R, fc="white", ec="none", zorder=14))
    for p in parts:
        u0, u1 = sorted((U(p[a + "0"]), U(p[a + "1"])))
        v0, v1 = V(p[b + "0"]), V(p[b + "1"])
        fc = WOOD if p["group"] == "fronts" else WOOD2
        if vertical:                                # ось крепежа — вертикально; flip — вниз (ящик перевёрнут)
            u0, u1, v0, v1 = (v0, v1, -u1, -u0) if flip else (v0, v1, u0, u1)
        rect = Rectangle((cx + u0 * sc, cy + v0 * sc), (u1 - u0) * sc, (v1 - v0) * sc, fc=fc, ec="k", lw=0.7,
                         hatch="////" if p["id"] == h["part"] else "\\\\\\\\", zorder=15)
        rect.set_clip_path(clip)
        ax.add_patch(rect)
    d, L = fdims(h.get("fastener"))
    kind = "conf" if "CONF" in (h.get("fastener") or "") else "screw"
    ang = (-math.pi / 2 if flip else math.pi / 2) if vertical else 0.0
    screw_shape(ax, cx, cy, d, L, ang, kind, sc, z=18)
    ax.add_patch(Circle((cx, cy), R, fc="none", ec="k", lw=1.4, zorder=22))
    rot_arrow(ax, cx - R * 0.55, cy + R * 0.55 if (flip or not vertical) else cy - R * 0.55)
    if face:
        fx, fy, txt = face
        pg.text(cx + fx * R, cy + fy * R, txt, size=7, ha="center", va="center", zorder=31,
                bbox=dict(fc="white", ec="none", pad=0.5))
    if label:
        pg.text(cx, cy - R - 3.5, label, size=7.2, ha="center", va="top", zorder=30)
    return {"a": a, "b": b, "c": c, "parts": [p["id"] for p in parts], "entry_part": h["part"]}


# ------------------------------------------------------------------ П13: пары «правильно / неправильно»
def mark(ax, x, y, ok):
    if ok:
        ax.plot([x - 3, x - 1, x + 3.5], [y, y - 2.5, y + 3], lw=2.2, c=OKC, zorder=30)
    else:
        ax.plot([x - 3, x + 3], [y - 3, y + 3], lw=2.2, c=BADC, zorder=30)
        ax.plot([x - 3, x + 3], [y + 3, y - 3], lw=2.2, c=BADC, zorder=30)


def pair_box(pg, x, y, w, h, draw_ok, draw_bad, cap_ok, cap_bad):
    for i, (fn, cap, ok) in enumerate(((draw_ok, cap_ok, True), (draw_bad, cap_bad, False))):
        x0 = x + i * (w / 2 + 2)
        pg.ax.add_patch(Rectangle((x0, y), w / 2 - 2, h, fc="none", ec=OKC if ok else BADC, lw=1.2, zorder=5))
        fn(pg.ax, x0 + (w / 2 - 2) / 2, y + h / 2 + 3)
        mark(pg.ax, x0 + 6, y + h - 6, ok)
        pg.text(x0 + (w / 2 - 2) / 2, y + 2.5, cap, size=6.8, ha="center", va="bottom")


def _sec(ax, x, y, w, h, fc=WOOD2, hatch="////"):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="k", lw=0.7, hatch=hatch, zorder=10))


def groove_ok(ax, cx, cy):          # боковина (вертикально), паз внизу, дно в пазу
    _sec(ax, cx - 14, cy - 12, 4, 26)
    ax.add_patch(Rectangle((cx - 11, cy - 8.5), 1.6, 3.2, fc="white", ec="k", lw=0.5, zorder=11))
    _sec(ax, cx - 11.2, cy - 8.5, 24, 3.2, WOOD2, "\\\\\\\\")
    _sec(ax, cx + 4, cy - 5.3, 3.2, 15, WOOD2, "\\\\\\\\")


def groove_bad(ax, cx, cy):         # паз вверху — дно не на месте
    _sec(ax, cx - 14, cy - 12, 4, 26)
    ax.add_patch(Rectangle((cx - 11, cy + 8.5), 1.6, 3.2, fc="white", ec="k", lw=0.5, zorder=11))
    _sec(ax, cx - 10, cy - 8.5, 22, 3.2, WOOD2, "\\\\\\\\")


def front_ok(ax, cx, cy):           # фасад + стенка, саморез изнутри (справа), лицо слева — чистое
    _sec(ax, cx - 12, cy - 13, 7, 26, WOOD)
    _sec(ax, cx - 5, cy - 10, 6, 23)
    screw_shape(ax, cx + 7, cy, 1.6, 10, math.pi, "screw", 1.0, z=12)
    ax.text(cx - 13, cy + 14, "лицо", fontsize=5.5, ha="right")


def front_bad(ax, cx, cy):          # саморез через лицо фасада
    _sec(ax, cx - 12, cy - 13, 7, 26, WOOD)
    _sec(ax, cx - 5, cy - 10, 6, 23)
    screw_shape(ax, cx - 17, cy, 1.6, 10, 0.0, "screw", 1.0, z=12)
    ax.text(cx - 13, cy + 14, "лицо", fontsize=5.5, ha="right")


def head_ok(ax, cx, cy):            # головка заподлицо с дном
    _sec(ax, cx - 14, cy - 2, 28, 4)
    _sec(ax, cx - 3, cy + 2, 6, 12, WOOD2, "\\\\\\\\")
    screw_shape(ax, cx, cy - 2, 1.6, 10, math.pi / 2, "screw", 1.0, z=12)


def head_bad(ax, cx, cy):           # головка выступает — заденет направляющую
    _sec(ax, cx - 14, cy - 2, 28, 4)
    _sec(ax, cx - 3, cy + 2, 6, 12, WOOD2, "\\\\\\\\")
    screw_shape(ax, cx, cy - 5, 1.6, 10, math.pi / 2, "screw", 1.0, z=12)


# ------------------------------------------------------------------ П16: наклейки-различители
def side_letter(name):
    """Л / П по наименованию детали (левая / правая); иначе пусто."""
    n = name.lower()
    return "Л" if "лев" in n or n.endswith(" л") else "П" if "прав" in n or n.endswith(" п") else ""


def sticker(pg, x, y, pos, letter, z=16):
    """Наклейка на детали (как её видит сборщик): номер позиции + Л / П."""
    w = 13 if letter else 8
    pg.ax.add_patch(Rectangle((x, y - 3.2), w, 6.4, fc="#fffbe6", ec="k", lw=0.8, zorder=z))
    pg.text(x + 1.2, y, str(pos), size=7.5, va="center", weight="bold", zorder=z + 1)
    if letter:
        pg.text(x + w - 1.2, y, letter, size=9, va="center", ha="right", weight="bold", color=RED, zorder=z + 1)


# ------------------------------------------------------------------ рамки
def check_box(pg, x, y, w, lines):
    h = 6 + 4.2 * len(lines)
    pg.ax.add_patch(Rectangle((x, y - h), w, h, fc="#eef5ee", ec=OKC, lw=1.0, zorder=3))
    pg.text(x + 3, y - 4, "ПРОВЕРИТЬ", size=7.5, weight="bold", color=OKC, va="center")
    for i, t in enumerate(lines):
        pg.text(x + 3, y - 8.5 - i * 4.2, t, size=7.5, va="center")
    return y - h


STEP_PREFIX = {"p": ""}           # «Я» внутри инструкции комода: шаги Я1…Я10 (сквозные ссылки)


def step(pg, x, y, n, title, prefix=None):
    lab = f"{STEP_PREFIX['p'] if prefix is None else prefix}{n}"
    pg.ax.add_patch(Polygon([(x, y - 9), (x + 16, y - 9), (x + 16, y + 3), (x, y + 3)], fc="k", ec="k", zorder=5))
    pg.text(x + 8, y - 3, lab, size=15 if len(lab) <= 2 else 11.5, ha="center", va="center", color="white",
            weight="bold", zorder=6)
    pg.text(x + 20, y - 3, title, size=9.5, va="center", weight="bold")


def figure(pg, D, box, items, **kw):
    ob = E.Oblique(pg, box, [b for b, _, _ in items], **kw)
    ob.draw(items)
    return ob



# ------------------------------------------------------------------ вид снизу (ящик перевёрнут на стол, перед — к себе)
def bottom_view(pg, D, box, holes=(), zones=(), title="вид на дно ящика: ящик перевёрнут, перед — к себе"):
    """Ортогональный вид на наружную нижнюю пласть дна. Ящик перевёрнут через переднюю кромку на стол: лево осталось
    слева, перед — внизу листа. Видны: торцы боковин (низ), дно между боковинами; стенки стоят на дне — их не видно
    (пунктир). Крепёж — только отверстия со входом снизу (dir «+z»), иначе ошибка в D["view_errors"]."""
    p, pos = D["p"], D["pos"]
    SL, SR, BT, F, B = p["SL"], p["SR"], p["BOT"], p["F"], p["B"]
    x0, y0, x1, y1 = box
    X0, X1, Y0, Y1 = SL["x0"], SR["x1"], SL["y0"], SL["y1"]
    sc = min((x1 - x0) / (X1 - X0), (y1 - y0) / (Y1 - Y0))
    ox = x0 + ((x1 - x0) - (X1 - X0) * sc) / 2
    oy = y0 + ((y1 - y0) - (Y1 - Y0) * sc) / 2
    P_ = lambda x, y: (ox + (x - X0) * sc, oy + (y - Y0) * sc)
    def R_(a, b, fc, ls="-", lw=0.9, z=5, hatch=None):
        (u0, v0), (u1, v1) = P_(a[0], a[1]), P_(b[0], b[1])
        pg.ax.add_patch(Rectangle((u0, v0), u1 - u0, v1 - v0, fc=fc, ec="k", lw=lw, ls=ls, zorder=z, hatch=hatch))
    R_((SL["x1"], BT["y0"]), (SR["x0"], BT["y1"]), WOOD, z=4)                          # дно — наружная пласть
    for S in (SL, SR):
        R_((S["x0"], S["y0"]), (S["x1"], S["y1"]), "#d9d9d9", z=5)                         # низ боковин
    for W in (F, B):
        R_((W["x0"], W["y0"]), (W["x1"], W["y1"]), "none", ls=(0, (3, 2)), lw=0.6, z=6)   # стенки — за дном
    for zn in zones:
        R_((zn[0], zn[1]), (zn[2], zn[3]), "#cfe0f5", ls=(0, (3, 2)), lw=1.1, z=7)
    for h in holes:
        if h["dir"] != "+z":
            D["view_errors"].append(f"вид снизу: {h['part']} — вход не снизу ({h['dir']})")
        u, v = P_(h["x"], h["y"])
        pg.ax.add_patch(Circle((u, v), 1.6, fc=RED, ec="k", lw=0.5, zorder=12))
    u, v = P_((X0 + X1) / 2, Y0)
    pg.text(u, v - 4, "ПЕРЕД (фасад) — к себе", size=7.5, ha="center", va="top", weight="bold")
    for S, let, k in ((SL, "Л", "SL"), (SR, "П", "SR")):
        u, v = P_((S["x0"] + S["x1"]) / 2, Y1)
        sticker(pg, u - 6.5, v + 5, pos[k], let)
    pg.text((x0 + x1) / 2, y1 + 13, title, size=7, ha="center", style="italic")
    return P_


def flip_icon(pg, x, y):
    """Пиктограмма: ящик переворачивают через переднюю кромку (вид сбоку)."""
    pg.ax.add_patch(Rectangle((x, y), 16, 7, fc=E.DONE, ec="k", lw=0.8))
    pg.ax.add_patch(Rectangle((x, y), 16, 1.6, fc=WOOD, ec="k", lw=0.6))
    pg.ax.add_patch(FancyArrowPatch((x + 16, y + 9), (x + 30, y + 9), connectionstyle="arc3,rad=-0.6",
                                    arrowstyle="-|>", mutation_scale=10, color=RED, lw=1.3))
    pg.ax.add_patch(Rectangle((x + 32, y), 16, 7, fc=E.DONE, ec="k", lw=0.8))
    pg.ax.add_patch(Rectangle((x + 32, y + 5.4), 16, 1.6, fc=WOOD, ec="k", lw=0.6))
    pg.text(x + 24, y - 3, "дно — вверх", size=6.5, ha="center", va="top")

# ================================================================== страницы
def page_set(D, n, total):
    pg = Page(D, n, total, "Набор «Ящик»")
    p, pos, H, hp, nd = D["p"], D["pos"], D["H"], D["hpos"], D["nd"]
    pg.ax.add_patch(Rectangle((10, 252), 190, 30, fc="#fff3e0", ec="k", lw=1.2))
    pg.text(16, 274, "ЯЩИК", size=20, weight="bold", va="center")
    pg.text(16, 262, f"собрать 1 → проверить с фасадом → ещё {nd - 1}", size=10, va="center")
    pg.text(16, 255.5, "Всё ниже — на ОДИН ящик; ×6 — число таких наборов, крепёж не умножать.", size=7.5, va="center")
    ob = E.Oblique(pg, (138, 255, 196, 280), [p[k] for k in ("SL", "SR", "F", "B", "BOT")], sgn=1)
    ob.draw([(p[k], E.DONE, {}) for k in ("SL", "SR", "F", "B", "BOT")])
    pg.text(125, 267, f"×{nd}", size=20, weight="bold", va="center", ha="center")
    pg.text(12, 245, "Детали (номер — на наклейке детали)", size=9, weight="bold")
    cells = [("SL", "боковина Л"), ("SR", "боковина П"), ("BOT", "дно"), ("F", "стенка передняя"),
             ("B", "стенка задняя"), ("FR", "фасад")]
    for i, (k, nm) in enumerate(cells):
        x, y = 12 + (i % 3) * 64, 210 - (i // 3) * 34
        b = p[k]
        g = next((q for q in D["grooves"] if q["part"] == b["id"]), None)
        ob = E.Oblique(pg, (x + 10, y, x + 40, y + 26), [b], sgn=1 if k != "SR" else -1)
        ob.draw([(b, E.HL, {"groove": g} if g else {})])
        E.pos_ball(pg, x + 4, y + 22, pos[k], r=3.6)
        pg.text(x + 25, y - 3, f"1× {nm}", size=7.5, va="center", ha="center")
        let = side_letter(b["name"])
        if let:
            sticker(pg, x + 40, y + 6, pos[k], let)
    pg.text(12, 166, "Крепёж — в натуральную величину (головки условно)", size=9, weight="bold")
    cnt = lambda key, kind: len(E.joint_holes(D, key, kind))
    fx = [("CONF-7x50", cnt("BOX", "conf_face"), "конфирмат 7 × 50", "conf"),
          ("SCREW-4x25D", cnt("BOT-", "screw_face"), "саморез 4 × 25 — дно", "screw"),
          ("SCREW-4x25", cnt("FRONT", "front_screw"), "саморез 4 × 25 — фасад", "screw")]
    for i, (hid, q, nm, kind) in enumerate(fx):
        y = 155 - i * 14
        d, L = fdims(hid)
        screw_shape(pg.ax, 14, y, d, L, 0.0, kind, 1.0)
        pg.text(70, y, f"{q}×", size=13, weight="bold", va="center")
        E.pos_ball(pg, 84, y, hp[hid], r=3.6)
        pg.text(90, y, nm, size=8, va="center")
    lq = H["LOCK-SCREW"]["qty"] // max(1, nd)
    pg.text(12, 108, f"Фурнитура ящика: замок MOVENTO Л + П — 1 пара (поз. {hp['SLIDE-LOCK']}), саморезы замка — {lq} "
            f"(поз. {hp['LOCK-SCREW']}, по поставке Blum).", size=7.5)
    pg.text(12, 103, "Направляющие, TIP-ON и синхронизация — набор «Корпус», не здесь.", size=7.5)
    # контрольная линейка 50 мм
    pg.line(14, 92, 64, 92, dict(lw=1.2, color="k", ls="-"))
    for k in range(6):
        pg.line(14 + k * 10, 92, 14 + k * 10, 94.5 if k % 5 else 96, dict(lw=0.8, color="k", ls="-"))
    pg.text(70, 93, "50 мм — проверка печати: должно совпасть с линейкой", size=7.5, va="center")
    pg.text(12, 80, "Инструмент", size=9, weight="bold")
    pg.text(12, 74, "шестигранник 4 · отвёртка PH2 · шаблон Blum T65.1000.02 · рулетка · угольник", size=8)
    pg.text(12, 62, "Как работать", size=9, weight="bold")
    pg.text(12, 56, "на мягкой подложке · детали сверить по номерам до начала · первый ящик — целиком с фасадом", size=8)
    pg.text(12, 50, "и проверкой, только потом остальные", size=8)
    pg.text(12, 38, "[М] — по нашей модели; размеры крепежа — из спецификации комплекта.", size=7, color="#444")
    return pg


def page_box1(D, n, total):
    pg = Page(D, n, total, "Ящик · шаги 1–2")
    p, pos = D["p"], D["pos"]
    g = {x["part"]: x for x in D["grooves"]}
    step(pg, 12, 279, 1, f"Дно {pos['BOT']} — в паз боковины {pos['SL']}")
    bm = E.moved(p["BOT"], dx=260)
    ob = figure(pg, D, (16, 200, 150, 268), [(p["SL"], E.HL, {"groove": g[p["SL"]["id"]]}), (bm, E.HL, {})], sgn=1)
    b = p["BOT"]
    ob.arrow((b["x1"] + 250, (b["y0"] + b["y1"]) / 2, b["z1"] + 40), (b["x1"] + 120, (b["y0"] + b["y1"]) / 2, b["z1"] + 40))
    E.pos_ball(pg, *ob.p(p["SL"]["x0"], p["SL"]["y0"], p["SL"]["z1"] + 15), pos["SL"], r=3.6)
    E.pos_ball(pg, *ob.p(bm["x1"], bm["y0"], bm["z1"] + 25), pos["BOT"], r=3.6)
    sticker(pg, *ob.p(p["SL"]["x0"], p["SL"]["y1"], p["SL"]["z1"] + 40), pos["SL"], "Л")
    pair_box(pg, 152, 214, 48, 40, groove_ok, groove_bad, "паз внизу", "паз вверху")
    check_box(pg, 16, 196, 184, ["дно входит от руки, края заподлицо спереди и сзади",
                                 "туго или болтается — стоп, сообщить Arvello (зазор паза — наше значение [М], проба [О])"])
    step(pg, 12, 160, 2, f"Стенки {pos['F']} и {pos['B']} — на дно, к боковине {pos['SL']}")
    Fm, Bm = E.moved(p["F"], dz=90), E.moved(p["B"], dz=90)
    ob2 = figure(pg, D, (16, 60, 196, 150), [(p["SL"], E.DONE, {}), (p["BOT"], E.DONE, {}), (Fm, E.HL, {}), (Bm, E.HL, {})],
                 sgn=1)
    for w, wm in ((p["F"], Fm), (p["B"], Bm)):
        xc, yc = (w["x0"] + w["x1"]) / 2, (w["y0"] + w["y1"]) / 2
        ob2.arrow((xc, yc, wm["z0"] - 5), (xc, yc, w["z0"] + 25))
    E.pos_ball(pg, *ob2.p(Fm["x1"], Fm["y0"], Fm["z1"] + 10), pos["F"], r=3.6)
    E.pos_ball(pg, *ob2.p(Bm["x1"], Bm["y1"], Bm["z1"] + 10), pos["B"], r=3.6)
    check_box(pg, 16, 52, 184, [f"передняя {pos['F']} — с 4 отверстиями Ø4,5 (к фасаду), задняя {pos['B']} — без них",
                                "стенки стоят на дне, отверстиями в торцах к боковине"])
    return pg


def _conf_page(D, n, total, side, sn, title):
    pg = Page(D, n, total, title)
    p, pos, hp = D["p"], D["pos"], D["hpos"]
    S = p[side]
    ch = [h for h in E.joint_holes(D, "", "conf_face") if h["part"] == S["id"]]
    step(pg, 12, 279, sn, f"{len(ch)} конфирмата через боковину {pos[side]} — снаружи")
    shown = [p[k] for k in ("SL", "F", "B", "BOT")] + ([p["SR"]] if side == "SR" else [])
    sgn = -1 if side == "SL" else 1
    ob = figure(pg, D, (16, 150, 196, 262), [(q, E.HL if q is S else E.DONE, {}) for q in shown], sgn=sgn)
    ob.fasteners(ch)
    E._check_view(D, ob, f"A4 шаг {sn}")
    count_badge(pg, 16, 140, len(ch), hp["CONF-7x50"], "конфирмат 7 × 50 · шестигранник 4")
    h0 = ch[0]
    x, y = ob.p(h0["x"], h0["y"], h0["z"])
    zinfo = zoom(pg, D, h0, 150, 112, R=30, win=34, label="сечение по конфирмату (из модели)")
    pg.line(x, y, 150 - 30 * 0.7, 112 + 30 * 0.7, dict(lw=0.6, color="k", ls="--"))
    D["zooms"].append((f"A4 шаг {sn}", h0, zinfo))
    check_box(pg, 16, 125, 100, ["головки заподлицо, без перекоса", "стенки прижаты к дну и боковине"])
    if side == "SR":
        skw = p["SR"]["x0"] - p["SL"]["x1"]
        check_box(pg, 16, 74, 184, [f"внутренняя ширина спереди и сзади {skw:g} +0 / −1,5 (Blum)",
                                    "диагонали короба сверху — разность ≤ 1 [М]"])
    return pg


def page_box2(D, n, total):
    return _conf_page(D, n, total, "SL", 3, "Ящик · шаг 3")


def page_box3(D, n, total):
    pg = Page(D, n, total, "Ящик · шаг 4")
    p, pos = D["p"], D["pos"]
    g = {x["part"]: x for x in D["grooves"]}
    step(pg, 12, 279, 4, f"Боковина {pos['SR']} — пазом на край дна")
    SRm = E.moved(p["SR"], dx=180)
    base = [p["SL"], p["BOT"], p["F"], p["B"]]
    ob = figure(pg, D, (16, 150, 196, 262), [(q, E.DONE, {}) for q in base] + [(SRm, E.HL, {"groove": g[p["SR"]["id"]]})],
                sgn=-1)
    ob.arrow((SRm["x0"] + 60, (SRm["y0"] + SRm["y1"]) / 2, SRm["z1"] + 30),
             (p["SR"]["x0"] + 40, (SRm["y0"] + SRm["y1"]) / 2, SRm["z1"] + 30))
    E.pos_ball(pg, *ob.p(SRm["x1"], SRm["y0"], SRm["z1"] + 15), pos["SR"], r=3.6)
    sticker(pg, *ob.p(SRm["x1"], SRm["y1"], SRm["z1"] + 40), pos["SR"], "П")
    check_box(pg, 16, 140, 184, ["паз боковины — на край дна, задвинуть до стенок",
                                 f"наклейка {pos['SR']} П — правая боковина; с {pos['SL']} Л не путать"])
    pair_box(pg, 16, 66, 100, 50, groove_ok, groove_bad, "паз внизу — дно в пазу", "паз вверху — неверно")
    return pg


def page_box4(D, n, total):
    return _conf_page(D, n, total, "SR", 5, "Ящик · шаг 5")


def page_box5(D, n, total):
    pg = Page(D, n, total, "Ящик · шаг 6")
    p, pos, hp = D["p"], D["pos"], D["hpos"]
    sc = E.joint_holes(D, "BOT-", "screw_face")
    step(pg, 12, 279, 6, f"Перевернуть ящик дном вверх · {len(sc)} самореза через дно {pos['BOT']}")
    flip_icon(pg, 150, 268)
    bottom_view(pg, D, (30, 172, 180, 252), holes=sc)
    count_badge(pg, 16, 160, len(sc), hp["SCREW-4x25D"], "саморез 4 × 25 · отвёртка PH2 · в красные точки")
    zinfo = zoom(pg, D, sc[0], 60, 118, R=30, win=30, label="сечение по саморезу дна (из модели)", vertical=True,
                 flip=True, face=(0.62, -0.28, "дно"))
    D["zooms"].append(("A4 шаг 6", sc[0], zinfo))
    pair_box(pg, 110, 96, 90, 46, head_ok, head_bad, "головка заподлицо", "выступает — заденет")
    check_box(pg, 16, 78, 184, [f"все {len(sc)} самореза в готовых отверстиях Ø4,5 с зенковкой (4 на ящик — сокращено [М])",
                                "засверловка в стенках Ø3 гл. 8 — наше значение по умолчанию [М], проба [О]"])
    return pg


def page_box6(D, n, total):
    pg = Page(D, n, total, "Ящик · шаги 7–8")
    p, pos, H, nd = D["p"], D["pos"], D["H"], D["nd"]
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    bt, SL, SR = p["BOT"], p["SL"], p["SR"]
    step(pg, 12, 279, 7, "Замки Л и П — на наружную пласть дна у передних углов")
    zones = [(SL["x1"], bt["y0"], SL["x1"] + 75, bt["y0"] + 90), (SR["x0"] - 75, bt["y0"], SR["x0"], bt["y0"] + 90)]
    P_ = bottom_view(pg, D, (22, 196, 138, 258), zones=zones, title="ящик дном вверх (как после шага 6), перед — к себе")
    for (zx0, zy0, zx1, zy1), t in zip(zones, ("замок Л", "замок П")):
        u, v = P_((zx0 + zx1) / 2, (zy0 + zy1) / 2)
        pg.text(u, v, t.split()[1], size=9, weight="bold", color=BLUE, ha="center", va="center", zorder=12)
    flip_icon(pg, 150, 268)
    lq = H["LOCK-SCREW"]["qty"] // max(1, nd)
    pg.text(144, 250, "зона 75 от боковины", size=7.5, color=BLUE)
    pg.text(144, 245, "(Blum 76XHSK_H_1) [Д]", size=7.5, color=BLUE)
    pg.text(144, 236, f"саморезы замка: {lq} на ящик", size=7.5)
    pg.text(144, 231, "тип — по поставке Blum [О]", size=7.5)
    check_box(pg, 16, 180, 184, ["отверстия — только по шаблону T65.1000.02; синие зоны — не координаты",
                                 "сверлит сборщик после сборки короба (наше решение [М])"])
    step(pg, 12, 150, 8, "Задний крючок Ø6 — только по шаблону T65.1000.02")
    pg.ax.add_patch(Rectangle((16, 118), 184, 22, fc="#fff3e0", ec="k", lw=1.2))
    pg.text(20, 133, "Шаблон задаёт сторону и положение отверстия — без шаблона не сверлить.", size=8.5, weight="bold")
    pg.text(20, 127, "Данные Blum [Д]: Ø6, глубина 10, 7 от заднего торца, 11 по высоте (SVG 76XHSK_H_2).", size=7.5)
    pg.text(20, 122, "На первом ящике сверить шаблон с этими данными и записать [О]; размер 125 не использовать.", size=7.5)
    ob2 = figure(pg, D, (30, 40, 180, 112), [(q, E.DONE, {}) for q in all5], sgn=-1, ys=-1)
    for S in (SL, SR):
        x, y = ob2.p((S["x0"] + S["x1"]) / 2, S["y1"], S["z0"] + 11)
        pg.ax.add_patch(Circle((x, y), 5, fc="none", ec=RED, lw=1.4, ls="--", zorder=12))
    pg.text(105, 32, "вид сзади: зоны крючков (не координаты)", size=7.5, ha="center", style="italic")
    return pg


def _cabinet(D, ext=0.0):
    """Колонна корпуса у первого ящика: стенки (обрезаны по высоте) и профили MOVENTO (условно); ext — выдвижение профиля."""
    r, s = D["r"], D["s"]
    P = {q["id"]: q for q in s["parts"]}
    cl, cr = P[r["colL"]], P[r["colR"]]
    rb = r["rb"]
    z0, z1 = r["floor"], D["p"]["SL"]["z1"] + 60
    walls = [{**cl, "z0": z0, "z1": z1}, {**cr, "z0": z0, "z1": z1}]
    yc0 = cl["y0"]
    prof = []
    for wall, sg, nm in ((cl["x1"], 1, "PRL"), (cr["x0"], -1, "PRR")):
        xa, xb = sorted((wall, wall + sg * (21 + 16)))
        prof.append({"id": nm, "x0": xa, "x1": xb, "y0": yc0 - ext, "y1": yc0 + r["NL"] - ext, "z0": rb, "z1": rb + 12})
        prof.append({"id": nm + "W", "x0": min(wall, wall + sg * 3), "x1": max(wall, wall + sg * 3),
                     "y0": yc0, "y1": yc0 + r["NL"], "z0": rb, "z1": rb + 45})
    return walls, prof


def lock_zoom(pg, cx, cy, R=26):
    """Круг у замка: схема (не контур Blum) — боковина ящика на профиле, замок под дном защёлкивается."""
    ax = pg.ax
    ax.add_patch(Circle((cx, cy), R, fc="white", ec="none", zorder=14))
    ax.add_patch(Rectangle((cx - 20, cy - 2), 40, 7, fc="#cfe0f5", ec=BLUE, lw=0.9, zorder=15))         # профиль
    ax.add_patch(Rectangle((cx - 8, cy + 5), 9, 20, fc=WOOD2, ec="k", lw=0.8, hatch="////", zorder=15))  # боковина
    ax.add_patch(Rectangle((cx + 1, cy + 9), 19, 4, fc=WOOD2, ec="k", lw=0.8, hatch="\\\\\\\\", zorder=15))  # дно
    ax.add_patch(Rectangle((cx + 2, cy + 5), 12, 4, fc="#7fa7d6", ec=BLUE, lw=0.9, zorder=16))         # замок
    ax.add_patch(FancyArrowPatch((cx + 8, cy + 3), (cx + 8, cy - 1), arrowstyle="-|>", mutation_scale=9, color=RED,
                                 lw=1.2, zorder=17))
    ax.add_patch(Circle((cx, cy), R, fc="none", ec="k", lw=1.4, zorder=22))
    pg.text(cx, cy - 12, "щёлк", size=9, ha="center", weight="bold", color=RED, zorder=23)
    pg.text(cx, cy - R - 3.5, "замок защёлкивается на профиле (схема)", size=7, ha="center", va="top")


def page_box7(D, n, total):
    pg = Page(D, n, total, "Ящик · шаг 9")
    p, r = D["p"], D["r"]
    step(pg, 12, 279, 9, "Ящик — на выдвинутые профили, опустить до щелчка замков")
    ext = 220
    walls, prof = _cabinet(D, ext)
    box = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    up = [E.moved(q, dy=-ext, dz=70) for q in box]
    items = [(w, "#ececec", {}) for w in walls] + [(q, "#cfe0f5", {}) for q in prof] + [(q, E.HL, {}) for q in up]
    ob = figure(pg, D, (16, 120, 196, 262), items, sgn=1)
    for S in (up[0], up[1]):
        for yy in (S["y0"] + 60, S["y1"] - 40):
            xm = (S["x0"] + S["x1"]) / 2
            ob.arrow((xm, yy, S["z0"] - 4), (xm, yy, S["z0"] - 52))
    pr = prof[0]
    x, y = ob.p(pr["x1"], pr["y0"], pr["z1"])
    E.callout(pg, x, y, x - 6, y - 18, "профиль выдвинут (условно, не контур Blum)", 7.5, BLUE)
    pg.text(16, 112, "1) выдвинуть оба профиля до упора   2) поставить ящик задней частью на профили (крючки — сзади)",
            size=7.5)
    pg.text(16, 106, "3) опустить переднюю часть ящика — замки Л и П щёлкают   4) задвинуть ящик", size=7.5)
    lock_zoom(pg, 160, 74)
    check_box(pg, 16, 96, 104, ["оба замка щёлкнули;", "ящик не снимается без нажатия", "рычагов замков;",
                                "ход до конца без касаний"])
    pg.text(16, 30, "Направляющие и TIP-ON BLUMOTION уже в корпусе: набор «Корпус» (6 саморезов 609.1500", size=7.5)
    pg.text(16, 25, "на профиль, синхронизация по отрезу) — " + STEP_PREFIX.get("rails", "инструкция корпуса, шаги направляющих")
            + ".", size=7.5)
    return pg


def page_box8(D, n, total):
    pg = Page(D, n, total, "Ящик · шаг 10")
    p, pos, hp, nd = D["p"], D["pos"], D["hpos"], D["nd"]
    fr, Fw = p["FR"], p["F"]
    fs = E.joint_holes(D, "FRONT", "front_screw")
    step(pg, 12, 279, 10, f"Фасад {pos['FR']} на выдвинутом ящике: {len(fs)} самореза изнутри")
    ext = 300
    walls, prof = _cabinet(D, ext)
    walls = [{**w, "y1": w["y0"] + 160} for w in walls]
    shown = [E.moved(p[k], dy=-ext) for k in ("SL", "SR", "F", "BOT")]
    frm = E.moved(fr, dy=-ext)
    items = [(w, "#ececec", {}) for w in walls] + [(q, "#cfe0f5", {}) for q in prof if not q["id"].endswith("W")] + \
            [(q, E.DONE, {}) for q in shown] + [(frm, E.HL, {})]
    ob = figure(pg, D, (16, 150, 128, 262), items, sgn=1, ys=-1)
    fsm = [{**h, "y": h["y"] - ext} for h in fs]
    ob.fasteners(fsm)
    E._check_view(D, ob, "A4 шаг 10")
    pg.text(72, 144, "ящик выдвинут на профилях; вид изнутри ящика (задняя стенка не показана)", size=6.8, ha="center",
            style="italic")
    zinfo = zoom(pg, D, fs[0], 162, 215, R=30, win=40, label="сечение: стенка + фасад (из модели)",
                 keys=("SL", "SR", "F", "BOT", "FR"), face=(0.98, 0.72, "лицо"))
    D["zooms"].append(("A4 шаг 10", fs[0], zinfo))
    count_badge(pg, 16, 133, len(fs), hp["SCREW-4x25"], "саморез 4 × 25 · PH2 · изнутри")
    pair_box(pg, 16, 74, 100, 50, front_ok, front_bad, "изнутри — лицо чистое", "через лицо фасада")
    gap = Fw["y0"] - fr["y1"]
    eng = fdims("SCREW-4x25")[1] - (Fw["y1"] - Fw["y0"]) - gap
    check_box(pg, 122, 126, 78, ["выставить по зазорам: 3 между", "фасадами, 1,5 по краям,", "2,5 до корпуса (Blum)",
                                 f"вход в фасад {eng:g}, до лица {fr['y1'] - fr['y0'] - eng:g} [М]"])
    fr0 = p["FR"]
    pg.text(122, 86, "Удержать фасад: 2 полоски двустороннего", size=6.8)
    pg.text(122, 82, "скотча на переднюю стенку короба [М][О].", size=6.8)
    pg.text(122, 77, "Первый (нижний) фасад: база — корпус:", size=6.8, weight="bold")
    pg.text(122, 73, f"низ на {kit13_n(fr0['z0'] - D['s']['derived']['plinth'])} выше низа боковины, край —", size=6.8)
    pg.text(122, 69, "1,5 от наружной грани боковины [М].", size=6.8)
    pg.text(122, 64, "Регулировка MOVENTO [Д: TD-132]: боковая", size=6.8)
    pg.text(122, 60, "±1,5; высота +3; наклон; глубина −1/+2.", size=6.8)
    pg.ax.add_patch(Rectangle((16, 22), 184, 34, fc="#fff3e0", ec="k", lw=1.2))
    pg.text(22, 47, "ПЕРВЫЙ ящик проверить целиком:", size=9, weight="bold")
    pg.text(22, 40, "нажатие открывает · мягко закрывается · фасад не задевает соседние", size=8)
    P_ = STEP_PREFIX["p"]
    pg.text(22, 32, f"Всё в порядке → повторить шаги {P_}1–{P_}10 ещё {nd - 1} раз(а).", size=9, weight="bold")
    pg.text(22, 26, "Нет — остановиться и сообщить Arvello.", size=8)
    return pg


PAGES = [page_set, page_box1, page_box2, page_box3, page_box4, page_box5, page_box6, page_box7, page_box8]


def verify_guide(D, pages):
    """Проверки выпуска инструкции: крепёж виден; тексты не накладываются; круг показывает деталь входа своего отверстия."""
    res = []
    res.append(("Крепёж на рисунках: вход виден и не закрыт", not D["view_errors"], D["view_errors"][:2]))
    ov = [(i + 1, b) for i, pg in enumerate(pages) for b in pg.check_overlaps()]
    res.append(("Тексты A4 не накладываются и в рамке", not ov, ov[:2]))
    bad = [w for w, h, z in D["zooms"] if h["part"] not in z["parts"] or len(z["parts"]) < 2]
    res.append(("Круг-увеличение: в сечении деталь входа и сопрягаемая", not bad, bad))
    return res


def write(path, opts):
    D = E.drawer_data(opts)
    D["view_errors"], D["zooms"] = [], []
    pages = []
    with PdfPages(path) as pdf:
        for i, mk in enumerate(PAGES, 1):
            pg = mk(D, i, len(PAGES))
            pg.fig.canvas.draw()
            pages.append(pg)
            pdf.savefig(pg.fig)
            pg.fig.savefig(str(path).replace(".pdf", f"-{i:02d}.png"), dpi=130)
    res = verify_guide(D, pages)
    for pg in pages:
        plt.close(pg.fig)
    return D, res


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "eng002_guide.pdf"
    o = {"width": "1200", "handle": "push", "changer": "yes", "body": "K110", "front": "K4069"}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        o[k] = v
    D, res = write(out, o)
    for name, ok, t in res:
        print(f"{'ok ' if ok else 'FAIL'} {name} — {t if not ok else 'да'}")
    sys.exit(0 if all(r[1] for r in res) else 1)
