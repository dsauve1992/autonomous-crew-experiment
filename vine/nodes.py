"""AST node types. Every node carries the position it started at."""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from .errors import Pos


@dataclass
class Node:
    pos: Pos


@dataclass
class Literal(Node):
    value: Any


@dataclass
class ListLit(Node):
    items: List[Node]


@dataclass
class MapLit(Node):
    pairs: List[Tuple[Node, Node]]


@dataclass
class StrLit(Node):
    """An interpolated string: literal chunks and holes, in order.

    Both kinds of part are ordinary expressions, and both are rendered the way
    `str` renders them -- which is the identity on the chunks, since a chunk is
    always a string. One rule, not two.
    """

    parts: List[Node]


@dataclass
class Ident(Node):
    name: str


@dataclass
class Unary(Node):
    op: str
    operand: Node


@dataclass
class Binary(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Logical(Node):
    op: str  # 'and' | 'or'
    left: Node
    right: Node


@dataclass
class Call(Node):
    callee: Node
    args: List[Node]


@dataclass
class Index(Node):
    target: Node
    key: Node


@dataclass
class FnLit(Node):
    params: List[str]
    body: Node
    name: Optional[str] = None


@dataclass
class If(Node):
    cond: Node
    then: Node
    otherwise: Optional[Node] = None


@dataclass
class Block(Node):
    stmts: List[Node] = field(default_factory=list)


@dataclass
class Let(Node):
    name: str
    value: Node


@dataclass
class Return(Node):
    """An early exit from the enclosing function. A statement, never an
    expression: it has no value to give the expression it sits in, and the
    grammar saying so is cheaper than every reader learning it.

    `value` is None for a bare `return`, which is `return nil`.
    """

    value: Optional[Node] = None
