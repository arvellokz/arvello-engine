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

OPTS = {"width": "1200", "handle": "push", "changer": "yes", "body": "K110", "front": "K4069"}
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
# 5. инструкция A4 (П11–П14): все проверки выпуска пройдены
from eng import eng002_guide as G  # noqa: E402
D3, r3 = G.write("/tmp/eng002_guide_test.pdf", OPTS)
res.append(("инструкция A4: проверки выпуска", all(x[1] for x in r3), [x[0] for x in r3 if not x[1]]))
# 6. негатив: круг-увеличение без сопрягаемой детали (только деталь входа) — проверка должна дать ошибку
pg = G.Page(D3, 1, 1, "тест")
h = E.joint_holes(D3, "BOT-", "screw_face")[0]
z = G.zoom(pg, D3, h, 100, 150, keys=("BOT",))
D3["zooms"] = [("тест", h, z)]
D3["view_errors"] = []
bad = [x for x in G.verify_guide(D3, []) if x[0].startswith("Круг") and not x[1]]
res.append(("круг без сопрягаемой детали → ошибка", bool(bad), z["parts"]))
G.plt.close(pg.fig)
# 7. инструкция на весь комод (П1): все проверки выпуска, в т. ч. крепёж в шагах = спецификации
from eng import eng002_chest as C  # noqa: E402
for ch in ("yes", "no"):
    D4, r4 = C.write(f"/tmp/eng002_chest_{ch}.pdf", {**OPTS, "changer": ch})
    res.append((f"комод, столик {ch}: проверки выпуска", all(x[1] for x in r4), [x for x in r4 if not x[1]][:1]))
# 8. негатив: шаг «забыл» крепёж (задняя стенка не учтена) — сумма не совпадёт со спецификацией
D4["used"].pop("SCREW-3.5x16", None)
bad = C.verify_counts(D4)
res.append(("крепёж шага не учтён → ошибка", bool(bad), bad[:1]))
# 9. негатив П16: у парной детали пропала буква Л / П — проверка выпуска должна дать ошибку
orig_sl = G.side_letter
G.side_letter = lambda name: "" if "Стойка" in name else orig_sl(name)
_, r5 = C.write("/tmp/eng002_chest_lab.pdf", OPTS)
res.append(("наклейка стойки без Л / П → ошибка", any(x[0].startswith("Наклейки") and not x[1] for x in r5), ""))
G.side_letter = orig_sl
# 10. негатив (Codex 13.11, вид снизу): отверстие со входом не снизу на виде дна → ошибка
Dn = E.drawer_data(OPTS); Dn["view_errors"] = []
pgn = G.Page(Dn, 1, 1, "тест")
bad_h = [dict(h, dir="-z") for h in E.joint_holes(Dn, "BOT-", "screw_face")]
G.bottom_view(pgn, Dn, (20, 20, 180, 120), holes=bad_h)
G.plt.close(pgn.fig)
res.append(("вид снизу: вход не снизу → ошибка", bool(Dn["view_errors"]), Dn["view_errors"][:1]))
# 11. комплект: один снимок на исполнение (манифест)
from eng import eng002_kit as K  # noqa: E402
_, kf = K.build("/tmp/eng002_kit")
res.append(("комплект: один снимок, проверки пройдены", not kf, kf[:1]))
for name, ok, t in res:
    print(f"{'✓' if ok else '✗'} {name:44s} | {t}")
from eng.testutil import finish  # noqa: E402
finish(all(r[1] for r in res))
