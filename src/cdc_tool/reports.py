"""Report generation utilities for CDC analysis."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from .analyzer import AnalysisReport, Crossing


def _crossing_to_dict(crossing: Crossing) -> Dict[str, Any]:
    data = asdict(crossing)
    return data


def render_text(report: AnalysisReport) -> str:
    lines = ["Clock Domains:"]
    if not report.clock_domains:
        lines.append("  (none detected)")
    else:
        for name, domain in sorted(report.clock_domains.items()):
            registers = ", ".join(sorted(domain.registers)) or "(no registers)"
            lines.append(f"  {name}: {registers}")

    lines.append("")
    lines.append("Crossings:")
    if not report.crossings:
        lines.append("  (none detected)")
    else:
        for crossing in report.crossings:
            status = "OK" if crossing.safe or crossing.rule in report.disabled_rules else "VIOLATION"
            lines.append(
                "  - {module}.{register} <= {signal} ({source}->{target}): {status} [{reason}]".format(
                    module=crossing.module,
                    register=crossing.register,
                    signal=crossing.signal,
                    source=crossing.source_domain or "comb",
                    target=crossing.target_domain or "comb",
                    status=status,
                    reason=crossing.reason,
                )
            )
    return "\n".join(lines)


def render_json(report: AnalysisReport) -> str:
    payload: Dict[str, Any] = {
        "clock_domains": {
            name: sorted(domain.registers)
            for name, domain in sorted(report.clock_domains.items())
        },
        "crossings": [_crossing_to_dict(crossing) for crossing in report.crossings],
        "disabled_rules": sorted(report.disabled_rules),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def format_report(report: AnalysisReport, fmt: str) -> str:
    if fmt == "text":
        return render_text(report)
    if fmt == "json":
        return render_json(report)
    raise ValueError(f"unsupported report format: {fmt}")


__all__ = [
    "format_report",
    "render_json",
    "render_text",
]
