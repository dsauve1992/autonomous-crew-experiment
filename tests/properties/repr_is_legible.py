"""`repr` output holds no character a reader cannot see.

The other half of the promise under **repr and str**, and the half
`repr_is_source.py` cannot reach. That one evaluates what `repr` wrote and
asks whether it comes back equal -- which stayed true for the whole time
`repr("a\x1eb")` answered a line with a record separator sitting invisibly
inside it. Source and legible are two claims, and only the first had a check.

Tick 20 added `\\u{...}` and made `repr` write the C0 and C1 controls with it.
This is the sentence that change was for, and it is checked over every
codepoint rather than a list, because the list would be the characters
somebody thought of.

The surrogates are here too, and not as an afterthought. The sentence is about
every codepoint *a Vine string can hold*, so it is only true if no string can
hold a surrogate half -- and one that could would not merely be illegible, it
would raise UnicodeEncodeError out of `print`, which is a Python traceback
reaching the user. The guard is watched firing rather than assumed.
"""

import io

from vine import run
from vine.errors import VineError
from vine.values import to_repr

CLAIM = (
    "repr of a string writes every codepoint as itself or as an escape and "
    "never as a character that does not print, and no string can hold a "
    "surrogate half"
)

# The characters that do not print: the C0 and C1 controls. A tab and a
# newline are in here too -- `repr` gives them `\\t` and `\\n`, so a raw one in
# the output is the same defect wearing a friendlier codepoint.
INVISIBLE = frozenset(
    chr(c) for c in list(range(0x00, 0x20)) + list(range(0x7F, 0xA0))
)

SURROGATES = range(0xD800, 0xE000)


def check():
    """Returns (how many codepoints were checked, the ones that broke it)."""
    failures = []
    checked = 0
    for c in range(0x110000):
        if c in SURROGATES:
            continue
        checked += 1
        text = to_repr(chr(c))
        raw = INVISIBLE.intersection(text)
        if raw:
            shown = " ".join(f"U+{ord(ch):04X}" for ch in sorted(raw))
            failures.append(
                (f"U+{c:04X}", f"repr is {text!r}, which holds {shown}")
            )
    for c in SURROGATES:
        checked += 1
        source = f'"\\u{{{c:x}}}"'
        try:
            run(source, "<property>", io.StringIO())
        except VineError:
            continue
        failures.append((f"U+{c:04X}", f"{source} was accepted -- it must not be"))
    return checked, failures
