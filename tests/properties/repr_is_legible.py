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
    "never as a character that does not print, no string can hold a surrogate "
    "half, and no error message quoting such a string holds one either"
)

# The characters that do not print: the C0 and C1 controls. A tab and a
# newline are in here too -- `repr` gives them `\\t` and `\\n`, so a raw one in
# the output is the same defect wearing a friendlier codepoint.
INVISIBLE = frozenset(
    chr(c) for c in list(range(0x00, 0x20)) + list(range(0x7F, 0xA0))
)

SURROGATES = range(0xD800, 0xE000)

# Programs that fail while quoting a string back at the reader, one per place
# in the implementation that builds a message out of a value. Every one of
# them uses `to_repr` today, which is why they are all legible -- and the
# reason to check rather than to note it is that an f-string is one keystroke
# away from embedding the value raw, in the message where which character was
# meant is the entire question. `{E}` is the escape for the codepoint under
# test, so the program text is ASCII whatever is being checked, and `a` and
# `b` around it keep every one of them failing for the same reason each time.
QUOTING = [
    'let "a{E}b" = 1',
    'let m = {{}}\nm["a{E}b"]',
    'int("a{E}b")',
    'float("a{E}b")',
    '{{"a{E}b": 1, "a{E}b": 2}}',
]


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
    for c in sorted(ord(ch) for ch in INVISIBLE) + [0xA0, 0x2028]:
        for template in QUOTING:
            checked += 1
            source = template.format(E=f"\\u{{{c:x}}}")
            try:
                run(source, "<property>", io.StringIO())
            except VineError as exc:
                rendered = exc.render()
                raw = INVISIBLE.intersection(rendered.replace("\n", ""))
                if raw:
                    shown = " ".join(f"U+{ord(ch):04X}" for ch in sorted(raw))
                    failures.append((source, f"the message holds {shown}"))
                continue
            failures.append((source, "did not fail -- it is here because it does"))
    return checked, failures
