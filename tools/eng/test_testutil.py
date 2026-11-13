"""Негатив к п. 5 разбора 13.11: при расхождении finish() завершает процесс с кодом 1, при совпадении — без выхода."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
code = "import sys; sys.path.insert(0, %r); from eng.testutil import finish; finish(%s)"
bad = subprocess.run([sys.executable, "-c", code % (str(root), "False")], capture_output=True, text=True)
good = subprocess.run([sys.executable, "-c", code % (str(root), "True")], capture_output=True, text=True)
res = [("расхождение → код 1", bad.returncode == 1), ("совпадение → код 0", good.returncode == 0)]
for n, ok in res:
    print(f"{'✓' if ok else '✗'} {n}")
sys.exit(0 if all(ok for _, ok in res) else 1)
