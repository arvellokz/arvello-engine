"""Чертёжные функции для плитных (корпусных) изделий: деталировка детали и разрезы по снимку.

Все размеры и отверстия берутся из снимка: деталь — параллелепипед в координатах изделия,
отверстие — точка входа, направление сверления, Ø и глубина (см. eng/samal.py).

detail()  — вид на пласть детали с отверстиями (видимые / невидимые / в торец — штриховой линией),
            кромками по сторонам, базой, направлением текстуры и координатными размерами от базы;
section() — разрез изделия плоскостью: рассечённые детали со штриховкой, отверстия в плоскости разреза.
"""
from __future__ import annotations

from .sheetlib import CTR, DIM, HID, PHANTOM, THIN, VIS

AX = {"x": 0, "y": 1, "z": 2}
NAME = {"-y": "перед", "+y": "зад", "+z": "верх", "-z": "низ", "-x": "лево", "+x": "право"}
EDGE_TXT = {"ABS2": "ABS 2", "PVC04": "0,4"}
EDGE_T = {"ABS2": 2.0, "PVC04": 0.4}


def vec(d):
    v = [0, 0, 0]
    v[AX[d[1]]] = 1 if d[0] == "+" else -1
    return tuple(v)


def name_of(v):
    i = next(k for k in range(3) if v[k])
    return ("+" if v[i] > 0 else "-") + "xyz"[i]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def neg(a):
    return tuple(-x for x in a)


class Frame:
    """Локальные координаты вида на пласть: n — нормаль к смотрящему, up — вверх листа."""

    def __init__(self, p, n, up):
        self.p, self.n, self.up = p, vec(n), vec(up)
        self.right = cross(neg(self.n), self.up)
        cs = [(x, y, z) for x in (p["x0"], p["x1"]) for y in (p["y0"], p["y1"]) for z in (p["z0"], p["z1"])]
        self.u0 = min(dot(c, self.right) for c in cs); self.v0 = min(dot(c, self.up) for c in cs)
        self.Lu = max(dot(c, self.right) for c in cs) - self.u0
        self.Lv = max(dot(c, self.up) for c in cs) - self.v0
        self.w0 = min(dot(c, self.n) for c in cs)
        self.t = max(dot(c, self.n) for c in cs) - self.w0

    def uv(self, x, y, z):
        return dot((x, y, z), self.right) - self.u0, dot((x, y, z), self.up) - self.v0

    def side(self, face):
        """Где на виде лежит грань с нормалью face: 'R','L','T','B' или 'F' (пласть к смотрящему), 'K' (обратная)."""
        v = vec(face)
        if v == self.right:
            return "R"
        if v == neg(self.right):
            return "L"
        if v == self.up:
            return "T"
        if v == neg(self.up):
            return "B"
        return "F" if v == self.n else "K"

    def base_corner(self):
        """Названия граней, образующих базовый угол (u=0, v=0)."""
        return NAME[name_of(neg(self.right))], NAME[name_of(neg(self.up))]


def blank(fr, edges):
    """Размер заготовки по u и v: готовый минус толщина кромки на каждой окромкованной стороне вида."""
    eu = sum(EDGE_T[t] for f, t in edges.items() if fr.side(f) in ("L", "R"))
    ev = sum(EDGE_T[t] for f, t in edges.items() if fr.side(f) in ("T", "B"))
    return fr.Lu - eu, fr.Lv - ev


def _spread(ps, lo, hi, gap):
    """Позиции подписей ординат: подпись «0» стоит в lo; не ближе gap друг к другу, по возможности не дальше hi."""
    fwd, last = [], lo
    for p in ps:
        last = max(p, last + gap)
        fwd.append(last)
    if not fwd or fwd[-1] <= hi:
        return fwd
    back, nxt = list(fwd), hi + gap
    for i in range(len(back) - 1, -1, -1):
        nxt = min(back[i], nxt - gap)
        back[i] = nxt
    return back if back[0] >= lo + gap else fwd


def detail(sh, s, pid, x, y, scale, n, up, holes=None, ext=None, ord_top=True, ord_right=True, label_sides=True):
    """Вид на пласть детали pid; (x, y) — левый нижний угол контура на листе. Возвращает (Frame, bbox на листе)."""
    p = next(q for q in s["parts"] if q["id"] == pid)
    fr = Frame(p, n, up)
    ext = ext or s["derived"].get("parts_ext", {}).get(pid, {})
    holes = [h for h in (holes if holes is not None else s["holes"]) if h["part"] == pid]
    P = lambda u, v: (x + u / scale, y + v / scale)
    x1, y1 = P(fr.Lu, fr.Lv)
    sh.rect(x, y, x1, y1, VIS)
    us, vs = set(), set()
    for h in holes:
        d = vec(h["dir"])
        hu, hv = fr.uv(h["x"], h["y"], h["z"])
        r = h["d"] / 2 / scale
        if d == fr.n or d == neg(fr.n):
            visible = h["through"] or d == neg(fr.n)
            cx, cy = P(hu, hv)
            sh.circle(cx, cy, max(r, 0.35), st=VIS if visible else HID)
            if h.get("cs") and (d == neg(fr.n)):
                sh.circle(cx, cy, max(r * 1.7, 0.6), st=THIN)
            sh.cross(cx, cy, max(r + 1.0, 1.4))
            us.add(round(hu, 1)); vs.add(round(hv, 1))
        else:
            du, dv = dot(d, fr.right), dot(d, fr.up)
            L = h["depth"]
            a = P(hu, hv); b = P(hu + du * L, hv + dv * L)
            if du:
                sh.line(a[0], a[1] - r, b[0], b[1] - r, HID); sh.line(a[0], a[1] + r, b[0], b[1] + r, HID)
                sh.line(b[0], b[1] - r, b[0], b[1] + r, HID)
                sh.line(a[0] - du * 1.2, a[1], b[0] + du * 1.2, b[1], CTR)
                vs.add(round(hv, 1))
            else:
                sh.line(a[0] - r, a[1], b[0] - r, b[1], HID); sh.line(a[0] + r, a[1], b[0] + r, b[1], HID)
                sh.line(b[0] - r, b[1], b[0] + r, b[1], HID)
                sh.line(a[0], a[1] - dv * 1.2, b[0], b[1] + dv * 1.2, CTR)
                us.add(round(hu, 1))
    # кромки: утолщённая линия вдоль стороны снаружи контура
    edges = ext.get("edges", {})
    for face, typ in edges.items():
        sd = fr.side(face)
        o = 1.1
        lw = dict(lw=2.4 if typ == "ABS2" else 1.2, color="#A23B2A", ls="-")
        if sd == "L":
            sh.line(x - o, y, x - o, y1, lw)
        elif sd == "R":
            sh.line(x1 + o, y, x1 + o, y1, lw)
        elif sd == "B":
            sh.line(x, y - o, x1, y - o, lw)
        elif sd == "T":
            sh.line(x, y1 + o, x1, y1 + o, lw)
    # подписи сторон (с типом кромки)
    if label_sides:
        for face in ("-x", "+x", "-y", "+y", "-z", "+z"):
            sd = fr.side(face)
            if sd not in ("L", "R", "T", "B"):
                continue
            t = NAME[face].upper() + (f" · {EDGE_TXT[edges[face]]}" if face in edges else "")
            if sd == "B":
                sh.text((x + x1) / 2, y - 2.6, t, size=5.6, ha="center", va="top", color="#333")
            elif sd == "L":
                sh.text(x - 2.6, (y + y1) / 2, t, size=5.6, ha="right", va="center", rotation=90, color="#333")
            elif sd == "T" and not ord_top:
                sh.text((x + x1) / 2, y1 + 2.4, t, size=5.6, ha="center", va="bottom", color="#333")
            elif sd == "R" and not ord_right:
                sh.text(x1 + 2.6, (y + y1) / 2, t, size=5.6, ha="left", va="center", rotation=90, color="#333")
            elif sd == "T":
                fr._top_label = t
            elif sd == "R":
                fr._right_label = t
    # база
    sh.ax.plot([x], [y], marker="s", ms=3.2, color="k")
    sh.text(x - 1.2, y - 1.2, "A", size=7, weight="bold", ha="right", va="top")
    # текстура
    g = ext.get("grain")
    if g:
        gv = vec("+" + g)
        gu, gvv = abs(dot(gv, fr.right)), abs(dot(gv, fr.up))
        cx, cy = (x + x1) / 2, y + (y1 - y) * 0.18
        Ls = min(12, (x1 - x) * 0.3) if gu else min(12, (y1 - y) * 0.3)
        if gu:
            sh.ax.annotate("", (cx + Ls / 2, cy), (cx - Ls / 2, cy), arrowprops=dict(arrowstyle="<->", lw=0.8))
        else:
            sh.ax.annotate("", (cx, cy + Ls / 2), (cx, cy - Ls / 2), arrowprops=dict(arrowstyle="<->", lw=0.8))
        sh.text(cx + 1.5, cy + 1.2, "текстура", size=5.2, color="#333")
    # координатные размеры от базы (ординаты)
    bb = [x, y, x1, y1]
    if ord_top:
        yy = y1 + 5.5
        sh.line(x, y1 + 2.5, x, yy, DIM)
        sh.text(x, yy + 0.6, "0", size=5.6, ha="center", va="bottom", rotation=90)
        uu = sorted(us | {round(fr.Lu, 1)})
        for u, tx in zip(uu, _spread([x + u / scale for u in uu], x, x1, 2.9)):
            px = x + u / scale
            sh.line(px, y1 + 2.5, px, yy, DIM)
            sh.text(tx, yy + 0.6, f"{u:g}", size=5.6, ha="center", va="bottom", rotation=90)
        bb[3] = yy + 9
        if getattr(fr, "_top_label", None):
            sh.text((x + x1) / 2, yy + 9.5, fr._top_label, size=5.6, ha="center", va="bottom", color="#333")
            bb[3] = yy + 13
    if ord_right:
        xx = x1 + 5.0
        sh.line(x1 + 2.5, y, xx, y, DIM)
        sh.text(xx + 0.6, y, "0", size=5.6, va="center")
        vv = sorted(vs | {round(fr.Lv, 1)})
        for v, ty in zip(vv, _spread([y + v / scale for v in vv], y, y1, 2.7)):
            py = y + v / scale
            sh.line(x1 + 2.5, py, xx, py, DIM)
            sh.text(xx + 0.6, ty, f"{v:g}", size=5.6, va="center")
        bb[2] = xx + 9
        if getattr(fr, "_right_label", None):
            sh.text(xx + 9.5, (y + y1) / 2, fr._right_label, size=5.6, ha="left", va="center", rotation=90, color="#333")
            bb[2] = xx + 13
    return fr, bb


KIND_RU = {"ecc_stem": "шток эксцентрика", "ecc_bolt": "под стяжку эксцентрика", "ecc_housing": "корпус эксцентрика",
           "dowel_face": "шкант", "dowel_edge": "шкант", "conf_face": "конфирмат", "conf_edge": "конфирмат",
           "back_pilot": "засверловка под саморез ХДФ", "runner_mark": "разметка: саморез профиля Blum Ø4 × 15", "front_screw": "саморез фасада", "handle": "винт ручки",
           "shelf_pin": "полкодержатель Ø5 (ряд ± 32)",
           "hinge_cup_screw": "саморез чашки петли"}


def hole_rows(s, pid, fr, node_fn=None):
    """Строки таблицы отверстий детали: Ø, глубина, где, количество, назначение, узел."""
    groups = {}
    for h in s["holes"]:
        if h["part"] != pid:
            continue
        d = vec(h["dir"])
        if d == fr.n or d == neg(fr.n):
            where = "пласть, насквозь" if h["through"] else ("пласть на виде" if d == neg(fr.n) else "обратная пласть")
            if not h["depth"] and not h["through"]:
                where = "пласть на виде, без сверления"
        else:
            where = "торец «" + NAME[name_of(neg(d))] + "», по оси толщины"
        dep = "насквозь" if h["through"] else ("разметка" if not h["depth"] else f"{h['depth']:g}")
        k = (h["d"], dep, where, KIND_RU[h["kind"]] + (", зенковка" if h.get("cs") else ""), node_fn(h) if node_fn else "")
        groups[k] = groups.get(k, 0) + 1
    rows = [[f"Ø{k[0]:g}", k[1], k[2], str(n), k[3], k[4]] for k, n in sorted(groups.items(), key=lambda kv: (-kv[0][0], kv[0][2]))]
    return rows


# ------------------------------------------------------------------ разрезы

def section(view, s, cut, val, uax, vax, window, kinds=("board", "buy"), skip=(), frame=True):
    """Разрез плоскостью cut = val. Проекция на оси uax, vax (строки '+y', '-x' …). window = (u0, u1, v0, v1)."""
    sh = view.s
    ua, va = vec(uax), vec(vax)
    u0, u1, v0, v1 = window

    def pu(pt):
        return dot(pt, ua), dot(pt, va)
    c = AX[cut]
    for p in s["parts"]:
        if p["kind"] not in kinds or p["id"] in skip:
            continue
        lo, hi = p["xyz"[c] + "0"], p["xyz"[c] + "1"]
        if not (lo < val < hi):
            continue
        a = pu((p["x0"], p["y0"], p["z0"])); b = pu((p["x1"], p["y1"], p["z1"]))
        pa, pb = (min(a[0], b[0]), max(a[0], b[0])), (min(a[1], b[1]), max(a[1], b[1]))
        ca, cb = (max(pa[0], u0), min(pa[1], u1)), (max(pb[0], v0), min(pb[1], v1))
        if ca[0] >= ca[1] or cb[0] >= cb[1]:
            continue
        q0, q1 = view.p(ca[0], cb[0]), view.p(ca[1], cb[1])
        from matplotlib.patches import Rectangle
        hatch = "xxxx" if p["kind"] == "buy" else ("////" if p["finish"] not in ("INNER",) else "\\\\\\\\")
        sh.ax.add_patch(Rectangle((q0[0], q0[1]), q1[0] - q0[0], q1[1] - q0[1], fill=True, fc="white", hatch=hatch,
                                  ec="#666", lw=0))
        for (e, val2, along) in (("u", pa[0], cb), ("u", pa[1], cb), ("v", pb[0], ca), ("v", pb[1], ca)):
            if e == "u" and u0 <= val2 <= u1:
                A, B = view.p(val2, along[0]), view.p(val2, along[1]); sh.line(A[0], A[1], B[0], B[1], VIS)
            if e == "v" and v0 <= val2 <= v1:
                A, B = view.p(along[0], val2), view.p(along[1], val2); sh.line(A[0], A[1], B[0], B[1], VIS)
    out = []
    for h in s["holes"]:
        hp = (h["x"], h["y"], h["z"])
        d = vec(h["dir"])
        if abs(hp[c] - val) < 0.01 and d[c] == 0:
            du, dv = dot(d, ua), dot(d, va)
            hu, hv = pu(hp)
            L, r = h["depth"], h["d"] / 2
            e0, e1 = (hu, hv), (hu + du * L, hv + dv * L)
            uu = sorted([e0[0], e1[0]]) if du else [hu - r, hu + r]
            vv = sorted([e0[1], e1[1]]) if dv else [hv - r, hv + r]
            if uu[1] < u0 or uu[0] > u1 or vv[1] < v0 or vv[0] > v1:
                continue
            q0, q1 = view.p(max(uu[0], u0), max(vv[0], v0)), view.p(min(uu[1], u1), min(vv[1], v1))
            sh.rect(q0[0], q0[1], q1[0], q1[1], VIS, fill="white")
            A, B = view.p(*e0), view.p(*e1)
            sh.line(A[0] - (du * 1.5), A[1] - (dv * 1.5), B[0] + du * 1.5, B[1] + dv * 1.5, CTR)
            out.append((h, view.p(*((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2))))
        elif d[c] != 0:
            ent = hp[c]; ext_ = ent + d[c] * h["depth"]
            if min(ent, ext_) < val < max(ent, ext_):
                hu, hv = pu(hp)
                if u0 <= hu <= u1 and v0 <= hv <= v1:
                    cx, cy = view.p(hu, hv)
                    sh.circle(cx, cy, h["d"] / 2 / view.sc, st=VIS, fill="white")
                    sh.cross(cx, cy, h["d"] / 2 / view.sc + 1.2)
                    out.append((h, (cx, cy)))
    # рамка окна (обрыв)
    if frame:
        a, b = view.p(u0, v0), view.p(u1, v1)
        sh.rect(a[0], a[1], b[0], b[1], PHANTOM)
    return out
