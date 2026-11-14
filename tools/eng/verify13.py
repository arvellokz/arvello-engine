"""Проверки снимка конфигурации для комплектов R01E (eng/models13.py): то же, что у «Самал» R02E, в общем виде.
verify(s) -> [(проверка, ok, подробности)]."""
from __future__ import annotations

from .cab import BLUM, MOV_SERIES, MOVENTO, TECH, NL_SERIES, RECESS, blum_points, movento_points

MADE = ("board", "tube", "plate")
FACE = ("ecc_stem", "dowel_face", "conf_face")
EDGE = ("ecc_bolt", "dowel_edge", "conf_edge")


def _n(x):
    return f"{x:g}".replace(".", ",")


def _box(h):
    ax = "xyz".index(h["dir"][1]); sg = 1 if h["dir"][0] == "+" else -1
    r = h["d"] / 2
    lo, hi = [h[k] - r for k in "xyz"], [h[k] + r for k in "xyz"]
    dep = 15 if h["kind"] == "runner_mark" else h["depth"]
    e = h["xyz"[ax]] + sg * dep
    lo[ax], hi[ax] = min(h["xyz"[ax]], e), max(h["xyz"[ax]], e)
    return lo, hi


def _clash(a, b, tol=0.3):
    (la, ha), (lb, hb) = _box(a), _box(b)
    return all(min(ha[i], hb[i]) - max(la[i], lb[i]) > tol for i in range(3))


def verify(s, report=None, texts=None, known_q=()):
    out = []
    add = lambda n, ok, t: out.append((n, bool(ok), str(t)))
    d = s["derived"]
    parts = {p["id"]: p for p in s["parts"]}
    made = [p for p in s["parts"] if p["kind"] in MADE]
    for c in s["checks"]:
        add(c["name"], c["ok"], f"{_n(c['expected'])} = {_n(c['actual'])}")
    # ---- детали не пересекаются
    clash = []
    grooves = {}
    for g in d.get("grooves", []):                # дно в пазу: пересечение ровно по объёму паза — не ошибка
        grooves[frozenset((g["part"], g["with"]))] = g
    for i, a in enumerate(made):
        for b in made[i + 1:]:
            ov = [min(a[k + "1"], b[k + "1"]) - max(a[k + "0"], b[k + "0"]) for k in "xyz"]
            if all(o > 0.01 for o in ov):
                g = grooves.get(frozenset((a["id"], b["id"])))
                if g and all(max(a[k + "0"], b[k + "0"]) >= g[k + "0"] - 0.01 and min(a[k + "1"], b[k + "1"]) <= g[k + "1"] + 0.01
                             for k in "xyz"):                    # пересечение целиком внутри паза
                    continue
                clash.append((a["id"], b["id"]))
    add("Детали не пересекаются (дно в пазу — по объёму паза)", not clash, "нет" if not clash else clash[:4])
    # ---- отверстие на грани своей детали
    off = []
    for h in s["holes"]:
        p = parts[h["part"]]
        ax = h["dir"][1]
        fv = p[ax + ("0" if h["dir"][0] == "+" else "1")]
        inside = all(p[k + "0"] - 0.01 <= h[k] <= p[k + "1"] + 0.01 for k in "xyz")
        if abs(h[ax] - fv) > 0.01 or not inside:
            off.append(h["id"] + " " + h["kind"] + " " + h["part"])
    add("Точка входа каждого отверстия — на грани своей детали", not off, "все" if not off else off[:4])
    # ---- остаток при глухом сверлении
    thin = []
    for h in s["holes"]:
        if h["through"] or not h["depth"] or parts[h["part"]]["kind"] != "board":
            continue
        p = parts[h["part"]]
        ax = h["dir"][1]
        L = p[ax + "1"] - p[ax + "0"]
        if L - h["depth"] < 3:
            thin.append(f"{h['id']} {h['kind']} {h['part']} ост. {L - h['depth']:g}")
    add("Остаток плиты при глухом сверлении ≥ 3 мм", not thin, "соблюдён" if not thin else thin[:4])
    # ---- сопряжение отверстий в соединениях
    bad = []
    for j, ids in d["joints"].items():
        hs = [h for h in s["holes"] if h["id"] in ids]
        face = [h for h in hs if h["kind"] in FACE]
        edge = [h for h in hs if h["kind"] in EDGE]
        for a in face:
            ax = "xyz".index(a["dir"][1])
            mates = [b for b in edge if all(abs(a[k] - b[k]) < 0.01 for k in "xyz" if "xyz".index(k) != ax)]
            if len(mates) != 1:
                bad.append(f"{j}:{a['id']}")
                continue
            b = mates[0]
            pa = a[a["dir"][1]] + (1 if a["dir"][0] == "+" else -1) * (a["depth"] if a["through"] else 0)
            if not (abs(b[b["dir"][1]] - pa) < 0.01 or abs(b[b["dir"][1]] - a[a["dir"][1]]) < 0.01):
                bad.append(f"{j}:{a['id']}~{b['id']}")
    add("Отверстия сопрягаемых деталей на одной оси", not bad,
        f"{len(d['joints'])} соединений" if not bad else bad[:5])
    # ---- Minifix
    Hh = [h for h in s["holes"] if h["kind"] == "ecc_housing"]
    Bo = [h for h in s["holes"] if h["kind"] == "ecc_bolt"]
    St = [h for h in s["holes"] if h["kind"] == "ecc_stem"]
    if Hh:
        def _pair(b):
            ax = b["dir"][1]
            for h in Hh:
                if h["joint"] != b["joint"]:
                    continue
                th = h["dir"][1]
                other = next(k for k in "xyz" if k not in (ax, th))
                if abs(abs(h[ax] - b[ax]) - 24) < 0.02 and abs(abs(h[th] - b[th]) - 8) < 0.02 and abs(h[other] - b[other]) < 0.02:
                    return True
            return False
        okB = all(_pair(b) for b in Bo)
        add("Häfele стр. 294/301: корпус Ø15 × 12,5, B = 24, болт Ø8 × 32, шток Ø5 × 12",
            all(h["d"] == 15 and h["depth"] == 12.5 for h in Hh) and okB and all(b["d"] == 8 and b["depth"] == 32 for b in Bo)
            and all(x["d"] == 5 and x["depth"] == 12 for x in St) and len(Hh) == len(Bo) == len(St), f"{len(Hh)} стяжек")
        thinH = [h["id"] for h in Hh if (lambda p, ax: p[ax + "1"] - p[ax + "0"])(parts[h["part"]], h["dir"][1]) - 13 < 3]
        add("Häfele стр. 294: под корпусом остаток ≥ 3 при +0,5", not thinH, "плита ≥ 16" if not thinH else thinH[:4])
    # ---- количества крепежа = отверстиям
    hw = {h["id"]: h for h in s["hardware"]}
    fc = {}
    for h in s["holes"]:
        if h["fastener"]:
            fc[h["fastener"]] = fc.get(h["fastener"], 0) + 1
    mism = [f"{k}: {hw[k]['qty'] if k in hw else '—'} ≠ {v}" for k, v in fc.items() if k != "HINGE" and (k not in hw or hw[k]["qty"] != v)]
    if "HINGE" in fc:
        if hw.get("HINGE", {}).get("qty") != fc["HINGE"]:
            mism.append(f"HINGE {hw.get('HINGE', {}).get('qty')} ≠ {fc['HINGE']}")
    if "ECC-15" in fc and hw.get("ECC-BOLT", {}).get("qty") != fc["ECC-15"]:
        mism.append("ECC-BOLT")
    add("Крепёж в спецификации = отверстиям", not mism, f"{sum(fc.values())} шт. по {len(fc)} позициям" if not mism else mism[:4])
    # ---- пересечения отверстий в детали
    coll = []
    byp = {}
    for h in s["holes"]:
        byp.setdefault(h["part"], []).append(h)
    for pid, hs in byp.items():
        if parts[pid]["kind"] != "board":
            continue
        for i, a in enumerate(hs):
            for b in hs[i + 1:]:
                if a["joint"] == b["joint"] and ({a["kind"], b["kind"]} <= {"ecc_bolt", "ecc_housing"}
                                                 or {a["kind"], b["kind"]} <= {"bed_edge", "bed_nut"}):
                    continue
                if _clash(a, b):
                    coll.append(f"{pid}:{a['kind']}/{b['kind']}")
    add("Отверстия в детали не пересекаются (кроме болт—корпус эксцентрика; саморез профиля — 15)", not coll,
        "нет" if not coll else coll[:4])
    # ---- ящики на скрытых направляющих по профилю (cab.SLIDE_PROFILES; ENG-005 п. 2, документы производителя)
    sm = [r for r in d.get("drawers", []) if r.get("sys") == "samet"]
    if sm:
        from .cab import SLIDE_PROFILES
        e, em = [], []
        for r in sm:
            S_ = SLIDE_PROFILES[r["slide"]]
            sl, sr, fp, bp, bt = (parts[i] for i in r["box"])
            tag = f"{r['pre']}{r['n']}"
            if r["NL"] not in S_["codes"]:
                e.append(f"{tag}: NS {r['NL']} нет в ряду {S_['name']}")
            if r["Dc"] < r["NL"] + S_["cd"]:
                e.append(f"{tag}: глубина {r['Dc']:g} < NS + {S_['cd']}")
            bigger = [ns for ns in S_["codes"] if ns > r["NL"] and ns + S_["cd"] <= r["Dc"]]
            if bigger:
                e.append(f"{tag}: NS {r['NL']} не наибольший (помещается {bigger[0]})")
            if abs((sl["y1"] - sl["y0"]) - (r["NL"] - S_["dd"])) > 0.01:
                e.append(f"{tag}: длина ящика {sl['y1'] - sl['y0']:g} ≠ NS − {S_['dd']}")
            if abs((sr["x0"] - sl["x1"]) - (r["LW"] - S_["diw"])) > 0.5:
                e.append(f"{tag}: внутренняя ширина {sr['x0'] - sl['x1']:g} ≠ проём − {S_['diw']}")
            if sl["x1"] - sl["x0"] > S_["side_max"]:
                e.append(f"{tag}: боковина > {S_['side_max']}")
            if r["z0"] - r["rb"] < S_["under"] - 0.01:
                e.append(f"{tag}: низ ящика над низом проёма < {S_['under']}")
            if r["limit_top"] - (r["z0"] + r["h"]) < -0.01:
                e.append(f"{tag}: над ящиком < {S_['top_min']}")
            m = [h for h in s["holes"] if h["kind"] == "runner_mark" and h["joint"].startswith(f"J-{r['pre']}RUNNER-{r['n']}-")]
            col = parts[r["colL"]]
            want = sorted(col["y0"] + S_["front_off"] + y for y in S_["points"].get(r["NL"], ()))
            for side in "LR":
                ms = sorted(h["y"] for h in m if h["joint"].endswith(f"-{side}"))
                if ms != [round(y, 2) for y in want]:
                    em.append(f"{tag}{side}: шурупы {ms} ≠ {want}")
            if any(abs(h["z"] - r["rb"] - S_["screw_axis"]) > 0.01 for h in m):
                em.append(f"{tag}: ось шурупов ≠ низ проёма + {S_['screw_axis']}")
            rq = S_["rear"]
            rr = [h for h in s["holes"] if h["kind"] == "slide_rear" and h["part"] == bp["id"]]
            if len(rr) != 2 or any(abs(h["z"] - r["z0"] - rq["from_bottom"]) > 0.01 or h["d"] != rq["d"]
                                   or h["depth"] != rq["depth"] for h in rr) or \
                    sorted(round(h["x"], 2) for h in rr) != [round(sl["x1"] + rq["from_side"], 2),
                                                            round(sr["x0"] - rq["from_side"], 2)]:
                em.append(f"{tag}: задние Ø{rq['d']} гл. {rq['depth']} ({rq['from_bottom']} от низа, {rq['from_side']} от боковины)")
        add("Направляющие по профилю: NS — наибольший с NS + cd ≤ глубины; длина ящика, внутренняя ширина, боковина, "
            "низ ящика над проёмом, над ящиком — по документу производителя", not e, f"{len(sm)} ящ." if not e else e[:4])
        add("Направляющие по профилю: места шурупов от конца направляющей (отступ от края корпуса), ось [М]; задний Ø6 "
            "Lock-Fix", not em, f"{len(sm)} ящ." if not em else em[:4])
        hq = lambda k: hw.get(k, {}).get("qty", 0)
        nm = sum(1 for h in s["holes"] if h["kind"] == "runner_mark" and h.get("fastener") == "SLIDE-SCREW-S")
        add("Направляющие по профилю: комплектность — пары направляющих = замки = ящики; шурупы = разметке",
            hq("SLIDES") == hq("SLIDE-LOCK") == len(sm) and hq("SLIDE-SCREW-S") == nm, f"{hq('SLIDES')} / {hq('SLIDE-LOCK')} / {nm}")
    # ---- ящики Blum
    drs = [r for r in d.get("drawers", []) if r.get("sys") != "samet"]
    if drs:
        e = []
        sys_of = lambda r: MOVENTO if r.get("sys") == "movento" else BLUM[r["tipon"]]
        pts_of = lambda r: movento_points(r["NL"]) if r.get("sys") == "movento" else blum_points(r["NL"], r["tipon"])
        for r in drs:
            sysd = sys_of(r)
            sl = parts[r["box"][0]]
            dims = sorted([sl["x1"] - sl["x0"], sl["y1"] - sl["y0"]])
            Lbox = dims[1]
            fp = parts[r["box"][2]]
            fdims = sorted([fp["x1"] - fp["x0"], fp["y1"] - fp["y0"]])
            if r["NL"] not in (MOV_SERIES if r.get("sys") == "movento" else NL_SERIES): e.append(f"NL {r['NL']}")
            if abs(Lbox - (r["NL"] - 10)) > 0.01: e.append(f"{r['pre']}{r['n']}: SKL {Lbox}")
            if abs(fdims[1] - (r["LW"] - 42)) > 0.01: e.append(f"{r['pre']}{r['n']}: SKW {fdims[1]}")
            if abs(r["z0"] - (r["rb"] + sysd["under"] - RECESS)) > 0.01: e.append("низ дна")
            if r["Dc"] < r["NL"] + 3: e.append("NL+3")
            if r["limit_top"] - (r["z0"] + r["h"]) < 0 or r["limit_top"] < 0: e.append("над коробом")
            if abs(r["rb"] - (r["floor"] + TECH["runner_lift"])) > 0.01 and r["n"] == 1: e.append("профиль над дном")
            if r["pts"] != list(pts_of(r)): e.append("точки")
        add("Blum 560H / 760H: SKL = NL − 10, SKW = LW − 42, место NL + 3, NL из ряда системы", not e,
            f"{len(drs)} ящ." if not e else e[:4])
        mv = [r for r in drs if r.get("sys") == "movento"]
        if mv:
            e = []
            gl = d.get("grooves", [])
            for r in mv:
                sl, sr, fp, bp, bt = (parts[i] for i in r["box"])
                h = sl["z1"] - sl["z0"]
                wall = h - RECESS - 16
                for w, nm in ((fp, "передняя"), (bp, "задняя")):
                    if abs((w["z1"] - w["z0"]) - wall) > 0.01 or abs(w["z0"] - bt["z1"]) > 0.01:
                        e.append(f"{r['pre']}{r['n']}: стенка {nm} {w['z1'] - w['z0']:g} ≠ {wall:g} или не на дне")
                skw = r["LW"] - 42
                cl = r.get("bottom_clear") or 0                         # раскрой Blum: дно 536 при SKW 526 (зазор 0)
                if abs((bt["x1"] - bt["x0"]) - (skw + 10 - 2 * cl)) > 0.01 or cl < 0 or cl > 1:
                    e.append(f"{r['pre']}{r['n']}: дно {bt['x1'] - bt['x0']:g} ≠ SKW + 10 − 2 × зазор {cl:g}")
                if abs((bt["y1"] - bt["y0"]) - (r["NL"] - 10)) > 0.01:
                    e.append(f"{r['pre']}{r['n']}: длина дна ≠ SKL")
                if abs(bt["z0"] - sl["z0"] - RECESS) > 0.01:
                    e.append(f"{r['pre']}{r['n']}: утопление дна")
                for S in (sl, sr):
                    g = [x for x in gl if x["part"] == S["id"] and x["with"] == bt["id"]]
                    if len(g) != 1 or abs(g[0]["depth"] - 5) > 0.01 or abs(g[0]["y1"] - g[0]["y0"] - (S["y1"] - S["y0"])) > 0.01:
                        e.append(f"{S['id']}: паз под дно")
            add("MOVENTO (раскрой Blum 12.11): стенки = h − 13 − 16 на дне, дно SKW + 10 × SKL в пазах 5, утопление 13",
                not e, f"{len(mv)} ящ." if not e else e[:3])
        marks = [h for h in s["holes"] if h["kind"] == "runner_mark"]
        okm = True
        for r in drs:
            sysd = sys_of(r)
            m = [h for h in marks if h["joint"].startswith(f"J-{r['pre']}RUNNER-{r['n']}-")]
            if len(m) != 2 * len(r["pts"]) or any(abs(h["z"] - r["rb"] - sysd["axis"]) > 0.01 for h in m):
                okm = False
        add("Blum: точки профиля по таблице NL (560H стр. 39/40, 760H каталог стр. 437), ось = низ профиля + 37 (38 TIP-ON)",
            okm, f"{len(marks)} точек")
        bot = all(r["z0"] + RECESS - r["rb"] in (sys_of(r)["under"],) for r in drs)
        add("Blum: низ дна − низ профиля = 27,5 (28,5 TIP-ON); утопление дна 13", bot, "все ящики")
        clear = [f"{r['pre']}{r['n']}" for r in drs if r["limit_top"] - (r["z0"] + r["h"]) < 0]
        add("Blum: над коробом ≥ 7 (до профиля следующего ящика / крышки)", not clear, "соблюдено" if not clear else clear)
        hd = [f"{r['pre']}{r['n']}" for r in drs if r["hz"] is not None and not r["through"] and r["hz"] - 4 <= r["z0"] + r["h"]]
        add("Винты ручек: головка выше короба или винт сквозь стенку короба", not hd, "соблюдено" if not hd else hd)
        nd = len(drs)
        hq = lambda k: hw.get(k, {}).get("qty", 0)
        add("Комплектность: пары направляющих = замки = ящики; саморезы замков 4 на ящик",
            hq("SLIDES") == hq("SLIDE-LOCK") == nd and hq("LOCK-SCREW") == 4 * nd and hq("SLIDE-SCREW") + hq("SLIDE-SCREW-M") == len(marks),
            f"{hq('SLIDES')} / {hq('SLIDE-LOCK')} / {hq('LOCK-SCREW')} / {hq('SLIDE-SCREW') + hq('SLIDE-SCREW-M')}")
        if any(r["tipon"] for r in drs):
            add("TIP-ON: синхронизатор на каждый ящик (560H стр. 23; 760H каталог стр. 436)", hq("TIPON-SYNC") == sum(r["tipon"] for r in drs), f"{hq('TIPON-SYNC')}")
    # ---- металл
    tubes = [p for p in s["parts"] if p["kind"] == "tube"]
    if tubes:
        inframe = {t for f in d.get("frames", []) for t in f["tubes"]}
        add("Каждая труба входит в раму / узел", all(t["id"] in inframe for t in tubes), f"{len(tubes)} труб")
        wl = d.get("welds", [])
        okw = all(a in parts and b in parts for a, b in wl)
        touch = all(all(min(parts[a][k + "1"], parts[b][k + "1"]) - max(parts[a][k + "0"], parts[b][k + "0"]) >= -0.01 for k in "xyz")
                    for a, b in wl)
        add("Сварные швы: детали существуют и касаются", okw and touch, f"{len(wl)} швов")
        ins = [h for h in s["holes"] if h["kind"] == "insert"]
        tt = [h for h in s["holes"] if h["kind"] == "tube_top"]
        add("Втулки M6 = отверстия в рамах под винты", len(ins) == sum(1 for h in tt if h["fastener"] == "SCREW-M6x16"),
            f"{len(ins)} втулок")
        if ins:
            rest = min(parts[h["part"]]["z1"] - parts[h["part"]]["z0"] - 17 for h in ins)
            add("Остаток столешницы под втулкой (гл. 17) ≥ 8", rest >= 8, f"{_n(rest)} мм")
    # ---- листы
    if report is not None:
        badr = {k: v for k, v in report.items() if v}
        add("Наложения текста и выход за рамку", not badr, "нет" if not badr else str(badr)[:300])
    if texts is not None:
        import re
        total = s.get("_total_sheets", 99)
        refs = {int(x) for t in texts for x in re.findall(r"(?:\bлист[а-я]*|(?<![А-Яа-я])л\.)\s*0?(\d{1,2})\b", t)}
        add("Все ссылки на листы существуют", refs <= set(range(1, total + 1)), f"{sorted(refs)}")
        qrefs = {x for t in texts for x in re.findall(r"В-\d+", t)}
        add("Все упомянутые В-n есть в вопросах / решениях", qrefs <= set(known_q), f"{len(qrefs)} упомянуто" +
            ("" if qrefs <= set(known_q) else f"; нет: {sorted(qrefs - set(known_q))}"))
    return out
