"""Инженерное ядро Arvello: снимок конфигурации -> 3D, чертёж, спецификация, раскрой, затраты.

Один снимок (snapshot) = изделие + ревизия конструкции + выбранные опции + рассчитанные детали.
Всё остальное (3D, 2D-чертёж, спецификация, раскрой, состав затрат, геометрия для фото)
строится только из снимка. Цены хранятся отдельно (catalog/prices.json) и в хеш не входят.

Виды деталей (EPart.kind):
  board — плита (ЛДСП, МДФ, ХДФ, столешница, камень); tube — профильная труба; timber — брус;
  plate — стальной лист/пластина; cap — заглушка; glass — стекло/зеркало; upholstery — мягкая панель;
  volume — объём без деталировки (цоколь, внутренний ящик): в спецификации есть, в материалы не считается;
  buy — покупное, показанное в 3D (ручка, профиль, подпятник); buy_part — часть покупного (ножка ручки);
  context — не входит в изделие (матрас, техника, декор для фото).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field

SCHEMA = "arvello.snapshot/2"
SHEET = (2800, 2070)          # формат плиты для раскроя (ЛДСП/МДФ/ХДФ), мм
SHEET_TRIM, SHEET_KERF = 10, 4


@dataclass
class EPart:
    """Деталь изделия. Геометрия — параллелепипед в мм: x — ширина/длина, y — глубина (перед y=0), z — высота."""
    id: str
    name: str
    kind: str
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float
    material: str          # ключ материала из prices.json
    finish: str = ""       # декор/покрытие: O, W, black, …
    group: str = ""        # группа для 3D: top, base, carcass, fronts …
    axis: str = ""         # для труб и бруса — ось длины (x|y|z)
    unit: str = ""         # наименование строки спецификации
    note: str = ""
    rgb: tuple = ()        # цвет для 3D (если пусто — по палитре изделия)
    bom_size: tuple = ()   # размер для спецификации, если отличается от габарита 3D (цоколь-планка)
    edge_m: float = 0.0    # кромка, м

    @property
    def size(self):
        return (round(self.x1 - self.x0, 3), round(self.y1 - self.y0, 3), round(self.z1 - self.z0, 3))

    @property
    def length(self):
        return self.size["xyz".index(self.axis)]


@dataclass
class Hardware:
    id: str
    name: str
    spec: str
    qty: float
    status: str = "кандидат"
    note: str = ""
    uom: str = "шт"


@dataclass
class Design:
    sku: str
    rev: str
    rev_status: str
    options: dict
    derived: dict
    parts: list
    hardware: list = field(default_factory=list)
    ops: dict = field(default_factory=dict)
    checks: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    holes: list = field(default_factory=list)
    blockers: list = field(default_factory=list)
    glows: list = field(default_factory=list)      # подсветка пола для 3D: [x0, y0, x1, y1, rgb, blur]


def snapshot(d: Design) -> dict:
    body = {
        "schema": SCHEMA, "sku": d.sku, "rev": d.rev, "rev_status": d.rev_status, "options": d.options,
        "derived": d.derived, "parts": [asdict(p) for p in d.parts], "hardware": [asdict(h) for h in d.hardware],
        "ops": d.ops, "holes": d.holes, "glows": d.glows,
    }
    canon = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    body["hash"] = hashlib.sha256(canon.encode()).hexdigest()[:16]
    body["checks"] = [{"name": n, "expected": e, "actual": a, "ok": e == a} for n, e, a in d.checks]
    body["notes"] = d.notes
    body["warnings"] = d.warnings
    body["blockers"] = d.blockers
    body["manufacturing_allowed"] = False
    return body


# ------------------------------------------------------------------ спецификация и раскрой

MADE = ("board", "tube", "timber", "plate", "cap", "glass", "upholstery", "volume")


def _dims(p):
    return (round(p["x1"] - p["x0"], 1), round(p["y1"] - p["y0"], 1), round(p["z1"] - p["z0"], 1))


def part_row(p):
    """Ключ, размер и количество материала одной детали (используют bom, раскрой и затраты)."""
    d = _dims(p)
    k = p["kind"]
    if k in ("tube", "timber"):
        L = d["xyz".index(p["axis"])]
        return (k, p["unit"], p["material"], p["finish"], L), f"L = {L:g}", L / 1000
    a, b, t = sorted(p.get("bom_size") or d, reverse=True)
    if k in ("plate", "cap"):
        return (k, p["unit"], p["material"], p["finish"], a, b, t), f"{a:g} × {b:g} × {t:g}", a * b * t / 1e9 * 7850
    return (k, p["unit"], p["material"], p["finish"], a, b, t), f"{a:g} × {b:g} × {t:g}", a * b / 1e6


def bom(snap: dict) -> dict:
    rows = {}
    for p in snap["parts"]:
        if p["kind"] not in MADE:
            continue
        key, size, q = part_row(p)
        r = rows.setdefault(key, {"unit": p["unit"], "kind": p["kind"], "material": p["material"], "finish": p["finish"],
                                  "size": size, "qty": 0, "ids": [], "amount": 0.0,
                                  "length": key[4] if p["kind"] in ("tube", "timber") else None,
                                  "edge_m": 0.0})
        r["qty"] += 1
        r["ids"].append(p["id"])
        r["amount"] += q
        r["edge_m"] += p.get("edge_m", 0)
    made = sorted(rows.values(), key=lambda r: (MADE.index(r["kind"]), r["material"], r["unit"]))
    net = sum(r["length"] * r["qty"] for r in made if r["kind"] == "tube")
    return {"made": made, "buy": snap["hardware"], "tube_net_mm": net, "sheets": sheet_plan(snap)}


def sheet_plan(snap: dict):
    """Раскрой плит по листам SHEET (полосами, с поворотом детали; для декора с рисунком без поворота).
    Оценка числа листов; деталь больше листа — отдельная пометка (нужен стык или другой формат)."""
    groups = {}
    for p in snap["parts"]:
        if p["kind"] != "board" or p["material"].startswith(("TOP", "STONE", "BEAM", "PINE")):
            continue
        a, b, _ = sorted(p.get("bom_size") or _dims(p), reverse=True)
        groups.setdefault((p["material"], p["finish"]), []).append((a, b, p["id"]))
    fmt = snap["derived"].get("supplier", {}).get("sheet", {})    # формат листа поставщика (ENG-005: 2750 × 1830)
    ext = snap["derived"].get("parts_ext", {})
    out = []
    for (mat, fin), items in sorted(groups.items()):
        SW, SH = fmt.get(mat, SHEET)
        W, H = SW - 2 * SHEET_TRIM, SH - 2 * SHEET_TRIM
        grain = fin == "O" or any(ext.get(pid, {}).get("grain") for _, _, pid in items)   # рисунок — без поворота
        over, fit = [], []
        for a, b, pid in items:
            if (a <= W and b <= H) or (not grain and b <= W and a <= H):
                fit.append((a, b, pid))
            else:
                over.append(pid)
        sheets, rows_left = [], None
        for a, b, pid in sorted(fit, key=lambda x: (-x[1], -x[0])):   # полосы по высоте b
            placed = False
            for sh in sheets:
                for row in sh["rows"]:
                    if row["h"] >= b and row["used"] + a + SHEET_KERF <= W:
                        row["used"] += a + SHEET_KERF; placed = True; break
                if placed:
                    break
                if sh["h_used"] + b + SHEET_KERF <= H:
                    sh["rows"].append({"h": b, "used": a + SHEET_KERF}); sh["h_used"] += b + SHEET_KERF
                    placed = True; break
            if not placed:
                sheets.append({"rows": [{"h": b, "used": a + SHEET_KERF}], "h_used": b + SHEET_KERF})
        area = sum(a * b for a, b, _ in fit) / 1e6
        n = len(sheets)
        out.append({"material": mat, "finish": fin, "parts": len(items), "sheets": n, "area_m2": round(area, 3),
                    "use": round(area / (n * SW * SH / 1e6), 2) if n else 0, "oversize": over, "format": (SW, SH)})
    return out


def cut_plan(lengths, stock=6000, kerf=3, trim=10):
    """Раскрой труб: first-fit-decreasing, пропил на деталь, торцовка с двух концов хлыста."""
    usable = stock - 2 * trim
    bars = []
    for L in sorted(lengths, reverse=True):
        for b in bars:
            if b["used"] + L + kerf <= usable:
                b["pieces"].append(L); b["used"] += L + kerf
                break
        else:
            bars.append({"pieces": [L], "used": L + kerf})
    for b in bars:
        b["rest"] = round(usable - b["used"], 1)
    return bars


def tube_lengths(snap: dict, material=None):
    return [round(_dims(p)["xyz".index(p["axis"])], 1) for p in snap["parts"]
            if p["kind"] == "tube" and (material is None or p["material"] == material)]


# ------------------------------------------------------------------ затраты

def cost(snap: dict, prices: dict) -> dict:
    """Себестоимость = материалы (расход × (1 + отход)) + покупные + операции + логистика + резерв;
    цена = себестоимость / (1 − маржа), вверх до 1000 ₸. Количества — из снимка, цены — из prices."""
    b = bom(snap)
    lines, missing = [], []

    def add(group, name, qty, unit, price, waste=0.0):
        lines.append({"group": group, "name": name, "qty": round(qty, 3), "unit": unit,
                      "waste": waste, "price": price, "sum": round(qty * (1 + waste) * price)})

    M = prices["materials"]
    agg = {}
    for r in b["made"]:
        if r["kind"] == "volume":
            missing.append(f"{r['unit']} ×{r['qty']}: деталировка не выполнена, в стоимость не входит")
            continue
        agg.setdefault(r["material"], 0.0)
        agg[r["material"]] += r["amount"]
    for mat, q in agg.items():
        m = M.get(mat)
        if not m:
            missing.append(f"нет цены материала {mat}")
            continue
        add("Материалы", m["name"], q, m["unit"], m["price"], m.get("waste", 0))
    H = prices["hardware"]
    for h in b["buy"]:
        if h["id"] not in H:
            missing.append(f"нет цены: {h['name']}")
            continue
        add("Покупные", h["name"], h["qty"], h.get("uom", "шт"), H[h["id"]]["price"])
    O = prices["operations"]
    for k, q in snap["ops"].items():
        if q and k not in O:
            missing.append(f"нет цены операции {k}")   # раньше — KeyError, расчёт прерывался
        elif q:
            add("Операции", O[k]["name"], q, O[k]["unit"], O[k]["price"])
    add("Логистика", "Доставка деталей и изделия", 1, "заказ", prices["logistics"]["per_order"])
    subtotal = sum(l["sum"] for l in lines)
    reserve = round(subtotal * prices["reserve"])
    cost_total = subtotal + reserve
    price = math.ceil(cost_total / (1 - prices["margin"]) / 1000) * 1000
    return {"lines": lines, "subtotal": subtotal, "reserve": reserve, "cost": cost_total, "margin": prices["margin"],
            "price": price, "prices_status": prices.get("_status", ""), "missing": missing}


# ------------------------------------------------------------------ 3D

def to_model(snap: dict, palette=None):
    """Снимок -> модель для рендера/3D (та же геометрия, что в чертеже и спецификации)."""
    from render import Glow, Model, Part
    P = [Part(p["id"], p["x0"], p["y0"], p["z0"], p["x1"], p["y1"], p["z1"],
              tuple(p["rgb"]) if p.get("rgb") else tuple(palette(p)), p["group"]) for p in snap["parts"]]
    G = [Glow(g[0], g[1], g[2], g[3], tuple(g[4]), g[5]) for g in snap.get("glows", [])]
    return Model(P, G)


def matches_builder(model, bmodel, tol=0.01):
    """3D из снимка ↔ исходная модель конструктора: те же детали и цвета; каждая деталь снимка лежит внутри
    своей детали конструктора (снимок может только укоротить деталь у стыка). Возвращает (ok, число укороченных)."""
    a, b = model.parts, bmodel.parts
    if len(a) != len(b):
        return False, 0
    trimmed = 0
    for p, q in zip(a, b):
        if p.name != q.name or tuple(p.color) != tuple(q.color) or p.group != q.group:
            return False, trimmed
        lo = all(getattr(p, k + "0") >= getattr(q, k + "0") - tol for k in "xyz")
        hi = all(getattr(p, k + "1") <= getattr(q, k + "1") + tol for k in "xyz")
        if not (lo and hi):
            return False, trimmed
        if any(abs(getattr(p, k) - getattr(q, k)) > tol for k in ("x0", "y0", "z0", "x1", "y1", "z1")):
            trimmed += 1
    return True, trimmed
