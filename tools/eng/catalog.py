"""Единая точка входа: любой товар каталога + опции -> снимок конфигурации.

«Опора» (ARV-TBL-003) и тумба «Самал» (ARV-NST-001) — собственные инженерные ядра (eng/opora.py, eng/samal.py),
ревизия из catalog/revisions.json.
Остальные модели — eng/generic.py (каталожная геометрия, оценка по 3D)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import generic, opora, samal
from .core import snapshot
from .revisions import catalog_rev

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def products():
    out = {}
    for f in sorted((ROOT / "catalog/products").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        out[p["sku"]] = p
    return out


@lru_cache(maxsize=1)
def materials():
    return json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))


def default_options(sku):
    p = products()[sku]
    o = {}
    for a in p["axes"]:
        o[a["key"]] = a["base"] if a.get("mode") == "layer" else a["values"][0]
    o.update(p.get("lifestyle_only", {}))
    if p.get("builder", "").startswith("floating_bed"):
        o["view"] = "full"            # в 3D-каталоге у парящих кроватей есть ось «изделие / только каркас»
    return o


def compile(sku, options=None, rev=None):
    """Снимок конфигурации товара. options — значения осей товара (как в 3D-каталоге)."""
    from builders import BUILDERS
    o = {**default_options(sku), **(options or {})}
    if sku == opora.SKU:
        d = opora.build({k: o[k] for k in ("size", "top", "metal")}, rev or catalog_rev(sku))
        pal = opora.palette(materials())
        for q in d.parts:                      # цвет для 3D хранится в снимке, как у остальных моделей
            q.rgb = tuple(int(c) for c in pal({"group": q.group, "finish": q.finish}))
        s = snapshot(d)
        s["product"] = products()[sku]["name"]
        return s
    if sku == samal.SKU:
        d = samal.build({"color": o["color"]}, rev or catalog_rev(sku))
        pal = samal.palette(materials())
        for q in d.parts:
            q.rgb = tuple(int(c) for c in pal({"finish": q.finish}))
        s = snapshot(d)
        s["product"] = products()[sku]["name"]
        s["model_checks"], s["wall_y"] = [], samal.D
        return s
    r = rev or catalog_rev(sku)
    if r == "R01E":
        return _from_kit(sku, o, BUILDERS)
    d = generic.build(products()[sku], o, BUILDERS, materials())
    s = snapshot(d)
    s["product"] = products()[sku]["name"]
    s["model_checks"], s["wall_y"] = d.model_checks, d.wall_y
    return s


# Детали, которые в режиме «только каркас» (ось view у парящих кроватей) не показываются.
SKELETON_HIDE = {"ARV-BED-002": {"carcass", "headboard", "bedding"}, "ARV-BED-002W": {"bedding"}}


def _from_kit(sku, o, BUILDERS):
    """Ревизия R01E: геометрия рабочего комплекта (tools/eng/kit13.make) — та же, что на чертежах цеха.
    Подсветка (glow) — только картинка для 3D и фото, в конструкции её нет: берётся из каталожного построителя."""
    from . import kit13
    s = kit13.make(sku, o)
    if o.get("view") == "skeleton":
        hide = SKELETON_HIDE.get(sku, {"bedding"})
        s["parts"] = [p for p in s["parts"] if p["group"] not in hide and p["kind"] != "context"]
    p = products()[sku]
    if p.get("builder") not in BUILDERS:      # новая модель без каталожного построителя: вид = геометрия комплекта
        s["model_checks"], s["wall_y"] = [], None
        return s
    bm, _ = BUILDERS[p["builder"]](o, materials())
    _visual(sku, s, bm)
    if bm.glows and o.get("view") != "skeleton":
        s["glows"] = [[g.x0, g.y0, g.x1, g.y1, list(g.color), g.blur_mm] for g in bm.glows]
    s["model_checks"], s["wall_y"] = getattr(bm, "checks", []), getattr(bm, "wall_y", None)
    return s


# ---- визуальный слой каталога (3D и фото). Конструкцию и спецификацию не меняет:
# предметы окружения (подушки, ТВ, смеситель, вещи на полках) и материалы стекла/зеркала для рендера.
CONTEXT_FROM_BUILDER = {
    "ARV-BTH-001": ("faucet", "spout"),
    "ARV-LIV-001": ("tv",),
    "ARV-WRD-005": ("obj0", "obj1", "obj2", "obj3"),
    "ARV-BED-003": ("sconce0l", "sconce1l"),
}
GLASS_RGB, MIRROR_RGB, TINTED_RGB = (24, 24, 26), (196, 206, 212), (70, 74, 80)


def _ctx_part(pid, name, q, group, rgb, dz=0.0):
    return {"id": pid, "name": name, "x0": q.x0, "y0": q.y0, "z0": q.z0 + dz, "x1": q.x1, "y1": q.y1, "z1": q.z1 + dz,
            "group": group, "kind": "context", "unit": None, "material": None, "finish": "context", "rgb": list(rgb)}


def _visual(sku, s, bm):
    mats = materials()
    B = {q.name: q for q in bm.parts}
    parts = s["parts"]
    for q in parts:
        nm = q["name"]
        if q.get("material") == "APPL" and q["finish"] == "black":
            q["rgb"] = list(GLASS_RGB)                    # стекло варочной панели / духовки
        elif nm.startswith("Беспроводная зарядка"):
            q["rgb"] = list(GLASS_RGB)
        elif nm.startswith("Зеркало"):
            q["rgb"] = list(MIRROR_RGB)
    # канавки рифления — тёмный оттенок своей панели (в 3D/фото), а не общий «коричневый»
    for g in [q for q in parts if q.get("finish") == "groove"]:
        host = next((q for q in parts if q is not g and q.get("finish") != "groove" and q["kind"] != "context"
                     and q["x0"] <= g["x0"] and q["x1"] >= g["x1"] and q["z0"] <= g["z0"] and q["z1"] >= g["z1"]
                     and q["y0"] <= g["y1"] and q["y1"] >= g["y0"]), None)
        if host is not None:
            g["rgb"] = [int(c * 0.62) for c in host["rgb"]]
    # кровати: матрас — цвет матраса, подушки из каталожной модели, поставленные на матрас комплекта
    mat = next((q for q in parts if q["group"] == "bedding" and q["kind"] == "context"), None)
    if mat is not None:
        mat["rgb"] = list(mats["fixed"]["mattress"]["rgb"])
        bmat = B.get("mattress")
        for name, q in B.items():
            if name.startswith("pillow") and bmat is not None:
                parts.append(_ctx_part(f"CTX-{name}", "Подушка (не входит)", q, "bedding",
                                       mats["fixed"]["pillow"]["rgb"], dz=mat["z1"] - bmat.z1))
    for name in CONTEXT_FROM_BUILDER.get(sku, ()):
        if name in B:
            q = B[name]
            parts.append(_ctx_part(f"CTX-{name}", f"Окружение: {name}", q, q.group, tuple(int(c) for c in q.color)))
    # стеклянные двери в рамке: в 3D — рамка + тонированное стекло из каталожной модели
    glass = [q for q in parts if "стеклян" in q["name"].lower() and q["group"] == "fronts"]
    for g in glass:
        inside = [q for q in bm.parts if q.group == "fronts" and q.x0 >= g["x0"] - 5 and q.x1 <= g["x1"] + 5
                  and q.z0 >= g["z0"] - 5 and q.z1 <= g["z1"] + 5]
        if inside:
            parts.remove(g)
            for q in inside:
                d = _ctx_part(f"{g['id']}~{q.name}", g["name"], q, "fronts", tuple(int(c) for c in q.color))
                d["kind"], d["finish"] = "visual", g["finish"]
                parts.append(d)
