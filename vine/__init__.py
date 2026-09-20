"""Vine: a small language for shaping data."""

import sys

from .errors import Source, VineError
from .interp import FailSignal, Interpreter
from .parser import parse

__version__ = "0.2.0"

# CPython will not convert between an int and its decimal digits past 4300 of
# them, and raises a ValueError where Vine has no answer to give. One limit,
# four tracebacks, and only the first is about text a program typed: a literal
# that long dies in the lexer, `int(s)` dies inside the conversion it had just
# finished checking, and `str(n)` and a hole die on a number that was
# *computed* -- `reduce(range(700), fn(a, i) { a * 10000000 }, 1)` is 4901
# digits and multiplies perfectly well, and printing it was the crash.
#
# So the limit is not Vine's. Vine's ints are unbounded in arithmetic, and
# writing one out is the same number said a different way; a language whose
# `*` has no ceiling cannot have one in `str`. CPython's limit is a mitigation
# against untrusted decimal input, which is a fact about servers and not about
# this language. What lifting it costs is that writing out an enormous int is
# quadratic and therefore slow -- a slow program, not a crash, and the first
# guard in this repository that anybody hits is `range`'s.
#
# Python 3.11 introduced both the limit and this switch; older versions have
# nothing to lift.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


def run(text, name="<input>", out=None, inp=None, origin=None):
    """Parse and evaluate `text`. Raises VineError on any user-facing failure.

    `origin` is the directory an `import` in this text resolves a relative
    name against -- the directory the file came from. `None` for text with no
    place on disk, where the working directory stands in; see `eval_import`.

    `inp` is the standard input `read()` answers with: `None` when the program
    was given none, or a zero-argument callable returning the text, called at
    most once and only if the program asks.

    A `fail` statement raises `FailSignal` out of here instead. That is not a
    VineError: the program did not break, it refused, and what it carries is
    the sentence it chose rather than a report about itself. Every caller of
    `run` has to say what a refusal looks like from where it stands.
    """
    source = Source(text, name, origin=origin)
    return Interpreter(source, out, inp).run(parse(source))
