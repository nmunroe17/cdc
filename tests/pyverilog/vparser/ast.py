"""Minimal stub of PyVerilog AST structures used for testing."""

from __future__ import annotations

from typing import List, Sequence, Tuple


class Node:
    """Base class for all stub AST nodes."""

    def children(self) -> Tuple[Node, ...]:
        return tuple()


class NodeVisitor:
    """Simplified visitor matching PyVerilog's interface."""

    def visit(self, node: Node | Sequence[Node] | None) -> None:
        if node is None:
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                self.visit(item)
            return
        method = getattr(self, "visit_" + node.__class__.__name__, self.generic_visit)
        method(node)

    def generic_visit(self, node: Node) -> None:
        for child in node.children():
            self.visit(child)


class Source(Node):
    def __init__(self, description: "Description") -> None:
        self.description = description

    def children(self) -> Tuple[Node, ...]:
        return (self.description,)


class Description(Node):
    def __init__(self, definitions: Sequence[Node]) -> None:
        self.definitions = list(definitions)

    def children(self) -> Tuple[Node, ...]:
        return tuple(self.definitions)


class ModuleDef(Node):
    def __init__(self, name: str, portlist: "Portlist | None" = None, items: Sequence[Node] | None = None) -> None:
        self.name = name
        self.portlist = portlist
        self.items = list(items or [])

    def children(self) -> Tuple[Node, ...]:
        result: List[Node] = []
        if self.portlist is not None:
            result.append(self.portlist)
        result.extend(self.items)
        return tuple(result)


class Port(Node):
    def __init__(self, first: Node | None = None) -> None:
        self.first = first

    def children(self) -> Tuple[Node, ...]:
        return (self.first,) if self.first is not None else tuple()


class Portlist(Node):
    def __init__(self, ports: Sequence[Port]) -> None:
        self.ports = list(ports)

    def children(self) -> Tuple[Node, ...]:
        return tuple(self.ports)


class Identifier(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Input(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Output(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Inout(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Decl(Node):
    def __init__(self, decls: Sequence[Node]) -> None:
        self.list = list(decls)

    def children(self) -> Tuple[Node, ...]:
        return tuple(self.list)


class Reg(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Wire(Node):
    def __init__(self, name: str) -> None:
        self.name = name


class Sens(Node):
    def __init__(self, sig: Identifier, type: str) -> None:  # noqa: A003 - mimic pyverilog interface
        self.sig = sig
        self.type = type


class SensList(Node):
    def __init__(self, senses: Sequence[Sens]) -> None:
        self.list = list(senses)

    def children(self) -> Tuple[Node, ...]:
        return tuple(self.list)


class Always(Node):
    def __init__(self, sens_list: SensList, statement: Node) -> None:
        self.sens_list = sens_list
        self.statement = statement

    def children(self) -> Tuple[Node, ...]:
        return (self.sens_list, self.statement)


class Lvalue(Node):
    def __init__(self, var: Node) -> None:
        self.var = var

    def children(self) -> Tuple[Node, ...]:
        return (self.var,)


class Pointer(Node):
    def __init__(self, var: Node, ptr: Node) -> None:
        self.var = var
        self.ptr = ptr

    def children(self) -> Tuple[Node, ...]:
        return (self.var, self.ptr)


class IntConst(Node):
    def __init__(self, value: str) -> None:
        self.value = value


class NonblockingSubstitution(Node):
    def __init__(self, left: Lvalue, right: Node) -> None:
        self.left = left
        self.right = right

    def children(self) -> Tuple[Node, ...]:
        return (self.left, self.right)


class BlockingSubstitution(Node):
    def __init__(self, left: Lvalue, right: Node) -> None:
        self.left = left
        self.right = right

    def children(self) -> Tuple[Node, ...]:
        return (self.left, self.right)


class Block(Node):
    def __init__(self, statements: Sequence[Node]) -> None:
        self.statements = list(statements)

    def children(self) -> Tuple[Node, ...]:
        return tuple(self.statements)


class IfStatement(Node):
    def __init__(self, cond: Node, true_statement: Node, false_statement: Node | None = None) -> None:
        self.cond = cond
        self.true_statement = true_statement
        self.false_statement = false_statement

    def children(self) -> Tuple[Node, ...]:
        children: List[Node] = [self.cond, self.true_statement]
        if self.false_statement is not None:
            children.append(self.false_statement)
        return tuple(children)


__all__ = [
    "Always",
    "Block",
    "BlockingSubstitution",
    "Decl",
    "Description",
    "Identifier",
    "IfStatement",
    "Inout",
    "Input",
    "IntConst",
    "Lvalue",
    "ModuleDef",
    "Node",
    "NodeVisitor",
    "NonblockingSubstitution",
    "Output",
    "Pointer",
    "Port",
    "Portlist",
    "Reg",
    "Sens",
    "SensList",
    "Source",
    "Wire",
]
