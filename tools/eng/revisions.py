"""Реестр ревизий: какая ревизия конструкции идёт в каталог (3D, фото, цена на сайте)."""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "catalog" / "revisions.json"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def catalog_rev(sku: str) -> str:
    return load()[sku]["catalog"]


def production_allowed(sku: str, rev: str) -> bool:
    """Допуск в изготовление — отдельно от показа в каталоге. Сейчас нигде не выдан."""
    return load()[sku].get("revisions", {}).get(rev, {}).get("production") == "разрешено"
