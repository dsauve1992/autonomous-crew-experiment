"""`repr(v)` is Vine source for `v`.

Stated in `docs/spec.md` under **repr and str**, and quoted there as the thing
every escape in `repr` exists for: for any value holding no function, `repr(v)`
is a Vine expression, and evaluating it gives a value `==` to `v`. Functions
are the exception and the only one -- a closure is its environment too, and no
expression denotes that -- so one reprs as `<fn name/arity>`, which must NOT
parse, because source that would not work is worse than a marker that cannot
be mistaken for it.

Tick 6 wrote the promise and checked it over twenty-four values by hand;
`repl/repr_roundtrip.transcript` is the golden that watches one round trip
textually, which is what a reader can verify by eye. This checks the same
sentence over every value the expressions below can build, which is what a
reader cannot.

The expression list is this property's own rather than shared with
no_traceback.py: that one wants arguments, chosen to break the thing being
called, and this one wants values, chosen to be hard to write back down.
"""

import io
import itertools

from vine import run
from vine.errors import VineError
from vine.values import Builtin, Function, equal, to_repr

CLAIM = (
    "repr of a value holding no function is Vine source that evaluates back "
    "to it, and repr of one holding a function is not Vine source at all"
)

# Scalars, chosen for the ways a value has been hard to write down before:
# floats that print in exponent form at both ends, an int with no float, the
# escapes, the brace interpolation made structural, a key of every type.
SCALARS = [
    "nil", "true", "false",
    "0", "1", "-1", "255", "1" + "0" * 40,
    "0.0", "-0.0", "2.5", "-2.5", "0.1 + 0.2", "1 / 3", "10 / 4",
    "1e16", "1e-4", "1e15 * 10", "1.7e308", "1e-320", "1e-323",
    '""', '"s"', '"a b"', '"\\n"', '"\\t"', '"\\r"', '"\\""', '"\\\\"',
    '"\\{"', '"}"', '"{1}"', '"café"', '"a\\nb\\tc"', '"\\\\n"',
]
# Values the language produces rather than the user typing them.
COMPUTED = [
    "range(3)", 'split("a,b,c", ",")', 'split("ab", "")', "sort([2.5, 1.0])",
    "keys({a: 1, b: 2})", "values({a: 1, b: nil})", 'upper("café")',
    'join(["a", "b"], "\\n")', "reduce(range(30), fn(a, b) { a * 10 }, 1)",
    "push([], nil)", 'set({}, 1.0, "x")', "reverse([1, [2]])",
    '"{0.1 + 0.2}"', '"{[1, "a"]}"', "str([1])", 'repr("\\{")',
]
# Values that hold a function, for the half of the claim that is an exception.
FUNCTIONS = [
    "fn(x) { x }", "print", "[fn() { 1 }]", "{a: print}", "[[print]]",
]


def values():
    """Every value this property is checked against, as (source, value).

    The scalars, the computed ones, and then containers built out of them --
    which is where the two conversions meet, since a container reprs its
    elements whichever conversion was asked of the container itself.
    """
    sources = list(SCALARS) + list(COMPUTED)
    for source in sources:
        yield source
    for source in sources:
        yield f"[{source}]"
        yield f"[{source}, {source}]"
        yield f"{{k: {source}}}"
        yield f'[[{source}], {{k: [{source}]}}]'
    # Every scalar as a map key beside every other, since map keys are the one
    # place where two values that are not `==` must stay two entries.
    keyable = [s for s in SCALARS if s not in ("nil",)]
    for a, b in itertools.combinations(keyable, 2):
        yield f"{{{a}: 1, {b}: 2}}"


def evaluate(source):
    return run(source, "<property>", io.StringIO())


def check():
    """Returns (how many values were checked, the ones that broke the claim)."""
    failures = []
    checked = 0
    for source in values():
        try:
            value = evaluate(source)
        except VineError as exc:
            failures.append((source, f"did not even run: {exc.message}"))
            continue
        checked += 1
        text = to_repr(value)
        try:
            back = evaluate(text)
        except VineError as exc:
            failures.append((source, f"repr is {text!r}, which is not source: {exc.message}"))
            continue
        if not equal(back, value):
            failures.append((source, f"repr is {text!r}, which reads back as {to_repr(back)!r}"))
    for source in FUNCTIONS:
        checked += 1
        text = to_repr(evaluate(source))
        try:
            evaluate(text)
        except VineError:
            continue
        failures.append((source, f"repr is {text!r}, which parses -- it must not"))
    return checked, failures
