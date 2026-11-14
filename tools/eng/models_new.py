"""Новые модели Arvello (каталог под цех, с 11.11.2026).

Сюда добавляются построители новых моделей. Каждая модель:
  1) функция-построитель f(o) -> Build (см. пример example_wardrobe_2d ниже и models13.py / models_rest.py);
  2) запись в NEW: "ARV-XXX-NNN": ("Название «Имя»", f);
  3) карточка catalog/products/ARV-XXX-NNN.json (оси и значения; поле "builder" можно не указывать);
  4) строка в catalog/revisions.json: {"catalog": "R01E", "revisions": {"R01E": {"status": ..., "production": "закрыто"}}}.
Комплект чертежей:  python tools/eng/kit13.py ARV-XXX-NNN out.pdf key=value ...

Правила конструкции — как у существующих корпусных моделей (eng/cab.py): корпус ЛДСП 16 на Minifix 15 + шкант 8×30,
фасады ЛДСП 18 с зазорами 1,5 по краям / 3 между фасадами, ХДФ 4 накладная, ящики Blum TANDEM 560H, остальная
фурнитура — «кандидат» с номером вопроса В-… Производство закрыто (manufacturing_allowed = False).
"""
from __future__ import annotations

from . import cab
from .cab import GAP, T, TB, TF, TIPON_GAP, Build
from .models13 import MODELS, REV, STATUS

NEW_STATUS = STATUS


def _check(b, name, exp, act):
    b.checks.append((name, exp, round(act, 3) if isinstance(act, float) else act))


# ============================================================ ОБРАЗЕЦ (не каталожная модель): шкаф распашной 2 двери
def example_wardrobe_2d(o):
    """Образец построителя: корпус на цоколе, полка и штанга, две двери на петлях, ручки 320."""
    from .models_rest import _anti_tip, _hang_rod
    W, color = int(o.get("width", 1000)), o.get("color", "W")
    H, PL, D = 2100, 80, 580
    b = Build(o.get("_sku", "ARV-EXAMPLE-001"), REV, NEW_STATUS, {"width": W, "color": color})
    yc0, yc1 = TF, D - TB
    shelf_z = H - 380
    c = b.carcass("", 0, W, PL, H, yc0, yc1, color, shelves=[(T, W - T, shelf_z, "Полка", "+")], label="корпус")
    b.plinth("", c, PL, front=50, side=20, back=16, fin=color)
    _hang_rod(b, c["L"], c["R"], shelf_z - 60, (yc0 + yc1) / 2)
    half = W / 2
    fronts = [(GAP / 2, half - GAP / 2, PL + GAP / 2, H - GAP / 2), (half + GAP / 2, W - GAP / 2, PL + GAP / 2, H - GAP / 2)]
    b.doors("", c, [c["L"], c["R"]], fronts, color, handle="v320", hz_from_top=(H - PL) - (1100 - PL), lefts=[True, False])
    _anti_tip(b, 1)
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = цоколь + боковина", H, PL + (c["L"].z1 - c["L"].z0))
    _check(b, "Глубина = фасад + корпус + ХДФ", D, TF + (c["L"].y1 - c["L"].y0) + TB)
    b.notes += ["ОБРАЗЕЦ построителя для новых моделей: не каталожная модель.",
                "Корпус ЛДСП 16 на Minifix; двери ЛДСП 18 на петлях (кандидат, В-20); ручки 320 у свободной кромки."]
    return b


EXAMPLE = {"ARV-EXAMPLE-001": ("Образец: шкаф распашной 2 двери", example_wardrobe_2d)}
EXAMPLE_PRODUCT = {
    "sku": "ARV-EXAMPLE-001", "name": "Образец: шкаф распашной 2 двери", "category": "WRD", "line": "STD",
    "desc": "Образец построителя для новых моделей.",
    "axes": [{"key": "width", "label": "Ширина", "mode": "frame", "values": [800, 1000], "labels": {"800": "80 см", "1000": "100 см"}},
             {"key": "color", "label": "Цвет", "mode": "frame", "values": ["W", "G"], "labels": {"W": "белый", "G": "графит"}}],
}



# ============================================================ общие узлы новых моделей
from . import models_rest as _MR

KQ3 = {
    "В-101": ("Штанга выдвижная для шкафа глубиной 450 (одежда вдоль глубины): изготовитель, длина под глубину корпуса, "
              "нагрузка, крепление к полке", "секции со штангой при глубине 45", "Arvello", "каталог изделия"),
    "В-102": ("Шкаф до потолка: монтажный зазор до потолка (принято 40 мм), планка-заглушка в цвет фасада и её крепление; "
              "подъём секций в помещение", "монтаж, вид сверху", "Arvello + монтажник", "замер высоты и диагонали проёма"),
}
_MR.KQ2.update(KQ3)
from .cab import FASTENERS as _F
_F.update({"PULLROD-SCREW": ("Саморез выдвижной штанги 4 × 16", "в комплекте штанги (кандидат)", "кандидат", "В-101", "шт")})


from . import kitchen as _KX
_F.update({
    "SCREW-4x25M": ("Саморез 4 × 25", "потай: снизу через крышку секции в дно антресоли; вход в дно 9, остаток 7",
                    "типовой", "", "шт"),
    "SCREW-4x25S": ("Саморез 4 × 25", "потай: через проставку в боковину; вход в боковину 9, остаток 7", "типовой", "", "шт"),
    "SHELF-PIN": ("Полкодержатель Ø5", "штифт стальной Ø5 с площадкой, 4 на съёмную полку (кандидат)", "кандидат", "В-103", "шт"),
})
KQ3.update({
    "В-103": ("Съёмные полки: полкодержатель Ø5 (артикул, глубина сверления 12), шаг перестановки 32; какие полки цех "
              "оставляет жёсткими для геометрии корпуса", "боковины секций с полками", "Arvello (по каталогу производителя)",
              "образец полкодержателя, техкарта"),
})
KQ3.update({
    "В-104": ("Дверь без ручки: TIP-ON 956A1006 с петлями BLUMOTION 71B3550 — открывание нажатием и мягкое закрытие; "
              "по каталогу Blum сочетание допустимо, проверить на первом заказе (если доводчик мешает открыванию — петли "
              "70T3550.TL без пружины и 956A1004)", "двери без ручек", "Arvello: проверка на первом заказе",
              "приёмка первого шкафа по чек-листу"),
    "В-105": ("Внутренние ящики за дверью: проставки ЛДСП 16 начинаются за планкой петли (61 мм от кромки, выступ 11 — по "
              "размерам планки 173H7100, у 173L8100 — сверить по каталогу Blum 2024/25 с. 154); проверить ход ящика при открытой двери 110° на первом заказе",
              "проставки, ящики", "Arvello: проверка на первом заказе", "приёмка первого шкафа по чек-листу"),
})
_MR.KQ2.update(KQ3)

PUSH_GAP = 2          # зазор дверь — корпус для TIP-ON (кандидат, В-104)
PLATE_ENV = {"y": 61, "protr": 11, "dz": 25}   # огибающая планки и плеча петли (кандидат, В-105)

LEG_H = 100                                   # опора регулируемая (как кухонные), цоколь на клипсах


def _hinges(hd):
    """Число петель по высоте двери: до 900 — 2, до 1600 — 3, до 2000 — 4, выше — 5 (кандидат, В-20)."""
    return 2 if hd <= 900 else 3 if hd <= 1600 else 4 if hd <= 2000 else 5


def _adj_shelf(b, pre, k, c, x0, sw, yc0, yc1, z, color):
    """Съёмная полка на 4 полкодержателях Ø5; в боковинах ряд отверстий −32 / 0 / +32 для перестановки."""
    sp = b.part(f"{pre}ASHELF-{k}", "Полка съёмная", x0 + T + 1, yc0 + 20, z, x0 + sw - T - 1, yc1 - 2, z + T, "LDSP16", color,
                "shelves", edges={"-y": "ABS2", "-x": "PVC04", "+x": "PVC04", "+y": "PVC04"})
    for S, xf, dr in ((c["L"], c["L"].x1, "-x"), (c["R"], c["R"].x0, "+x")):
        for yy in (yc0 + 60, yc1 - 50):
            for dz in (-32, 0, 32):
                b.hole(S.id, f"J-{pre}PIN{k}", "shelf_pin", xf, yy, z - 2.5 + dz, dr, 5, 12, "SHELF-PIN" if dz == 0 else None,
                       note="полкодержатель; ряд для перестановки ± 32")
    return sp


# MOVENTO 760H + TIP-ON BLUMOTION (нажатие + мягкое закрытие): места саморезов — каталог Blum 2024/25 с. 428,
# короб — раскрой конфигуратора Blum (12.11). Включено для накладных ящиков (комод ARV-NST-101).
# Внутренние ящики за дверью (WRD-101) — пока TANDEM 560H со встроенным TIP-ON: у внутреннего ящика MOVENTO другие
# размеры (X + 23 / 18), не сверены.
USE_MOVENTO_TOB = True
USE_MOVENTO_INNER = False
DRAWER_LOAD = 10                              # груз в ящике комода, кг — принятый (одежда), подтверждает Arvello


def _movento_tob(b):
    """Внутренние ящики: MOVENTO 760H…S + TIP-ON BLUMOTION — открывание нажатием и мягкое закрытие (12.11).
    Правила места те же, что у TANDEM: SKW = LW − 42 (+0 / −1,5), SKL = NL − 10, внутренний ящик NL + X + 7."""
    r = b.derived["drawers"][-1]
    nd = sum(1 for q in b.derived["drawers"] if q["tipon"])
    b.hw["SLIDES"].update(name="Направляющая MOVENTO 760H (пара Л/П) под TIP-ON BLUMOTION",
                          spec=f"Blum 760H{r['NL'] * 10:04d}S, NL {r['NL']}, 40 кг, полное выдвижение; разметка профиля — "
                               "шаблон T65.1000.02", qty=nd)
    b.hw["SLIDE-LOCK"].update(name="Замок ящика MOVENTO (пара Л/П)", spec="Blum T51.7601 (по каталогу MOVENTO)")
    b.hw["TIPON-SYNC"].update(name="TIP-ON BLUMOTION: блок, защёлка, синхронизация",
                              spec=f"Blum T60 для MOVENTO, по массе ящика; синхронизация — отрез LW − 267 = {r['LW'] - 267:g}",
                              status="кандидат", note="подобрать блок по массе ящика у поставщика Blum")
    b.derived["drawer_system"] = "MOVENTO TIP-ON BLUMOTION"


def _sections_var(b, W, n, H, PL, top, D, color, pattern, push=False, inner_drawers=False):
    """Секции одинаковой ширины W/n на регулируемых опорах + антресоли до H.
    pattern — H (штанга и полка над ней), S (полки: 2 жёсткие + съёмные, внизу ящики по опции)."""
    sw = W / n
    gap = PUSH_GAP if push else 0
    yc0, yc1 = TF + gap, D - TB
    yc = (yc0 + yc1) / 2
    pullout = D < 500
    hat = min(top - 300, 1840)                # низ полки над штангой: штанга не выше ≈ 1,78 м
    legs_x = []
    tall = (top - PL - GAP) > 2000
    for i, kind in enumerate(pattern):
        x0 = i * sw
        pre = f"S{i + 1}-"
        fixed, adj = [], []
        if kind == "S":
            z1 = PL + T + 480                 # жёсткая полка над зоной ящиков
            span = (top - T) - (z1 + T)
            nb = max(2, round(span / 340))
            step = (top - T - z1) / nb
            zz = [round(z1 + k * step) for k in range(1, nb)]
            mid = zz[len(zz) // 2] if len(zz) >= 3 else None
            fixed = [z1] + ([mid] if mid else [])
            adj = [z for z in zz if z != mid]
        else:
            fixed = [hat]
        sh = [(x0 + T, x0 + sw - T, z, "Полка жёсткая", "+") for z in sorted(fixed)]
        c = b.carcass(pre, x0, x0 + sw, PL, top, yc0, yc1, color, shelves=sh, label=f"секция {i + 1}")
        xs = [x0 + 70, x0 + sw - 70]
        pts = [(x, yc0 + 90) for x in xs] + [(x, yc1 - 90) for x in xs]
        b.feet(pre, c, PL, pts, "LEGK", 50, name=f"Опора регулируемая {PL}",
               spec=f"пластик, h {PL} (регулировка ±15), площадка 50, под клипсу цоколя (кандидат)", status="кандидат",
               note="В-37")
        legs_x += xs
        for k, z in enumerate(adj, 1):
            _adj_shelf(b, pre, k, c, x0, sw, yc0, yc1, z, color)
        if kind == "H":
            s_ = c["shelves"][0]
            if pullout:
                xm = (s_.x0 + s_.x1) / 2
                for dx in (-12, 12):
                    for yy in (yc0 + 40, yc1 - 40):
                        b.hole(s_.id, f"J-{pre}PULLROD", "pilot", xm + dx, yy, s_.z0, "+z", 2.5, 10, "PULLROD-SCREW",
                               note="выдвижная штанга (кандидат)")
                b.part(f"{pre}PULLROD", "Штанга выдвижная", xm - 20, yc0 + 20, s_.z0 - 60, xm + 20, yc1 - 20, s_.z0,
                       "ROD", "steel", "interior", kind="buy")
                b.buy("PULLROD", "Штанга выдвижная", f"под глубину корпуса {yc1 - yc0:g}, нагрузка ≥ 10 кг (кандидат)", 1,
                      "кандидат", "В-101")
                _MR._kq(b, "В-101")
            else:
                _MR._hang_rod(b, c["L"], c["R"], s_.z0 - 80, yc)
        if kind == "S" and inner_drawers:
            fl = c["BOT"].z1
            ceil = c["shelves"][0].z0
            sy0 = yc0 + PLATE_ENV["y"] + 1          # проставка начинается за планкой петли (В-105)
            sp = {}
            for side, sx0, nrm in (("L", x0 + T, "-x"), ("R", x0 + sw - 2 * T, "+x")):
                sp[side] = b.part(f"{pre}SPACER-{side}", "Проставка направляющей " + ("левая" if side == "L" else "правая"), sx0, sy0, fl, sx0 + T, yc1, ceil, "LDSP16",
                                  "INNER", "interior", edges={"-y": "PVC04"})
                for zz in (fl + 90, ceil - 90):
                    b.screws_into(sp[side], c[side], nrm, "y", [sy0 + 50, yc1 - 50], "SCREW-4x25S",
                                  f"J-{pre}SPACER-{side}", pilot=(3, 8), at=zz)
            fr = [(x0 + T + 26, x0 + sw - T - 26, fl + 4 + k * 222, fl + 4 + k * 222 + 216) for k in range(2)]
            b.drawers(pre, c, sp["L"], sp["R"], fl, ceil, fr, "INNER", "INNER", handle=None, tipon=True, front_mat="LDSP16",
                      front_t=16, front_unit="Передняя панель внутреннего ящика", setback=-7, box_max=150,
                      front_edges={"-x": "PVC04", "+x": "PVC04", "-z": "PVC04", "+z": "ABS2"})
            b.derived.setdefault("inner_gap", []).append(6)
            if USE_MOVENTO_INNER:
                _movento_tob(b)
        m = b.carcass(pre + "M-", x0, x0 + sw, top, H, yc0, yc1, color, label=f"антресоль {i + 1}")
        b.screws_into(c["TOP"], m["BOT"], "+z", "x", [x0 + 100, x0 + sw - 100], "SCREW-4x25M", f"J-{c['TOP'].id}-MEZ",
                      pilot=(3, 8), at=yc)
        left = i % 2 == 0
        side = c["L"] if left else c["R"]
        b.doors(pre, c, [side], [(x0 + GAP / 2, x0 + sw - GAP / 2, PL + GAP / 2, top - GAP / 2)], color,
                handle=None if push else "v320", hz_from_top=(top - PL) - (1100 - PL), lefts=[left], nh_rule=_hinges)
        ms = m["L"] if left else m["R"]
        b.doors(pre + "M-", m, [ms], [(x0 + GAP / 2, x0 + sw - GAP / 2, top + GAP / 2, H - GAP / 2)], color,
                handle=None if push else "bar128", hz_from_top=(H - top) - 60, lefts=[left], nh_rule=_hinges)
    # цоколь: лицевой на клипсах к опорам + два торцевых
    _KX._plinth(b, "PLINTH", 0, W, yc0 + 40, PL, color, legs=legs_x)
    _KX._end_plinths(b, [("PLINTH-L", "y", yc0 + 40 + T, yc1 - 10, 20 + T), ("PLINTH-R", "y", yc0 + 40 + T, yc1 - 10, W - 20)],
                     PL, color)
    b.buy("CLIP", "Клипса цоколя", "к регулируемой опоре, в комплекте саморезы (кандидат)", len(legs_x), "кандидат", "В-37")
    for p_ in b.P:                              # антресоль — свои наименования (в спецификации не путать с секцией)
        if "-M-" in p_.id and p_.kind == "board":
            p_.name = p_.unit = f"{p_.unit} антресоли"
    if push:                                   # 12.11: петли с доводчиком + TIP-ON для петель с пружиной (956A1006)
        b.buy("PUSH-LONG", "TIP-ON для двери с доводчиком", "Blum 956A1006 (длинный, для петель с пружиной / BLUMOTION) + "
              "адаптер 956A1201 (отступ 20, 2 самореза 3,5 × 15); у свободной кромки на высоте ручки ± 300; зазор 2 "
              "(заводская настройка, регулировка +4 / −1)", 2 * n, "кандидат", "В-104")
        _MR._kq(b, "В-104")
        b.derived["push_gap"] = gap
    if n > 1:
        b.buy("TIE", "Стяжка межсекционная Ø5", "4 на стык секций + 2 на антресоль (сверлить по месту)", 6 * (n - 1),
              "кандидат", "В-41")
    _MR._anti_tip(b, n)
    _MR._kq(b, "В-37", "В-103")
    if inner_drawers:
        _MR._kq(b, "В-105")
        b.derived["plate_env"] = dict(PLATE_ENV)
    for p_ in b.P:                              # текстура дверей — вертикально у всех (согласовать рисунок фасада)
        if p_.group == "fronts" and p_.kind == "board" and "DOOR" in p_.id:
            b.grain_override[p_.id] = "z"
    b.derived["levels"] = [0, PL, top, H]
    b.derived["ceiling_gap"] = 40
    b.derived["cut_x"] = round(sw * (1.5 if n > 1 else 0.5) + 77)   # разрез по секции с полками, мимо опор
    # различающие названия позиций (разбор 13.11: одинаковые имена у разных позиций — цех перепутает)
    kinds = {f"S{i + 1}-": ("со штангой" if k == "H" else ("с полками и ящиками" if inner_drawers else "с полками"))
             for i, k in enumerate(pattern)}
    hinge = {r["door"]: r["left"] for r in b.derived["doors"]}
    for p_ in b.P:
        if p_.kind != "board":
            continue
        pre = next((k for k in kinds if p_.id.startswith(k)), None)
        kd = kinds.get(pre, "")
        if "-SIDE-" in p_.id and "BOX" not in p_.id:
            base = "Боковина " + ("левая" if p_.id.endswith("-L") else "правая")
            p_.name = p_.unit = f"{base} {'антресоли над секцией' if '-M-' in p_.id else 'секции'} {kd}"
        elif "-SHELF-" in p_.id:
            p_.name = p_.unit = "Полка над штангой" if kd == "со штангой" else f"Полка жёсткая секции {kd}"
        elif "DOOR" in p_.id:
            side = "левая (петли слева)" if hinge.get(p_.id, True) else "правая (петли справа)"
            p_.name = p_.unit = f"Дверь {'антресоли ' if '-M-' in p_.id else ''}{side}"
        elif "-BOX" in p_.id and p_.id.endswith(("-SL", "-SR")):
            p_.name = p_.unit = "Боковина ящика " + ("левая" if p_.id.endswith("-SL") else "правая")
        elif p_.id == "PLINTH":
            p_.name = p_.unit = "Цоколь передний"
        elif p_.id in ("PLINTH-L", "PLINTH-R"):
            p_.name = p_.unit = "Цоколь торцевой"


# ============================================================ ARV-WRD-101 Шкаф распашной до потолка
def wrd101_top(H):
    """Высота стыка секция / антресоль: 2040 при 2400 … 2280 при 2800 (дверь секции ≤ 2180, антресоль 360–520)."""
    return int(round((2040 + (H - 2400) * 0.6) / 10) * 10)


def wardrobe_ceiling(o):
    W, H, D = int(o["width"]), int(o["height"]), int(o["depth"])
    color, handle, fill = o["color"], o["handle"], o["fill"]
    PL = LEG_H
    top = wrd101_top(H)
    n = -(-W // 600)
    b = Build("ARV-WRD-101", REV, NEW_STATUS, {"width": W, "height": H, "depth": D, "handle": handle, "fill": fill,
                                                 "color": color})
    pattern = "".join("H" if i % 2 == 0 else "S" for i in range(n))
    _sections_var(b, W, n, H, PL, top, D, color, pattern, push=(handle == "push"), inner_drawers=(fill == "drawers"))
    b.derived.update(width=W, depth=D, height=H, plinth=PL)
    _check(b, "Ширина = число секций × ширина секции", W, n * (W / n))
    _check(b, "Высота = опоры + секция + антресоль", H, PL + (top - PL) + (H - top))
    gap = PUSH_GAP if handle == "push" else 0
    _check(b, "Глубина = дверь + зазор TIP-ON + корпус + ХДФ", D, TF + gap + (D - TB - TF - gap) + TB)
    b.notes += [f"Шкаф до потолка: {n} секции по {W // n} мм; высота изделия {H} — потолок не ниже {H + 40} (зазор 40 "
                "закрывает планка, В-102).",
                f"Корпус ЛДСП 16 на Minifix, на регулируемых опорах {PL} (±15), цоколь на клипсах (В-37).",
                "В секциях с полками 2 полки жёсткие, остальные съёмные на полкодержателях (В-103).",
                "Двери ЛДСП 18 на петлях (кандидат, В-20): выше 2000 — 5 петель; " +
                (f"без ручек, TIP-ON; корпус отступает от двери на {PUSH_GAP} (В-104)." if handle == "push"
                 else "ручки 320 у свободной кромки, на антресоли 128.")]
    if D < 500:
        b.notes.append("Глубина 450: одежда на выдвижной штанге вдоль глубины (В-101).")
    if fill == "drawers":
        b.notes.append("В секциях с полками — 2 внутренних ящика Blum 560H TIP-ON (открывание нажатием, без ручек), "
                       "направляющие на проставках ЛДСП 16 — короб проходит мимо планки петли (В-105).")
    _MR._kq(b, "В-41", "В-102")
    b.derived["kq_text"] = {
        "В-37": ("Опоры регулируемые 100 (±15) и клипсы цоколя: артикул, нагрузка на опору (масса шкафа — лист 01, "
                 "4 опоры на секцию)",
                 "опоры, цоколь", "Arvello", "образцы, паспорт опоры"),
        "В-41": ("Монтаж шкафа: стяжки секций Ø5 (сверлить по месту), антресоли на секции, крепление к стене, проверка "
                 "вертикали и зазоров дверей после загрузки", "монтаж", "монтажник + Arvello", "техкарта монтажа"),
    }
    if H > 2600:
        b.warnings.append("Высота больше 2600: секции собирать на месте, проверить подъём и диагональ корпуса.")
    return b


# ============================================================ ARV-NST-101 Комод на 6 ящиков (+ пеленальный столик)
_F.update({
    "SCREW-4x25P": ("Саморез 4 × 25", "потай: через левую стойку в правую; вход 9, остаток 7", "типовой", "", "шт"),
    "SCREW-4x25T": ("Саморез 4 × 25", "потай: снизу через крышку комода в основание столика; вход 9, остаток 7",
                    "типовой", "", "шт"),
})
KQ3.update({
    "В-106": ("Пеленальный столик: матрас 700 × 500 × до 50 (внутри бортов 768 × 514), борт 150 — над матрасом 100; "
              "требования к пеленальным столикам (EN 12221) и устойчивость с уголками к стене проверить на отдельном образце "
              "до передачи клиенту; конкретный матрас выбрать и сверить", "столик", "Arvello",
              "образец столика до продажи, протокол проверки"),
})
_MR.KQ2.update(KQ3)


NST_PROFILE = "dspc"          # ENG-005 п. 1 (14.11): комод — по материалам ДСП Центра (cab.SUPPLY)
# ENG-005 п. 2 (14.11, 02:00 / 02:05): уровень фурнитуры — опция «level» комода; уровень → профиль направляющих
# (cab.SLIDE_PROFILES). Построитель марку не знает: смена профиля здесь пересобирает листы и смету.
# «blum» — прежний вариант MOVENTO / TANDEM (данные Blum сохранены, опция).
NST_SLIDES = "profile"
NST_LEVELS = {"eco": "samet-slidea-sc", "std": "samet-smart-sc", "comf": "samet-smart-posc"}
PUSH_FRONT_GAP = 2.5          # [М] зазор фасад — корпус под нажатие: в каталоге Samet full | Power не указан (В-108)
KQ3_SAMET = {
    "В-108": ("Направляющие (профиль cab.SLIDE_PROFILES): допущения [М] — {assumed}; утопление дна 13 (на сечении Samet «12»); "
              "крепление замков Lock-Fix по месту — сверить по инструкции монтажа и пробным ящиком", "ящики", "Arvello",
              "инструкция монтажа производителя, пробный ящик"),
}


def chest6(o):
    """Комод 2 × 3 ящика на цоколе; ручки или нажатие (MOVENTO TIP-ON BLUMOTION); опция — съёмный пеленальный столик."""
    W, changer = int(o["width"]), o["changer"] == "yes"
    samet = NST_SLIDES == "profile"
    level = o.get("level", "comf")
    if samet:
        prof = NST_LEVELS[level]
        handle = "push" if cab.SLIDE_PROFILES[prof]["push"] else "bar"   # без ручки — только с открыванием нажатием
    else:
        handle = o.get("handle", "push")
    # цвет — реальные декоры ДСП Центра (14.11): корпус (+ цоколь, столик) и фасады отдельно; короба и ХДФ — белые
    color, fcol = o.get("body", "K110"), o.get("front", "K4069")
    for k_, v_ in (("корпус", color), ("фасады", fcol)):
        if v_ not in cab.DSPC_DECORS:
            raise ValueError(f"{k_}: декор «{v_}» — не из базы ДСП Центра (cab.DSPC_DECORS)")
    H, PL = 880, 60
    D = 530 if changer else 500                  # со столиком глубже: матрас 700 × 500 ложится целиком (внутри 514)
    push = handle == "push"
    if samet:
        gap = PUSH_FRONT_GAP if push else 0
    else:
        gap = (2.5 if USE_MOVENTO_TOB else TIPON_GAP) if push else 0   # зазор фасад — корпус под TIP-ON
    b = Build("ARV-NST-101", REV, NEW_STATUS, {"width": W, **({"level": level} if samet else {"handle": handle}),
                                                "changer": o["changer"], "body": color, "front": fcol}, profile=NST_PROFILE)
    TF, TB = b.TF, b.TB
    yc0, yc1 = TF + gap, D - TB
    # стойка двойная (2 × 16): саморезы профилей Blum 4 × 15 с двух сторон одной плиты 16 встретились бы
    # корпуса эксцентриков каждой стойки — со стороны своей колонны (к ним есть доступ после стыковки стоек)
    # ХДФ: шаг ≈ 150, в двойную стойку — только в левую половину (обе под одной полосой ХДФ) [М], 13.11
    b.back_opts = {"step": cab.TECH["back_step"], "round": True, "skip": ["PART-2"]}
    c = b.carcass("", 0, W, PL, H, yc0, yc1, color, partitions=[(W / 2 - T, T, "Стойка левая", "+"),
                                                                  (W / 2, T, "Стойка правая", "-")], label="корпус")
    st, st2 = c["parts"][0], c["parts"][1]
    b.screws_into(st, st2, "+x", "y", [yc0 + 60, yc1 - 60], "SCREW-4x25P", "J-ST-PAIR", pilot=(3, 8), at=(PL + H) / 2)
    b.plinth("", c, PL, front=50, side=20, back=16)           # цвет — по профилю (ДСП Центр: в цвет корпуса)
    fl, ce = c["BOT"].z1, c["TOP"].z0
    for k, (cl, cr, x0, x1) in enumerate(((c["L"], st, 0, W / 2), (st2, c["R"], W / 2, W)), 1):
        hs = [(H - PL) / 3] * 3
        fr, z = [], PL
        for h in hs:
            fr.append((x0 + (GAP / 2 if k == 1 else GAP / 2), x1 - GAP / 2, z + GAP / 2, z + h - GAP / 2))
            z += h
        if samet:
            b.slide_drawers(f"C{k}-", c, cl, cr, fl, ce, fr, fcol, "INNER", prof, gap=gap,
                            handle=None if push else "bar128", box_max=150)
            continue
        mov = push and USE_MOVENTO_TOB
        b.drawers(f"C{k}-", c, cl, cr, fl, ce, fr, fcol, "INNER",
                  handle=None if push else "bar128", tipon=push, box_max=150 if mov else 170, movento=mov,
                  load=DRAWER_LOAD if mov else None)
    if push and USE_MOVENTO_TOB and not samet:
        b.derived["drawer_system"] = "MOVENTO TIP-ON BLUMOTION"
    _MR._anti_tip(b, 2)
    if changer:
        L, Dt, Hr = 800, D, 150                  # борт 150: над матрасом 50 остаётся 100 (сверить с EN 12221, В-106)
        base = b.part("CH-BASE", "Основание пеленального столика", 0, 0, H, L, Dt, H + T, "LDSP16", color, "top",
                      edges={"-y": "ABS2", "-x": "ABS2", "+x": "ABS2", "+y": "PVC04"})
        rb = b.part("CH-BACK", "Бортик столика задний", 0, Dt - T, H + T, L, Dt, H + T + Hr, "LDSP16", color, "top",
                    edges={"+z": "ABS2", "-x": "ABS2", "+x": "ABS2"})
        rl = b.part("CH-L", "Бортик столика левый", 0, 0, H + T, T, Dt - T, H + T + Hr, "LDSP16", color, "top",
                    edges={"+z": "ABS2", "-y": "ABS2"})
        rr = b.part("CH-R", "Бортик столика правый", L - T, 0, H + T, L, Dt - T, H + T + Hr, "LDSP16", color, "top",
                    edges={"+z": "ABS2", "-y": "ABS2"})
        b.conf(base, rb, "+z", "x", [60, L / 2, L - 60], "J-CH-BACK")
        b.conf(base, rl, "+z", "y", [60, Dt - T - 60], "J-CH-L")
        b.conf(base, rr, "+z", "y", [60, Dt - T - 60], "J-CH-R")
        b.conf(rb, rl, "-y", "z", [H + T + Hr / 2], "J-CH-BL")
        b.conf(rb, rr, "-y", "z", [H + T + Hr / 2], "J-CH-BR")
        tp = c["TOP"]
        for yy in (yc0 + 80, yc1 - 80):
            b.screws_into(tp, base, "+z", "x", [120, L - 120], "SCREW-4x25T", "J-CH-MOUNT", pilot=(3, 8), at=yy)
        b.buy("MAT", "Матрас пеленальный 700 × 500", "толщина до 50, моющийся чехол; модель подобрать и сверить размеры до "
              "выпуска (В-106)", 1, "кандидат", "В-106")
        b.buy("CAP-14", "Заглушка Ø14 в цвет", "закрыть отверстия крепления столика после снятия", 4, "типовой", "В-106")
        _MR._kq(b, "В-106")
        b.notes.append(f"Пеленальный столик 800 × {Dt}, бортики {Hr} с трёх сторон, съёмный (В-106).")
        b.derived["fits"] = [("матрас 700 × 500 внутри бортов", (700, 500), (L - 2 * T, Dt - T))]
        b.derived["mount_steps_after"] = ["Пеленальный столик: бортики к основанию конфирматами (узел В), поставить на "
                                          "крышку слева, 4 самореза 4 × 25 снизу через крышку (доступ — из верхнего ящика)."]
    # уголки крепления к стене (В-48): на крышке у задней кромки, площадка 40 × 40 (кандидат). Со столиком основание
    # занимает крышку слева (0 … 800) — левый уголок сдвигается вправо от основания (проверка ENG-002, 13.11).
    aw = 40
    xs = [80, W - 80] if not changer else [800 + 20 + aw / 2, W - 80]
    b.derived["wall_angles"] = [{"x0": x - aw / 2, "x1": x + aw / 2, "y0": yc1 - aw, "y1": yc1, "z": H} for x in xs]
    if changer:
        # 3-я точка слева (13.11, [М]): уголок ВНУТРИ левой колонны под крышкой — полка к крышке снизу, вторая полка через
        # ХДФ в стену. Не зависит от съёмного столика (крепление через бортик столика пропадёт при его снятии).
        # Над коробом верхнего ящика свободно ≈ 75 — уголок 40 проходит; проверка verify_new п. 16.
        b.derived["wall_angles"].append({"x0": T + 30, "x1": T + 30 + aw, "y0": yc1 - aw, "y1": yc1,
                                         "z0": H - T - aw, "z1": H - T, "z": H - T, "inside": True})
        b.hw["WALL-ANGLE"]["qty"] = 3
    Htot = H + T + Hr if changer else H
    b.derived.update(width=W, depth=D, height=Htot, plinth=PL, levels=[0, PL, H] + ([Htot] if changer else []))
    if changer:
        b.derived["preassembled"] = ["CH-"]       # столик собирают целиком до установки на комод
    b.derived["height_marks"] = [("корпус (без столика)", H)] + ([("рабочая поверхность столика", H + T),
                                                                  ("верх бортиков — габарит", Htot)] if changer else [])
    for p_ in b.P:                               # левые / правые и передние / задние — словами
        if p_.kind == "board" and "-BOX" in p_.id and p_.id.endswith(("-SL", "-SR")):
            p_.name = p_.unit = "Боковина ящика " + ("левая" if p_.id.endswith("-SL") else "правая")
        if p_.id in ("PL-F", "PL-B"):
            p_.name = p_.unit = "Цоколь " + ("передний" if p_.id == "PL-F" else "задний")
        if p_.id in ("PL-SL", "PL-SR"):
            p_.name = p_.unit = "Цоколь боковой " + ("левый" if p_.id == "PL-SL" else "правый")
    _check(b, "Ширина = 2 боковины + крышка", W, 2 * T + (c["TOP"].x1 - c["TOP"].x0))
    _check(b, "Высота = цоколь + боковина", H, PL + (c["L"].z1 - c["L"].z0))
    _check(b, "Глубина = фасад + зазор + корпус + ХДФ", D, TF + gap + (yc1 - yc0) + TB)
    b.notes += [f"Комод {W} × {D} × {H}: 2 колонки по 3 ящика, " + (
                f"{cab.SLIDE_PROFILES[prof]['name']} ({cab.SLIDE_PROFILES[prof]['level']}), NS {b.derived['drawers'][0]['NL']}"
                f" ({cab.SLIDE_PROFILES[prof]['ref'].split(' (')[0]})" + ("; без ручек, открывание нажатием." if push else
                "; ручки 128.") if samet else
                "Blum MOVENTO 760H + TIP-ON BLUMOTION (нажатие и мягкое закрытие); короб — дно в пазах боковин."
                if push and USE_MOVENTO_TOB else "Blum TANDEM со встроенным TIP-ON (нажатие)." if push else
                "Blum TANDEM BLUMOTION с ручками (мягкое закрытие)."),
                "Крепление к стене обязательно (детская комната): 2 уголка (В-48)."]
    if b.profile == "dspc":
        b.notes.append(f"Материалы — по базе ДСП Центра (ENG-005): ЛДСП 16 везде, фасады {TF}; кромка ПВХ 2 × 19 на фасадах и "
                       f"видимых торцах, ПВХ 1 × 19 на остальном; ХДФ {TB}; цоколь в цвет корпуса.")
        for k_, v_ in (("корпуса", color), ("фасадов", fcol)):
            if not cab.DSPC_DECORS[v_][3]:
                b.warnings.append(f"Кромка в цвет декора {k_} «{cab.DSPC_DECORS[v_][0]}» у ДСП Центра не проверена — "
                                  "проверить наличие до заказа.")
        if push and USE_MOVENTO_TOB and not samet:
            b.warnings.append(f"Фасад {TF} мм под MOVENTO + TIP-ON BLUMOTION: толщину фасада по документам Blum не сверяли "
                              "(Blum — на замену, ENG-005 п. 2).")
    _MR._kq(b, "В-48")
    if samet:
        q = KQ3_SAMET["В-108"]
        b.derived.setdefault("kq_text", {})["В-108"] = (q[0].format(assumed=cab.SLIDE_PROFILES[prof]["assumed"]),) + q[1:]
        _MR.KQ2["В-108"] = b.derived["kq_text"]["В-108"]
        _MR._kq(b, "В-108")
    return b


# ============================================================ реестр новых моделей
NEW: dict = {
    "ARV-WRD-101": ("Шкаф распашной до потолка", wardrobe_ceiling),
    "ARV-NST-101": ("Комод на 6 ящиков", chest6),
}
MODELS.update(NEW)
