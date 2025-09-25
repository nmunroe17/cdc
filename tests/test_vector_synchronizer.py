from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

pytest.importorskip("pyverilog")

from cdc_tool.analyzer import analyze_design
from cdc_tool.parser import parse_design


def test_vector_synchronizer_first_stage_is_safe():
    design = parse_design([Path(__file__).parent / "fixtures" / "vector_sync.v"])
    report = analyze_design(design)

    first_stage = next(
        (crossing for crossing in report.crossings if crossing.register == "sync[0]"),
        None,
    )
    assert first_stage is not None
    assert first_stage.safe
    assert first_stage.reason == "two-stage synchronizer"
    assert not report.has_violations()
