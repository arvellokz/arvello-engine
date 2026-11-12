"""Самопроверка среды: собирает комплект чертежей ОБРАЗЦА новой модели (models_new.example_wardrobe_2d),
не добавляя его в каталог. Если этот скрипт проходит — среда готова к разработке новых моделей.

    python tools/eng/selftest_new_model.py [out_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from eng import kit13, models_new  # noqa: E402
from eng.catalog import products  # noqa: E402
from eng.models13 import MODELS  # noqa: E402


def main(out_dir="work/selftest"):
    out = ROOT / out_dir
    out.mkdir(parents=True, exist_ok=True)
    sku = "ARV-EXAMPLE-001"
    MODELS.update(models_new.EXAMPLE)                    # временная регистрация, только в этом процессе
    products()[sku] = models_new.EXAMPLE_PRODUCT
    pdf = out / f"{sku}-W1000.pdf"
    s, checks, figs = kit13.write_kit(sku, str(pdf), {"width": 1000, "color": "W"})
    for f in figs:
        plt.close(f)
    bad = [c for c in checks if not c[1]]
    for n, ok, t in checks:
        print("ok " if ok else "FAIL", n, "—", t)
    print(f"\n{sku}: листов {len(figs)}, деталей {len(s['parts'])}, хеш {s['hash']}, PDF {pdf}")
    print("ГОТОВО: среда работает" if not bad else f"ЕСТЬ ОШИБКИ: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
