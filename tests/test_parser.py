from pathlib import Path

from cdc_tool.parser import parse_design


FIXTURES = Path(__file__).parent / "fixtures"


def test_extracts_functional_clock_for_async_reset_block():
    design = parse_design([FIXTURES / "async_reset.v"])
    module = design.modules["async_reset_example"]

    assert module.registers["rst_sync"].clock == "clk"
    assert module.registers["state"].clock == "clk"
