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
from eng.boardkit import EDGE_TXT  # noqa: E402
from eng.cab import TECH as TECH_  # noqa: E402
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
    """u = x' + sgn·kx·y', v = zs·z + ky·y'. sgn = +1 — видна правая грань, −1 — левая; zs = −1 — вид снизу;
    ys = −1 — вид сзади (изделие повёрнуто на 180°: x' = −x, y' = −y). Видимые грани в повёрнутых координатах:
    боковая (+x' при sgn > 0), верх / низ, передняя (−y')."""

    def __init__(self, sh, box, boxes, sgn=1, zs=1, ys=1):
        self.sh, self.sgn, self.zs, self.ys = sh, sgn, zs, ys
        self.drawn, self.errors = [], []
        boxes = [self._t(b) for b in boxes]
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

    def _t(self, b):
        """Коробка в повёрнутые координаты вида."""
        if self.ys > 0:
            return b
        return {**b, "x0": -b["x1"], "x1": -b["x0"], "y0": -b["y1"], "y1": -b["y0"]}

    def _uv(self, x, y, z):
        return x + self.sgn * K[0] * y, self.zs * z + K[1] * y

    def p(self, x, y, z):
        """Точка в координатах изделия → лист."""
        u, v = self._uv(self.ys * x, self.ys * y, z)
        return self.o[0] + u * self.sc, self.o[1] + v * self.sc

    def _pv(self, x, y, z):
        u, v = self._uv(x, y, z)
        return self.o[0] + u * self.sc, self.o[1] + v * self.sc

    def box(self, b, fill, lw=0.9, ls="-", alpha=1.0, groove=None):
        self.drawn.append(b)
        b = self._t(b)
        groove = self._t(groove) if groove else None
        x0, x1, y0, y1, z0, z1 = b["x0"], b["x1"], b["y0"], b["y1"], b["z0"], b["z1"]
        xs = x1 if self.sgn > 0 else x0
        zt = z1 if self.zs > 0 else z0
        faces = [[(xs, y0, z0), (xs, y1, z0), (xs, y1, z1), (xs, y0, z1)],          # боковая грань
                 [(x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt)],          # верх (или низ при виде снизу)
                 [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]]          # передняя грань
        shade = (0.86, 0.95, 1.0)
        for f, k in zip(faces, shade):
            pts = [self._pv(*q) for q in f]
            c = matplotlib.colors.to_rgb(fill)
            self.sh.ax.add_patch(Polygon(pts, closed=True, fc=tuple(min(1, ch * k) for ch in c), ec="k", lw=lw, ls=ls,
                                         alpha=alpha, zorder=2))
        if groove:                                                                      # паз на видимой грани
            g = groove
            pts = [self._pv(xs, g["y0"], g["z0"]), self._pv(xs, g["y1"], g["z0"]), self._pv(xs, g["y1"], g["z1"]),
                   self._pv(xs, g["y0"], g["z1"])]
            self.sh.ax.add_patch(Polygon(pts, closed=True, fc="#5a5a5a", ec="k", lw=0.5, zorder=3))

    def draw(self, items):
        """items: [(box, fill, kw)] — рисуются от дальних к ближним."""
        def key(it):
            b = self._t(it[0])
            zf = b["z1"] if self.zs > 0 else -b["z0"]     # по видимой грани: утопленное дно — за торцами боковин
            return (-(b["y0"] + b["y1"]) / 2, zf, self.sgn * (b["x0"] + b["x1"]) / 2)
        for b, fill, kw in sorted(items, key=key):
            self.box(b, fill, **kw)

    def arrow(self, a, b, color=RED, lw=1.6):
        self.sh.ax.add_patch(FancyArrowPatch(self.p(*a), self.p(*b), arrowstyle="-|>", mutation_scale=14, color=color,
                                             lw=lw, zorder=12))

    def dots(self, pts, color=RED, r=1.3, shape="o"):
        for q in pts:
            x, y = self.p(*q)
            if shape == "s":
                self.sh.ax.add_patch(matplotlib.patches.Rectangle((x - r, y - r), 2 * r, 2 * r, fc=color, ec="k", lw=0.5,
                                                                  zorder=12))
            elif shape == "^":
                self.sh.ax.add_patch(Polygon([(x - r * 1.2, y - r), (x + r * 1.2, y - r), (x, y + r * 1.3)], fc=color,
                                             ec="k", lw=0.5, zorder=12))
            else:
                self.sh.ax.add_patch(matplotlib.patches.Circle((x, y), r, fc=color, ec="k", lw=0.5, zorder=12))

    def visible_entry(self, h):
        """Вход отверстия (сторона, с которой вкручивают крепёж) виден на этом рисунке и ничем не закрыт.
        Возвращает текст ошибки или None."""
        AX = {"x": 0, "y": 1, "z": 2}
        a, sg = h["dir"][1], (1 if h["dir"][0] == "+" else -1)
        n = [0, 0, 0]
        n[AX[a]] = -sg                                   # наружу из детали — против направления сверления
        nv = (self.ys * n[0], self.ys * n[1], n[2])      # в координатах вида
        seen = {(self.sgn, 0, 0), (0, 0, self.zs), (0, -1, 0)}
        if nv not in seen:
            return f"{h['part']}: вход крепежа с невидимой стороны ({h['dir']})"
        pt = [h["x"], h["y"], h["z"]]
        i = AX[a]
        for b in self.drawn:
            if b["id"] == h["part"]:
                continue
            lo, hi = [b["x0"], b["y0"], b["z0"]], [b["x1"], b["y1"], b["z1"]]
            others = [k for k in range(3) if k != i]
            if all(lo[k] + 0.01 < pt[k] < hi[k] - 0.01 for k in others) and \
                    ((n[i] > 0 and hi[i] > pt[i] + 0.01) or (n[i] < 0 and lo[i] < pt[i] - 0.01)):
                return f"{h['part']}: вход крепежа закрыт деталью {b['id']}"
        return None

    def fasteners(self, holes, color=RED, r=1.3, shape="o"):
        """Точки крепежа только с проверкой: вход виден и не закрыт. Ошибки копятся в self.errors."""
        for h in holes:
            e = self.visible_entry(h)
            if e:
                self.errors.append(e)
        self.dots([(h["x"], h["y"], h["z"]) for h in holes], color, r, shape)


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
            "status": "ПРИМЕР ENG-002 — НЕ УТВЕРЖДЕНО, НЕ ДЛЯ ИЗГОТОВЛЕНИЯ. [М] заложено в модели · [Д] документ "
                      + ("производителя" if D["r"].get("sys") == "samet" else "Blum") + " · "
                      "[С] проверить на станке · [О] проверить на образце"}


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
    sh.dim_h(ia[0], ib[0], ia[1], ib[1], ia[1] + 6, f"{p['SR']['x0'] - p['SL']['x1']:g} (SKW = LW − 42 +0/−1,5 — Blum TD-132) [Д]")
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
    cl = r.get("bottom_clear") or 0
    bw = bt["x1"] - bt["x0"]
    sh.text(205, 199, f"Паз {kit13.n_(g['w'])} × {g['depth']:g} по всей длине, {g['from_edge']:g} от нижней кромки; дно "
            f"{kit13.n_(bw)} = SKW + 10 (раскрой Blum [Д]) − 2 × зазор {kit13.n_(cl)} [М].", size=6.8)
    sh.text(205, 194.5, "Паз и зазор — наши значения по умолчанию (допуск плиты ±0,3 разных поставщиков); проверить "
            "на пробе [О].", size=6.8, color=RED)
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
    sh.dim_v(a[1], c[1], a[0], a[0], a[0] - 7, f"{Y1 - Y0:g} (SKL = NL − 10, Blum) [Д]")
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
        rows.append([str(pos[k]), nm, " × ".join(kit13.n_(round(v, 1)) for v in dims), "1", str(nd), "[М]"])
    cnt = lambda key, kind: len(joint_holes(D, key, kind))
    art = lambda hid: H[hid]["spec"].split(" (")[0].replace("Blum ", "").split(",")[0]
    for hid, q, nm in (("CONF-7x50", cnt("BOX", "conf_face"), "Конфирмат 7 × 50"),
                       ("SCREW-4x25D", cnt("BOT-", "screw_face"), "Саморез 4 × 25 (дно → стенки)"),
                       ("SCREW-4x25", cnt("FRONT", "front_screw"), "Саморез 4 × 25 (фасад → короб)")):
        rows.append([str(hp[hid]), nm, "", str(q), str(q * nd), "[М]"])
    for hid, nm, st in (("SLIDES", "Направляющая MOVENTO, пара Л/П", "[Д][О]"), ("SLIDE-LOCK", "Замок MOVENTO, пара Л+П", "[Д][О]"),
                        ("TIPON-SYNC", "TIP-ON BLUMOTION, набор + синхр.", "[Д][О]")):
        rows.append([str(hp[hid]), nm, art(hid), "1", str(nd), st])
    lq = H["LOCK-SCREW"]["qty"] // max(1, nd)
    rows.append([str(hp["LOCK-SCREW"]), "Саморез крепления замка", "по поставке Blum", str(lq), str(lq * nd), "[Д][О]"])
    sh.text(205, 186, f"Спецификация одного ящика (ящиков в изделии: {nd})", size=8, weight="bold")
    yb = sh.table(205, 182, ["Поз.", "Наименование", "Размер / артикул", "На 1", f"На {nd}", ""], rows, [10, 72, 46, 11, 11, 21],
                  row_h=4.6, size=6.0)
    # таблица операций по деталям — кто и где
    ext = D["s"]["derived"]["parts_ext"]
    etx = lambda k: EDGE_TXT[next(iter(ext[p[k]["id"]]["edges"].values()))]     # кромка детали — из модели (профиль)
    ops = [[str(pos["SL"]) + ", " + str(pos["SR"]), f"раскрой; кромка {etx('SL')} — верх; Ø7 насквозь ×4; паз " + kit13.n_(16 + TECH_["groove_w_add"]) + " × 5", "цех", "[М] [С]"],
           [str(pos["BOT"]), "раскрой без кромки; Ø4,5 насквозь, зенковка ×6", "цех", "[М] [С]"],
           [str(pos["F"]) + ", " + str(pos["B"]), f"раскрой; кромка {etx('F')} — верх; Ø5 гл. 36 ×4; Ø3 снизу ×3", "цех", "[М] [С]"],
           [str(pos["F"]), "дополнительно Ø4,5 насквозь ×4 (крепление фасада)", "цех", "[М]"],
           [str(pos["FR"]), f"раскрой; кромка {etx('FR')} по контуру; без присадки", "цех", "[М]"],
           ["ящик", "крючок Ø6 гл. 10 и замки — шаблон Blum T65.1000.02", "сборщик", "[Д] [М] [О]"],
           ["ящик", "фасад — 4 самореза 4 × 25 изнутри, по месту", "сборщик", "[М] [О]"]]
    sh.text(205, yb - 4, "Таблица операций (по образцу БАЗИС «таблица операций», разд. 3.2.2)", size=8, weight="bold")
    sh.table(205, yb - 8, ["Поз.", "Операция", "Кто", "Достоверность"], ops, [16, 110, 18, 27], row_h=4.6, size=6.2)
    sh.text(32, 64, "Цех изготавливает детали; изделие собирает сборщик Arvello (листы С1–С5). Крючок и замки по умолчанию "
            "сверлит сборщик по шаблону Blum [М].", size=7.0)
    sh.text(32, 59, "Координаты отверстий — листы деталей комплекта. [М] — заложено в нашей модели, не независимое "
            "подтверждение.", size=7.0)
    return sh


# ================================================================== листы С: инструкция сборщику
def parts_sheet(D, n, total):
    p, pos, H, hp, nd = D["p"], D["pos"], D["H"], D["hpos"], D["nd"]
    sh = Sheet("Сборка ящика — набор деталей", stamp(D, "сборщику"), n, total, "без масштаба")
    sh.text(28, 280, f"ЯЩИК — собрать 1, проверить с фасадом, затем повторить ещё {nd - 1} раз(а)", size=15, weight="bold")
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
    cnt = lambda key, kind: len(joint_holes(D, key, kind))
    sh.text(28, 152, "А. В набор ящика (собирается на столе)", size=12, weight="bold")
    fx = [("CONF-7x50", cnt("BOX", "conf_face"), "конфирмат 7 × 50", "шестигранник 4", "[М]"),
          ("SCREW-4x25D", cnt("BOT-", "screw_face"), "саморез 4 × 25 (дно → стенки)", "отвёртка PH2", "[М]"),
          ("SCREW-4x25", cnt("FRONT", "front_screw"), "саморез 4 × 25 (фасад, изнутри)", "отвёртка PH2", "[М]")]
    for i, (hid, q, nm, tool, st) in enumerate(fx):
        x = 30 + i * 128
        pos_ball(sh, x + 5, 140, hp[hid])
        sh.text(x + 14, 140, f"{q} ×", size=14, weight="bold", va="center")
        sh.text(x + 34, 142, nm + " " + st, size=9, va="center")
        sh.text(x + 34, 136, "инструмент: " + tool, size=8, va="center", color="#444")
    lq = H["LOCK-SCREW"]["qty"] // max(1, nd)
    rows = [[str(hp["SLIDE-LOCK"]), "Замок MOVENTO, пара Л + П", H["SLIDE-LOCK"]["spec"].split(" (")[0].replace("Blum ", ""), "1 пара",
             "[Д] артикул; [О] комплект поставки"],
            [str(hp["LOCK-SCREW"]), "Саморез крепления замка", "тип — по поставке Blum", f"{lq} шт.",
             "[Д] кол-во по рисунку Blum; [О] тип"]]
    sh.table(30, 128, ["Поз.", "Фурнитура ящика", "Артикул", "Кол.", "Достоверность"], rows, [12, 70, 70, 20, 75],
             row_h=5.2, size=7.5)
    sh.text(28, 103, "Б. Для установки в корпус (шаг 7, не в наборе ящика)", size=12, weight="bold")
    sync = H["TIPON-SYNC"]["spec"]
    rows = [[str(hp["SLIDES"]), "Направляющая MOVENTO, пара Л / П", H["SLIDES"]["spec"].split(",")[0].replace("Blum ", ""),
             "1 пара", "[Д]; [О] поставка"],
            [str(hp["SLIDE-SCREW-M"]), "Саморез профиля Ø3,5 × 15 (Blum 609.1500)", "6 на профиль",
             f"{H['SLIDE-SCREW-M']['qty'] // max(1, nd)} шт.", "[Д] каталог 2024 с. 428"],
            [str(hp["TIPON-SYNC"]), "TIP-ON BLUMOTION: блок + защёлка + адаптер, Л + П", sync.split(" (")[0].replace("Blum ", ""),
             "1 набор", "[Д] конфигуратор; [О] состав"],
            [str(hp["TIPON-SYNC"]), "Синхронизация TIP-ON BLUMOTION (отрезать)", "T60.1125W, отрез " +
             sync.split("отрез ")[-1].split(" (")[0], "1 шт.", "[Д] каталог стр. 436"]]
    sh.table(30, 98, ["Поз.", "Фурнитура в корпус", "Артикул / размер", "Кол.", "Достоверность"], rows, [12, 82, 58, 20, 75],
             row_h=5.2, size=7.5)
    sh.text(28, 63, "Инструмент", size=12, weight="bold")
    notes(sh, 30, 58, ["шестигранник 4 (конфирматы) · отвёртка PH2 · шаблон Blum T65.1000.02 (крючок, замки) ·",
                       "рулетка, угольник · мягкая подложка на стол (не царапать фасад)."], size=9)
    sh.text(28, 46, "Состав поставки Blum сверить с упаковкой до сборки первого ящика [О].", size=8.5, color=RED)
    return sh


def _build_steps(D):
    p = D["p"]
    g = {x["part"]: x for x in D["grooves"]}
    return p, g


def _check_view(D, ob, where):
    for e in ob.errors:
        D["view_errors"].append(f"{where}: {e}")


def sheet_steps_1(D, n, total):
    p, g = _build_steps(D)
    pos = D["pos"]
    sh = Sheet("Сборка ящика — шаги 1–2", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 1, f"Дно поз. {pos['BOT']} — в паз левой боковины поз. {pos['SL']}")
    ob = Oblique(sh, (40, 150, 215, 265), [p["SL"], moved(p["BOT"], dx=260)], sgn=1)
    ob.draw([(p["SL"], HL, {"groove": g[p["SL"]["id"]]}), (moved(p["BOT"], dx=260), HL, {})])
    b = p["BOT"]
    ob.arrow((b["x1"] + 250, (b["y0"] + b["y1"]) / 2, b["z1"] + 40), (b["x1"] + 120, (b["y0"] + b["y1"]) / 2, b["z1"] + 40))
    x, y = ob.p(p["SL"]["x1"], p["SL"]["y1"] - 40, (g[p["SL"]["id"]]["z0"] + g[p["SL"]["id"]]["z1"]) / 2)
    callout(sh, x, y, x + 30, y + 42, "паз — внизу, к дну", size=9)
    pos_ball(sh, *ob.p(p["SL"]["x0"], p["SL"]["y0"], p["SL"]["z1"] + 15), pos["SL"])
    pos_ball(sh, *ob.p(b["x1"] + 260, b["y0"], b["z1"] + 25), pos["BOT"])
    notes(sh, 222, 262, ["Левую боковину положите пазом к себе,", "паз — у нижней кромки.",
                         "Задвиньте дно в паз на всю длину.", "Края дна и боковины — заподлицо",
                         "спереди и сзади.", "", "Контроль: дно входит от руки, без молотка.",
                         "Если туго или болтается — остановитесь", "и сообщите: зазор паза — наше значение",
                         "по умолчанию, проверяется пробой [М][О]."])
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
    ob3 = Oblique(sh, (195, 60, 300, 118), [p["SL"], p["F"], p["B"], p["BOT"]], sgn=-1)
    ob3.draw([(p["BOT"], DONE, {}), (p["F"], DONE, {}), (p["B"], DONE, {}), (p["SL"], HL, {})])
    ch = [h for h in joint_holes(D, "", "conf_face") if h["part"] == p["SL"]["id"]]
    ob3.fasteners(ch)
    _check_view(D, ob3, "шаг 2")
    x, y = ob3.p(ch[0]["x"], ch[0]["y"], ch[0]["z"])
    callout(sh, x, y, x - 28, y + 30, f"{len(ch)} × конфирмат 7 × 50", size=9, color=RED)
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
    skw = p["SR"]["x0"] - p["SL"]["x1"]
    notes(sh, 240, 262, ["Паз правой боковины — на край дна,", "задвинуть до стенок.",
                         "Конфирматы 4 шт. — снаружи правой", "боковины, шестигранник 4.",
                         "", "Контроль после шага (К-я1):", "внутренняя ширина спереди и сзади:",
                         f"номинал {skw:g} = LW − 42 [Д: Blum];",
                         "допуск +0 / −1,5 — Blum TD-132 / каталог [Д],", "наш допуск стенок −0,5 / +0 — [М][О];",
                         "диагонали сверху — разность ≤ 1 [М][О]."], size=8.8)
    step_head(sh, 28, 138, 4, f"Перевернуть ящик: {len(joint_holes(D, 'BOT-', 'screw_face'))} самореза 4 × 25 через дно поз. {pos['BOT']} в стенки")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    ob2 = Oblique(sh, (40, 14, 230, 122), all5, sgn=1, zs=-1)
    ob2.draw([(q, DONE if q is not p["BOT"] else HL, {}) for q in all5])
    sc = joint_holes(D, "BOT-", "screw_face")
    ob2.fasteners(sc)
    _check_view(D, ob2, "шаг 4")
    x, y = ob2.p(sc[0]["x"], sc[0]["y"], sc[0]["z"])
    callout(sh, x, y, x + 12, y + 18, f"{len(sc)} × саморез 4 × 25, отвёртка PH2", size=9, color=RED)
    notes(sh, 240, 120, ["Ящик кверху дном на мягкой подложке.", "Саморезы — в готовые отверстия Ø4,5",
                         "с зенковкой; головка заподлицо", "с дном (не выступает — иначе", "заденет направляющую).",
                         "", "Засверловка в стенках Ø3 гл. 8 —", "наше значение по умолчанию [М][О]."], size=8.8)
    return sh


BLOCK = "#fbe3df"


def blocked_banner(sh, x, y, w, text):
    sh.ax.add_patch(Polygon([(x, y - 11), (x + w, y - 11), (x + w, y + 3), (x, y + 3)], fc=BLOCK, ec=RED, lw=1.2, zorder=4))
    sh.text(x + 3, y - 4, text, size=9.5, va="center", color=RED, weight="bold", zorder=5)


def sheet_steps_3(D, n, total):
    p, g = _build_steps(D)
    pos = D["pos"]
    sh = Sheet("Сборка ящика — шаги 5–6 (замки, крючок)", stamp(D, "сборщику"), n, total, "без масштаба")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    bt, SL, SR = p["BOT"], p["SL"], p["SR"]
    step_head(sh, 28, 282, 5, "Замки MOVENTO Л и П — под дно у передних углов, по шаблону T65.1000.02")
    zones = [{"id": "LZ", "x0": SL["x1"], "x1": SL["x1"] + 75, "y0": bt["y0"], "y1": bt["y0"] + 90, "z0": bt["z0"] - 1,
              "z1": bt["z0"]},
             {"id": "RZ", "x0": SR["x0"] - 75, "x1": SR["x0"], "y0": bt["y0"], "y1": bt["y0"] + 90, "z0": bt["z0"] - 1,
              "z1": bt["z0"]}]
    ob = Oblique(sh, (40, 160, 225, 268), all5, sgn=1, zs=-1)
    ob.draw([(q, DONE, {}) for q in all5])
    for zn, t in zip(zones, ("замок Л — у левой боковины", "замок П — у правой боковины")):
        pts = [ob.p(zn["x0"], zn["y0"], bt["z0"]), ob.p(zn["x1"], zn["y0"], bt["z0"]), ob.p(zn["x1"], zn["y1"], bt["z0"]),
               ob.p(zn["x0"], zn["y1"], bt["z0"])]
        sh.ax.add_patch(Polygon(pts, closed=True, fc="#cfe0f5", ec="#1f5fa8", lw=1.2, ls="--", zorder=11))
        x, y = ob.p(zn["x1"], zn["y0"], bt["z0"])
        callout(sh, x, y, x + 4, y - (10 if "Л" in t else 22), t, 8.8, "#1f5fa8")
    a0, a1 = ob.p(SL["x1"], bt["y0"], bt["z0"]), ob.p(SL["x1"] + 75, bt["y0"], bt["z0"])
    sh.dim_h(a0[0], a1[0], a0[1], a1[1], a0[1] - 8, "75")
    notes(sh, 232, 264, ["Ящик кверху дном. Замок левый — у левой боковины, правый — у правой,",
                         "у передних углов, в зоне 75 от боковины [Д: Blum рис. 76XHSK_H_1].",
                         "Положение замка и отверстий — ТОЛЬКО по шаблону Blum T65.1000.02;",
                         "синие зоны — где работать, а не координаты отверстий.",
                         f"Саморезы замка — {D['H']['LOCK-SCREW']['qty'] // max(1, D['nd'])} шт. на ящик, тип — по поставке Blum [О].",
                         "", "Отверстия сверлит сборщик по шаблону после сборки короба",
                         "(наше решение по умолчанию [М])."], size=8.6)
    step_head(sh, 28, 140, 6, "Задний крючок: отверстие Ø6 в задней части каждой боковины")
    blocked_banner(sh, 46, 124, 245, "ТОЛЬКО ПО ШАБЛОНУ T65.1000.02: на первом ящике сверить с данными Blum")
    ob2 = Oblique(sh, (40, 14, 200, 108), all5, sgn=-1, zs=1, ys=-1)
    ob2.draw([(q, DONE, {}) for q in all5])
    for S in (SL, SR):
        x, y = ob2.p((S["x0"] + S["x1"]) / 2, S["y1"], S["z0"] + 11)
        sh.ax.add_patch(matplotlib.patches.Circle((x, y), 5.5, fc="none", ec=RED, lw=1.4, ls="--", zorder=12))
    x, y = ob2.p((SL["x0"] + SL["x1"]) / 2, SL["y1"], SL["z0"] + 11)
    callout(sh, x, y, x + 10, y + 26, "зона крючка (не координата)", 8.8, RED)
    sh.text(120, 16, "вид сзади на ящик", size=8, ha="center", style="italic")
    notes(sh, 210, 106, ["Данные Blum (docs/blum, SVG 76XHSK_H_2) [Д]:",
                         "отверстие Ø6, глубина 10, 7 от заднего торца, 11 по высоте.",
                         "Сторону входа и базу «11» задаёт шаблон; на рисунке — только зона;",
                         "размер Var1 = 125 («Omission») не использовать [О].",
                         "Порядок: на первом ящике приложить шаблон T65.1000.02, сверить",
                         "с данными Blum и записать результат [О].",
                         "Сверлит сборщик по шаблону [М]."], size=8.6)
    return sh


def sheet_steps_4(D, n, total):
    p, g = _build_steps(D)
    pos, r, H, s = D["pos"], D["r"], D["H"], D["s"]
    P = {q["id"]: q for q in s["parts"]}
    sh = Sheet("Сборка ящика — шаги 7–8 (направляющие, фасад)", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 7, "Ящик — на направляющие MOVENTO в корпусе; проверить фиксацию")
    cl, cr = P[r["colL"]], P[r["colR"]]
    SL, SR, bt = p["SL"], p["SR"], p["BOT"]
    rb = r["rb"]
    z0w, z1w = rb - 25, SL["z1"] + 90
    vf = View(sh, 0.27 ** -1 if False else 3.6, (40, 168), (cl["x0"] - 5, z0w))
    for S in (cl, cr):
        vf.rect(S["x0"], z0w, S["x1"], z1w, VIS)
        x0_, y0_ = vf.p(S["x0"], z0w); x1_, y1_ = vf.p(S["x1"], z1w)
        sh.hatch(x0_, y0_, x1_, y1_)
    lift = 70
    for S in (SL, SR):
        vf.rect(S["x0"], S["z0"] + lift, S["x1"], S["z1"] + lift, VIS)
    vf.rect(SL["x1"], bt["z0"] + lift, SR["x0"], bt["z1"] + lift, THIN)
    for wall, sgn in ((cl["x1"], 1), (cr["x0"], -1)):
        x_in = wall + sgn * (21 + 16)
        vf.rect(min(wall, x_in), rb, max(wall, x_in), rb + 12, dict(lw=0.9, color="#1f5fa8", ls="-"))
        vf.rect(min(wall, wall + sgn * 3), rb, max(wall, wall + sgn * 3), rb + 45, dict(lw=0.9, color="#1f5fa8", ls="-"))
        xx, yy = vf.p(wall + sgn * 1.5, rb + 38)
        sh.cross(xx, yy, 2.2)
    for S in (SL, SR):
        xm = (S["x0"] + S["x1"]) / 2
        a, b = vf.p(xm, S["z0"] + lift - 4), vf.p(xm, S["z0"] + 6)
        sh.ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=RED, lw=1.4, zorder=12))
    xa, ya = vf.p(cl["x1"] + 30, rb + 12)
    callout(sh, xa, ya, xa + 20, ya - 14, "профиль MOVENTO (схематично, не контур Blum)", 8.5, "#1f5fa8")
    xs_, ys_ = vf.p(cl["x1"] + 1.5, rb + 38)
    callout(sh, xs_, ys_, xs_ + 30, ys_ + 30, "ось саморезов 38 над низом профиля [Д]", 8.5)
    sh.text(40, 160, "разрез по передней части колонны, вид спереди", size=8, style="italic")
    notes(sh, 255, 264, ["Профили уже закреплены в корпусе: 6 саморезов 609.1500",
                         "Ø3,5 × 15 на профиль, 19 / 37 / 69 / 243 / 261 / 293 от передней",
                         "кромки корпуса [Д: Blum 2024 с. 428]. TIP-ON BLUMOTION и",
                         "синхронизация — по инструкции Blum в упаковке [Д][О].",
                         "Выдвинуть профили. Поставить ящик задней частью на профили",
                         "(крючки — в отверстия шага 6), опустить спереди до щелчка замков.",
                         "", "Проверить: ящик не снимается без нажатия замков; ход",
                         "без касаний; TIP-ON открывает от нажатия [О]."], size=8.6)
    # шаг 8: фасад изнутри
    step_head(sh, 28, 140, 8, f"Фасад поз. {pos['FR']}: 4 самореза 4 × 25 ИЗНУТРИ ящика через переднюю стенку")
    fr, Fw = p["FR"], p["F"]
    shown = [p[k] for k in ("SL", "SR", "F", "BOT")] + [fr]
    ob = Oblique(sh, (40, 14, 175, 120), shown, sgn=1, ys=-1)
    ob.draw([(q, DONE, {}) for q in shown[:-1]] + [(fr, HL, {})])
    fs = joint_holes(D, "FRONT", "front_screw")
    ob.fasteners(fs)
    _check_view(D, ob, "шаг 8")
    x, y = ob.p(fs[0]["x"], fs[0]["y"], fs[0]["z"])
    callout(sh, x, y, x - 95, y + 34, f"{len(fs)} × саморез 4 × 25 — изнутри, PH2", 9, RED)
    sh.text(108, 10, "вид изнутри ящика (сзади); задняя стенка не показана", size=8, ha="center", style="italic")
    # сечение: фасад + стенка + саморез
    L = 25
    t_f, t_w = fr["y1"] - fr["y0"], Fw["y1"] - Fw["y0"]
    gap = Fw["y0"] - fr["y1"]
    eng = L - t_w - gap
    sc_, X0, Y0 = 1.6, 186, 70
    sh.rect(X0, Y0, X0 + t_f * sc_, Y0 + 40, VIS); sh.hatch(X0, Y0, X0 + t_f * sc_, Y0 + 40)
    xw = X0 + (t_f + gap) * sc_
    sh.rect(xw, Y0 + 6, xw + t_w * sc_, Y0 + 40, VIS); sh.hatch(xw, Y0 + 6, xw + t_w * sc_, Y0 + 40, "\\\\\\\\")
    yz = Y0 + 26
    xe = xw + t_w * sc_
    sh.ax.plot([xe + 6, xe - (t_w + gap + eng) * sc_], [yz, yz], lw=2.4, color=RED, zorder=8)
    sh.ax.add_patch(Polygon([(xe, yz - 3), (xe + 6, yz - 3), (xe + 6, yz + 3), (xe, yz + 3)], fc=RED, ec=RED, zorder=8))
    sh.dim_h(xe - (t_w + gap + eng) * sc_, xe, yz + 3, yz + 3, Y0 + 45, f"саморез {L}")
    sh.dim_h(X0 + (t_f - eng) * sc_, X0 + t_f * sc_, Y0, Y0, Y0 - 6, f"вход {eng:g}")
    sh.dim_h(X0, X0 + (t_f - eng) * sc_, Y0, Y0, Y0 - 13, f"до лица {t_f - eng:g}")
    sh.text(X0 - 2, Y0 + 36, "лицо", size=8, ha="right")
    sh.text(X0 + t_f * sc_ / 2, Y0 + 14, f"фасад {t_f:g}", size=7.5, rotation=90, ha="center", va="center",
            bbox=dict(fc="white", ec="none", pad=0.4))
    sh.text(xw + t_w * sc_ / 2, Y0 + 14, f"стенка {t_w:g}", size=7.5, rotation=90, ha="center", va="center",
            bbox=dict(fc="white", ec="none", pad=0.4))
    sh.text(X0, Y0 + 52, "Сечение по саморезу, М 1,6:1", size=8.5, weight="bold")
    notes(sh, 265, 118, ["Фасад приложить снаружи по зазорам: 3 между", "фасадами, 1,5 по краям; до корпуса 2,5",
                         "(TIP-ON BLUMOTION, Blum) [Д].",
                         "Саморезы — ИЗНУТРИ ящика через отверстия", f"Ø4,5 передней стенки, вход в фасад {eng:g}, до",
                         f"лица {t_f - eng:g} [М]. Лицевая сторона фасада —", "БЕЗ отверстий и саморезов.",
                         "Фасад к стенке — вплотную, без зазора [М].",
                         "", "ПЕРВЫЙ ящик проверить до остальных 5 [О]:", "нажатие открывает, мягко закрывается,",
                         "фасад не задевает соседние."], size=8.4)
    return sh


# ================================================================== ящик на направляющих по профилю (Samet, ENG-005 п. 2)
def _prof(D):
    from eng.cab import SLIDE_PROFILES
    return SLIDE_PROFILES[D["r"]["slide"]]


def _conf_of(D, k):
    return [h for h in joint_holes(D, "", "conf_face") if h["part"] == D["p"][k]["id"]]


def sheet_shop_s(D, n, total):
    p, r, pos = D["p"], D["r"], D["pos"]
    S_ = _prof(D)
    sh = Sheet("Ящик: сборочный чертёж, спецификация, операции", stamp(D, "для цеха"), n, total, "1:5")
    box = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    X0, X1 = min(b["x0"] for b in box), max(b["x1"] for b in box)
    Y0, Y1 = min(b["y0"] for b in box), max(b["y1"] for b in box)
    Z0, Z1 = min(b["z0"] for b in box), max(b["z1"] for b in box)
    sc = 5
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
    sh.dim_h(ia[0], ib[0], ia[1], ib[1], ia[1] + 6, f"{p['SR']['x0'] - p['SL']['x1']:g} (проём − {S_['diw']} ±0,5 — "
             f"{S_['brand']} {S_['series']}) [Д]")
    # сечение по задней стенке: дно утоплено между стенками; задний Ø6
    bt, bw, SL = p["BOT"], p["B"], p["SL"]
    vs = View(sh, 1, (215, 205), (SL["x0"] - 2, Z0 - 2))
    for b_, pat in ((SL, "////"), (bw, "\\\\")):
        x0_ = b_["x0"] if b_ is SL else SL["x1"]
        x1_ = b_["x1"] if b_ is SL else SL["x1"] + 30
        u0, v0 = vs.p(x0_, b_["z0"]); u1, v1 = vs.p(x1_, b_["z0"] + 50)
        sh.rect(u0, v0, u1, v1, VIS); sh.hatch(u0, v0, u1, v1, pat)
    u0, v0 = vs.p(SL["x1"], bt["z0"]); u1, v1 = vs.p(SL["x1"] + 30, bt["z1"])
    sh.rect(u0, v0, u1, v1, HID)
    rq = S_["rear"]
    rr = [h for h in D["s"]["holes"] if h["kind"] == "slide_rear" and h["part"] == bw["id"]]
    hx = min(rr, key=lambda h: h["x"])
    cu, cv = vs.p(hx["x"], hx["z"])
    sh.ax.add_patch(matplotlib.patches.Circle((cu, cv), rq["d"] / 2, fc="white", ec="k", lw=0.8, zorder=6))
    sh.view_title(205, 280, "Сечение по задней стенке (М 1:1): дно утоплено, задний Ø6")
    e0 = vs.p(SL["x0"], SL["z0"]); e1 = vs.p(SL["x0"], bt["z0"])
    sh.dim_v(e0[1], e1[1], e0[0], e0[0], e0[0] - 6, f"{bt['z0'] - SL['z0']:g}")
    sh.dim_v(e0[1], cv, cu, cu, e0[0] - 13, f"{rq['from_bottom']}")
    sh.dim_h(vs.p(SL["x1"], 0)[0], cu, cv, cv, cv - 9, f"{rq['from_side']}")
    sh.leader(cu + 3, cv + 2, cu + 26, cv + 14, f"Ø{rq['d']} гл. {rq['depth']} — штифт направляющей [Д]", size=7)
    sh.leader(u1 - 4, (v0 + v1) / 2, u1 + 12, v1 + 8, f"поз. {pos['BOT']} дно", size=7)
    sh.text(205, 199, f"Дно между стенками на конфирматах, утопление {bt['z0'] - SL['z0']:g} от нижней кромки [М]; задние Ø6 — "
            f"{rq['from_bottom']} от низа, {rq['from_side']} от боковины [Д: {S_['series']}].", size=6.8)
    sh.text(205, 194.5, "Утопление дна — наше значение (на сечении производителя «12»); проверить пробой [О].", size=6.8,
            color=RED)
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
    sh.dim_v(a[1], c[1], a[0], a[0], a[0] - 7, f"{Y1 - Y0:g} (NS − {S_['dd']}, {S_['brand']}) [Д]")
    for k, (u, v) in {"SL": (p["SL"]["x0"], (Y0 + Y1) / 2), "SR": (p["SR"]["x1"], (Y0 + Y1) / 2),
                      "F": ((X0 + X1) / 2, p["F"]["y0"]), "B": ((X0 + X1) / 2, p["B"]["y1"]),
                      "BOT": ((X0 + X1) / 2 + 60, (Y0 + Y1) / 2)}.items():
        x, y = vt.p(u, v)
        tx = x - 14 if k == "SL" else x + 14 if k == "SR" else x + 22
        ty = y - 9 if k == "F" else y + 9 if k == "B" else y
        sh.balloon(x, y, tx, ty, pos[k])
    H, hp, nd = D["H"], D["hpos"], D["nd"]
    rows = []
    for k, nm in (("SL", "Боковина ящика левая"), ("SR", "Боковина ящика правая"), ("BOT", "Дно ящика"),
                  ("F", "Стенка ящика передняя"), ("B", "Стенка ящика задняя"), ("FR", "Фасад ящика")):
        b = p[k]
        dims = sorted((b["x1"] - b["x0"], b["y1"] - b["y0"], b["z1"] - b["z0"]), reverse=True)
        rows.append([str(pos[k]), nm, " × ".join(kit13.n_(round(v, 1)) for v in dims), "1", str(nd), "[М]"])
    for hid, q, nm in (("CONF-7x50", len(joint_holes(D, "BOX", "conf_face")), "Конфирмат 7 × 50"),
                       ("SCREW-4x25", len(joint_holes(D, "FRONT", "front_screw")), "Саморез 4 × 25 (фасад → короб)")):
        rows.append([str(hp[hid]), nm, "", str(q), str(q * nd), "[М]"])
    code = S_["codes"][r["NL"]]
    rows.append([str(hp["SLIDES"]), f"Направляющая {S_['brand']}, пара Л/П", f"{code}, NS {r['NL']}", "1", str(nd),
                 "[Д][О]" if not S_["code_note"] else "уточнить"])
    rows.append([str(hp["SLIDE-LOCK"]), f"Замок {S_['brand']}, пара Л+П", S_["lock"].split(": ")[-1].split(" (")[0][:28], "1",
                 str(nd), "[Д][О]"])
    sh.text(205, 186, f"Спецификация одного ящика (ящиков в изделии: {nd})", size=8, weight="bold")
    yb = sh.table(205, 182, ["Поз.", "Наименование", "Размер / артикул", "На 1", f"На {nd}", ""], rows, [10, 72, 46, 11, 11, 21],
                  row_h=4.6, size=6.0)
    ext = D["s"]["derived"]["parts_ext"]
    etx = lambda k: EDGE_TXT[next(iter(ext[p[k]["id"]]["edges"].values()))]
    nc = lambda k: len(_conf_of(D, k))
    ops = [[str(pos["SL"]) + ", " + str(pos["SR"]), f"раскрой; кромка {etx('SL')} — верх; Ø7 насквозь ×{nc('SL')}", "цех", "[М]"],
           [str(pos["BOT"]), "раскрой без кромки; Ø5 в торцы под конфирматы", "цех", "[М]"],
           [str(pos["F"]), f"раскрой; кромка {etx('F')} — верх; Ø7 насквозь ×{nc('F')}; Ø4,5 ×4 (фасад)", "цех", "[М]"],
           [str(pos["B"]), f"раскрой; кромка {etx('B')} — верх; Ø7 насквозь ×{nc('B')}; Ø{rq['d']} гл. {rq['depth']} ×2", "цех",
            "[М] [Д]"],
           [str(pos["FR"]), f"раскрой; кромка {etx('FR')} по контуру" + ("; Ø5 ×2 под ручку" if r.get("hz") is not None else
                                                                         "; без присадки"), "цех", "[М]"],
           ["ящик", "замки Lock-Fix — по документу производителя, по месту", "сборщик", "[Д] [О]"],
           ["ящик", "фасад — 4 самореза 4 × 25 изнутри, по месту", "сборщик", "[М] [О]"]]
    sh.text(205, yb - 4, "Таблица операций (по образцу БАЗИС «таблица операций», разд. 3.2.2)", size=8, weight="bold")
    sh.table(205, yb - 8, ["Поз.", "Операция", "Кто", "Достоверность"], ops, [16, 110, 18, 27], row_h=4.6, size=6.2)
    sh.text(32, 64, "Цех изготавливает детали и сверлит все отверстия, включая задние Ø6; изделие собирает сборщик Arvello "
            "(листы С1–С5).", size=7.0)
    sh.text(32, 59, "Координаты отверстий — листы деталей комплекта. [М] — заложено в нашей модели, не независимое "
            "подтверждение.", size=7.0)
    return sh


def parts_sheet_s(D, n, total):
    p, pos, H, hp, nd, r = D["p"], D["pos"], D["H"], D["hpos"], D["nd"], D["r"]
    S_ = _prof(D)
    sh = Sheet("Сборка ящика — набор деталей", stamp(D, "сборщику"), n, total, "без масштаба")
    sh.text(28, 280, f"ЯЩИК — собрать 1, проверить с фасадом, затем повторить ещё {nd - 1} раз(а)", size=15, weight="bold")
    sh.text(28, 271, "Перед сборкой разложите детали одного ящика и сверьте номера на наклейках с позициями ниже.", size=9)
    cells = [("SL", "Боковина левая", "Ø7 — снаружи"), ("SR", "Боковина правая", "Ø7 — снаружи"),
             ("BOT", "Дно", "без кромки"), ("F", "Стенка передняя", "4 отв. Ø4,5 — к фасаду"),
             ("B", "Стенка задняя", "2 отв. Ø6 снизу — назад"), ("FR", "Фасад", "лицо — наружу")]
    for i, (k, nm, hint) in enumerate(cells):
        cx, cy = 30 + (i % 3) * 128, 160 + (1 - i // 3) * 58
        b = p[k]
        ob = Oblique(sh, (cx + 4, cy + 4, cx + 70, cy + 46), [b], sgn=1 if k != "SR" else -1)
        ob.draw([(b, HL, {})])
        pos_ball(sh, cx + 8, cy + 46, pos[k])
        sh.text(cx + 76, cy + 36, nm, size=10, weight="bold")
        sh.text(cx + 76, cy + 29, "1 шт.", size=10)
        dims = sorted((b["x1"] - b["x0"], b["y1"] - b["y0"], b["z1"] - b["z0"]), reverse=True)
        sh.text(cx + 76, cy + 22, " × ".join(kit13.n_(round(v, 1)) for v in dims), size=8.5)
        sh.text(cx + 76, cy + 15, hint, size=8, color="#444")
    sh.text(28, 152, "А. В набор ящика (собирается на столе)", size=12, weight="bold")
    fx = [("CONF-7x50", len(joint_holes(D, "BOX", "conf_face")), "конфирмат 7 × 50", "шестигранник 4"),
          ("SCREW-4x25", len(joint_holes(D, "FRONT", "front_screw")), "саморез 4 × 25 (фасад, изнутри)", "отвёртка PH2")]
    for i, (hid, q, nm, tool) in enumerate(fx):
        x = 30 + i * 128
        pos_ball(sh, x + 5, 140, hp[hid])
        sh.text(x + 14, 140, f"{q} ×", size=14, weight="bold", va="center")
        sh.text(x + 34, 142, nm + " [М]", size=9, va="center")
        sh.text(x + 34, 136, "инструмент: " + tool, size=8, va="center", color="#444")
    rows = [[str(hp["SLIDE-LOCK"]), f"Замок {S_['brand']}, пара Л + П", S_["lock"].split(" (")[0], "1 пара",
             "[Д] артикул; [О] комплект поставки"]]
    sh.table(30, 128, ["Поз.", "Фурнитура ящика", "Артикул", "Кол.", "Достоверность"], rows, [12, 60, 80, 20, 75],
             row_h=5.2, size=7.5)
    sh.text(28, 108, "Б. Для установки в корпус (шаг 7, не в наборе ящика)", size=12, weight="bold")
    ns = H["SLIDE-SCREW-S"]["qty"] // max(1, nd)
    rows = [[str(hp["SLIDES"]), f"Направляющая {S_['name']}, пара Л / П", f"{S_['codes'][r['NL']]}, NS {r['NL']}", "1 пара",
             "[Д]; [О] поставка" if not S_["code_note"] else "уточнить код у продавца"],
            [str(hp["SLIDE-SCREW-S"]), "Шуруп Ø3,5 для ДСП (направляющая к корпусу)", "по разметке", f"{ns} шт.",
             f"[Д] {S_['series']}"]]
    sh.table(30, 103, ["Поз.", "Фурнитура в корпус", "Артикул / размер", "Кол.", "Достоверность"], rows, [12, 102, 38, 20, 75],
             row_h=5.2, size=7.5)
    sh.text(28, 78, "Инструмент", size=12, weight="bold")
    notes(sh, 30, 73, ["шестигранник 4 (конфирматы) · отвёртка PH2 · рулетка, угольник ·",
                       "мягкая подложка на стол (не царапать фасад)."], size=9)
    sh.text(28, 61, f"Состав поставки {S_['brand']} сверить с упаковкой до сборки первого ящика [О].", size=8.5, color=RED)
    return sh


def steps_s1(D, n, total):
    p, pos = D["p"], D["pos"]
    sh = Sheet("Сборка ящика — шаги 1–2", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 1, f"Стенки поз. {pos['F']}, {pos['B']} и дно поз. {pos['BOT']} — к левой боковине поз. {pos['SL']}")
    Fm, Bm, Tm = moved(p["F"], dz=110), moved(p["B"], dz=110), moved(p["BOT"], dz=60)
    ob = Oblique(sh, (40, 150, 215, 265), [p["SL"], Fm, Bm, Tm], sgn=1)
    ob.draw([(p["SL"], DONE, {}), (Fm, HL, {}), (Bm, HL, {}), (Tm, HL, {})])
    for w, wm in ((p["F"], Fm), (p["B"], Bm), (p["BOT"], Tm)):
        xc, yc = (w["x0"] + w["x1"]) / 2, (w["y0"] + w["y1"]) / 2
        ob.arrow((xc, yc, wm["z0"] - 5), (xc, yc, w["z0"] + 25))
    pos_ball(sh, *ob.p(Fm["x1"], Fm["y0"], Fm["z1"] + 10), pos["F"])
    pos_ball(sh, *ob.p(Bm["x1"], Bm["y1"], Bm["z1"] + 10), pos["B"])
    pos_ball(sh, *ob.p(Tm["x1"], (Tm["y0"] + Tm["y1"]) / 2, Tm["z1"] + 10), pos["BOT"])
    rec = p["BOT"]["z0"] - p["SL"]["z0"]
    notes(sh, 222, 262, ["Левую боковину положите отверстиями Ø7 вниз", "(снаружи).",
                         "Стенки ставятся торцами к боковине, низ стенок —", "заподлицо с низом боковины.",
                         f"Дно — между стенками, на {rec:g} выше нижней кромки [М].",
                         "Передняя стенка — с 4 отв. Ø4,5 (к фасаду),", "задняя — с 2 отв. Ø6 снизу (штифты)."])
    ch = _conf_of(D, "SL")
    step_head(sh, 28, 138, 2, f"{len(ch)} конфирматов 7 × 50 через левую боковину — снаружи")
    ob3 = Oblique(sh, (40, 14, 200, 122), [p["SL"], p["F"], p["B"], p["BOT"]], sgn=-1)
    ob3.draw([(p["BOT"], DONE, {}), (p["F"], DONE, {}), (p["B"], DONE, {}), (p["SL"], HL, {})])
    ob3.fasteners(ch)
    _check_view(D, ob3, "шаг 2")
    x, y = ob3.p(ch[0]["x"], ch[0]["y"], ch[0]["z"])
    callout(sh, x, y, x - 28, y + 30, f"{len(ch)} × конфирмат 7 × 50", size=9, color=RED)
    notes(sh, 222, 120, ["Конфирматы — СНАРУЖИ левой боковины,", "шестигранник 4.",
                         "Затягивать без перекоса; стенки и дно", "прижаты к боковине."], size=8.6)
    return sh


def steps_s2(D, n, total):
    p, pos = D["p"], D["pos"]
    S_ = _prof(D)
    sh = Sheet("Сборка ящика — шаги 3–4", stamp(D, "сборщику"), n, total, "без масштаба")
    ch = _conf_of(D, "F") + _conf_of(D, "B")
    step_head(sh, 28, 282, 3, f"{len(ch)} конфирмата через стенки поз. {pos['F']} и {pos['B']} в торец дна")
    base = [p[k] for k in ("SL", "F", "B", "BOT")]
    ob = Oblique(sh, (40, 150, 230, 265), base, sgn=1)
    ob.draw([(q, HL if q in (p["F"], p["B"]) else DONE, {}) for q in base])
    ob.fasteners(_conf_of(D, "F"))
    _check_view(D, ob, "шаг 3")
    h0 = _conf_of(D, "F")[0]
    x, y = ob.p(h0["x"], h0["y"], h0["z"])
    callout(sh, x, y, x + 8, y - 22, f"{len(ch)} × конфирмат 7 × 50 (по 2 на стенку)", size=9, color=RED)
    notes(sh, 240, 262, ["Конфирматы — снаружи передней и задней", "стенок, в торец дна.",
                         "Дно — по всей ширине без щели к стенкам."], size=8.8)
    cs = _conf_of(D, "SR")
    step_head(sh, 28, 138, 4, f"Правая боковина поз. {pos['SR']}: {len(cs)} конфирматов — снаружи")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    ob2 = Oblique(sh, (40, 14, 230, 122), all5, sgn=1)
    ob2.draw([(q, HL if q is p["SR"] else DONE, {}) for q in all5])
    ob2.fasteners(cs)
    _check_view(D, ob2, "шаг 4")
    x, y = ob2.p(cs[0]["x"], cs[0]["y"], cs[0]["z"])
    callout(sh, x, y, x + 12, y + 18, f"{len(cs)} × конфирмат 7 × 50", size=9, color=RED)
    skw = p["SR"]["x0"] - p["SL"]["x1"]
    notes(sh, 240, 120, ["Контроль после шага (К-я1):", "внутренняя ширина спереди и сзади:",
                         f"номинал {skw:g} = проём − {S_['diw']} [Д: {S_['brand']}];", "допуск ±0,5 [Д];",
                         "наш допуск стенок −0,5 / +0 — [М][О];", "диагонали сверху — разность ≤ 1 [М][О]."], size=8.8)
    return sh


def steps_s3(D, n, total):
    p, pos = D["p"], D["pos"]
    S_ = _prof(D)
    rq = S_["rear"]
    sh = Sheet("Сборка ящика — шаги 5–6 (задние Ø6, замки)", stamp(D, "сборщику"), n, total, "без масштаба")
    all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
    bt, SL, SR, Bw = p["BOT"], p["SL"], p["SR"], p["B"]
    step_head(sh, 28, 282, 5, f"Задняя стенка поз. {pos['B']}: проверить 2 отверстия Ø{rq['d']} гл. {rq['depth']}")
    ob2 = Oblique(sh, (40, 160, 200, 262), all5, sgn=-1, zs=1, ys=-1)
    ob2.draw([(q, DONE, {}) for q in all5])
    rr = [h for h in D["s"]["holes"] if h["kind"] == "slide_rear" and h["part"] == Bw["id"]]
    for h in rr:
        x, y = ob2.p(h["x"], h["y"], h["z"])
        sh.ax.add_patch(matplotlib.patches.Circle((x, y), 2.2, fc=RED, ec="k", lw=0.6, zorder=12))
    x, y = ob2.p(rr[0]["x"], rr[0]["y"], rr[0]["z"])
    callout(sh, x, y, x + 10, y + 26, f"Ø{rq['d']} гл. {rq['depth']}: {rq['from_bottom']} от низа, {rq['from_side']} от боковины",
            8.8, RED)
    notes(sh, 210, 262, [f"Данные {S_['brand']} {S_['series']} [Д]: Ø{rq['d']}, глубина {rq['depth']},",
                         f"{rq['from_bottom']} от низа ящика, {rq['from_side']} от боковины.",
                         "Отверстия сверлит цех (таблица отверстий задней стенки).",
                         "Нет отверстий — не сверлить по месту, сообщить в цех."], size=8.6)
    step_head(sh, 28, 140, 6, f"Замки {S_['brand']} Л и П — под дно у передних углов")
    zones = [{"x0": SL["x1"], "x1": SL["x1"] + 75, "y0": bt["y0"], "y1": bt["y0"] + 90},
             {"x0": SR["x0"] - 75, "x1": SR["x0"], "y0": bt["y0"], "y1": bt["y0"] + 90}]
    ob = Oblique(sh, (40, 14, 225, 122), all5, sgn=1, zs=-1)
    ob.draw([(q, DONE, {}) for q in all5])
    for zn, t_ in zip(zones, ("замок Л — у левой боковины", "замок П — у правой боковины")):
        pts = [ob.p(zn["x0"], zn["y0"], bt["z0"]), ob.p(zn["x1"], zn["y0"], bt["z0"]), ob.p(zn["x1"], zn["y1"], bt["z0"]),
               ob.p(zn["x0"], zn["y1"], bt["z0"])]
        sh.ax.add_patch(Polygon(pts, closed=True, fc="#cfe0f5", ec="#1f5fa8", lw=1.2, ls="--", zorder=11))
        x, y = ob.p(zn["x1"], zn["y0"], bt["z0"])
        callout(sh, x, y, x + 4, y - (10 if "Л" in t_ else 22), t_, 8.8, "#1f5fa8")
    notes(sh, 232, 120, ["Ящик кверху дном. Замок левый — у левой боковины,", "правый — у правой, у передних углов.",
                         f"{S_['lock'].split(' (')[0]}.",
                         "Положение и шурупы — по документу и упаковке", f"{S_['brand']}, по месту [Д][О].",
                         "Синие зоны — где работать, а не координаты."], size=8.6)
    return sh


def steps_s4(D, n, total):
    p, pos, r, s = D["p"], D["pos"], D["r"], D["s"]
    S_ = _prof(D)
    P = {q["id"]: q for q in s["parts"]}
    sh = Sheet("Сборка ящика — шаги 7–8 (направляющие, фасад)", stamp(D, "сборщику"), n, total, "без масштаба")
    step_head(sh, 28, 282, 7, f"Ящик — на направляющие {S_['brand']} в корпусе; проверить фиксацию")
    cl, cr = P[r["colL"]], P[r["colR"]]
    SL, SR, bt = p["SL"], p["SR"], p["BOT"]
    rb = r["rb"]
    z0w, z1w = rb - 25, SL["z1"] + 90
    vf = View(sh, 3.6, (40, 168), (cl["x0"] - 5, z0w))
    for S in (cl, cr):
        vf.rect(S["x0"], z0w, S["x1"], z1w, VIS)
        x0_, y0_ = vf.p(S["x0"], z0w); x1_, y1_ = vf.p(S["x1"], z1w)
        sh.hatch(x0_, y0_, x1_, y1_)
    lift = 60
    for S in (SL, SR):
        vf.rect(S["x0"], S["z0"] + lift, S["x1"], S["z1"] + lift, VIS)
    vf.rect(SL["x1"], bt["z0"] + lift, SR["x0"], bt["z1"] + lift, THIN)
    for wall, sgn in ((cl["x1"], 1), (cr["x0"], -1)):
        x_in = wall + sgn * (S_["diw"] / 2)
        vf.rect(min(wall, x_in), rb, max(wall, x_in), rb + 12, dict(lw=0.9, color="#1f5fa8", ls="-"))
        xx, yy = vf.p(wall + sgn * 1.5, rb + S_["screw_axis"])
        sh.cross(xx, yy, 2.2)
    for S in (SL, SR):
        xm = (S["x0"] + S["x1"]) / 2
        a, b = vf.p(xm, S["z0"] + lift - 4), vf.p(xm, S["z0"] + 6)
        sh.ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=RED, lw=1.4, zorder=12))
    xa, ya = vf.p(cl["x1"] + 20, rb + 12)
    callout(sh, xa, ya, xa + 20, ya - 14, f"направляющая {S_['brand']} (схематично, не контур)", 8.5, "#1f5fa8")
    xs_, ys_ = vf.p(cl["x1"] + 1.5, rb + S_["screw_axis"])
    callout(sh, xs_, ys_, xs_ + 30, ys_ + 30, f"ось шурупов {S_['screw_axis']} над низом направляющей [М] (10–12 [Д])", 8.5)
    sh.text(40, 160, "разрез по передней части колонны, вид спереди", size=8, style="italic")
    notes(sh, 255, 264, [f"Направляющие уже закреплены в корпусе: шурупы Ø3,5,",
                         " / ".join(str(v) for v in r["pts"]) + f" от конца направляющей, она на {S_['front_off']}",
                         f"от передней кромки корпуса [Д: {S_['series']}].",
                         "Выдвинуть направляющие. Поставить ящик: штифты", "направляющих — в задние Ø6 (шаг 5),",
                         "опустить спереди до щелчка замков.", "",
                         "Проверить: ящик не снимается без нажатия замков; ход", "без касаний."], size=8.6)
    step_head(sh, 28, 140, 8, f"Фасад поз. {pos['FR']}: 4 самореза 4 × 25 ИЗНУТРИ ящика через переднюю стенку")
    fr, Fw = p["FR"], p["F"]
    shown = [p[k] for k in ("SL", "SR", "F", "BOT")] + [fr]
    ob = Oblique(sh, (40, 14, 175, 120), shown, sgn=1, ys=-1)
    ob.draw([(q, DONE, {}) for q in shown[:-1]] + [(fr, HL, {})])
    fs = joint_holes(D, "FRONT", "front_screw")
    ob.fasteners(fs)
    _check_view(D, ob, "шаг 8")
    x, y = ob.p(fs[0]["x"], fs[0]["y"], fs[0]["z"])
    callout(sh, x, y, x - 95, y + 34, f"{len(fs)} × саморез 4 × 25 — изнутри, PH2", 9, RED)
    t_f, t_w = fr["y1"] - fr["y0"], Fw["y1"] - Fw["y0"]
    eng = 25 - t_w - (Fw["y0"] - fr["y1"])
    g_ = r.get("gap", 0)
    notes(sh, 200, 118, ["Фасад приложить снаружи по зазорам: 3 между фасадами,",
                         "1,5 по краям; " + (f"до корпуса {g_:g} (нажатие) [М]." if g_ else "вплотную к корпусу."),
                         "Саморезы — ИЗНУТРИ ящика через отверстия Ø4,5 с зенковкой", f"передней стенки, вход в фасад {eng:g}, до лица "
                         f"{t_f - eng:g} [М].", "Лицевая сторона фасада — без отверстий и саморезов" +
                         ("." if r.get("hz") is None else ", кроме ручки (2 винта М4 × 22 в Ø5)."),
                         "", f"ПЕРВЫЙ ящик проверить до остальных {D['nd'] - 1} [О]:",
                         ("нажатие открывает, " if S_["push"] else "") + "мягко закрывается, фасад не задевает соседние."],
          size=8.4)
    return sh


SHEETS_BLUM = [sheet_shop, parts_sheet, sheet_steps_1, sheet_steps_2, sheet_steps_3, sheet_steps_4]
SHEETS_SLIDE = [sheet_shop_s, parts_sheet_s, steps_s1, steps_s2, steps_s3, steps_s4]


def write(path, opts):
    D = drawer_data(opts)
    D["view_errors"] = []
    makers = SHEETS_SLIDE if D["r"].get("sys") == "samet" else SHEETS_BLUM
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
    o = {"width": "1200", "level": "comf", "changer": "yes", "body": "K110", "front": "K4069"}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        o[k] = v
    D, _ = write(out, o)
    if D["view_errors"]:
        print("FAIL Крепёж на рисунках: вход не виден или закрыт —", "; ".join(D["view_errors"]))
        sys.exit(1)
    print("ok  Крепёж на рисунках: вход виден и не закрыт — все шаги")
    print("ok", out)
