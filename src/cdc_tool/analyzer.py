"""Clock domain analysis for the CDC tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from .parser import DesignGraph, Module, Register


@dataclass
class ClockDomain:
    """Registers associated with a particular clock signal."""

    name: str
    registers: Set[str] = field(default_factory=set)


@dataclass
class Crossing:
    """Represents a single observed clock-domain crossing."""

    module: str
    signal: str
    register: str
    source_domain: Optional[str]
    target_domain: Optional[str]
    safe: bool
    reason: str
    rule: str = "unsafe_crossing"


@dataclass
class AnalysisReport:
    """Aggregated data from the analysis stage."""

    clock_domains: Dict[str, ClockDomain]
    crossings: List[Crossing]
    disabled_rules: Set[str] = field(default_factory=set)

    def violations(self) -> List[Crossing]:
        return [
            crossing
            for crossing in self.crossings
            if not crossing.safe and crossing.rule not in self.disabled_rules
        ]

    def has_violations(self) -> bool:
        return bool(self.violations())

    def exit_code(self) -> int:
        return 1 if self.has_violations() else 0


def derive_clock_domains(design: DesignGraph) -> Dict[str, ClockDomain]:
    domains: Dict[str, ClockDomain] = {}
    for register in design.iter_registers():
        if register.clock is None:
            continue
        domain = domains.setdefault(register.clock, ClockDomain(name=register.clock))
        domain.registers.add(register.name)
    return domains


def _collect_module_registers(design: DesignGraph) -> Dict[str, Dict[str, Register]]:
    return {module.name: module.registers for module in design.iter_modules()}


def _is_synchronized(register: Register, module: Module) -> bool:
    """Very small heuristic for detecting two-stage synchronizers."""

    for candidate in module.registers.values():
        if candidate is register:
            continue
        if candidate.clock != register.clock:
            continue
        if candidate.drivers == {register.name}:
            return True
    return False


def classify_crossings(design: DesignGraph) -> List[Crossing]:
    module_regs = _collect_module_registers(design)
    crossings: List[Crossing] = []

    for module in design.iter_modules():
        for register in module.registers.values():
            target_domain = register.clock
            for signal in sorted(register.drivers):
                source_reg = module_regs[module.name].get(signal)
                source_domain = source_reg.clock if source_reg else None
                if source_domain == target_domain:
                    continue

                safe = False
                reason = "combinational path" if source_domain is None else "async source"
                if source_domain != target_domain and target_domain is not None:
                    if _is_synchronized(register, module):
                        safe = True
                        reason = "two-stage synchronizer"
                crossings.append(
                    Crossing(
                        module=module.name,
                        signal=signal,
                        register=register.name,
                        source_domain=source_domain,
                        target_domain=target_domain,
                        safe=safe,
                        reason=reason,
                    )
                )
    return crossings


def analyze_design(
    design: DesignGraph,
    disabled_rules: Optional[Sequence[str]] = None,
) -> AnalysisReport:
    """Run the CDC analysis pipeline on a parsed design."""

    disabled_set = set(disabled_rules or [])
    domains = derive_clock_domains(design)
    crossings = classify_crossings(design)
    return AnalysisReport(
        clock_domains=domains,
        crossings=crossings,
        disabled_rules=disabled_set,
    )


__all__ = [
    "AnalysisReport",
    "ClockDomain",
    "Crossing",
    "analyze_design",
    "classify_crossings",
    "derive_clock_domains",
]
