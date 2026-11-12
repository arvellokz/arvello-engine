"""Проверки тумбы «Самал» (ARV-NST-001, R01E): ядро, комплект, единый источник.

    python tools/eng/test_samal.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import matplotlib.pyplot as plt  # noqa: E402

from builders import BUILDERS  # noqa: E402
from eng import kit_samal  # noqa: E402
from eng.catalog import compile, materials  # noqa: E402
from eng.core import bom, matches_builder, to_model  # noqa: E402
from eng.stamp import model_hash  # noqa: E402

COLORS = ("W", "C", "O", "G")


def test_geometry_same_for_all_colors():
    geo = {c: [(p["id"], p["x0"], p["y0"], p["z0"], p["x1"], p["y1"], p["z1"]) for p in compile(kit_samal.SKU, {"color": c})["parts"]]
           for c in COLORS}
    assert all(g == geo["W"] for g in geo.values())


def test_builder_is_core():
    for c in COLORS:
        s = compile(kit_samal.SKU, {"color": c})
        bm, _ = BUILDERS["nightstand"]({"color": c}, materials())
        assert model_hash(to_model(s)) == model_hash(bm)
        assert matches_builder(to_model(s), bm) == (True, 0)


def test_bom_counts():
    s = compile(kit_samal.SKU, {"color": "O"})
    q = {r["unit"]: r["qty"] for r in bom(s)["made"]}
    assert q["Боковина ящика"] == 4 and q["Фасад ящика"] == 2 and q["Цоколь продольный"] == 2
    assert q["Боковина левая"] == q["Боковина правая"] == 1      # зеркальные — разные позиции


def test_kit_all_colors():
    for c in COLORS:
        with tempfile.TemporaryDirectory() as d:
            s, checks, figs = kit_samal.build_and_verify(str(Path(d) / "k.pdf"), {"color": c})
            for f in figs:
                plt.close(f)
        bad = [(n, t) for n, ok, t in checks if not ok]
        assert not bad, (c, bad)
    return len(checks)


def test_manufacturing_closed():
    s = compile(kit_samal.SKU, {"color": "W"})
    assert s["manufacturing_allowed"] is False and s["blockers"]


if __name__ == "__main__":
    test_geometry_same_for_all_colors(); print("ok геометрия одинакова для 4 декоров")
    test_builder_is_core(); print("ok 3D-каталог = ядро")
    test_bom_counts(); print("ok спецификация")
    n = test_kit_all_colors(); print(f"ok комплект: {n} проверок × 4 декора")
    test_manufacturing_closed(); print("ok выпуск закрыт")
