"""The escape list is written three times and the three say the same thing.

`\\n \\t \\r \\" \\\\ \\{ \\}` and `\\u{...}` appear in **Lexical structure** in
`docs/spec.md`, in `ESCAPE_HELP` in `vine/lexer.py`, and -- the only one that
decides anything -- in the `ESCAPES` table the lexer actually reads. Tick 20
added `\\u{...}` to all three by hand and tick 20's handoff flagged the shape:
one list, three spellings, and the only thing joining them was that the same
person edited them in the same hour.

What guards them today is `tests/cases/errors/unknown_escape.err`, and it
guards less than it looks. A golden compares a message with itself -- it pins
the *text* of `ESCAPE_HELP` and says nothing about whether that text is true.
Measured rather than asserted: adding `"0": chr(0)` to `ESCAPES` gives the
lexer an escape that neither list documents, and before this file existed the
whole suite passed. Dropping `"}"` from `ESCAPES` -- the other direction, the
help offering an escape the lexer refuses -- was caught, but by
`interpolation.vine`, which happens to contain a `\}`. A golden reaches the
escapes somebody thought to write down in it; nothing compared the list with
the table.

Three clauses:

- Every escape the help names is one the lexer takes.
- Every escape the lexer takes is one the help names -- the other direction,
  and the one a golden can never reach, since a golden only ever sees the
  message and never the table.
- The spec's bullet names the same eight, in the same order.

The count is exact, for the reason `spec_examples_run.py` gives: a property
that reads a document has one clause more than it looks, and it is *how much
it read*. If the spec's bullet is reworded so the parse below finds six
escapes, a floor would pass and this fails.

`\\u{...}` is the odd one: it takes an argument, so it is not in `ESCAPES` and
is checked by running one rather than by looking it up.
"""

import io
import pathlib
import re

from vine import run
from vine.errors import VineError
from vine.lexer import ESCAPES, ESCAPE_HELP

CLAIM = (
    "the escape list in docs/spec.md, the list in ESCAPE_HELP and the "
    "escapes the lexer actually accepts are one list of eight, and no other "
    "escape is accepted"
)

SPEC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "spec.md"

# How many there are. Exact on purpose -- see the docstring.
EXPECTED = 8

# An escape as either list writes it: `\u{...}` first so it is not read as a
# bare `\u`, then any single character after a backslash.
TOKEN = re.compile(r"\\u\{\.\.\.\}|\\.")

# The escape with an argument, which no lookup table can hold.
ARGUMENT = "\\u{...}"


def named_in_help():
    return TOKEN.findall(ESCAPE_HELP)


def named_in_spec():
    """The escapes the **Lexical structure** bullet lists.

    That bullet wraps across source lines, so the paragraph is rejoined before
    it is read. The slice is delimited by prose on both sides: if either
    phrase is reworded the parse finds nothing and the count clause fails,
    which is the intended behaviour and not a bug in the regex.
    """
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    match = re.search(r"Escapes: (.*?)\. A `\{` opens", text)
    if not match:
        return []
    return TOKEN.findall(match.group(1).replace("`", ""))


def accepted(escape):
    """Does the lexer take this escape inside a string?"""
    try:
        run(f'"a{escape}b"', "<property>", io.StringIO())
        return True
    except VineError:
        return False


def check():
    failures, checked = [], 0
    helped, specced = named_in_help(), named_in_spec()

    for label, listed in (("ESCAPE_HELP", helped), ("the spec bullet", specced)):
        checked += 1
        if len(listed) != EXPECTED:
            failures.append(
                (
                    label,
                    f"names {len(listed)} escapes and there are {EXPECTED}: "
                    f"{listed}. If the list changed, edit all three places and "
                    "EXPECTED in the same commit.",
                )
            )

    checked += 1
    if helped != specced:
        failures.append(
            ("the two lists", f"ESCAPE_HELP says {helped}, the spec {specced}")
        )

    # Every escape the help names, the lexer takes.
    for escape in helped:
        checked += 1
        probe = "\\u{41}" if escape == ARGUMENT else escape
        if not accepted(probe):
            failures.append((escape, "is offered by ESCAPE_HELP and refused"))

    # And every escape the lexer takes, the help names. The table, plus the
    # one that carries an argument and so is not in it.
    for char in sorted(ESCAPES):
        checked += 1
        if "\\" + char not in helped:
            failures.append(
                ("\\" + char, "is in the lexer's ESCAPES and unnamed by the help")
            )
    checked += 1
    if accepted("\\u{41}") and ARGUMENT not in helped:
        failures.append((ARGUMENT, "is accepted and unnamed by the help"))

    # Nothing else is an escape. Every other ASCII character, since an escape
    # is one character and the list is closed.
    for c in range(0x20, 0x7F):
        char = chr(c)
        if char in ESCAPES or char == "u":
            continue
        checked += 1
        if accepted("\\" + char):
            failures.append(
                ("\\" + char, "is accepted and the list is supposed to be closed")
            )
    return checked, failures
