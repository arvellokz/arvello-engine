"""Проверки каталога с разделением результатов (CHECKS-001 v1.1; REVIEW-001 R-03).

  python tools/eng/check_catalog.py technical    # E-03, E-04, E-05(ч.): техническая корректность
  python tools/eng/check_catalog.py commercial   # E-06: коммерческая готовность (наличие и статус цен)
  python tools/eng/check_catalog.py all          # оба отчёта

Обходятся ВСЕ варианты; ошибка одного варианта или одной проверки не прерывает остальные.
Код выхода: 0 — нарушений нет, 1 — есть нарушения в запрошенной группе. Каждая группа пишет свой отчёт
(work/checks/technical.json, work/checks/commercial.json) с полным списком нарушений.
Цены «пример» считаются коммерчески НЕготовыми: наличие строки в прайсе не равно подтверждённой цене.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "eng"))
from builders import BUILDERS  # noqa: E402
from eng.catalog import compile, materials, products  # noqa: E402
from eng.core import MADE, bom, cost, matches_builder, part_row, to_model  # noqa: E402
from test_catalog import variants  # noqa: E402

PRICES = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))
REVS = json.loads((ROOT / "catalog/revisions.json").read_text(encoding="utf-8"))
EXPECTED_VARIANTS = 9586   # 14.11: комод — уровень фурнитуры (3) × корпус × фасады (16 × 16) × ширина × столик = 3072


def _expected_rev(sku):
    v = REVS.get(sku)
    return v.get("catalog") if isinstance(v, dict) else None


def technical():
    fails, n = [], 0

    def check(cond, code, sku, v, msg):
        if not cond:
            fails.append({"check": code, "sku": sku, "config": v, "msg": msg})

    for sku, p in products().items():
        for v in variants(p):
            n += 1
            try:
                s = compile(sku, v)
            except Exception as e:  # сборка не удалась — фиксируем и идём дальше
                fails.append({"check": "E-03", "sku": sku, "config": v, "msg": f"снимок не собран: {e!r}"})
                continue
            try:
                if s["rev"] == "R00":
                    bm, _ = BUILDERS[p["builder"]](v, materials())
                    check(matches_builder(to_model(s), bm)[0], "E-03", sku, v, "3D ≠ снимок")
                exp = _expected_rev(sku)
                if exp:
                    check(s["rev"] == exp, "E-05", sku, v, f"ревизия {s['rev']} ≠ реестр {exp}")
                check(s["manufacturing_allowed"] is False, "E-05", sku, v, "производство разрешено без решения")
                made = sorted(x["id"] for x in s["parts"] if x["kind"] in MADE)
                b = bom(s)
                check(sorted(i for r in b["made"] for i in r["ids"]) == made, "E-04", sku, v,
                      "спецификация ≠ детали (пропуск или дубль)")
                for x in s["parts"]:
                    check(x["x1"] > x["x0"] and x["y1"] > x["y0"] and x["z1"] > x["z0"], "E-03", sku, v,
                          f"пустой/отрицательный размер {x['id']}")
            except Exception:
                fails.append({"check": "E-03", "sku": sku, "config": v, "msg": traceback.format_exc(limit=2)})
    # расход = затраты (по базовой конфигурации)
    names = {k: m["name"] for k, m in PRICES["materials"].items()}
    for sku in products():
        s = compile(sku)
        amounts = {}
        for x in s["parts"]:
            if x["kind"] in MADE and x["kind"] != "volume":
                amounts[x["material"]] = amounts.get(x["material"], 0) + part_row(x)[2]
        got = {l["name"]: l["qty"] for l in cost(s, PRICES)["lines"] if l["group"] == "Материалы"}
        for k, q in amounts.items():
            if k in names:   # материал без цены — это коммерческий пробел, не техническая ошибка
                check(abs(got.get(names[k], -1) - round(q, 3)) < 1e-6, "E-04", sku, {}, f"расход {k} ≠ затраты")
    if n != EXPECTED_VARIANTS:
        fails.append({"check": "E-03", "sku": "*", "config": {}, "msg": f"вариантов {n}, ожидалось {EXPECTED_VARIANTS}"})
    return {"group": "technical", "variants": n, "failures": fails}


def commercial():
    example = "ПРИМЕР" in PRICES.get("_status", "").upper()
    fails, n, ready = [], 0, 0
    for sku, p in products().items():
        for v in variants(p):
            n += 1
            try:
                s = compile(sku, v)
                c = cost(s, PRICES)
                gaps = [m for m in c["missing"] if m.startswith("нет цены")]
                for m in gaps:
                    fails.append({"check": "E-06", "sku": sku, "config": v, "msg": m})
                if example:
                    fails.append({"check": "E-06", "sku": sku, "config": v,
                                  "msg": "цены прайса — пример, не подтверждены"})
                if not gaps and not example:
                    ready += 1
            except Exception as e:
                fails.append({"check": "E-06", "sku": sku, "config": v, "msg": f"расчёт не выполнен: {e!r}"})
    skus = sorted({f["sku"] for f in fails if not f["msg"].startswith("цены прайса")})
    return {"group": "commercial", "variants": n, "commercially_ready": ready, "prices_example": example,
            "models_with_missing_price": len(skus), "failures": fails}


def main(which):
    out = ROOT / "work/checks"; out.mkdir(parents=True, exist_ok=True)
    bad = False
    for name, fn in (("technical", technical), ("commercial", commercial)):
        if which not in (name, "all"):
            continue
        r = fn()
        (out / f"{name}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        by = {}
        for f in r["failures"]:
            by[f["check"]] = by.get(f["check"], 0) + 1
        print(f"{name}: вариантов {r['variants']}, нарушений {len(r['failures'])} {by}",
              {k: v for k, v in r.items() if k not in ("failures", "group", "variants")})
        bad |= bool(r["failures"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
