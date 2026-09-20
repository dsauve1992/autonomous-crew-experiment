"""1000 is where a walk of a value stops, and nothing else moves it.

**Bindings** promises a number, and the whole of what the number buys is that
it is the *same* number every time it is asked. Before tick 33 there was no
number: the walk ran on CPython's stack, so the depth a value could reach was
a fact about how much of that stack the rest of the program was holding and
how much of it the machine had given the process. `x == x` stopped at 3489 at
the top level and at 1995 inside 498 calls; `print(x)` stopped at 2329 and,
on a thread with a 512KB stack, at 232. Two programs holding the same value
disagreed about whether it was a program, and so did two machines.

So the claim is an equality between three things a program has no business
depending on, and each clause is one of them.

- **Which question is asked.** `==`, `repr`, `str`, `print`, a hole, and
  offering the value as a key are six separate walks over five functions in
  `values.py`. A depth counter added to four of them and forgotten on the
  fifth is the plausible mistake, and it is invisible in a golden: every
  golden of this message goes through one walk.
- **How deep the calls around it are.** This is the clause the old
  implementation failed outright, and it is the reason the limit had to stop
  being the stack: call frames and walk frames came out of one budget, so
  spending more on calls left less for the value. Nesting the *same* walk of
  the *same* value inside 0, 100, 300 and 490 calls has to answer the same
  thing four times.
- **How much stack the machine has.** Checked by running the first clause in
  threads of 512KB, 1MB and 8MB -- the range an ordinary machine spans, and a
  factor of sixteen in what CPython's C stack will hold. This is the clause
  that reaches the `join` fix: put the generator back into `to_display` and
  512KB fails here, at a depth of about 232, while every other clause in the
  suite stays green.

The boundary is checked from both sides. A clause that only watched 1001 fail
would pass for a limit of 1, which is the failure mode a limit has: it is the
*permission* that is hard to keep, not the refusal. So 1000 must answer, and
answer the same in all three clauses.

`reduce` builds the value because a literal cannot: the parser stops one at
200 deep, which is itself one of the measurements behind the number. That is
also why the type grid in `no_traceback.py` cannot reach this message at all
-- every value it builds is written out.

**Each clause was broken on the committed tree**, and what a sabotage costs
elsewhere is as much the point as what it costs here.

- The guard deleted from `to_display` alone -- one walker of the five --
  breaks 28 of the 84 here: every `print`, `repr`, `str` and hole, and not
  one of the two walks that go through `equal` and `canonical`. Elsewhere it
  breaks *one* of the two goldens of this message, the one that prints; the
  one that compares stays green, because a golden can only see the walk it
  happens to use.
- The generator handed back to `join` breaks 16, every one of them on the
  512KB and 1MB threads, and **nothing else in the repository** -- 171 of 172
  still pass. The portability the number rests on is visible here and nowhere
  else.
- The two budgets shared again -- the value's allowance shrinking two levels
  per call, which is the old implementation's defect written as a line --
  breaks 42 here and one other property.
"""

import io
import threading

from vine import run
from vine.errors import VineError

CLAIM = (
    "a value 1000 deep can be walked and one 1001 deep cannot, whichever "
    "question asks, however deep the calls around it, and whatever stack the "
    "machine gave the process"
)

MESSAGE = "value nested more than 1000 deep"

# `reduce(range(n), ...)` wraps the seed n times, so the value is n + 1 deep.
DEPTHS = {1000: "walks", 1001: MESSAGE}

# Six questions that read a whole value, over the five walkers in values.py:
# to_display, to_repr, equal, canonical (through to_key) and holds_function
# (through the key check, which runs before canonical).
WALKS = {
    "print": "print(v)",
    "repr": "print(len(repr(v)))",
    "str": "print(len(str(v)))",
    "==": "print(v == v)",
    "hole": 'print(len("{v}"))',
    "key": "print(len(set({}, v, 1)))",
}

# A ladder of Vine calls to run the walk at the bottom of. 490 is as close to
# MAX_DEPTH as this can go and leave room for the walk's own frames.
NESTINGS = [0, 100, 300, 490]

# The walk goes *inside* the ladder as the statement it already is, and the
# ladder answers a constant, so nothing walks the value again on the way out.
# `v` is the parameter's name too, so the walk is the same source at every
# nesting -- which is what the clause is comparing.
LADDER_HEAD = "let deep = fn(d, v) {\n  if d == 0 {\n    "
LADDER_TAIL = "\n    return 0\n  }\n  return deep(d - 1, v)\n}\n"

STACKS = [512 * 1024, 1024 * 1024, 8 * 1024 * 1024]


def program(walk, depth, nesting):
    """A value `depth` deep, walked `nesting` Vine calls down."""
    build = f"let v = reduce(range({depth - 1}), fn(a, i) {{ [a] }}, [])\n"
    if nesting == 0:
        return build + WALKS[walk] + "\n"
    return (
        build
        + LADDER_HEAD
        + WALKS[walk]
        + LADDER_TAIL
        + f"print(deep({nesting}, v))\n"
    )


def outcome(source):
    """`walks`, the message, or whatever else came out."""
    try:
        run(source, "depth.vine", out=io.StringIO())
        return "walks"
    except VineError as err:
        return err.message
    except RecursionError:
        return "a Python traceback"


def clauses():
    """(label, source, expected) for the first two clauses."""
    for walk in WALKS:
        for depth, expected in DEPTHS.items():
            for nesting in NESTINGS:
                where = "at the top level" if nesting == 0 else f"under {nesting} calls"
                yield (
                    f"{walk} of a value {depth} deep, {where}",
                    program(walk, depth, nesting),
                    expected,
                )


def on_a_stack(size, cases):
    """Run `cases` on a thread of `size` bytes, and hand back what each said."""
    said = []
    thread = threading.Thread(
        target=lambda: said.extend(outcome(source) for _, source, _ in cases)
    )
    previous = threading.stack_size(size)
    try:
        thread.start()
        thread.join()
    finally:
        threading.stack_size(previous)
    return said


def check():
    cases = list(clauses())
    failures = []
    checked = 0

    for label, source, expected in cases:
        checked += 1
        got = outcome(source)
        if got != expected:
            failures.append((label, f"answered {got!r}, not {expected!r}"))

    # Clause three. Only the top-level nesting, because what the stack size
    # decides is how deep one walk can go and a ladder only spends it twice.
    flat = [case for case in cases if ", at the top level" in case[0]]
    for size in STACKS:
        said = on_a_stack(size, flat)
        checked += len(flat)
        for (label, _, expected), got in zip(flat, said):
            if got != expected:
                failures.append(
                    (label, f"on a {size // 1024}KB stack answered {got!r}, "
                     f"not {expected!r}")
                )

    return checked, failures
