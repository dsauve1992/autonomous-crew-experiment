"""No control character comes out of `repr` as itself, and the escaped set is
exactly `Cc`.

The other half of the promise under **repr and str**, and the half
`repr_is_source.py` cannot reach. That one evaluates what `repr` wrote and
asks whether it comes back equal -- which stayed true for the whole time
`repr("a\x1eb")` answered a line with a record separator sitting invisibly
inside it. Source and legible are two claims, and only the first had a check.

Tick 20 added `\\u{...}` and made `repr` write the C0 and C1 controls with it.
This is the sentence that change was for, and it is checked over every
codepoint rather than a list, because the list would be the characters
somebody thought of.

Tick 21 narrowed what the first clause claims, and added the second. It had
said `repr` output "holds no character a reader cannot see" -- which is false:
`repr("\u200b")` is three codepoints that render as two, and a zero-width
space is invisible outright rather than merely confusable. The check could not
see that, because INVISIBLE below was the set `repr` escapes, read back. A
property whose expectation is the implementation's own table is one answer
wearing two hats, and it can only ever fail on a leak, never on a gap.

So the gap is closed with a side the implementation does not own: Unicode's
own `Cc`. The spec claims the escaped set is the controls and nothing wider
because `Cc` is closed forever; `escaped_set_is_cc` compares `to_repr` against
`unicodedata` in both directions, so a gap fails it and so does a widening,
and so would the standard reopening the category.

The surrogates are here too, and not as an afterthought. The sentence is about
every codepoint *a Vine string can hold*, so it is only true if no string can
hold a surrogate half -- and one that could would not merely be illegible, it
would raise UnicodeEncodeError out of `print`, which is a Python traceback
reaching the user. The guard is watched firing rather than assumed.
"""

import io
import unicodedata

from vine import run
from vine.errors import VineError
from vine.values import to_repr

CLAIM = (
    "repr never writes a control character as itself, the set it escapes with "
    "a codepoint escape is exactly Unicode's Cc less the three with shorter "
    "spellings, no string can hold a surrogate half, and no error message "
    "quoting such a string holds one either"
)

# The characters this file calls illegible: the C0 and C1 controls, written
# out here rather than read off `REPR_ESCAPES`, which is the table under test.
# A tab and a newline are in here too -- `repr` gives them `\\t` and `\\n`, so a
# raw one in the output is the same defect wearing a friendlier codepoint.
#
# This set is NOT "the characters a reader cannot see". It is narrower, and
# the spec now says so: a zero-width space is invisible and is not in here,
# because `repr` deliberately does not escape it. Do not widen this to close
# that gap -- widening it would assert a promise the language does not make.
INVISIBLE = frozenset(
    chr(c) for c in list(range(0x00, 0x20)) + list(range(0x7F, 0xA0))
)

# The three controls that already had a shorter spelling before `\\u{...}`
# existed, so `repr` writes those and not a codepoint escape.
NAMED = frozenset("\n\t\r")

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
        # The boundary, against Unicode rather than against `REPR_ESCAPES`.
        # The spec says the escaped set is the controls and nothing wider
        # *because* `Cc` is the set the standard closed forever -- so `Cc` is
        # the honest other side, and a disagreement either way is a finding:
        # a gap means something illegible prints as itself, a widening means
        # `repr(s)` has started depending on a table that moves.
        char = chr(c)
        wants_escape = unicodedata.category(char) == "Cc" and char not in NAMED
        has_escape = text.startswith('"\\u{')
        if wants_escape != has_escape:
            if not has_escape:
                why = "Unicode files it under Cc and it is not escaped"
            elif char in NAMED:
                why = "it has a shorter spelling and must be written with that"
            else:
                why = "Unicode does not file it under Cc, so it must not be"
            failures.append((f"U+{c:04X}", f"repr is {text!r}: {why}"))
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
