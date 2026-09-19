"""`len` and `reverse` reach exactly the types **len and reverse** gives them,
and `reverse` undoes itself on every value it reaches.

Both sentences are universal and the section states them in one line each, so
neither can be carried by a case: `tests/cases/len_reverse.vine` shows the
involution on three values, and three is the number that always agrees.

The type lists below are a second copy of the ones in `docs/spec.md`, which
is deliberate and is the point. A copy that agrees proves nothing on its own;
what it does is fail when the implementation drifts, and make a tick that
widens either builtin edit the sentence in the same commit as the code. If
this file is ever changed to read the lists out of the document, the two stop
being two and the check stops being one -- which is what tick 13 found.

The involution is checked with `==` rather than `repr`, because `repr` would
compare two renderings and the claim is about values. That matters for the one
value `repr` cannot write: a list holding a function reverses twice back to a
list `==` to itself, since `==` on functions is identity, and a repr-based
check would have compared `<fn ...>` with `<fn ...>` and passed for the wrong
reason.
"""

import io

from vine import run
from vine.errors import VineError

CLAIM = (
    "len and reverse accept exactly the types docs/spec.md gives them and fail "
    "on every other, and reverse is its own inverse on all of them"
)

from no_traceback import VALUES

# The grid holds no list with a function in it, and that is the value the
# involution is least obviously true of -- see the docstring.
EXTRA = ["[print]", "[nil, [1], {a: 1}]", "[[1], [2], [3]]"]

LEN_TAKES = ("string", "list", "map")
REVERSE_TAKES = ("string", "list")


def answer(src):
    out = io.StringIO()
    try:
        run(src, "<len-and-reverse>", out)
    except VineError as e:
        return "error: " + str(e).splitlines()[0]
    return out.getvalue().strip()


def check():
    checked = 0
    failures = []

    for value in VALUES + EXTRA:
        kind = answer(f"print(type({value}))")

        for name, takes in (("len", LEN_TAKES), ("reverse", REVERSE_TAKES)):
            checked += 1
            got = answer(f"print({name}({value}))")
            failed = got.startswith("error: ")
            if kind in takes and failed:
                failures.append((f"{name}({value})", f"refused a {kind}: {got}"))
            elif kind not in takes and not failed:
                failures.append((f"{name}({value})", f"accepted a {kind}, answering {got}"))

        if kind in REVERSE_TAKES:
            checked += 1
            got = answer(f"print(reverse(reverse({value})) == {value})")
            if got != "true":
                failures.append(
                    (f"reverse(reverse({value})) == {value}", f"answered {got}")
                )

    return checked, failures
