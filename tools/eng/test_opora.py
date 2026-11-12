"""Проверки сквозной цепочки «Опоры»: python -m pytest tools/eng -q  (или python tools/eng/test_opora.py)."""
from __future__ import annotations

import gzip
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from builders import BUILDERS  # noqa: E402
from eng.core import bom, cost, cut_plan, snapshot, to_model, tube_lengths  # noqa: E402
from eng.freeze_order import freeze  # noqa: E402
from eng.opora import LENGTHS, build, palette  # noqa: E402
from eng.stamp import model_hash  # noqa: E402

MATS = json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))
PRICES = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))
OPT = {"size": 1600, "top": "O", "metal": "black"}


def test_golden_1512_from_r02e_package():
    """Каждая из 1512 комбинаций пакета R02-E: все детали (id + границы), все отверстия, крепёж, размеры."""
    n = 0
    with gzip.open(Path(__file__).parent / "fixtures/opora-r02e-golden.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            g = json.loads(line)
            cfg = dict(g["config"]); cfg["size"] = cfg.pop("length")
            s = snapshot(build(cfg, "R02E"))
            mine = {p["id"]: [p["x0"], p["y0"], p["z0"], p["x1"], p["y1"], p["z1"]] for p in s["parts"]}
            gold = {p["id"]: p["bounds"] for p in g["parts"]}
            assert mine.keys() == gold.keys(), (g["config"], mine.keys() ^ gold.keys())
            for k in gold:
                assert all(abs(a - b) < 1e-9 for a, b in zip(mine[k], gold[k])), (g["config"], k, mine[k], gold[k])
            hk = ("id", "part_id", "x", "y", "z", "kind", "width", "length", "pilot", "pilot_depth")
            assert [tuple(h[k] for k in hk) for h in s["holes"]] == [tuple(h[k] for k in hk) for h in g["holes"]], g["config"]
            gd = g["dimensions"]; d = s["derived"]
            assert (d["width"], d["frame_h"], d["leg"], d["bar"]) == (gd["depth"], gd["frame_height"], gd["post_cut"], gd["frame_width"])
            buy = {h["id"]: h["qty"] for h in s["hardware"]}
            gb = {b["id"]: b["quantity"] for b in g["bom"] if b["kind"] == "purchased"}
            assert (buy["INSERT-M6"], buy["SCREW-M6x16"], buy["WASHER-6.4x18"], buy["RIVNUT-M8"]) == \
                   (gb["INSERT-SK330"], gb["SCREW-M6x16"], gb["WASHER-M6"], gb["RIVET-NUT-M8"])
            assert set(g["blockers"]) <= set(s["blockers"])
            n += 1
    assert n == 1512


def test_r03e_low_feet():
    s = snapshot(build(OPT, "R03E"))
    assert all(c["ok"] for c in s["checks"]), [c for c in s["checks"] if not c["ok"]]
    d = s["derived"]
    assert (d["frame_h"], d["leg"], d["feet_y"]) == (713, 633, 115)
    feet = [p for p in s["parts"] if p["id"].startswith("FOOT")]
    assert len(feet) == 4 and all(100 <= p["y0"] and p["y1"] <= 900 - 100 for p in feet)   # внутри нижней перекладины
    for L in LENGTHS:                                        # не хуже прежнего стола на перекладинах более чем на 15%
        a = snapshot(build({**OPT, "size": L}, "R03E"))["derived"]["tip_load_kg"]
        b = snapshot(build({**OPT, "size": L}, "R00"))["derived"]["tip_load_kg"]
        assert a >= 0.85 * b, (L, a, b)


def test_r02e_matches_package():
    s = snapshot(build(OPT, "R02E"))
    assert all(c["ok"] for c in s["checks"]), [c for c in s["checks"] if not c["ok"]]
    bars = cut_plan(tube_lengths(s))
    assert [b["rest"] for b in bars] == [109, 4141]          # R02-E, лист 9


def test_all_sizes_build():
    for rev in ("R00", "R02E", "R03E"):
        for L in LENGTHS:
            s = snapshot(build({**OPT, "size": L}, rev))
            assert all(c["ok"] for c in s["checks"]), (rev, L)
            assert s["derived"]["width"] == (800 if L <= 1400 else 900)


def test_out_of_range_rejected():
    for bad in ({**OPT, "size": 2100}, {**OPT, "size": 1650}, {**OPT, "base": "solid"}, {**OPT, "thickness": 18},
                {**OPT, "substrate": "solid-wood"}, {**OPT, "foot_height": 3}, {**OPT, "size": float("nan")},
                {**OPT, "size": True}, {**OPT, "colour": "red"}):
        try:
            build(bad, "R02E")
        except (ValueError, TypeError):
            continue
        raise AssertionError(bad)


def test_3d_drawing_bom_cost_share_parts():
    s = snapshot(build(OPT, "R02E"))
    model = to_model(s, palette(MATS))
    assert [(p.name, p.x0, p.y0, p.z0, p.x1, p.y1, p.z1) for p in model.parts] == \
           [(p["id"], p["x0"], p["y0"], p["z0"], p["x1"], p["y1"], p["z1"]) for p in s["parts"]]
    b = bom(s)
    ids = [i for r in b["made"] for i in r["ids"]]
    assert sorted(ids) == sorted(p["id"] for p in s["parts"] if p["kind"] != "buy")
    c = cost(s, PRICES)
    tube_m = sum(l["qty"] for l in c["lines"] if l["name"].startswith("Труба"))
    assert abs(tube_m - b["tube_net_mm"] / 1000) < 1e-6
    assert c["price"] % 1000 == 0 and c["price"] >= c["cost"]


def test_catalog_builder_uses_core():
    m, _ = BUILDERS["dining_table_u"](OPT, MATS)
    s = m.snapshot
    assert s["rev"] == "R03E" and s["options"]["base"] == "linked" and s["derived"]["feet_h"] == 12
    assert [p.name for p in m.parts] == [p["id"] for p in s["parts"]]


def test_hash_changes_with_geometry_not_with_prices():
    a, b = snapshot(build(OPT, "R00")), snapshot(build(OPT, "R02E"))
    assert a["hash"] != b["hash"]
    assert snapshot(build(OPT, "R02E"))["hash"] == b["hash"]
    ma, mb = to_model(a, palette(MATS)), to_model(b, palette(MATS))
    assert model_hash(ma) != model_hash(mb)        # смена ревизии -> фото устарели


def test_freeze_is_write_once():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            freeze("ORD-T1", "ARV-TBL-003", OPT, "R02E", trial=False, root=tmp)
            raise AssertionError("неутверждённая ревизия без --trial")
        except SystemExit:
            pass
        out, snap = freeze("ORD-T1", "ARV-TBL-003", OPT, "R02E", trial=True, root=tmp)
        assert (out / "drawing.pdf").exists() and json.loads((out / "manifest.json").read_text())["config_hash"] == snap["hash"]
        try:
            freeze("ORD-T1", "ARV-TBL-003", OPT, "R02E", trial=True, root=tmp)
            raise AssertionError("перезапись заказа")
        except SystemExit:
            pass


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1; print("ok", k)
    print(f"{n} проверок пройдено")
