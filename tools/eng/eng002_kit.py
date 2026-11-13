"""ENG-002 · единый выпуск за один запуск: A3 для цеха + A4 для сборщика + CSV, один снимок модели на исполнение.

Разбор 13.11 (G5): выпуск — одним набором, старые копии заменяются. Все файлы исполнения строятся из одного состояния
модели; снимок (хеш геометрии и опций) у них обязан совпасть, иначе выход с ошибкой. Сверка «A4 = A3»: что сказано
сборщику (зенковка, число саморезов), то есть и на листах цеха.

Запуск: python3 tools/eng/eng002_kit.py [папка]   (по умолчанию docs/eng-002/выпуск)
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import bazis as BZ  # noqa: E402
from eng import eng002_chest as C  # noqa: E402
from eng import eng002_drawer as E  # noqa: E402
from eng import eng002_guide as G  # noqa: E402
from eng import kit13  # noqa: E402

DOC_VERSION = "ENG-002 вид 5 (13.11.2026)"
BASE = {"width": "1200", "handle": "push", "color": "O"}
WRD = {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers", "color": "O"}


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout


def a4_vs_a3(a4_text, s):
    """Что сказано сборщику в A4, то есть на листах цеха A3 (один снимок). Возвращает список расхождений."""
    bad = []
    bz = s["_bazis"][0]
    regs = bz["panels"].values()
    cs_all = sum(1 for r in regs for q in r["P"]["holes"] if q["h"].get("cs"))
    cs_marked = sum(len(r.get("cs_marked", ())) for r in regs)
    if "зенковк" in a4_text.lower():
        if not cs_all:
            bad.append("A4 говорит «с зенковкой», а в модели нет отверстий с зенковкой")
        elif cs_marked < cs_all:
            bad.append(f"A4 говорит «с зенковкой», а на листах цеха зенковка у {cs_marked} из {cs_all} отверстий")
    elif cs_all:
        bad.append("на листах цеха есть зенковка, а A4 о ней молчит")
    m = re.search(r"(\d+) самореза в готовых отверстиях", a4_text)
    if m:
        per_box = int(re.search(r"\((\d+) на ящик", a4_text).group(1)) if re.search(r"\((\d+) на ящик", a4_text) else None
        bottoms = [h for h in s["holes"] if h.get("cs") and "-BOX" in h["part"] and h["part"].endswith("-BOT")]
        if per_box is not None:
            boxes = {h["part"] for h in bottoms}
            if boxes and any(sum(1 for h in bottoms if h["part"] == b) != per_box for b in boxes):
                bad.append(f"A4: {per_box} самореза дна на ящик, на листах цеха — другое число отверстий")
    return bad


def write_csv(path, s):
    """CSV для цеха — из тех же строк спецификации, что лист A3 (позиция, заготовка), и покупные изделия."""
    rows = s["_bazis"][2]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([f"Обозначение: {BZ.designation(s)}", f"Снимок: {s['hash']}", "R01E — не для изготовления"])
        w.writerow(["Поз.", "Наименование", "Кол-во", "Материал", "Готовый размер, мм", "Заготовка, мм", "Примечание"])
        for r in rows:
            if r[0] and r[0].strip():
                w.writerow(r[:7])
        w.writerow([])
        w.writerow(["Код", "Наименование", "Спецификация", "Кол-во", "Ед.", "Статус"])
        for h in s["hardware"]:
            w.writerow([h["id"], h["name"], h["spec"], h["qty"], h.get("uom", "шт"), h["status"]])


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in list(out.glob("*.pdf")) + list(out.glob("*.csv")):
        f.unlink()
    rows, fails = [], []

    def a3(sku, o, name):
        s, checks, figs = kit13.write_kit(sku, str(out / name), dict(o))
        for f_ in figs:
            kit13.plt.close(f_)
        return s, [(n, ok, t) for n, ok, t in checks]

    sets = [("ARV-NST-101", {**BASE, "changer": "yes"}, "комод 1200, со столиком", "ARV-NST-101_комод_со_столиком"),
            ("ARV-NST-101", {**BASE, "changer": "no"}, "комод 1200, без столика", "ARV-NST-101_комод_без_столика"),
            ("ARV-WRD-101", WRD, "шкаф 2400 × 2800 × 450", "ARV-WRD-101_шкаф_2400x2800x450")]
    for sku, o, tag, stem in sets:
        files = []
        s3, ch3 = a3(sku, o, f"{stem}_A3_цех.pdf")
        files.append((f"{stem}_A3_цех.pdf", s3["hash"], ch3))
        csvn = f"{stem}_детали_и_покупные.csv"
        write_csv(out / csvn, s3)
        files.append((csvn, s3["hash"], [("из спецификации A3", True, "")]))
        if sku == "ARV-NST-101":
            a4n = f"{stem}_инструкция_A4.pdf"
            D1, r1 = C.write(str(out / a4n), o)
            files.append((a4n, D1["s"]["hash"], r1))
            bad = a4_vs_a3(pdf_text(out / a4n), s3)
            files.append(("сверка A4 = A3", s3["hash"], [(b, False, "") for b in bad] or [("A4 = A3", True, "")]))
            if o["changer"] == "yes":
                D2, r2 = G.write(str(out / "ARV-NST-101_ящик_инструкция_A4.pdf"), o)
                D3, _ = E.write(str(out / "ARV-NST-101_ящик_пример_A3.pdf"), o)
                files += [("ARV-NST-101_ящик_инструкция_A4.pdf", D2["s"]["hash"], r2),
                          ("ARV-NST-101_ящик_пример_A3.pdf", D3["s"]["hash"],
                           [("Крепёж на рисунках", not D3["view_errors"], "")])]
                bad = a4_vs_a3(pdf_text(out / "ARV-NST-101_ящик_инструкция_A4.pdf"), s3)
                files.append(("сверка A4 ящика = A3", s3["hash"], [(b, False, "") for b in bad] or [("A4 = A3", True, "")]))
        hs = {h for _, h, _ in files}
        if len(hs) != 1:
            fails.append(f"{tag}: разные снимки {sorted(hs)}")
        for name, h, res in files:
            bad = [x[0] for x in res if not x[1]]
            fails += [f"{name}: {b}" for b in bad]
            rows.append((tag, name, h, "пройдены" if not bad else "ОШИБКА: " + "; ".join(bad)))
    for f in out.glob("*.png"):
        f.unlink()
    md = ["# ENG-002 · манифест выпуска", "",
          f"Версия оформления: **{DOC_VERSION}**. Один запуск `python3 tools/eng/eng002_kit.py` строит всё ниже из одного "
          "состояния модели. Снимок модели — хеш геометрии и опций: у файлов одного исполнения он один (A3 цеха, A4 "
          "сборщика, CSV). Строки «сверка A4 = A3» — что сказано сборщику, то есть на листах цеха. Статус: R01E, не для "
          "изготовления, не утверждено. Старые копии (в том числе в Obsidian) заменить этим набором.", "",
          "| Исполнение | Файл | Снимок модели | Проверки выпуска |", "|---|---|---|---|"]
    md += [f"| {t} | `{n}` | `{h}` | {r} |" for t, n, h, r in rows]
    (out / "МАНИФЕСТ.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rows, fails


if __name__ == "__main__":
    rows, fails = build(sys.argv[1] if len(sys.argv) > 1 else "docs/eng-002/выпуск")
    for r in rows:
        print(" | ".join(r))
    print("FAIL " + "; ".join(fails) if fails else "ok  выпуск: один снимок на исполнение, проверки пройдены")
    sys.exit(1 if fails else 0)
