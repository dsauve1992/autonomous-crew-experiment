"""A map finds a key exactly when `==` says it is the same key.

**Types** says two keys are the same key when they are `==`, and since tick 30
that sentence covers lists and maps as well as scalars. It is a promise about
two mechanisms that do not share a line of code: `equal` in `vine/values.py`
decides `==` by walking the two values, and `canonical` builds the hashable
form a Python dict compares. Two statements of one rule, which is the shape
**Consistency is not correctness** in `PRINCIPLES.md` is about -- except that
here they are not consistent by construction, and a disagreement between them
is not an error. It is a map that answers the wrong value, or reports a key
absent that it holds. That is the failure this whole feature exists to remove,
so it is the one thing worth a property.

Three clauses, each broken on its own.

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

The values include ones holding a function, which is the only refusal left,
so clause 3 has both answers to agree about and clause 1 skips them -- a value
no map can hold is not a pair of anything.
"""

import io
import itertools

from vine import run
from vine.errors import VineError

CLAIM = (
    "a map holds a key exactly when == says it is the same key, hands it "
    "back as the value that was put in, and the five spellings that take a "
    "key agree about which values are keys"
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
