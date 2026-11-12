"""Помечает устаревшие фото: геометрия варианта изменилась после генерации.

    python tools/stale.py            # проверить site_images/index.json и записать stale: true/false
Фото варианта с stale: true на сайте показываются с пометкой «требует обновления» в админке."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa: E402
from eng.stamp import model_hash  # noqa: E402
from eng.catalog import compile as compile_snapshot  # noqa: E402
from eng.core import to_model  # noqa: E402


def main(index_path=ROOT / "site_images" / "index.json"):
    mats = json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))
    prods = {json.loads(f.read_text(encoding="utf-8"))["sku"]: json.loads(f.read_text(encoding="utf-8"))
             for f in (ROOT / "catalog/products").glob("*.json")}
    idx = json.loads(Path(index_path).read_text(encoding="utf-8"))
    stale = []
    for pi in idx["products"]:
        p = prods[pi["sku"]]
        base = {a["key"]: a["base"] for a in p["axes"] if a.get("mode") == "layer"}
        for vk, pv in pi["variants"].items():
            if not pv.get("geometry"):
                continue
            model = to_model(compile_snapshot(pi["sku"], {**pv["values"], **base}))  # текущая ревизия каталога
            now = model_hash(model)
            pv["stale"] = now != pv["geometry"]
            if pv["stale"]:
                stale.append(f"{pi['sku']} {vk}")
    Path(index_path).write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Устаревших вариантов: {len(stale)}")
    for s in stale:
        print("  ", s)
    return stale


if __name__ == "__main__":
    main(*sys.argv[1:])
