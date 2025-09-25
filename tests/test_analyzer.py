from pathlib import Path

from cdc_tool.analyzer import analyze_design
from cdc_tool.parser import parse_design


FIXTURES = Path(__file__).parent / "fixtures"


def test_async_reset_block_does_not_appear_as_crossing():
    design = parse_design([FIXTURES / "async_reset.v"])
    report = analyze_design(design)

    offending = [
        crossing
        for crossing in report.crossings
        if crossing.module == "async_reset_example" and crossing.register == "state"
    ]

    assert offending == []
