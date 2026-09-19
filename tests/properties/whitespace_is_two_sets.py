"""Vine has two whitespace sets, and the spec states the size of both.

**Text** says `trim` removes "every character Unicode calls whitespace --
twenty-nine of them today", and that "the lexer, `int` and `float` all take
the same four". Two numbers, stated in prose, guarded by nothing. This file is
what makes them claims rather than decoration.

The reason to pin them is not that either is likely wrong today; both were
true when they were written and both are true now. It is that one of them
*moves*. `trim` is Python's `str.strip()`, which asks the Unicode table the
host was built against, and that table gains characters between releases. The
lexer's four are written out in `SPACE` and in `skip_trivia` and move only
when somebody edits them. So the document holds one number that a Python
upgrade can falsify without anybody touching this repository -- exactly the
failure a golden cannot see, because no golden reads the document.

Three clauses, and they fail for three different reasons:

- `trim` takes 29 and the four separators and the non-breaking space are
  among them. Fails if the host's Unicode table moved.
- The lexer, `int` and `float` take exactly four, the same four. Fails if
  somebody widens one of the three and not the others -- which is the shape
  the spec says is deliberate, so it should cost a failing test to change.
- There are four in the second set and every one of them is in the first.
  Fails if somebody edits this file's expectation rather than the code.

Sabotaged one at a time, which is the only way to learn which of them is
load-bearing. Narrowing `trim` to the four fails the first alone (25 of
them). Widening the lexer fails the second alone, and widening `int` and
`float` without the lexer fails it differently, which is the disagreement
**Text** calls deliberate. A fifth clause was written and then deleted: see
the note in `check`.

Stated over Vine programs rather than over `str.strip` directly, because what
the spec promises is what `trim` does, and `trim` is reachable from a program.

One thing this cost, and it is the reason the probe is written the way it is.
The lexer clause first read `1<ws>+<ws>1`, and the newline failed it: the
program is `1`, then `+`, which is not an expression. That is not the lexer
keeping a newline -- `skip_trivia` consumes it like the other three -- it is
the newline carrying a flag the other three do not, and **Lexical structure**
says so. So the four are trivia, and only three of them are *insignificant*
trivia, and a probe at statement level cannot tell those apart. It is written
inside `(` `)`, where **Lexical structure** promises newlines are ignored,
which is the one context where the four really are interchangeable -- and the
probe now checks that promise too, for free.
"""

import io
import unicodedata

from vine import run
from vine.errors import VineError
from vine.values import to_display

CLAIM = (
    "trim removes exactly the 29 characters Unicode calls whitespace, the "
    "lexer, int and float take exactly the four a program's source may hold, "
    "and those four are a strict subset of the twenty-nine"
)

# The four a program may hold, written out rather than imported from the
# lexer: this is the expectation, and the lexer is what it is checked against.
PROGRAM_SPACE = frozenset(" \t\r\n")

# What Unicode calls whitespace, asked of the standard rather than of `trim`.
# `str.isspace` is the wrong question -- it is true of characters `strip` does
# not take -- so this is the category test plus the two the standard lists
# outside it.
def unicode_space():
    return frozenset(
        chr(c)
        for c in range(0x110000)
        if unicodedata.category(chr(c)) in ("Zs", "Zl", "Zp")
        or c in (0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x1C, 0x1D, 0x1E, 0x1F, 0x85)
    )


EXPECTED_UNICODE_SPACE = 29
SEPARATORS = frozenset(chr(c) for c in range(0x1C, 0x20))
NBSP = " "


def answer(source):
    """What a Vine expression evaluates to, as text. Errors come back tagged."""
    try:
        return to_display(run(source, "<property>", io.StringIO()))
    except VineError as exc:
        return "!" + exc.render().split("\n")[0]


def trims(char):
    """Does `trim` take this character off both ends of a string?"""
    escape = f"\\u{{{ord(char):x}}}"
    return answer(f'trim("{escape}a{escape}")') == "a"


def check():
    failures, checked = [], 0
    standard = unicode_space()

    if len(standard) != EXPECTED_UNICODE_SPACE:
        failures.append(
            (
                f"unicodedata {unicodedata.unidata_version}",
                f"calls {len(standard)} characters whitespace, and **Text** "
                f"says {EXPECTED_UNICODE_SPACE}. The table moved; update the "
                "count in docs/spec.md and here, in the same commit.",
            )
        )

    # Clause one: trim takes all of them, and nothing else.
    for c in range(0x110000):
        if 0xD800 <= c < 0xE000:
            continue
        char = chr(c)
        checked += 1
        wanted = char in standard
        if trims(char) != wanted:
            verb = "does not" if wanted else "does"
            failures.append(
                (f"U+{c:04X}", f"trim {verb} take it, and Unicode disagrees")
            )

    for char in sorted(SEPARATORS) + [NBSP]:
        checked += 1
        if char not in standard:
            failures.append(
                (f"U+{ord(char):04X}", "**Text** names it and Unicode does not")
            )

    # Clause two: the lexer, int and float take the same four and no more.
    for c in sorted(ord(ch) for ch in standard):
        char, escape = chr(c), f"\\u{{{c:x}}}"
        wanted = char in PROGRAM_SPACE
        checked += 3
        # The lexer: whitespace between two tokens, so anything it does not
        # skip is a token and the program does not parse. Inside `(` `)`,
        # because that is where the four are interchangeable -- see the note
        # on the newline at the top of this file.
        if (answer(f"(1{char}+{char}1)") == "2") != wanted:
            verb = "skips" if not wanted else "does not skip"
            failures.append((f"U+{c:04X}", f"the lexer {verb} it"))
        for name in ("int", "float"):
            got = answer(f'{name}("{escape}1{escape}")')
            if (not got.startswith("!")) != wanted:
                verb = "takes" if not wanted else "refuses"
                failures.append((f"U+{c:04X}", f"{name} {verb} it as padding"))

    # Clause three: four, and every one of them inside the twenty-nine.
    checked += 1
    if len(PROGRAM_SPACE) != 4:
        failures.append(("PROGRAM_SPACE", f"holds {len(PROGRAM_SPACE)}, not 4"))
    outside = PROGRAM_SPACE - standard
    if outside:
        shown = " ".join(f"U+{ord(ch):04X}" for ch in sorted(outside))
        failures.append(
            ("PROGRAM_SPACE", f"{shown} is not whitespace to Unicode")
        )
    # There was a fourth check here, asserting the two sets are not equal.
    # It is gone: it cannot fail on its own. Making them equal means widening
    # PROGRAM_SPACE to all 29, and the clause above tests membership of it
    # character by character against three implementations, so 76 failures
    # arrive before that one does. A clause that only ever fires in company
    # is not a test, it is a count -- see the reviewer role file.
    return checked, failures
