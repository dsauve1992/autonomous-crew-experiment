"""A fold that grows a container copies a square, and the count is exact.

**What the fold costs** in `docs/spec.md` priced `push`, `set` and `concat` in
seconds on one machine. A second is not reproducible -- it is a fact about the
machine, the interpreter's build and what else was running -- and a check that
asserts one flakes. The thing that section is actually claiming is a *curve*,
and a curve is countable: `push(xs, x)` is `items + [x]`, so it copies
`len(xs)` elements, and a fold that calls it once per element copies
`0 + 1 + ... + (n-1)`. That number is the same on every machine forever.

So this counts **elements carried across**: how many elements of a container a
builtin was handed end up in the container it answers. The unit is one
element, not one call, because the whole of the section's argument is that
the price is per element of an accumulator rather than per call.

`map` copies **none** under that rule, and that is not a quibble: every
element of `map`'s answer is a call's result, not an element of its input. So
a map program's count is zero however long the list, while the same walk
written as a fold over `push` is a square -- which is the sentence the section
opens with, standing up without a clock.

**Twelve builtins copy and twenty-two do not**, and the roster clause below
holds that split against `REGISTRY` in both directions. (It said *twenty-one*
from the day it was written and the table held twenty-two; the roster clause
checks the table against `REGISTRY` and cannot read the sentence above it, so
a count in prose beside a count in code is a third thing nobody holds.) It is there because
the count is a *floor*: a builtin that copies and is not in the table makes
every figure here too small, silently, and the program that would notice is
the one nobody wrote. An added builtin fails the roster clause the day it is
added, which is the same reason `roster_names_every_builtin.py` exists.

**The tombstone group is the second finding, and it is tick 44's seconds in
this file's unit.** `examples/pipeline.vine` folds a map of the steps that
have started and not ended. At most a handful are ever live -- but until tick
46 nothing in Vine took a key out of a map, so an ended step was held as `nil`
and the accumulator grew to every pair the log ever mentioned. Tick 44
measured that on two logs of the same length, one whose key set grows and one
whose does not, and got 2.261s against 0.999s at 2400 events. Seconds do not
travel. The same two programs counted here are **n²** against **2n - 1**: one
square, one line, from the same number of events, and the same on every
machine forever.

Tick 46 added `remove` and four more rows, and the four are what the sentence
above could not settle. *the same fold with remove* is **0**: the map is empty
before every open and one entry before every close, so nothing is ever carried
anywhere. *the same fold rebuilt in Vine* is **n** -- removal written as four
lines of ordinary Vine over `keys`, which **What the fold costs** used to call
"the same square with a larger constant" and which is linear. That row is the
finding: the square was never a property of the problem, and the sentence that
said it was had stood for two ticks and been reasoned from twice. The last two
rows hold a window of three open keys rather than one, because a builtin that
costs zero is not a ratio -- there the builtin is **4n - 7** and the
composition **8n - 8**, which is a constant apart and not a curve apart.

None of the six discovers anything about `set` or `remove` that a fold above
them does not. What the *group* holds is the thing no single program can say:
the curve is decided by whether the key set grows, that is now the program's
choice, and both ways of making the choice cost the same shape.

**The dedupe pair is the finding.** The section offers the map spelling as
*the shape to reach for* against the `contains` spelling, on 0.13s against
9.37s. Both copy `n(n-1)/2` -- the same square, since `set` copies a map the
way `push` copies a list. What the list spelling adds is `n(n-1)/2`
*comparisons*, and a comparison is a Python call while a copy is a `memcpy`
the host does in C. So the seventy-two is a constant factor and not a
different curve, and the two clauses here say exactly that: same copies,
and one of them alone pays the comparisons.

Sabotage, each against the committed tree, and each run to the end:

- `push` appending in place -- the shortcut the section says is closed --
  breaks 6 of the count assertions here, every one of them reading *copied
  0, not 45*. Three goldens break too: `building_lists`, `immutability` and
  `lists`. So the repository already watched this one, and what it watched was
  the **answer**. What this adds is the price, which is the half that a
  representation change is allowed to move and a golden cannot see. (Six
  against the 48 assertions of tick 37's list and six against the 93 of this
  one: the two programs added in tick 45 fold `set` and this sabotage does not
  reach them.)
- `set` writing into the map it was handed breaks **12 of 93** -- both folds
  over `set`, both tombstone programs, and `dedupe by keys` -- and four
  goldens: `immutability`, `map_keys`, `map_order` and `maps`. Same split as
  `push`: the goldens hold the answer, this holds the price.
- `contains` on a list answered by the host's `in` rather than by `equal`
  breaks the 3 comparison assertions on the dedupe pair, at *compared 0, not
  45*, and 12 clauses of `composition_holds.py`. The second is the one that
  says the answer is wrong; the first is the one that says where the seventy
  went.
- A copier dropped from the table breaks 4: the 3 programs that reach it, and
  the roster clause, which is what stops a wrong figure here from reading as a
  true one.

Four more in tick 46, against a control of 207:

- `remove` writing into the map it was handed breaks 3 files: this one at the
  3 window-of-three assertions (*copied 17, not 33*), `map_remove.vine`, and 2
  claims of `spec_examples_run.py`. The two window-of-one programs do **not**
  break, because a fold that holds one key at a time copies zero either way --
  which is why the window-of-three pair is here and not only the headline.
- `remove` copying the map when the key is absent breaks **this file and
  nothing else**, at 3 assertions (*copied 36, not 33*). It answers every
  question a program can ask identically; the shortcut is only ever visible as
  a count, so this is the one clause in the repository that holds it.
- `remove` taking a scalar key straight to the host's dict instead of through
  `interp.key_for` breaks 6 assertions here, `map_remove.vine` and 2 spec
  claims. The counts read *copied 45, not 0*: the lookup never matches, so
  nothing is removed and the fold is a square again. A seam bug shows up here
  as the curve coming back.
- `remove` dropped from the `COPIERS` table breaks 5: the 3 window assertions
  and both directions of the roster clause.

What the count cannot see: it is elements **carried across**, worked out from
the sizes of the containers a builtin was handed and answered. An
implementation that copies more inside itself without changing what it answers
-- `rest` slicing the whole list and then dropping the head -- is invisible
here. This prices the shape of the algorithm, which is what the section
argues; it does not price the host's memory traffic, which is what the seconds
below it were reaching for and could not hold still.

What this does not price: a program that folds `reverse`, `sort` or `concat`
over a growing accumulator pays a square through a builtin this file counts
but does not have a program for. The table reaches it; the clauses do not.
"""

import io

from vine import run
from vine.builtins import REGISTRY
from vine import values as values_module
from vine import interp as interp_module

CLAIM = (
    "a fold that grows a container copies n(n-1)/2 elements where map copies "
    "none, and the two spellings of dedupe copy the same square -- what one "
    "of them adds is a square of comparisons"
)

# How many elements of a container the builtin was handed end up in the one it
# answers. `args` are the arguments it was called with, `result` what it
# answered; both are Vine values and the call succeeded.
#
# `push` counts its input rather than its answer so that the count is the old
# list and not the new one; every other copier answers exactly what it copied.
# `reverse` of a string builds a new string and carries no element of a
# container, so it counts nothing there.
#
# A builtin that answers the very container it was handed copied nothing, and
# `counted` below says so before it asks the table. That is not a formality:
# it is the one line that makes an in-place `push` -- the shortcut **What the
# fold costs** says is closed -- count zero here instead of counting a list
# that grew under the measurement.
COPIERS = {
    "push": lambda args, result: len(args[0]),
    "concat": lambda args, result: len(result),
    "rest": lambda args, result: len(result),
    "take": lambda args, result: len(result),
    "drop": lambda args, result: len(result),
    "reverse": lambda args, result: len(result) if isinstance(result, list) else 0,
    "sort": lambda args, result: len(result),
    "filter": lambda args, result: len(result),
    "set": lambda args, result: len(args[0]),
    # `remove` answers what it kept, and answers the map itself when the key
    # was not there -- so `counted` scores that call zero before the table is
    # asked, which is the truth: nothing was carried anywhere.
    "remove": lambda args, result: len(result),
    "keys": lambda args, result: len(result),
    "values": lambda args, result: len(result),
}

# The other twenty-one, each with the reason its answer holds no element of a
# container it was handed. Stated rather than implied, because "it does not
# copy" and "nobody thought about it" look identical in an absence.
NON_COPIERS = {
    "read": "answers the string it was handed; nothing is built per element",
    "print": "answers nil",
    "repr": "answers a string",
    "type": "answers a string",
    "len": "answers an int",
    "str": "answers a string",
    "int": "answers an int",
    "float": "answers a float",
    "fixed": "answers a string",
    "pow": "answers a number",
    "range": "builds a list of fresh ints",
    "map": "every element of the answer is a call's result",
    "reduce": "builds nothing; the answer is whatever the function built",
    "first": "answers one element and no container",
    "contains": "answers a bool",
    "get": "answers one value and no container",
    "split": "builds a list of new strings from a string",
    "join": "answers a string",
    "upper": "answers a string",
    "lower": "answers a string",
    "trim": "answers a string",
    "reveal": "answers a string",
}


def counted(source):
    """Run `source`, and answer (elements copied, elements compared).

    The copy count wraps `Builtin.fn` on the registry itself, which is the
    same object `install` puts in every environment, so nothing the program
    can do routes around it. The comparison count wraps `equal` in both
    modules that reach it: `values`, where `contains` looks it up per call,
    and `interp`, which imported it by name and would otherwise let `==` run
    uncounted.
    """
    copied = [0]
    compared = [0]

    def wrap(builtin, price):
        original = builtin.fn

        def counting(interp, pos, args):
            result = original(interp, pos, args)
            if result is not args[0]:
                copied[0] += price(args, result)
            return result

        builtin.fn = counting
        return original

    def counting_equal(a, b, depth=0):
        compared[0] += 1
        return real_equal(a, b, depth)

    restore = [
        (b, wrap(b, COPIERS[b.name])) for b in REGISTRY if b.name in COPIERS
    ]
    real_equal = values_module.equal
    values_module.equal = counting_equal
    interp_module.equal = counting_equal
    try:
        run(source, "cost.vine", out=io.StringIO())
    finally:
        for builtin, original in restore:
            builtin.fn = original
        values_module.equal = real_equal
        interp_module.equal = real_equal
    return copied[0], compared[0]


def square(n):
    """0 + 1 + ... + (n-1): what a fold pays to grow a container n times."""
    return n * (n - 1) // 2


# Each program is written over `n` elements and priced by hand from the
# definitions in docs/spec.md, before anything ran. (copies, comparisons).
PROGRAMS = {
    "a fold over push": (
        "print(len(reduce(range({n}), fn(a, x) {{ push(a, x) }}, [])))",
        lambda n: (square(n), 0),
    ),
    "a fold over set": (
        "print(len(reduce(range({n}), fn(m, x) {{ set(m, x, x) }}, {{}})))",
        lambda n: (square(n), 0),
    ),
    # n concats, the left side 0, 1, ... n-1 long and the right side always 1.
    "a fold over concat": (
        "print(len(reduce(map(range({n}), fn(i) {{ [i] }}), concat, [])))",
        lambda n: (square(n) + n, 0),
    ),
    "map": (
        "print(len(map(range({n}), fn(x) {{ x }})))",
        lambda n: (0, 0),
    ),
    # filter carries the elements it keeps, so it is linear and not free.
    "filter": (
        "print(len(filter(range({n}), fn(x) {{ true }})))",
        lambda n: (n, 0),
    ),
    # rest on lists of n, n-1, ... 1 -- a recursion pays the fold's square
    # without being a fold, which is why the section's sentence about folds
    # had to be narrowed. Its n + 1 comparisons are the `len(xs) == 0` of its
    # n + 1 calls, and they are here because the first count written for this
    # program said zero: `==` compares, and a guard is a comparison the
    # program's author does not think of as one.
    "a recursion over rest": (
        "let walk = fn(xs) {{\n"
        "  if len(xs) == 0 {{ return 0 }}\n"
        "  return 1 + walk(rest(xs))\n"
        "}}\n"
        "print(walk(range({n})))",
        lambda n: (square(n), n + 1),
    ),
    # Every element distinct, so contains misses every time and scans the
    # whole accumulator: n scans of 0, 1, ... n-1 elements, and n pushes of
    # lists 0, 1, ... n-1 long. The same square, twice, one of them in Python.
    "dedupe by contains": (
        "let dedupe = fn(xs) {{\n"
        "  reduce(xs, fn(a, x) {{\n"
        "    if contains(a, x) {{ return a }}\n"
        "    return push(a, x)\n"
        "  }}, [])\n"
        "}}\n"
        "print(len(dedupe(range({n}))))",
        lambda n: (square(n), square(n)),
    ),
    # A map that cannot forget. 2n events over n keys: event 2i opens key i
    # and event 2i+1 ends it. At most one key is ever live, and `set` is the
    # only way into a map, so an ended key is held as nil and the map grows to
    # n. The opens copy 0, 1, ... n-1 and the closes copy 1, 2, ... n, which
    # is n(n-1) + n = n*n. The 2n comparisons are the `j % 2 == 0` of the 2n
    # events. `examples/pipeline.vine` is this fold; see **What the fold
    # costs**.
    "a fold over a map that cannot forget": (
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  let k = int(j / 2)\n"
        "  if j % 2 == 0 {{ set(m, k, j) }} else {{ set(m, k, nil) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (n * n, 2 * n),
    ),
    # The same 2n events over one key, which is the same program handed a log
    # whose live set does not grow. The map is one entry from the first event
    # on, so every set after the first copies exactly one: 2n - 1, and linear.
    # The gap between this line and the one above is the whole finding, in the
    # unit that travels.
    "the same fold over one key": (
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  if j % 2 == 0 {{ set(m, 0, j) }} else {{ set(m, 0, nil) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (2 * n - 1, 2 * n),
    ),
    # The same 2n events again, with `remove` closing the key instead of
    # setting it to nil. The map is empty before every open and one entry
    # before every close, so `set` copies nothing and `remove` answers a map
    # of nothing: **zero**, at every n. The 2n comparisons are the guard, as
    # above -- the removal itself compares nothing, because a key's slot is a
    # hash and not a scan.
    "the same fold with remove": (
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  let k = int(j / 2)\n"
        "  if j % 2 == 0 {{ set(m, k, j) }} else {{ remove(m, k) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (0, 2 * n),
    ),
    # And the same fold again with removal written in Vine rather than called:
    # `keys` filtered and folded back into a map, which is what **Not in v0.2**
    # said would be "the same square with a larger constant" and is not. Each
    # close copies the one key out of `keys` and keeps none of it, so this is
    # **n** -- linear, like the builtin and unlike the tombstone. That is the
    # finding of tick 46, and it is the number that took the curve out of the
    # argument for the builtin. Its n extra comparisons over the row above are
    # the `j != k` of the filter, one per surviving key.
    "the same fold rebuilt in Vine": (
        "let without = fn(m, k) {{\n"
        "  reduce(filter(keys(m), fn(j) {{ j != k }}), fn(acc, j) {{ set(acc, j, get(m, j)) }}, {{}})\n"
        "}}\n"
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  let k = int(j / 2)\n"
        "  if j % 2 == 0 {{ set(m, k, j) }} else {{ without(m, k) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (n, 3 * n),
    ),
    # One key live is the case where the builtin costs nothing at all, which
    # is not a ratio. These two hold a window of three instead -- close the key
    # opened two events ago -- so both spellings pay a constant per event and
    # the constant can be compared. `set` copies 2 and `remove` answers 2 in
    # the steady state, with the first two opens cheaper: 4n - 7.
    "a window of three, with remove": (
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  let k = int(j / 2)\n"
        "  if j % 2 == 0 {{ set(m, k, j) }} else {{ remove(m, k - 2) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (4 * n - 7, 2 * n),
    ),
    # The same window, rebuilt in Vine: `keys` carries three, `filter` keeps
    # two, and the fold back in copies 0 + 1. Twice the builtin's copies and
    # two and a half times its comparisons -- a constant, not a curve, which
    # is why the builtin's argument had to be found somewhere other than here.
    # See **Taking a key out** in docs/spec.md.
    "a window of three, rebuilt in Vine": (
        "let without = fn(m, k) {{\n"
        "  reduce(filter(keys(m), fn(j) {{ j != k }}), fn(acc, j) {{ set(acc, j, get(m, j)) }}, {{}})\n"
        "}}\n"
        "let held = reduce(range({n} * 2), fn(m, j) {{\n"
        "  let k = int(j / 2)\n"
        "  if j % 2 == 0 {{ set(m, k, j) }} else {{ without(m, k - 2) }}\n"
        "}}, {{}})\n"
        "print(len(held))",
        lambda n: (8 * n - 8, 5 * n - 3),
    ),
    # The same answer through a map: the same square of copies, and keys
    # carrying the n of them out at the end. No comparison anywhere.
    "dedupe by keys": (
        "let dedupe = fn(xs) {{\n"
        "  keys(reduce(xs, fn(m, x) {{ set(m, x, true) }}, {{}}))\n"
        "}}\n"
        "print(len(dedupe(range({n}))))",
        lambda n: (square(n) + n, 0),
    ),
}

# Three sizes, so a count that is right at one n by coincidence is not right
# at three. 40 is the ceiling the recursion sets: it nests one call per
# element and **Bindings** stops a call chain at 500.
SIZES = [10, 20, 40]


def check():
    failures = []
    checked = 0

    for label, (template, price) in PROGRAMS.items():
        for n in SIZES:
            checked += 2
            copies, comparisons = counted(template.format(n=n))
            want_copies, want_comparisons = price(n)
            if copies != want_copies:
                failures.append(
                    (f"{label}, n = {n}", f"copied {copies} elements, not {want_copies}")
                )
            if comparisons != want_comparisons:
                failures.append(
                    (
                        f"{label}, n = {n}",
                        f"compared {comparisons} elements, not {want_comparisons}",
                    )
                )

    # The roster: the table above accounts for every builtin, once.
    installed = [b.name for b in REGISTRY]
    checked += len(installed)
    for name in installed:
        if name in COPIERS and name in NON_COPIERS:
            failures.append((name, "is in both halves of the table"))
        elif name not in COPIERS and name not in NON_COPIERS:
            failures.append(
                (name, "is a builtin this file has not said whether it copies")
            )
    for name in list(COPIERS) + list(NON_COPIERS):
        if name not in installed:
            failures.append((name, "is in the table and is not a builtin"))

    return checked, failures
