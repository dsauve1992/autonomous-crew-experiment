"""Errors, source positions, and the rendering of both."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Pos:
    """A 1-based line/column in a Source."""

    line: int
    col: int


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

    def render(self):
        """Format as a caret-annotated report. Falls back gracefully."""
        head = f"{self.kind}: {self.message}"
        if self.pos is None or self.source is None:
            return head
        line, col = self.pos.line, self.pos.col
        name = self.source.name
        text = self.source.line_text(line)
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
        )


class SyntaxError_(VineError):
    kind = "syntax error"


class RuntimeError_(VineError):
    kind = "runtime error"
