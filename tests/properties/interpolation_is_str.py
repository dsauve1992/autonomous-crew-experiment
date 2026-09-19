"""A hole is `str`, and a list shows its elements as source.

Two sentences from `docs/spec.md`, checked together because the first one
alone is the cheap kind of check.

The first is under **Strings**, the last of the four decisions: the value in a
hole "is converted the way `str` converts it, not `repr`", so `"{x}"` and
`str(x)` "can never disagree". Nothing could tell. Interpolation landed in
tick 4 and `str` has been changed since -- floats gained an exponent form in
tick 6 -- with no case asking the two to agree on anything but a name, an int
and a list of ints. It is a real claim, because the two are separate code
paths, and it is still only a claim that the implementation agrees with
itself. See **Consistency is not correctness** in PRINCIPLES.md.

The second is under **Inside a container**, and it is the one with content:
a container's elements are shown as *source*, whichever conversion was asked
of the container. Written as an equation a Vine program can check,

    str(xs) == "[" + join(map(xs, repr), ", ") + "]"

for every list `xs`. The spec argues for that rule from the damage of losing
it -- with elements flattened to text, the one-element list holding `a, b` and
the two-element list holding `a` and `b` both come out `[a, b]` -- so this is
the half that fails if anybody ever makes `str` friendlier to the reader one
level down.

There is a third line here that looks like content and is not, and it is
written down so the next reader does not mistake it for a test: `str` and
`repr` agree on every value except a string. True, and `to_repr` reaches that
answer by *calling* `to_display` for everything that is not a string, so the
assertion cannot fail until that delegation is restructured. It was written
believing it said more, and a sabotage said otherwise -- changing `str` of
`nil` did not break it, because it broke both sides together. It stays as a
guard on the delegation, labelled as one.

The values are repr_is_source.py's, unchanged: that list was built to hold
things that are hard to write down, which is exactly where two ways of writing
a value down would stop agreeing.
"""

import io

from vine import run
from vine.errors import VineError
from repr_is_source import FUNCTIONS, values

CLAIM = (
    "interpolating a value gives exactly what str gives, and a list shows "
    "its elements as source however the list itself was asked for"
)

# One program per value. `v` is bound first so the source of the value never
# has to survive being written inside a string literal.
PROBE = """let v = {source}
let xs = [v, v]
print(type(v), str(v) == "{{v}}", str(v) == repr(v))
print(str(xs) == "[" + join(map(xs, repr), ", ") + "]")
print("{{xs}}" == str(xs))
"""


def check():
    """Returns (how many values were checked, the ones that broke the claim)."""
    failures = []
    checked = 0
    for source in list(values()) + list(FUNCTIONS):
        out = io.StringIO()
        try:
            run(PROBE.format(source=source), "<property>", out)
        except VineError as exc:
            failures.append((source, f"did not even run: {exc.message}"))
            continue
        checked += 1
        first, nested, hole = out.getvalue().split("\n")[:3]
        kind, hole_is_str, str_is_repr = first.split()
        if hole_is_str != "true":
            failures.append((source, f"a {kind} in a hole is not what str gives"))
        if hole != "true":
            failures.append((source, f"a list of {kind} in a hole is not what str gives"))
        if nested != "true":
            failures.append((source, f"str of a list of {kind} is not its elements' repr"))
        if kind == "string" and str_is_repr == "true":
            failures.append((source, "str of a string is its repr -- one of them is not quoting"))
        if kind != "string" and str_is_repr == "false":
            failures.append((source, f"str of a {kind} is not its repr, and only a string may differ"))
    return checked, failures
