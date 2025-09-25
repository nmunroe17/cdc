from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SRC = ROOT / "src"

for path in (TESTS, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
