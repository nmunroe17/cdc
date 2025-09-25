"""Verilog front-end for the CDC analysis tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from pyverilog.vparser import ast as vast
from pyverilog.vparser.parser import parse


@dataclass
class Net:
    """Representation of a net (wire) in a Verilog module."""

    name: str
    kind: str = "wire"


@dataclass
class Register:
    """Representation of a sequential element in a Verilog module."""

    name: str
    module: str
    clock: Optional[str] = None
    drivers: Set[str] = field(default_factory=set)


@dataclass
class Module:
    """Container holding the signals that make up a Verilog module."""

    name: str
    ports: Set[str] = field(default_factory=set)
    nets: Dict[str, Net] = field(default_factory=dict)
    registers: Dict[str, Register] = field(default_factory=dict)


@dataclass
class DesignGraph:
    """High-level view of the design produced by the parser."""

    modules: Dict[str, Module]

    def iter_modules(self) -> Iterable[Module]:
        for module in self.modules.values():
            yield module

    def iter_registers(self) -> Iterable[Register]:
        for module in self.iter_modules():
            yield from module.registers.values()

    def find_register(self, name: str, module: Optional[Module] = None) -> Optional[Register]:
        """Find a register by name, optionally scoping to a module."""

        if module is not None and name in module.registers:
            return module.registers[name]
        for mod in self.modules.values():
            if name in mod.registers:
                return mod.registers[name]
        return None


class _IdentifierCollector(vast.NodeVisitor):
    """Collect identifier names used inside expressions."""

    def __init__(self) -> None:
        self.names: Set[str] = set()

    def visit_Identifier(self, node: vast.Identifier) -> None:  # pragma: no cover - trivial
        self.names.add(node.name)

    @classmethod
    def collect(cls, node: vast.Node) -> Set[str]:
        collector = cls()
        collector.visit(node)
        return collector.names


class _DesignBuilder(vast.NodeVisitor):
    """Traverse the AST to build a :class:`DesignGraph`."""

    def __init__(self) -> None:
        self.modules: Dict[str, Module] = {}
        self._module_stack: List[Module] = []
        self._clock_stack: List[Optional[str]] = []

    # Helpers -----------------------------------------------------------------
    @property
    def module(self) -> Module:
        return self._module_stack[-1]

    @property
    def current_clock(self) -> Optional[str]:
        return self._clock_stack[-1] if self._clock_stack else None

    # Visit methods -----------------------------------------------------------
    def visit_ModuleDef(self, node: vast.ModuleDef) -> None:
        module = Module(name=node.name)
        self._module_stack.append(module)
        try:
            for item in node.items or []:
                self.visit(item)
        finally:
            self._module_stack.pop()
            self.modules[module.name] = module

    def visit_Portlist(self, node: vast.Portlist) -> None:  # pragma: no cover - structural
        for port in node.ports or []:
            if isinstance(port, vast.Port) and isinstance(port.first, vast.Identifier):
                self.module.ports.add(port.first.name)
            elif isinstance(port, vast.Identifier):
                self.module.ports.add(port.name)

    def visit_Input(self, node: vast.Input) -> None:  # pragma: no cover - structural
        self.module.ports.add(node.name)

    def visit_Output(self, node: vast.Output) -> None:  # pragma: no cover - structural
        self.module.ports.add(node.name)

    def visit_Inout(self, node: vast.Inout) -> None:  # pragma: no cover - structural
        self.module.ports.add(node.name)

    def visit_Decl(self, node: vast.Decl) -> None:
        for decl in node.list or []:
            if isinstance(decl, vast.Reg):
                self.module.registers.setdefault(
                    decl.name,
                    Register(name=decl.name, module=self.module.name),
                )
            elif isinstance(decl, vast.Wire):
                self.module.nets.setdefault(
                    decl.name,
                    Net(name=decl.name, kind="wire"),
                )

    def visit_InstanceList(self, node: vast.InstanceList) -> None:  # pragma: no cover - stub
        # We do not model hierarchy at the moment, but continue traversal.
        for inst in node.instances or []:
            self.visit(inst)

    def visit_Always(self, node: vast.Always) -> None:
        clock = self._extract_clock(node)
        self._clock_stack.append(clock)
        try:
            self.visit(node.statement)
        finally:
            self._clock_stack.pop()

    def visit_BlockingSubstitution(self, node: vast.BlockingSubstitution) -> None:
        self._handle_assignment(node.left, node.right)

    def visit_NonblockingSubstitution(self, node: vast.NonblockingSubstitution) -> None:
        self._handle_assignment(node.left, node.right)

    # Internal helpers --------------------------------------------------------
    def _extract_clock(self, node: vast.Always) -> Optional[str]:
        sens = node.sens_list
        if not isinstance(sens, vast.SensList):
            return None

        candidates: List[str] = []

        def _looks_like_reset(name: str) -> bool:
            lowered = name.lower()
            return any(token in lowered for token in ("rst", "reset", "areset", "srst", "clr"))

        for entry in sens.list:
            if not isinstance(entry, vast.Sens):
                continue
            if entry.type not in {"posedge", "negedge"}:
                continue
            if not isinstance(entry.sig, vast.Identifier):
                continue
            signal = entry.sig.name
            candidates.append(signal)
            if not _looks_like_reset(signal):
                return signal

        if candidates:
            return candidates[-1]
        return None

    def _handle_assignment(self, left: vast.Node, right: vast.Node) -> None:
        if not isinstance(left, vast.Lvalue):
            return
        target = left.var
        if isinstance(target, vast.Pointer):
            target = target.var
        if isinstance(target, vast.Identifier):
            name = target.name
        else:
            return

        register = self.module.registers.get(name)
        if register is None:
            return
        clock = self.current_clock
        if clock is not None and register.clock is None:
            register.clock = clock
        register.drivers.update(_IdentifierCollector.collect(right))


def parse_design(files: Sequence[Path]) -> DesignGraph:
    """Parse the given Verilog files into a :class:`DesignGraph`."""

    if not files:
        raise ValueError("no input files were provided")

    paths = [Path(path) for path in files]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"the following design files are missing: {', '.join(missing)}"
        )

    ast, _ = parse([str(path) for path in paths])
    builder = _DesignBuilder()
    builder.visit(ast)
    return DesignGraph(modules=builder.modules)


__all__ = [
    "DesignGraph",
    "Module",
    "Net",
    "Register",
    "parse_design",
]
