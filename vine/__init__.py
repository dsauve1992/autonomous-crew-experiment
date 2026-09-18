"""Vine: a small language for shaping data."""

from .errors import Source, VineError
from .interp import Interpreter
from .parser import parse

__version__ = "0.1.0"


def run(text, name="<input>", out=None):
    """Parse and evaluate `text`. Raises VineError on any user-facing failure."""
    source = Source(text, name)
    return Interpreter(source, out).run(parse(source))
