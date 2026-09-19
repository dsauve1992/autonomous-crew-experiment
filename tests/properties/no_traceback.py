"""A Vine program fails as a Vine error, or it does not fail.

The claim is `docs/spec.md`'s, in the docstring of `VineError`: "Anything Vine
reports to the user. Never a Python traceback." Everything below is one
sentence applied to as many programs as can be enumerated cheaply -- there is
no expectation to write per program, because the expectation is the same for
all of them and is written once, at the top of this file.

Nothing here is random. A fuzzer that finds a bug on Tuesday and not on
Wednesday is not a test, and could not be a golden suite's neighbour; every
program below is enumerated, so a failure reproduces by running ./check again.

What it has caught, in tick 7: `huge + 2.5` where huge is an int no float can
hold (four operators), `range(2 ** 63)`, and expressions nested past the
Python stack (nine constructs, three entry paths). Tick 6 found five more with
the first version of it, which lived in a scratch file and was thrown away.

The last value in VALUES is the one boundary here that has never caught
anything: a list holding a float beside an int no float can hold. Tick 7's
`huge + 2.5` bug was arithmetic converting the int and Python raising where it
could not; tick 10 added `sort(xs, key)`, which puts those two values on
either side of a `<` instead, and wanted the same boundary watched from then
on rather than checked once by hand. Comparison converts nothing, so it is
quiet -- and quiet is the answer this file exists to keep getting.
"""

import io
import itertools

from vine import run
from vine.errors import VineError
from vine.builtins import REGISTRY
from vine.parser import MAX_NESTING
from vine.repl import Repl

CLAIM = "every failure a Vine program can reach is a Vine error, not a Python traceback"

# Ordinary values, and the ones that sit on a seam. The first twelve are tick
# 6's; everything after them is a boundary some part of the implementation
# treats specially -- an int with no float, the largest float, a float that
# underflows, an empty container, a container needing a key, a function value,
# and a list holding two representations that have to be compared to each other.
VALUES = [
    "1", "2.5", '"s"', "true", "nil", "[1]", "{a: 1}", "fn(x) { x }",
    "[]", '""', "{}", "-1",
    "0", "0.0", "-0.0", "false", "1" + "0" * 400, "1.7e308", "1e-320",
    '"\\n"', "[[1]]", '[1, "a"]', "{1: 2}", "print", "[1, 2, 3]",
    "[1.7e308, " + "1" + "0" * 400 + "]",
]

BINARY = ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=",
          "and", "or", "|>"]

# Fragments of source, for the lexer and parser rather than the evaluator.
# Every pair and triple of these is a program. Most are not valid Vine; the
# claim does not ask them to be.
FRAGMENTS = [
    "(", ")", "[", "]", "{", "}", '"', '"a"', '"{', '}"', "\\", "1", "1.",
    ".5", "1e", "1e400", "let", "x", "=", "fn", "if", "else", "do", "|>",
    ",", ":", ".", "#c", "\n", "true", "nil", "and", "not", "-", "%",
    '"\\q"', '"{1}"', "2²", "café", "_", "0x1", "01", "1_0", "'",
    "`", "\t", ";", "@", "$", "?", "!", "&", "**", "^",
]

# Constructs the parser reaches itself through, each written as a function of
# how deep to nest it. The depths checked are around MAX_NESTING and far past
# it: the guard has to fire before Python's stack does, for every one of them.
NESTS = {
    "list": lambda n: "[" * n + "1" + "]" * n,
    "paren": lambda n: "(" * n + "1" + ")" * n,
    "block": lambda n: "do {" * n + "1" + "}" * n,
    "map": lambda n: "{a: " * n + "1" + "}" * n,
    "fn": lambda n: "fn() {" * n + "1" + "}" * n,
    "if": lambda n: "if true {" * n + "1" + "}" * n,
    "not": lambda n: "not " * n + "1",
    "neg": lambda n: "-" * n + "1",
    "hole": lambda n: '"{' * n + "1" + '}"' * n,
    "index": lambda n: "[" * n + "1" + "]" * n + "[0]",
    "pipe": lambda n: "[1]" + " |> rest" * n,
    "chain": lambda n: "1" + " + 1" * n,
}
DEPTHS = [1, 2, MAX_NESTING - 1, MAX_NESTING, MAX_NESTING + 1, 5000]


# An argument position that is not the one being varied. Any value would do;
# what it must not be is interesting.
FILLER = "1"


def argument_lists(n):
    """Argument lists of length `n`, varying every pair of positions.

    For n up to two that is the whole product. Past two it is not: the product
    grows by a factor of twenty-five per argument, and the third argument of
    the three builtins that take one -- `reduce`'s accumulator, `set`'s value,
    `get`'s default -- is stored, returned or passed on rather than inspected.
    Every pair of positions still meets, which is where the five tracebacks of
    tick 6 were: a map in one argument and a list offered as its key in the
    next.
    """
    if n <= 2:
        yield from itertools.product(VALUES, repeat=n)
        return
    for i, j in itertools.combinations(range(n), 2):
        for left, right in itertools.product(VALUES, repeat=2):
            args = [FILLER] * n
            args[i], args[j] = left, right
            yield tuple(args)


def arities_for(low, high):
    """The argument counts worth trying against a builtin taking `low` to
    `high`. Both boundaries and both sides of them: a builtin that counts its
    arguments before looking at them is a different program at each count."""
    top = low + 1 if high is None else high
    return sorted({0, max(low - 1, 0), low, top, top + 1})


def programs():
    """Every program this property is checked against."""
    # Every builtin, at every count around its arity, over every value.
    for b in REGISTRY:
        low, high = b.arity
        for n in arities_for(low, high):
            if high is not None and n > high:
                # Past the maximum the count is refused before any argument is
                # looked at, so the values cannot change the answer. One
                # program says it; every value still appears here at other
                # counts, and on its own further down.
                yield f"{b.name}({', '.join([FILLER] * n)})"
                continue
            for combo in argument_lists(n):
                yield f"{b.name}({', '.join(combo)})"
    # Every binary operator between every pair of values, and both unary ones.
    for op in BINARY:
        for left, right in itertools.product(VALUES, repeat=2):
            yield f"({left}) {op} ({right})"
    for value in VALUES:
        yield f"-({value})"
        yield f"not ({value})"
        yield f'"{{{value}}}"'  # the same value inside a string hole
        yield f"({value}).k"
        yield f"let x = ({value})\nx"
        for other in VALUES:
            yield f"({value})[{other}]"
    # Pipelines, which rewrite a call rather than making one.
    for value in VALUES:
        for b in REGISTRY:
            yield f"({value}) |> {b.name}"
            yield f"({value}) |> {b.name}(1)"
    # Nesting, at and past the limit.
    for nest in NESTS.values():
        for depth in DEPTHS:
            yield nest(depth)
    # Source that is mostly not a program at all, for the lexer and parser.
    for a, b in itertools.product(FRAGMENTS, repeat=2):
        yield a + b
    for a, b, c in itertools.combinations_with_replacement(FRAGMENTS, 3):
        yield a + b + c


def entries():
    """Programs typed at a prompt instead of run from a file.

    The REPL is a second entry path over the same evaluator, and the parts it
    does not share are the ones a file cannot reach: continuation, abandoning
    an entry, and a session that has to survive the error and answer again.
    """
    for b in REGISTRY:
        for value in VALUES:
            yield f"{b.name}({value})\n1 + 1\n"
    for value in VALUES:
        yield f"({value})\n"
        yield f"let x = ({value})\nx\n"
    for nest in NESTS.values():
        for depth in (MAX_NESTING + 1, 5000):
            yield nest(depth) + "\n1 + 1\n"
    for text in ["[1,\n2]\n", "(\n1\n)\n", "let x =\n", "do {\n", "1 +\n",
                 "[\n" * 300, "\n\n\n", "   \n", "^C\n", '"{\n',
                 "let f = fn() { f() }\nf()\n1 + 1\n"]:
        yield text


class Keyboard:
    """tests/run.py's Keyboard, minus the Ctrl-C line, which is its own case."""

    def __init__(self, text):
        self.lines = text.splitlines(keepends=True)
        self.i = 0

    def readline(self):
        if self.i >= len(self.lines):
            return ""
        line = self.lines[self.i]
        self.i += 1
        if line.rstrip("\n") == "^C":
            raise KeyboardInterrupt
        return line

    def isatty(self):
        return False


def check():
    """Returns (how many programs were checked, the ones that broke the claim)."""
    failures = []
    checked = 0
    for source in programs():
        checked += 1
        try:
            run(source, "<property>", io.StringIO())
        except VineError:
            pass
        except Exception as exc:
            failures.append((source, f"{type(exc).__name__}: {exc}"))
    for text in entries():
        checked += 1
        try:
            Repl(Keyboard(text), io.StringIO(), interactive=False).run()
        except Exception as exc:
            failures.append((repr(text), f"{type(exc).__name__}: {exc}"))
    return checked, failures
