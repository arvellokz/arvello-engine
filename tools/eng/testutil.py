"""Общий конец тестов: итог и код выхода (разбор 13.11, п. 5 — при расхождении тест возвращает 1, CI видит провал)."""
from __future__ import annotations

import sys


def finish(ok: bool) -> None:
    print("ИТОГ:", "все совпали" if ok else "есть расхождения")
    if not ok:
        sys.exit(1)
