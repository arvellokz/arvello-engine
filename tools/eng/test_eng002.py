"""ENG-002: проверка рисунков сборщику — крепёж показан со стороны, с которой его вкручивают, и не закрыт деталью.

Негативный случай — ошибка листа 5 первой версии (проверка Codex, п. 1): саморезы фасада нарисованы на виде спереди,
точки попали на лицевую сторону фасада. Проверка должна дать ошибку.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import eng002_drawer as E  # noqa: E402
from eng.sheetlib import Sheet  # noqa: E402

OPTS = {"width": "1200", "handle": "push", "changer": "yes", "color": "O"}
res = []
D = E.drawer_data(OPTS)
p = D["p"]
fs = E.joint_holes(D, "FRONT", "front_screw")
all5 = [p[k] for k in ("SL", "SR", "F", "B", "BOT")]
st = E.stamp(D, "тест")


def run(boxes, **kw):
    sh = Sheet("тест", st, 1, 1, "—")
    ob = E.Oblique(sh, (40, 20, 200, 120), boxes, **kw)
    ob.draw([(b, E.DONE, {}) for b in boxes])
    ob.fasteners(fs)
    E.kit13.plt.close(sh.fig)
    return ob.errors


# 1. как в первой версии: вид спереди, фасад перед коробом — саморезы «на лице фасада»
e = run(all5 + [p["FR"]], sgn=1)
res.append(("вид спереди с фасадом (ошибка v1)", bool(e), e[:1]))
# 2. вид сзади, но с задней стенкой — вход закрыт задней стенкой
e = run(all5 + [p["FR"]], sgn=1, ys=-1)
res.append(("вид сзади, задняя стенка закрывает", bool(e), e[:1]))
# 3. правильный вид: сзади, без задней стенки
e = run([p[k] for k in ("SL", "SR", "F", "BOT")] + [p["FR"]], sgn=1, ys=-1)
res.append(("вид изнутри (сзади, без задней стенки)", not e, e[:1]))
# 4. весь пример листов: ни одной ошибки
D2, _ = E.write("/tmp/eng002_test.pdf", OPTS)
res.append(("пример листов целиком", not D2["view_errors"], D2["view_errors"][:1]))
for name, ok, t in res:
    print(f"{'✓' if ok else '✗'} {name:44s} | {t}")
print("ИТОГ:", "все совпали" if all(r[1] for r in res) else "есть расхождения")
