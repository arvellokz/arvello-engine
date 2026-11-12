"""ENG-002 — пример новых листов для одного ящика комода ARV-NST-101 (MOVENTO + TIP-ON BLUMOTION).

Два выхода из одной модели:
  лист Ц — для цеха: сборочный чертёж ящика по образцу БАЗИС («сборочный чертёж на ящики», руководство
           «Создание документов с модели», 16.04.2026, разд. 2.4.2): виды в проекционной связи, сечение паза,
           позиции, спецификация ящика, таблица операций по деталям (кто и где выполняет);
  листы С1–С4 — для сборщиков Arvello: шаги с крупными рисунками (последовательность — по образцу инструкции IKEA).
Метки достоверности: [Д] — по документу (модель генератора / Blum, docs/blum), [С] — проверить на станке цеха,
[О] — проверить на образце. Листы — пример, НЕ утверждены.

Запуск: python3 tools/eng/eng002_drawer.py out.pdf [width=1200 changer=yes]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon  # noqa: E402

from eng import kit13  # noqa: E402
from eng.sheetlib import CTR, HID, RED, THIN, VIS, Sheet, View  # noqa: E402

GREY, HL, DONE = "#9a9a9a", "#f3c48b", "#e4e4e4"
K = math.cos(math.radians(40)) * 0.55, math.sin(math.radians(40)) * 0.55    # косоугольная проекция: глубина × 0,55


# ------------------------------------------------------------------ данные одного ящика из модели
def drawer_data(opts):
    s = kit13.make("ARV-NST-101", opts)
    pos, _, hpos = kit13.positions(s)
    r = s["derived"]["drawers"][0]
    P = {p["id"]: p for p in s["parts"]}
    ids = dict(zip(("SL", "SR", "F", "B", "BOT"), r["box"]))
    ids["FR"] = r["front"]
    parts = {k: P[v] for k, v in ids.items()}
    holes = [h for h in s["holes"] if h["part"] in ids.values()]
    H = {h["id"]: h for h in s["hardware"]}
    nd = len(s["derived"]["drawers"])
    grooves = [g for g in s["derived"].get("grooves", []) if g["part"] in (ids["SL"], ids["SR"])]
    return dict(s=s, r=r, p=parts, ids=ids, pos={k: pos[v] for k, v in ids.items()}, holes=holes, H=H, hpos=hpos,
                nd=nd, grooves=grooves)


def joint_holes(D, key, kind):
    return [h for h in D["holes"] if key in h["joint"] and h["kind"] == kind]


# ------------------------------------------------------------------ косоугольная проекция (крупные рисунки сборщику)
class Oblique:
    """u = x + sgn·kx·y, v = zs·z + ky·y. sgn = +1 — видна правая грань, −1 — левая; zs = −1 — вид снизу (перевёрнуто)."""

    def __init__(self, sh, box, boxes, sgn=1, zs=1):
        self.sh, self.sgn, self.zs = sh, sgn, zs
        us, vs = [], []
        for b in boxes:
            for x in (b["x0"], b["x1"]):
                for y in (b["y0"], b["y1"]):
                    for z in (b["z0"], b["z1"]):
                        u, v = self._uv(x, y, z)
                        us.append(u); vs.append(v)
        x0, y0, x1, y1 = box
        self.sc = min((x1 - x0) / (max(us) - min(us)), (y1 - y0) / (max(vs) - min(vs)))
        self.o = (x0 + ((x1 - x0) - (max(us) - min(us)) * self.sc) / 2 - min(us) * self.sc,
                  y0 + ((y1 - y0) - (max(vs) - min(vs)) * self.sc) / 2 - min(vs) * self.sc)

    def _uv(self, x, y, z):
        return x + self.sgn * K[0] * y, self.zs * z + K[1] * y

    def p(self, x, y, z):
        u, v = self._uv(x, y, z)
        return self.o[0] + u * self.sc, self.o[1] + v * self.sc

    def box(self, b, fill, lw=0.9, ls="-", alpha=1.0, groove=None):
        x0, x1, y0, y1, z0, z1 = b["x0"], b["x1"], b["y0"], b["y1"], b["z0"], b["z1"]
        xs = x1 if self.sgn > 0 else x0
        zt = z1 if self.zs > 0 else z0
        faces = [[(xs, y0, z0), (xs, y1, z0), (xs, y1, z1), (xs, y0, z1)],          # боковая грань
                 [(x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt)],          # верх (или низ при виде снизу)
                 [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]]          # передняя грань
        shade = (0.86, 0.95, 1.0)
        for f, k in zip(faces, shade):
            pts = [self.p(*q) for q in f]
            c = matplotlib.colors.to_rgb(fill)
            self.sh.ax.add_patch(Polygon(pts, closed=True, fc=tuple(min(1, ch * k) for ch in c), ec="k", lw=lw, ls=ls,
                                         alpha=alpha, zorder=2))
        if groove:                                                                      # паз на видимой грани
            g = groove
            pts = [self.p(xs, g["y0"], g["z0"]), self.p(xs, g["y1"], g["z0"]), self.p(xs, g["y1"], g["z1"]),
                   self.p(xs, g["y0"], g["z1"])]
            self.sh.ax.add_patch(Polygon(pts, closed=True, fc="#5a5a5a", ec="k", lw=0.5, zorder=3))

    def draw(self, items):
        """items: [(box, fill, kw)] — рисуются от дальних к ближним."""
        key = lambda it: (-(it[0]["y0"] + it[0]["y1"]) / 2, self.zs * (it[0]["z0"] + it[0]["z1"]) / 2,
                          self.sgn * (it[0]["x0"] + it[0]["x1"]) / 2)
        for b, fill, kw in sorted(items, key=key):
            self.box(b, fill, **kw)

    def arrow(self, a, b, color=RED, lw=1.6):
        self.sh.ax.add_patch(FancyArrowPatch(self.p(*a), self.p(*b), arrowstyle="-|>", mutation_scale=14, color=color,
                                             lw=lw, zorder=12))

    def dots(self, pts, color=RED, r=1.3):
        for q in pts:
            x, y = self.p(*q)
            self.sh.ax.add_patch(matplotlib.patches.Circle((x, y), r, fc=color, ec="k", lw=0.5, zorder=12))


def moved(b, dx=0, dy=0, dz=0):
    return {**b, "x0": b["x0"] + dx, "x1": b["x1"] + dx, "y0": b["y0"] + dy, "y1": b["y1"] + dy,
            "z0": b["z0"] + dz, "z1": b["z1"] + dz}


def callout(sh, x, y, tx, ty, text, size=9.0, color="k"):
    sh.ax.plot([x, tx], [y, ty], lw=0.7, color=color, zorder=13)
    sh.text(tx + 1, ty, text, size=size, ha="left", va="center", color=color, zorder=14,
            bbox=dict(fc="white", ec=color, lw=0.5, pad=1.2))


def pos_ball(sh, x, y, n, r=4.2):
    sh.ax.add_patch(matplotlib.patches.Circle((x, y), r, fc="white", ec="k", lw=1.0, zorder=14))
    sh.text(x, y, str(n), size=9.5, ha="center", va="center", weight="bold", zorder=15)


def step_head(sh, x, y, n, title):
    sh.ax.add_patch(Polygon([(x, y - 9), (x + 14, y - 9), (x + 14, y + 3), (x, y + 3)], fc="k", ec="k", zorder=5))
    sh.text(x + 7, y - 3, str(n), size=15, ha="center", va="center", color="white", weight="bold", zorder=6)
    sh.text(x + 18, y - 3, title, size=11, va="center", weight="bold")


def notes(sh, x, y, lines, size=8.6, step=4.6):
    for i, t in enumerate(lines):
        sh.text(x, y - i * step, t, size=size, va="top")
    return y - len(lines) * step


STAMP = None


def stamp(D, sub):
    s = D["s"]
    return {"product": f"Комод ARV-NST-101 · ящик (пример ENG-002)", "doc": f"ARV-NST-101.ENG002",
            "rev": "R01E-пример", "hash": s["hash"], "config": f"ARV-NST-101 · {kit13.cfg_ru(s, short=True)} · {sub}"[:86],
            "status": "ПРИМЕР ENG-002 — НЕ УТВЕРЖДЕНО, НЕ ДЛЯ ИЗГОТОВЛЕНИЯ. [Д] по документу · [С] проверить на станке · "
                      "[О] проверить на образце"}


# ================================================================== лист Ц: сборочный чертёж ящика для цеха
def sheet_shop(D, n, total):
    p, r, pos = D["p"], D["r"], D["pos"]
    sh = Sheet("Ящик: сборочный чертёж, спецификация, операции", stamp(D, "для цеха"), n, total, "1:5")
    box = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    X0, X1 = min(b["x0"] for b in box), max(b["x1"] for b in box)
    Y0, Y1 = min(b["y0"] for b in box), max(b["y1"] for b in box)
    Z0, Z1 = min(b["z0"] for b in box), max(b["z1"] for b in box)
    sc = 5
    # вид спереди (x, z) — без фасада
    vf = View(sh, sc, (32, 205), (X0, Z0))
    for k in ("SL", "SR", "F"):
        b = p[k]
        vf.rect(b["x0"], b["z0"], b["x1"], b["z1"], VIS)
    b = p["BOT"]
    vf.rect(b["x0"], b["z0"], b["x1"], b["z1"], HID)
    sh.view_title(32, 248, "Вид спереди (без фасада), М 1:5")
    a, c = vf.p(X0, Z0), vf.p(X1, Z1)
    sh.dim_h(a[0], c[0], a[1], a[1], a[1] - 7, f"{X1 - X0:g}")
    sh.dim_v(a[1], c[1], c[0], c[0], c[0] + 7, f"{Z1 - Z0:g}")
    ia, ib = vf.p(p["SL"]["x1"], Z1), vf.p(p["SR"]["x0"], Z1)
    sh.dim_h(ia[0], ib[0], ia[1], ib[1], ia[1] + 6, f"{p['SR']['x0'] - p['SL']['x1']:g} (SKW = LW − 42) [Д]")
    # сечение А-А по передней стенке: дно в пазах, стенка на дне
    vs = View(sh, 1, (215, 205), (p["SL"]["x0"] - 2, Z0 - 2))
    for k in ("SL",):
        b = p[k]
        vs.rect(b["x0"], b["z0"], b["x1"], b["z0"] + 50, VIS)
        x_, y_ = vs.p(b["x0"], b["z0"]); x2, y2 = vs.p(b["x1"], b["z0"] + 50)
        sh.hatch(x_, y_, x2, y2)
    bt, fw, g = p["BOT"], p["F"], D["grooves"][0]
    xa, ya = vs.p(p["SL"]["x1"] - g["depth"], bt["z0"]); xb, yb = vs.p(p["SL"]["x1"] + 30, bt["z1"])
    sh.rect(xa, ya, xb, yb, dict(lw=0.6, color="w", ls="-"), fill="white")
    sh.rect(xa, ya, xb, yb, VIS); sh.hatch(xa, ya, xb, yb, "\\\\\\\\")
    xc, yc = vs.p(fw["x0"], fw["z0"]); xd, yd = vs.p(fw["x0"] + 30, fw["z0"] + 20)
    sh.rect(xc, yc, xd, yd, VIS)
    sh.view_title(205, 280, "Сечение А-А (М 1:1): дно в пазу боковины, стенка на дне")
    e0, e1 = vs.p(p["SL"]["x0"], bt["z0"]), vs.p(p["SL"]["x0"], bt["z1"])
    sh.dim_v(vs.p(0, p["SL"]["z0"])[1], e0[1], e0[0], e0[0], e0[0] - 6, f"{bt['z0'] - p['SL']['z0']:g}")
    sh.dim_v(e0[1], e1[1], e0[0], e0[0], e0[0] - 13, f"{bt['z1'] - bt['z0']:g}")
    gx0, gx1 = vs.p(p["SL"]["x1"] - g["depth"], bt["z1"]), vs.p(p["SL"]["x1"], bt["z1"])
    sh.dim_h(gx0[0], gx1[0], gx0[1], gx1[1], gx0[1] + 34, f"паз {g['depth']:g}")
    sh.leader(xb - 6, (ya + yb) / 2, xb + 18, ya - 6, f"поз. {pos['BOT']} дно", size=7)
    sh.leader(xc + 10, yd - 4, xd + 22, yd + 6, f"поз. {pos['F']} стенка", size=7)
    sh.leader(x_ + 3, y_ + 30, x_ - 6, y_ + 38, f"поз. {pos['SL']}", size=7)
    sh.text(205, 199, f"Паз {g['w']:g} × {g['depth']:g} по всей длине боковины, {g['from_edge']:g} от нижней кромки [Д: раскрой "
            "Blum 12.11 — дно SKW + 10].", size=6.8)
    sh.text(205, 194.5, "Посадка дна в паз: номинал дна 536 = 526 + 2 × 5 — без зазора; ширина паза под фактическую "
            "толщину плиты — [С][О] (вопрос Ц-4).", size=6.8, color=RED)
    # вид сверху (x, y)
    vt = View(sh, sc, (32, 78), (X0, Y0))
    for k in ("SL", "SR", "F", "B"):
        b = p[k]
        vt.rect(b["x0"], b["y0"], b["x1"], b["y1"], VIS)
    b = p["BOT"]
    vt.rect(b["x0"], b["y0"], b["x1"], b["y1"], HID)
    for h in joint_holes(D, "", "conf_face"):
        u, v = vt.p(h["x"], h["y"])
        sh.cross(u, v, 2.0)
    sh.view_title(32, 78 + (Y1 - Y0) / sc + 14, "Вид сверху, М 1:5 (перед — внизу)")
    a, c = vt.p(X0, Y0), vt.p(X1, Y1)
    sh.dim_v(a[1], c[1], a[0], a[0], a[0] - 7, f"{Y1 - Y0:g} (SKL = NL − 10) [Д]")
    # позиции
    for k, (u, v) in {"SL": (p["SL"]["x0"], (Y0 + Y1) / 2), "SR": (p["SR"]["x1"], (Y0 + Y1) / 2),
                      "F": ((X0 + X1) / 2, p["F"]["y0"]), "B": ((X0 + X1) / 2, p["B"]["y1"]),
                      "BOT": ((X0 + X1) / 2 + 60, (Y0 + Y1) / 2)}.items():
        x, y = vt.p(u, v)
        tx = x - 14 if k == "SL" else x + 14 if k == "SR" else x + 22
        ty = y - 9 if k == "F" else y + 9 if k == "B" else y
        sh.balloon(x, y, tx, ty, pos[k])
    # спецификация ящика
    H, hp, nd = D["H"], D["hpos"], D["nd"]
    rows = []
    for k, nm in (("SL", "Боковина ящика левая"), ("SR", "Боковина ящика правая"), ("BOT", "Дно ящика"),
                  ("F", "Стенка ящика передняя"), ("B", "Стенка ящика задняя"), ("FR", "Фасад ящика")):
        b = p[k]
        dims = sorted((b["x1"] - b["x0"], b["y1"] - b["y0"], b["z1"] - b["z0"]), reverse=True)
        rows.append([str(pos[k]), nm, " × ".join(kit13.n_(round(v, 1)) for v in dims), "1", str(nd), "[Д]"])
    cnt = lambda key, kind: len(joint_holes(D, key, kind))
    art = lambda hid: H[hid]["spec"].split(" (")[0].replace("Blum ", "").split(",")[0]
    for hid, q, nm in (("CONF-7x50", cnt("BOX", "conf_face"), "Конфирмат 7 × 50"),
                       ("SCREW-4x25D", cnt("BOT-", "screw_face"), "Саморез 4 × 25 (дно → стенки)"),
                       ("SCREW-4x25", cnt("FRONT", "front_screw"), "Саморез 4 × 25 (фасад → короб)")):
        rows.append([str(hp[hid]), nm, "", str(q), str(q * nd), "[Д]"])
    for hid, nm, st in (("SLIDES", "Направляющая MOVENTO, пара Л/П", "[Д]"), ("SLIDE-LOCK", "Замок MOVENTO, пара Л+П", "[Д]"),
                        ("TIPON-SYNC", "TIP-ON BLUMOTION, набор + синхр.", "[Д][О]")):
        rows.append([str(hp[hid]), nm, art(hid), "1", str(nd), st])
    sh.text(205, 186, f"Спецификация одного ящика (ящиков в изделии: {nd})", size=8, weight="bold")
    yb = sh.table(205, 182, ["Поз.", "Наименование", "Размер / артикул", "На 1", f"На {nd}", ""], rows, [10, 72, 46, 11, 11, 21],
                  row_h=4.6, size=6.0)
    # таблица операций по деталям — кто и где
    ops = [[str(pos["SL"]) + ", " + str(pos["SR"]), "раскрой; кромка 0,4 — верх; Ø7 насквозь ×4; паз 16 × 5", "цех", "[Д] [С]"],
           [str(pos["BOT"]), "раскрой без кромки; Ø4,5 насквозь, зенковка ×6", "цех", "[Д] [С]"],
           [str(pos["F"]) + ", " + str(pos["B"]), "раскрой; кромка 0,4 — верх; Ø5 гл. 36 ×4; Ø3 снизу ×3", "цех", "[Д] [С]"],
           [str(pos["F"]), "дополнительно Ø4,5 насквозь ×4 (крепление фасада)", "цех", "[Д]"],
           [str(pos["FR"]), "раскрой; кромка ABS 2 по контуру; без присадки", "цех", "[Д]"],
           ["ящик", "крючок Ø6 гл. 10 и замки — шаблон Blum T65.1000.02", "сборщик", "[Д] [О]"],
           ["ящик", "фасад — 4 самореза 4 × 25 изнутри, по месту", "сборщик", "[О]"]]
    sh.text(205, yb - 4, "Таблица операций (по образцу БАЗИС «таблица операций», разд. 3.2.2)", size=8, weight="bold")
    sh.table(205, yb - 8, ["Поз.", "Операция", "Кто", "Достоверность"], ops, [16, 110, 18, 27], row_h=4.6, size=6.2)
    sh.text(32, 60, "Цех изготавливает детали; ящик собирает сборщик Arvello (листы С1–С4). Координаты отверстий — "
            "листы деталей комплекта.", size=7.0)
    return sh


# ================================================================== листы С: инструкция сборщику
def parts_sheet(D, n, total):
    p, pos, H, hp, nd = D["p"], D["pos"], D["H"], D["hpos"], D["nd"]
    sh = Sheet("Сборка ящика — набор деталей", stamp(D, "сборщику"), n, total, "без масштаба")
    sh.text(28, 280, f"ЯЩИК — собрать 1, проверить, затем повторить ещё {nd - 1} раз(а)", size=15, weight="bold")
    sh.text(28, 271, "Перед сборкой разложите детали одного ящика и сверьте номера на наклейках с позициями ниже.", size=9)
    cells = [("SL", "Боковина левая", "паз (тёмная полоса) — внизу, внутрь"), ("SR", "Боковина правая", "паз (тёмная полоса) — внизу, внутрь"),
             ("BOT", "Дно", "без кромки"), ("F", "Стенка передняя", "4 отв. Ø4,5 — к фасаду"),
             ("B", "Стенка задняя", "без отверстий Ø4,5"), ("FR", "Фасад", "лицо — наружу")]
    for i, (k, nm, hint) in enumerate(cells):
        cx, cy = 30 + (i % 3) * 128, 160 + (1 - i // 3) * 58
        b = p[k]
        ob = Oblique(sh, (cx + 4, cy + 4, cx + 70, cy + 46), [b], sgn=1 if k != "SR" else -1)
        g = next((x for x in D["grooves"] if x["part"] == b["id"]), None)
        ob.draw([(b, HL, {"groove": g} if g else {})])
        pos_ball(sh, cx + 8, cy + 46, pos[k])
        sh.text(cx + 76, cy + 36, nm, size=10, weight="bold")
        sh.text(cx + 76, cy + 29, "1 шт.", size=10)
        dims = sorted((b["x1"] - b["x0"], b["y1"] - b["y0"], b["z1"] - b["z0"]), reverse=True)
        sh.text(cx + 76, cy + 22, " × ".join(kit13.n_(round(v, 1)) for v in dims), size=8.5)
        sh.text(cx + 76, cy + 15, hint, size=8, color="#444")
    sh.text(28, 150, "Крепёж на один ящик", size=12, weight="bold")
    cnt = lambda key, kind: len(joint_holes(D, key, kind))
    fx = [("CONF-7x50", cnt("BOX", "conf_face"), "конфирмат 7 × 50", "шестигранник 4"),
          ("SCREW-4x25D", cnt("BOT-", "screw_face"), "саморез 4 × 25 (дно → стенки)", "отвёртка PH2"),
          ("SCREW-4x25", cnt("FRONT", "front_screw"), "саморез 4 × 25 (фасад)", "отвёртка PH2")]
    for i, (hid, q, nm, tool) in enumerate(fx):
        x = 30 + i * 128
        pos_ball(sh, x + 5, 136, hp[hid])
        sh.text(x + 14, 136, f"{q} ×", size=14, weight="bold", va="center")
        sh.text(x + 34, 138, nm, size=9, va="center")
        sh.text(x + 34, 132, "инструмент: " + tool, size=8, va="center", color="#444")
    sh.text(28, 118, "Фурнитура Blum на один ящик", size=12, weight="bold")
    for i, (hid, t) in enumerate((("SLIDES", "направляющие MOVENTO, пара Л/П"), ("SLIDE-LOCK", "замки, пара Л/П"),
                                  ("TIPON-SYNC", "TIP-ON BLUMOTION: блок, защёлка, адаптер, синхронизация"))):
        pos_ball(sh, 35, 107 - i * 9, hp[hid])
        sh.text(44, 107 - i * 9, f"1 компл. — {t}: " + H[hid]["spec"].split(" (")[0].split(",")[0], size=8.5, va="center")
    sh.text(28, 74, "Инструмент", size=12, weight="bold")
    notes(sh, 30, 68, ["шестигранник 4 (конфирматы) · отвёртка PH2 · шаблон Blum T65.1000.02 со сверлом Ø6 (крючок, замки) ·",
                       "рулетка, угольник · мягкая подложка на стол (не царапать фасад)."], size=9)
    return sh


def _build_steps(D):
    p = D["p"]
    g = {x["part"]: x for x in D["grooves"]}
    return p, g


def sheet_steps_1(D, n, total):
    p, g = _build_steps(D)
    pos = D["pos"]
    sh = Sheet("Сборка ящика — шаги 1–2", stamp(D, "сборщику"), n, total, "без масштаба")
    # шаг 1: дно в паз левой боковины
    step_head(sh, 28, 282, 1, f"Дно поз. {pos['BOT']} — в паз левой боковины поз. {pos['SL']}")
    ob = Oblique(sh, (40, 150, 215, 265), [p["SL"], moved(p["BOT"], dx=260)], sgn=1)
    ob.draw([(p["SL"], HL, {"groove": g[p["SL"]["id"]]}), (moved(p["BOT"], dx=260), HL, {})])
    b = p["BOT"]
    ob.arrow((b["x1"] + 250, (b["y0"] + b["y1"]) / 2, b["z1"] + 40), (b["x1"] + 120, (b["y0"] + b["y1"]) / 2, b["z1"] + 40))
    x, y = ob.p(p["SL"]["x1"], p["SL"]["y1"] - 40, (g[p["SL"]["id"]]["z0"] + g[p["SL"]["id"]]["z1"]) / 2)
    callout(sh, x, y, x + 30, y + 42, "паз 16 × 5 — внизу, к дну", size=9)
    pos_ball(sh, *ob.p(p["SL"]["x0"], p["SL"]["y0"], p["SL"]["z1"] + 15), pos["SL"])
    pos_ball(sh, *ob.p(b["x1"] + 260, b["y0"], b["z1"] + 25), pos["BOT"])
    notes(sh, 222, 262, ["Левую боковину положите пазом к себе,", "паз — у нижней кромки.",
                         "Задвиньте дно в паз на всю длину.", "Края дна и боковины — заподлицо",
                         "спереди и сзади.", "", "Контроль: дно входит без молотка;",
                         "если туго — остановитесь, сообщите", "(посадка паза — вопрос Ц-4) [О]."])
    # шаг 2: стенки на дно + конфирматы через левую боковину
    step_head(sh, 28, 138, 2, f"Стенки поз. {pos['F']} и {pos['B']} — на дно, к левой боковине; 4 конфирмата")
    base = [p["SL"], p["BOT"]]
    Fm, Bm = moved(p["F"], dz=90), moved(p["B"], dz=90)
    ob2 = Oblique(sh, (40, 14, 185, 122), base + [Fm, Bm], sgn=1)
    ob2.draw([(p["SL"], DONE, {}), (p["BOT"], DONE, {}), (Fm, HL, {}), (Bm, HL, {})])
    for w, wm in ((p["F"], Fm), (p["B"], Bm)):
        xc, yc = (w["x0"] + w["x1"]) / 2, (w["y0"] + w["y1"]) / 2
        ob2.arrow((xc, yc, wm["z0"] - 5), (xc, yc, w["z0"] + 25))
    pos_ball(sh, *ob2.p(Fm["x1"], Fm["y0"], Fm["z1"] + 10), pos["F"])
    pos_ball(sh, *ob2.p(Bm["x1"], Bm["y1"], Bm["z1"] + 10), pos["B"])
    # вставка: вид слева — конфирматы снаружи левой боковины
    ob3 = Oblique(sh, (195, 60, 300, 118), [p["SL"], p["F"], p["B"], p["BOT"]], sgn=-1)
    ob3.draw([(p["BOT"], DONE, {}), (p["F"], DONE, {}), (p["B"], DONE, {}), (p["SL"], HL, {})])
    ch = [(h["x"], h["y"], h["z"]) for h in joint_holes(D, p["SL"]["id"][-6:] + "-", "conf_face") if h["part"] == p["SL"]["id"]]
    ob3.dots(ch)
    x, y = ob3.p(*ch[0])
    callout(sh, x, y, x - 28, y + 30, f"4 × конфирмат 7 × 50", size=9, color=RED)
    sh.text(247, 57, "вид слева: снаружи левой боковины", size=8, ha="center", style="italic")
    notes(sh, 305, 120, ["Стенки ставятся на дно, отверстиями", "в торцах к боковине.",
                         "Передняя стенка — с 4 отв. Ø4,5", "(для фасада), задняя — без них.",
                         "Конфирматы — СНАРУЖИ левой", "боковины, шестигранник 4.",
                         "Затягивать без перекоса;", "стенки прижаты к дну."], size=8.6)
    return sh


def sheet_steps_2(D, n, total):
    p, g = _build_steps(D)
    pos = D["pos"]
    sh = Sheet("Сборка ящика — шаги 3–4", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 3, f"Правая боковина поз. {pos['SR']}: паз — на дно; 4 конфирмата")
    SRm = moved(p["SR"], dx=180)
    base = [p["SL"], p["BOT"], p["F"], p["B"]]
    ob = Oblique(sh, (40, 150, 230, 265), base + [SRm], sgn=-1)
    ob.draw([(q, DONE, {}) for q in base] + [(SRm, HL, {"groove": g[p["SR"]["id"]]})])
    x, y = ob.p(SRm["x0"], (SRm["y0"] + SRm["y1"]) / 2, (g[p["SR"]["id"]]["z0"] + g[p["SR"]["id"]]["z1"]) / 2)
    callout(sh, x, y, x + 8, y - 22, "паз — на край дна", size=9)
    ob.arrow((SRm["x0"] + 60, (SRm["y0"] + SRm["y1"]) / 2, SRm["z1"] + 30),
             (p["SR"]["x0"] + 40, (SRm["y0"] + SRm["y1"]) / 2, SRm["z1"] + 30))
    pos_ball(sh, *ob.p(SRm["x1"], SRm["y0"], SRm["z1"] + 15), pos["SR"])
    notes(sh, 240, 262, ["Паз правой боковины — на край дна,", "задвинуть до стенок.",
                         "Конфирматы 4 шт. — снаружи правой", "боковины, шестигранник 4.",
                         "", "Контроль после шага (К-я1):", "внутренняя ширина спереди и сзади",
                         f"{p['SR']['x0'] - p['SL']['x1']:g} +0 / −1,5 [Д: Blum LW − 42];",
                         "диагонали короба сверху — разность ≤ 1."], size=8.8)
    # шаг 4: перевернуть — саморезы снизу
    step_head(sh, 28, 138, 4, f"Перевернуть ящик: 6 саморезов 4 × 25 через дно поз. {pos['BOT']} в стенки")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    ob2 = Oblique(sh, (40, 14, 230, 122), all5, sgn=1, zs=-1)
    ob2.draw([(q, DONE if q is not p["BOT"] else HL, {}) for q in all5])
    sc = [(h["x"], h["y"], h["z"]) for h in joint_holes(D, "BOT-", "screw_face")]
    ob2.dots(sc)
    x, y = ob2.p(*sc[0])
    callout(sh, x, y, x + 12, y + 18, "6 × саморез 4 × 25, отвёртка PH2", size=9, color=RED)
    notes(sh, 240, 120, ["Ящик кверху дном на мягкой подложке.", "Саморезы — в готовые отверстия Ø4,5",
                         "с зенковкой; головка заподлицо", "с дном (не выступает — иначе", "заденет направляющую).",
                         "", "Глубина засверловки в стенках —", "вопрос Ц-5 (8 или 12) [С]."], size=8.8)
    return sh


def sheet_steps_3(D, n, total):
    p, g = _build_steps(D)
    pos, r, H = D["pos"], D["r"], D["H"]
    sh = Sheet("Сборка ящика — шаги 5–7", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 5, "Крючок и замки — по шаблону Blum T65.1000.02")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    bt = p["BOT"]
    locks = [{"x0": p["SL"]["x1"] + 5, "x1": p["SL"]["x1"] + 45, "y0": bt["y0"] + 10, "y1": bt["y0"] + 85,
              "z0": bt["z0"] - 12, "z1": bt["z0"]},
             {"x0": p["SR"]["x0"] - 45, "x1": p["SR"]["x0"] - 5, "y0": bt["y0"] + 10, "y1": bt["y0"] + 85,
              "z0": bt["z0"] - 12, "z1": bt["z0"]}]
    ob = Oblique(sh, (40, 165, 200, 265), all5 + locks, sgn=1, zs=-1)
    ob.draw([(q, DONE, {}) for q in all5] + [(q, "#7fa7d6", {}) for q in locks])
    for q, t in zip(locks, ("замок Л", "замок П")):
        x, y = ob.p(q["x1"], q["y0"], q["z0"])
        callout(sh, x, y, x + 6, y - 12 if t.endswith("Л") else y - 22, t + " — по шаблону (условно)", 8.5, "#1f5fa8")
    notes(sh, 210, 262, ["Замки MOVENTO (пара Л / П) — под дно у передних углов, по шаблону [Д: Blum].",
                         "Задний крючок: отверстие Ø6 гл. 10 в заднем торце каждой боковины, 7 от заднего",
                         "торца и 11 по высоте — сверлить ТОЛЬКО по шаблону T65.1000.02 [Д: docs/blum; О].",
                         "Размер «125» на рисунке Blum не трактовать без шаблона (открыто в docs/blum).",
                         "Цех эти отверстия не сверлит."], size=8.6)
    step_head(sh, 28, 158, 6, "Ящик — на направляющие (после крепления направляющих в корпусе)")
    notes(sh, 46, 145, ["Направляющие MOVENTO и блоки TIP-ON BLUMOTION уже стоят в корпусе (лист «Корпус и направляющие»,",
                        "саморезы 609.1500 Ø3,5 × 15, 6 на профиль — 19 / 37 / 69 / 243 / 261 / 293 от передней кромки) [Д].",
                        "Выдвинуть профили, поставить ящик задними крючками на профили, опустить спереди до щелчка замков.",
                        "Контроль: ящик ходит без касаний; синхронизация TIP-ON установлена (отрез " +
                        H["TIPON-SYNC"]["spec"].split("отрез ")[-1].split(" (")[0] + ")."], size=8.8)
    step_head(sh, 28, 112, 7, f"Фасад поз. {pos['FR']}: 4 самореза 4 × 25 изнутри через переднюю стенку")
    fr = p["FR"]
    items = [(q, DONE, {}) for q in all5] + [(moved(fr, dy=-70), HL, {})]
    ob3 = Oblique(sh, (40, 14, 200, 100), all5 + [moved(fr, dy=-70)], sgn=1)
    ob3.draw(items)
    fs = [(h["x"], h["y"], h["z"]) for h in joint_holes(D, "FRONT", "front_screw")]
    ob3.dots(fs)
    x, y = ob3.p(*fs[0])
    callout(sh, x, y, x + 20, y + 42, "4 × саморез 4 × 25 изнутри, PH2 (за фасадом)", 9, RED)
    notes(sh, 210, 100, ["Фасад приложить по зазорам: 3 между фасадами, 1,5 по краям,",
                         "до корпуса 2,5 (TIP-ON BLUMOTION, Blum) [Д].",
                         "Прижать, закрутить саморезы изнутри короба (вход в фасад 9) [Д].",
                         "Контроль ПЕРВОГО ящика до остальных 5 [О]: нажатие открывает,",
                         "ящик мягко закрывается, фасад не задевает соседние.",
                         "Всё в порядке — собрать остальные ящики так же."], size=8.6)
    return sh


def write(path, opts):
    D = drawer_data(opts)
    makers = [sheet_shop, parts_sheet, sheet_steps_1, sheet_steps_2, sheet_steps_3]
    total = len(makers)
    figs = []
    with PdfPages(path) as pdf:
        for i, mk in enumerate(makers, 1):
            sh = mk(D, i, total)
            pdf.savefig(sh.fig)
            sh.fig.savefig(str(path).replace(".pdf", f"-{i:02d}.png"), dpi=110)
            figs.append(sh)
            kit13.plt.close(sh.fig)
    return D, figs


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "eng002_drawer.pdf"
    o = {"width": "1200", "handle": "push", "changer": "yes", "color": "O"}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        o[k] = v
    write(out, o)
    print("ok", out)
