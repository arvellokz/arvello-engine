"""ENG-003 · таблица Excel для распила (БАЗИС-Раскрой и резчик): одна строка на деталь (позицию).

Задача из журнала 13.11 (чат, аккаунт 2): БАЗИС-Раскрой открывает список панелей из MS Excel (руководство
«Модуль БАЗИС Раскрой», п. 5.2.5; флажок «Длину и ширину считывать как готовую»), CSV в п. 5.2.1 не указан — даём .xlsx.

Колонки: поз., наименование, материал, декор, толщина, длина и ширина ГОТОВЫЕ (с кромкой), кол-во, кромка по 4 сторонам
(Д1, Д2 — стороны вдоль длины; Ш1, Ш2 — вдоль ширины; толщина и цвет), текстура, примечание (какая сторона детали где).
Длина — вдоль текстуры (у деталей с текстурой); без текстуры длина — бо́льшая сторона, деталь можно поворачивать.
Детали одного материала (плита + толщина + декор) — одним блоком, блоки разделены пустой строкой.

Сверка (check_vs_csv): позиции, названия, кол-во, материал и готовые размеры = CSV выпуска того же снимка модели;
число облицованных сторон и метры кромки = модели. Расхождение — ошибка выпуска.

    python3 tools/eng/export_cutting.py SKU out.xlsx [key=value ...] [--csv выпуск.csv]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import bazis as BZ  # noqa: E402
from eng import kit13  # noqa: E402,F401  регистрирует все модели
from eng.boardkit import EDGE_TXT, NAME, dot, vec  # noqa: E402
from eng.kit13 import MAT_RU, fin_ru, n_, positions  # noqa: E402

COLS = ["Поз.", "Наименование", "Материал", "Декор", "Толщина, мм", "Длина, мм", "Ширина, мм", "Кол-во",
        "Кромка Д1", "Кромка Д2", "Кромка Ш1", "Кромка Ш2", "Текстура", "Примечание"]
WIDTHS = [6, 44, 10, 24, 11, 10, 10, 8, 20, 20, 20, 20, 22, 44]
EDGE_RU = {"ABS2": "ABS 2", "PVC04": "ПВХ 0,4"}


def _r(x):
    x = round(x, 3)
    return int(x) if x == int(x) else x


def part_row(s, ps, ids):
    """Строка таблицы для позиции: из модели (панель первой детали позиции), не из спецификации."""
    pid = ids[0]
    p = next(q for q in s["parts"] if q["id"] == pid)
    P = BZ.panel_data(s, pid)
    fr = P["fr"]
    deco = fin_ru(p["finish"], p["kind"])
    grain = P["grain"]
    if grain:
        along_u = abs(dot(vec("+" + grain), fr.right)) == 1
    else:
        along_u = fr.Lu >= fr.Lv
    L, W = (fr.Lu, fr.Lv) if along_u else (fr.Lv, fr.Lu)
    sides = {e["side"]: e for e in P["edges"]}
    d_sides, w_sides = (("T", "B"), ("L", "R")) if along_u else (("L", "R"), ("T", "B"))
    d_sides, w_sides = (tuple(sorted(pr, key=lambda sd: sd not in sides)) for pr in (d_sides, w_sides))  # кромка — в 1-ю
    cells, where = [], []
    for code, sd in zip(("Д1", "Д2", "Ш1", "Ш2"), d_sides + w_sides):
        e = sides.get(sd)
        if e:
            cells.append(f"{EDGE_RU[e['typ']]}, в цвет {deco}")
            where.append(f"{code} — {NAME[e['face']]}")
        else:
            cells.append("")
    note = ("кромка: " + ", ".join(where)) if where else "без кромки"
    return dict(pos=ps, name=p["unit"], mat=MAT_RU.get(p["material"], p["material"]), deco=deco, t=_r(fr.t),
                L=_r(L), W=_r(W), qty=len(ids), edges=cells, n_edges=len(P["edges"]),
                edge_m={t: sum(e["L"] for e in P["edges"] if e["typ"] == t) * len(ids) / 1000 for t in EDGE_TXT},
                grain="вдоль длины" if grain else "нет (можно поворачивать)", note=note)


def cutting_rows(s):
    """Строки по позициям-панелям, сгруппированные по материалу (в порядке первого появления), внутри — по позициям."""
    _, rep, _ = positions(s)
    rows = [part_row(s, ps, ids) for ps, ids in rep
            if next(q for q in s["parts"] if q["id"] == ids[0])["kind"] == "board"]
    blocks = {}
    for r in rows:
        blocks.setdefault((r["mat"], r["deco"]), []).append(r)
    return list(blocks.values())


def write_xlsx(path, s, blocks=None):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    blocks = blocks if blocks is not None else cutting_rows(s)
    wb = Workbook()
    ws = wb.active
    ws.title = "Раскрой"
    ws.append([f"Обозначение: {BZ.designation(s)}", None, None, None, f"Снимок: {s['hash']}", None, None, None,
               "R01E — не для изготовления. Размеры — ГОТОВЫЕ, с кромкой."])
    ws["A1"].font = ws["E1"].font = ws["I1"].font = Font(bold=True)
    ws.append([])
    ws.append(COLS)
    thin = Side(style="thin", color="999999")
    for c in ws[3]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="E8E8E8")
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
    for i, blk in enumerate(blocks):
        if i:
            ws.append([])
        for r in blk:
            ws.append([r["pos"], r["name"], r["mat"], r["deco"], r["t"], r["L"], r["W"], r["qty"], *r["edges"],
                       r["grain"], r["note"]])
    for i, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"
    info = wb.create_sheet("О таблице")
    for line in [
        f"Изделие: {BZ.designation(s)} · снимок модели {s['hash']} (тот же, что на листах A3 и в CSV выпуска).",
        "Статус: R01E — не для изготовления, не утверждено.",
        "Длина и ширина — готовые размеры детали с кромкой (в БАЗИС-Раскрое: «Длину и ширину считывать как готовую»).",
        "Длина — вдоль текстуры. «Текстура: нет» — деталь без рисунка, можно поворачивать при раскрое.",
        "Д1, Д2 — кромка на сторонах вдоль длины; Ш1, Ш2 — на сторонах вдоль ширины. В примечании — где сторона на изделии.",
        "Кромка ABS 2 и ПВХ 0,4 — в цвет декора детали. Пустая ячейка — сторона без кромки.",
        "Блоки — по материалу (плита, толщина, декор), разделены пустой строкой.",
        "Отверстия и пазы — на листах A3 для цеха (в этой таблице их нет).",
    ]:
        info.append([line])
    info.column_dimensions["A"].width = 120
    wb.save(path)
    return blocks


# ------------------------------------------------------------------ сверка с CSV выпуска
def read_csv_parts(path):
    """Строки деталей CSV выпуска (до первой пустой строки) и снимок из заголовка."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    snap = rows[0][1].split(":", 1)[1].strip()
    out = []
    for r in rows[2:]:
        if not r or not any(x.strip() for x in r):
            break
        if len(r) > 5 and r[5].strip():        # деталь — с заготовкой; покупные идут в той же таблице без заготовки
            out.append(r)
    return snap, out


def _thick_axis(p):
    sz = {a: p[a + "1"] - p[a + "0"] for a in "xyz"}
    return min(sz, key=sz.get)


def plast_edges(s):
    """Кромка, назначенная в модели на пласть (не на торец): на листах её нет, но метры кромки она завышает."""
    out = []
    for p in s["parts"]:
        th = _thick_axis(p) if p["kind"] == "board" else None
        for f, t in s["derived"]["parts_ext"].get(p["id"], {}).get("edges", {}).items():
            if f[1] == th:
                out.append((p["id"], p["unit"], f, t))
    return out


def model_edge_m(s):
    """Метры кромки по модели, только торцы (как derived edge_*_m, но без кромки на пласти)."""
    m = {t: 0.0 for t in EDGE_TXT}
    for p in s["parts"]:
        if p["kind"] != "board":
            continue
        th = _thick_axis(p)
        sz = {a: p[a + "1"] - p[a + "0"] for a in "xyz"}
        for f, t in s["derived"]["parts_ext"].get(p["id"], {}).get("edges", {}).items():
            if f[1] != th:
                m[t] += max(v for a, v in sz.items() if a not in (f[1], th)) / 1000
    return m


def _dims(txt):
    return sorted(float(x.strip().replace(",", ".")) for x in txt.split("×"))


def check_vs_csv(s, blocks, csv_path):
    """Возвращает список расхождений таблицы распила с CSV выпуска и с моделью (пустой — совпадает)."""
    bad = []
    snap, crow = read_csv_parts(csv_path)
    if snap != s["hash"]:
        bad.append(f"снимок CSV {snap} ≠ снимок модели {s['hash']}")
    rows = [r for b in blocks for r in b]
    xs = {str(r["pos"]): r for r in rows}
    cs = {r[0]: r for r in crow}
    if len(xs) != len(rows):
        bad.append("в таблице распила позиция повторяется")
    for p_ in sorted(set(cs) - set(xs), key=int):
        bad.append(f"поз. {p_} есть в CSV, нет в таблице распила")
    for p_ in sorted(set(xs) - set(cs), key=int):
        bad.append(f"поз. {p_} есть в таблице распила, нет в CSV")
    for p_ in sorted(set(xs) & set(cs), key=int):
        x, c = xs[p_], cs[p_]
        if x["name"] != c[1]:
            bad.append(f"поз. {p_}: название «{x['name']}» ≠ CSV «{c[1]}»")
        if str(x["qty"]) != c[2].strip():
            bad.append(f"поз. {p_}: кол-во {x['qty']} ≠ CSV {c[2]}")
        if f"{x['mat']} {x['deco']}" != c[3]:
            bad.append(f"поз. {p_}: материал «{x['mat']} {x['deco']}» ≠ CSV «{c[3]}»")
        if any(abs(a - b) > 0.01 for a, b in zip(sorted([x["L"], x["W"], x["t"]]), _dims(c[4]))):
            bad.append(f"поз. {p_}: размер {n_(x['L'])} × {n_(x['W'])} × {n_(x['t'])} ≠ CSV {c[4]}")
    if sum(r["qty"] for r in rows) != sum(int(c[2]) for c in crow if c[2].strip().isdigit()):
        bad.append("общее число деталей ≠ CSV")
    for blk in blocks:
        if len({(r["mat"], r["deco"]) for r in blk}) != 1:
            bad.append("в одном блоке разные материалы")
    if len({(b[0]["mat"], b[0]["deco"]) for b in blocks}) != len(blocks):
        bad.append("один материал разбит на несколько блоков")
    for r in rows:
        if sum(1 for e in r["edges"] if e) != r["n_edges"]:
            bad.append(f"поз. {r['pos']}: кромка в таблице не на всех облицованных сторонах")
    mm = model_edge_m(s)
    for t in EDGE_TXT:
        m = sum(r["edge_m"][t] for r in rows)
        if abs(m - mm[t]) > 0.02:
            bad.append(f"кромка {EDGE_TXT[t]}: {m:.2f} м в таблице ≠ {mm[t]:.2f} м в модели (торцы)")
    return bad


def check_xlsx_file(path, blocks):
    """Файл: блоки разделены ровно одной пустой строкой, строк деталей столько же, сколько позиций."""
    from openpyxl import load_workbook
    ws = load_workbook(path)["Раскрой"]
    vals = [[c.value for c in r] for r in ws.iter_rows(min_row=4)]
    bad = []
    got, cur = [], []
    for v in vals:
        if all(x is None for x in v):
            if cur:
                got.append(cur)
            cur = []
        else:
            cur.append(v)
    if cur:
        got.append(cur)
    if [len(b) for b in got] != [len(b) for b in blocks]:
        bad.append(f"в файле блоки {[len(b) for b in got]} ≠ {[len(b) for b in blocks]}")
    if any(all(x is None for x in a) and all(x is None for x in b) for a, b in zip(vals, vals[1:])):
        bad.append("в файле две пустые строки подряд")
    return bad


def export(sku, out, options=None, csv_path=None):
    s = kit13.make(sku, options)
    blocks = write_xlsx(out, s)
    bad = check_xlsx_file(out, blocks)
    if csv_path:
        bad += check_vs_csv(s, blocks, csv_path)
    return s, blocks, bad, plast_edges(s)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:]]
    cp = None
    if "--csv" in a:
        i = a.index("--csv")
        cp = a[i + 1]
        del a[i:i + 2]
    s, blocks, bad, warn = export(a[0], a[1], dict(x.split("=", 1) for x in a[2:]), cp)
    print(f"{a[0]} {s['rev']} {s['hash']}: {sum(len(b) for b in blocks)} поз. в {len(blocks)} блоках → {a[1]}")
    for w in warn:
        print("ВНИМАНИЕ: кромка на пласти в модели (в таблицу не попала):", *w)
    for b in bad:
        print("FAIL", b)
    sys.exit(1 if bad else 0)
