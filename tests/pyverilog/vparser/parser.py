"""Minimal stub parser returning ASTs for regression fixtures."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from . import ast as vast


def parse(files: List[str]):
    modules = []
    for filename in files:
        text = Path(filename).read_text()
        modules.append(_parse_module(text))
    source = vast.Source(vast.Description(modules))
    return source, {}


_MODULE_RE = re.compile(r"module\s+(?P<name>\w+)\s*\((?P<ports>.*?)\);(?P<body>.*)endmodule", re.S)


def _parse_module(text: str) -> vast.ModuleDef:
    match = _MODULE_RE.search(text)
    if not match:
        raise ValueError("Unsupported module format in stub parser")

    name = match.group("name")
    ports_raw = match.group("ports")
    body = match.group("body")

    port_names = _parse_ports(ports_raw)
    portlist = vast.Portlist([vast.Port(vast.Identifier(p)) for p in port_names])

    registers = set(_find_regs(ports_raw)) | set(_find_regs(body))

    items: List[vast.Node] = []
    if registers:
        items.append(vast.Decl([vast.Reg(reg) for reg in sorted(registers)]))

    for header, block in _extract_always_blocks(body):
        sens = _parse_sensitivity_list(header)
        statement = _parse_block_statement(block)
        items.append(vast.Always(sens, statement))

    return vast.ModuleDef(name=name, portlist=portlist, items=items)


_PORT_NAME_RE = re.compile(r"(?:input|output|inout)\s+(?:wire|reg)?\s*(\w+)")


def _parse_ports(port_blob: str) -> List[str]:
    names: List[str] = []
    for part in port_blob.split(','):
        part = part.strip()
        if not part:
            continue
        match = _PORT_NAME_RE.search(part)
        if match:
            names.append(match.group(1))
        else:
            names.append(part.split()[-1])
    return names


_REG_RE = re.compile(r"\breg\b[^;]*?(\w+)")


def _find_regs(text: str) -> List[str]:
    return [match.group(1) for match in _REG_RE.finditer(text)]


def _extract_always_blocks(body: str) -> List[Tuple[str, str]]:
    blocks: List[Tuple[str, str]] = []
    index = 0
    while True:
        always_idx = body.find("always", index)
        if always_idx == -1:
            break
        paren_start = body.find("(", always_idx)
        paren_end = body.find(")", paren_start)
        sens = body[paren_start + 1 : paren_end]
        begin_idx = body.find("begin", paren_end)
        block_text, length = _collect_block(body[begin_idx:])
        block_text = block_text.replace("end else", "end\nelse")
        blocks.append((sens, block_text))
        index = begin_idx + length
    return blocks


def _collect_block(text: str) -> Tuple[str, int]:
    depth = 0
    idx = 0
    start = None
    length = len(text)
    while idx < length:
        if text.startswith("begin", idx):
            if start is None:
                start = idx
            depth += 1
            idx += len("begin")
            continue
        if text.startswith("end", idx):
            depth -= 1
            idx += len("end")
            if depth == 0 and start is not None:
                return text[start:idx], idx
            continue
        idx += 1
    raise ValueError("Unbalanced begin/end in always block")


def _parse_sensitivity_list(spec: str) -> vast.SensList:
    senses = []
    for clause in spec.split("or"):
        clause = clause.strip()
        if not clause:
            continue
        parts = clause.split()
        if len(parts) != 2:
            continue
        edge, signal = parts
        senses.append(vast.Sens(vast.Identifier(signal), edge))
    return vast.SensList(senses)


def _parse_block_statement(block_text: str) -> vast.Node:
    lines = [line.strip() for line in block_text.splitlines() if line.strip() and line.strip() != "begin" and line.strip() != "end"]
    if lines and lines[0].startswith("if"):
        return _parse_if_block(lines)
    return _statements_to_block(_parse_simple_statements(lines))


def _parse_if_block(lines: List[str]) -> vast.IfStatement:
    cond_match = re.search(r"!\s*(\w+)", lines[0])
    if not cond_match:
        raise ValueError("Unsupported if condition in stub parser")
    reset_signal = cond_match.group(1)

    reset_assigns: List[vast.Node] = []
    else_assigns: List[vast.Node] = []
    target_list = reset_assigns

    for line in lines[1:]:
        if line.startswith("else"):
            target_list = else_assigns
            continue
        if line.startswith("if"):
            continue
        if "<=" in line:
            target_list.append(_parse_assignment(line))

    return vast.IfStatement(
        cond=vast.Identifier(reset_signal),
        true_statement=_statements_to_block(reset_assigns),
        false_statement=_statements_to_block(else_assigns),
    )


def _parse_simple_statements(lines: List[str]) -> List[vast.Node]:
    statements: List[vast.Node] = []
    for line in lines:
        if "<=" in line:
            statements.append(_parse_assignment(line))
    return statements


def _parse_assignment(line: str) -> vast.NonblockingSubstitution:
    lhs, rhs = [part.strip() for part in line.rstrip(';').split('<=')]
    left = vast.Lvalue(vast.Identifier(lhs))
    if rhs.endswith("'b0") or rhs.endswith("'b1") or rhs.isdigit():
        right: vast.Node = vast.IntConst(rhs)
    else:
        right = vast.Identifier(rhs)
    return vast.NonblockingSubstitution(left, right)


def _statements_to_block(statements: List[vast.Node]) -> vast.Node:
    if not statements:
        return vast.Block([])
    if len(statements) == 1:
        return statements[0]
    return vast.Block(statements)


__all__ = ["parse"]
