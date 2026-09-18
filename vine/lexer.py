"""Turns Vine source text into a flat list of tokens."""

from dataclasses import dataclass

from .errors import Pos, SyntaxError_

KEYWORDS = {"let", "fn", "if", "else", "do", "true", "false", "nil", "and", "or", "not"}

# Longest first, so that '==' wins over '=' and '|>' over '|'.
OPERATORS = [
    "|>",
    "==",
    "!=",
    "<=",
    ">=",
    "+",
    "-",
    "*",
    "/",
    "%",
    "<",
    ">",
    "=",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    ",",
    ":",
    ".",
]

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}

# Identifiers are [A-Za-z_][A-Za-z0-9_]* and numbers are ASCII digits, exactly
# as docs/spec.md says. Python's own str.isalpha/isdigit are Unicode-aware and
# would silently widen both: `café` would lex as an identifier, and `2²` would
# lex as a number and then crash int() with a Python traceback.
DIGITS = frozenset("0123456789")
IDENT_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
IDENT_REST = IDENT_START | DIGITS


@dataclass
class Token:
    kind: str  # 'num' | 'str' | 'ident' | 'kw' | 'op' | 'eof'
    value: object
    pos: Pos

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.pos.line}:{self.pos.col})"


class Lexer:
    def __init__(self, source):
        self.src = source
        self.text = source.text
        self.i = 0
        self.line = 1
        self.col = 1
        # One entry per bracket still open: (suppress newlines?, the bracket,
        # where it was opened). Inside ( ) or [ ] an expression may wrap
        # freely, so newlines are suppressed there -- but a { } block nested
        # inside them (a function body, say) needs them back, so this is a
        # stack of flags rather than a depth counter. What is left on it when
        # the input ends is the list of brackets nobody closed, which is what
        # the parser needs to blame the right character for running out of
        # input.
        self.brackets = []

    def error(self, message):
        return SyntaxError_(message, self.here(), self.src)

    def here(self):
        return Pos(self.line, self.col, self.src)

    def peek(self, offset=0):
        j = self.i + offset
        return self.text[j] if j < len(self.text) else ""

    def advance(self):
        ch = self.text[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def suppressing(self):
        return bool(self.brackets) and self.brackets[-1][0]

    def unclosed(self):
        """The brackets still open, outermost first, once tokenizing is done."""
        return [(bracket, pos) for _, bracket, pos in self.brackets]

    def tokens(self):
        out = []
        while True:
            saw_newline = self.skip_trivia()
            if saw_newline and not self.suppressing() and out and not self.continues():
                out.append(Token("nl", None, self.here()))
            if self.i >= len(self.text):
                out.append(Token("eof", None, self.here()))
                return out
            out.append(self.next_token())

    def continues(self):
        """True when the next line picks up the previous one, not a new one.

        A pipeline written down the page is the idiom the whole language is
        built around, and both docs/spec.md and README.md show one at the top
        level:

            orders
              |> map(total)
              |> reduce(add, 0.0)

        Without this the newline after `orders` ends the statement and the next
        line starts with an infix operator, which is a syntax error. `|>` is
        the only operator treated this way, and it can be: no expression begins
        with it, so a line that starts with `|>` can only be a continuation.
        `-` could never have this, being a prefix operator too.
        """
        return self.text.startswith("|>", self.i)

    def skip_trivia(self):
        """Consume whitespace and comments. Returns True if a newline was passed."""
        saw_newline = False
        while self.i < len(self.text):
            ch = self.peek()
            if ch == "\n":
                saw_newline = True
                self.advance()
            elif ch in " \t\r":
                self.advance()
            elif ch == "#":
                while self.i < len(self.text) and self.peek() != "\n":
                    self.advance()
            else:
                break
        return saw_newline

    def next_token(self):
        pos = self.here()
        ch = self.peek()
        if ch in DIGITS:
            return self.number(pos)
        if ch == '"':
            return self.string(pos)
        if ch in IDENT_START:
            return self.word(pos)
        for op in OPERATORS:
            if self.text.startswith(op, self.i):
                for _ in op:
                    self.advance()
                if op in ("(", "["):
                    self.brackets.append((True, op, pos))
                elif op == "{":
                    self.brackets.append((False, op, pos))
                elif op in (")", "]", "}"):
                    if self.brackets:
                        self.brackets.pop()
                return Token("op", op, pos)
        raise self.error(f"unexpected character {ch!r}")

    def number(self, pos):
        digits = ""
        while self.peek() in DIGITS:
            digits += self.advance()
        if self.peek() == "." and self.peek(1) in DIGITS:
            digits += self.advance()
            while self.peek() in DIGITS:
                digits += self.advance()
            return Token("num", float(digits), pos)
        return Token("num", int(digits), pos)

    def string(self, pos):
        self.advance()  # opening quote
        out = ""
        while True:
            if self.i >= len(self.text):
                raise SyntaxError_("unterminated string", pos, self.src)
            at = self.here()
            ch = self.advance()
            if ch == '"':
                return Token("str", out, pos)
            if ch == "\n":
                raise SyntaxError_("unterminated string", pos, self.src)
            if ch == "\\":
                if self.i >= len(self.text):
                    raise SyntaxError_("unterminated string", pos, self.src)
                esc = self.advance()
                if esc not in ESCAPES:
                    # `at` is the backslash. self.here() would be the character
                    # after the escape, which is not the thing to look at.
                    raise SyntaxError_(f"unknown escape '\\{esc}'", at, self.src)
                out += ESCAPES[esc]
            else:
                out += ch

    def word(self, pos):
        name = ""
        while self.peek() in IDENT_REST:
            name += self.advance()
        return Token("kw" if name in KEYWORDS else "ident", name, pos)
