"""Оформление листов A3: штамп, типы линий, размеры с выносными линиями, позиции, обозначения узлов и разрезов.

Всё рисуется в координатах листа (мм, начало — левый нижний угол). Виды переводят координаты изделия
в координаты листа через View(scale, origin). После отрисовки листа check_overlaps() проверяет,
что тексты не накладываются друг на друга и не выходят за рамку.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

A3 = (420.0, 297.0)
IN = 25.4
RED = "#A23B2A"
plt.rcParams["font.family"] = "DejaVu Sans"

# типы линий (толщина в пунктах; 1 pt ≈ 0,35 мм)
VIS = dict(lw=1.1, color="k", ls="-")                      # видимый контур, ≈0,4 мм
THIN = dict(lw=0.5, color="k", ls="-")                     # тонкая сплошная
HID = dict(lw=0.6, color="k", ls=(0, (4, 2)))              # невидимый контур
CTR = dict(lw=0.45, color="k", ls=(0, (10, 2, 2, 2)))      # осевая / центровая
PHANTOM = dict(lw=0.5, color="#555", ls=(0, (8, 2, 2, 2, 2, 2)))  # смежная деталь / контур снятой детали
DIM = dict(lw=0.45, color="k", ls="-")


class Sheet:
    def __init__(self, title, stamp, n, total, scale_note):
        self.fig = plt.figure(figsize=(A3[0] / IN, A3[1] / IN))
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, A3[0]); ax.set_ylim(0, A3[1]); ax.axis("off")
        self.ax = ax
        # рамка: поле подшивки 20 слева, 5 по остальным сторонам
        ax.add_patch(Rectangle((20, 5), 395, 287, fill=False, lw=1.4))
        self._stamp(title, stamp, n, total, scale_note)

    # ---------------------------------------------------------------- штамп
    def _stamp(self, title, s, n, total, scale_note):
        """Штамп 185 × 48 в правом нижнем углу: изделие, документ и лист, люди, ревизия, масштаб, листы, конфигурация."""
        ax = self.ax
        x0, y0, w, h = 230, 5, 185, 48
        self.STAMP_TOP = y0 + h
        ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.1))
        for yy in (8, 16, 24, 32, 40):
            ax.plot([x0, x0 + w], [y0 + yy, y0 + yy], lw=0.4, c="k")
        for xx in (50, 100, 130):
            ax.plot([x0 + xx, x0 + xx], [y0 + 8, y0 + 32], lw=0.4, c="k")
        t = lambda x, y, txt, **kw: ax.text(x, y, txt, va="center", **{"fontsize": 6.3, **kw})
        t(x0 + 2, y0 + 44, s["product"], fontsize=9, weight="bold")
        t(x0 + 2, y0 + 36, f"{s['doc']}-{n:02d}  ·  {title}", fontsize=7.0, weight="bold")
        t(x0 + 2, y0 + 28, "Разработал (Arvello)"); t(x0 + 52, y0 + 28, "____________")
        t(x0 + 2, y0 + 20, "Проверил"); t(x0 + 52, y0 + 20, "____________")
        t(x0 + 2, y0 + 12, "К изготовлению"); t(x0 + 52, y0 + 12, "НЕ УТВЕРЖДЕНО", color=RED, weight="bold", fontsize=6.0)
        t(x0 + 102, y0 + 28, "Ревизия"); t(x0 + 132, y0 + 28, s["rev"], weight="bold")
        t(x0 + 102, y0 + 20, "Масштаб"); t(x0 + 132, y0 + 20, scale_note, weight="bold", fontsize=6.0)
        t(x0 + 102, y0 + 12, "Лист / листов"); t(x0 + 132, y0 + 12, f"{n} / {total}", weight="bold")
        t(x0 + 2, y0 + 4, f"Конфигурация: {s['config']} · снимок {s['hash']} · единицы: мм", fontsize=5.3)
        ax.text(25, 289, s["status"], fontsize=6.6, color=RED, va="top", weight="bold")

    # ---------------------------------------------------------------- примитивы (координаты листа)
    def rect(self, x0, y0, x1, y1, st=VIS, fill=None):
        self.ax.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0),
                                    fill=fill is not None, fc=fill or "none", ec=st["color"], lw=st["lw"], ls=st["ls"]))

    def line(self, x0, y0, x1, y1, st=THIN):
        self.ax.plot([x0, x1], [y0, y1], color=st["color"], lw=st["lw"], ls=st["ls"], solid_capstyle="butt")

    def circle(self, x, y, r, st=VIS, fill=None):
        self.ax.add_patch(Circle((x, y), r, fill=fill is not None, fc=fill or "none", ec=st["color"], lw=st["lw"], ls=st["ls"]))

    def slot(self, x, y, length, width, horizontal=True, st=VIS):
        """Паз со скруглёнными концами: длина по оси, ширина поперёк."""
        if horizontal:
            self.ax.add_patch(FancyBboxPatch((x - length / 2 + width / 2, y - width / 2), length - width, width,
                                             boxstyle=f"round,pad=0,rounding_size={width / 2}", fill=False,
                                             ec=st["color"], lw=st["lw"], ls=st["ls"], mutation_aspect=1))
            self.ax.add_patch(Circle((x - length / 2 + width / 2, y), width / 2, fill=False, ec=st["color"], lw=st["lw"]))
            self.ax.add_patch(Circle((x + length / 2 - width / 2, y), width / 2, fill=False, ec=st["color"], lw=st["lw"]))
            self.rect(x - length / 2 + width / 2, y - width / 2, x + length / 2 - width / 2, y + width / 2, st=dict(lw=0, color="w", ls="-"), fill="white")
            self.line(x - length / 2 + width / 2, y - width / 2, x + length / 2 - width / 2, y - width / 2, st)
            self.line(x - length / 2 + width / 2, y + width / 2, x + length / 2 - width / 2, y + width / 2, st)
        else:
            self.slot_v(x, y, length, width, st)

    def slot_v(self, x, y, length, width, st=VIS):
        r = width / 2
        self.ax.add_patch(Circle((x, y - length / 2 + r), r, fill=False, ec=st["color"], lw=st["lw"]))
        self.ax.add_patch(Circle((x, y + length / 2 - r), r, fill=False, ec=st["color"], lw=st["lw"]))
        self.rect(x - r, y - length / 2 + r, x + r, y + length / 2 - r, st=dict(lw=0, color="w", ls="-"), fill="white")
        self.line(x - r, y - length / 2 + r, x - r, y + length / 2 - r, st)
        self.line(x + r, y - length / 2 + r, x + r, y + length / 2 - r, st)

    def cross(self, x, y, size=3.0):
        self.line(x - size, y, x + size, y, CTR); self.line(x, y - size, x, y + size, CTR)

    def text(self, x, y, s, size=7.0, **kw):
        return self.ax.text(x, y, s, fontsize=size, **kw)

    def hatch(self, x0, y0, x1, y1, pattern="////"):
        self.ax.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0), fill=False,
                                    hatch=pattern, ec="#444", lw=0))
        self.rect(x0, y0, x1, y1, VIS)

    # ---------------------------------------------------------------- размеры
    def _arrow(self, x, y, dx, dy):
        L, W = 2.6, 0.75
        n = (dx * dx + dy * dy) ** 0.5 or 1
        ux, uy = dx / n, dy / n
        px, py = -uy, ux
        self.ax.add_patch(Polygon([(x, y), (x - ux * L + px * W, y - uy * L + py * W), (x - ux * L - px * W, y - uy * L - py * W)],
                                  closed=True, fc="k", ec="k", lw=0.2))

    def dim_h(self, xa, xb, y_feat_a, y_feat_b, y_dim, text, size=6.8, text_side="above"):
        """Горизонтальный размер: выносные линии от точек (xa, y_feat_a), (xb, y_feat_b) до линии y_dim."""
        g = 1.2 if y_dim > max(y_feat_a, y_feat_b) else -1.2
        for x, yf in ((xa, y_feat_a), (xb, y_feat_b)):
            self.line(x, yf + (1.0 if g > 0 else -1.0), x, y_dim + g * 1.5, DIM)
        self.line(xa, y_dim, xb, y_dim, DIM)
        inside = abs(xb - xa) > 9
        if inside:
            self._arrow(xa, y_dim, -(1 if xb > xa else -1), 0); self._arrow(xb, y_dim, (1 if xb > xa else -1), 0)
        else:
            lo, hi = min(xa, xb), max(xa, xb)
            self.line(lo - 5, y_dim, lo, y_dim, DIM); self.line(hi, y_dim, hi + 5, y_dim, DIM)
            self._arrow(lo, y_dim, 1, 0); self._arrow(hi, y_dim, -1, 0)
        tx = (xa + xb) / 2 if inside else max(xa, xb) + 6
        ha = "center" if inside else "left"
        return self.text(tx, y_dim + (0.8 if text_side == "above" else -0.8), text, size=size, ha=ha,
                         va="bottom" if text_side == "above" else "top")

    def dim_v(self, ya, yb, x_feat_a, x_feat_b, x_dim, text, size=6.8):
        g = 1.2 if x_dim > max(x_feat_a, x_feat_b) else -1.2
        for y, xf in ((ya, x_feat_a), (yb, x_feat_b)):
            self.line(xf + (1.0 if g > 0 else -1.0), y, x_dim + g * 1.5, y, DIM)
        self.line(x_dim, ya, x_dim, yb, DIM)
        inside = abs(yb - ya) > 9
        if inside:
            self._arrow(x_dim, ya, 0, -(1 if yb > ya else -1)); self._arrow(x_dim, yb, 0, (1 if yb > ya else -1))
            ty, va = (ya + yb) / 2, "center"
        else:
            lo, hi = min(ya, yb), max(ya, yb)
            self.line(x_dim, lo - 5, x_dim, lo, DIM); self.line(x_dim, hi, x_dim, hi + 5, DIM)
            self._arrow(x_dim, lo, 0, 1); self._arrow(x_dim, hi, 0, -1)
            ty, va = hi + 6, "bottom"
        return self.text(x_dim - 0.9, ty, text, size=size, ha="right", va=va, rotation=90)

    def leader(self, x, y, tx, ty, text, size=6.6, dot=True, ha=None):
        if dot:
            self.circle(x, y, 0.55, st=THIN, fill="k")
        self.line(x, y, tx, ty, THIN)
        ha = ha or ("left" if tx >= x else "right")
        shelf = 2 + len(text.split("\n")[0]) * size * 0.19
        x2 = tx + shelf if ha == "left" else tx - shelf
        self.line(tx, ty, x2, ty, THIN)
        return self.text(tx + (0.8 if ha == "left" else -0.8), ty + 0.6, text, size=size, ha=ha, va="bottom")

    def balloon(self, x, y, tx, ty, num, r=3.4):
        """Позиция: выноска с точкой на детали и номер в кружке."""
        self.circle(x, y, 0.55, st=THIN, fill="k")
        d = ((tx - x) ** 2 + (ty - y) ** 2) ** 0.5 or 1
        self.line(x, y, tx - (tx - x) / d * r, ty - (ty - y) / d * r, THIN)
        self.circle(tx, ty, r, st=THIN, fill="white")
        return self.text(tx, ty, str(num), size=7.2 if len(str(num)) < 3 else 5.8, ha="center", va="center", weight="bold")

    def node_mark(self, x, y, r, letter, ref, dx=1, dy=1):
        """Обозначение выносного элемента: окружность на виде, полка с буквой и ссылкой на лист."""
        self.circle(x, y, r, st=THIN)
        a = 0.7071
        sx, sy = x + dx * r * a, y + dy * r * a
        ex, ey = sx + dx * 6, sy + dy * 6
        self.line(sx, sy, ex, ey, THIN)
        self.line(ex, ey, ex + dx * 15, ey, THIN)
        return self.text(ex + dx * 0.8, ey + 0.7, f"{letter} ({ref})", size=7.2, weight="bold", va="bottom",
                         ha="left" if dx > 0 else "right")

    def section_marks(self, x0, y0, x1, y1, letter, dx=0, dy=-1):
        """Линия разреза: утолщённые штрихи на концах, стрелки направления взгляда, буквы."""
        for x, y in ((x0, y0), (x1, y1)):
            self.ax.plot([x - 3 * abs(x1 - x0 and 1) * 0, x], [y, y], lw=0)
        L = 6
        if abs(x1 - x0) > abs(y1 - y0):
            for x in (x0, x1):
                self.line(x - L / 2, y0, x + L / 2, y0, dict(lw=1.6, color="k", ls="-"))
                self.line(x, y0, x, y0 + 7 * dy, THIN); self._arrow(x, y0 + 7 * dy, 0, dy)
                self.text(x + 1.5, y0 + 8 * dy, letter, size=8.5, weight="bold", va="center")
        else:
            for y in (y0, y1):
                self.line(x0, y - L / 2, x0, y + L / 2, dict(lw=1.6, color="k", ls="-"))
                self.line(x0, y, x0 + 7 * dx, y, THIN); self._arrow(x0 + 7 * dx, y, dx, 0)
                self.text(x0 + 8 * dx, y + 1.5, letter, size=8.5, weight="bold", ha="center")

    def view_title(self, x, y, s, size=8.0):
        t = self.text(x, y, s, size=size, weight="bold", va="bottom")
        return t

    def front_arrow(self, x, y, label="ПЕРЕД", dx=0, dy=-1):
        self.line(x, y, x + dx * 9, y + dy * 9, dict(lw=0.9, color="k", ls="-"))
        self._arrow(x + dx * 9, y + dy * 9, dx, dy)
        self.text(x + 2, y - 2 if dy < 0 else y + 2, label, size=7, weight="bold", va="center")

    def table(self, x, y_top, cols, rows, widths, row_h=5.2, head=True, size=6.5, max_chars=None):
        """Таблица: cols — заголовки, widths — ширины колонок (мм). Возвращает y низа таблицы."""
        y = y_top
        total = sum(widths)
        allrows = ([cols] if head else []) + rows
        for i, r in enumerate(allrows):
            self.line(x, y, x + total, y, THIN if i else dict(lw=0.8, color="k", ls="-"))
            cx = x
            for c, w in zip(r, widths):
                s = str(c)
                lim = max_chars or int(w / (size * 0.21))
                if len(s) > lim:
                    s = s[:lim - 1] + "…"
                self.text(cx + 1.2, y - row_h / 2, s, size=size, va="center",
                          weight="bold" if (head and i == 0) else "normal")
                cx += w
            y -= row_h
        self.line(x, y, x + total, y, dict(lw=0.8, color="k", ls="-"))
        cx = x
        for w in widths + [0]:
            self.line(cx, y_top, cx, y, THIN)
            cx += w
        return y

    # ---------------------------------------------------------------- проверка
    def check_overlaps(self, tol=0.6):
        """Пары накладывающихся текстов и тексты за рамкой. tol — допустимое перекрытие, мм."""
        r = self.fig.canvas.get_renderer()
        px = self.fig.bbox.width / A3[0]
        boxes = [(t.get_window_extent(r), t.get_text()) for t in self.ax.texts if t.get_text().strip()]
        bad = []
        for i, (a, ta) in enumerate(boxes):
            if a.x0 < 20 * px - 1 or a.x1 > 415 * px + 1 or a.y0 < 5 * px - 1 or a.y1 > 292 * px + 1:
                bad.append(("за рамкой", ta[:40], ""))
            for b, tb in boxes[i + 1:]:
                ox = min(a.x1, b.x1) - max(a.x0, b.x0)
                oy = min(a.y1, b.y1) - max(a.y0, b.y0)
                if ox > tol * px and oy > tol * px:
                    bad.append(("наложение", ta[:40], tb[:40]))
        return bad


class View:
    """Перевод координат изделия (мм) в координаты листа: page = origin + (model - m0) / scale."""

    def __init__(self, sheet, scale, origin, m0=(0.0, 0.0)):
        self.s, self.sc, self.o, self.m0 = sheet, scale, origin, m0

    def p(self, u, v):
        return (self.o[0] + (u - self.m0[0]) / self.sc, self.o[1] + (v - self.m0[1]) / self.sc)

    def rect(self, u0, v0, u1, v1, st=VIS, fill=None):
        a, b = self.p(u0, v0), self.p(u1, v1)
        self.s.rect(a[0], a[1], b[0], b[1], st, fill)

    def line(self, u0, v0, u1, v1, st=THIN):
        a, b = self.p(u0, v0), self.p(u1, v1)
        self.s.line(a[0], a[1], b[0], b[1], st)
