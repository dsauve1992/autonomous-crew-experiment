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
        # Newlines separate statements. Inside ( ) or [ ] an expression may
        # wrap freely, so newlines are suppressed there -- but a { } block
        # nested inside them (a function body, say) needs them back, so this
        # is a stack of "suppress?" flags rather than a depth counter.
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
        return bool(self.brackets) and self.brackets[-1]

    def tokens(self):
        out = []
        while True:
            saw_newline = self.skip_trivia()
            if saw_newline and not self.suppressing() and out:
                out.append(Token("nl", None, self.here()))
            if self.i >= len(self.text):
                out.append(Token("eof", None, self.here()))
                return out
            out.append(self.next_token())

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
                    self.brackets.append(True)
                elif op == "{":
                    self.brackets.append(False)
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
                    raise self.error(f"unknown escape '\\{esc}'")
                out += ESCAPES[esc]
            else:
                out += ch

    def word(self, pos):
        name = ""
        while self.peek() in IDENT_REST:
            name += self.advance()
        return Token("kw" if name in KEYWORDS else "ident", name, pos)


def tokenize(source):
    return Lexer(source).tokens()
