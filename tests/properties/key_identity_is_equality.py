"""A map finds a key exactly when `==` says it is the same key.

**Types** says two keys are the same key when they are `==`, and since tick 30
that sentence covers lists and maps as well as scalars. It is a promise about
two mechanisms: `equal` in `vine/values.py` decides `==` by walking the two
values, and `canonical` builds the hashable form a Python dict compares. Two
statements of one rule, which is the shape **Consistency is not correctness**
in `PRINCIPLES.md` is about -- except that here they are not consistent by
construction, and a disagreement between them is not an error. It is a map
that answers the wrong value, or reports a key absent that it holds. That is
the failure this whole feature exists to remove, so it is the one thing worth
a property.

**Where the two mechanisms are one.** Until tick 31 this file said they "do
not share a line of code", and that was false at the place it mattered.
`equal`'s map branch reads `all(k in b and ...)`, and `k` is a `Key`, so
`k in b` is `Key.__eq__`, which is `canonical`. *Every* map comparison in
Vine therefore asks `canonical` about its keys -- `{a: 1} == {a: 1}` as much
as `{[1]: 2} == {[1]: 2}`. Clause 1 compares `==` against a map lookup, so
wherever a key is a map, both of its sides go through the same function and
it is checking one mechanism twice. That is **A delegation makes two answers
one** in `PRINCIPLES.md`, and clause 4 is the second side it takes back: the
promise the delegation makes, written where it can be seen to fail.

Four clauses, each broken on its own.

1. **A map holds `B` exactly when `A == B`**, for every ordered pair of values
   below. This is the whole claim, written the way a Vine program can ask it:
   `contains(set({}, A, "v"), B)` and `A == B` are the same boolean, and where
   they agree on `true`, `get` answers the stored value rather than the
   default. The pairs are chosen for the places the two mechanisms could
   part -- `[1]` against `[1.0]`, which are two keys; `{a: 1, b: 2}` against
   `{b: 2, a: 1}`, which are one, because `equal` does not compare a map's
   order and `canonical` therefore may not either. Making `canonical` return
   a tuple of a map's pairs rather than a frozenset breaks 4 pairs here.

2. **A key comes back out as the value that was put in, in its own order.**
   `keys(set({}, A, 1))` is `[A]`, and `repr` of the two agrees -- which is
   the stronger half, since `==` would be satisfied by a map key handed back
   with its pairs shuffled. It is the clause that catches the obvious
   implementation of clause 1: a canonical form good enough to compare with
   is not good enough to hand back, and `Key` keeps the original value beside
   it for exactly this reason.

3. **The five spellings that take a key agree about what a key is.** A
   literal, `set`, `get`, `contains` and `m[k]` all reach `key_for`, and the
   rule is worth stating where the enumeration can see it: for every value
   below, either all five accept it or all five refuse it with the same
   message. **Types** promises that agreement in a sentence listing the five
   by name, and until this clause nothing checked more than one of them at a
   time. Widening `key_for` for `set` alone would pass every other check in
   the suite.

4. **A map wrapping a key is `==` exactly when the keys are.**
   `{A: 1} == {B: 1}` and `A == B` are the same boolean. The spec prints one
   instance of this, `{{a: 1, b: 2}: "x"} == {{b: 2, a: 1}: "x"}`, and
   `spec_examples_run.py` runs that one line; this is the same claim over
   every pair. It is the clause that fails when `equal` and `canonical` part
   *in key position*, which is the one place clause 1 cannot look. Making
   `equal`'s map branch compare keys by `repr` rather than by identity --
   the plausible mistake, since `repr` is source and looks like an identity
   -- breaks 8 pairs here, and in the suite as tick 30 left it, exactly one
   other thing: the single `{{a: 1, b: 2}: "x"} == {{b: 2, a: 1}: "x"}` line
   in **Composite keys**, which `spec_examples_run.py` runs. Against tick
   30's value list clause 1 caught none of it at all, and two of the eight
   are `0.0` against `-0.0` -- the borrowed answer that had no entry in key
   position before this tick.

The values include ones holding a function, which is the only refusal left,
so clause 3 has both answers to agree about and clauses 1 and 4 skip them --
a value no map can hold is not a pair of anything.
"""

import io
import itertools

from vine import run
from vine.errors import VineError

CLAIM = (
    "a map holds a key exactly when == says it is the same key, hands it "
    "back as the value that was put in, agrees with == about a key it is "
    "wrapped around, and is refused by all five spellings or by none"
)

# Values chosen for where `equal` and `canonical` could part: the type-strict
# scalars, the same scalars one layer down inside a list, two maps that differ
# only in order, and the empty containers that have no element to disagree on.
VALUES = [
    "nil", "true", "false", "0", "1", "1.0", '"1"', '""', '"a"',
    "0.0", "-0.0", "2.5", "10 / 4",
    "[]", "[1]", "[1.0]", "[true]", '["1"]', "[nil]", "[1, 2]", "[2, 1]",
    "[[1]]", "[[1.0]]", "[1, [2]]", "[[1], 2]",
    "{}", "{a: 1}", "{a: 1.0}", "{b: 1}", "{a: 1, b: 2}", "{b: 2, a: 1}",
    "{a: {b: 1}}", "{a: [1]}", "[{a: 1}]", "[{a: 1, b: 2}]", "[{b: 2, a: 1}]",
    # Tick 31. Nothing above puts a composite key *inside* a value, so
    # `canonical`'s list and map branches were reached only from the top --
    # and `-0.0`, the fourth answer this feature borrows from Python, had no
    # entry one level down at all. A grid reaches exactly what is in its
    # value list.
    "[0.0]", "[-0.0]", "{[1]: 1}", "{[1.0]: 1}",
    "{{a: 1, b: 2}: 1}", "{{b: 2, a: 1}: 1}",
]

# Values that are not keys at all. Clause 3's other answer.
NOT_KEYS = ["print", "fn(x) { x }", "[print]", "{a: print}", "[[trim]]"]

# The five spellings, as a program taking the key twice: once to build a map
# with, once to ask it about. `{}` is the empty map a literal cannot ask about,
# so the literal's spelling asks whether the key it just wrote is found.
SPELLINGS = [
    "{{({key}): 1}}",
    "set({{}}, {key}, 1)",
    "get({{}}, {key}, nil)",
    "contains({{}}, {key})",
    'get({{}}, {key})',
]


def answer(source):
    """What `source` evaluates to, or the VineError it raised."""
    try:
        return run(source, "<property>", io.StringIO())
    except VineError as exc:
        return exc


def check():
    failures = []
    checked = 0

    # Clause 1 and 2 need each value once as a built map and once as a probe.
    for a, b in itertools.product(VALUES, repeat=2):
        checked += 1
        same = answer(f"({a}) == ({b})")
        found = answer(f'contains(set({{}}, {a}, "v"), {b})')
        got = answer(f'get(set({{}}, {a}, "v"), {b}, "miss")')
        if isinstance(same, VineError) or isinstance(found, VineError):
            failures.append(((a, b), "did not run"))
            continue
        if found is not same:
            failures.append((
                (a, b),
                f"== says {same} and the map says {found}",
            ))
        elif got != ("v" if same else "miss"):
            failures.append(((a, b), f"contains says {found} and get answers {got!r}"))

    for source in VALUES:
        checked += 1
        back = answer(f"repr(keys(set({{}}, {source}, 1)))")
        want = answer(f"repr([{source}])")
        if back != want:
            failures.append((source, f"comes back out as {back} and went in as {want}"))

    # Clause 4: a map wrapping a key is `==` exactly when the keys are. The
    # only clause that reaches `canonical` and `equal` where they disagree
    # about a *key*, which is where clause 1 asks one mechanism twice.
    for a, b in itertools.product(VALUES, repeat=2):
        checked += 1
        same = answer(f"({a}) == ({b})")
        wrapped = answer(f"({{({a}): 1}}) == ({{({b}): 1}})")
        if isinstance(same, VineError) or isinstance(wrapped, VineError):
            failures.append(((a, b), "did not run"))
        elif wrapped is not same:
            failures.append((
                (a, b),
                f"== says {same} and a map holding each under one key "
                f"says {wrapped}",
            ))

    # Clause 3: the five spellings agree, both ways.
    for source in VALUES + NOT_KEYS:
        checked += 1
        seen = []
        for spelling in SPELLINGS:
            outcome = answer(spelling.format(key=source))
            seen.append(outcome.message if isinstance(outcome, VineError) else None)
        if len(set(seen)) != 1:
            failures.append((
                source,
                "is refused by some spellings and not others: "
                + "; ".join(
                    f"{s.format(key='k')} -> {m or 'accepted'}"
                    for s, m in zip(SPELLINGS, seen)
                ),
            ))
        elif (seen[0] is None) == (source in NOT_KEYS):
            failures.append((
                source,
                "is accepted" if seen[0] is None else f"is refused: {seen[0]}",
            ))

    return checked, failures
