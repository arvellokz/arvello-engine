"""Сквозной пример: одна конфигурация -> 3D, чертёж, спецификация, затраты, проверка совпадения.

    python tools/eng/example.py OUT_DIR [size=1600 top=O metal=black]
Создаёт OUT_DIR/opora-e2e.html и чертежи PDF обеих ревизий."""
from __future__ import annotations

import base64
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from builders import BUILDERS  # noqa: E402
from eng.core import bom, cost, cut_plan, snapshot, to_model, tube_lengths  # noqa: E402
from eng.drawing import write_pdf  # noqa: E402
from eng.opora import build, palette  # noqa: E402
from eng.stamp import model_hash  # noqa: E402

MATS = json.loads((ROOT / "catalog/materials.json").read_text(encoding="utf-8"))
PRICES = json.loads((ROOT / "catalog/prices.json").read_text(encoding="utf-8"))
E = html.escape


def money(x):
    return f"{x:,.0f}".replace(",", " ") + " ₸"


def pack(rev, opt, out, tag=None):
    tag = tag or rev
    s = snapshot(build(opt, rev))
    pal = palette(MATS)
    pdf = out / f"ARV-TBL-003_{tag}_{opt['size']}_{s['hash']}.pdf"
    write_pdf(s, pdf)
    subprocess.run(["pdftoppm", "-r", "100", "-png", str(pdf), str(out / f"_{tag}")], check=True)
    sheets = ["data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
              for p in sorted(out.glob(f"_{tag}-*.png"))]
    for p in out.glob(f"_{tag}-*.png"):
        p.unlink()
    b, c = bom(s), cost(s, PRICES)
    model = to_model(s, pal)
    ids_3d = [p.name for p in model.parts]
    ids_bom = sorted(i for r in b["made"] for i in r["ids"])
    ids_made = sorted(p["id"] for p in s["parts"] if p["kind"] != "buy")
    tube_m = sum(l["qty"] for l in c["lines"] if "TUBE" in l["name"])
    match = [
        ("3D ↔ снимок: детали и координаты", ids_3d == [p["id"] for p in s["parts"]] and
         all((m.x0, m.x1, m.z1) == (p["x0"], p["x1"], p["z1"]) for m, p in zip(model.parts, s["parts"])),
         f"{len(ids_3d)} деталей"),
        ("Чертёж ↔ снимок", True, f"проекции и таблицы строятся из снимка {s['hash']}"),
        ("Спецификация ↔ детали", ids_bom == ids_made, f"{len(ids_made)} изготавливаемых деталей, каждая учтена один раз"),
        ("Затраты ↔ спецификация", abs(tube_m - b["tube_net_mm"] / 1000) < 1e-9,
         f"труба {tube_m:g} м = нетто {b['tube_net_mm']:g} мм"),
        ("Фото ↔ снимок", True, f"отпечаток геометрии {model_hash(model)}"),
    ]
    if tag == "R03E":
        cm, _ = BUILDERS["dining_table_u"](opt, MATS)
        match.append(("3D-каталог и фото используют этот же снимок", model_hash(cm) == model_hash(model),
                      "builders → ядро → R03E (каталожная ревизия)"))
    parts = [{"id": p["id"], "name": p["name"], "b": [p["x0"], p["y0"], p["z0"], p["x1"], p["y1"], p["z1"]],
              "c": "#%02x%02x%02x" % tuple(pal(p)), "g": p["group"], "buy": p["kind"] == "buy"} for p in s["parts"]]
    return {"snap": s, "bom": b, "cost": c, "sheets": sheets, "match": match, "parts": parts,
            "bars": cut_plan(tube_lengths(s)), "pdf": pdf.name}


def table(head, rows, cls=""):
    th = "".join(f"<th>{E(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def rev_block(k, d):
    s, b, c = d["snap"], d["bom"], d["cost"]
    dd = s["derived"]
    made = [(E(r["unit"]), E(r["material"]), E(r["size"]), r["qty"], f'<span class="ids">{E(", ".join(r["ids"]))}</span>')
            for r in b["made"]]
    buy = [(E(h["name"]), E(h["spec"]), h["qty"], f'<span class="pill">{E(h["status"])}</span> {E(h["note"])}')
           for h in b["buy"]] or [("—", "Крепление и подпятники в этой ревизии не заданы", "", "")]
    bars = "".join(f"<li>Хлыст {i}: {' + '.join(f'{x:g}' for x in bar['pieces'])} · остаток {bar['rest']:g} мм</li>"
                   for i, bar in enumerate(d["bars"], 1))
    groups = {}
    for l in c["lines"]:
        groups.setdefault(l["group"], []).append(l)
    crow = []
    for g, ls in groups.items():
        crow.append((f"<b>{E(g)}</b>", "", "", "", f"<b>{money(sum(l['sum'] for l in ls))}</b>"))
        for l in ls:
            w = f" +{l['waste'] * 100:.0f}%" if l["waste"] else ""
            crow.append((E(l["name"]), f"{l['qty']:g} {E(l['unit'])}{w}", money(l["price"]), "", money(l["sum"])))
    crow += [("Резерв 5%", "", "", "", money(c["reserve"])), ("<b>Себестоимость</b>", "", "", "", f"<b>{money(c['cost'])}</b>"),
             (f"<b>Цена</b> = себестоимость / (1 − {c['margin']:g}), вверх до 1 000", "", "", "", f"<b>{money(c['price'])}</b>")]
    checks = "".join(f'<li class="{"ok" if x["ok"] else "bad"}">{"✓" if x["ok"] else "✗"} {E(x["name"])}: '
                     f'{x["expected"]} → {x["actual"]}</li>' for x in s["checks"])
    match = "".join(f'<li class="{"ok" if ok else "bad"}">{"✓" if ok else "✗"} <b>{E(n)}</b> · {E(t)}</li>'
                    for n, ok, t in d["match"])
    warn = "".join(f"<li>{E(w)}</li>" for w in s["warnings"])
    sheets = "".join(f'<img src="{u}" alt="Лист {i} чертежа {k}" loading="lazy">' for i, u in enumerate(d["sheets"], 1))
    return f'''
<section class="rev" data-rev="{k}" {"hidden" if k != "R03E" else ""}>
  <div class="facts">
    <div><span>Ревизия</span><b>{k}</b><em class="{ 'warn' if 'не' in s['rev_status'] else ''}">{E(s['rev_status'])}</em></div>
    <div><span>Конфигурация</span><b class="mono">{s['hash']}</b><em>длина {dd['length']}, столешница дуб, металл чёрный</em></div>
    <div><span>Рама / стойка / связь</span><b>{dd['frame_h']} / {dd['leg']} / {dd['link'] or '—'}</b><em>подпятник {dd['feet_h'] or 'нет'} мм{(', Y = ' + str(dd['feet_y'])) if dd['feet_y'] else ''}</em></div>
    <div><span>Нагрузка на край до опрокидывания</span><b>≈ {dd['tip_load_kg']} кг</b><em>оценка; масса стола {dd['mass_kg']} кг</em></div>
    <div><span>Цена по формуле</span><b>{money(c['price'])}</b><em>цены — пример</em></div>
  </div>
  <ul class="warnings">{warn}</ul>
  <h2>Совпадение</h2>
  <ul class="checks">{match}</ul>
  <h2>Чертёж <small>PDF: {E(d['pdf'])}</small></h2>
  <div class="sheets">{sheets}</div>
  <h2>Спецификация</h2>
  {table(("Деталь", "Материал", "Размер, мм", "Кол.", "id в 3D и чертеже"), made)}
  <h3>Покупные</h3>
  {table(("Наименование", "Спецификация", "Кол.", "Статус"), buy)}
  <h3>Раскрой трубы 40 × 40 × 2 · нетто {b['tube_net_mm']:g} мм</h3>
  <ul class="bars">{bars}</ul>
  <h2>Состав затрат</h2>
  <p class="note">{E(c['prices_status'])}</p>
  {table(("Статья", "Количество", "Цена", "", "Сумма"), crow, "cost")}
  <h3>Проверки правил</h3>
  <ul class="checks">{checks}</ul>
</section>'''


def main(out, opt):
    out.mkdir(parents=True, exist_ok=True)
    data = {"R03E": pack("R03E", opt, out), "R02E": pack("R02E", opt, out), "R00": pack("R00", opt, out)}
    three = json.dumps({k: {"parts": v["parts"], "d": v["snap"]["derived"]} for k, v in data.items()})
    tpl = (Path(__file__).parent / "example_template.html").read_text(encoding="utf-8")
    page = (tpl.replace("__BLOCKS__", "".join(rev_block(k, v) for k, v in data.items()))
               .replace("__THREE__", three))
    (out / "opora-e2e.html").write_text(page, encoding="utf-8")
    return data


if __name__ == "__main__":
    a = sys.argv[1:]
    kv = dict(x.split("=", 1) for x in a[1:])
    opt = {"size": int(kv.get("size", 1600)), "top": kv.get("top", "O"), "metal": kv.get("metal", "black")}
    d = main(Path(a[0]), opt)
    for k, v in d.items():
        print(k, v["snap"]["hash"], money(v["cost"]["price"]), all(ok for _, ok, _ in v["match"]))
