"""Шрифт листов — из репозитория (разбор 13.11, Windows без DejaVu Sans): наш файл подключён; без файла — ошибка."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
from eng import fonts  # noqa: E402
from eng import sheetlib  # noqa: E402,F401  подключает шрифт при импорте
from eng.testutil import finish  # noqa: E402

res = []
got = sheetlib.FONTS
res.append(("обычный и жирный — из tools/eng/fonts/",
            all(Path(p).parent == fonts.FONT_DIR for p in got.values())))
try:
    fonts.setup(tempfile.mkdtemp())                       # пустая папка — как Windows без шрифта
    res.append(("нет файла шрифта → ошибка", False))
except fonts.FontMissing:
    res.append(("нет файла шрифта → ошибка", True))
fonts.setup()
import matplotlib.pyplot as plt  # noqa: E402
fig = plt.figure()
t = fig.text(0.1, 0.5, "Короба на конфирматах", weight="bold")
from matplotlib import font_manager as fm  # noqa: E402
res.append(("текст листа берёт наш файл", Path(fm.findfont(t.get_fontproperties())).parent == fonts.FONT_DIR))
for n, ok in res:
    print(f"{'✓' if ok else '✗'} {n}")
finish(all(ok for _, ok in res))
