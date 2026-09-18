"""Pratt parser: tokens in, AST out."""

from .errors import SyntaxError_
from .lexer import tokenize
from .nodes import (
    Binary,
    Block,
    Call,
    FnLit,
    Ident,
    If,
    Index,
    Let,
    ListLit,
    Literal,
    Logical,
    MapLit,
    Unary,
)

# Binding power of each infix operator. Higher binds tighter.
INFIX = {
    "|>": 1,
    "or": 2,
    "and": 3,
    "==": 4,
    "!=": 4,
    "<": 5,
    "<=": 5,
    ">": 5,
    ">=": 5,
    "+": 6,
    "-": 6,
    "*": 7,
    "/": 7,
    "%": 7,
}
UNARY_BP = 8
POSTFIX_BP = 9


class Parser:
    def __init__(self, source):
        self.src = source
        self.toks = tokenize(source)
        self.i = 0

    # -- token helpers ----------------------------------------------------

    def peek(self):
        return self.toks[self.i]

    def next(self):
        tok = self.toks[self.i]
        if tok.kind != "eof":
            self.i += 1
        return tok

    def at(self, kind, value=None):
        tok = self.peek()
        return tok.kind == kind and (value is None or tok.value == value)

    def accept(self, kind, value=None):
        if self.at(kind, value):
            return self.next()
        return None

    def expect(self, kind, value=None):
        if self.at(kind, value):
            return self.next()
        want = repr(value) if value is not None else kind
        raise self.error(f"expected {want}, found {self.describe(self.peek())}")

    def describe(self, tok):
        if tok.kind == "eof":
            return "end of input"
        if tok.kind == "nl":
            return "end of line"
        return repr(tok.value)

    def error(self, message, tok=None):
        tok = tok or self.peek()
        err = SyntaxError_(message, tok.pos, self.src)
        # Running out of input is not the same failure as finding the wrong
        # thing: the first may just mean the user has not finished typing.
        err.at_eof = tok.kind == "eof"
        return err

    def skip_nl(self):
        while self.at("nl"):
            self.next()

    # -- statements -------------------------------------------------------

    def parse_program(self):
        pos = self.peek().pos
        stmts = self.statements(terminators={"eof"})
        self.expect("eof")
        return Block(pos, stmts)

    def statements(self, terminators):
        stmts = []
        self.skip_nl()
        while not self.at_terminator(terminators):
            stmts.append(self.statement())
            if self.at_terminator(terminators):
                break
            if not self.at("nl"):
                raise self.error(
                    f"expected end of line between statements, found "
                    f"{self.describe(self.peek())}"
                )
            self.skip_nl()
        return stmts

    def at_terminator(self, terminators):
        tok = self.peek()
        if "eof" in terminators and tok.kind == "eof":
            return True
        if "}" in terminators and tok.kind == "op" and tok.value == "}":
            return True
        return False

    def statement(self):
        if self.at("kw", "let"):
            return self.let_stmt()
        return self.expression()

    def let_stmt(self):
        pos = self.next().pos
        name = self.expect("ident").value
        self.expect("op", "=")
        self.skip_nl()
        value = self.expression()
        if isinstance(value, FnLit) and value.name is None:
            value.name = name
        return Let(pos, name, value)

    # -- expressions ------------------------------------------------------

    def expression(self, min_bp=0):
        left = self.prefix()
        while True:
            left = self.postfix(left)
            tok = self.peek()
            op = tok.value if tok.kind in ("op", "kw") else None
            if op not in INFIX or INFIX[op] < min_bp:
                return left
            self.next()
            self.skip_nl()
            if op == "|>":
                left = self.pipe(left, tok)
            elif op in ("and", "or"):
                left = Logical(tok.pos, op, left, self.expression(INFIX[op] + 1))
            else:
                left = Binary(tok.pos, op, left, self.expression(INFIX[op] + 1))

    def pipe(self, left, tok):
        """`x |> f(a)` is `f(x, a)`; `x |> f` is `f(x)`."""
        right = self.expression(INFIX["|>"] + 1)
        if isinstance(right, Call):
            return Call(tok.pos, right.callee, [left] + right.args)
        return Call(tok.pos, right, [left])

    def prefix(self):
        tok = self.peek()
        if tok.kind == "num" or tok.kind == "str":
            self.next()
            return Literal(tok.pos, tok.value)
        if tok.kind == "kw":
            if tok.value in ("true", "false"):
                self.next()
                return Literal(tok.pos, tok.value == "true")
            if tok.value == "nil":
                self.next()
                return Literal(tok.pos, None)
            if tok.value == "not":
                self.next()
                return Unary(tok.pos, "not", self.expression(UNARY_BP))
            if tok.value == "fn":
                return self.fn_lit()
            if tok.value == "if":
                return self.if_expr()
            if tok.value == "do":
                self.next()
                return self.block()
        if tok.kind == "ident":
            self.next()
            return Ident(tok.pos, tok.value)
        if tok.kind == "op":
            if tok.value == "-":
                self.next()
                return Unary(tok.pos, "-", self.expression(UNARY_BP))
            if tok.value == "(":
                self.next()
                inner = self.expression()
                self.expect("op", ")")
                return inner
            if tok.value == "[":
                return self.list_lit()
            if tok.value == "{":
                return self.map_lit()
        raise self.error(f"expected an expression, found {self.describe(tok)}")

    def postfix(self, left):
        while True:
            if self.at("op", "("):
                pos = self.next().pos
                args = self.comma_list(")")
                left = Call(pos, left, args)
            elif self.at("op", "["):
                pos = self.next().pos
                key = self.expression()
                self.expect("op", "]")
                left = Index(pos, left, key)
            elif self.at("op", "."):
                pos = self.next().pos
                name = self.expect("ident").value
                left = Index(pos, left, Literal(pos, name))
            else:
                return left

    def comma_list(self, close):
        """Parse `expr, expr, ...` up to and including `close`."""
        items = []
        self.skip_nl()
        if self.accept("op", close):
            return items
        while True:
            self.skip_nl()
            items.append(self.expression())
            self.skip_nl()
            if self.accept("op", ","):
                self.skip_nl()
                if self.at("op", close):  # trailing comma
                    break
                continue
            break
        self.skip_nl()
        self.expect("op", close)
        return items

    def list_lit(self):
        pos = self.expect("op", "[").pos
        return ListLit(pos, self.comma_list("]"))

    def map_lit(self):
        pos = self.expect("op", "{").pos
        pairs = []
        self.skip_nl()
        if self.accept("op", "}"):
            return MapLit(pos, pairs)
        while True:
            self.skip_nl()
            key = self.map_key()
            self.expect("op", ":")
            self.skip_nl()
            pairs.append((key, self.expression()))
            self.skip_nl()
            if self.accept("op", ","):
                self.skip_nl()
                if self.at("op", "}"):
                    break
                continue
            break
        self.skip_nl()
        self.expect("op", "}")
        return MapLit(pos, pairs)

    def map_key(self):
        """A bare identifier is shorthand for its own name as a string key."""
        tok = self.peek()
        if tok.kind == "ident":
            self.next()
            return Literal(tok.pos, tok.value)
        return self.expression()

    def fn_lit(self):
        pos = self.expect("kw", "fn").pos
        self.expect("op", "(")
        params = []
        self.skip_nl()
        if not self.accept("op", ")"):
            while True:
                self.skip_nl()
                params.append(self.expect("ident").value)
                self.skip_nl()
                if self.accept("op", ","):
                    self.skip_nl()
                    if self.at("op", ")"):
                        break
                    continue
                break
            self.skip_nl()
            self.expect("op", ")")
        seen = set()
        for p in params:
            if p in seen:
                raise self.error(f"duplicate parameter '{p}'")
            seen.add(p)
        return FnLit(pos, params, self.block())

    def if_expr(self):
        pos = self.expect("kw", "if").pos
        cond = self.expression()
        then = self.block()
        save = self.i
        self.skip_nl()
        if self.accept("kw", "else"):
            if self.at("kw", "if"):
                return If(pos, cond, then, self.if_expr())
            return If(pos, cond, then, self.block())
        self.i = save
        return If(pos, cond, then, None)

    def block(self):
        pos = self.expect("op", "{").pos
        stmts = self.statements(terminators={"}"})
        self.expect("op", "}")
        return Block(pos, stmts)


def parse(source):
    return Parser(source).parse_program()
