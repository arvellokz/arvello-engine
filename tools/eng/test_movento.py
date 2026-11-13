"""MOVENTO 760H + TIP-ON BLUMOTION: точки профиля и короб сверяются с данными Blum для NL 350 / 400 / 450 / 500.

Эталон — выписано вручную из документов Blum, не из cab.py:
  каталог Blum 2024/25 с. 428 «Attachment of runners 760H – 40 kg», вариант A (саморез 609.1500 во все места):
  NL 300–350 — 19, 37, 69, 243, 261; NL 380–600 — 19, 37, 69, 243, 261, 293; ось саморезов — низ профиля + 38;
  конфигуратор Blum 12.11 (LW 568, NL 450, боковина 150): стенки 526 × 121, дно 536 × 440, боковины 440 × 150.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eng import cab  # noqa: E402

BLUM_PTS = {350: [19, 37, 69, 243, 261], 400: [19, 37, 69, 243, 261, 293], 450: [19, 37, 69, 243, 261, 293],
            500: [19, 37, 69, 243, 261, 293]}
res = []


def build(NL, LW=568, bh=150):
    b = cab.Build("TEST-MOV", "R01E", "тест", {})
    Dc = NL + 10.5                                  # наибольшая NL ряда: NL + 3 ≤ Dc и NL ≤ Dc − 10
    zf, zc = 100, 100 + 1 + bh + 60
    L = b.part("L", "Боковина", 0, 0, 0, 16, Dc, 400, "LDSP16", "W", "carcass")
    R = b.part("R", "Боковина", 16 + LW, 0, 0, 32 + LW, Dc, 400, "LDSP16", "W", "carcass")
    fr = [(0, 32 + LW, zf - 10, zf + bh + 40)]
    r = b.drawers("T-", {}, L, R, zf, zc, fr, "W", "W", handle=None, tipon=True, box_max=bh, movento=True, load=10)[0]
    return b, r


for NL, want in BLUM_PTS.items():
    b, r = build(NL)
    holes = [h for h in b.holes if h["joint"].startswith("J-T-RUNNER-1-L")]
    ys = sorted(round(h["y"], 1) for h in holes)
    zs = {round(h["z"] - r["rb"], 1) for h in holes}
    res.append((f"NL {NL}: точки профиля", ys == want and r["NL"] == NL, f"{ys} / эталон {want}"))
    res.append((f"NL {NL}: ось саморезов над низом профиля", zs == {38.0}, f"{zs}"))
    P = {p.id: p for p in b.P}
    sl, sr, fp, bp, bt = (P[i] for i in r["box"])
    size = lambda p: sorted(round(v, 1) for v in (p.x1 - p.x0, p.y1 - p.y0, p.z1 - p.z0))
    res.append((f"NL {NL}: боковина", size(sl) == sorted([16, 150, NL - 10]), size(sl)))
    res.append((f"NL {NL}: стенки", size(fp) == size(bp) == sorted([16, 121, 526]), size(fp)))
    bw = 536 - 2 * cab.TECH["bottom_clear"]          # раскрой Blum 536 минус наш зазор в пазах [М]
    res.append((f"NL {NL}: дно (Blum 536 − 2 × зазор)", size(bt) == sorted([16, bw, NL - 10]), size(bt)))
    res.append((f"NL {NL}: артикул", f"760H{NL * 10:04d}S" in b.hw["SLIDES"]["spec"], b.hw["SLIDES"]["spec"][:30]))
# NL 550 / 600 вне ряда генератора
try:
    cab.movento_points(550)
    res.append(("NL 550 вне ряда", False, "принята"))
except ValueError:
    res.append(("NL 550 вне ряда", True, "ValueError"))
for name, ok, t in res:
    print(f"{'✓' if ok else '✗'} {name:40s} | {t}")
from eng.testutil import finish  # noqa: E402
finish(all(r[1] for r in res))
