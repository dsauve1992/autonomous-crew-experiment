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


# How many calls a report names before it starts counting them instead. The
# caret is inside the innermost one, so these are read innermost first: they
# answer *which call produced this*, which is the question a reader with a
# helper function on screen cannot answer from their own text. The outer ones
# they can walk up to, having been given a position inside their own program;
# 500 of them would bury the report, and `frame()` counts what it drops.
MAX_FRAMES = 3


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
        # The call chain: how many calls this failure has left on its way
        # out, and the ones the report names. See frame().
        self.frames = 0
        self.named = []

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

    def marks(self, pos):
        """Whether `pos` names the very character the caret is on.

        A note pointing where the caret already points costs a line and says
        nothing, and a bare `line:col` is read against whichever source the
        report quotes -- so this cannot compare line and column alone.
        """
        if self.pos is None or pos is None:
            return False
        here = self.pos.source or self.source
        return (pos.source or here) is (self.pos.source or here) and (
            pos.line,
            pos.col,
        ) == (self.pos.line, self.pos.col)

    def frame(self, label, pos):
        """Record a call this failure left on its way out, and return self.

        The caret is where the failure was *detected*, and inside a function
        that is a place the reader did not choose to be. A frame is the fact
        that answers *which call*: the position is a call in the reader's own
        text, so it is a note rather than a help, and it states where control
        came from rather than guessing what was meant.

        Two calls are counted and not named. One whose position is the
        caret's is not a second place to look -- `fn(n) { loop(n) }` failing
        at its own recursive call is the case. One identical to the call just
        named is recursion, and on a stack that is the only thing it can be:
        three copies of the same line are the noise a note exists to avoid,
        and the count below says how deep it went. Past MAX_FRAMES the rest
        are counted rather than named; see note_lines().
        """
        self.frames += 1
        if pos is None or self.marks(pos) or len(self.named) >= MAX_FRAMES:
            return self
        here = (label, pos.line, pos.col, pos.source)
        if self.named and here == self.named[-1]:
            return self
        self.named.append(here)
        return self.note(f"{label} was called at {{pos}}", pos)

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
        hidden = self.frames - len(self.named)
        if hidden:
            # Counted rather than named: too deep, at the caret already, or
            # the same call over again. A reader is owed the depth even when
            # the lines would say nothing -- a failure two hundred calls down
            # reads exactly like one at the top without it.
            calls = "call is" if hidden == 1 else "calls are"
            out.append(f"{pad} = note: {hidden} more {calls} not shown")
        return out


class SyntaxError_(VineError):
    kind = "syntax error"

    # True when the parser ran out of input rather than finding the wrong
    # thing. The REPL reads this to tell "unfinished" from "wrong".
    at_eof = False


class RuntimeError_(VineError):
    kind = "runtime error"
