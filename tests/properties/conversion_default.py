"""A default answers exactly where a conversion refuses text, and nowhere else.

`int(s, default)` and `float(s, default)` are the whole of tick 28, and the
argument for that shape over a pair of `is_number` builtins is structural: a
predicate is a second reading of the grammar and has to be held equal to the
first by somebody, while a default is the first reading with its failure
answered. `examples/timesheet.vine` is what happens without it -- eleven lines
of hand-written grammar that already disagreed with `float` about `"1e5"`.

A structural argument still has to be checked, because "the two forms are one
implementation" is a claim about code that a later tick can quietly falsify by
splitting them. Four clauses, over every string this file can enumerate:

1. **Where the one-argument form answers, the two-argument form answers the
   same value.** A default may not change a conversion that worked. This is
   the clause that would break if the default were consulted before the read
   rather than after it.
2. **Where the one-argument form refuses text, the two-argument form answers
   the default.** The other half: every failure over text is covered, and not
   a subset of them chosen by whoever wrote the matcher.
3. **`float(s, nil) != nil` is `float(s)` answers**, and the same for `int`.
   This is the composition **Conversions** refuses `is_number` on, and by
   tick 14's principle a refusal that rests on a composition owes the domain
   rather than an example. The domain is every string below.
4. **A value that is not text is refused with or without a default**, with the
   same headline. The default covers a failed read and not a category
   mistake -- `get`'s line, drawn again -- and the message a reader gets must
   not move because they passed one.

What this file cannot reach: a string longer than a few characters, of which
there are infinitely many and the alphabet below is the part that matters.
`LONG` holds the ones that are about length itself.
"""

import io
import itertools

from vine import run
from vine.errors import VineError
from vine.values import to_repr

CLAIM = (
    "a default leaves a conversion that works alone, answers every conversion "
    "that refuses text, is refused by a value that is not text, and makes "
    "`float(s, nil) != nil` mean exactly `float(s) answers`"
)

# Every character that decides whether text is a number, in Vine's reading or
# in some other language's: the digits, both signs, the point, the exponent,
# the spaces `int` skips and one it does not, the separator Python allows in a
# literal, a letter, and a digit that is a digit only in Unicode.
ALPHABET = ["0", "1", "9", "-", "+", ".", "e", "_", " ", "\t", " ", "a", "١"]

STRINGS = [""]
for _n in (1, 2, 3):
    STRINGS += ["".join(c) for c in itertools.product(ALPHABET, repeat=_n)]

# Spellings longer than three characters that are their own question.
LONG = [
    "1e5",          # the one the hand-written grammar got wrong
    "1e400",        # the shape of a number, past every float there is
    "1.5e-3", "  12  ", "\t-7\n", ".5", "1.", "+.5e+2",
    "inf", "-inf", "nan", "Infinity",   # numbers Python reads and Vine has not
    "1_000", "0x10", "0b1", "1,000", "12 34",
    "١٢٣",               # digits that are digits only in Unicode
    "1" + "0" * 5000,                   # wider than a float, and read exactly
    "9" * 400 + ".5",
]
STRINGS += LONG

# Values that are not text at all. `int` and `float` read some of them and
# refuse the rest; clause 4 is about the ones they refuse.
NON_TEXT = [
    "1", "2.5", "true", "false", "nil", "[]", "[1]", "{}", "{a: 1}",
    "fn(x) { x }", "print", "-0.0", "1.7e308", "1" + "0" * 400,
]

# A default that no conversion could ever have produced, so clause 1 and
# clause 2 cannot agree by accident.
MARKER = '"<default>"'


def answer(src):
    """What a one-line program writes, or the message it failed with."""
    out = io.StringIO()
    try:
        run(src, "<default>", out)
    except VineError as error:
        return "error: " + str(error)
    return out.getvalue()


def check():
    checked = 0
    failures = []

    for name in ("int", "float"):
        for text in STRINGS:
            literal = to_repr(text)  # repr is Vine source -- repr_is_source.py
            plain = answer(f"print(repr({name}({literal})))")
            with_default = answer(f"print(repr({name}({literal}, {MARKER})))")
            answered = not plain.startswith("error: ")
            checked += 1
            if answered and with_default != plain:
                failures.append((
                    f"{name}({literal}, {MARKER})",
                    f"wrote {with_default!r} where {name}({literal}) wrote {plain!r}",
                ))
            if not answered and with_default != MARKER + "\n":
                failures.append((
                    f"{name}({literal}, {MARKER})",
                    f"wrote {with_default!r} where the default was {MARKER}",
                ))
            # Clause 3: the predicate the spec refuses, spelled in Vine.
            checked += 1
            predicate = answer(f"print({name}({literal}, nil) != nil)")
            if predicate != ("true\n" if answered else "false\n"):
                failures.append((
                    f"{name}({literal}, nil) != nil",
                    f"wrote {predicate!r} and {name}({literal}) "
                    + ("answered" if answered else "refused"),
                ))

        for value in NON_TEXT:
            plain = answer(f"print(repr({name}({value})))")
            with_default = answer(f"print(repr({name}({value}, {MARKER})))")
            checked += 1
            if not plain.startswith("error: "):
                if with_default != plain:
                    failures.append((
                        f"{name}({value}, {MARKER})",
                        f"wrote {with_default!r} where {name}({value}) wrote {plain!r}",
                    ))
            elif with_default != plain:
                failures.append((
                    f"{name}({value}, {MARKER})",
                    f"failed with {with_default!r}; without a default it is {plain!r}",
                ))

    return checked, failures
