"""Проверки всего каталога: python tools/eng/test_catalog.py
Каждый из 610 вариантов 3D-каталога: снимок = 3D (отпечаток), спецификация учитывает каждую деталь один раз,
затраты считают тот же расход, отрицательных и пустых размеров нет, всё покупное и все материалы имеют цену."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa: E402
from eng.catalog import compile, materials, products  # noqa: E402
from eng.core import MADE, bom, cost, part_row, to_model  # noqa: E402
from eng.stamp import model_hash  # noqa: E402
from eng.core import matches_builder  # noqa: E402

PRICES = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))


def variants(p):
    axes = [(a["key"], a.get("site_values", a["values"])) for a in p["axes"]]
    if p.get("builder", "").startswith("floating_bed"):
        axes.append(("view", ["full", "skeleton"]))
    for combo in itertools.product(*[v for _, v in axes]):
        yield {k: v for (k, _), v in zip(axes, combo)}


def test_all_variants():
    """Техническая корректность всех вариантов (E-03, E-04, E-05) — без цен. Все нарушения собираются,
    не прерываясь на первом. Цены проверяются отдельно: test_prices_commercial (E-06)."""
    from check_catalog import technical
    r = technical()
    assert not r["failures"], r["failures"][:5]
    return r["variants"]


def test_prices_commercial():
    """E-06 — коммерческая готовность. Ожидаемо красная, пока прайс — пример и есть пропуски.
    Не отключать и не маскировать; отчёт: python tools/eng/check_catalog.py commercial."""
    from check_catalog import commercial
    r = commercial()
    assert not r["failures"], (len(r["failures"]), r["models_with_missing_price"])


def test_material_amounts_match_cost():
    names = {k: v["name"] for k, v in PRICES["materials"].items()}
    for sku in products():
        s = compile(sku)
        amounts = {}
        for x in s["parts"]:
            if x["kind"] in MADE and x["kind"] != "volume":
                amounts[x["material"]] = amounts.get(x["material"], 0) + part_row(x)[2]
        got = {l["name"]: l["qty"] for l in cost(s, PRICES)["lines"] if l["group"] == "Материалы"}
        for k, v in amounts.items():
            if k not in names:      # материал без цены — коммерческий пробел (E-06), не ошибка расхода
                continue
            assert abs(got[names[k]] - round(v, 3)) < 1e-6, (sku, k)


def test_context_not_in_bom():
    s = compile("ARV-BED-002")
    ids = {i for r in bom(s)["made"] for i in r["ids"]}
    assert not any(x in ids for x in ("mattress", "pillow0", "pillow1"))
    s = compile("ARV-KIT-004")
    assert not any("fridge" in i or "hob" in i for r in bom(s)["made"] for i in r["ids"])


if __name__ == "__main__":
    print("вариантов (техника):", test_all_variants())
    test_material_amounts_match_cost(); print("ok расход = затраты (36 моделей)")
    test_context_not_in_bom(); print("ok матрас, техника не в спецификации")
    try:
        test_prices_commercial(); print("ok цены")
    except AssertionError as e:
        print("E-06 КРАСНАЯ (ожидаемо, см. work/checks/commercial.json):", e); sys.exit(1)
