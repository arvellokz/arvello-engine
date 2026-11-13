"""Шрифт листов из репозитория (tools/eng/fonts/), не из системы.

Разбор 13.11: у ChatGPT на Windows не было DejaVu Sans, matplotlib молча подставил другой шрифт — строка вышла за
рамку. Теперь шрифт подключается из файлов репозитория; другие «DejaVu Sans» (системные, из matplotlib) убираются из
списка; если файла нет или подставился не наш файл — ошибка, а не замена.
"""
from __future__ import annotations

from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "fonts"
FAMILY = "DejaVu Sans"
FILES = ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf")


class FontMissing(RuntimeError):
    pass


def font_file(name="DejaVuSans.ttf", font_dir=None):
    p = Path(font_dir or FONT_DIR) / name
    if not p.is_file():
        raise FontMissing(f"нет файла шрифта {p} — листы не строятся (подмена шрифта запрещена)")
    return str(p)


def setup(font_dir=None):
    """Подключить шрифт из папки репозитория для matplotlib; вернуть {вес: путь}. Ошибка — если файла нет."""
    import matplotlib
    from matplotlib import font_manager as fm

    d = Path(font_dir or FONT_DIR).resolve()
    paths = [font_file(f, d) for f in FILES]
    fm.fontManager.ttflist = [f for f in fm.fontManager.ttflist if f.name != FAMILY]   # только наш файл
    for p in paths:
        fm.fontManager.addfont(p)
    fm.fontManager._findfont_cached.cache_clear()
    matplotlib.rcParams["font.family"] = FAMILY
    matplotlib.rcParams["font.sans-serif"] = [FAMILY]
    matplotlib.rcParams["pdf.fonttype"] = 42            # шрифт вкладывается в PDF целиком
    got = {}
    for w in ("normal", "bold"):
        f = Path(fm.findfont(fm.FontProperties(family=FAMILY, weight=w), fallback_to_default=False)).resolve()
        if f.parent != d:
            raise FontMissing(f"вместо шрифта из {d} подставлен {f}")
        got[w] = str(f)
    return got



