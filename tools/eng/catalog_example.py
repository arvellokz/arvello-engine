"""Сквозной пример по всему каталогу: для каждой модели одна конфигурация ->
снимок, 3D, чертёж PDF, спецификация, раскрой, затраты, проверки совпадения.

    python tools/eng/catalog_example.py OUT_DIR
OUT_DIR/drawings/<SKU>.pdf, OUT_DIR/sheets/<SKU>-1.png и -2.png, OUT_DIR/catalog-e2e.json, OUT_DIR/summary.csv."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa: E402
from eng.catalog import compile, default_options, materials, products  # noqa: E402
from eng.core import MADE, bom, cost, part_row, to_model  # noqa: E402
from eng.drawing import fin_name, mat_name, write_pdf  # noqa: E402
from eng.stamp import model_hash  # noqa: E402
from eng.core import matches_builder  # noqa: E402

def _kit_opora():
    from eng import kit_opora
    return kit_opora


def _kit_samal():
    from eng import kit_samal
    return kit_samal


KITS = {"ARV-TBL-003": _kit_opora, "ARV-NST-001": _kit_samal}

CATS = [("KIT", "Кухни"), ("BED", "Кровати"), ("NST", "Тумбы и комоды"), ("WRD", "Шкафы и прихожие"),
        ("LIV", "Гостиная"), ("TBL", "Столы"), ("BTH", "Ванная"), ("OFF", "Офис")]


def checks_for(sku, opts, s, b, c, n_pages, cat3d):
    p = products()[sku]
    bm, _ = BUILDERS[p["builder"]](opts, materials())
    m = to_model(s)
    made_ids = sorted(x["id"] for x in s["parts"] if x["kind"] in MADE)
    bom_ids = sorted(i for r in b["made"] for i in r["ids"])
    mat_from_parts = {}
    for x in s["parts"]:
        if x["kind"] in MADE and x["kind"] != "volume":
            mat_from_parts[x["material"]] = mat_from_parts.get(x["material"], 0) + part_row(x)[2]
    names = {k: v["name"] for k, v in json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))["materials"].items()}
    cost_amount = {l["name"]: l["qty"] for l in c["lines"] if l["group"] == "Материалы"}
    mat_ok = all(abs(cost_amount.get(names[k], -1) - round(v, 3)) < 1e-6 for k, v in mat_from_parts.items() if k in names)
    v3 = None
    if cat3d:
        prod3 = next(x for x in cat3d["products"] if x["sku"] == sku)
        key = "|".join(str(opts.get(a["key"], "full")) for a in prod3["axes"])
        v3 = prod3["variants"].get(key, {}).get("eng", {}).get("h")
    return [
        ("3D ↔ снимок", matches_builder(m, bm)[0], f"{len(s['parts'])} деталей, укорочено у стыков: {matches_builder(m, bm)[1]}; 3D строится из снимка"),
        ("3D-каталог показывает этот снимок", v3 == s["hash"], f"вариант в каталоге: {v3}"),
        ("Спецификация ↔ детали", made_ids == bom_ids, f"{len(made_ids)} деталей, каждая учтена один раз"),
        ("Затраты ↔ спецификация", mat_ok, "расход материалов в затратах = сумме по деталям"),
        ("Чертёж из снимка", n_pages >= 3, f"{n_pages} листов, снимок {s['hash']}"),
    ]


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "drawings").mkdir(exist_ok=True); (out / "sheets").mkdir(exist_ok=True)
    prices = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))
    cat3d_path = Path("/home/claude/viewer/catalog3d.json")
    cat3d = json.loads(cat3d_path.read_text(encoding="utf-8")) if cat3d_path.exists() else None
    items, rows = [], []
    order = sorted(products(), key=lambda k: ([c for c, _ in CATS].index(products()[k]["category"]), k))
    for sku in order:
        p = products()[sku]
        opts = default_options(sku)
        s = compile(sku, opts)
        b, c = bom(s), cost(s, prices)
        pdf = out / "drawings" / f"{sku}.pdf"
        kit_checks = None
        if sku in KITS:                     # рабочий комплект по шаблону (Опора, Самал)
            mod = KITS[sku]()
            r = mod.build_and_verify(str(pdf), opts)
            kit_checks = r[1]
            if len(r) > 2:
                import matplotlib.pyplot as plt
                for fig in r[2]:
                    plt.close(fig)
            n_pages = mod.TOTAL
        else:
            n_pages = write_pdf(s, pdf)
        subprocess.run(["pdftoppm", "-r", "90", "-png", str(pdf), str(out / "sheets" / sku)], check=True)
        for f in (out / "sheets").glob(f"{sku}-*.png"):
            f.rename(out / "sheets" / f"{sku}-{int(f.stem.split('-')[-1])}.png")
        chk = checks_for(sku, opts, s, b, c, n_pages, cat3d)
        if kit_checks is not None:
            bad = [n for n, ok, _ in kit_checks if not ok]
            chk.append(("Рабочий комплект: проверки листа 7 задания", not bad,
                        f"{len(kit_checks) - len(bad)} из {len(kit_checks)}" + (f"; не пройдено: {bad}" if bad else "")))
        d = s["derived"]
        dims = (f"{d['length']} × {d['width']} × {d['height']}" if "length" in d else f"{d['width']} × {d['depth']} × {d['height']}")
        items.append({
            "sku": sku, "name": p["name"], "cat": p["category"], "line": p.get("line", ""), "opts": opts,
            "rev": s["rev"], "status": s["rev_status"], "hash": s["hash"], "dims": dims, "pages": n_pages,
            "warn": s["warnings"],
            "parts3d": [[x["id"], x["x0"], x["y0"], x["z0"], x["x1"], x["y1"], x["z1"],
                         "#%02x%02x%02x" % tuple(x["rgb"]), x["kind"]] for x in s["parts"] if x["kind"] != "buy_part"],
            "bom": [[r["unit"], mat_name(r["material"]), fin_name(r["finish"]), r["size"], r["qty"]] for r in b["made"]],
            "buy": [[h["name"], h["spec"], h["qty"], h.get("uom", "шт"), h["status"]] for h in b["buy"]],
            "sheets": [[mat_name(x["material"]), fin_name(x["finish"]), x["parts"], x["sheets"], x["use"], x["oversize"]]
                       for x in b["sheets"]],
            "cost": {"lines": [[l["group"], l["name"], l["qty"], l["unit"], l["price"], l["waste"], l["sum"]] for l in c["lines"]],
                     "reserve": c["reserve"], "cost": c["cost"], "price": c["price"], "margin": c["margin"],
                     "missing": c["missing"]},
            "checks": [[n, ok, t] for n, ok, t in chk],
            "rules": [[x["name"], x["ok"]] for x in s["checks"]],
        })
        rows.append([sku, p["name"], s["rev"], s["hash"], dims, len([x for x in s["parts"] if x["kind"] in MADE]),
                     sum(x["sheets"] for x in b["sheets"]), c["cost"], c["price"], n_pages, all(ok for _, ok, _ in chk)])
    n_var = sum(len(x["variants"]) for x in cat3d["products"]) if cat3d else None
    meta = {"prices_status": prices["_status"], "cats": CATS, "variants": n_var}
    data = json.dumps({"meta": meta, "items": items}, ensure_ascii=False, separators=(",", ":"))
    (out / "catalog-e2e.json").write_text(data, encoding="utf-8")
    tpl = (Path(__file__).parent / "catalog_template.html").read_text(encoding="utf-8")
    (out / "catalog-e2e.html").write_text(tpl.replace("__DATA__", data.replace("</", "<\\/")), encoding="utf-8")
    with open(out / "summary.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["sku", "name", "rev", "snapshot", "dims", "parts", "sheets", "cost", "price_example", "pdf_pages", "all_checks_ok"])
        w.writerows(rows)
    return items


if __name__ == "__main__":
    items = main(Path(sys.argv[1]))
    bad = [i["sku"] for i in items if not all(c[1] for c in i["checks"])]
    print(f"моделей: {len(items)} · листов PDF: {sum(i['pages'] for i in items)} · с расхождениями: {bad or 'нет'}")
