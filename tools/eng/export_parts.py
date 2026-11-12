"""Деталировка и покупные изделия конфигурации в CSV (для цеха; формат программы цеха — уточнить).

    python tools/eng/export_parts.py SKU out_dir [key=value ...]

Пишет <SKU>-<хеш>-детали.csv и <SKU>-<хеш>-покупные.csv (UTF-8 с BOM, разделитель «;» — открывается в Excel).
Размеры — из снимка конфигурации, тот же снимок, что в PDF-комплекте (хеш совпадает).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from eng import kit13  # noqa: E402,F401  регистрирует все модели, включая models_new
from eng.core import bom  # noqa: E402
from eng.kit13 import MAT_RU, make  # noqa: E402


def export(sku, out_dir, options=None):
    s = make(sku, options)
    b = bom(s)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = f"{sku}-{s['hash']}"
    p1 = out / f"{base}-детали.csv"
    with open(p1, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Деталь", "Материал", "Код материала", "Декор", "Размер, мм (Д × Ш × Т)", "Кол-во", "Кромка, м", "ID деталей"])
        for r in b["made"]:
            w.writerow([r["unit"], MAT_RU.get(r["material"], r["material"]), r["material"], r["finish"], r["size"], r["qty"],
                        round(r.get("edge_m") or 0, 2), " ".join(r["ids"])])
    p2 = out / f"{base}-покупные.csv"
    with open(p2, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Код", "Наименование", "Спецификация", "Кол-во", "Ед.", "Статус", "Вопрос"])
        for h in b["buy"]:
            w.writerow([h["id"], h["name"], h["spec"], h["qty"], h.get("uom", "шт"), h["status"], h.get("note", "")])
    return s, p1, p2


if __name__ == "__main__":
    a = sys.argv[1:]
    kv = dict(x.split("=", 1) for x in a[2:])
    s, p1, p2 = export(a[0], a[1], kv)
    print(f"{a[0]} {s['rev']} {s['hash']}\n{p1}\n{p2}")
