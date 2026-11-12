"""Реестр ценовых разрывов ядра (CHECKS-001, E-06; REVIEW-001 R-04).

Воспроизведение:  python tools/eng/price_gaps.py  [--out work/price_gaps]
Обходит все варианты 3D-каталога (те же, что test_catalog.py), собирает каждый код материала,
покупной позиции и операции из снимков и сверяет с catalog/prices.json.

Категории:
  нет_строки          — кода нет в прайсе, похожего кода тоже нет;
  возможно_другой_код — кода нет, но в прайсе есть код с теми же размерами/смыслом (сопоставление не подтверждено);
  деталировка         — деталь-объём без раскроя: в стоимость не входит;
  цена_пример         — строка есть, но весь прайс помечен как пример (_status), цена не подтверждена.
Цены не придумываются и не заполняются; скрипт только перечисляет.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "eng"))
from eng.catalog import compile, products  # noqa: E402
from eng.core import MADE, bom  # noqa: E402
from test_catalog import variants  # noqa: E402

PRICES_PATH = ROOT / "catalog/prices.json"
# Кандидаты сопоставления: код ядра -> код прайса. Только подсказка для 02, не подтверждённое соответствие.
ALIAS_RULES = [
    (re.compile(r"^BEAM(\d+x\d+)$"), lambda m: f"TIMBER{m.group(1)}"),
    (re.compile(r"^STONE\d+$"), lambda m: "STONE"),
]
# Похожие по названию строки прайса (возможно, старый код той же позиции). Тип прайса указан явно,
# если он отличается от типа в ядре. Сопоставление — гипотеза для 02/06, не решение.
ALIAS_EXPLICIT = {
    "CABLEBOX": "покупное:CABLE-BOX",
    "LIFT": "покупное:LIFT-MECH",
    "HANDLE-320": "покупное:HANDLE",
    "GLIDE-M8": "покупное:FOOT-ADJ",
    "UPH": "материал:UPHOLSTERY",
    "UPH-PANEL": "материал:UPHOLSTERY",
    "MIRROR": "материал:MIRROR",
    "weld_joint": "операция:weld_frame_joint",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_version() -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in (ROOT / "tools/eng").glob("*.py") if x.name != "price_gaps.py" and not x.name.startswith("test_")) + [ROOT / "catalog/revisions.json"]:
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()[:16]


def cfg_str(v: dict) -> str:
    return ", ".join(f"{k}={val}" for k, val in v.items())


def run(out: Path):
    prices = json.loads(PRICES_PATH.read_text(encoding="utf-8"))
    is_example = "ПРИМЕР" in prices.get("_status", "").upper()
    P = {"материал": prices["materials"], "покупное": prices["hardware"], "операция": prices["operations"]}

    # код -> сведения
    codes = {}
    sku_rows = []
    for sku, p in products().items():
        nvar, gapvar = 0, 0
        sku_codes = set()
        rev = None
        for v in variants(p):
            s = compile(sku, v)
            rev = s["rev"]
            nvar += 1
            used = []
            for r in bom(s)["made"]:
                if r["kind"] == "volume":
                    used.append(("деталировка", r["unit"], "объём", r["unit"]))
                else:
                    used.append(("материал", r["material"], r["kind"], ""))
            for h in s["hardware"]:
                used.append(("покупное", h["id"], h.get("uom", "шт"), h.get("name", "")))
            for k, q in s.get("ops", {}).items():
                if q:
                    used.append(("операция", k, "", ""))
            var_gap = False
            for typ, code, unit, name in used:
                key = (typ, code)
                c = codes.setdefault(key, {"type": typ, "code": code, "unit": unit, "name": name,
                                           "skus": set(), "configs": defaultdict(list), "n_variants": 0})
                c["skus"].add(sku); c["n_variants"] += 1
                if len(c["configs"][sku]) < 3:
                    c["configs"][sku].append(cfg_str(v))
                if typ == "деталировка" or code not in P[typ]:
                    var_gap = True
                    sku_codes.add(code)
            gapvar += var_gap
        sku_rows.append({"sku": sku, "rev": rev, "variants": nvar, "variants_with_gap": gapvar,
                         "gap_codes": " ".join(sorted(sku_codes))})

    rows = []
    for (typ, code), c in sorted(codes.items()):
        if typ == "деталировка":
            cat, hint = "деталировка", ""
        elif code in P[typ]:
            cat = "цена_пример" if is_example else "есть"
            hint = ""
        else:
            hint = ""
            for rx, f in ALIAS_RULES:
                m = rx.match(code)
                if m and f(m) in P[typ]:
                    hint = f"{typ}:{f(m)}"
            if not hint and code in ALIAS_EXPLICIT:
                t2, c2 = ALIAS_EXPLICIT[code].split(":")
                if c2 in P[t2]:
                    hint = ALIAS_EXPLICIT[code]
            cat = "возможно_другой_код" if hint else "нет_строки"
        rows.append({
            "категория": cat, "тип": typ, "код": code, "единица_или_вид": c["unit"], "название": c["name"],
            "кандидат_в_прайсе": hint, "моделей": len(c["skus"]), "вариантов": c["n_variants"],
            "модели": " ".join(sorted(c["skus"])),
            "примеры_конфигураций": " | ".join(f"{s}: {cfgs[0]}" for s, cfgs in sorted(c["configs"].items())[:3]),
        })

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "price_gaps_codes.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";"); w.writeheader(); w.writerows(rows)
    with open(out / "price_gaps_models.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(sku_rows[0]), delimiter=";"); w.writeheader(); w.writerows(sku_rows)

    count = defaultdict(lambda: defaultdict(int))
    for r in rows:
        count[r["категория"]][r["тип"]] += 1
    summary = {
        "engine_version": engine_version(),
        "prices_sha256": sha(PRICES_PATH),
        "prices_status": prices.get("_status", ""),
        "variants": sum(r["variants"] for r in sku_rows),
        "models": len(sku_rows),
        "models_with_gap": sum(1 for r in sku_rows if r["variants_with_gap"]),
        "variants_with_gap": sum(r["variants_with_gap"] for r in sku_rows),
        "codes_by_category": {k: dict(v) for k, v in count.items()},
        "prices_rows_unused": {
            t: sorted(set(P[t]) - {c for (tt, c) in codes if tt == t}) for t in P},
    }
    (out / "price_gaps_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work/price_gaps"))
    a = ap.parse_args()
    print(json.dumps(run(Path(a.out)), ensure_ascii=False, indent=1))
