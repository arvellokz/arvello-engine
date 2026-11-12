"""Пакет для ChatGPT: задание + пронумерованные референсы + промпты по каждому кадру набора фото.

    python tools/gpt_pack.py OUT_DIR          # после build_jobs.py --set catalog/photo_set.json

Оба кадра — как реальная фотография в квартире (офисная мебель — в офисе), естественный дневной свет:
  main      — главное фото: изделие крупно, спокойная стена за ним, минимум декора;
  interior  — интерьерный кадр: комната шире, изделие в жизни.
Результаты ChatGPT сохраняются как NN.png в work/inbox → generate.py --import-inbox (по gpt_manifest.json)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa: E402
from eng.catalog import compile as compile_snapshot  # noqa: E402
from facts import current_facts  # noqa: E402

CAT_ORDER = ["BED", "NST", "WRD", "LIV", "KIT", "TBL", "BTH", "OFF"]

# Где стоит изделие в кадре (чтобы ChatGPT не поставил настенное на пол и т.п.)
PLACEMENT = {
    "BED": "The bed stands with its headboard against a wall.",
    "ARV-BED-003": "The wall panel with the upholstered panels is fixed to the wall behind the bed; the two bedside shelves hang on it; the sconces are on the panel.",
    "NST": "It stands against a wall.",
    "ARV-NST-001": "It stands next to a made bed (bed partly visible), against the wall.",
    "ARV-NST-004": "It is wall-mounted beside a bed at about 40 cm above the floor; the floor under it is free.",
    "ARV-NST-003": "It stands against the living-room wall; a TV may hang on the wall above it.",
    "WRD": "It stands against a wall.",
    "ARV-WRD-004": "It is built into a niche from wall to wall and from floor to ceiling, like a flat wall of doors.",
    "ARV-WRD-006": "It stands along the wall of a small walk-in closet, with a few clothes on the rails and folded items on the shelves.",
    "ARV-WRD-007": "The wardrobe stands in the corner of the hallway reaching the ceiling; the bench and the mirror are fixed to the wall next to it.",
    "ARV-WRD-003": "It stands against the hallway wall, near the front door.",
    "ARV-LIV-001": "The console hangs on the wall with no legs; the wall panel covers the wall behind it from the floor; a TV hangs on the panel above the console.",
    "ARV-LIV-002": "It stands free in the room as a divider between the living area and the dining area, open from both sides.",
    "ARV-WRD-005": "It stands against the living-room wall.",
    "KIT": "The kitchen is fitted along the wall from wall to wall; the wall cabinets hang on the same wall.",
    "ARV-KIT-003": "The L-shaped kitchen is fitted into a corner of the room: both runs stand against walls.",
    "ARV-KIT-005": "The kitchen runs along the wall; the island stands free in front of it with an aisle of about 120 cm, bar stools at the island's room side.",
    "TBL": "It stands in the room with chairs around or at it.",
    "ARV-TBL-002": "It stands against the wall in a bedroom or kids' room, with a chair.",
    "ARV-TBL-004": "It stands in a home-office corner with an office chair.",
    "BTH": "The vanity frame is fixed to the bathroom wall; the faucet comes out of the wall above the basin.",
    "OFF": "It stands in the office with office chairs.",
    "ARV-OFF-005": "It stands under an office desk.",
    "ARV-OFF-006": "It stands against an office wall.",
    "ARV-OFF-004": "It stands in the office lobby facing the entrance.",
}

ROOM_HINT = {
    "bedroom": "a bedroom", "living room": "a living room", "kitchen": "a kitchen-living room", "dining area": "a dining area",
    "hallway": "an entrance hallway", "walk-in closet": "a walk-in closet", "bathroom": "a bathroom", "home office": "a home office corner",
    "office": "an office", "open-plan office": "an open-plan office", "meeting room": "a meeting room",
    "office lobby": "an office lobby", "executive office": "an executive office",
}


def placement(sku, cat):
    return PLACEMENT.get(sku) or PLACEMENT.get(cat, "")


def prompt(prod, kind, facts, cfg, ref_name, office):
    room_key = prod["room_en"]
    room = cfg["rooms"].get(room_key, "a calm modern apartment interior")
    where = "a real modern office in Almaty" if office else "a real apartment in a new residential building in Almaty"
    L = [f"Photorealistic photograph of a {prod['product_en']} taken in {where}, in {ROOM_HINT.get(room_key, room_key)}. "
         "It must look like a real photo by a professional interior photographer, not a 3D render.",
         f"REFERENCE: the attached image {ref_name} is a 3D model of this exact product made from its production drawing. "
         "Copy the product from it exactly: shape, proportions, every part and its position, the number of doors, drawers, "
         "shelves, legs and handles, the colors of each part. Do not add, remove or redesign anything on the product. "
         "Keep the same camera angle as the reference.",
         "PRODUCT (exact):"]
    L += [f"- {f}" for f in facts]
    L.append(f"PLACEMENT: {placement(prod['sku'], prod['category'])}")
    if kind == "main":
        L.append(f"SCENE: {room}. This is the main product photo: the product is the clear subject and fills about 70% of the "
                 "frame; behind it a calm warm-white wall and a light natural oak floor; at most one or two small decor items "
                 "that do not cover the product; nothing in front of it.")
    else:
        L.append(f"SCENE: {room}. This is a lifestyle interior photo: show more of the room around the product, "
                 "lived-in but tidy; the product stays fully visible and clearly the main piece of furniture.")
    L.append("LIGHT: natural daylight only, from a large window at the side; soft realistic shadows and reflections; "
             "no studio flash; true-to-life colors (white stays clean warm white, graphite stays dark grey, oak stays light "
             "natural oak, black metal stays matte black).")
    L.append("CAMERA: full-frame camera, 35–50 mm lens, eye level of a standing person or slightly above, vertical lines stay "
             "vertical, sharp focus on the product.")
    L.append("DO NOT: change the product design; add text, logos, watermarks, price tags or people; distort proportions; "
             "crop the product" + (" (a small crop at the frame edge is fine for the room)" if kind == "interior" else "") + ".")
    L.append("FORMAT: one image, vertical portrait 2:3 (1024 × 1536).")
    return "\n".join(L)


def main(out):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    (out / "референсы").mkdir(parents=True)
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    mats = json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))
    pset = json.loads((ROOT / "catalog/photo_set.json").read_text(encoding="utf-8"))
    prods = {json.loads(f.read_text(encoding="utf-8"))["sku"]: json.loads(f.read_text(encoding="utf-8"))
             for f in (ROOT / "catalog/products").glob("*.json")}
    jobs = [json.loads(l) for l in (ROOT / "work/jobs.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    base = [j for j in jobs if j["type"] == "base"]
    base.sort(key=lambda j: (CAT_ORDER.index(prods[j["sku"]]["category"]), j["sku"],
                             [c for c in pset["models"][j["sku"]]].index(next(c for c in pset["models"][j["sku"]]
                                                                              if all(c[k] == v for k, v in j["variant"].items()))),
                             j["order"]))
    manifest, blocks = {}, []
    for n, j in enumerate(base, 1):
        nn = f"{n:02d}"
        p = prods[j["sku"]]
        cfg_full = next(c for c in pset["models"][j["sku"]] if all(c[k] == v for k, v in j["variant"].items()))
        _, facts = BUILDERS[p["builder"]](cfg_full, mats)             # с подсветкой «Нимба» и т.п.
        facts = current_facts(j["sku"], facts, compile_snapshot(j["sku"], cfg_full))
        kind = "main" if j["angle"] == "hero" else "interior"
        ref_src = ROOT / j["refs"][0]
        ref_name = f"{nn}_{j['sku']}_{'главное' if kind == 'main' else 'интерьер'}.jpg"
        shutil.copy(ref_src, out / "референсы" / ref_name)
        manifest[nn] = j["job_id"]
        lab = {a["key"]: (a.get("label", a["key"]), a.get("labels", {})) for a in p["axes"]}
        ru = "; ".join(f"{lab[k][0]}: {lab[k][1].get(str(v), v)}" for k, v in cfg_full.items() if k in lab)
        blocks.append((nn, p, kind, ru, ref_name,
                       prompt(p, kind, facts, cfg, ref_name, p["category"] == "OFF")))
    (out / "gpt_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    write_task(out / "ЗАДАНИЕ_для_ChatGPT.md", blocks)
    print(f"Кадров: {len(blocks)} → {out}")
    return blocks


def write_task(path, blocks):
    n = len(blocks)
    head = f"""# Задание: фотографии мебели Arvello для сайта ({n} кадров)

Ты — фотограф-визуализатор мебельного бренда Arvello (Алматы). По каждому кадру ниже нужно сгенерировать **одну
фотореалистичную картинку** — как будто это настоящее фото мебели в реальной квартире (офисная мебель — в офисе),
снятое при естественном дневном свете.

## Главные правила
1. **Мебель — строго как на референсе.** Каждому кадру соответствует картинка-референс с тем же номером
   (например, `07_ARV-NST-001_главное.jpg`). Это 3D-модель по рабочему чертежу: форма, пропорции, количество дверей,
   ящиков, полок, ножек и ручек, их расположение и цвета деталей — **ничего не менять, не добавлять и не убирать**.
   Менять можно только окружение, свет и фактуру материалов (чтобы выглядело как фото, а не 3D).
2. **Ракурс** — как на референсе.
3. **Реалистичность:** обычная новая квартира в Алматы, не роскошный интерьер; естественный свет из окна;
   мягкие тени; настоящие текстуры (ЛДСП матовая, дуб — светлый натуральный, металл — матовый).
4. **Цвета без искажений:** белый — чистый тёплый белый, графит — тёмно-серый, кашемир — тёплый бежево-серый,
   дуб — светлый натуральный, чёрный металл — матовый чёрный.
5. **Нельзя:** текст, логотипы, водяные знаки, ценники, люди; искажать пропорции; обрезать изделие.
6. **Формат:** одна картинка на кадр, вертикальная 2:3 (1024 × 1536).
7. Типы кадров: **«главное»** — изделие крупно (≈70% кадра), спокойная стена за ним, минимум декора;
   **«интерьер»** — комната шире, изделие в жизни, но целиком видно.

## Порядок работы
- Я присылаю референсы пачками (по ~10 картинок) и пишу, какие номера делать.
- На каждый номер — **одна картинка** по его промпту ниже (промпт на английском — используй его как есть).
- Перед каждой картинкой пиши строку **«Кадр NN»**.
- Вопросов не задавай; если что-то неясно — следуй референсу.
- Если я пишу «переделай NN: …» — сделай заново этот кадр с учётом замечания, мебель по-прежнему как на референсе.

## Проверка перед тем, как показать картинку
- Число дверей / ящиков / ручек / ножек = как на референсе?
- Цвета деталей = как на референсе?
- Свет естественный, нет «студийного» вида и 3D-пластика?
- Нет текста и логотипов?

---

## Кадры
"""
    lines = [head]
    for nn, p, kind, ru, ref, pr in blocks:
        lines.append(f"### Кадр {nn} — {p['name']} — {'главное' if kind == 'main' else 'интерьер'}\n")
        lines.append(f"Исполнение: {ru}. Референс: `{ref}`\n")
        lines.append("```\n" + pr + "\n```\n")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
