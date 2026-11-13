"""Листы для цеха по руководству БАЗИС «Создание документов с модели» (16.04.2026) — новые модели (models_new.NEW).

Решение владельца 13.11: комплект для цеха — полностью по правилам руководства, чтобы цеху на БАЗИСе было привычно.
Правила (раздел руководства → что делает генератор → проверка в verify_bazis):
  Б1  2.3, гл. 3   чертёж на каждую панель, один лист (при длинной таблице — второй лист чертежа)
  Б2  2.3.2        лицевая сторона — пласть с бо́льшим числом отверстий; второе изображение (обратная сторона) — если
                   глухие отверстия на обеих пластях
  Б3  2.3.2        виды с торца — при торцевых отверстиях
  Б4  2.3.4, 2.3.10 отверстия пронумерованы на виде; таблица N / D / H / X / Y / Тип, порядок: сквозные, лицевые,
                   обратные, торцевые; номер на виде = строка таблицы
  Б5  2.3.6        паз — обозначение на виде и сечение паза
  Б6  2.3.8        облицовка кромок — знак с номером на каждой облицованной стороне, таблица облицовки и порядок
                   облицовывания (короткие → длинные [М])
  Б7  2.3.2, 7.3   контур / размер заготовки: готовый − кромка + припуск на фуговку (cab.TECH) — одинаково на листе
                   детали и в спецификации
  Б8  2.3.10, 3.2.2 таблица операций на панель с колонкой «кто» (цех / сборщик)
  Б9  2.4.2        сборочный чертёж на ящики и блоки (столик) со спецификацией узла
  Б10 гл. 2.6, П8  обозначение исполнения (модель.ревизия.исполнение) и снимок — на всех листах и в спецификации
  Б11 П7           таблицы без обрезки «…»
Типовые значения, зависящие от цеха (размеры от облицовки, порядок операций, припуск): cab.TECH, метка [М], проба [О].
"""
from __future__ import annotations

from matplotlib.patches import Rectangle

from eng import boardkit
from eng.boardkit import EDGE_T, EDGE_TXT, NAME, Frame, dot, name_of, neg, vec
from eng.cab import TECH
from eng.sheetlib import CTR, HID, RED, THIN, VIS, Sheet, View

TYPE_ORDER = {"С": 0, "Л": 1, "О": 2, "Т": 3}
TYPE_RU = {"С": "сквозное", "Л": "лицевое", "О": "обратное", "Т": "торцевое"}
SIDE_RU = {"L": "левая", "R": "правая", "T": "верхняя", "B": "нижняя"}


def _n(x):
    from eng.kit13 import n_
    return n_(x)


# ------------------------------------------------------------------ обозначение исполнения (Б10)
def variant_code(s):
    """Код исполнения из опций конфигурации: значения по порядку, коротко (1200-PUSH-YES-O)."""
    vals = []
    for k, v in s["options"].items():
        v = str(v)
        vals.append(v if v.isdigit() else v[:4].upper())
    return "-".join(vals)


def designation(s):
    return f"{s['sku']}.{s['rev']}.{variant_code(s)}"


# ------------------------------------------------------------------ данные панели
def blank_size(fr, edges):
    """Б7: заготовка = готовый − толщина кромки + припуск на фуговку на каждую облицованную сторону."""
    al = TECH["edge_allow"]
    eu = sum(EDGE_T[t] - al for f, t in edges.items() if fr.side(f) in ("L", "R"))
    ev = sum(EDGE_T[t] - al for f, t in edges.items() if fr.side(f) in ("T", "B"))
    return round(fr.Lu - eu, 1), round(fr.Lv - ev, 1)


def panel_data(s, pid):
    from eng.kit13 import view_dirs
    p = next(q for q in s["parts"] if q["id"] == pid)
    n, up = view_dirs(s, p)
    fr = Frame(p, n, up)
    if fr.Lv > 1.5 * fr.Lu:                      # разбор 13.11 (G4): высокую панель кладём длинной стороной вдоль листа
        up = name_of(neg(fr.right))
        fr = Frame(p, n, up)
    ext = s["derived"]["parts_ext"].get(pid, {})
    hs = []
    for h in s["holes"]:
        if h["part"] != pid:
            continue
        d = vec(h["dir"])
        u, v = fr.uv(h["x"], h["y"], h["z"])
        if d == neg(fr.n) or d == fr.n:
            typ = "С" if h["through"] else ("Л" if d == neg(fr.n) else "О")
            side, w = None, None
        else:
            typ = "Т"
            side = fr.side(name_of(neg(d)))
            w = round((fr.w0 + fr.t) - dot((h["x"], h["y"], h["z"]), fr.n), 1)    # от пласти на виде
        cs = ("Л" if d == neg(fr.n) else "О") if h.get("cs") and typ == "С" else None   # пласть входа самореза
        hs.append(dict(h=h, typ=typ, u=round(u, 1), v=round(v, 1), side=side, w=w, cs=cs))
    hs.sort(key=lambda q: (TYPE_ORDER[q["typ"]], q["side"] or "", q["u"], q["v"]))
    for i, q in enumerate(hs, 1):
        q["N"] = i
    blind_l = any(q["typ"] == "Л" for q in hs)
    blind_o = any(q["typ"] == "О" for q in hs)
    grooves = []
    for gi, g in enumerate([g for g in s["derived"].get("grooves", []) if g["part"] == pid], 1):
        th = next(a for a in "xyz" if abs(p[a + "1"] - p[a + "0"] - fr.t) < 0.01 and abs(dot(vec("+" + a), fr.n)) == 1)
        on_face = abs(g[th + "1"] - p[th + "1"]) < 0.01 and dot(vec("+" + th), fr.n) > 0 or \
            abs(g[th + "0"] - p[th + "0"]) < 0.01 and dot(vec("-" + th), fr.n) > 0
        cs = [(x, y, z) for x in (g["x0"], g["x1"]) for y in (g["y0"], g["y1"]) for z in (g["z0"], g["z1"])]
        uvs = [fr.uv(*c) for c in cs]
        grooves.append(dict(name=f"П{gi}", g=g, face="Л" if on_face else "О",
                            u0=min(a for a, _ in uvs), u1=max(a for a, _ in uvs),
                            v0=min(b for _, b in uvs), v1=max(b for _, b in uvs)))
    edges = ext.get("edges", {})
    elist = []
    for f, t in edges.items():
        sd = fr.side(f)
        if sd not in ("L", "R", "T", "B"):
            continue
        L = fr.Lv if sd in ("L", "R") else fr.Lu
        elist.append(dict(face=f, side=sd, typ=t, L=round(L, 1)))
    elist.sort(key=lambda e: (e["L"], "LRTB".index(e["side"])))            # короткие → длинные [М]
    for i, e in enumerate(elist, 1):
        e["order"] = i
    return dict(p=p, fr=fr, n=n, up=up, holes=hs, need_two=blind_l and blind_o, grooves=grooves, edges=elist,
                blank=blank_size(fr, edges), grain=ext.get("grain"), wide=max(fr.Lu, fr.Lv) >= WIDE_FROM)


def operations(s, P):
    """Б8: таблица операций панели (БАЗИС 2.3.10 / 3.2.2) с исполнителем."""
    p, hs = P["p"], P["holes"]
    ops = [["1", "раскрой", f"заготовка {_n(P['blank'][0])} × {_n(P['blank'][1])} × {_n(round(P['fr'].t, 1))}", "цех"]]
    if P["edges"]:
        ops.append([str(len(ops) + 1), "облицовка кромок",
                    f"{len(P['edges'])} стор., порядок {'-'.join(str(e['order']) for e in P['edges'])} (кор. → длин.) [М]",
                    "цех"])
    drill = [q for q in hs if q["h"]["depth"] or q["h"]["through"]]
    if drill:
        ops.append([str(len(ops) + 1), "присадка", f"{len(drill)} отв. по таблице, {TECH['dims_from']} [М]", "цех"])
    mark = [q for q in hs if not (q["h"]["depth"] or q["h"]["through"])]
    if mark:
        ops.append([str(len(ops) + 1), "разметка (накол)", f"{len(mark)} точек под саморезы профилей Blum", "цех"])
        ops.append([str(len(ops) + 1), "профили Blum", f"{len(mark)} саморезов по разметке", "сборщик"])
    for g in P["grooves"]:
        gg = g["g"]
        along_u = (g["u1"] - g["u0"]) >= (g["v1"] - g["v0"])
        dist = round(g["v0"] if along_u else g["u0"], 1)          # от базы A изображения 1 (разбор 13.11)
        ops.append([str(len(ops) + 1), "паз", f"{g['name']}: {_n(gg['w'])} × {_n(gg['depth'])}, {_n(dist)} от "
                    f"{'нижнего' if along_u else 'левого'} края (база A)", "цех"])
    box = [r for r in s["derived"].get("drawers", []) if p["id"] in r["box"][:2]]
    if box:
        ops.append([str(len(ops) + 1), "крючок, замки Blum", "по шаблону T65.1000.02 после сборки короба [М]", "сборщик"])
    return ops


# ------------------------------------------------------------------ рисование
class Labels:
    """Размещение номеров отверстий без наложений: 8 позиций вокруг центра, приблизительные рамки текста (мм)."""

    def __init__(self, sh, size=None):
        size = LABEL_PT if size is None else size
        self.sh, self.size, self.boxes = sh, size, []

    def _box(self, x, y, t, ha, va):
        w, h = len(t) * self.size * 0.24 + 0.5, self.size * 0.42
        x0 = x if ha == "left" else x - w
        y0 = y if va == "bottom" else y - h
        return (x0, y0, x0 + w, y0 + h)

    def put(self, x, y, t, avoid=()):
        cands = [(1.0, 0.8, "left", "bottom"), (1.0, -0.8, "left", "top"), (-1.0, 0.8, "right", "bottom"),
                 (-1.0, -0.8, "right", "top"), (2.6, 2.2, "left", "bottom"), (2.6, -2.2, "left", "top"),
                 (-2.6, 2.2, "right", "bottom"), (-2.6, -2.2, "right", "top"), (0.0, 3.4, "left", "bottom"),
                 (0.0, -3.4, "right", "top"), (4.2, 0.0, "left", "bottom"), (-4.2, 0.0, "right", "top")]
        for dx, dy, ha, va in cands:
            b = self._box(x + dx, y + dy, t, ha, va)
            if all(b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3] for o in self.boxes + list(avoid)):
                break
        self.boxes.append(b)
        self.sh.text(x + dx, y + dy, t, size=self.size, ha=ha, va=va, color="#1f3f8f", weight="bold")
        return b


def _image(sh, P, x, y, sc, mirror, reg, labels, title):
    """Изображение пласти: mirror=False — лицевая (вид), True — обратная (зеркально по u)."""
    fr = P["fr"]
    Lu, Lv = fr.Lu, fr.Lv
    U = (lambda u: Lu - u) if mirror else (lambda u: u)
    Pt = lambda u, v: (x + U(u) / sc, y + v / sc)
    x1, y1 = x + Lu / sc, y + Lv / sc
    sh.rect(x, y, x1, y1, VIS)
    sh.ax.plot([x], [y], marker="s", ms=3.0, color="k")
    sh.text(x - 1.2, y - 1.2, "A", size=7, weight="bold", ha="right", va="top")
    ty = None if mirror else reg.get("title_y")
    if ty is None:
        sh.text(x, y1 + 6.5, title, size=6.4, weight="bold", va="bottom")      # выше знаков облицовки верхней стороны
        labels.boxes.append((x, y1 + 6, x + len(title) * 1.3, y1 + 10.5))
    else:                                       # подпись над полем чертежа (узкие высокие панели)
        sh.text(x, ty, title, size=6.4, weight="bold", va="bottom")
    labels.boxes.append(((x + x1) / 2 - 5, y - 10, (x + x1) / 2 + 5, y - 5))            # размер по ширине
    xd = (x1 + 6) if not mirror else (x - 6)
    labels.boxes.append((xd - 3, (y + y1) / 2 - 5, xd + 3, (y + y1) / 2 + 5))            # размер по высоте
    # знаки облицовки (Б6): номер в кружке + материал, у середины стороны
    for e in P["edges"]:
        sd = e["side"]
        if mirror and sd in ("L", "R"):
            sd = "R" if sd == "L" else "L"
        o = 1.2
        lw = dict(lw=2.2 if e["typ"] == "ABS2" else 1.1, color=RED, ls="-")
        if sd == "L":
            sh.line(x - o, y, x - o, y1, lw); px, py = x - 3.2, y + (y1 - y) * 0.15
        elif sd == "R":
            sh.line(x1 + o, y, x1 + o, y1, lw); px, py = x1 + 3.2, y + (y1 - y) * 0.15
        elif sd == "B":
            sh.line(x, y - o, x1, y - o, lw); px, py = x + (x1 - x) * 0.15, y - 3.6
        else:
            sh.line(x, y1 + o, x1, y1 + o, lw); px, py = x1 - (x1 - x) * 0.12, y1 + 3.6
        labels.boxes.append((px - 2.3, py - 2.3, px + 2.3, py + 2.3))     # номера отверстий обходят знак
        sh.circle(px, py, 2.0, dict(lw=0.8, color=RED, ls="-"), fill="white")
        sh.text(px, py, str(e["order"]), size=6, ha="center", va="center", color=RED, weight="bold")
        reg["edges_signed"].add(e["face"])
    own = "О" if mirror else "Л"
    for q in P["holes"]:
        if q["typ"] == "Т":
            continue
        if q["typ"] != "С" and q["typ"] != own and (P["need_two"] or mirror):
            continue                          # на двух изображениях каждое показывает свои глухие отверстия
        cx, cy = Pt(q["u"], q["v"])
        r = max(q["h"]["d"] / 2 / sc, 0.45)
        vis = q["typ"] in ("С", own)
        sh.circle(cx, cy, r, st=VIS if vis else HID)
        sh.cross(cx, cy, r + 0.9)
        labels.put(cx + r * 0.5, cy + r * 0.5, str(q["N"]))
        reg["drawn"].setdefault(q["h"]["id"], set()).add(q["N"])
    for g in P["grooves"]:
        u0, u1 = sorted((U(g["u0"]), U(g["u1"])))
        a, b = (x + u0 / sc, y + g["v0"] / sc), (x + u1 / sc, y + g["v1"] / sc)
        vis = g["face"] == own
        sh.rect(a[0], a[1], b[0], b[1], dict(lw=0.7, color="k", ls="-" if vis else (0, (3, 2))))
        if vis:
            sh.ax.add_patch(Rectangle(a, b[0] - a[0], b[1] - a[1], fill=False, hatch="////", ec="#666", lw=0))
        sh.text(b[0] - 2, (a[1] + b[1]) / 2 + 1.5, f"{g['name']} ({'лиц.' if vis else 'обр.'})", size=5.4, ha="right",
                color="#333")
        reg["grooves_marked"].add(g["name"])
    # текстура
    if P["grain"]:
        gv = vec("+" + P["grain"])
        along_u = abs(dot(gv, fr.right)) == 1
        cx, cy = (x + x1) / 2, y + (y1 - y) * 0.15
        L_ = min(10, (x1 - x) * 0.25) if along_u else min(10, (y1 - y) * 0.25)
        if along_u:
            sh.ax.annotate("", (cx + L_, cy), (cx - L_, cy), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#7a5a2a"))
        else:
            sh.ax.annotate("", (cx, cy + L_), (cx, cy - L_), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#7a5a2a"))
    sh.dim_h(x, x1, y, y, y - 7.5, _n(round(Lu, 1)))
    sh.dim_v(y, y1, x1 if not mirror else x, x1 if not mirror else x, (x1 + 6) if not mirror else (x - 6),
             _n(round(Lv, 1)))
    return (x, y, x1, y1)


def _end_view(sh, P, side, box, sc, reg, labels):
    """Б3: вид с торца side — полоса толщиной t, отверстия торца с номерами (вдоль стороны, от пласти на виде)."""
    fr = P["fr"]
    x, y, x1, y1 = box
    t = fr.t / sc
    hs = [q for q in P["holes"] if q["typ"] == "Т" and q["side"] == side]
    gap = 10
    if side in ("B", "T"):
        yy = y - gap - t if side == "B" else y1 + gap
        sh.rect(x, yy, x1, yy + t, VIS)
        for q in hs:
            cx = x + q["u"] / sc
            cy = yy + (fr.t - q["w"]) / sc if side == "B" else yy + q["w"] / sc
            sh.circle(cx, cy, max(q["h"]["d"] / 2 / sc, 0.4), VIS)
            labels.put(cx, cy, str(q["N"]))
            reg["drawn"].setdefault(q["h"]["id"], set()).add(q["N"])
        sh.text(x1 + 1.5, yy + t / 2, f"торец «{SIDE_RU[side]}»", size=5.2, va="center", color="#333")
    else:
        xx = x - gap - t if side == "L" else x1 + gap
        sh.rect(xx, y, xx + t, y1, VIS)
        for q in hs:
            cy = y + q["v"] / sc
            cx = xx + (fr.t - q["w"]) / sc if side == "L" else xx + q["w"] / sc
            sh.circle(cx, cy, max(q["h"]["d"] / 2 / sc, 0.4), VIS)
            labels.put(cx, cy, str(q["N"]))
            reg["drawn"].setdefault(q["h"]["id"], set()).add(q["N"])
        sh.text(xx + t / 2, y1 + 1.5, f"торец «{SIDE_RU[side]}»", size=5.2, ha="center", va="bottom", color="#333")
    reg["end_drawn"].add(side)


def _groove_section(sh, P, g, x, y):
    """Б5: сечение паза М 2:1 — толщина панели, паз шириной w и глубиной depth на расстоянии from_edge."""
    gg, t = g["g"], P["fr"].t
    k = 1.5
    W = (gg["from_edge"] + gg["w"] + 10) * k
    sh.rect(x, y, x + W, y + t * k, VIS)
    sh.ax.add_patch(Rectangle((x, y), W, t * k, fill=False, hatch="////", ec="#666", lw=0))
    gx0 = x + gg["from_edge"] * k
    gy = y + (t - gg["depth"]) * k if g["face"] == "Л" else y
    sh.ax.add_patch(Rectangle((gx0, gy), gg["w"] * k, gg["depth"] * k, fc="white", ec="k", lw=0.9, zorder=5))
    sh.dim_h(x, gx0, y, y, y - 4, _n(gg["from_edge"]), size=5.6)
    sh.dim_h(gx0, gx0 + gg["w"] * k, y, y, y - 9, _n(gg["w"]), size=5.6)
    sh.dim_v(gy, gy + gg["depth"] * k, x + W, x + W, x + W + 4, _n(gg["depth"]), size=5.6)
    sh.text(x, y + t * k + 2, f"{g['name']} — сечение М 1,5:1 ({'лицевая' if g['face'] == 'Л' else 'обратная'} пласть)",
            size=5.8, weight="bold", va="bottom")


def wtable(sh, x, y, cols, rows, widths, size=5.6, rh=3.9):
    old = Sheet.WRAP
    Sheet.WRAP = True
    yb = sh.table(x, y, cols, rows, widths, row_h=rh, size=size)
    Sheet.WRAP = old
    return yb


WIDE_FROM = 1400        # длинная сторона ≥ 1400: поле чертежа на всю ширину листа, таблица отверстий — на втором листе
MIN_PRINT = 100         # длинная сторона панели ≥ 1000 мм печатается не короче 100 мм (проверка Б12)
LABEL_PT = 6.0          # номера отверстий не мельче 6 pt (разбор 13.11, G4)
HOLE_COLS = ["N", "D", "H", "X", "Y", "Тип", "Изобр."]
HOLE_W = [9, 9, 17, 25, 25, 32, 33]


def hole_rows(P):
    rows = []
    for q in P["holes"]:
        h = q["h"]
        H = "насквозь" if h["through"] else ("разметка" if not h["depth"] else _n(h["depth"]))
        if q["typ"] == "Т":
            X = _n(q["u"] if q["side"] in ("T", "B") else q["v"])
            Y = f"{_n(q['w'])} от пласти"
            img = f"торец {SIDE_RU[q['side']]}"
        else:
            mirror = P["need_two"] and q["typ"] == "О"
            X = _n(round(P["fr"].Lu - q["u"], 1) if mirror else q["u"])
            Y = _n(q["v"])
            img = "2 (обратная)" if mirror else "1 (лицевая)"
        typ = TYPE_RU[q["typ"]]
        if q.get("cs"):                       # разбор 13.11: в A4 «с зенковкой» — значит, и на листе цеха
            from eng.cab import TECH
            typ = f"сквозное + зенк. Ø{_n(TECH['countersink_d'])}"
            img = "1 (лицевая)" if q["cs"] == "Л" else ("2 (обратная)" if P["need_two"] else "с обратной")
        rows.append([str(q["N"]), _n(h["d"]), H, X, Y, typ, img])
    return rows


def n_sheets(s, pid):
    P = panel_data(s, pid)
    n = len(P["holes"])
    if P["wide"]:
        return 1 + -(-n // 104) if n else 1
    return 1 + -(-max(0, n - 52) // 104)


def panel_sheets(c, ps, ids, reg_all, n0):
    """Лист(ы) чертежа панели (Б1–Б8). Возвращает список Sheet; регистр — в reg_all[pid]."""
    from eng.kit13 import MAT_RU, fin_ru, stamp_for
    s = c.s
    pid = ids[0]
    P = panel_data(s, pid)
    p, fr = P["p"], P["fr"]
    reg = dict(pos=ps, P=P, drawn={}, end_drawn=set(), grooves_marked=set(), sections=set(), edges_signed=set(),
               two=False, table=[], ops=[], sheets=0)
    reg_all[pid] = reg
    sh = Sheet(f"Деталь поз. {ps} — {p['unit']}", stamp_for(s), n0, c.total, "по виду")
    sh.text(25, 283, f"Поз. {ps}  {p['unit']} — {len(ids)} шт.   {MAT_RU.get(p['material'], p['material'])} "
            f"{fin_ru(p['finish'])}", size=8.5, weight="bold", va="top")
    sh.text(25, 277, f"Готовый {_n(round(fr.Lu, 1))} × {_n(round(fr.Lv, 1))} × {_n(round(fr.t, 1))} · заготовка "
            f"{_n(P['blank'][0])} × {_n(P['blank'][1])} (− кромка + припуск {_n(TECH['edge_allow'])} на фуговку) [М] · "
            f"размеры {TECH['dims_from']}, база A [М]", size=6.3, va="top")
    sh.text(25, 272.5, f"Порядок: {TECH['op_order']} [М] (БАЗИС с. 38). Вид — лицевая пласть "
            f"(«{NAME[name_of(fr.n)]}»), вверх — «{NAME[name_of(fr.up)]}».", size=6.0, va="top", color="#333")
    sides = sorted({q["side"] for q in P["holes"] if q["typ"] == "Т"})
    two = P["need_two"]
    wide = P["wide"]
    ax0, ax1 = 34, (405 if wide else 250)
    ay0, ay1 = 128, 258
    reg["title_y"] = 265.5
    hgap = 22
    padx = (14 if ("L" in sides) else 0) + (14 if ("R" in sides) else 0) + 8
    pady = (14 if ("B" in sides) else 0) + (14 if ("T" in sides) else 0) + 8
    SC = (1, 2, 2.5, 4, 5, 8, 10, 15, 20, 25, 40, 50)
    fit = lambda aw, ah: next((k for k in SC if fr.Lu / k <= aw and fr.Lv / k <= ah), 50)
    side_by_side = False
    if two:                                      # два изображения: рядом или друг под другом — что крупнее
        sc_v = fit(ax1 - ax0 - padx, (ay1 - ay0 - hgap) / 2 - pady)
        sc_h = fit((ax1 - ax0 - hgap) / 2 - padx, ay1 - ay0 - pady)
        side_by_side = sc_h < sc_v
        sc = min(sc_v, sc_h)
    else:
        sc = fit(ax1 - ax0 - padx, ay1 - ay0 - pady)
    labels = Labels(sh)
    reg["sc"], reg["print_long"] = sc, round(max(fr.Lu, fr.Lv) / sc, 1)
    reg["label_pt"] = labels.size
    x = ax0 + (14 if "L" in sides else 0) + 4
    y_top = ay1 - (14 if "T" in sides else 0)
    y = y_top - fr.Lv / sc
    if two:                                      # подпись изображения 2 — заранее, чтобы номера изобр. 1 её обходили
        t2 = f"Изображение 2 — обратная{'' if side_by_side else ' пласть'} (зеркально), М 1:{_n(sc)}"
        xx = x + fr.Lu / sc + hgap + (14 if "R" in sides else 0) + 14 if side_by_side else x
        t2y = y + fr.Lv / sc if side_by_side else y - hgap - (14 if "B" in sides else 0)
        labels.boxes.append((xx, t2y + 6, xx + len(t2) * 1.3, t2y + 10.5))
    box = _image(sh, P, x, y, sc, False, reg, labels, f"Изображение 1 — лицевая пласть, М 1:{_n(sc)}")
    for sd in sides:
        _end_view(sh, P, sd, box, sc, reg, labels)
    if two:
        if side_by_side:
            x2 = box[2] + hgap + (14 if "R" in sides else 0) + 14
            _image(sh, P, x2, y, sc, True, reg, labels, f"Изображение 2 — обратная (зеркально), М 1:{_n(sc)}")
        else:
            y2 = y - hgap - (14 if "B" in sides else 0) - fr.Lv / sc
            _image(sh, P, x, y2, sc, True, reg, labels, f"Изображение 2 — обратная пласть (зеркально), М 1:{_n(sc)}")
        reg["two"] = True
    ylow = box[1] - (14 if "B" in sides else 0) - 18          # сечение — под изображением 1, слева
    for i, g in enumerate(P["grooves"]):
        gx, gy = box[0] + i * 80, max(ylow - P["fr"].t * 1.5, 126)
        _groove_section(sh, P, g, gx, gy)
        reg["sections"].add(g["name"])
        reg.setdefault("draw_boxes", []).append((gx, gy - 10, gx + (g["g"]["from_edge"] + g["g"]["w"] + 10) * 1.5 + 8,
                                                 gy + P["fr"].t * 1.5 + 5))
    reg.setdefault("draw_boxes", []).append(box)
    # таблица облицовки (Б6) и операций (Б8)
    erows = [[str(e["order"]), NAME[e["face"]], EDGE_TXT[e["typ"]], _n(e["L"])] for e in P["edges"]]
    yb = 120
    if erows:
        sh.text(25, yb, "Облицовка кромок", size=6.6, weight="bold")
        yb = wtable(sh, 25, yb - 2, ["№", "Сторона", "Материал", "Длина"], erows, [9, 30, 22, 18]) - 2
        sh.text(25, yb, "№ = порядок облицовывания: короткие → длинные [М]", size=5.4, va="top", color="#333")
    reg["ops"] = operations(s, P)
    sh.text(110 if erows else 25, 120, "Таблица операций", size=6.6, weight="bold")
    wtable(sh, 110 if erows else 25, 118, ["№", "Операция", "Что", "Кто"], reg["ops"], [7, 26, 72, 15] if erows else
           [7, 30, 120, 18])
    # таблица отверстий (Б4); продолжение — второй лист чертежа
    rows = hole_rows(P)
    reg["table"] = [int(r[0]) for r in rows]
    reg["cs_marked"] = {int(r[0]) for r in rows if "зенк" in r[5]}
    out = [sh]
    per = 52
    chunks = [rows[i:i + per] for i in range(0, len(rows), per)] or [[]]
    legend = ("Тип: сквозное / лицевое (с изобр. 1) / обратное / торцевое; H — глубина. X, Y — от базы A "
              "изображения; у торца X — вдоль торца, Y — от лицевой пласти.\nЗенк. — на пласти, указанной в «Изобр.» "
              "(вход самореза).")
    if wide:                                     # всё поле — под изображение; таблица — на следующем листе чертежа
        sh.text(260, 120, f"Таблица отверстий ({len(rows)}) — лист {n0 + 1:02d}" if rows else "Отверстий нет",
                size=6.6, weight="bold")
        rest = rows
    else:
        sh.text(258, 283, f"Таблица отверстий ({len(rows)})" + (" — начало" if len(chunks) > 1 else ""), size=7,
                weight="bold", va="top")
        if rows:
            wtable(sh, 258, 278, HOLE_COLS, chunks[0], HOLE_W)
            sh.text(258, 66, legend, size=5.2, va="top", color="#333")
        else:
            sh.text(258, 276, "отверстий нет", size=6.5, va="top")
        rest = rows[per:]
    for k, ch in enumerate([rest[i:i + 2 * per] for i in range(0, len(rest), 2 * per)], 2):   # две колонки по 52
        sh2 = Sheet(f"Деталь поз. {ps} — лист {k} чертежа", stamp_for(s), n0 + k - 1, c.total, "—")
        sh2.text(25, 283, f"Поз. {ps}  {p['unit']} — таблица отверстий, лист {k} чертежа (БАЗИС 2.3.10)",
                 size=8, weight="bold", va="top")
        wtable(sh2, 25, 276, HOLE_COLS, ch[:per], HOLE_W)
        if ch[per:]:
            wtable(sh2, 190, 276, HOLE_COLS, ch[per:], HOLE_W)
        sh2.text(25, 62, legend, size=5.6, va="top", color="#333")
        out.append(sh2)
    reg["sheets"] = len(out)
    return out


# ------------------------------------------------------------------ сборочные чертежи узлов (Б9)
def units(s):
    """Узлы для сборочных чертежей: ящики (по одинаковому составу) и столик."""
    from eng.kit13 import positions
    pos, _, hpos = positions(s)
    P = {q["id"]: q for q in s["parts"]}
    out = []
    groups = {}
    for r in s["derived"].get("drawers", []):
        ids = list(r["box"]) + [r["front"]]
        sig = tuple(sorted(pos[i] for i in ids))
        groups.setdefault(sig, []).append((r, ids))
    for sig, lst in groups.items():
        r, ids = lst[0]
        joints = {h["joint"] for h in s["holes"] if h["part"] in ids and h["kind"] != "runner_mark"}
        fast = {}
        for h in s["holes"]:
            if h["joint"] in joints and h.get("fastener") and h["kind"] != "runner_mark":
                fast[h["fastener"]] = fast.get(h["fastener"], 0) + 1
        blum = {k: 1 for k in ("SLIDES", "SLIDE-LOCK", "TIPON-SYNC") if any(hh["id"] == k for hh in s["hardware"])}
        lq = next((hh["qty"] for hh in s["hardware"] if hh["id"] == "LOCK-SCREW"), 0)
        if lq:
            blum["LOCK-SCREW"] = lq // max(1, len(s["derived"]["drawers"]))
        out.append(dict(kind="ящик", name=f"Ящик ({'MOVENTO' if r.get('sys') == 'movento' else 'TANDEM'}) NL {r['NL']}",
                        rec=r, ids=ids, count=len(lst), fast=fast, blum=blum, parts={pos[i]: ids.count(i) for i in ids}))
    ch = [q["id"] for q in s["parts"] if q["id"].startswith("CH-") and q["kind"] == "board"]
    if ch:
        fast = {}
        for h in s["holes"]:
            if h["joint"].startswith("J-CH") and h.get("fastener"):
                fast[h["fastener"]] = fast.get(h["fastener"], 0) + 1
        out.append(dict(kind="столик", name="Пеленальный столик", rec=None, ids=ch, count=1, fast=fast, blum={},
                        parts={pos[i]: 1 for i in ch}))
    return out, pos, hpos


def unit_sheet(c, U, reg_units, n):
    from eng.kit13 import fin_ru, stamp_for
    s = c.s
    P = {q["id"]: q for q in s["parts"]}
    H = {h["id"]: h for h in s["hardware"]}
    pos, hpos = c.pos, c.hpos
    parts = [P[i] for i in U["ids"]]
    X0, X1 = min(q["x0"] for q in parts), max(q["x1"] for q in parts)
    Y0, Y1 = min(q["y0"] for q in parts), max(q["y1"] for q in parts)
    Z0, Z1 = min(q["z0"] for q in parts), max(q["z1"] for q in parts)
    sh = Sheet(f"Сборочный чертёж: {U['name']}", stamp_for(s), n, c.total, "по виду")
    sh.text(25, 283, f"Сборочный чертёж узла «{U['name']}» — {U['count']} шт. в изделии (БАЗИС 2.4.2)", size=8.5,
            weight="bold", va="top")
    sc = next(k for k in (2, 4, 5, 8, 10, 15, 20) if (X1 - X0) / k <= 175 and ((Z1 - Z0) + (Y1 - Y0)) / k <= 170)
    vf = View(sh, sc, (50, 262 - (Z1 - Z0) / sc), (X0, Z0))
    for q in sorted(parts, key=lambda q: -q["y0"]):
        vf.rect(q["x0"], q["z0"], q["x1"], q["z1"], VIS if q["y0"] <= Y0 + 40 else HID)
    sh.text(50, 266, f"Вид спереди, М 1:{_n(sc)}", size=6.6, weight="bold")
    vt = View(sh, sc, (50, 262 - (Z1 - Z0) / sc - 18 - (Y1 - Y0) / sc), (X0, Y0))
    for q in parts:
        vt.rect(q["x0"], q["y0"], q["x1"], q["y1"], VIS)
    sh.text(50, 262 - (Z1 - Z0) / sc - 14, f"Вид сверху, М 1:{_n(sc)} (перед — внизу)", size=6.6, weight="bold")
    a, b = vt.p(X0, Y0), vt.p(X1, Y1)
    sh.dim_h(a[0], b[0], a[1], a[1], a[1] - 7, _n(round(X1 - X0, 1)))
    sh.dim_v(a[1], b[1], a[0], a[0], a[0] - 7, _n(round(Y1 - Y0, 1)))
    # выноски (разбор 13.11, G4): детали левой части — кружки слева, остальные — справа; выноски горизонтальные,
    # на разной высоте (≥ 8 мм) — не пересекаются и не проходят через точки других позиций
    rects = {}
    for q in sorted(parts, key=lambda q: (q["x0"], q["y0"])):
        ps = pos[q["id"]]
        if ps not in rects:
            (u0, v0), (u1, v1) = vt.p(q["x0"], q["y0"]), vt.p(q["x1"], q["y1"])
            rects[ps] = (min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1))
    mid, wv = (a[0] + b[0]) / 2, b[0] - a[0]
    col = {"L": a[0] - 20, "R": b[0] + 14}
    used = {"L": [(a[1] + b[1]) / 2], "R": []}        # слева посередине — число размера глубины
    leaders = []
    for ps, (u0, v0, u1, v1) in sorted(rects.items(), key=lambda t: t[1][3] - t[1][1]):    # тонкие — первыми
        sd = "L" if (u0 + u1) / 2 < mid - 0.25 * wv else "R"
        u = (u0 + u1) / 2 if u1 - u0 < 0.5 * wv else u0 + 0.7 * (u1 - u0)
        vc, hh = (v0 + v1) / 2, (v1 - v0) * 0.4
        cands = sorted({round(vc + k * 0.5, 1) for k in range(-int(hh * 2), int(hh * 2) + 1)} | {vc},
                       key=lambda t: abs(t - vc))
        v = next((t for t in cands if all(abs(t - o) >= 8 for o in used[sd])), vc)
        used[sd].append(v)
        leaders.append((ps, (u, v), sd))
    out_l = []
    for sd in ("L", "R"):                       # кружки — в том же порядке по высоте, что точки, шаг ≥ 8
        prev = None
        for ps, (u, v), _ in sorted([t for t in leaders if t[2] == sd], key=lambda t: -t[1][1]):
            by = v if prev is None else min(v, prev - 8)
            prev = by
            sh.balloon(u, v, col[sd], by, ps)
            out_l.append((ps, (u, v), (col[sd], by)))
    leaders = out_l
    rows = []
    for ps, k in sorted(U["parts"].items()):
        q = next(P[i] for i in U["ids"] if pos[i] == ps)
        d = sorted((q["x1"] - q["x0"], q["y1"] - q["y0"], q["z1"] - q["z0"]), reverse=True)
        rows.append([str(ps), q["unit"], " × ".join(_n(round(v, 1)) for v in d), str(k), str(k * U["count"])])
    for fid, k in sorted(U["fast"].items()):
        rows.append([str(hpos.get(fid, "")), H[fid]["name"] if fid in H else fid, "", str(k), str(k * U["count"])])
    for fid, k in U["blum"].items():
        rows.append([str(hpos[fid]), H[fid]["name"], H[fid]["spec"].split(" (")[0].replace("Blum ", ""), str(k),
                     str(k * U["count"])])
    sh.text(240, 276, "Спецификация узла", size=7.5, weight="bold")
    wtable(sh, 240, 273, ["Поз.", "Наименование", "Размер / артикул", "На 1", f"На {U['count']}"], rows, [11, 58, 52, 13, 15])
    reg_units.append(dict(U=U, rows=rows, leaders=leaders))
    return sh


# ------------------------------------------------------------------ проверки (Б1–Б11)
def _cross(a, b, c, d):
    """Отрезки ab и cd пересекаются во внутренних точках (общий конец — не пересечение)."""
    o = lambda p, q, r: (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = o(c, d, a), o(c, d, b), o(a, b, c), o(a, b, d)
    return d1 * d2 < -1e-9 and d3 * d4 < -1e-9


def leaders_crossing(leaders):
    return [(p1, p2) for i, (p1, a, b) in enumerate(leaders) for p2, c, d in leaders[i + 1:] if _cross(a, b, c, d)]


def verify_bazis(s, bz, sheet_texts, spec_rows):
    """[(проверка, ok, подробности)] — по регистру того, что нарисовано, и по моделям."""
    out = []
    add = lambda n, ok, t: out.append((n, bool(ok), str(t)))
    from eng.kit13 import positions
    _, rep, _ = positions(s)
    boards = [ids[0] for ps, ids in rep if next(q for q in s["parts"] if q["id"] == ids[0])["kind"] == "board"]
    regs = bz["panels"]
    miss = [pid for pid in boards if pid not in regs or regs[pid]["sheets"] < 1]
    add("БАЗИС Б1: чертёж на каждую панель", not miss, f"{len(boards)} панелей" if not miss else miss[:3])
    bad = [pid for pid, r in regs.items() if r["P"]["need_two"] != r["two"]]
    add("БАЗИС Б2: второе изображение — ровно когда глухие отверстия на обеих пластях", not bad,
        f"с двумя изображениями: {sum(r['two'] for r in regs.values())}" if not bad else bad[:3])
    bad = [pid for pid, r in regs.items() if {q["side"] for q in r["P"]["holes"] if q["typ"] == "Т"} - r["end_drawn"]]
    add("БАЗИС Б3: вид с торца для каждой стороны с торцевыми отверстиями", not bad, "есть" if not bad else bad[:3])
    bad = []
    for pid, r in regs.items():
        ids = [q["h"]["id"] for q in r["P"]["holes"]]
        nums = [q["N"] for q in r["P"]["holes"]]
        if r["table"] != nums or any(r["drawn"].get(i) != {n} for i, n in zip(ids, nums)):
            bad.append(pid)
    add("БАЗИС Б4: каждое отверстие пронумеровано на виде, номер = строка таблицы (сквозн. → лиц. → обр. → торц.)",
        not bad, f"{sum(len(r['table']) for r in regs.values())} отверстий" if not bad else bad[:3])
    bad = [f"{pid}: {r['label_pt']} pt" for pid, r in regs.items() if r.get("label_pt", 0) < LABEL_PT]
    bad += [f"{pid}: 1:{_n(r['sc'])}, {r['print_long']} мм" for pid, r in regs.items()
            if max(r["P"]["fr"].Lu, r["P"]["fr"].Lv) >= 1000 and r.get("print_long", 0) < MIN_PRINT]
    add(f"БАЗИС Б12: номера отверстий ≥ {_n(LABEL_PT)} pt; длинная панель печатается ≥ {MIN_PRINT} мм", not bad,
        f"мельче всех: {min(r.get('print_long', 0) for r in regs.values() if max(r['P']['fr'].Lu, r['P']['fr'].Lv) >= 1000)} мм"
        if not bad and any(max(r['P']['fr'].Lu, r['P']['fr'].Lv) >= 1000 for r in regs.values()) else
        ("соблюдено" if not bad else bad[:3]))
    bad = [pid for pid, r in regs.items() if {q["N"] for q in r["P"]["holes"] if q["h"].get("cs")} - r.get("cs_marked", set())]
    ncs = sum(1 for r in regs.values() for q in r["P"]["holes"] if q["h"].get("cs"))
    add("БАЗИС Б4б: зенковка указана в таблице отверстий для каждого отверстия под саморез с потайной головкой",
        not bad, f"{ncs} отверстий с зенковкой" if not bad else bad[:3])
    bad = [pid for pid, r in regs.items() for g in r["P"]["grooves"]
           if g["name"] not in r["grooves_marked"] or g["name"] not in r["sections"]]
    add("БАЗИС Б5: паз обозначен на виде и показан в сечении", not bad,
        f"{sum(len(r['P']['grooves']) for r in regs.values())} пазов" if not bad else bad[:3])
    bad = []
    for pid, r in regs.items():
        es = r["P"]["edges"]
        if {e["face"] for e in es} != r["edges_signed"] or [e["L"] for e in es] != sorted(e["L"] for e in es):
            bad.append(pid)
    add("БАЗИС Б6: знак облицовки на каждой облицованной стороне, порядок короткие → длинные", not bad,
        "соблюдено" if not bad else bad[:3])
    sb = {r[0]: r[5] for r in spec_rows if r[0].isdigit()}
    pair = lambda t: sorted(t.split(" × ")) if t else None       # порядок сторон как у готового размера в строке
    bad = [f"поз. {r['pos']}" for r in regs.values()
           if pair(sb.get(str(r["pos"]))) != pair(f"{_n(r['P']['blank'][0])} × {_n(r['P']['blank'][1])}")]
    add("БАЗИС Б7: заготовка (− кромка + припуск на фуговку) на листе детали = в спецификации", not bad,
        "совпадает" if not bad else bad[:3])
    bad = []
    for pid, r in regs.items():
        ops = {o[1] for o in r["ops"]}
        need = {"раскрой"} | ({"облицовка кромок"} if r["P"]["edges"] else set()) | \
               ({"присадка"} if any(q["h"]["depth"] or q["h"]["through"] for q in r["P"]["holes"]) else set()) | \
               ({"паз"} if r["P"]["grooves"] else set())
        if not need <= ops or any(o[3] not in ("цех", "сборщик") for o in r["ops"]):
            bad.append(pid)
    add("БАЗИС Б8: таблица операций на панель (раскрой, кромка, присадка, паз) с колонкой «кто»", not bad,
        "есть" if not bad else bad[:3])
    us = bz["units"]
    H = {h["id"]: h["qty"] for h in s["hardware"]}
    need_u = (1 if s["derived"].get("drawers") else 0) + (1 if any(q["id"].startswith("CH-") for q in s["parts"]) else 0)
    bad = []
    for u in us:
        U = u["U"]
        for fid, k in list(U["fast"].items()) + list(U["blum"].items()):
            if k * U["count"] > H.get(fid, 0) + 0.01:
                bad.append(f"{U['name']}: {fid} {k}×{U['count']} > {H.get(fid)}")
        for ps, k in U["parts"].items():
            n_model = len(next(ids for p_, ids in rep if p_ == ps))
            if k * U["count"] != n_model:
                bad.append(f"{U['name']}: поз. {ps} {k}×{U['count']} ≠ {n_model}")
    add("БАЗИС Б9: сборочные чертежи узлов (ящики, столик) со спецификацией узла, узел × кол-во ≤ спецификации",
        len({u['U']['kind'] for u in us}) >= need_u and not bad, f"{len(us)} узл." if not bad else bad[:3])
    bad = [f"{u['U']['name']}: поз. {a}–{b_}" for u in us for a, b_ in leaders_crossing(u.get("leaders", []))]
    add("БАЗИС Б9б: выноски позиций на сборочных чертежах не пересекаются", not bad,
        f"{sum(len(u.get('leaders', [])) for u in us)} выносок" if not bad else bad[:3])
    des = designation(s)
    bad = [i + 1 for i, t in enumerate(sheet_texts) if not any(des in x for x in t)]
    spec_ok = any(des in x and s["hash"] in x for t in sheet_texts for x in t)
    add("БАЗИС Б10: обозначение исполнения на всех листах и в спецификации (со снимком)", not bad and spec_ok,
        des if not bad and spec_ok else f"нет на листах {bad[:5]}; в спецификации {'да' if spec_ok else 'нет'}")
    bad = [r["pos"] for r in regs.values() for b in r.get("draw_boxes", [])
           if b[2] > (410 if r["P"]["wide"] else 255) or b[1] < 122]
    add("БАЗИС: изображения и сечения — в поле чертежа (не заходят на таблицы)", not bad, "да" if not bad else bad[:3])
    flat = "".join("".join(t) for t in sheet_texts).replace(" ", "").replace("\n", "")
    short = [h["id"] for h in s["hardware"] if h["spec"].replace(" ", "") not in flat]
    add("БАЗИС Б11б: характеристики покупных изделий — полностью (без обрезки в коде)", not short,
        "все полностью" if not short else short[:3])
    cut = [(i + 1, x[:40]) for i, t in enumerate(sheet_texts) for x in t if x.rstrip().endswith("…")]
    add("БАЗИС Б11: таблицы и тексты без обрезки «…»", not cut, "нет" if not cut else cut[:3])
    return out
