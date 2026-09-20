"""Pratt parser: tokens in, AST out."""

import sys

from .errors import SyntaxError_
from .lexer import OPENER, Lexer
from .rules import (
    BRACE_RULE,
    CONTINUATION_RULE,
    EXPONENT_RULE,
    HOLE_RULE,
    FAIL_RULE,
    RETURN_RULE,
)
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
    Fail,
    Return,
    StrLit,
    Unary,
)
from .values import to_repr

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

# How deep expressions may nest before we call it too deep. Everything the
# parser recurses on -- a list, a map, a block, a function body, an `if`, a
# parenthesis, a hole in a string, a unary operator -- reaches itself through
# expression(), so counting there counts all of them. 200 is far beyond any
# program written by hand; what the number is for is firing before the stack
# does, and the value only has to be generous enough not to refuse real work.
MAX_NESTING = 200
# A nesting level costs up to six Python frames, so CPython's own limit fired
# first at between 165 and 495 levels depending on the construct -- and a
# RecursionError is a Python traceback, not a Vine error. Raise the ceiling
# high enough that our guard wins, exactly as the interpreter does for call
# depth. Measured in tick 7; function bodies and `if` were the most expensive,
# and this doubles them.
PY_FRAMES_PER_LEVEL = 12

# What a token kind is called when a message has to name one. `ident`, `istr`
# and `iend` are names for the parser's own use; a person writing Vine has
# never been told what they mean, and a message that uses one is asking the
# reader to debug the implementation instead of their program.
KIND_NAMES = {
    "ident": "a name",
    "num": "a number",
    "str": "a string",
    "istr": "a string",
    "kw": "a keyword",
    "eof": "end of input",
    "nl": "end of line",
}


class Parser:
    def __init__(self, source):
        self.src = source
        lexer = Lexer(source)
        self.toks = lexer.tokens()
        # Brackets nobody closed. Blaming one of these beats blaming the end
        # of the file; see error().
        self.unclosed = lexer.unclosed()
        self.i = 0
        # How many expressions are open above this point. See MAX_NESTING.
        self.depth = 0
        # How many function bodies are open above this point. `return` is a
        # statement only inside one, and the parser is where that is known:
        # whether a `return` has a function to leave does not depend on
        # anything that happens when the program runs.
        self.fn_depth = 0
        # Where the statement being parsed began. A line that opens with
        # an infix operator is a mistake with a rule behind it, and this
        # is what tells that line from the `+` in `1 + + 2`. See prefix().
        self.stmt_start = None

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

    def expect(self, kind, value=None, why=None, decorate=None):
        """Consume a token of `kind` (and `value`), or fail saying what was
        wanted. `why` says what the token was for -- `expected ':'` names a
        character, `expected ':' after the map key` names a mistake.
        `decorate` is called with the error before it is raised, for the sites
        that know something extra about how this one goes wrong.
        """
        if self.at(kind, value):
            return self.next()
        want = repr(value) if value is not None else KIND_NAMES.get(kind, kind)
        if why:
            want += " " + why
        err = self.error(f"expected {want}, found {self.describe(self.peek())}")
        if decorate is not None:
            decorate(err)
        raise err

    def describe(self, tok):
        """Name a token the way a reader of the program would name it."""
        if tok.kind in ("eof", "nl", "istr"):
            return KIND_NAMES[tok.kind]
        if tok.kind == "ichunk":
            # An `ichunk` is the text after a hole; the lexer gave it the
            # position of the `}` that ended the hole, which is the character
            # a reader is looking for here.
            return "'}'"
        if tok.kind == "iend":
            return "the end of a string"
        if tok.kind == "str":
            # Vine strings are double-quoted; Python's repr would print
            # 'abc', which is what this parser calls an identifier.
            return f"the string {to_repr(tok.value)}"
        if tok.kind == "num":
            return f"the number {to_repr(tok.value)}"
        if tok.kind == "ident":
            return f"the name {tok.value!r}"
        if tok.kind == "kw":
            return f"the keyword {tok.value!r}"
        return repr(tok.value)

    def error(self, message, tok=None):
        tok = tok or self.peek()
        pos = tok.pos
        if tok.kind == "eof" and self.unclosed:
            # Running out of input is rarely a problem with the last line. It
            # is a problem with the bracket that was never closed, so quote
            # that line and point the caret at the bracket itself.
            bracket, pos = self.unclosed[-1]
            message = f"unclosed {bracket!r}"
        err = SyntaxError_(message, pos, self.src)
        if tok.kind == "eof":
            # Every bracket but the innermost is a second place to look. The
            # caret can only be in one of them, and a reader told about one
            # unclosed bracket has no reason to suspect a second.
            for bracket, other in reversed(self.unclosed[:-1]):
                err.note(f"{bracket!r} at {{pos}} is also unclosed", other)
        # Running out of input is not the same failure as finding the wrong
        # thing: the first may just mean the user has not finished typing.
        err.at_eof = tok.kind == "eof"
        return err

    def waiting(self, bracket, pos):
        """A `decorate` that names the bracket the missing one has to match.

        The caret can only be in one place, and for a closer the interesting
        place is usually the opener -- which may be lines away and is the
        thing a reader has to go and count.

        Unless it is the place the caret is already on. At end of input
        error() moves the caret onto the innermost unclosed bracket and says
        `unclosed '('` -- so for `("a"` the opener *is* the caret, and the
        note read `the '(' at 1:1 is still open` under a caret on that '('.
        A note costs a line and is read as a second place to look; naming the
        first one twice is worse than saying nothing. Found in tick 25 by
        note_and_help_shape.py, which broke on 308 programs and no golden at
        all: one golden carries this note, `missing_comma.err`, and there the
        caret is on a wrong token three lines below the '(' -- the case where
        the note is the whole of the answer, and the one that is kept.
        """
        if pos is None:  # pragma: no cover - every caller has the opener
            return None

        def note(err):
            if err.pos is not None and err.pos.line == pos.line and err.pos.col == pos.col:
                return err  # the caret is already on it; see above
            return err.note(f"the {bracket!r} at {{pos}} is still open", pos)

        return note

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
            self.stmt_start = self.i
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
        if self.at("kw", "return"):
            return self.return_stmt()
        if self.at("kw", "fail"):
            return self.fail_stmt()
        return self.expression()

    def fail_stmt(self):
        """`fail expr`: this run did not work, and here is what to tell them.

        Legal wherever a statement is, and refused nowhere -- unlike `return`,
        which needs a function to leave. What `fail` ends is the program, and
        a program is what every statement is inside.

        The message is required. `return` has a bare form because a function
        that answers nothing answers `nil`, which is a value; a program that
        fails with nothing on stderr is the one ending **Errors** forbids, so
        the grammar is where that is settled rather than the runtime.
        """
        tok = self.next()
        if self.at("nl") or self.at("eof") or self.at("op", "}"):
            raise self.error("'fail' needs a message", tok).help(FAIL_RULE)
        return Fail(tok.pos, self.expression())

    def return_stmt(self):
        tok = self.next()
        if self.fn_depth == 0:
            raise self.error("'return' outside a function", tok).help(RETURN_RULE)
        if self.at("nl") or self.at("eof") or self.at("op", "}"):
            return Return(tok.pos, None)
        return Return(tok.pos, self.expression())

    def let_stmt(self):
        pos = self.next().pos
        name = self.expect("ident", why="after 'let'").value
        self.expect("op", "=", why="after the name being bound")
        self.skip_nl()
        value = self.expression()
        if isinstance(value, FnLit) and value.name is None:
            value.name = name
        return Let(pos, name, value)

    # -- expressions ------------------------------------------------------

    def expression(self, min_bp=0):
        """The one place the parser reaches itself, and so the one place
        nesting is counted. An operator chain does not nest -- `1 + 1 + 1`
        loops here rather than recursing -- so the count is of brackets,
        blocks, holes and unary operators, which is what costs stack."""
        self.depth += 1
        if self.depth > MAX_NESTING:
            raise self.error(f"expression nested more than {MAX_NESTING} deep")
        try:
            left = self.prefix()
            while True:
                left = self.postfix(left)
                tok = self.peek()
                op = tok.value if tok.kind in ("op", "kw") else None
                if op not in INFIX or INFIX[op] < min_bp:
                    return left
                self.next()
                self.skip_nl()
                if op == "*" and self.at("op", "*"):
                    # `**` is two tokens, so the failure lands on the second
                    # '*' with a true and useless message. Every reader
                    # arrives knowing this operator from somewhere; refusing
                    # it without naming what replaces it is the mistake the
                    # ':' in a hole already taught -- see Powers in
                    # docs/spec.md.
                    raise self.error(
                        "expected an expression, found "
                        + self.describe(self.peek())
                    ).help(EXPONENT_RULE)
                if op == "|>":
                    left = self.pipe(left, tok)
                elif op in ("and", "or"):
                    left = Logical(tok.pos, op, left, self.expression(INFIX[op] + 1))
                else:
                    left = Binary(tok.pos, op, left, self.expression(INFIX[op] + 1))
        finally:
            self.depth -= 1

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
        if tok.kind == "istr":
            return self.interp_str()
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
                self.expect("op", ")", decorate=self.waiting("(", tok.pos))
                return inner
            if tok.value == "[":
                return self.list_lit()
            if tok.value == "{":
                return self.map_lit()
        err = self.error(f"expected an expression, found {self.describe(tok)}")
        if tok.kind in ("op", "kw") and tok.value in INFIX and self.opens_a_line():
            err.help(CONTINUATION_RULE)
        raise err

    def opens_a_line(self):
        """Whether the token here is the first of a statement on its own line.

        The lexer emits `nl` only where a newline separates statements: never
        inside `(` `)` or `[` `]`, where an expression may wrap, and never
        before a `|>`, which continues the line above it. So a newline
        immediately before the first token of a statement is exactly the
        reader who tried to continue a line from the left -- and the same
        wrapped expression two lines earlier, inside `print(...)`, is legal.
        """
        return (
            self.i == self.stmt_start
            and self.i > 0
            and self.toks[self.i - 1].kind == "nl"
        )

    def interp_str(self):
        """An interpolated string: `istr`, then hole/`ichunk` pairs, then `iend`.

        The lexer has already decided where each hole's expression ends, so
        this asks for exactly one expression per hole and no more. `"{x y}"`
        is a mistake worth naming rather than a silent two-expression block.
        """
        tok = self.next()
        parts = [Literal(tok.pos, tok.value)] if tok.value else []
        while not self.at("iend"):
            parts.append(self.expression())
            if not self.at("ichunk"):
                err = self.error(
                    "expected '}' to close the interpolation, found "
                    + self.describe(self.peek())
                )
                if self.at("op", ":"):
                    # Almost every other language with interpolation puts a
                    # format spec after a colon here, and Vine deliberately
                    # does not -- see Formatting in docs/spec.md. Refusing a
                    # syntax everyone arrives with is cheap; refusing it
                    # without naming what replaces it is not.
                    err.help(HOLE_RULE)
                raise err
            chunk = self.next()
            if chunk.value:
                parts.append(Literal(chunk.pos, chunk.value))
        self.next()
        return StrLit(tok.pos, parts)

    def postfix(self, left):
        while True:
            if self.at("op", "("):
                pos = self.next().pos
                args = self.comma_list(")", pos)
                left = Call(pos, left, args)
            elif self.at("op", "["):
                pos = self.next().pos
                key = self.expression()
                self.expect("op", "]", decorate=self.waiting("[", pos))
                left = Index(pos, left, key)
            elif self.at("op", "."):
                pos = self.next().pos
                name = self.expect("ident", why="after '.'").value
                left = Index(pos, left, Literal(pos, name))
            else:
                return left

    def comma_list(self, close, opener=None):
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
        self.expect("op", close, decorate=self.waiting(OPENER[close], opener))
        return items

    def list_lit(self):
        pos = self.expect("op", "[").pos
        return ListLit(pos, self.comma_list("]", pos))

    def map_lit(self):
        # A `{` that is the very first token of an interpolation is almost
        # always someone reaching for another language's `{{` escape. The
        # check is exact rather than a guess: the previous token is the text
        # the lexer emitted immediately before opening the hole.
        in_hole = self.i > 0 and self.toks[self.i - 1].kind in ("istr", "ichunk")
        pos = self.expect("op", "{").pos
        pairs = []
        self.skip_nl()
        if self.accept("op", "}"):
            return MapLit(pos, pairs)
        while True:
            self.skip_nl()
            key = self.map_key()
            self.expect(
                "op", ":", why="after the map key", decorate=self.doubled(in_hole)
            )
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
        self.expect("op", "}", decorate=self.waiting("{", pos))
        return MapLit(pos, pairs)

    def doubled(self, in_hole):
        """A `decorate` for the `{{` mistake: `"{{1}}"` is a hole holding the
        map literal `{1`, and `expected ':'` is true about it and unhelpful."""
        if not in_hole:
            return None
        return lambda err: err.note(
            "'{' inside an interpolation opens a map literal, "
            "not an escaped brace"
        ).help(BRACE_RULE)

    def map_key(self):
        """A bare identifier is shorthand for its own name as a string key."""
        tok = self.peek()
        if tok.kind == "ident":
            self.next()
            return Literal(tok.pos, tok.value)
        return self.expression()

    def fn_lit(self):
        pos = self.expect("kw", "fn").pos
        paren = self.expect("op", "(", why="to open the parameter list").pos
        params = []
        self.skip_nl()
        if not self.accept("op", ")"):
            while True:
                self.skip_nl()
                params.append(self.expect("ident", why="for a parameter").value)
                self.skip_nl()
                if self.accept("op", ","):
                    self.skip_nl()
                    if self.at("op", ")"):
                        break
                    continue
                break
            self.skip_nl()
            self.expect("op", ")", decorate=self.waiting("(", paren))
        seen = set()
        for p in params:
            if p in seen:
                raise self.error(f"duplicate parameter '{p}'")
            seen.add(p)
        self.fn_depth += 1
        try:
            body = self.block()
        finally:
            self.fn_depth -= 1
        return FnLit(pos, params, body)

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
        pos = self.expect("op", "{", why="to open a block").pos
        stmts = self.statements(terminators={"}"})
        self.expect("op", "}")
        return Block(pos, stmts)


def parse(source):
    """Parse `source` into a Block, or raise SyntaxError_.

    The pair around the call is the one the interpreter keeps for call depth:
    a limit the user is told about, and a raised recursion ceiling that lets
    that limit fire before CPython's does. The RecursionError below is belt
    and braces -- MAX_NESTING should win -- and it exists because before tick
    7 the parser had neither half, and a deeply nested program left as a
    traceback from a file, from `-e`, and at a prompt, where it also ended
    the session.
    """
    parser = Parser(source)
    needed = 1000 + MAX_NESTING * PY_FRAMES_PER_LEVEL
    previous = sys.getrecursionlimit()
    if previous < needed:
        sys.setrecursionlimit(needed)
    try:
        return parser.parse_program()
    except RecursionError:  # pragma: no cover - MAX_NESTING fires first
        raise SyntaxError_(
            "expression nested too deeply", parser.peek().pos, source
        ) from None
    finally:
        sys.setrecursionlimit(previous)
