"""Проверки новых моделей (с 12.11.2026) по разбору ARV-WRD-101 R01E, снимок 0e0f07487367a6f2.

verify_new(s, texts) -> [(проверка, статус, подробности)], статус: "пройдено" | "ошибка" | "требует данных".
Каждая проверка пересчитывает величину по снимку независимо от правил, которыми снимок построен.
texts — все надписи листов комплекта (для проверок текста сборки и контроля).
"""
from __future__ import annotations

import re

OK, ERR, DATA = "пройдено", "ошибка", "требует данных"

# Согласованные наборы «планка — отверстие — крепёж» (Blum CLIP, планки крестообразные 0 мм)
# Каталог Blum 2024/25 с. 152–154 (docs/blum/2026-11-12_TANDEM_петли_TIP-ON-двери.md, п. 2.2):
# евровинты Ø6 предустановлены только у 173L8100; 173H7100, 175H7100, 173L6100 — под саморезы Ø3,5 / Ø4, не под Ø5.
PLATE_SET = {
    "173L8100": {"d": 5.0, "fast": "SCREW-6.3x13", "txt": "системные винты Ø6 предустановлены, Ø5 гл. 13"},
    "173H7100": {"d": None, "fast": "SCREW-4x?", "txt": "саморезы Ø3,5 / Ø4, без отверстий Ø5"},
    "175H7100": {"d": None, "fast": "SCREW-4x?", "txt": "саморезы Ø3,5 / Ø4, без отверстий Ø5"},
    "173L6100": {"d": None, "fast": "SCREW-4x?", "txt": "саморезы Ø3,5 / Ø4, без отверстий Ø5"},
}
SCREW_ON_CUPS = ("71B3550", "70T3550")       # чашка на саморезах: 2 самореза, схема 45 / 9,5
PUSH_GAP_MIN = 2.0                           # кандидат: зазор дверь — корпус под TIP-ON (В-104)
PLATE_DEFAULT = {"y": 61, "protr": 11, "dz": 25}


def _len(fid):
    m = re.search(r"x(\d+)", fid or "")
    return float(m.group(1)) if m else None


def _ov(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def verify_new(s, texts):
    out = []
    add = lambda n, st, t: out.append((n, st, str(t)))
    P = {p["id"]: p for p in s["parts"]}
    H = {h["id"]: h for h in s["hardware"]}
    holes = s["holes"]
    d = s["derived"]
    T = " ".join(texts)
    boards = [p for p in s["parts"] if p["kind"] == "board"]
    carc = [p for p in boards if p["group"] == "carcass"]
    doors = [p for p in boards if p["group"] == "fronts" and "DOOR" in p["id"]]

    # 1. Ход двери без ручки (TIP-ON): зазор между закрытой дверью и передней кромкой корпуса
    if s["options"].get("handle") == "push" and doors:
        bad = []
        for dr in doors:
            near = [c["y0"] for c in carc if _ov(c["x0"], c["x1"], dr["x0"], dr["x1"]) > 1
                    and _ov(c["z0"], c["z1"], dr["z0"], dr["z1"]) > 1]
            g = min(near) - dr["y1"] if near else 99
            if g < PUSH_GAP_MIN - 0.01:
                bad.append(f"{dr['id']}: {g:g}")
        add("Дверь TIP-ON: зазор дверь — корпус ≥ 2 (кандидат В-104)", ERR if bad else OK,
            "у всех дверей ≥ 2" if not bad else f"зазор {bad[0]} мм, ход нажатия 0; всего {len(bad)} дв.")
        lines = [h for k, h in H.items() if "TIP-ON" in h["name"] and "двер" in h["name"]]
        tall = [dr for dr in doors if dr["z1"] - dr["z0"] > 1300]
        sprung = "71B" in H.get("HINGE", {}).get("spec", "") or "BLUMOTION" in H.get("HINGE", {}).get("spec", "")
        if sprung:                                  # петля с пружиной: только 956A1006, по одному на каждую дверь
            okv = all("956A1006" in h["spec"] for h in lines) and sum(h["qty"] for h in lines) >= len(doors)
        else:
            okv = all(any("956A" in h["spec"] for h in lines) for _ in tall[:1]) and (not any(
                dr["z1"] - dr["z0"] <= 1300 for dr in doors) or any("956.1" in h["spec"] for h in lines))
        add("TIP-ON двери: версия по высоте двери (длинная > 1300, короткая ≤ 1300)", OK if okv else ERR,
            ", ".join(f"{h['spec'][:40]}… × {h['qty']}" for h in lines) or "нет строк TIP-ON для дверей")

    # 2. Петля, планка и крепёж — из одного набора
    hs = H.get("HINGE", {}).get("spec", "")
    plate = next((k for k in PLATE_SET if k in hs), None)
    ph = [h for h in holes if h["kind"] == "hinge_plate"]
    if ph:
        if not plate:
            add("Петля: планка — отверстие — крепёж из одного набора", DATA, f"артикул планки не распознан: {hs[:60]}")
        else:
            rule = PLATE_SET[plate]
            wrong = [h["id"] for h in ph if rule["d"] is None or abs(h["d"] - rule["d"]) > 0.01 or h.get("fastener") != rule["fast"]]
            add("Петля: планка — отверстие — крепёж из одного набора", ERR if wrong else OK,
                f"{plate}: {rule['txt']}; " + (f"{len(ph)} отв. совпадают" if not wrong else
                                               f"{len(wrong)} отв. Ø5 под евровинт не подходят к планке"))
    cups = [h for h in holes if h["kind"] == "hinge_cup"]
    if cups:
        need = any(a in hs for a in SCREW_ON_CUPS)
        cs = [h for h in holes if h["kind"] == "hinge_cup_screw"]
        miss = []
        for c in cups:
            n = sum(1 for h in cs if h["part"] == c["part"] and abs(h["z"] - c["z"]) <= 23 and abs(h["x"] - c["x"]) <= 10
                    and abs(abs(h["z"] - c["z"]) - 22.5) < 0.1 and abs(abs(h["x"] - c["x"]) - 9.5) < 0.1) \
                + sum(1 for h in cs if h["part"] == c["part"] and abs(h["x"] - c["x"]) <= 23 and abs(h["z"] - c["z"]) <= 10
                      and abs(abs(h["x"] - c["x"]) - 22.5) < 0.1 and abs(abs(h["z"] - c["z"]) - 9.5) < 0.1)
            if need and n != 2:
                miss.append(c["id"])
        q = H.get("SCREW-3.5x15", {}).get("qty", 0)
        bad = bool(miss) or (need and q != 2 * len(cups))
        add("Чашка петли на саморезах: 2 отверстия по схеме 45 / 9,5, саморезы в спецификации", ERR if bad else OK,
            f"чашек {len(cups)}, без крепежа {len(miss)}, саморезов 3,5 × 15 в спецификации {q}")

    # 3. Внутренний ящик за дверью: проход мимо планки и плеча петли
    env = d.get("plate_env") or PLATE_DEFAULT
    drs = d.get("drawers", [])
    if drs and doors:
        clash, worst = [], 1e9
        for r in drs:
            box = [P[i] for i in r["box"] if i in P]
            fr = P[r["front"]]
            bz0, bz1 = min(b["z0"] for b in box), max(b["z1"] for b in box)
            for dh in [h for h in holes if h["kind"] == "hinge_plate"]:
                S = P[dh["part"]]
                if not (S["x0"] - 1 <= fr["x0"] <= S["x1"] + 700 or S["x0"] - 700 <= fr["x1"] <= S["x1"] + 1):
                    continue
                if _ov(bz0, bz1, dh["z"] - env["dz"], dh["z"] + env["dz"]) <= 0 and \
                        _ov(fr["z0"], fr["z1"], dh["z"] - env["dz"], dh["z"] + env["dz"]) <= 0:
                    continue
                if not (_ov(S["y0"], S["y1"], fr["y0"], box[0]["y1"]) > 0):
                    continue
                inner = S["x1"] if dh["dir"] == "-x" else S["x0"]
                parts_x = [min(abs(q["x0"] - inner), abs(q["x1"] - inner)) for q in box + [fr]
                           if _ov(q["y0"], q["y1"], S["y0"], S["y1"]) > 0]
                cl = min(parts_x) - env["protr"]
                worst = min(worst, cl)
                if cl < 3:
                    clash.append(f"{r['pre']}ящ.{r['n']} — {S['id']} z {dh['z']:g}: {cl:g}")
        add("Ящик за дверью: короб и панель проходят мимо планки петли (≥ 3 при выступе 11, кандидат В-105)",
            ERR if clash else OK, f"мин. зазор {worst:g} мм" if not clash else f"{clash[0]}; всего {len(clash)}")
        sp = [p for p in boards if "SPACER" in p["id"]]
        cut = []
        for p in sp:
            side = [c for c in carc if c["name"].startswith("Боковина") and _ov(c["z0"], c["z1"], p["z0"], p["z1"]) > 0
                    and (abs(c["x1"] - p["x0"]) < 0.1 or abs(c["x0"] - p["x1"]) < 0.1)]
            for S in side:
                for dh in [h for h in holes if h["kind"] == "hinge_plate" and h["part"] == S["id"]]:
                    if p["z0"] < dh["z"] + env["dz"] and dh["z"] - env["dz"] < p["z1"] and p["y0"] < S["y0"] + env["y"]:
                        cut.append(p["id"])
        if sp:
            add("Проставка не заходит на планку петли", ERR if cut else OK, "нет" if not cut else cut[:3])
        add("Ящик за открытой дверью 110°: траектория двери и плеча петли", DATA,
            "контура петли 70T3550 / 71B3550 нет — проверить на образце (В-105)")
        for r in drs:
            fr = P[r["front"]]
            if fr["y0"] > 1 and (r["pre"], r["n"]) == (drs[0]["pre"], drs[0]["n"]):
                back = max(c["y1"] for c in carc if c["name"].startswith("Боковина"))
                need = r["NL"] + (fr["y1"] - fr["y0"]) + 7
                add("Внутренний ящик Blum: место от передней панели NL + X + 7", OK if back - fr["y0"] >= need else ERR,
                    f"{r['NL']:g} + {fr['y1'] - fr['y0']:g} + 7 = {need:g} ≤ {back - fr['y0']:g}; длина с панелью "
                    f"{r['box_l'] + fr['y1'] - fr['y0']:g}")

    # 4. Зазор внутренних передних панелей — из модели и в тексте сборки
    inner = sorted([p for p in boards if p["name"].startswith("Передняя панель внутреннего")], key=lambda p: (p["x0"], p["z0"]))
    gaps = sorted({round(b["z0"] - a["z1"], 1) for a, b in zip(inner, inner[1:]) if abs(a["x0"] - b["x0"]) < 0.1})
    if gaps:
        said = all(re.search(rf"внутренн[^.;]*зазор {g:g}\b", T) for g in gaps)
        add("Зазор внутренних передних панелей: в тексте = в модели", OK if said else ERR,
            f"модель {', '.join(f'{g:g}' for g in gaps)} мм; " + ("в шагах и контроле указан" if said else "в тексте 3 мм / не указан"))

    # 5. Допуск деталей короба согласован с допуском внутренней ширины (Blum LW − 42, +0 / −1,5)
    if drs:
        k4 = re.search(r"внутренняя ширина[^|]*?(\d+(?:,\d)?) \+0 / −1,5", T)
        spec = re.search(r"[Сс]тенки и дно короба[^.]*?−0,5 / \+0", T)
        add("Допуск стенок короба внутри допуска короба (К1 ↔ К4)", OK if spec else ERR,
            "стенки −0,5 / +0 при коробе +0 / −1,5" if spec else "общий ±0,5 допускает стенку +0,4 — короб вне +0 / −1,5")

    # 6. Саморез через деталь в пласть: направление, зацепление, остаток
    bad, n = [], 0
    for j, ids in d.get("joints", {}).items():
        hj = [h for h in holes if h["id"] in set(ids)]
        thr = [h for h in hj if h["kind"] == "screw_face"]
        pil = [h for h in hj if h["kind"] == "pilot"]
        for h in thr:
            L = _len(h.get("fastener"))
            mate = next((q for q in pil if q["dir"] == h["dir"] and all(abs(q[k] - h[k]) < 0.1 for k in "xyz" if k != h["dir"][1])),
                        None)
            if not L or not mate:
                continue
            n += 1
            ax = h["dir"][1]
            E = P[mate["part"]]
            tE = E[ax + "1"] - E[ax + "0"]
            eng = L - h["depth"]
            rest = tE - eng
            if eng < 6 or rest < 3 or mate["depth"] > eng + 0.01:
                bad.append(f"{h.get('fastener')} {h['part']}→{E['id']}: вход {eng:g}, остаток {rest:g}")
    if n:
        add("Саморез сквозь деталь в пласть: вход ≥ 6, остаток ≥ 3, засверловка ≤ входа", ERR if bad else OK,
            f"{n} саморезов" if not bad else f"{bad[0]}; всего {len(bad)}")
    for k, h in H.items():
        m = re.search(r"вход в ([а-я ]+?) (\d+)", h["spec"])
        if m and k.startswith("SCREW-4x25M"):
            ok = "дно антресоли" in h["spec"] and m.group(2) == "9"
            add("Текст крепежа антресоли = соединению", OK if ok else ERR, h["spec"])
        if m and k == "SCREW-4x30M":
            add("Текст крепежа антресоли = соединению", ERR, f"«{h['spec']}», а винт идёт из крышки в дно антресоли")

    # 7. Монтаж: крепление к стене есть в порядке сборки
    if "WALL-ANGLE" in H:
        ok = re.search(r"\d+\.[^.]*к стене", T) is not None
        add("Порядок сборки: крепление к стене до навески дверей", OK if ok else ERR,
            "шаг есть" if ok else "уголки в спецификации, шага крепления нет")
    lv = d.get("levels")
    if lv and d.get("ceiling_gap"):
        Hh = s["options"].get("height")
        okh = lv[-1] == Hh and f"{Hh + 40}" in T
        add("Высота изделия и проёма разделены (потолок ≥ H + 40, В-102)", OK if okh else ERR,
            f"изделие {Hh}, проём ≥ {Hh + 40}" if okh else "в листах нет высоты проёма")

    # 8. Лишние шаги и ссылки
    words = []
    mods = set(d.get("modules", []))
    if "CASTER" not in H and re.search(r"колёс", T):
        words.append("колёса")
    if not any("TOP28" in p["material"] or "TOP38" in p["material"] for p in boards) and re.search(r"столешниц", T):
        words.append("столешница")
    if "kitchen_set" not in mods and re.search(r"кухн", T):
        words.append("кухня")
    add("В листах нет шагов и ссылок чужих изделий", ERR if words else OK, "нет" if not words else ", ".join(words))
    steps_k = set(re.findall(r"[Дд]иагонали[^.]*?\((К\d+(?:, К\d+)*)\)", T))
    cited = {k for grp in steps_k for k in grp.split(", ")}
    diag_rows = set(re.findall(r"(К\d+)\s+[^К|]{0,40}?диагонали по фасадной", T))
    okk = bool(cited) and diag_rows <= cited
    add("Шаг выставления диагоналей ссылается на все строки контроля корпусов", OK if okk else ERR,
        f"шаг: {', '.join(sorted(cited)) or '—'}; строки: {', '.join(sorted(diag_rows)) or '—'}")

    # 10. Доступ инструмента: вход корпуса эксцентрика, головки самореза и конфирмата не закрыт другой деталью
    blocked = []
    for h in holes:
        if h["kind"] not in ("ecc_housing", "screw_face", "conf_face"):
            continue
        ax = h["dir"][1]
        sgn = -1 if h["dir"][0] == "+" else 1               # наружу — против направления сверления
        q = {k: h[k] for k in "xyz"}
        q[ax] = h[ax] + sgn * 3
        for p in boards:
            if p["id"] == h["part"] or p["group"] == "fronts":   # фасады ставят после короба / корпуса
                continue
            pre_ = [x for x in d.get("preassembled", []) if h["part"].startswith(x)]
            if pre_ and not p["id"].startswith(pre_[0]):     # узел собран до установки — головки закрываются потом
                continue
            if all(p[k + "0"] + 0.01 < q[k] < p[k + "1"] - 0.01 for k in "xyz"):
                blocked.append(f"{h['part']} ({h['kind']}) закрыт {p['id']}")
                break
    add("Доступ инструмента к эксцентрикам, саморезам и конфирматам после сборки", ERR if blocked else OK,
        "все входы свободны" if not blocked else f"{blocked[0]}; всего {len(blocked)}")
    # 11. Габарит в штампе = габарит модели выбранной комплектации
    zmax = max(p["z1"] for p in boards)
    add("Высота изделия в штампе и общем виде = верх модели", OK if abs(d.get("height", 0) - zmax) < 0.6 else ERR,
        f"штамп {d.get('height')}, модель {zmax:g}")
    # 12. Покупной аксессуар помещается (матрас, корзины …)
    for nm, need, have in d.get("fits", []):
        ok = all(hv >= nd for nd, hv in zip(need, have))
        add(f"Помещается: {nm}", OK if ok else ERR, f"нужно {' × '.join(f'{v:g}' for v in need)}, есть "
            f"{' × '.join(f'{v:g}' for v in have)}")
    # 13. Нет шагов про двери и полки, которых у изделия нет
    if not doors and re.search(r"[Дд]вер", " ".join(t for t in texts if "Контроль" in t or "Монтаж" in t or "Ящики" in t)):
        add("Нет шагов про двери у изделия без дверей", ERR, "в сборке / контроле упомянута дверь")

    # 14. MOVENTO + TIP-ON BLUMOTION (каталог Blum 2022/23 стр. 436–437): зазор фасада, блок по массе и NL, точки профиля
    mv = [r for r in d.get("drawers", []) if r.get("sys") == "movento"]
    if mv:
        # независимая копия таблицы Blum 2024/25 с. 428 (не из cab): места саморезов A от передней кромки корпуса
        ref = {270: [19, 37, 69, 197], **{n: [19, 37, 69, 243, 261] for n in (300, 320, 350)},
               **{n: [19, 37, 69, 243, 261, 293] for n in (380, 400, 420, 450, 480, 500, 520)}}
        bad = []
        for r in mv:
            fr = P[r["front"]]
            near = [c["y0"] for c in carc if _ov(c["x0"], c["x1"], fr["x0"], fr["x1"]) > 1 and _ov(c["z0"], c["z1"], fr["z0"], fr["z1"]) > 1]
            g = min(near) - fr["y1"] if near else 99
            if g < 2.5 - 0.01:
                bad.append(f"{r['pre']}{r['n']}: зазор фасада {g:g} < 2,5")
            if ref.get(r["NL"]) != list(r["pts"]):
                bad.append(f"{r['pre']}{r['n']}: точки {r['pts']} ≠ каталог с. 428 для NL {r['NL']}")
            if any(h.get("fastener") != "SLIDE-SCREW-M" for h in holes if h["joint"].startswith(f"J-{r['pre']}RUNNER-{r['n']}-")):
                bad.append(f"{r['pre']}{r['n']}: крепёж профиля не 609.1500 Ø3,5 × 15")
            m = [h for h in holes if h["joint"].startswith(f"J-{r['pre']}RUNNER-{r['n']}-")]
            ys = sorted({round(h["y"] - (fr["y1"] + g), 1) for h in m})
            if ys != sorted(float(v) for v in ref.get(r["NL"], [])):
                bad.append(f"{r['pre']}{r['n']}: разметка {ys} от кромки корпуса")
        spec = H.get("TIPON-SYNC", {}).get("spec", "")
        nl, kg = mv[0]["NL"], max(r.get("kg", 0) for r in mv)
        want = ("T60L7040" if kg <= 10 else "T60L7140") if nl <= 320 else ("T60L7340" if kg <= 20 else "T60L7540")
        if want not in spec:
            bad.append(f"блок TIP-ON BLUMOTION: нужен {want} (NL {nl}, {kg:g} кг)")
        if "760H" not in H.get("SLIDES", {}).get("spec", ""):
            bad.append("направляющая не 760H")
        add("MOVENTO TIP-ON BLUMOTION: зазор фасада ≥ 2,5, точки профиля по каталогу 2024 с. 428, блок по NL и массе", ERR if bad else OK,
            f"{len(mv)} ящ., NL {nl}, {kg:g} кг" if not bad else f"{bad[0]}; всего {len(bad)}")

    # 15. Фасад ящика крепится изнутри: вплотную к передней стенке, саморез входит в фасад и не выходит на лицо
    #     (ENG-002: фасад висел в 2,5 от короба при TIP-ON — вход самореза 6,5 вместо 9)
    drs_all = d.get("drawers", [])
    if drs_all:
        bad = []
        for r in drs_all:
            fr, fw = P[r["front"]], P[r["box"][2]]
            gap = round(fw["y0"] - fr["y1"], 2)
            fs = [h for h in holes if h["joint"] == f"J-{r['pre']}FRONT{r['n']}-BOX{r['n']}"]
            on_face = [h for h in fs if h["part"] == fr["id"]]
            for h in fs:
                L = _len(h.get("fastener"))
                if h["part"] != fw["id"] or h["dir"] != "-y" or L is None:
                    continue
                eng = L - (fw["y1"] - fw["y0"]) - gap
                rest = (fr["y1"] - fr["y0"]) - eng
                if gap > 0.01 or eng < 6 or rest < 3:
                    bad.append(f"{r['pre']}ящ.{r['n']}: зазор фасад — стенка {gap:g}, вход {eng:g}, остаток до лица {rest:g}")
                    break
            if on_face:
                bad.append(f"{r['pre']}ящ.{r['n']}: отверстие крепежа на фасаде ({on_face[0]['kind']})")
            if not fs:
                bad.append(f"{r['pre']}ящ.{r['n']}: нет крепления фасада")
        add("Фасад ящика: вплотную к передней стенке, саморез изнутри — вход в фасад ≥ 6, остаток до лица ≥ 3",
            ERR if bad else OK, f"{len(drs_all)} ящ." if not bad else f"{bad[0]}; всего {len(bad)}")

    # 9. Текстура дубовых дверей — одним направлением (вертикально)
    gr = {d["parts_ext"].get(p["id"], {}).get("grain") for p in doors if p["finish"] == "O"}
    if gr:
        add("Текстура дверей одного направления (вертикально)", OK if gr == {"z"} else ERR,
            "все вертикально" if gr == {"z"} else f"направления: {', '.join(sorted(g or '—' for g in gr))}")
    return out
