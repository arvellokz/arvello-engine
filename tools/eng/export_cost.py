"""ENG-005 п. 5 · себестоимость изделия из движка (смета поставщика плиты + фурнитура по уровням).

Считает из той же модели, что листы и таблица распила (снимок один):
  плита — целыми листами: площадь деталей × 1,15 / площадь листа → вверх (как ДСП Центр: материал целыми листами);
          партия N изделий — листы делятся (ceil(N × площадь × 1,15 / лист) / N на изделие);
  кромка — материал: метры по типу и декору × 1,2 → вверх до метра (так в смете ДСП Центра 14.11); наклейка — метры × цена;
  распил — за каждый лист; присадка — опция (по умолчанию сверлит сборщик, ENG-005 п. 3): счётчик отверстий по диаметрам;
  направляющие — по уровню (эконом / стандарт / комфорт), цена за ящик; остальная фурнитура — «без цены» (не придумываем).
Цены — только из docs/поставщики/dspc/прайс_2026-11-14.json (источник у каждой). Нет цены — строка «без цены», в сумму не идёт.

    python3 tools/eng/export_cost.py SKU [key=value ...] [--batch N] [--md out.md]
    python3 tools/eng/export_cost.py --site [out.json]     (себестоимость для сайта, решение 14.11 22:55)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from eng import cab, kit13  # noqa: E402
from eng.kit13 import n_  # noqa: E402

PRICES = ROOT / "docs" / "поставщики" / "dspc" / "прайс_2026-11-14.json"
WASTE = 1.15
LEVELS = ("эконом", "стандарт", "комфорт")
# Blum и наша фурнитура уровня «по документу» у ДСП Центра не продаются: цены нет, в сумму не идёт.
SLIDE_IDS = {"SLIDES", "SLIDE-LOCK", "LOCK-SCREW", "TIPON-SYNC", "SLIDE-SCREW-M"}


def load_prices(path=PRICES):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _thick_axis(p):
    sz = {a: p[a + "1"] - p[a + "0"] for a in "xyz"}
    return min(sz, key=sz.get), sz


def base_name(s, p):
    """Наименование листа в базе поставщика для детали (по профилю модели); None — не сопоставлено."""
    S = cab.SUPPLY[s["derived"].get("supplier", {}).get("profile", "base")]
    return S["base_names"].get(p["finish"])


def drill_class(d):
    if d <= 4:
        return "le4"
    if 5 <= d <= 14:
        return "5_14"
    if d > 15:
        return "gt15"
    return None                      # Ø 4–5 и Ø 15 — в прайсе ДСП Центра не названы


def holes_by_d(s):
    """Счётчик отверстий по диаметрам (все отверстия листов цеха, включая метки направляющих)."""
    out = {}
    for h in s["holes"]:
        out[h["d"]] = out.get(h["d"], 0) + 1
    return dict(sorted(out.items()))


def cost(s, prices=None, batch=1):
    """Смета одного изделия. Возвращает dict: lines (что, кол-во, ед., цена, сумма, источник), totals по уровням, missing."""
    pr = prices or load_prices()
    lines, missing = [], []
    boards = [p for p in s["parts"] if p["kind"] == "board"]
    ext = s["derived"]["parts_ext"]
    # плита
    area = {}
    for p in boards:
        th, sz = _thick_axis(p)
        a, b = (v for k, v in sz.items() if k != th)
        nm = base_name(s, p)
        if nm is None or nm not in pr["sheets"]:
            missing.append(f"плита {p['material']} {p['finish']} ({p['unit']}) — нет в базе / прайсе поставщика")
            continue
        area[nm] = area.get(nm, 0) + a * b / 1e6
    sheets = {}
    for nm, A in area.items():
        sh = pr["sheets"][nm]
        S1 = sh["size"][0] * sh["size"][1] / 1e6
        n = math.ceil(batch * A * WASTE / S1 - 1e-9) / batch
        sheets[nm] = n
        lines.append(dict(group="материалы", what=nm, qty=n, unit="лист", price=sh["price"], sum=n * sh["price"],
                          src=sh["src"], note=f"детали {A:.2f} м² × {WASTE} / {S1:.2f} м²"))
    # кромка: материал и наклейка
    em = {}
    for p in boards:
        th, sz = _thick_axis(p)
        for f, t in ext.get(p["id"], {}).get("edges", {}).items():
            L = max(v for k, v in sz.items() if k not in (f[1], th)) / 1000
            em[(t, p["finish"])] = em.get((t, p["finish"]), 0) + L
    glue = 0.0
    for (t, fin), m in sorted(em.items()):
        glue += m
        key = f"{t}|{fin}"
        e = pr["edge"].get(key)
        if not e:
            missing.append(f"кромка {t} {fin}: {m:.2f} м — нет в прайсе")
            continue
        buy = math.ceil(m * pr["edge_buy_factor"] * batch - 1e-9) / batch
        lines.append(dict(group="материалы", what=e["name"], qty=buy, unit="м", price=e["price"], sum=buy * e["price"],
                          src=e["src"], note=f"по модели {m:.2f} м × {pr['edge_buy_factor']} → вверх"))
    w = pr["work"]
    lines.append(dict(group="работы", what="Наклейка кромки до 23 мм по прямой", qty=round(glue, 2), unit="м",
                      price=w["edging"]["price"], sum=glue * w["edging"]["price"], src=w["edging"]["src"], note=""))
    n_ldsp = sum(n for nm, n in sheets.items() if not nm.startswith("HDF"))
    n_hdf = sum(n for nm, n in sheets.items() if nm.startswith("HDF"))
    lines.append(dict(group="работы", what="Распил ЛДСП", qty=n_ldsp, unit="лист", price=w["cut_ldsp"]["price"],
                      sum=n_ldsp * w["cut_ldsp"]["price"], src=w["cut_ldsp"]["src"], note=""))
    if n_hdf:
        lines.append(dict(group="работы", what="Распил ХДФ", qty=n_hdf, unit="лист", price=w["cut_hdf"]["price"],
                          sum=n_hdf * w["cut_hdf"]["price"], src=w["cut_hdf"]["src"], note=""))
    # присадка — опция
    hd = holes_by_d(s)
    drill, drill_missing = 0, []
    for d, q in hd.items():
        c = drill_class(d)
        if c is None:
            drill_missing.append(f"Ø{n_(d)} × {q}")
        else:
            drill += q * pr["drill"][c]
    # фурнитура
    drs = s["derived"].get("drawers", [])
    nd = len(drs)
    # ENG-005 п. 2: направляющие — по профилю модели (cab.SLIDE_PROFILES), цена по артикулу; нет цены — «нет цены»
    slides, slide_note = {}, ""
    sm = [r for r in drs if r.get("sys") == "samet"]
    if sm:
        S_ = cab.SLIDE_PROFILES[sm[0]["slide"]]
        codes = sorted({cab.SLIDE_PROFILES[r["slide"]]["codes"][r["NL"]] for r in sm})
        p_ = [pr["slides"]["samet"].get(c_) for c_ in codes]
        nm = f"{S_['name']} NS {sm[0]['NL']}, арт. {', '.join(codes)}"
        if all(p_):
            slides[S_["level"]] = dict(nd=nd, name=nm, src=p_[0]["src"], price=p_[0]["price"], sum=nd * p_[0]["price"])
        else:
            slides[S_["level"]] = dict(nd=nd, name=nm, src="—", price=None, sum=None)
            slide_note = f"нет цены артикула {', '.join(codes)} в прайсе: уточнить"
        if S_["code_note"]:
            slide_note = (slide_note + "; " if slide_note else "") + S_["code_note"]
    elif drs:
        slides["Blum"] = dict(nd=nd, name="Blum (в модели) — цены нет", src="—", price=None, sum=None)
    hw_nopr = [f"{h['name']} × {n_(h['qty'])} {h.get('uom', 'шт')}" for h in s["hardware"] if h["id"] not in SLIDE_IDS]
    dspc = sum(x["sum"] for x in lines)
    totals = {lv: (round(dspc + x["sum"]) if x["sum"] is not None else None) for lv, x in slides.items()}
    return dict(lines=lines, dspc=round(dspc, 2), mat=round(sum(x["sum"] for x in lines if x["group"] == "материалы"), 2),
                work=round(sum(x["sum"] for x in lines if x["group"] == "работы"), 2), sheets=sheets,
                edge_m={f"{t}|{f}": round(m, 2) for (t, f), m in em.items()}, holes=hd, drill=drill,
                drill_missing=drill_missing, slides=slides, slide_note=slide_note, totals=totals, hw_nopr=hw_nopr, missing=missing, batch=batch,
                hash=s["hash"], sku=s["sku"])


def level_totals(sku, options, prices=None):
    """Итог по трём уровням фурнитуры: модель собирается на каждом уровне (ящик у профилей разный по ширине)."""
    out = {}
    for lv in ("eco", "std", "comf"):
        s_ = kit13.make(sku, {**options, "level": lv})
        c_ = cost(s_, prices)
        (name, x), = c_["slides"].items()
        out[name] = dict(total=c_["totals"][name], slides=x, dspc=c_["dspc"], note=c_["slide_note"])
    return out


# ------------------------------------------------------------------ себестоимость для сайта (решение 14.11, 22:55)
SITE_OUT = ROOT / "docs" / "экономика" / "себестоимость_движок.json"
SITE_SET = [  # модель, опции, подпись — что выгружаем для сайта
    *[("ARV-NST-101", {"width": "1200", "changer": ch, "level": lv}, f"комод 1200, {'со столиком' if ch == 'yes' else 'без столика'}")
      for ch in ("no", "yes") for lv in ("eco", "std", "comf")],
    ("ARV-WRD-101", {"width": "2400", "height": "2800", "depth": "450", "handle": "push", "fill": "drawers"},
     "шкаф 2400 × 2800 × 450"),
]


def drill_split(s):
    """Станковые отверстия (цена за отверстие) и то, что делает сборщик без цены: разметка под шурупы направляющих
    и пилотные Ø ≤ 3."""
    mach, mark, pilot = 0, 0, 0
    for h in s["holes"]:
        if h["kind"] == "runner_mark":
            mark += 1
        elif h["d"] <= 3:
            pilot += 1
        else:
            mach += 1
    return mach, mark, pilot


def site_entry(sku, options, label="", prices=None):
    """Строка себестоимости для сайта: плита + кромка + распил (партия), станковые отверстия, направляющие по уровню,
    сборка и доставка [М]. total_complete = False, если чего-то нет в прайсе (тогда total — нижняя граница)."""
    pr = prices or load_prices()
    S = pr["site"]
    s = kit13.make(sku, dict(options))
    c = cost(s, pr, batch=S["batch"])
    mach, mark, pilot = drill_split(s)
    missing = list(c["missing"])
    (lv, sl), = c["slides"].items() if c["slides"] else (("нет ящиков", None),)
    slides = None
    if sl and lv in LEVELS:
        slides = {"level": lv, "name": sl["name"], "qty": sl["nd"], "price": sl["price"], "sum": sl["sum"], "src": sl["src"]}
        if sl["sum"] is None:
            missing.append(f"направляющие {sl['name']}: нет цены")
    elif sl:
        lv, sl = None, None
        missing.append("внутренние ящики Blum: цены нет")
    if c["slide_note"]:
        missing.append(c["slide_note"])
    other_hw = [x for x in c["hw_nopr"]]
    blum = [h["name"] for h in s["hardware"] if "Blum" in h["spec"] and h["id"] not in SLIDE_IDS]
    if blum:
        missing.append("фурнитура Blum без цены: " + "; ".join(blum))
    drill = mach * S["drill_machine"]["price"]
    parts = {
        "plate_edge_cut": round(c["dspc"]),
        "drilling": drill,
        "slides": slides["sum"] if slides and slides["sum"] is not None else 0,
        "assembly": S["assembly"]["price"],
        "delivery": S["delivery"]["price"],
    }
    total = sum(parts.values())
    mk = S["markup"]
    from eng import bazis as BZ
    return {
        "sku": sku, "label": label, "options": dict(s["options"]), "designation": BZ.designation(s), "snapshot": s["hash"],
        "level": lv if sl else None, "batch": S["batch"],
        "parts": parts,
        "detail": {
            "sheets": c["sheets"], "edge_m": c["edge_m"], "material": round(c["mat"]), "work": round(c["work"]),
            "holes": {"machine": mach, "price_each": S["drill_machine"]["price"], "assembler_pilot_d_le_3": pilot,
                      "assembler_runner_marks": mark, "by_d": {str(k): v for k, v in c["holes"].items()}},
            "slides": slides,
            "not_priced": other_hw,
        },
        "total": total, "total_complete": not missing, "missing": missing,
        "site_price": int(math.ceil(total * mk["factor"] / mk["round_up"]) * mk["round_up"]),
    }


def site_export(path=SITE_OUT, prices=None):
    pr = prices or load_prices()
    S = pr["site"]
    items = [site_entry(sku, o, lab, pr) for sku, o, lab in SITE_SET]
    out = {
        "_comment": "Себестоимость из движка для сайта (решение владельца 14.11, 22:55). R01E — оценка, не для изготовления. "
                    "Не вошло: крепёж, ручки, уголки, упаковка. total_complete = false — чего-то нет в прайсе, total — "
                    "нижняя граница (см. missing).",
        "generated_by": "tools/eng/export_cost.py --site",
        "prices": str(PRICES.relative_to(ROOT)), "prices_date": pr["date"],
        "assumptions": {
            "batch": f"плита, кромка, распил — партия {S['batch']} изделий (листы делятся по площади, те же декоры)",
            "drilling": f"{S['drill_machine']['price']} ₸ за станковое отверстие — {S['drill_machine']['src']}; "
                        + S["drill_machine"]["rule"],
            "assembly": f"{S['assembly']['price']} ₸ — {S['assembly']['src']}",
            "delivery": f"{S['delivery']['price']} ₸ — {S['delivery']['src']}",
            "markup": S["markup"]["src"],
            "decors": "по умолчанию: корпус Белый 110 (корпус) SM, фасады Дуб Бунратти 4069",
        },
        "items": items,
    }
    Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def to_md(s, c):
    from eng import bazis as BZ
    L = [f"# Себестоимость {BZ.designation(s)} · снимок {c['hash']}", "",
         f"R01E — не для изготовления. Цены — {PRICES.relative_to(ROOT)} (розница 14.11, ориентир). "
         + (f"Партия {c['batch']} изд.: листы и кромка делятся." if c["batch"] > 1 else "Один заказ: листы целиком."), "",
         "| Статья | Кол-во | Цена, ₸ | Сумма, ₸ | Источник / расчёт |", "|---|---|---|---|---|"]
    for x in c["lines"]:
        L.append(f"| {x['what']} | {n_(round(x['qty'], 2))} {x['unit']} | {n_(x['price'])} | {n_(round(x['sum'], 2))} | "
                 f"{x['src']}{'; ' + x['note'] if x['note'] else ''} |")
    L += [f"| **Плита, кромка, распил (поставщик)** | | | **{n_(round(c['dspc']))}** | материалы {n_(round(c['mat']))} + "
          f"работы {n_(round(c['work']))} |", ""]
    L += ["| Уровень фурнитуры | Направляющие | Ящиков | Цена, ₸ | Итого с плитой, ₸ |", "|---|---|---|---|---|"]
    for lv, x in c["slides"].items():
        L.append(f"| {lv} | {x['name']} ({x['src']}) | {x['nd']} | {n_(x['price']) if x['price'] else '—'} | "
                 f"**{n_(c['totals'][lv]) if c['totals'][lv] is not None else 'нет данных'}** |")
    if c["slide_note"]:
        L += [f"**{c['slide_note'][0].upper()}{c['slide_note'][1:]}.**"]
    L += ["", f"**Присадка у поставщика (опция; по умолчанию сверлит сборщик):** {n_(c['drill'])} ₸ — отверстия "
          + ", ".join(f"Ø{n_(d)} × {q}" for d, q in c["holes"].items()) + "."]
    if c["drill_missing"]:
        L.append(f"Нет цены в прайсе (Ø 4–5 и Ø 15 не названы): {', '.join(c['drill_missing'])}.")
    L += ["", "**Не вошло (нет цены):** " + "; ".join(c["hw_nopr"]) + "; сборка, доставка, упаковка."]
    if c["missing"]:
        L += ["", "**Не сопоставлено поставщику:** " + "; ".join(c["missing"])]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--site":                    # выгрузка для сайта: docs/экономика/себестоимость_движок.json
        out = site_export(a[1] if len(a) > 1 else SITE_OUT)
        for it in out["items"]:
            tg = lambda v: f"{v:,}".replace(",", " ")
            print(f"{it['label']:28s} {it['level'] or '—':9s} {tg(it['total']):>8} ₸ "
                  f"{'' if it['total_complete'] else '(нижняя граница)':16s}  цена сайта ×1,5: {tg(it['site_price'])} ₸")
        sys.exit(0)
    batch, md = 1, None
    for flag in ("--batch", "--md"):
        if flag in a:
            i = a.index(flag)
            v = a[i + 1]
            del a[i:i + 2]
            if flag == "--batch":
                batch = int(v)
            else:
                md = v
    s = kit13.make(a[0], dict(x.split("=", 1) for x in a[1:]))
    c = cost(s, batch=batch)
    text = to_md(s, c)
    if md:
        Path(md).write_text(text, encoding="utf-8")
    print(text)
    sys.exit(1 if c["missing"] else 0)
