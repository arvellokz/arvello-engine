"""Экспорт геометрии всех товаров каталога в один JSON для 3D-просмотрщика.

    python tools/export_3d.py out.json
Каждая комбинация опций -> список деталей [x0,y0,z0,x1,y1,z1, цвет, группа] в мм.
"""
import itertools, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa
from eng.catalog import compile as compile_snapshot  # noqa
from eng.core import bom as eng_bom, to_model  # noqa
from eng.stamp import model_hash  # noqa
from eng.core import matches_builder  # noqa
PRICE_NAMES = {k: v["name"] for k, v in json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))["materials"].items()}

mats = json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))
angles = json.loads((ROOT / "catalog/angles.json").read_text(encoding="utf-8"))
META = {
 "ARV-BED-002": ("Парящая кровать на сварном стальном каркасе, основание утоплено на 200 мм, снизу подсветка.",
                 [("Техкарта «Нимб» (наш расчёт)", "")]),
 "ARV-BED-002W": ("Деревянная версия парящей кровати для цехов без сварки.",
                  [("Ana White — Simple Floating Bed", "https://www.ana-white.com/woodworking-projects/simple-floating-bed-plans-mountain-modern-collection")]),
 "ARV-TBL-003": ("Обеденный стол на двух сварных рамах из трубы 40×40, со связями под столешницей и низкими регулируемыми подпятниками.",
                 [("Ripaton — параметры U-опор", "https://www.ripaton.fr/en/made-to-measure/made-to-measure-inverted-U-shaped-steel-table-leg-authentique-330")]),
 "ARV-KIT-004": ("Линейная кухня без ручек: профиль Gola, колонны до верха шкафов, тёмный низ и светлый верх.",
                 [("Blum Cabinet Configurator", "https://blum.com/nz/en/services/planning-construction-product-selection/cabinet-configurator"),
                  ("Ana White — нижний модуль", "https://www.ana-white.com/woodworking-projects/frameless-kitchen-base-cabinet-universal-template"),
                  ("Ana White — верхний модуль", "https://www.ana-white.com/woodworking-projects/frameless-kitchen-wall-cabinet-universal-template")]),
 "ARV-WRD-004": ("Встроенный шкаф до потолка без ручек, открывание нажатием, фасады сливаются со стеной.",
                 [("Blum Cabinet Configurator", "https://blum.com/nz/en/services/planning-construction-product-selection/cabinet-configurator"),
                  ("Ana White — гардеробная система", "https://www.ana-white.com/woodworking-projects/master-closet-system")]),
 "ARV-WRD-007": ("Прихожая: шкаф до потолка, подвесная скамья на стальных кронштейнах, зеркало с подсветкой.",
                 [("Blum Cabinet Configurator", "https://blum.com/nz/en/services/planning-construction-product-selection/cabinet-configurator")]),
 "ARV-LIV-001": ("ТВ-зона: подвесная тумба с откидными фасадами и стеновая панель (гладкая или с рейками).",
                 [("Blum Cabinet Configurator", "https://blum.com/nz/en/services/planning-construction-product-selection/cabinet-configurator")]),
}
CATS = [("KIT", "Кухни"), ("BED", "Кровати"), ("NST", "Тумбы и комоды"), ("WRD", "Шкафы и прихожие"),
        ("LIV", "Гостиная"), ("TBL", "Столы"), ("BTH", "Ванная"), ("OFF", "Офис")]

def kind_of(rgb):
    rgb = tuple(int(c) for c in rgb)
    if rgb == tuple(mats["colors"]["O"]["rgb"]) or rgb in ((222, 196, 150), (214, 186, 140)):
        return "wood"
    if rgb in (tuple(m["rgb"]) for m in mats["metal"].values()) or rgb in ((120, 124, 130), (168, 170, 174), (34, 34, 36)):
        return "metal"
    if rgb in ((24, 24, 26),):
        return "glass"
    if rgb == (196, 206, 212):
        return "mirror"
    if rgb == (255, 210, 150):
        return "led"
    if rgb == (70, 74, 80):
        return "tinted"
    if rgb in (tuple(mats["fixed"]["mattress"]["rgb"]), tuple(mats["fixed"]["pillow"]["rgb"])) or \
            rgb in (tuple(f["rgb"]) for f in mats["fabric"].values()):
        return "fabric"
    return "matte"

palette, pidx, groups, gidx = [], {}, [], {}
def ci(rgb):
    k = tuple(int(c) for c in rgb)
    if k not in pidx:
        pidx[k] = len(palette); palette.append([*k, kind_of(k)])
    return pidx[k]
def gi(g):
    if g not in gidx:
        gidx[g] = len(groups); groups.append(g)
    return gidx[g]

out = {"palette": palette, "groups": groups, "angles": angles, "cats": CATS, "products": []}
prods = {p["sku"]: p for p in (json.loads(f.read_text(encoding="utf-8")) for f in (ROOT / "catalog/products").glob("*.json"))}
LINE_ORDER = {"Тренд": 0, "STD": 1, "Офис": 2}
ORDER = [s for c, _ in CATS for s in sorted((k for k, p in prods.items() if p["category"] == c),
                                             key=lambda k: (LINE_ORDER.get(prods[k].get("line"), 3), k))]
for sku in ORDER:
    p = prods[sku]
    axes = []
    for a in p["axes"]:
        vals = a.get("site_values", a["values"])
        labels = dict(a.get("labels", {}))
        for v in vals:
            labels.setdefault(str(v), f"{v / 10:.0f} см" if isinstance(v, int) else str(v))
        axes.append({"key": a["key"], "label": a["label"], "values": vals, "labels": labels})
    if p.get("builder", "").startswith("floating_bed"):
        axes.append({"key": "view", "label": "Вид", "values": ["full", "skeleton"],
                     "labels": {"full": "изделие", "skeleton": "только каркас"}})
    variants = {}
    for combo in itertools.product(*[a["values"] for a in axes]):
        v = {a["key"]: val for a, val in zip(axes, combo)}
        bmodel, facts = BUILDERS[p["builder"]](v, mats) if p.get("builder") in BUILDERS else (None, {})
        snap = compile_snapshot(sku, v)                      # единый снимок: 3D, чертёж, спецификация
        model = to_model(snap)
        if snap["rev"] == "R00":                             # R01E+ — геометрия рабочих чертежей, не построителя
            assert matches_builder(model, bmodel)[0], f"{sku} {v}: 3D и снимок разошлись"
        b = eng_bom(snap)
        eng = {"rev": snap["rev"], "st": snap["rev_status"], "h": snap["hash"],
               "bom": [[r["unit"], PRICE_NAMES.get(r["material"], r["material"] or "—"), r["size"], r["qty"]] for r in b["made"]],
               "buy": [[h["name"], h["qty"], h.get("uom", "шт")] for h in b["buy"]],
               "sheets": sum(x["sheets"] for x in b["sheets"]), "warn": snap["warnings"][:4]}
        parts = [[round(q.x0), round(q.y0), round(q.z0), round(q.x1), round(q.y1), round(q.z1), ci(q.color), gi(q.group)]
                 for q in model.parts]
        glows = [[round(g.x0), round(g.y0), round(g.x1), round(g.y1), ci(g.color), round(g.blur_mm)] for g in model.glows]
        key = "|".join(str(x) for x in combo)
        variants[key] = {"parts": parts, "glows": glows, "checks": snap.get("model_checks") or getattr(bmodel, "checks", []),
                         "wall": snap.get("wall_y") or getattr(bmodel, "wall_y", None), "eng": eng}
    ref_axes = [{"key": a["key"], "values": a["values"]} for a in p["axes"] if a.get("mode", "frame") == "frame"]
    ref_fixed = {a["key"]: a["base"] for a in p["axes"] if a.get("mode") == "layer"}
    if p.get("builder", "").startswith("floating_bed"):
        ref_fixed["view"] = "full"
    desc, src = META.get(sku, (p.get("desc", ""), p.get("sources", [])))
    out["products"].append({"sku": sku, "name": p["name"], "category": p["category"], "line": p.get("line", ""),
                            "desc": desc, "sources": src, "en": p["product_en"], "cam_flip": bool(p.get("cam_flip")),
                            "ref": {"axes": ref_axes, "fixed": ref_fixed, "angles": p.get("angles", [])},
                            "axes": axes, "variants": variants})
Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("variants:", sum(len(x["variants"]) for x in out["products"]), "size KB:", Path(sys.argv[1]).stat().st_size // 1024)
