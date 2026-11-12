"""Описание изделия для промпта генератора по ТЕКУЩЕЙ ревизии каталога (catalog/revisions.json).

Тексты построителей (builders.py) писались под каталожную геометрию R00. Здесь они приводятся
к рабочим чертежам: правки по известным отличиям (лист «Отличия от каталога», В-43) и строка с
габаритами, посчитанными из снимка — той же геометрии, что на чертежах цеха и в 3D-каталоге."""
from __future__ import annotations

import re

FIXES = {
    # «Кокон» R01E: 4 мягкие панели только за кроватью, тумбы навешены на стеновую панель
    "ARV-BED-003": [
        (r"a full-wall soft headboard \d+ cm wide made of 7 vertical upholstered panels from 30 to 150 cm height, over a smooth "
         r"wall cladding in (.+?)\.$",
         r"a full-wall smooth wall cladding in \1; on it, only behind the bed, 4 vertical upholstered panels from 30 to 150 cm "
         r"height (the cladding beside them stays smooth)."),
        (r"On each side a wall-hung nightstand", "On each side, hung on the wall cladding, a wall-hung nightstand"),
    ],
    "ARV-KIT-003": [
        (r"L-shaped kitchen, 2400 cm and 1600 mm runs", "L-shaped kitchen with 240 cm and 160 cm runs"),
        (r"recessed plinth\.", "recessed plinth that also closes the open ends of both runs."),
    ],
    "ARV-KIT-001": [(r"recessed plinth\.", "recessed plinth that also closes both open ends.")],
    "ARV-KIT-002": [(r"recessed plinth\.", "recessed plinth that also closes both open ends.")],
    "ARV-KIT-005": [
        (r"a kitchen island (\d+) x 90 cm with handleless drawers facing the kitchen,",
         r"a kitchen island \1 x 90 cm with handleless drawers facing the kitchen and a closed flat back panel "
         r"in the cabinet color on the room side,"),
    ],
    "ARV-LIV-002": [(r"boxes with a flat front", "boxes with a flat push-to-open front")],
    "ARV-BED-002": [(r"plinth: black matte powder-coated steel", "recessed plinth: matte black panels")],
}


def overall_cm(snap):
    P = [p for p in snap["parts"] if p["kind"] not in ("context",)]
    if not P:
        return None
    w = max(p["x1"] for p in P) - min(p["x0"] for p in P)
    d = max(p["y1"] for p in P) - min(p["y0"] for p in P)
    h = max(p["z1"] for p in P) - min(p["z0"] for p in P)
    return round(w / 10), round(d / 10), round(h / 10)


def current_facts(sku, facts, snap):
    out = []
    for f in facts:
        for pat, rep in FIXES.get(sku, []):
            f = re.sub(pat, rep, f)
        out.append(f)
    dims = overall_cm(snap)
    if dims:
        out.append(f"Overall size of the product from its production drawing (rev. {snap['rev']}): "
                   f"{dims[0]} cm wide x {dims[1]} cm deep x {dims[2]} cm high.")
    return out
