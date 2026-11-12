"""Заморозка комплекта заказа: снимок, чертёж, спецификация и затраты сохраняются один раз и больше не пересчитываются.

    python tools/eng/freeze_order.py ORD-0001 ARV-TBL-003 size=1600 top=O metal=black [rev=R02E] [--trial]
Изменения каталога и цен после этого не трогают папку заказа. --trial — пробный образец по ревизии без допуска в изготовление (в манифесте пометка trial)."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from eng.core import bom, cost, snapshot  # noqa: E402
from eng.drawing import write_pdf  # noqa: E402
from eng.opora import build  # noqa: E402
from eng.revisions import catalog_rev, production_allowed  # noqa: E402

ENGINES = {"ARV-TBL-003": build}


def freeze(order_id, sku, options, rev=None, trial=False, root=ROOT / "orders"):
    out = Path(root) / order_id
    if out.exists():
        raise SystemExit(f"{order_id} уже заморожен — комплект не перезаписывается")
    rev = rev or catalog_rev(sku)
    if not production_allowed(sku, rev) and not trial:
        raise SystemExit(f"{sku} {rev}: изготовление не разрешено; для пробного образца добавьте --trial")
    snap = snapshot(ENGINES[sku](options, rev))
    prices = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True)
    files = {
        "snapshot.json": json.dumps(snap, ensure_ascii=False, indent=1),
        "bom.json": json.dumps(bom(snap), ensure_ascii=False, indent=1),
        "cost.json": json.dumps(cost(snap, prices), ensure_ascii=False, indent=1),
    }
    for n, txt in files.items():
        (out / n).write_text(txt, encoding="utf-8")
    write_pdf(snap, out / "drawing.pdf")
    man = {"order": order_id, "frozen_at": datetime.now().isoformat(timespec="seconds"), "sku": sku, "rev": rev,
           "trial": trial, "config_hash": snap["hash"],
           "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir())}}
    (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in out.iterdir():
        os.chmod(f, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return out, snap


if __name__ == "__main__":
    a = sys.argv[1:]
    trial = "--trial" in a
    a = [x for x in a if x != "--trial"]
    kv = dict(x.split("=", 1) for x in a[2:])
    rev = kv.pop("rev", None)
    if "size" in kv:
        kv["size"] = int(kv["size"])
    out, snap = freeze(a[0], a[1], kv, rev, trial)
    print(f"Заморожено: {out} · {snap['rev']} · конфигурация {snap['hash']}")
