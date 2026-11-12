"""ENG-002 · сборка всего комплекта примера за один запуск + манифест (проверка Codex 13.11: общий идентификатор).

Все PDF строятся из одного состояния модели; снимок модели (хеш геометрии) — идентификатор данных, «вид» — версия
оформления документов. В манифесте у файлов одного исполнения снимок обязан совпасть, иначе выход с ошибкой.

Запуск: python3 tools/eng/eng002_kit.py [папка]   (по умолчанию docs/eng-002)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import eng002_chest as C  # noqa: E402
from eng import eng002_drawer as E  # noqa: E402
from eng import eng002_guide as G  # noqa: E402

DOC_VERSION = "ENG-002 вид 4 (13.11.2026)"
BASE = {"width": "1200", "handle": "push", "color": "O"}


def build(out):
    out = Path(out)
    rows, fails = [], []
    for ch, tag in (("yes", "со столиком"), ("no", "без столика")):
        o = {**BASE, "changer": ch}
        suf = "" if ch == "yes" else "_без_столика"
        D1, r1 = C.write(str(out / f"ARV-NST-101_комод{suf}_инструкция_A4.pdf"), o)
        files = [(f"ARV-NST-101_комод{suf}_инструкция_A4.pdf", D1["s"]["hash"], r1)]
        if ch == "yes":
            D2, r2 = G.write(str(out / "ARV-NST-101_ящик_инструкция_A4.pdf"), o)
            D3, _ = E.write(str(out / "ARV-NST-101_ящик_ENG-002.pdf"), o)
            files += [("ARV-NST-101_ящик_инструкция_A4.pdf", D2["s"]["hash"], r2),
                      ("ARV-NST-101_ящик_ENG-002.pdf", D3["s"]["hash"], [("Крепёж на рисунках", not D3["view_errors"], "")])]
        hs = {h for _, h, _ in files}
        if len(hs) != 1:
            fails.append(f"{tag}: разные снимки {sorted(hs)}")
        for name, h, res in files:
            bad = [x[0] for x in res if not x[1]]
            fails += [f"{name}: {b}" for b in bad]
            rows.append((tag, name, h, "пройдены" if not bad else "ОШИБКА: " + "; ".join(bad)))
    for f in out.glob("*.png"):
        f.unlink()
    md = ["# ENG-002 · манифест комплекта примера", "",
          f"Версия оформления: **{DOC_VERSION}**. Снимок модели — хеш геометрии и опций из генератора: у файлов одного "
          "исполнения он один. Наклейки несут исполнение и первые 8 знаков снимка. Статус: пример, не утверждено.", "",
          "| Исполнение | Файл | Снимок модели | Проверки выпуска |", "|---|---|---|---|"]
    md += [f"| {t} | `{n}` | `{h}` | {r} |" for t, n, h, r in rows]
    (out / "МАНИФЕСТ.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rows, fails


if __name__ == "__main__":
    rows, fails = build(sys.argv[1] if len(sys.argv) > 1 else "docs/eng-002")
    for r in rows:
        print(" | ".join(r))
    print("FAIL " + "; ".join(fails) if fails else "ok  комплект: один снимок на исполнение, проверки пройдены")
    sys.exit(1 if fails else 0)
