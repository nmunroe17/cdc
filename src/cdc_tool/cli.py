"""Command line interface for the CDC analysis tool."""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path
from typing import List, Optional, Sequence, TextIO

from .analyzer import analyze_design
from .parser import parse_design
from .reports import format_report

DEFAULT_RULES = {"unsafe_crossing"}


def _expand_globs(patterns: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern, recursive=True))
        files.extend(Path(match) for match in matches)
    unique: List[Path] = []
    seen = set()
    for path in files:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clock-domain crossing analysis tool")
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input Verilog files or glob patterns",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Report format (default: text)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. Defaults to stdout.",
    )
    parser.add_argument(
        "--disable-rule",
        dest="disabled_rules",
        action="append",
        default=[],
        help="Disable a rule (may be specified multiple times)",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List available analysis rules and exit",
    )
    return parser


def _list_rules(stream: TextIO = sys.stdout) -> None:
    for rule in sorted(DEFAULT_RULES):
        print(rule, file=stream)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.list_rules:
        _list_rules()
        return 0

    files = _expand_globs(args.inputs)
    if not files:
        parser.error("no input files matched the provided patterns")

    try:
        design = parse_design(files)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error parsing design: {exc}", file=sys.stderr)
        return 2

    report = analyze_design(design, disabled_rules=args.disabled_rules)
    try:
        rendered = format_report(report, args.format)
    except ValueError as exc:
        parser.error(str(exc))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered)

    return report.exit_code()


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
