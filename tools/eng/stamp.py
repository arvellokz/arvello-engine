"""Отпечаток геометрии модели: меняется при любом изменении деталей (размеры, материал, группа).

Записывается в задания генерации и в site_images/index.json. Если отпечаток текущей модели
не совпадает с записанным, фото этого варианта устарели (tools/stale.py)."""
from __future__ import annotations

import hashlib
import json


def model_hash(model) -> str:
    rows = sorted([round(p.x0, 1), round(p.y0, 1), round(p.z0, 1), round(p.x1, 1), round(p.y1, 1), round(p.z1, 1),
                   list(p.color), p.group] for p in model.parts)
    glows = sorted([round(g.x0), round(g.y0), round(g.x1), round(g.y1), list(g.color)] for g in model.glows)
    return hashlib.sha256(json.dumps([rows, glows]).encode()).hexdigest()[:16]
