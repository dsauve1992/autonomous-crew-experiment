"""Errors, source positions, and the rendering of both."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pos:
    """A 1-based line/column, and the Source it points into.

    Carrying the source matters once more than one source is alive at a time:
    in the REPL a closure defined three entries ago can fail today, and the
    caret must quote the line it was written on, not the line being evaluated.
    """

    line: int
    col: int
    source: object = field(default=None, compare=False, repr=False)


class Source:
    """A named blob of Vine code. Owns the lines, so errors can quote them."""

    def __init__(self, text, name="<input>"):
        self.text = text
        self.name = name
        self.lines = text.split("\n")

    def line_text(self, line):
        if 1 <= line <= len(self.lines):
            return self.lines[line - 1]
        return ""


class VineError(Exception):
    """Anything Vine reports to the user. Never a Python traceback."""

    kind = "error"

    def __init__(self, message, pos=None, source=None):
        super().__init__(message)
        self.message = message
        self.pos = pos
        self.source = source
        # Extra lines under the caret, as (label, text, pos). See note().
        self.notes = []

    def note(self, text, pos=None):
        """Add a fact the headline message leaves out, and return self.

        A note exists for the case where the message is true and still
        misleading -- `unterminated string` is correct about `"{"` and says
        nothing about the brace that changed meaning. It states a fact; it
        does not guess what the user meant. `{pos}` in `text` is replaced by
        the position given, which is how a failure carries a *second* place
        to look: the caret is where the parser stopped, the note is where the
        cause is.
        """
        self.notes.append(("note", text, pos))
        return self

    def help(self, text):
        """Add a suggestion, and return self.

        Separate from note() on purpose: a note is a fact about this program,
        a help is a rule of the language offered because it is likely to be
        the one the reader wants. Keeping them apart is what stops a guess
        from being printed in the voice of a fact.
        """
        self.notes.append(("help", text, None))
        return self

    def render(self):
        """Format as a caret-annotated report. Falls back gracefully."""
        head = f"{self.kind}: {self.message}"
        source = self.source
        if self.pos is not None and self.pos.source is not None:
            source = self.pos.source  # the position knows best; see Pos
        if self.pos is None or source is None:
            return "\n".join([head] + self.note_lines("", source))
        line, col = self.pos.line, self.pos.col
        name = source.name
        text = source.line_text(line)
        gutter = str(line)
        pad = " " * len(gutter)
        return "\n".join(
            [
                head,
                f"{pad}--> {name}:{line}:{col}",
                f"{pad} |",
                f"{gutter} | {text}",
                f"{pad} | {' ' * (col - 1)}^",
            ]
            + self.note_lines(pad, source)
        )

    def note_lines(self, pad, source):
        out = []
        for label, text, pos in self.notes:
            if pos is not None:
                where = f"{pos.line}:{pos.col}"
                if pos.source is not None and pos.source is not source:
                    # A second source is alive: bare line:col would be read
                    # against the wrong text. See Pos, and PRINCIPLES.md.
                    where = f"{pos.source.name}:{where}"
                text = text.replace("{pos}", where)
            out.append(f"{pad} = {label}: {text}")
        return out


class SyntaxError_(VineError):
    kind = "syntax error"

    # True when the parser ran out of input rather than finding the wrong
    # thing. The REPL reads this to tell "unfinished" from "wrong".
    at_eof = False


class RuntimeError_(VineError):
    kind = "runtime error"
