"""Turns Vine source text into a flat list of tokens."""

from dataclasses import dataclass

from .errors import Pos, SyntaxError_
from .values import INFINITY

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

# `\{` is how a literal brace is written, now that a bare one opens a hole.
# `\}` is accepted for symmetry: a bare `}` outside a hole is already literal,
# but someone who escapes the open brace will reach for the close one too, and
# "unknown escape" is a poor answer to a reasonable guess.
#
# `\u{...}` is not in here because it carries an argument; see codepoint().
ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    '"': '"',
    "\\": "\\",
    "{": "{",
    "}": "}",
}

ESCAPE_HELP = 'the escapes are \\n \\t \\r \\" \\\\ \\{ \\} and \\u{...}'

# What a codepoint escape is made of. Upper and lower case both, because the
# hex a reader copies out of a character table comes in both.
HEX = frozenset("0123456789abcdefABCDEF")

CODEPOINT_HELP = "a codepoint is written '\\u{1e}' -- hex digits in braces"

# Which opener a closer is allowed to pop off the bracket stack. Popping on any
# closer would let `)` end a string interpolation, and the lexer would carry on
# in the wrong mode.
OPENER = {")": "(", "]": "[", "}": "{"}

# Identifiers are [A-Za-z_][A-Za-z0-9_]* and numbers are ASCII digits, exactly
# as docs/spec.md says. Python's own str.isalpha/isdigit are Unicode-aware and
# would silently widen both: `café` would lex as an identifier, and `2²` would
# lex as a number and then crash int() with a Python traceback.
DIGITS = frozenset("0123456789")
IDENT_START = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
IDENT_REST = IDENT_START | DIGITS


@dataclass
class Token:
    # 'num' | 'str' | 'ident' | 'kw' | 'op' | 'nl' | 'eof', plus the three
    # an interpolated string becomes: 'istr' | 'ichunk' | 'iend'. See chunk().
    kind: str
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
        # where it was opened, is it a string interpolation?). Inside ( ) or
        # [ ] an expression may wrap freely, so newlines are suppressed there
        # -- but a { } block nested inside them (a function body, say) needs
        # them back, so this is a stack of flags rather than a depth counter.
        # What is left on it when the input ends is the list of brackets
        # nobody closed, which is what the parser needs to blame the right
        # character for running out of input.
        self.brackets = []
        # One Pos per interpolated string currently open, innermost last.
        # Non-empty means the lexer is inside a `{...}` hole: chunks of
        # literal text are read to completion the moment they begin, so there
        # is no third state to be in.
        self.strings = []
        # Where the last `#` consumed inside a hole was. Kept for one message
        # and nothing else: see unterminated().
        self.hole_comment = None

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
        return [(b, pos) for _, b, pos, hole in self.brackets if not hole]

    def open_hole(self):
        """Where the innermost open interpolation began, or None."""
        for _, _, pos, hole in reversed(self.brackets):
            if hole:
                return pos
        return None

    def unterminated_string(self, quote):
        """`unterminated string`, blaming `quote` -- plus what a hole changes.

        The message is true wherever it comes from, and true is not the same
        as useful. `"{"` is a brace to everyone who has written one anywhere
        else: the `{` opens a hole, the `"` after it opens a *second* string,
        and that one runs to the end of the file. Blaming the `{` instead
        would be a guess -- `"{ "abc` is a genuinely unterminated inner string
        -- so the caret stays where the parser actually stopped and the note
        supplies the fact both cases are missing.
        """
        err = SyntaxError_("unterminated string", quote, self.src)
        hole = self.open_hole()
        if hole is not None:
            err.note(
                "this string is inside the interpolation "
                "opened by the '{' at {pos}",
                hole,
            )
            err.help("a literal brace is written '\\{'")
        return err

    def tokens(self):
        out = []
        while True:
            saw_newline = self.skip_trivia()
            if self.strings and saw_newline:
                raise self.unterminated()
            if saw_newline and not self.suppressing() and out and not self.continues():
                out.append(Token("nl", None, self.here()))
            if self.i >= len(self.text):
                if self.strings:
                    raise self.unterminated()
                out.append(Token("eof", None, self.here()))
                return out
            self.next_token(out)

    def unterminated(self):
        """The innermost open string ran off the end of its line.

        The note reads the other way round from unterminated_string()'s: the
        string blamed here *contains* the open hole rather than sitting inside
        one, and a hole is always open when this is raised -- `self.strings`
        is non-empty only between a hole opening and the string closing, and
        the string can only close from inside chunk().

        The second note is for the `#` case alone, and it earns its line: the
        reader can see a closing quote at the end of that line and has to be
        told it is inside a comment. Without the first note they would learn
        the wrong rule from it, since a `#` in a string's ordinary text is
        just a character.
        """
        err = SyntaxError_("unterminated string", self.strings[-1], self.src)
        err.note(
            "the '{' at {pos} opened an interpolation, "
            "and the line ended with it still open",
            self.open_hole(),
        )
        if self.hole_comment is not None:
            err.note(
                "the '#' at {pos} began a comment, "
                "so the rest of the line is not part of the program",
                self.hole_comment,
            )
        return err

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
                if self.strings:
                    self.hole_comment = self.here()
                while self.i < len(self.text) and self.peek() != "\n":
                    self.advance()
            else:
                break
        return saw_newline

    def next_token(self, out):
        """Lex one token -- or, for a string, the several a string becomes."""
        pos = self.here()
        ch = self.peek()
        if ch in DIGITS:
            out.append(self.number(pos))
            return
        if ch == '"':
            self.advance()
            self.chunk(pos, out, None)
            return
        if ch in IDENT_START:
            out.append(self.word(pos))
            return
        for op in OPERATORS:
            if self.text.startswith(op, self.i):
                for _ in op:
                    self.advance()
                if op in ("(", "["):
                    self.brackets.append((True, op, pos, False))
                elif op == "{":
                    self.brackets.append((False, op, pos, False))
                elif self.brackets and self.brackets[-1][1] == OPENER.get(op):
                    was_hole = self.brackets.pop()[3]
                    if was_hole:
                        # `}` ended an interpolation: back to reading text.
                        self.chunk(self.strings[-1], out, pos)
                        return
                out.append(Token("op", op, pos))
                return
        err = self.error(f"unexpected character {ch!r}")
        if ch == "^":
            # The other spelling of the operator Vine does not have. A
            # spreadsheet writes it this way and so does every BASIC.
            err.help("there is no exponent operator; x to the power y is pow(x, y)")
        raise err

    def number(self, pos):
        digits = ""
        while self.peek() in DIGITS:
            digits += self.advance()
        is_float = False
        if self.peek() == "." and self.peek(1) in DIGITS:
            is_float = True
            digits += self.advance()
            while self.peek() in DIGITS:
                digits += self.advance()
        if self.peek() in ("e", "E") and self.exponent_follows():
            is_float = True
            digits += self.advance()
            if self.peek() in ("+", "-"):
                digits += self.advance()
            while self.peek() in DIGITS:
                digits += self.advance()
        if not is_float:
            return Token("num", int(digits), pos)
        value = float(digits)
        if value in (INFINITY, -INFINITY):
            raise SyntaxError_(
                "number too large to be a float", pos, self.src
            ).help("the largest float is about 1.8e308")
        return Token("num", value, pos)

    def exponent_follows(self):
        """Whether the `e` at the cursor begins an exponent rather than a name.

        `1e5` is a float; `1.and` already lexes as `1` then a name, and `1e`
        must keep doing the same. The guard is the same shape as the one on
        `.`: look past the marker for what the syntax requires.
        """
        if self.peek(1) in DIGITS:
            return True
        return self.peek(1) in ("+", "-") and self.peek(2) in DIGITS

    def chunk(self, quote, out, after):
        """Read literal text up to the next hole or the closing quote.

        `quote` is where the string opened. `after` is None for the text that
        follows the opening quote and the Pos of the `}` that ended the
        previous hole otherwise -- which is also the token stream's shape: a
        plain string is one `str` token exactly as before, and an interpolated
        one is `istr` (the text before the first hole), then the tokens of each
        hole's expression followed by the `ichunk` of text after it, then
        `iend`. The parser never has to know where a hole's expression stops;
        the lexer, which is already counting brackets, tells it.
        """
        text = ""
        while True:
            if self.i >= len(self.text):
                raise self.unterminated_string(quote)
            at = self.here()
            ch = self.advance()
            if ch == '"':
                if after is None:
                    out.append(Token("str", text, quote))
                else:
                    out.append(Token("ichunk", text, after))
                    out.append(Token("iend", None, at))
                    self.strings.pop()
                return
            if ch == "{":
                if after is None:
                    out.append(Token("istr", text, quote))
                    self.strings.append(quote)
                else:
                    out.append(Token("ichunk", text, after))
                self.brackets.append((False, "{", at, True))
                return
            if ch == "\n":
                raise self.unterminated_string(quote)
            if ch == "\\":
                if self.i >= len(self.text):
                    raise self.unterminated_string(quote)
                esc = self.advance()
                if esc == "u":
                    text += self.codepoint(at, quote)
                elif esc not in ESCAPES:
                    # `at` is the backslash. self.here() would be the character
                    # after the escape, which is not the thing to look at.
                    raise SyntaxError_(
                        f"unknown escape '\\{esc}'", at, self.src
                    ).help(ESCAPE_HELP)
                else:
                    text += ESCAPES[esc]
            else:
                text += ch

    def codepoint(self, at, quote):
        """Read the `{...}` of a `\\u{...}` escape and answer its character.

        `at` is the backslash. Which position an error blames differs by which
        error it is, and the split is the one unterminated_string() makes: a
        malformed escape blames the character that stopped it and carries a
        note naming the `\\u` it belongs to, because the reader has to be shown
        where the parser actually is; a well-formed escape naming a codepoint
        no string can hold blames the backslash, because there the whole
        escape is the mistake and no single character of it is.

        There is one limit and not two. Digits are not counted, so
        `\\u{000041}` and `\\u{41}` are the same `A`; what is checked is the
        value, which is the thing Unicode actually bounds.
        """
        if self.peek() != "{":
            raise SyntaxError_(
                "expected '{' after '\\u'", at, self.src
            ).help(CODEPOINT_HELP)
        self.advance()
        digits = ""
        while self.peek() in HEX:
            digits += self.advance()
        if self.peek() != "}":
            if self.peek() in ("", "\n"):
                # The string ran out, not merely the escape. That is the
                # larger fact and it already has a message that blames the
                # quote the string opened at, which is where to look.
                raise self.unterminated_string(quote)
            raise SyntaxError_(
                "expected '}' to close a codepoint escape", self.here(), self.src
            ).note("the escape was opened by the '\\u' at {pos}", at).help(
                CODEPOINT_HELP
            )
        self.advance()
        if not digits:
            raise SyntaxError_(
                "a codepoint escape needs at least one hex digit", at, self.src
            ).help(CODEPOINT_HELP)
        value = int(digits, 16)
        if value > 0x10FFFF:
            raise SyntaxError_(
                f"codepoint escape '\\u{{{digits}}}' is past the last "
                "codepoint, '\\u{10ffff}'",
                at,
                self.src,
            )
        if 0xD800 <= value <= 0xDFFF:
            raise SyntaxError_(
                f"codepoint escape '\\u{{{digits}}}' is a surrogate half, "
                "which is not a character",
                at,
                self.src,
            ).help(
                "surrogates exist only inside UTF-16; a string holding one "
                "could not be printed"
            )
        return chr(value)

    def word(self, pos):
        name = ""
        while self.peek() in IDENT_REST:
            name += self.advance()
        return Token("kw" if name in KEYWORDS else "ident", name, pos)
