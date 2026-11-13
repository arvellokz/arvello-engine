"""Общее инженерное ядро корпусной мебели и металлокаркасов Arvello (R01E).

Обобщение правил тумбы «Самал» R02E (eng/samal.py) на любые корпуса, и «Опоры» — на сварные рамы.
Модели (eng/models13.py) собирают изделие из модулей: корпус, цоколь/ножки/колёса/навес, ящики Blum,
двери, рама из трубы, столешница на резьбовых втулках.

Подтверждено документами (как в «Самал» R02E):
  Blum TANDEM 560H, RU me16460573 v4: BLUMOTION — стр. 20, 22, 39; встроенный TIP-ON — стр. 23, 24, 40
    (ряд NL, SKW = LW − 42, SKL = NL − 10, место NL + 3, утопление дна 12–15, низ дна → низ профиля
     27,5 / 28,5 (TIP-ON), ось саморезов → низ профиля 37 / 38, точки саморезов по таблицам стр. 39 / 40,
     замки T51.1700.04, синхронизатор TIP-ON T57.1140S, раскрой LW − 31; зазор фасада TIP-ON 3,5).
  Häfele Minifix 15 262.26.033 + болт S200 262.27.679, CFCD 2014 стр. 294, 301.
Остальная фурнитура — кандидаты: в листах и в спецификации помечена «кандидат», закрывается вопросами.

Система координат изделия как в «Самал»: x — ширина слева направо (вид спереди), y — глубина от лица (y = 0)
назад, z — высота от пола. Отверстие: {id, part, joint, kind, x, y, z, dir, d, depth, through, cs, fastener, note}.
"""
from __future__ import annotations

import math

from .core import Design, EPart, Hardware

T, TF, TB = 16, 18, 4
GAP = 3
ECC = {"housing_d": 15, "housing_depth": 12.5, "B": 24, "bolt_d": 8, "bolt_depth": 32, "stem_d": 5, "stem_depth": 12}
DOWEL = {"d": 8, "face_depth": 12, "edge_depth": 20}
CONF = {"d_face": 7, "d_edge": 5, "edge_depth": 36}
NL_SERIES = (250, 270, 300, 320, 350, 380, 400, 420, 450, 480, 500, 520, 550, 600)
# Blum стр. 39 (BLUMOTION) и стр. 40 (TIP-ON): точки крепления профиля, верхний ряд, от передней кромки корпуса
_PTS_BM = [((250, 270), (19, 37, 69, 133)), ((300, 380), (19, 37, 69, 165, 261)), ((400, 420), (19, 37, 69, 165, 229)),
           ((450, 480), (19, 37, 69, 165, 261)), ((500, 550), (19, 37, 69, 243, 261, 284)), ((600, 600), (19, 37, 69, 243, 261, 325))]
_PTS_TO = {250: (19, 37, 69, 133, 197), 270: (19, 37, 69, 133, 197), 300: (19, 37, 69, 165, 261), 320: (19, 37, 69, 165, 261),
           350: (19, 37, 69, 165, 261, 325), 380: (19, 37, 69, 165, 261, 357), 400: (19, 37, 69, 165, 229, 357),
           420: (19, 37, 69, 165, 261, 389), 450: (19, 37, 69, 165, 261, 421), 480: (19, 37, 69, 165, 261, 453),
           500: (19, 37, 69, 243, 261, 284, 453), 520: (19, 37, 69, 243, 261, 284, 485), 550: (19, 37, 69, 243, 261, 284, 517),
           600: (19, 37, 69, 243, 261, 325, 549)}
BLUM = {False: {"under": 27.5, "axis": 37, "art": "560H{:04d}B", "ref": "Blum TANDEM стр. 20, 22, 39", "name": "BLUMOTION"},
        True: {"under": 28.5, "axis": 38, "art": "560H{:04d}T", "ref": "Blum TANDEM стр. 23, 24, 40", "name": "встроенный TIP-ON"}}
RECESS = 13
TIPON_GAP = 3.5
# Blum MOVENTO 760H…S + TIP-ON BLUMOTION (docs/blum/2026-11-12_MOVENTO_TIP-ON-BLUMOTION.md):
#   каталог Blum 2022/23 (KA-150) стр. 436 — артикулы, набор TIP-ON BLUMOTION, синхронизация (LW − 267);
#   каталог Blum 2024/25 с. 428 «Attachment of runners, 760H – 40 kg» — места саморезов A (Ø3,5 × 15, 609.1500: ○ и ◐)
#   от передней кромки корпуса; DXF Blum (NL 450) — те же отверстия в профиле; точка 28 у 760H не используется;
#   «Space requirement» — низ дна → низ профиля 28,5, ось саморезов мин. 38 (39 — если профиль до сборки корпуса,
#   рисунок 76XHKOR), над ящиком 7; зазор фасада 2,5.
#   Короб — раскрой конфигуратора Blum 12.11: стенки = боковина − утопление 13 − дно 16, дно SKW + 10 в пазах боковин.
#   NL 550 / 600 не используются: у них дополнительная задняя точка «по желанию» (**), в генераторе не нужна.
MOV_SERIES = (270, 300, 320, 350, 380, 400, 420, 450, 480, 500, 520)
_PTS_MOV = {270: (19, 37, 69, 197), **{nl: (19, 37, 69, 243, 261) for nl in (300, 320, 350)},
            **{nl: (19, 37, 69, 243, 261, 293) for nl in (380, 400, 420, 450, 480, 500, 520)}}
MOVENTO = {"under": 28.5, "axis": 38, "art": "760H{:04d}S", "name": "TIP-ON BLUMOTION", "gap": 2.5,
           "ref": "Blum каталог 2022/23 стр. 436–437, TD-132", "groove": 5,
           "bottom_clear": 0.5}
# Технологические значения Arvello по умолчанию (решение владельца 12.11: не подстраиваемся под один цех — задаём сами
# по общепринятым нормам, держим в одном месте, проверяем пробой [О]). Выдерживают допуск толщины ЛДСП 16 разных
# поставщиков (обычно ±0,3). Меняются здесь — модель, чертежи и инструкции пересобираются.
TECH = {
    "groove_w_add": 0.5,      # паз под дно: ширина = толщина дна + 0,5 (дно 16 → паз 16,5)
    "bottom_clear": 0.5,      # зазор дна в пазу на сторону: дно = SKW + 2 × 5 − 2 × 0,5 (Blum зазор не задаёт)
    "blum_drill_by": "сборщик Arvello по шаблону Blum T65.1000.02 после сборки короба",   # крючок и замки
    # профиль над опорой (дном / полкой) на 1: Blum задаёт МИНИМУМ 38 от опоры до оси (39 — если профиль ставят до сборки
    # корпуса). Запас +1 держит минимум при допуске толщины плиты (±0,3 у разных поставщиков) и неровности дна и
    # покрывает оба порядка сборки. Это наше решение [М], Blum его не требует.
    "runner_lift": 1.0,
    # крепёж комода ARV-NST-101 (13.11, решение владельца — сократить) [М]:
    "back_step": 150,             # ХДФ: шаг саморезов ≈ 150 (к ближайшему), в двойную стойку — в одну половину
    "drawer_bottom_screws": 2,    # дно ящика MOVENTO → стенка: 2 самореза на стенку (4 на ящик)
    # Оформление для цеха по руководству БАЗИС «Создание документов с модели» (решение владельца 13.11). Где правило
    # зависит от цеха — типовой вариант руководства как наше значение [М], проверка пробой [О]:
    "op_order": "раскрой → облицовка кромок → присадка",     # БАЗИС с. 38 — типовая последовательность
    "dims_from": "от облицовки",   # размеры отверстий — от кромок детали с наклеенной облицовкой (БАЗИС 2.3.3)
    "edge_allow": 1.0,            # припуск на фуговку на каждую облицованную сторону, мм (заготовка = готовый − кромка + 1)
    "edge_order": "короткие → длинные",   # порядок облицовывания: длинная кромка перекрывает торцы коротких
    "countersink_d": 8.0,         # зенковка под головку самореза Ø3,5–4 в сквозном Ø4,5, со стороны входа самореза
}
MOVENTO["bottom_clear"] = TECH["bottom_clear"]

# Профиль материалов поставщика (ENG-005 п. 1, решение владельца 14.11: ориентир — ДСП Центр, Алматы). Профиль меняет
# толщину фасада и ХДФ (геометрия строится от них), заменяет кромку и декоры на то, что есть в базе поставщика.
# «base» — как было до 14.11 (36 старых моделей и шкаф WRD-101 пока на нём). Данные ДСП Центра:
# docs/поставщики/dspc/ДСП_Центр_база_материалов_2026-11-13.xlsx и смета 14.11 (кромка только ПВХ 1 и 2 мм × 19,
# ХДФ только 3 мм, ЛДСП 18 — только 13 декоров LT 2800 × 2120; к «Дуб натуральный» (Амберг 4090) нет кромки в цвет).
SUPPLY = {
    "base": {"name": "базовый (до 14.11)", "TF": 18, "TB": 4, "front_mat": "LDSP18", "back_mat": "HDF4",
             "edge_map": {}, "fin_map": {}, "back_fin": "INNER", "plinth_fin": "black", "base_names": {}},
    "dspc": {"name": "ДСП Центр (Алматы), 14.11", "TF": 16, "TB": 3, "front_mat": "LDSP16", "back_mat": "HDF3",
             # видимые кромки (фасады, передние торцы) ABS 2 → ПВХ 2 × 19; остальные ПВХ 0,4 → ПВХ 1 × 19
             "edge_map": {"ABS2": "PVC2", "PVC04": "PVC1"},
             "fin_map": {"O": "B4069", "INNER": "W110"},      # W, G — не сопоставлены (предупреждение)
             "back_fin": "HDFW", "plinth_fin": "body",
             "base_names": {"B4069": "ЛДСП Дуб Бунратти 4069 16*2750*1830 SwissKrono",
                            "W110": "ЛДСП Белый 110 (корпус) SM 16*2750*1830 SwissKrono",
                            "HDFW": "HDF ламинированный Белый фасадный 3*2500*2070 SH"}},
}
GRAIN_FINS = {"O", "B4069"}           # декоры с рисунком: деталь — с направлением текстуры
MAT_T = {"LDSP16": 16, "LDSP18": 18, "HDF4": 4, "HDF3": 3}


def _ru(x):
    return format(x, "g").replace(".", ",")


def movento_points(NL):
    if NL not in _PTS_MOV:
        raise ValueError(f"MOVENTO NL {NL}: вне ряда генератора (270–520)")
    return _PTS_MOV[NL]


def tob_unit(NL, kg):
    """Блок TIP-ON BLUMOTION по каталогу стр. 436: S0 / S1 для NL 270–320, L1 (≤ 20 кг) / L3 (15–40) для NL 350–600."""
    if NL <= 320:
        return ("S0", "T60L7040") if kg <= 10 else ("S1", "T60L7140")
    return ("L1", "T60L7340") if kg <= 20 else ("L3", "T60L7540")


def blum_points(NL, tipon):
    if tipon:
        return _PTS_TO[NL]
    return next(p for (a, b), p in _PTS_BM if a <= NL <= b)


def pick_nl(depth, series=NL_SERIES):
    """Наибольшая NL ряда Blum: NL + 3 ≤ глубина корпуса и NL ≤ глубина − 10 (как у «Самал»)."""
    ok = [s for s in series if s + 3 <= depth and s <= depth - 10]
    if not ok:
        raise ValueError(f"глубина {depth}: направляющая Blum 560H не помещается")
    return max(ok)


AX = "xyz"
# Крепёж: id -> (наименование, спецификация, статус, примечание, ед.)
FASTENERS = {
    "BED-BOLT": ("Стяжка кроватная: винт M6 × 90 + гайка-бочонок Ø10", "сталь оцинк., под шестигранник 4", "типовой", "", "шт"),
    "LIFT-BOLT": ("Болт мебельный M8 × 40 с гайкой и шайбой", "крепление механизма к борту (кандидат)", "кандидат", "В-44", "шт"),
    "WSCREW-5x80": ("Саморез по дереву 5 × 80", "потай, жёлтый цинк", "типовой", "", "шт"),
    "WSCREW-5x60": ("Саморез по дереву 5 × 60", "потай, жёлтый цинк", "типовой", "", "шт"),
    "WSCREW-4x40": ("Саморез по дереву 4 × 40", "потай, жёлтый цинк", "типовой", "", "шт"),
    "BOLT-M6x45": ("Болт M6 × 45 с шайбой", "DIN 912 / 7985, чёрный", "типовой", "", "шт"),
    "RIVNUT-M6": ("Гайка заклёпочная M6", "сталь, под отв. Ø9", "типовой", "", "шт"),
    "GLIDE-M8": ("Опора регулируемая M8", "h 20, Ø30, гайка M8 приварена к пластине (кандидат)", "кандидат", "В-26", "шт"),
    "ROD-SCREW": ("Саморез штангодержателя 3,5 × 16", "в комплекте держателя", "типовой", "", "шт"),
    "TRACK-SCREW": ("Саморез направляющей 4 × 16", "по системе дверей (кандидат)", "кандидат", "В-45", "шт"),
    "HOOK-SCREW": ("Саморез крючка 4 × 25", "в комплекте крючка", "типовой", "", "шт"),
    "PANEL-SCREW": ("Саморез 3,5 × 25", "потай: панель — основа", "типовой", "", "шт"),
    "ECC-15": ("Корпус эксцентрика Minifix 15", "Häfele 262.26.033, плита 16: A 8,0, X 12,5 +0,5 (стр. 294)", "по документу",
               "лист 2014 г. — сверить с поставкой", "шт"),
    "DOWEL-8x30": ("Шкант 8 × 30", "берёза, рифлёный", "типовой", "", "шт"),
    "CONF-7x50": ("Конфирмат 7 × 50", "под шестигранник 4", "типовой", "", "шт"),
    "SCREW-4x25": ("Саморез 4 × 25", "потай, по ЛДСП: фасад — короб", "типовой", "", "шт"),
    "SCREW-3.5x16": ("Саморез 3,5 × 16", "с прессшайбой, для ХДФ", "типовой", "", "шт"),
    "SCREW-M4x22": ("Винт ручки M4 × 22", "в комплекте ручки", "кандидат", "", "шт"),
    "SLIDE-SCREW": ("Саморез крепления профиля Blum", "Ø4 × 15 (тип A, Blum стр. 39 / 40)", "по документу", "", "шт"),
    "SLIDE-SCREW-M": ("Саморез крепления профиля MOVENTO", "Blum 609.1500, Ø3,5 × 15 (вариант A, каталог Blum 2024/25 "
                      "с. 428)", "по документу", "", "шт"),
    "SCREW-4x25D": ("Саморез 4 × 25", "потай: снизу через дно ящика в стенку; вход 9", "типовой", "", "шт"),
    "SCREW-4x13": ("Саморез 4 × 13", "полукруглая головка, под ножку / колесо / раму (остаток плиты ≥ 3)", "типовой", "", "шт"),
    "SCREW-4x30": ("Саморез 4 × 30", "потай: крышка корпуса — столешница (вход в столешницу 14)", "типовой", "", "шт"),
    "SCREW-6.3x13": ("Системный винт Ø6 (евровинт)", "предустановлен в планке 173L8100, отверстие Ø5 гл. 13 (Blum: Ø5, "
                     "min 11,5) — отдельно не заказывать", "в комплекте планки", "Blum 173L8100, каталог 2024/25 с. 154", "шт"),
    "SCREW-3.5x15": ("Саморез 3,5 × 15", "крепление чашки петли (схема 45 / 9,5), Blum 609.1500", "кандидат", "В-20", "шт"),
    "HANGER-SCREW": ("Саморез навеса 4 × 16", "в комплекте навеса", "кандидат", "", "шт"),
    "INSERT-M6": ("Втулка резьбовая M6", "RAMPA SK330 040615001, Ø12 × 15 (как «Опора»)", "кандидат",
                  "наличие у поставщика не подтверждено", "шт"),
    "SCREW-M6x16": ("Винт M6 × 16 с шайбой 6,4 × 18", "ISO 7380-1 / ISO 7093-1, A2", "кандидат", "", "шт"),
    "BOLT-M6x16": ("Винт M6 × 16 + заклёпочная гайка M6", "соединение балки с рамой", "кандидат", "", "компл"),
    "RIVNUT-M8": ("Заклёпочная гайка M8 + подпятник M8", "регулируемый, войлок/пластик, ход ≈10", "кандидат", "артикул не выбран", "компл"),
    "RIVNUT-M6G": ("Заклёпочная гайка M6 + подпятник M6", "регулируемый, Ø20, под трубу 20 × 20", "кандидат", "артикул не выбран", "компл"),
    "ANCHOR-M8": ("Анкер / болт к стене M8", "по типу стены (бетон, кирпич, ГКЛ с закладной)", "кандидат",
                  "тип стены неизвестен", "шт"),
    "SCREW-4x16C": ("Саморез 4 × 16 + шайба", "крепление полки к уголку рамы", "типовой", "", "шт"),
    "SCREW-M4x40": ("Винт ручки M4 × 40", "сквозь фасад 18 и стенку короба 16, ввёртывание в ручку ≥ 4", "кандидат", "", "шт"),
    "SCREW-ST4.2x13": ("Саморез по металлу 4,2 × 13", "лоток — балка", "типовой", "", "шт"),
    "SCREW-3x12": ("Саморез 3 × 12", "крепление профиля / устройства", "типовой", "", "шт"),
    "BRACKET-SCREW": ("Саморез 3,5 × 16", "к мебельному уголку", "типовой", "", "шт"),
    "TOP-CONN": ("Стяжка столешницы (евростяжка) 150", "с гайками, для соединения половин столешницы", "кандидат", "", "шт"),
}


def _g(p, ax, end):
    return getattr(p, ax + end)


def _mid(p, ax):
    return (_g(p, ax, "0") + _g(p, ax, "1")) / 2


class Build:
    """Накопитель изделия: детали, отверстия, соединения, фурнитура, проверки."""

    def __init__(self, sku, rev, rev_status, options, profile="base"):
        self.sku, self.rev, self.rev_status, self.options = sku, rev, rev_status, options
        self.profile = profile
        self.S = SUPPLY[profile]
        self.TF, self.TB = self.S["TF"], self.S["TB"]
        self.P, self.holes, self.joints = [], [], {}
        self.back_opts = {}           # {"step", "round", "skip": [id]} — крепёж ХДФ модели; пусто — как у всех (шаг ≤ 150)
        self.hw = {}
        self.checks, self.warnings, self.notes, self.blockers = [], [], [], []
        self.derived = {"drawers": [], "doors": [], "frames": [], "welds": [], "carcasses": [], "modules": set()}
        self.glows = []
        self.grain_override = {}

    # ------------------------------------------------------------------ детали и отверстия
    def part(self, pid, name, x0, y0, z0, x1, y1, z1, mat, fin, group, unit=None, edges=None, kind="board", axis="",
             note="", pos=None):
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            raise ValueError(f"{pid}: пустой объём {x0, y0, z0, x1, y1, z1}")
        e = EPart(pid, name, kind, round(x0, 3), round(y0, 3), round(z0, 3), round(x1, 3), round(y1, 3), round(z1, 3),
                  mat, fin, group, axis=axis, unit=unit or name, note=note)
        if kind == "board":
            S = self.S
            if fin in S["fin_map"] and not mat.startswith("HDF"):
                e.finish = S["fin_map"][fin]
            edges = {f: S["edge_map"].get(ty, ty) for f, ty in (edges or {}).items()}
            sz = {"x": e.x1 - e.x0, "y": e.y1 - e.y0, "z": e.z1 - e.z0}
            th = min(sz, key=sz.get)
            bad = [f for f in edges if f[1] == th]
            if bad:                  # 13.11 (ENG-003): кромка на пласти не бывает — ошибка модели, а не данные
                if self.profile != "base":
                    raise ValueError(f"{pid}: кромка на пласти {bad}")
                self.warnings.append(f"{pid}: кромка на пласти {bad} — проверить (ENG-005)")
            if mat in MAT_T and abs(sz[th] - MAT_T[mat]) > 0.01:
                raise ValueError(f"{pid}: толщина {sz[th]} ≠ материал {mat}")
        e.edges = dict(edges or {})
        e.grain = ""
        e.pos = pos
        self.P.append(e)
        return e

    def get(self, pid):
        return next(p for p in self.P if p.id == pid)

    def hole(self, pid, joint, kind, x, y, z, dr, d, depth, fastener=None, through=False, cs=False, note=""):
        h = {"id": f"H{len(self.holes) + 1:03d}", "part": pid, "joint": joint, "kind": kind, "x": round(x, 2),
             "y": round(y, 2), "z": round(z, 2), "dir": dr, "d": d, "depth": depth, "through": through, "cs": cs,
             "fastener": fastener, "note": note}
        self.holes.append(h)
        self.joints.setdefault(joint, []).append(h["id"])
        return h

    def buy(self, hid, name, spec, qty, status="кандидат", note="", uom="шт"):
        if hid in self.hw:
            self.hw[hid]["qty"] += qty
        else:
            self.hw[hid] = {"name": name, "spec": spec, "qty": qty, "status": status, "note": note, "uom": uom}

    # ------------------------------------------------------------------ соединения плит
    @staticmethod
    def _third(n_ax, along):
        return next(a for a in AX if a not in (n_ax, along))

    def ecc(self, F, E, n, along, vals, hdir_sign, joint):
        """Minifix 15 + S200: шток в пласть F, болт в торец E, корпус в пласть E на B = 24 от плоскости контакта.
        n — направление из F в E ('+x'…); along — ось линии стыка; hdir_sign '+'/'-' — с какой пласти E корпус.
        Ось болта — на A = 8,0 от пласти с корпусом (Häfele стр. 294); для плиты 16 это середина."""
        ax, sg = n[1], (1 if n[0] == "+" else -1)
        plane = _g(F, ax, "1") if sg > 0 else _g(F, ax, "0")
        th = self._third(ax, along)
        a_axis = _g(E, th, "0") + 8.0 if hdir_sign == "+" else _g(E, th, "1") - 8.0
        for v in vals:
            p = {ax: plane, along: v, th: a_axis}
            self.hole(F.id, joint, "ecc_stem", p["x"], p["y"], p["z"], ("-" if sg > 0 else "+") + ax, ECC["stem_d"],
                      ECC["stem_depth"], "ECC-15")
            self.hole(E.id, joint, "ecc_bolt", p["x"], p["y"], p["z"], n, ECC["bolt_d"], ECC["bolt_depth"])
            q = dict(p)
            q[ax] = plane + sg * ECC["B"]
            q[th] = _g(E, th, "0") if hdir_sign == "+" else _g(E, th, "1")
            self.hole(E.id, joint, "ecc_housing", q["x"], q["y"], q["z"], hdir_sign + th, ECC["housing_d"], ECC["housing_depth"])
        self.derived["modules"].add("ecc")

    def dowel(self, F, E, n, along, vals, joint):
        ax, sg = n[1], (1 if n[0] == "+" else -1)
        plane = _g(F, ax, "1") if sg > 0 else _g(F, ax, "0")
        th = self._third(ax, along)
        for v in vals:
            p = {ax: plane, along: v, th: _mid(E, th)}
            self.hole(F.id, joint, "dowel_face", p["x"], p["y"], p["z"], ("-" if sg > 0 else "+") + ax, DOWEL["d"],
                      DOWEL["face_depth"], "DOWEL-8x30")
            self.hole(E.id, joint, "dowel_edge", p["x"], p["y"], p["z"], n, DOWEL["d"], DOWEL["edge_depth"])

    def conf(self, F, E, n, along, vals, joint):
        """Конфирмат через F (вход с дальней пласти F, зенковка) в торец E."""
        ax, sg = n[1], (1 if n[0] == "+" else -1)
        near = _g(F, ax, "1") if sg > 0 else _g(F, ax, "0")
        far = _g(F, ax, "0") if sg > 0 else _g(F, ax, "1")
        tF = abs(near - far)
        th = self._third(ax, along)
        for v in vals:
            p = {ax: far, along: v, th: _mid(E, th)}
            self.hole(F.id, joint, "conf_face", p["x"], p["y"], p["z"], n, CONF["d_face"], tF, "CONF-7x50", through=True, cs=True)
            p[ax] = near
            self.hole(E.id, joint, "conf_edge", p["x"], p["y"], p["z"], n, CONF["d_edge"], CONF["edge_depth"])

    def bed_bolt(self, F, E, n, along, vals, joint, nut_sign, L=90, nut_at=60):
        """Стяжка кроватная: винт M6 × L через F (Ø7 насквозь) в торец E (Ø7 гл. L − tF + 5), гайка-бочонок Ø10 —
        поперёк E со стороны nut_sign ('+'/'−' по третьей оси), на nut_at от наружной пласти F."""
        ax, sg = n[1], (1 if n[0] == "+" else -1)
        near = _g(F, ax, "1") if sg > 0 else _g(F, ax, "0")
        far = _g(F, ax, "0") if sg > 0 else _g(F, ax, "1")
        tF = abs(near - far)
        th = self._third(ax, along)
        tE = _g(E, th, "1") - _g(E, th, "0")
        for v in vals:
            p = {ax: far, along: v, th: _mid(E, th)}
            self.hole(F.id, joint, "bed_face", p["x"], p["y"], p["z"], n, 7, tF, "BED-BOLT", through=True)
            p[ax] = near
            self.hole(E.id, joint, "bed_edge", p["x"], p["y"], p["z"], n, 7, L - tF + 5)
            q = dict(p)
            q[ax] = near + sg * (nut_at - tF)
            q[th] = _g(E, th, "1") if nut_sign == "+" else _g(E, th, "0")
            self.hole(E.id, joint, "bed_nut", q["x"], q["y"], q["z"], ("-" if nut_sign == "+" else "+") + th, 10,
                      round(tE / 2 + 5, 1))
        self.derived["modules"].add("bed_bolt")

    def screws_into(self, F_far, E, n, along, vals, fastener, joint, d_face=4.5, kind="screw_face", pilot=None, at=None):
        """Саморез через деталь F (сквозное с зенковкой) в пласть E (засверловка pilot = (d, глубина)).
        at — координата по третьей оси (по умолчанию середина F)."""
        ax, sg = n[1], (1 if n[0] == "+" else -1)
        F = F_far
        near = _g(F, ax, "1") if sg > 0 else _g(F, ax, "0")
        far = _g(F, ax, "0") if sg > 0 else _g(F, ax, "1")
        th = self._third(ax, along)
        for v in vals:
            p = {ax: far, along: v, th: _mid(F, th) if at is None else at}
            self.hole(F.id, joint, kind, p["x"], p["y"], p["z"], n, d_face, abs(near - far), fastener, through=True, cs=True)
            if pilot:
                p[ax] = near
                self.hole(E.id, joint, "pilot", p["x"], p["y"], p["z"], n, pilot[0], pilot[1])

    # ------------------------------------------------------------------ корпус
    def carcass(self, pre, x0, x1, z0, z1, yc0, yc1, color, partitions=(), shelves=(), back=True, top=True,
                vis_bottom=False, open_front=(), label="", side_drop=0):
        """Корпус по правилам «Самал»: боковины на всю высоту, крышка и дно между ними, Minifix + шканты,
        ХДФ 4 накладная. partitions — [(x_left, thickness, name)]: стойки между крышкой и дном;
        shelves — [(xa, xb, z_bottom, name, hdir)] постоянные полки между вертикалями."""
        Dc = yc1 - yc0
        L = self.part(f"{pre}SIDE-L", "Боковина левая", x0, yc0, z0 - side_drop, x0 + T, yc1, z1, "LDSP16", color, "carcass",
                      edges={"-y": "ABS2", "+z": "ABS2", "-z": "ABS2" if vis_bottom else "PVC04"})
        R = self.part(f"{pre}SIDE-R", "Боковина правая", x1 - T, yc0, z0 - side_drop, x1, yc1, z1, "LDSP16", color, "carcass",
                      edges={"-y": "ABS2", "+z": "ABS2", "-z": "ABS2" if vis_bottom else "PVC04"})
        TOP = self.part(f"{pre}TOP", "Крышка", x0 + T, yc0, z1 - T, x1 - T, yc1, z1, "LDSP16", color, "carcass",
                        edges={"-y": "ABS2"}) if top else None
        BOT = self.part(f"{pre}BOTTOM", "Дно", x0 + T, yc0, z0, x1 - T, yc1, z0 + T, "LDSP16", color, "carcass",
                        edges={"-y": "ABS2"})
        ys = self._ecc_ys(Dc, yc0)
        for S, n, hs in ((L, "+x", None), (R, "-x", None)):
            for B_, hd in ((TOP, "+"), (BOT, "-")):
                if B_ is None:
                    continue
                j = f"J-{pre}{S.id[-1]}-{B_.id[len(pre):]}"
                self.ecc(S, B_, n, "y", ys["ecc"], hd, j)
                self.dowel(S, B_, n, "y", ys["dowel"], j)
        parts = {"L": L, "R": R, "TOP": TOP, "BOT": BOT, "parts": []}
        verts = [L]
        for i, pt in enumerate(partitions, 1):
            xl, t, nm = pt[:3]
            phd = pt[3] if len(pt) > 3 else "+"      # с какой пласти стойки корпуса эксцентриков
            Pp = self.part(f"{pre}PART-{i}", nm or "Стойка", xl, yc0, z0 + T, xl + t, yc1, z1 - (T if top else 0), "LDSP16",
                           color, "carcass", edges={"-y": "ABS2"})
            for B_, n, hd in ((TOP, "-z", "+"), (BOT, "+z", "+")):
                if B_ is None:
                    continue
                j = f"J-{pre}PART{i}-{B_.id[len(pre):]}"
                self.ecc(B_, Pp, n, "y", ys["ecc"], phd, j)
                self.dowel(B_, Pp, n, "y", ys["dowel"], j)
            parts["parts"].append(Pp)
            verts.append(Pp)
        verts.append(R)
        parts["shelves"] = []
        for i, (xa, xb, zs, nm, hdir) in enumerate(shelves, 1):
            S_ = self.part(f"{pre}SHELF-{i}", nm or "Полка постоянная", xa, yc0, zs, xb, yc1, zs + T, "LDSP16", color,
                           "carcass", edges={"-y": "ABS2"})
            left = next(v for v in verts if abs(v.x1 - xa) < 0.01)
            right = next(v for v in verts if abs(v.x0 - xb) < 0.01)
            for V, n, tag in ((left, "+x", "L"), (right, "-x", "R")):
                j = f"J-{pre}SH{i}{tag}"
                ys2 = self._ecc_ys(Dc, yc0)
                self.ecc(V, S_, n, "y", ys2["ecc"], hdir, j)
                self.dowel(V, S_, n, "y", ys2["dowel"], j)
            parts["shelves"].append(S_)
        if back:
            BK = self.part(f"{pre}BACK", "Задняя стенка", x0 + 2, yc1, z0 + 2, x1 - 2, yc1 + self.TB, z1 - 2,
                           self.S["back_mat"], self.S["back_fin"],
                           "carcass")
            parts["BACK"] = BK
            self._back_screws(pre, verts, [b for b in (TOP, BOT) if b] + parts["shelves"], yc1, z0, z1, x0, x1)
        self.derived["carcasses"].append({"pre": pre, "x0": x0, "x1": x1, "z0": z0, "z1": z1, "yc0": yc0, "yc1": yc1,
                                          "Dc": Dc, "label": label, "verts": [v.id for v in verts]})
        return parts

    @staticmethod
    def _ecc_ys(Dc, yc0, shift=0):
        e = [37, Dc - 37] if Dc < 700 else [37, Dc / 2, Dc - 37]
        dw = [37 + 32, Dc - 37 - 32] if Dc < 700 else [37 + 32, Dc / 2 + 32, Dc - 37 - 32]
        return {"ecc": [yc0 + v + shift for v in e], "dowel": [yc0 + v + shift for v in dw]}

    def _back_screws(self, pre, verts, horiz, yc1, z0, z1, x0, x1):
        o = self.back_opts
        step, end = o.get("step", 150), 30
        verts = [V for V in verts if V.id not in o.get("skip", ())]

        def span(a, b):
            k = max(1, (round if o.get("round") else math.ceil)((b - a) / step))
            return [round(a + (b - a) * i / k) for i in range(k + 1)]
        for V in verts:
            for z in span(V.z0 + end, V.z1 - end):
                self.hole(V.id, f"J-{pre}BACK", "back_pilot", _mid(V, "x"), yc1, z, "-y", 2.5, 12, "SCREW-3.5x16")
        for Hh in horiz:
            for x in span(Hh.x0 + 28, Hh.x1 - 28):
                self.hole(Hh.id, f"J-{pre}BACK", "back_pilot", x, yc1, _mid(Hh, "z"), "-y", 2.5, 12, "SCREW-3.5x16")

    # ------------------------------------------------------------------ основания корпуса
    def plinth(self, pre, c, h, front=40, side=20, back=16, fin=None):
        """Рамка цоколя «Самал»: 4 детали на шкантах, к дну — конфирматами через дно."""
        BOT = c["BOT"]
        if fin is None:                               # ENG-005: у ДСП Центра цоколь в цвет корпуса (без листа ради 4 планок)
            fin = c["L"].finish if self.S["plinth_fin"] == "body" else self.S["plinth_fin"]
        x0, x1 = c["L"].x0, c["R"].x1
        yc0, yc1 = c["L"].y0, c["L"].y1
        px0, px1, py0, py1 = x0 + side, x1 - side, yc0 - self.TF + front, yc1 - back
        F = self.part(f"{pre}PL-F", "Цоколь продольный", px0, py0, 0, px1, py0 + T, h, "LDSP16", fin, "carcass",
                      edges={"-x": "PVC04", "+x": "PVC04"})
        Bk = self.part(f"{pre}PL-B", "Цоколь продольный", px0, py1 - T, 0, px1, py1, h, "LDSP16", fin, "carcass",
                       edges={"-x": "PVC04", "+x": "PVC04"})
        SL = self.part(f"{pre}PL-SL", "Цоколь боковой", px0, py0 + T, 0, px0 + T, py1 - T, h, "LDSP16", fin, "carcass")
        SR = self.part(f"{pre}PL-SR", "Цоколь боковой", px1 - T, py0 + T, 0, px1, py1 - T, h, "LDSP16", fin, "carcass")
        zz = (12, h - 12) if h >= 40 else (h / 2,)
        for strip, n in ((F, "+y"), (Bk, "-y")):
            for side_, in ((SL,), (SR,)):
                self.dowel(strip, side_, n, "z", zz, f"J-{pre}PL-{strip.id[-1]}-{side_.id[-2:]}")
        xs = [px0 + 50 + (px1 - px0 - 100) * i / max(1, round((px1 - px0 - 100) / 350)) for i in
              range(round((px1 - px0 - 100) / 350) + 1)]
        self.conf(BOT, F, "-z", "x", [round(x) for x in xs], f"J-{pre}BOT-PL-F")
        self.conf(BOT, Bk, "-z", "x", [round(x) for x in xs], f"J-{pre}BOT-PL-B")
        for S_ in (SL, SR):
            self.conf(BOT, S_, "-z", "y", [round((py0 + py1) / 2)], f"J-{pre}BOT-{S_.id[-5:]}")
        self.derived["modules"].add("plinth")
        return {"F": F, "B": Bk, "SL": SL, "SR": SR}

    def feet(self, pre, c, h, pts, kind, base, fin="black", name="Ножка", spec="", status="кандидат", note=""):
        """Покупные опоры под дном (ножки или колёса): площадка base × base, 4 самореза 4 × 13 в дно."""
        BOT = c["BOT"] if isinstance(c, dict) else c
        for i, (x, y) in enumerate(pts, 1):
            self.part(f"{pre}{kind}-{i}", name, x - base / 2, y - base / 2, BOT.z0 - h, x + base / 2, y + base / 2, BOT.z0,
                      kind, fin, "base", kind="buy", note=spec)
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                o = base / 2 - 8
                self.hole(BOT.id, f"J-{pre}{kind}{i}", "foot_screw", x + dx * o, y + dy * o, BOT.z0, "+z", 3, 10, "SCREW-4x13",
                          note="засверловка Ø3 гл. 10 по месту площадки")
        self.buy(kind, name, spec, len(pts), status, note)
        self.derived["modules"].add("feet")

    def hangers(self, pre, c, spec, status="кандидат", note=""):
        """Навес мебельный скрытый, 2 шт. в верхних задних углах; крепление к внутренней пласти боковин."""
        for S, sg in ((c["L"], "-x"), (c["R"], "+x")):
            xf = S.x1 if sg == "-x" else S.x0
            for dz in (30, 62):
                self.hole(S.id, f"J-{pre}HANG", "hanger_screw", xf, S.y1 - 40, S.z1 - dz, sg, 3, 10, "HANGER-SCREW",
                          note="засверловка по шаблону навеса")
        self.buy("HANGER", "Навес мебельный скрытый регулируемый", spec, 2, status, note)
        self.buy("HANGER-RAIL", "Шина навесная к стене", "длина = ширина корпуса − 40; крепление по типу стены", 1, status, note)
        self.derived["modules"].add("hang")

    # ------------------------------------------------------------------ фасады и ящики
    def drawers(self, pre, c, colL, colR, floor_z, ceil_z, fronts, color, inner_fin, handle="bar128", tipon=False,
                front_mat=None, front_t=None, front_edges=None, front_unit="Фасад ящика", box_max=None,
                handle_through=False, notch=None, caps=None, setback=0, movento=False, load=None):
        """Ящики Blum 560H (или MOVENTO 760H + TIP-ON BLUMOTION при movento=True) в проёме между colL и colR.
        fronts — [(fx0, fx1, fz0, fz1)] снизу вверх. Короба — по правилам «Самал» R02E (LW − 42, NL − 10, утопление 13);
        MOVENTO — по раскрою конфигуратора Blum: стенки на дне, дно в пазах боковин. load — груз в ящике, кг (блок TOB)."""
        if movento and (not tipon or handle or notch or setback):
            raise ValueError("MOVENTO: только накладной ящик TIP-ON BLUMOTION без ручки и выреза")
        sysd = MOVENTO if movento else BLUM[tipon]
        front_mat = front_mat or self.S["front_mat"]
        front_t = front_t or self.TF
        yc0, yc1 = colL.y0 + setback, colL.y1
        Dc = yc1 - yc0
        NL = pick_nl(Dc, MOV_SERIES if movento else NL_SERIES)
        LW = colR.x0 - colL.x1
        bx0, bx1 = colL.x1 + 5, colR.x0 - 5
        # накладной фасад крепится к коробу вплотную: короб начинается от тыльной стороны фасада. При TIP-ON / TIP-ON
        # BLUMOTION закрытый ящик стоит на зазор впереди корпуса (Blum: регулировка глубины, зазор фасада 2,5 / 3,5),
        # точки профиля — по-прежнему от передней кромки корпуса (yc0).
        by0 = yc0 if setback else min(yc0, front_t)
        by1 = by0 + NL - 10
        pts = movento_points(NL) if movento else blum_points(NL, tipon)
        recs = []
        hz_all = []
        f0 = fronts[0][2]
        rbs = [floor_z + TECH["runner_lift"] + (fz0 - f0) for (_, _, fz0, _) in fronts]
        for i, (fx0, fx1, fz0, fz1) in enumerate(fronts):
            n = i + 1
            rb = rbs[i]
            z0 = rb + sysd["under"] - RECESS
            limit = (rbs[i + 1] - 7) if i + 1 < len(fronts) else (ceil_z - 7)
            if caps and caps[i] is not None:
                limit = min(limit, caps[i])
            hz = None
            if handle:
                fh = fz1 - fz0
                hz = fz1 - 45 if fh > 160 else (fz0 + fz1) / 2
                if not handle_through:
                    limit = min(limit, hz - 4 - 2)
            bh = math.floor((limit - z0) / 10) * 10
            if box_max:
                bh = min(bh, box_max)
            if bh < 60:
                raise ValueError(f"{pre} ящик {n}: высота короба {bh} < 60")
            fy0 = yc0 - front_t if setback else 0
            fr = self.part(f"{pre}FRONT-{n}", front_unit, fx0, fy0, fz0, fx1, fy0 + front_t, fz1, front_mat, color,
                           "fronts", unit=front_unit, edges=front_edges or {"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
            k = f"{pre}BOX{n}"
            z1 = z0 + bh
            sl = self.part(f"{k}-SL", "Боковина ящика", bx0, by0, z0, bx0 + T, by1, z1, "LDSP16", inner_fin, "interior",
                           edges={"+z": "PVC04"})
            sr = self.part(f"{k}-SR", "Боковина ящика", bx1 - T, by0, z0, bx1, by1, z1, "LDSP16", inner_fin, "interior",
                           edges={"+z": "PVC04"})
            if not movento:
                fp = self.part(f"{k}-F", "Стенка ящика передняя", bx0 + T, by0, z0, bx1 - T, by0 + T, z1, "LDSP16", inner_fin,
                               "interior", edges={"+z": "PVC04"})
            zc = [40, bh - 35] if bh >= 100 else [bh / 2]
            if movento:
                boxids = self._mov_box(k, sl, sr, bx0, bx1, by0, by1, z0, z1, inner_fin)
                fp = self.get(boxids[2])
            elif not notch:
                bp = self.part(f"{k}-B", "Стенка ящика задняя", bx0 + T, by1 - T, z0, bx1 - T, by1, z1, "LDSP16", inner_fin,
                               "interior", edges={"+z": "PVC04"})
                bt = self.part(f"{k}-BOT", "Дно ящика", bx0 + T, by0 + T, z0 + RECESS, bx1 - T, by1 - T, z0 + RECESS + T, "LDSP16",
                               inner_fin, "interior")
                for side, panel_n in ((sl, "+x"), (sr, "-x")):
                    for panel in (fp, bp):
                        self.conf(side, panel, panel_n, "z", [z0 + v for v in zc], f"J-{k}-{side.id[-2:]}-{panel.id[-1]}")
                    self.conf(side, bt, panel_n, "y", [by0 + 76, by1 - 76], f"J-{k}-{side.id[-2:]}-BOT")
                xs_b = [bx0 + T + 80, bx1 - T - 80] if (bx1 - bx0 - 2 * T) >= 260 else [(bx0 + bx1) / 2]
                self.conf(fp, bt, "+y", "x", xs_b, f"J-{k}-F-BOT")
                self.conf(bp, bt, "-y", "x", xs_b, f"J-{k}-B-BOT")
                boxids = [sl.id, sr.id, fp.id, bp.id, bt.id]
            else:
                boxids = self._u_box(k, sl, sr, fp, bx0, bx1, by0, by1, z0, z1, bh, zc, inner_fin, notch)
            lo = fp.z0 + 30 if movento else z0 + 55   # у MOVENTO передняя стенка стоит на дне
            zs = [lo, z0 + bh - 15] if bh >= 100 else [lo]
            for x in (bx0 + T + 40, bx1 - T - 40):
                for z in zs:
                    self.hole(fp.id, f"J-{pre}FRONT{n}-BOX{n}", "front_screw", x, fp.y1, z, "-y", 4.5, T, "SCREW-4x25",
                              through=True, cs=True, note="зенковка изнутри короба; в фасад — без засверловки, вход 9")
            if handle:
                xc = (fx0 + fx1) / 2
                for x in (xc - 64, xc + 64):
                    if handle_through:
                        self.hole(fr.id, f"J-{pre}HANDLE{n}", "handle", x, 0, hz, "+y", 5, front_t, "SCREW-M4x40", through=True)
                        self.hole(fp.id, f"J-{pre}HANDLE{n}", "handle_box", x, fp.y0, hz, "+y", 5, T, through=True,
                                  note="сверлить вместе с фасадом по месту крепления (кондуктор ручки)")
                    else:
                        self.hole(fr.id, f"J-{pre}HANDLE{n}", "handle", x, 0, hz, "+y", 5, front_t, "SCREW-M4x22", through=True)
                self.part(f"{pre}HANDLE-{n}", "Ручка-скоба 128", xc - 80, -26, hz - 6, xc + 80, -14, hz + 6, "HANDLE-128",
                          "black", "fronts", kind="buy")
                for s_, xx in (("a", xc - 64), ("b", xc + 64)):
                    self.part(f"{pre}HANDLE-{n}{s_}", "Стойка ручки", xx - 5, -14, hz - 5, xx + 5, 0, hz + 5, "HANDLE-128", "black",
                              "fronts", kind="buy_part")
                hz_all.append(hz)
            for S, xf, dr in ((colL, colL.x1, "-x"), (colR, colR.x0, "+x")):
                za = rb + sysd["axis"]
                for yy in pts:
                    self.hole(S.id, f"J-{pre}RUNNER-{n}-{'L' if dr == '-x' else 'R'}", "runner_mark", xf, yc0 + yy, za, dr,
                              3.5 if movento else 4, 0, "SLIDE-SCREW-M" if movento else "SLIDE-SCREW", note="разметка, без сверления")
            recs.append({"pre": pre, "n": n, "NL": NL, "tipon": tipon, "LW": LW, "rb": rb, "z0": z0, "h": bh, "box_w": bx1 - bx0,
                         "inner_w": bx1 - bx0 - 2 * T, "box_l": NL - 10, "Dc": Dc, "colL": colL.id, "colR": colR.id,
                         "floor": floor_z, "ceil": ceil_z, "front": fr.id, "hz": hz, "pts": list(pts),
                         "box": boxids, "limit_top": limit, "through": handle_through, "notch": notch,
                         "front_t": front_t, "setback_front": bool(setback), "sys": "movento" if movento else "tandem",
                         "bottom_clear": MOVENTO["bottom_clear"] if movento else None,
                         "load": load})
        nd = len(fronts)
        self.derived["drawers"] += recs
        self.derived["modules"].add("tipon" if tipon else "blumotion")
        if movento:
            self._mov_hw(recs, NL, LW, load)
            return recs
        self.buy("SLIDES", "Направляющая TANDEM plus 560H (пара Л/П)", f"Blum {sysd['art'].format(NL * 10)}, NL {NL}, 30 кг, "
                 f"{sysd['name']} ({sysd['ref'].split(',')[0]})", nd, "по документу", "крепёж и замки в комплект не входят", "компл")
        self.buy("SLIDE-LOCK", "Замок ящика (пара Л/П)", "Blum T51.1700.04 (стр. 20 / 23)", nd, "по документу", "", "компл")
        self.buy("LOCK-SCREW", "Саморез крепления замка", "2 на замок (рисунок Blum); тип — по поставке Blum", 4 * nd,
                 "по рисунку", "тип самореза в документе не указан")
        if tipon:
            self.buy("TIPON-SYNC", "Вал синхронизатора TIP-ON", f"Blum T57.1140S, раскрой LW − 31 = {LW - 31} (стр. 23)", nd,
                     "по документу", "рекомендован при любой ширине корпуса", "шт")
        if handle:
            self.buy("HANDLE-128", "Ручка-скоба", "межосевое 128, чёрная матовая (как «Самал»)", nd, "кандидат", "", "шт")
        return recs

    def _mov_box(self, k, sl, sr, bx0, bx1, by0, by1, z0, z1, fin):
        """Короб MOVENTO по раскрою конфигуратора Blum (12.11): боковины на всю высоту, передняя и задняя стенки
        SKW × (h − 13 − 16) стоят на дне, дно (SKW + 10) × SKL в пазах боковин 16 × 5 на 13 от нижней кромки."""
        g = MOVENTO["groove"]
        zb0, zb1 = z0 + RECESS, z0 + RECESS + T
        E = {"+z": "PVC04"}
        fp = self.part(f"{k}-F", "Стенка ящика передняя", bx0 + T, by0, zb1, bx1 - T, by0 + T, z1, "LDSP16", fin, "interior", edges=E)
        bp = self.part(f"{k}-B", "Стенка ящика задняя", bx0 + T, by1 - T, zb1, bx1 - T, by1, z1, "LDSP16", fin, "interior", edges=E)
        c = MOVENTO["bottom_clear"]
        bt = self.part(f"{k}-BOT", "Дно ящика", bx0 + T - g + c, by0, zb0, bx1 - T + g - c, by1, zb1, "LDSP16", fin,
                       "interior")
        gr = self.derived.setdefault("grooves", [])
        for side, x0_, x1_ in ((sl, bx0 + T - g, bx0 + T), (sr, bx1 - T, bx1 - T + g)):
            gr.append({"part": side.id, "with": bt.id, "x0": x0_, "x1": x1_, "y0": by0, "y1": by1, "z0": zb0,
                       "z1": zb1 + TECH["groove_w_add"], "w": T + TECH["groove_w_add"], "depth": g, "from_edge": RECESS,
                       "note": f"паз {_ru(T + TECH['groove_w_add'])} × {g} по всей длине, от нижней кромки {RECESS} — под дно ящика "
                               f"(дно SKW + 10 − 2 × {_ru(TECH['bottom_clear'])}) [М]"})
        zc = [(zb1 - z0) + 25, (z1 - z0) - 25] if (z1 - zb1) >= 90 else [(zb1 + z1) / 2 - z0]
        for side, n in ((sl, "+x"), (sr, "-x")):
            for panel in (fp, bp):
                self.conf(side, panel, n, "z", [z0 + v for v in zc], f"J-{k}-{side.id[-2:]}-{panel.id[-1]}")
        xs = [bx0 + T + 80, (bx0 + bx1) / 2, bx1 - T - 80] if (bx1 - bx0 - 2 * T) >= 400 else [bx0 + T + 80, bx1 - T - 80]
        if TECH["drawer_bottom_screws"] == 2:          # сокращено 13.11 [М]: 2 на стенку, 4 на ящик
            xs = [bx0 + T + 80, bx1 - T - 80]
        for panel in (fp, bp):
            self.screws_into(bt, panel, "+z", "x", xs, "SCREW-4x25D", f"J-{k}-BOT-{panel.id[-1]}", pilot=(3, 8),
                             at=(panel.y0 + panel.y1) / 2)
        return [sl.id, sr.id, fp.id, bp.id, bt.id]

    def _mov_hw(self, recs, NL, LW, load):
        nd = len(recs)
        dens = 650                                   # ЛДСП, как в массе изделия (design)
        for r in recs:
            ps = [self.get(i) for i in r["box"]] + [self.get(r["front"])]
            own = sum((p.x1 - p.x0) * (p.y1 - p.y0) * (p.z1 - p.z0) / 1e9 * dens for p in ps)
            r["kg_own"] = round(own, 1)
            r["kg"] = round(own + (load or 0), 1)
        kg = max(r["kg"] for r in recs)
        unit, art = tob_unit(NL, kg)
        self.derived["tob"] = {"unit": unit, "art": art, "kg": kg, "load": load, "NL": NL, "LW": LW}
        self.buy("SLIDES", "Направляющая MOVENTO 760H BLUMOTION (пара Л/П) под TIP-ON BLUMOTION",
                 f"Blum {MOVENTO['art'].format(NL * 10)}, NL {NL}, 40 кг, полное выдвижение, зазор фасада 2,5 "
                 "(артикул — каталог Blum 2022/23 стр. 436 и конфигуратор 12.11; места саморезов — каталог 2024/25 с. 428)", nd, "по документу", "крепёж и замки отдельно", "компл")
        self.buy("SLIDE-LOCK", "Замок ящика MOVENTO (Л + П)", "Blum T51.7600 (конфигуратор 12.11; по отдельности — "
                 "T51.7601 Л/П, TD-132 стр. 3); крепление и крючок — шаблон T65.1000.02", nd, "по документу", "", "компл")
        self.buy("LOCK-SCREW", "Саморез крепления замка", "2 на замок (рисунок Blum); тип — по поставке Blum", 4 * nd,
                 "по рисунку", "тип самореза в документе не указан")
        sync = (f"синхронизация T60.1125W, отрез LW − 267 = {LW - 267:g}" if LW >= 314 else
                f"синхронизация одной деталью T60.300D, отрез LW − 241 = {LW - 241:g}")
        self.buy("TIPON-SYNC", "TIP-ON BLUMOTION: набор (блок + защёлка + адаптер) и синхронизация",
                 f"Blum {art} (блок {unit}; ящик с фасадом {_ru(max(r['kg_own'] for r in recs))} кг + груз {_ru(load or 0)} кг = "
                 f"{_ru(kg)} кг); {sync} (каталог стр. 436, монтаж TD-132 стр. 24)", nd,
                 "по документу", "груз в ящике принят — подтверждает Arvello", "компл")


    def _u_box(self, k, sl, sr, fp, bx0, bx1, by0, by1, z0, z1, bh, zc, fin, notch):
        """U-образный короб вокруг сифона: notch = (xc, ширина канала, y начала канала)."""
        xc, w, yf = notch
        xa, xb = xc - w / 2 - T, xc + w / 2 + T          # наружные грани стенок канала
        E = {"+z": "PVC04"}
        BL = self.part(f"{k}-BL", "Стенка ящика задняя", bx0 + T, by1 - T, z0, xa, by1, z1, "LDSP16", fin, "interior", edges=E)
        BR = self.part(f"{k}-BR", "Стенка ящика задняя", xb, by1 - T, z0, bx1 - T, by1, z1, "LDSP16", fin, "interior", edges=E)
        CL = self.part(f"{k}-CL", "Стенка канала", xa, yf + T, z0, xa + T, by1, z1, "LDSP16", fin, "interior", edges=E)
        CR = self.part(f"{k}-CR", "Стенка канала", xb - T, yf + T, z0, xb, by1, z1, "LDSP16", fin, "interior", edges=E)
        CF = self.part(f"{k}-CF", "Стенка канала поперечная", xa, yf, z0, xb, yf + T, z1, "LDSP16", fin, "interior", edges=E)
        zb0, zb1 = z0 + RECESS, z0 + RECESS + T
        BF = self.part(f"{k}-BOT", "Дно ящика переднее", bx0 + T, by0 + T, zb0, bx1 - T, yf, zb1, "LDSP16", fin, "interior")
        BBL = self.part(f"{k}-BOTL", "Дно ящика боковое", bx0 + T, yf, zb0, xa, by1 - T, zb1, "LDSP16", fin, "interior")
        BBR = self.part(f"{k}-BOTR", "Дно ящика боковое", xb, yf, zb0, bx1 - T, by1 - T, zb1, "LDSP16", fin, "interior")
        zz = [z0 + v for v in zc]
        self.conf(sl, fp, "+x", "z", zz, f"J-{k}-SL-F")
        self.conf(sr, fp, "-x", "z", zz, f"J-{k}-SR-F")
        self.conf(sl, BL, "+x", "z", zz, f"J-{k}-SL-B")
        self.conf(sr, BR, "-x", "z", zz, f"J-{k}-SR-B")
        self.conf(CL, BL, "-x", "z", zz, f"J-{k}-CL-B")
        self.conf(CR, BR, "+x", "z", zz, f"J-{k}-CR-B")
        self.conf(CF, CL, "+y", "z", zz, f"J-{k}-CF-CL")
        self.conf(CF, CR, "+y", "z", zz, f"J-{k}-CF-CR")
        zm = (zb0 + zb1) / 2
        self.conf(sl, BF, "+x", "y", [by0 + 60], f"J-{k}-SL-BOT")
        self.conf(sr, BF, "-x", "y", [by0 + 60], f"J-{k}-SR-BOT")
        self.conf(sl, BBL, "+x", "y", [(yf + by1) / 2], f"J-{k}-SL-BOTL")
        self.conf(sr, BBR, "-x", "y", [(yf + by1) / 2], f"J-{k}-SR-BOTR")
        self.conf(fp, BF, "+y", "x", [bx0 + T + 80, bx1 - T - 80], f"J-{k}-F-BOT")
        self.conf(CF, BF, "-y", "x", [xc], f"J-{k}-CF-BOT")
        self.conf(BL, BBL, "-y", "x", [(bx0 + T + xa) / 2], f"J-{k}-BL-BOTL")
        self.conf(BR, BBR, "-y", "x", [(xb + bx1 - T) / 2], f"J-{k}-BR-BOTR")
        # стыки дна: переднее ↔ боковые — шканты 8 × 30 в торцы (вдоль y)
        self.dowel(BF, BBL, "+y", "x", [(bx0 + T + xa) / 2], f"J-{k}-BOT-BOTL")
        self.dowel(BF, BBR, "+y", "x", [(xb + bx1 - T) / 2], f"J-{k}-BOT-BOTR")
        return [sl.id, sr.id, fp.id, BL.id, BR.id, CL.id, CR.id, CF.id, BF.id, BBL.id, BBR.id]

    def bracket(self, A, B_, n_a, pts, joint):
        """Мебельный уголок 30 × 30 изнутри: по саморезу 3,5 × 16 в пласть A (вход по n_a) и в пласть B."""
        for (pa, pb) in pts:
            self.hole(A.id, joint, "bracket_pilot", *pa, 3, 10, "BRACKET-SCREW")
            self.hole(B_.id, joint, "bracket_pilot", *pb, 3, 10, "BRACKET-SCREW")
        self.buy("BRACKET", "Уголок мебельный 30 × 30", "сталь оцинк., 2 отверстия Ø4", len(pts), "типовой")

    def merge(self, sub, fmap, dmap):
        """Перенос узла sub (собран в своих координатах) поворотом вокруг Z: fmap(x, y, z) -> (X, Y, Z),
        dmap('+x') -> '-y' и т. п."""
        for p in sub.P:
            a = fmap(p.x0, p.y0, p.z0)
            b = fmap(p.x1, p.y1, p.z1)
            q = EPart(p.id, p.name, p.kind, round(min(a[0], b[0]), 3), round(min(a[1], b[1]), 3), round(min(a[2], b[2]), 3),
                      round(max(a[0], b[0]), 3), round(max(a[1], b[1]), 3), round(max(a[2], b[2]), 3), p.material, p.finish,
                      p.group, axis=dmap("+" + p.axis)[1] if p.axis else "", unit=p.unit, note=p.note)
            q.edges = {dmap(f): t for f, t in p.edges.items()}
            q.grain, q.pos = "", None
            self.P.append(q)
        for h in sub.holes:
            X, Y, Z = fmap(h["x"], h["y"], h["z"])
            nh = dict(h, x=round(X, 2), y=round(Y, 2), z=round(Z, 2), dir=dmap(h["dir"]), id=f"H{len(self.holes) + 1:03d}")
            self.holes.append(nh)
            self.joints.setdefault(nh["joint"], []).append(nh["id"])
        for k, v in sub.hw.items():
            self.buy(k, v["name"], v["spec"], v["qty"], v["status"], v["note"], v["uom"])
        for key in ("drawers", "doors", "carcasses"):
            for r in sub.derived[key]:
                self.derived[key].append(dict(r, rotated=True))
        self.derived["modules"] |= sub.derived["modules"]

    def doors(self, pre, c, hinge_side, fronts, color, handle="bar128", hz_from_top=50, lefts=None, nh_rule=None):
        """Распашные двери на петлях (кандидат Blum CLIP top 110°, накладные, планка 0): чашка Ø35 гл. 13,
        центр чашки 22,5 от кромки двери; планка — 2 отверстия Ø5 гл. 13 на 37 от передней кромки боковины, ± 16."""
        recs = []
        for i, ((fx0, fx1, fz0, fz1), S) in enumerate(zip(fronts, hinge_side), 1):
            d = self.part(f"{pre}DOOR-{i}", "Дверь", fx0, 0, fz0, fx1, self.TF, fz1, self.S["front_mat"], color, "fronts",
                          unit="Дверь",
                          edges={"-x": "ABS2", "+x": "ABS2", "-z": "ABS2", "+z": "ABS2"})
            left = abs(S.x0 - min(p.x0 for p in self.P if p.group == "carcass")) < 400 and S.id.endswith("SIDE-L")
            if lefts is not None:
                left = lefts[i - 1]
            xc = fx0 + 22.5 if left else fx1 - 22.5
            hd = fz1 - fz0
            nh = 2 if hd <= 900 else 3 if hd <= 1500 else 4
            if nh_rule:
                nh = nh_rule(hd)
            hs = [fz0 + 100 + (hd - 200) * k / (nh - 1) for k in range(nh)]
            xin = 9.5 if left else -9.5                          # отверстия чашки — к середине двери
            xf, dr = (S.x1, "-x") if left else (S.x0, "+x")
            for k, z in enumerate(hs, 1):
                self.hole(d.id, f"J-{pre}HINGE{i}", "hinge_cup", xc, self.TF, z, "-y", 35, 13, "HINGE",
                          note="кандидат: размер C и глубина — по каталогу петли")
                for dz in (-22.5, 22.5):
                    self.hole(d.id, f"J-{pre}HINGE{i}", "hinge_cup_screw", xc + xin, self.TF, z + dz, "-y", 2.5, 8, "SCREW-3.5x15",
                              note="засверловка под саморез чашки, схема 45 / 9,5")
                for dz in (-16, 16):
                    self.hole(S.id, f"J-{pre}HINGE{i}", "hinge_plate", xf, S.y0 + 37, z + dz, dr, 5, 13, "SCREW-6.3x13",
                              note="кандидат: монтажная планка 0 мм")
            if handle == "v320":
                hx = fx1 - 40 if left else fx0 + 40
                zc = fz1 - hz_from_top
                for z in (zc - 160, zc + 160):
                    self.hole(d.id, f"J-{pre}DHANDLE{i}", "handle", hx, 0, z, "+y", 5, self.TF, "SCREW-M4x22", through=True)
                self.part(f"{pre}DHANDLE-{i}", "Ручка-скоба 320", hx - 6, -26, zc - 176, hx + 6, -14, zc + 176, "HANDLE-320",
                          "black", "fronts", kind="buy")
                for s_, zz in (("a", zc - 160), ("b", zc + 160)):
                    self.part(f"{pre}DHANDLE-{i}{s_}", "Стойка ручки", hx - 5, -14, zz - 5, hx + 5, 0, zz + 5, "HANDLE-320",
                              "black", "fronts", kind="buy_part")
                self.buy("HANDLE-320", "Ручка-скоба вертикальная", "межосевое 320, чёрная матовая", 1, "кандидат", "", "шт")
            elif handle:
                hz = fz1 - hz_from_top
                xc2 = (fx0 + fx1) / 2
                for x in (xc2 - 64, xc2 + 64):
                    self.hole(d.id, f"J-{pre}DHANDLE{i}", "handle", x, 0, hz, "+y", 5, self.TF, "SCREW-M4x22", through=True)
                self.part(f"{pre}DHANDLE-{i}", "Ручка-скоба 128", xc2 - 80, -26, hz - 6, xc2 + 80, -14, hz + 6, "HANDLE-128", "black",
                          "fronts", kind="buy")
                for s_, xx in (("a", xc2 - 64), ("b", xc2 + 64)):
                    self.part(f"{pre}DHANDLE-{i}{s_}", "Стойка ручки", xx - 5, -14, hz - 5, xx + 5, 0, hz + 5, "HANDLE-128",
                              "black", "fronts", kind="buy_part")
                self.buy("HANDLE-128", "Ручка-скоба", "межосевое 128, чёрная матовая (как «Самал»)", 1, "кандидат", "", "шт")
            recs.append({"door": d.id, "side": S.id, "hinges": len(hs), "left": left})
        n = sum(r["hinges"] for r in recs)
        self.buy("HINGE", "Петля накладная 110° с доводчиком", "кандидат Blum CLIP top BLUMOTION 71B3550 (на саморезы) + "
                 "планка 0 мм 173L8100 (системные винты Ø6 предустановлены, каталог Blum 2024/25 с. 154)",
                 n, "кандидат", "нужен каталог Blum CLIP top (В-20)")
        self.derived["doors"] += recs
        self.derived["modules"].add("doors")

    # ------------------------------------------------------------------ металл
    def tube(self, pid, name, x0, y0, z0, x1, y1, z1, prof, fin, axis, unit=None, group="frame"):
        return self.part(pid, name, x0, y0, z0, x1, y1, z1, prof, fin, group, unit=unit or name, kind="tube", axis=axis)

    def plate(self, pid, name, x0, y0, z0, x1, y1, z1, fin, group="frame", mat="S235-4"):
        return self.part(pid, name, x0, y0, z0, x1, y1, z1, mat, fin, group, unit=name, kind="plate")

    def weld(self, a, b):
        self.derived["welds"].append((a.id, b.id))

    def top_fix(self, top, tubes, ys_or_xs, along, joint, insert=True):
        """Столешница к раме. insert=True: в верхней стенке трубы Ø7, в нижней — технологическое Ø13; винт M6 × 16
        в резьбовую втулку M6 (Ø10 гл. 17) в столешнице снизу. insert=False (тонкая столешница): саморез 4 × 16
        через Ø4,5 в верхней стенке, засверловка Ø3 гл. 12 в столешницу; в нижней стенке Ø8."""
        for tb in tubes:
            for v in ys_or_xs:
                p = {"x": _mid(tb, "x"), "y": _mid(tb, "y"), along: v}
                if not (_g(tb, along, "0") + 15 <= v <= _g(tb, along, "1") - 15):
                    continue
                if insert:
                    self.hole(tb.id, joint, "tube_top", p["x"], p["y"], tb.z1, "-z", 7, 2, "SCREW-M6x16", through=True,
                              note="верхняя стенка")
                    self.hole(tb.id, joint, "tube_access", p["x"], p["y"], tb.z0, "+z", 13, 2, through=True,
                              note="нижняя стенка — доступ ключа")
                    self.hole(top.id, joint, "insert", p["x"], p["y"], top.z0, "+z", 10, 17, "INSERT-M6",
                              note="втулка RAMPA SK330 по разметке с готовой рамы")
                else:
                    self.hole(tb.id, joint, "tube_top", p["x"], p["y"], tb.z1, "-z", 4.5, 2, "SCREW-4x16C", through=True,
                              note="верхняя стенка")
                    self.hole(tb.id, joint, "tube_access", p["x"], p["y"], tb.z0, "+z", 8, 2, through=True)
                    self.hole(top.id, joint, "pilot", p["x"], p["y"], top.z0, "+z", 3, 12, note="засверловка по раме")
        self.derived["modules"].add("top_fix" if insert else "top_screw")

    def glide(self, tb, pts, joint, fastener="RIVNUT-M8", d=11):
        for (x, y) in pts:
            self.hole(tb.id, joint, "rivnut", x, y, tb.z0, "+z", d, 2, fastener, through=True, note="заклёпочная гайка в нижнюю стенку")

    # ------------------------------------------------------------------ сборка снимка
    def design(self):
        hw_count = {}
        for h in self.holes:
            if h["fastener"]:
                hw_count[h["fastener"]] = hw_count.get(h["fastener"], 0) + 1
        d = Design(self.sku, self.rev, self.rev_status, self.options, {}, self.P, holes=self.holes, glows=self.glows)
        hw = []
        for k, v in self.hw.items():
            hw.append(Hardware(k, v["name"], v["spec"], v["qty"], v["status"], v["note"], v["uom"]))
        for k, q in sorted(hw_count.items()):
            if k in self.hw or k == "HINGE":
                continue
            nm, spec, st, note, uom = FASTENERS[k]
            hw.append(Hardware(k, nm, spec, q, st, note, uom))
        if "ecc" in self.derived["modules"]:
            hw.append(Hardware("ECC-BOLT", "Болт стяжки S200", "Häfele 262.27.679, B 24, резьба 11 под Ø5 (стр. 301)",
                               hw_count.get("ECC-15", 0), "по документу", "лист 2014 г. — сверить с поставкой"))
        if hw_count.get("DOWEL-8x30"):
            hw.append(Hardware("GLUE-PVA", "Клей ПВА D3", "для шкантов", round(0.002 * hw_count["DOWEL-8x30"], 2), "типовой", "", "кг"))
        d.hardware = hw
        boards = [p for p in self.P if p.kind == "board"]
        for p in boards:
            if p.finish in GRAIN_FINS:
                sz = {"x": p.x1 - p.x0, "y": p.y1 - p.y0, "z": p.z1 - p.z0}
                p.grain = self.grain_override.get(p.id) or max(sz, key=sz.get)
        for p in boards:
            p.edge_m = round(sum(max(_edge_len(p, f)) for f in p.edges) / 1000, 3)
        mass = 0.0
        for p in self.P:
            vol = (p.x1 - p.x0) * (p.y1 - p.y0) * (p.z1 - p.z0) / 1e9
            if p.kind == "board":
                mass += vol * (850 if p.material.startswith("HDF") else 760 if p.material.startswith("MDF") else 650)
            elif p.kind == "tube":
                mass += _tube_kg_m(p.material) * p.length / 1000
            elif p.kind == "plate":
                mass += vol * 7850
        der = dict(self.derived)
        der["modules"] = sorted(der["modules"])
        der["mass_kg"] = round(mass + self.derived.get("mass_modules", 0), 1)
        der["parts_ext"] = {p.id: {"edges": p.edges, "grain": p.grain, "pos": p.pos} for p in self.P if p.kind == "board"}
        der["joints"] = self.joints
        der["edge_abs2_m"] = round(sum(max(_edge_len(p, f)) for p in boards for f, t in p.edges.items() if t == "ABS2") / 1000, 2)
        der["edge_m"] = {}
        for p in boards:
            for f_, t_ in p.edges.items():
                der["edge_m"][t_] = der["edge_m"].get(t_, 0) + max(_edge_len(p, f_)) / 1000
        der["edge_m"] = {k: round(v, 2) for k, v in der["edge_m"].items()}
        der["supplier"] = {"profile": self.profile, **{k: self.S[k] for k in ("name", "base_names")}}
        der["edge_04_m"] = round(sum(max(_edge_len(p, f)) for p in boards for f, t in p.edges.items() if t == "PVC04") / 1000, 2)
        d.derived = der
        d.ops = {"board_cut": len(boards), "drill_hole": len(self.holes), "tube_cut": sum(p.kind == "tube" for p in self.P),
                 "weld_joint": len(self.derived["welds"]), "assembly": 1}
        d.checks = self.checks
        d.warnings = self.warnings
        d.notes = self.notes
        d.blockers = self.blockers
        return d


def _edge_len(p, face):
    sx, sy, sz = p.x1 - p.x0, p.y1 - p.y0, p.z1 - p.z0
    return {"-x": (sy, sz), "+x": (sy, sz), "-y": (sx, sz), "+y": (sx, sz), "-z": (sx, sy), "+z": (sx, sy)}[face]


def _tube_kg_m(prof):
    import re
    m = re.match(r"TUBE(\d+)x(\d+)x([\d.]+)", prof)
    if not m:
        return 2.0
    a, b, t = map(float, m.groups())
    return (a * b - (a - 2 * t) * (b - 2 * t)) * 7850 / 1e6
